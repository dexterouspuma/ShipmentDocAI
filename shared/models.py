"""Pydantic models — the typed shape of extracted data and review state.

These are the Python form of the markdown schemas in `schemas/`. Every extracted
value is wrapped in `ExtractedField` so we always carry a confidence score and the
original-vs-corrected value, which the review UI needs.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Generic, Optional, TypeVar
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


def _utcnow() -> datetime:
    """Timezone-aware UTC now (datetime.utcnow() is deprecated in 3.12)."""
    return datetime.now(timezone.utc)

from .enums import (
    DocumentType,
    TransportMode,
    ProcessingStatus,
    ReviewAction,
)

T = TypeVar("T")


class ExtractedField(BaseModel, Generic[T]):
    """A single extracted value plus the metadata the review UI relies on.

    `value` is the current (possibly analyst-corrected) value.
    `original_value` preserves what the model first returned, for audit.
    `confidence` (0-1) from Document Intelligence drives low-confidence highlighting.
    """
    value: Optional[T] = None
    original_value: Optional[T] = None
    confidence: Optional[float] = None
    edited: bool = False
    # Bounding box on the page (page, x, y, w, h) for click-to-highlight in the UI.
    bbox: Optional[list[float]] = None
    page: Optional[int] = None


# --- Repeating sub-tables ---------------------------------------------------

class Party(BaseModel):
    role: str  # SHIPPER | CONSIGNEE | NOTIFY | BROKER
    name: ExtractedField[str] = Field(default_factory=ExtractedField)
    address: ExtractedField[str] = Field(default_factory=ExtractedField)
    contact_tel: ExtractedField[str] = Field(default_factory=ExtractedField)
    contact_email: ExtractedField[str] = Field(default_factory=ExtractedField)


class ChargeLine(BaseModel):
    description: ExtractedField[str] = Field(default_factory=ExtractedField)
    basis: ExtractedField[str] = Field(default_factory=ExtractedField)
    rate: ExtractedField[float] = Field(default_factory=ExtractedField)
    amount: ExtractedField[float] = Field(default_factory=ExtractedField)


class GoodsLine(BaseModel):
    """Generic line item for invoices / packing lists."""
    line_no: ExtractedField[int] = Field(default_factory=ExtractedField)
    description: ExtractedField[str] = Field(default_factory=ExtractedField)
    hs_code: ExtractedField[str] = Field(default_factory=ExtractedField)
    quantity: ExtractedField[float] = Field(default_factory=ExtractedField)
    unit: ExtractedField[str] = Field(default_factory=ExtractedField)
    unit_price: ExtractedField[float] = Field(default_factory=ExtractedField)
    amount: ExtractedField[float] = Field(default_factory=ExtractedField)
    # packing-list extras
    cartons: ExtractedField[int] = Field(default_factory=ExtractedField)
    net_weight_kg: ExtractedField[float] = Field(default_factory=ExtractedField)
    gross_weight_kg: ExtractedField[float] = Field(default_factory=ExtractedField)
    dimensions_cm: ExtractedField[str] = Field(default_factory=ExtractedField)


# --- The unified extracted payload ------------------------------------------

class ExtractedDocument(BaseModel):
    """All fields we may extract across document types. Type-specific fields stay
    empty when not applicable. Stored as JSON alongside the relational summary so
    we keep full fidelity even as the schema evolves."""
    document_type: DocumentType = DocumentType.UNKNOWN
    transport_mode: TransportMode = TransportMode.UNKNOWN

    # Header / shared
    issuer_name: ExtractedField[str] = Field(default_factory=ExtractedField)
    reference_no: ExtractedField[str] = Field(default_factory=ExtractedField)
    issue_date: ExtractedField[str] = Field(default_factory=ExtractedField)

    # Join keys (see schemas/README.md)
    bl_number: ExtractedField[str] = Field(default_factory=ExtractedField)
    mbl_number: ExtractedField[str] = Field(default_factory=ExtractedField)
    hbl_number: ExtractedField[str] = Field(default_factory=ExtractedField)
    invoice_ref: ExtractedField[str] = Field(default_factory=ExtractedField)
    container_no: ExtractedField[str] = Field(default_factory=ExtractedField)
    seal_no: ExtractedField[str] = Field(default_factory=ExtractedField)

    # Routing / transport
    vessel_voyage: ExtractedField[str] = Field(default_factory=ExtractedField)
    flight_no: ExtractedField[str] = Field(default_factory=ExtractedField)
    port_of_loading: ExtractedField[str] = Field(default_factory=ExtractedField)
    port_of_discharge: ExtractedField[str] = Field(default_factory=ExtractedField)
    eta: ExtractedField[str] = Field(default_factory=ExtractedField)
    last_free_day: ExtractedField[str] = Field(default_factory=ExtractedField)

    # Cargo
    goods_description: ExtractedField[str] = Field(default_factory=ExtractedField)
    hs_code: ExtractedField[str] = Field(default_factory=ExtractedField)
    no_of_packages: ExtractedField[str] = Field(default_factory=ExtractedField)
    gross_weight: ExtractedField[str] = Field(default_factory=ExtractedField)
    measurement_cbm: ExtractedField[str] = Field(default_factory=ExtractedField)
    incoterms: ExtractedField[str] = Field(default_factory=ExtractedField)
    freight_terms: ExtractedField[str] = Field(default_factory=ExtractedField)
    cargo_value: ExtractedField[str] = Field(default_factory=ExtractedField)

    # Totals
    total_due: ExtractedField[float] = Field(default_factory=ExtractedField)
    currency: ExtractedField[str] = Field(default_factory=ExtractedField)

    # Repeating sections
    parties: list[Party] = Field(default_factory=list)
    charges: list[ChargeLine] = Field(default_factory=list)
    goods_lines: list[GoodsLine] = Field(default_factory=list)

    # Free-text catch-all (remarks, terms)
    remarks_text: ExtractedField[str] = Field(default_factory=ExtractedField)


# --- Document record (DB-backed) --------------------------------------------

class FreightCoding(BaseModel):
    """Analyst-supplied freight cost-coding inputs (PIDSA worksheet).

    Stored on the document so the coding sheet can be regenerated and audited.
    `cost_center_alloc` maps a charge-type key -> {cost_center -> amount}.
    `chemistry_kgs` maps a chemistry code -> KGS.
    """
    division: str = "MTY"                                  # MTY | OEM
    gl_codes: dict[str, str] = Field(default_factory=dict)  # charge-type -> G/L code (analyst-entered)
    chemistry_kgs: dict[str, float] = Field(default_factory=dict)
    cost_center_alloc: dict[str, dict[str, float]] = Field(default_factory=dict)
    approved_by: str = ""
    manager: str = ""


class DocumentRecord(BaseModel):
    """The top-level record tracked through the pipeline."""
    id: UUID = Field(default_factory=uuid4)
    original_filename: str
    blob_path_raw: str
    document_type: DocumentType = DocumentType.UNKNOWN
    status: ProcessingStatus = ProcessingStatus.UPLOADED
    uploaded_by: Optional[str] = None
    uploaded_at: datetime = Field(default_factory=_utcnow)
    extracted_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    page_count: Optional[int] = None
    min_confidence: Optional[float] = None  # lowest field confidence, for review triage
    error_message: Optional[str] = None
    extracted: Optional[ExtractedDocument] = None
    freight_coding: Optional[FreightCoding] = None


class AuditEntry(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    document_id: UUID
    action: ReviewAction
    actor: str
    field_name: Optional[str] = None
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    timestamp: datetime = Field(default_factory=_utcnow)
