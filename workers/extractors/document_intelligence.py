"""Azure AI Document Intelligence extractor.

Routes each document type to the right model (prebuilt-invoice for commercial
invoices; custom-trained models for the rest, by ID from env) and maps the
returned fields into our `ExtractedDocument`.

The field mapping below is a STARTING POINT. Custom-model field names are defined
when you label samples in Document Intelligence Studio, so finalize `_FIELD_MAP`
(and the line-item mapping) once the models are trained.
"""
from __future__ import annotations

import os
from typing import Optional

from shared.models import ExtractedDocument, ExtractedField, Party, ChargeLine
from shared.enums import DocumentType, TransportMode
from .base import Extractor

# Which model analyzes each document type. Custom IDs come from env (set after
# training); commercial invoices use the prebuilt model.
_MODEL_ENV = {
    DocumentType.ARRIVAL_NOTICE: "DOCINTEL_MODEL_ARRIVAL_NOTICE",
    DocumentType.CARRIER_INVOICE: "DOCINTEL_MODEL_CARRIER_INVOICE",
    DocumentType.PACKING_LIST: "DOCINTEL_MODEL_PACKING_LIST",
    DocumentType.BOL: "DOCINTEL_MODEL_BOL",
    DocumentType.COMMERCIAL_INVOICE: "DOCINTEL_MODEL_INVOICE",  # prebuilt-invoice
}

# Map our ExtractedDocument attribute  ->  the model's field name.
# TODO: align right-hand side with the labeled field names per trained model.
_FIELD_MAP = {
    "issuer_name": "IssuerName",
    "reference_no": "ReferenceNumber",
    "issue_date": "IssueDate",
    "bl_number": "BLNumber",
    "container_no": "ContainerNumber",
    "seal_no": "SealNumber",
    "port_of_loading": "PortOfLoading",
    "port_of_discharge": "PortOfDischarge",
    "eta": "ETA",
    "gross_weight": "GrossWeight",
    "no_of_packages": "NumberOfPackages",
    "goods_description": "GoodsDescription",
    "incoterms": "Incoterms",
    "freight_terms": "FreightTerms",
    "total_due": "TotalDue",
    "currency": "Currency",
}


class DocumentIntelligenceExtractor(Extractor):
    def __init__(self):
        endpoint = os.environ["DOCINTEL_ENDPOINT"]
        from azure.ai.documentintelligence import DocumentIntelligenceClient
        key = os.environ.get("DOCINTEL_KEY")
        if key:
            from azure.core.credentials import AzureKeyCredential
            self._client = DocumentIntelligenceClient(endpoint, AzureKeyCredential(key))
        else:
            from azure.identity import DefaultAzureCredential
            self._client = DocumentIntelligenceClient(endpoint, DefaultAzureCredential())

    def _model_id(self, document_type: DocumentType) -> str:
        env_key = _MODEL_ENV.get(document_type)
        model_id = os.environ.get(env_key, "") if env_key else ""
        if not model_id:
            # Fallback to prebuilt layout so we still get OCR + tables.
            return "prebuilt-layout"
        return model_id

    def extract(self, data: bytes, document_type: DocumentType) -> ExtractedDocument:
        model_id = self._model_id(document_type)
        poller = self._client.begin_analyze_document(model_id, body=data)
        result = poller.result()

        doc = ExtractedDocument(document_type=document_type)
        analyzed = result.documents[0] if getattr(result, "documents", None) else None
        if analyzed and analyzed.fields:
            doc.transport_mode = self._detect_mode(analyzed.fields)
            for attr, field_name in _FIELD_MAP.items():
                field = analyzed.fields.get(field_name)
                if field is not None:
                    setattr(doc, attr, self._to_extracted(field))
            self._map_parties(analyzed.fields, doc)
            self._map_charges(analyzed.fields, doc)
        return doc

    # --- helpers -----------------------------------------------------------

    @staticmethod
    def _value_of(field):
        # SDK exposes typed accessors; fall back to content string.
        for attr in ("value_string", "value_number", "value_date", "content"):
            v = getattr(field, attr, None)
            if v is not None:
                return v
        return None

    def _to_extracted(self, field) -> ExtractedField:
        value = self._value_of(field)
        return ExtractedField(
            value=value,
            original_value=value,
            confidence=getattr(field, "confidence", None),
        )

    @staticmethod
    def _detect_mode(fields) -> TransportMode:
        # TODO: refine using model fields (e.g. presence of flight vs vessel).
        if fields.get("FlightNumber") or fields.get("MAWBNumber"):
            return TransportMode.AIR
        return TransportMode.UNKNOWN

    def _map_parties(self, fields, doc: ExtractedDocument) -> None:
        for role, fname in (("SHIPPER", "Shipper"), ("CONSIGNEE", "Consignee"),
                            ("NOTIFY", "NotifyParty")):
            f = fields.get(fname)
            if f is not None:
                doc.parties.append(Party(role=role, name=self._to_extracted(f)))

    def _map_charges(self, fields, doc: ExtractedDocument) -> None:
        # Custom models typically return charge lines as a table-valued field.
        # TODO: map the labeled charges table once the model is trained.
        charges = fields.get("Charges")
        items = getattr(charges, "value_array", None) if charges else None
        for item in items or []:
            obj = getattr(item, "value_object", {}) or {}
            doc.charges.append(ChargeLine(
                description=self._to_extracted(obj["Description"]) if "Description" in obj else ExtractedField(),
                amount=self._to_extracted(obj["Amount"]) if "Amount" in obj else ExtractedField(),
            ))
