"""Azure AI Agent extractor.

Extracts text from the PDF using pypdf, then sends it to the configured AI Agent
which returns extracted shipment fields as JSON.
"""
from __future__ import annotations

import io
import json
import os
from typing import Any

from shared.models import (
    ExtractedDocument, ExtractedField, Party, ChargeLine, GoodsLine,
)
from shared.enums import DocumentType, TransportMode
from .base import Extractor

_PROMPT = """You are a shipment document extraction assistant.

Extract all available fields from the document text below and return ONLY a JSON object
with this structure (omit fields you cannot find):

{{
  "transport_mode": "OCEAN_FCL | OCEAN_LCL | AIR | ROAD | UNKNOWN",
  "issuer_name": "string",
  "reference_no": "string",
  "issue_date": "string",
  "bl_number": "string",
  "mbl_number": "string",
  "hbl_number": "string",
  "invoice_ref": "string",
  "container_no": "string",
  "seal_no": "string",
  "vessel_voyage": "string",
  "flight_no": "string",
  "port_of_loading": "string",
  "port_of_discharge": "string",
  "eta": "string",
  "last_free_day": "string",
  "goods_description": "string",
  "hs_code": "string",
  "no_of_packages": "string",
  "gross_weight": "string",
  "measurement_cbm": "string",
  "incoterms": "string",
  "freight_terms": "string",
  "cargo_value": "string",
  "total_due": number,
  "currency": "string",
  "remarks_text": "string",
  "parties": [
    {{"role": "SHIPPER|CONSIGNEE|NOTIFY|BROKER", "name": "string", "address": "string"}}
  ],
  "charges": [
    {{"description": "string", "basis": "string", "rate": number, "amount": number}}
  ],
  "goods_lines": [
    {{
      "line_no": number,
      "description": "string",
      "hs_code": "string",
      "quantity": number,
      "unit": "string",
      "unit_price": number,
      "amount": number
    }}
  ]
}}

Document type: {document_type}

--- DOCUMENT TEXT ---
{text}
--- END ---
"""

_TRANSPORT_MAP = {
    "OCEAN_FCL": TransportMode.OCEAN_FCL,
    "OCEAN_LCL": TransportMode.OCEAN_LCL,
    "AIR": TransportMode.AIR,
    "ROAD": TransportMode.ROAD,
}


def _f(value, conf=0.90) -> ExtractedField:
    return ExtractedField(value=value, original_value=value, confidence=conf)


def _parse(data: dict) -> ExtractedDocument:
    doc = ExtractedDocument(document_type=DocumentType.UNKNOWN)

    mode_str = (data.get("transport_mode") or "").upper()
    doc.transport_mode = _TRANSPORT_MAP.get(mode_str, TransportMode.UNKNOWN)

    scalar_fields = [
        "issuer_name", "reference_no", "issue_date", "bl_number", "mbl_number",
        "hbl_number", "invoice_ref", "container_no", "seal_no", "vessel_voyage",
        "flight_no", "port_of_loading", "port_of_discharge", "eta", "last_free_day",
        "goods_description", "hs_code", "no_of_packages", "gross_weight",
        "measurement_cbm", "incoterms", "freight_terms", "cargo_value",
        "currency", "remarks_text",
    ]
    for field in scalar_fields:
        val = data.get(field)
        if val not in (None, ""):
            setattr(doc, field, _f(val))

    total_due = data.get("total_due")
    if total_due is not None:
        try:
            doc.total_due = _f(float(total_due))
        except (TypeError, ValueError):
            pass

    for p in data.get("parties") or []:
        party = Party(role=p.get("role", ""))
        if p.get("name"):
            party.name = _f(p["name"])
        if p.get("address"):
            party.address = _f(p["address"])
        doc.parties.append(party)

    for c in data.get("charges") or []:
        charge = ChargeLine()
        if c.get("description"):
            charge.description = _f(c["description"])
        if c.get("basis"):
            charge.basis = _f(c["basis"])
        for attr in ("rate", "amount"):
            val = c.get(attr)
            if val is not None:
                try:
                    setattr(charge, attr, _f(float(val)))
                except (TypeError, ValueError):
                    pass
        doc.charges.append(charge)

    for g in data.get("goods_lines") or []:
        line = GoodsLine()
        if g.get("line_no") is not None:
            line.line_no = _f(int(g["line_no"]))
        for attr in ("description", "hs_code", "unit"):
            if g.get(attr):
                setattr(line, attr, _f(g[attr]))
        for attr in ("quantity", "unit_price", "amount"):
            val = g.get(attr)
            if val is not None:
                try:
                    setattr(line, attr, _f(float(val)))
                except (TypeError, ValueError):
                    pass
        doc.goods_lines.append(line)

    return doc


class AgentExtractor(Extractor):
    def __init__(self):
        from azure.identity import DefaultAzureCredential
        from azure.ai.projects import AIProjectClient

        endpoint = os.environ["AZURE_AI_ENDPOINT"]
        self._agent_name = os.environ["AZURE_AI_AGENT_NAME"]
        self._agent_version = os.environ.get("AZURE_AI_AGENT_VERSION", "1")

        client = AIProjectClient(endpoint=endpoint, credential=DefaultAzureCredential())
        self._openai = client.get_openai_client()

    @staticmethod
    def _pdf_to_text(data: bytes) -> str:
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(data))
        return "\n".join(page.extract_text() or "" for page in reader.pages)

    def extract(self, data: bytes, document_type: DocumentType) -> ExtractedDocument:
        text = self._pdf_to_text(data)
        prompt = _PROMPT.format(
            document_type=document_type.value,
            text=text,
        )

        response = self._openai.responses.create(
            input=[{"role": "user", "content": prompt}],
            extra_body={
                "agent_reference": {
                    "name": self._agent_name,
                    "version": self._agent_version,
                    "type": "agent_reference",
                }
            },
        )

        text = response.output_text or ""
        # Strip markdown code fences if the agent wraps the JSON
        text = text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()

        parsed: dict[str, Any] = json.loads(text)
        return _parse(parsed)
