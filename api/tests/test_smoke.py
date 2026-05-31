"""End-to-end smoke tests for the API (local mode, no Azure).

Covers: health, upload (real sample PDF), list, get, and cover-sheet generation
in both PDF and Excel formats.
"""
from shared.models import DocumentRecord, ExtractedDocument, ExtractedField
from shared.enums import DocumentType, ProcessingStatus, CoverSheetFormat
from app.services import cover_sheet


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_upload_list_get(client, sample_pdf):
    r = client.post(
        "/documents?document_type=arrival_notice",
        files={"file": ("arrival_notice.pdf", sample_pdf, "application/pdf")},
    )
    assert r.status_code == 201, r.text
    doc = r.json()
    # In local mode, extraction runs in-process on enqueue, so the doc is already
    # 'extracted' by the time the upload returns. (In Azure it would be 'queued'.)
    assert doc["status"] == "extracted"
    assert doc["page_count"] and doc["page_count"] >= 1
    doc_id = doc["id"]

    r = client.get("/documents")
    assert r.status_code == 200
    assert any(d["id"] == doc_id for d in r.json())

    r = client.get(f"/documents/{doc_id}")
    assert r.status_code == 200
    assert r.json()["original_filename"] == "arrival_notice.pdf"

    # The review UI fetches the original PDF from this endpoint.
    r = client.get(f"/documents/{doc_id}/file")
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    assert r.content[:4] == b"%PDF"


def test_upload_rejects_non_pdf(client):
    r = client.post(
        "/documents",
        files={"file": ("notes.txt", b"hello", "text/plain")},
    )
    assert r.status_code == 400


def _approved_record() -> DocumentRecord:
    ed = ExtractedDocument(document_type=DocumentType.ARRIVAL_NOTICE)
    ed.issuer_name = ExtractedField(value="EVERGREEN LINE", confidence=0.99)
    ed.bl_number = ExtractedField(value="EGLV143026058813", confidence=0.97)
    ed.total_due = ExtractedField(value=756.00, confidence=0.95)
    return DocumentRecord(
        original_filename="x.pdf", blob_path_raw="local://x", extracted=ed,
        document_type=DocumentType.ARRIVAL_NOTICE, status=ProcessingStatus.APPROVED,
    )


def test_cover_sheet_pdf():
    data, filename, content_type = cover_sheet.generate(_approved_record(), CoverSheetFormat.PDF)
    assert filename.endswith(".pdf")
    assert content_type == "application/pdf"
    assert data[:4] == b"%PDF"               # valid PDF header
    assert len(data) > 500


def test_cover_sheet_excel():
    data, filename, content_type = cover_sheet.generate(_approved_record(), CoverSheetFormat.EXCEL)
    assert filename.endswith(".xlsx")
    assert data[:2] == b"PK"                  # xlsx is a zip; PK header
    assert len(data) > 500
