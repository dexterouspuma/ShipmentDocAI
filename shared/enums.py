"""Fixed value sets used across the app (stored in DB, sent over the API)."""
from enum import Enum


class DocumentType(str, Enum):
    """The document types we ingest. Drives which extraction model is used."""
    ARRIVAL_NOTICE = "arrival_notice"
    COMMERCIAL_INVOICE = "commercial_invoice"
    CARRIER_INVOICE = "carrier_invoice"
    PACKING_LIST = "packing_list"
    BOL = "bol"
    UNKNOWN = "unknown"  # set on intake before type is detected


class TransportMode(str, Enum):
    """Arrival notices (and some BOLs) vary by mode; switches header fields."""
    OCEAN_FCL = "ocean_fcl"
    OCEAN_LCL = "ocean_lcl"
    AIR = "air"
    UNKNOWN = "unknown"


class ProcessingStatus(str, Enum):
    """Lifecycle of a document from upload to completion."""
    UPLOADED = "uploaded"          # stored in blob, not yet queued
    QUEUED = "queued"              # message placed on Service Bus
    EXTRACTING = "extracting"      # worker is calling Document Intelligence
    EXTRACTED = "extracted"        # fields persisted, awaiting review
    EXTRACTION_FAILED = "extraction_failed"  # moved to dead-letter / needs retry
    IN_REVIEW = "in_review"        # an analyst has it open
    APPROVED = "approved"          # analyst approved the extracted data
    REJECTED = "rejected"          # analyst rejected the document
    COVER_SHEET_GENERATED = "cover_sheet_generated"


class ReviewAction(str, Enum):
    """What an analyst did, recorded in the audit log."""
    OPENED = "opened"
    EDITED_FIELD = "edited_field"
    APPROVED = "approved"
    REJECTED = "rejected"
    SENT_BACK = "sent_back"
    GENERATED_COVER_SHEET = "generated_cover_sheet"


class CoverSheetFormat(str, Enum):
    """Analyst-selectable output format for cover sheets."""
    PDF = "pdf"
    EXCEL = "excel"
