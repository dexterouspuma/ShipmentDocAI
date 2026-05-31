"""Extraction processing — the core, with injected dependencies.

`process_document` is deliberately dependency-injected (repo, storage, extractor)
so it runs the same way in three contexts:
  - local end-to-end: called in-process by the API's LocalQueue handler
  - Azure: called by worker.py for each Service Bus message
  - tests: called with an in-memory repo + stub extractor
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from uuid import UUID

from shared.enums import ProcessingStatus
from extractors.base import Extractor, min_confidence

log = logging.getLogger("processor")


def process_document(document_id: str, *, repo, storage, extractor: Extractor) -> None:
    doc_uuid = UUID(str(document_id))
    record = repo.get(doc_uuid)
    if record is None:
        log.warning("process_document: %s not found", document_id)
        return

    record.status = ProcessingStatus.EXTRACTING
    repo.update(record)

    try:
        data = storage.read(record.blob_path_raw)
        extracted = extractor.extract(data, record.document_type)

        record.extracted = extracted
        record.document_type = extracted.document_type
        record.status = ProcessingStatus.EXTRACTED
        record.extracted_at = datetime.now(timezone.utc)
        record.error_message = None
        # Triage signal for the review queue.
        record.min_confidence = min_confidence(extracted)
        repo.update(record)
        log.info("Extracted %s (type=%s, min_conf=%s)",
                 document_id, extracted.document_type.value, record.min_confidence)
    except Exception as exc:  # noqa: BLE001
        record.status = ProcessingStatus.EXTRACTION_FAILED
        record.error_message = str(exc)
        repo.update(record)
        log.exception("Extraction failed for %s", document_id)
        raise
