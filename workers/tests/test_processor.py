"""Unit tests for the extraction processor using fakes (in-memory repo + stub)."""
from typing import Optional
from uuid import UUID

from shared.models import DocumentRecord
from shared.enums import DocumentType, ProcessingStatus
from extractors.stub import StubExtractor
from extractors.base import min_confidence
from processor import process_document


class FakeRepo:
    def __init__(self):
        self._d: dict[UUID, DocumentRecord] = {}

    def create(self, rec):
        self._d[rec.id] = rec
        return rec

    def get(self, doc_id) -> Optional[DocumentRecord]:
        return self._d.get(doc_id)

    def update(self, rec):
        self._d[rec.id] = rec
        return rec


class FakeStorage:
    def read(self, blob_path: str) -> bytes:
        return b"%PDF-fake-bytes"


def test_process_document_populates_and_flags_low_confidence():
    repo, storage = FakeRepo(), FakeStorage()
    rec = DocumentRecord(original_filename="an.pdf", blob_path_raw="local://an.pdf",
                         document_type=DocumentType.ARRIVAL_NOTICE)
    repo.create(rec)

    process_document(str(rec.id), repo=repo, storage=storage, extractor=StubExtractor())

    out = repo.get(rec.id)
    assert out.status == ProcessingStatus.EXTRACTED
    assert out.extracted is not None
    assert out.extracted.bl_number.value == "EGLV143026058813"
    assert out.extracted.bl_number.confidence == 0.97
    # The stub seeds a low-confidence goods_description (0.62) -> drives min_confidence.
    assert out.min_confidence is not None and out.min_confidence < 0.8
    assert len(out.extracted.parties) == 3
    assert len(out.extracted.charges) == 2


def test_min_confidence_helper():
    doc = StubExtractor().extract(b"x", DocumentType.ARRIVAL_NOTICE)
    assert abs(min_confidence(doc) - 0.62) < 1e-9


def test_failed_extraction_sets_status():
    class Boom(StubExtractor):
        def extract(self, data, document_type):
            raise ValueError("boom")

    repo, storage = FakeRepo(), FakeStorage()
    rec = DocumentRecord(original_filename="x.pdf", blob_path_raw="local://x.pdf",
                         document_type=DocumentType.BOL)
    repo.create(rec)

    try:
        process_document(str(rec.id), repo=repo, storage=storage, extractor=Boom())
    except ValueError:
        pass

    out = repo.get(rec.id)
    assert out.status == ProcessingStatus.EXTRACTION_FAILED
    assert "boom" in (out.error_message or "")
