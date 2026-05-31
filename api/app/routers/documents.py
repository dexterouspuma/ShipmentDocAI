"""Document intake + listing endpoints."""
from __future__ import annotations

import io
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse

from shared.models import DocumentRecord
from shared.enums import DocumentType, ProcessingStatus
from app.auth import User, current_user
from app.repository import get_repository
from app.services.storage import get_storage
from app.services.queue import get_queue

router = APIRouter(prefix="/documents", tags=["documents"])


def _page_count(data: bytes) -> Optional[int]:
    try:
        from pypdf import PdfReader
        return len(PdfReader(io.BytesIO(data)).pages)
    except Exception:  # noqa: BLE001
        return None


@router.post("", status_code=status.HTTP_201_CREATED)
def upload_document(
    file: UploadFile = File(...),
    document_type: DocumentType = DocumentType.UNKNOWN,
    user: User = Depends(current_user),
) -> DocumentRecord:
    """Accept a PDF, store it, create the record, and enqueue extraction."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Only PDF uploads are supported")

    data = file.file.read()
    if not data:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Empty file")

    repo, storage, queue = get_repository(), get_storage(), get_queue()

    record = DocumentRecord(
        original_filename=file.filename,
        blob_path_raw="",  # set after save
        document_type=document_type,
        uploaded_by=user.id,
        page_count=_page_count(data),
    )
    blob_name = f"{record.id}/{file.filename}"
    record.blob_path_raw = storage.save_raw(blob_name, data)
    record.status = ProcessingStatus.QUEUED
    repo.create(record)

    queue.enqueue_extraction(str(record.id))
    return record


@router.get("")
def list_documents(
    status_filter: Optional[ProcessingStatus] = None,
    user: User = Depends(current_user),
) -> list[DocumentRecord]:
    return get_repository().list(status=status_filter)


@router.get("/{document_id}")
def get_document(document_id: UUID, user: User = Depends(current_user)) -> DocumentRecord:
    record = get_repository().get(document_id)
    if record is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")
    return record


@router.get("/{document_id}/file")
def get_document_file(document_id: UUID, user: User = Depends(current_user)):
    """Stream the original PDF for the review UI's side-by-side viewer."""
    record = get_repository().get(document_id)
    if record is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")
    try:
        data = get_storage().read(record.blob_path_raw)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"File not available: {exc}") from exc
    return StreamingResponse(
        io.BytesIO(data),
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{record.original_filename}"'},
    )
