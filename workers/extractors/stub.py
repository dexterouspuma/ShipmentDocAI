"""Local stub extractor.

Returns plausible, deterministic extracted data (with confidence scores, including
a couple of intentionally low-confidence fields) so the full pipeline and the
review UI can be exercised without Azure. NOT used in dev/prod.
"""
from __future__ import annotations

from shared.models import (
    ExtractedDocument, ExtractedField, Party, ChargeLine, GoodsLine,
)
from shared.enums import DocumentType, TransportMode
from .base import Extractor


def _f(value, conf):
    return ExtractedField(value=value, original_value=value, confidence=conf)


class StubExtractor(Extractor):
    def extract(self, data: bytes, document_type: DocumentType) -> ExtractedDocument:
        doc = ExtractedDocument(
            document_type=document_type,
            transport_mode=TransportMode.OCEAN_FCL,
        )
        doc.issuer_name = _f("EVERGREEN LINE", 0.99)
        doc.reference_no = _f("EVGL-NYC-2026-058813", 0.96)
        doc.issue_date = _f("25-May-2026", 0.94)
        doc.bl_number = _f("EGLV143026058813", 0.97)
        doc.container_no = _f("EMCU4917832", 0.93)
        doc.seal_no = _f("EVG-772641", 0.91)
        doc.port_of_loading = _f("KAOHSIUNG, TAIWAN (TWKHH)", 0.95)
        doc.port_of_discharge = _f("NEW YORK / NEW JERSEY (USNYK)", 0.95)
        doc.eta = _f("18-Jun-2026", 0.9)
        doc.gross_weight = _f("11,240 KGS", 0.88)
        doc.no_of_packages = _f("1,560 CTNS", 0.86)
        # Intentionally low confidence — should be highlighted in the review UI.
        doc.goods_description = _f("PLASTIC HOUSEHOLD GOODS & STORAGE", 0.62)
        doc.incoterms = _f("FOB Kaohsiung", 0.9)
        doc.freight_terms = _f("PREPAID", 0.97)
        doc.total_due = _f(756.00, 0.92)
        doc.currency = _f("USD", 0.99)

        doc.parties = [
            Party(role="SHIPPER",
                  name=_f("TAIWAN PRECISION PLASTICS CO., LTD.", 0.95)),
            Party(role="CONSIGNEE",
                  name=_f("ATLANTIC SUPPLY GROUP LLC", 0.94)),
            Party(role="NOTIFY",
                  name=_f("GEODIS LOGISTICS LLC", 0.7)),
        ]
        doc.charges = [
            ChargeLine(description=_f("Destination THC", 0.95),
                       basis=_f("Per Container", 0.9), rate=_f(450.0, 0.95), amount=_f(450.0, 0.95)),
            ChargeLine(description=_f("Documentation / B/L Release Fee", 0.93),
                       basis=_f("Per B/L", 0.9), rate=_f(80.0, 0.93), amount=_f(80.0, 0.93)),
        ]
        if document_type in (DocumentType.COMMERCIAL_INVOICE, DocumentType.PACKING_LIST):
            doc.goods_lines = [
                GoodsLine(line_no=_f(1, 0.95),
                          description=_f("LED panel light 60x60", 0.9),
                          quantity=_f(1200, 0.92), unit=_f("PCS", 0.95),
                          unit_price=_f(12.5, 0.9), amount=_f(15000.0, 0.9)),
            ]
        return doc
