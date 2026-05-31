"""Analyst review endpoints — open, edit fields, approve, reject, audit trail."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from shared.models import DocumentRecord, AuditEntry
from shared.enums import ProcessingStatus, ReviewAction
from app.auth import User, current_user
from app.repository import get_repository

router = APIRouter(prefix="/documents/{document_id}", tags=["review"])


class FieldEdit(BaseModel):
    field_path: str        # e.g. "bl_number" or "charges[2].amount"
    new_value: Any


def _require(document_id: UUID) -> DocumentRecord:
    rec = get_repository().get(document_id)
    if rec is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")
    return rec


@router.post("/open")
def open_for_review(document_id: UUID, user: User = Depends(current_user)) -> DocumentRecord:
    repo = get_repository()
    rec = _require(document_id)
    if rec.status not in (ProcessingStatus.EXTRACTED, ProcessingStatus.IN_REVIEW):
        raise HTTPException(status.HTTP_409_CONFLICT,
                            f"Cannot review a document in status '{rec.status.value}'")
    rec.status = ProcessingStatus.IN_REVIEW
    repo.update(rec)
    repo.add_audit(AuditEntry(document_id=document_id, action=ReviewAction.OPENED, actor=user.id))
    return rec


@router.patch("/fields")
def edit_field(document_id: UUID, edit: FieldEdit, user: User = Depends(current_user)) -> DocumentRecord:
    """Record an analyst correction. The field_path resolution against the nested
    ExtractedDocument is intentionally simple here (top-level fields); nested paths
    like charges[i].amount are handled by the UI sending the resolved path and the
    worker/repository persisting the JSON. Audited regardless."""
    repo = get_repository()
    rec = _require(document_id)
    if rec.extracted is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Document has no extracted data yet")

    old_value = None
    field = getattr(rec.extracted, edit.field_path, None)
    if field is not None and hasattr(field, "value"):
        old_value = field.value
        field.value = edit.new_value
        field.edited = True
    # Nested paths (charges[i].x) are persisted via the full JSON by the UI; we
    # still audit the change here.

    repo.update(rec)
    repo.add_audit(AuditEntry(
        document_id=document_id, action=ReviewAction.EDITED_FIELD, actor=user.id,
        field_name=edit.field_path,
        old_value=None if old_value is None else str(old_value),
        new_value=None if edit.new_value is None else str(edit.new_value),
    ))
    return rec


@router.post("/approve")
def approve(document_id: UUID, user: User = Depends(current_user)) -> DocumentRecord:
    repo = get_repository()
    rec = _require(document_id)
    if rec.status != ProcessingStatus.IN_REVIEW:
        raise HTTPException(status.HTTP_409_CONFLICT, "Open the document for review first")
    rec.status = ProcessingStatus.APPROVED
    rec.reviewed_by = user.id
    rec.reviewed_at = datetime.now(timezone.utc)
    repo.update(rec)
    repo.add_audit(AuditEntry(document_id=document_id, action=ReviewAction.APPROVED, actor=user.id))
    return rec


@router.post("/reject")
def reject(document_id: UUID, reason: str = "", user: User = Depends(current_user)) -> DocumentRecord:
    repo = get_repository()
    rec = _require(document_id)
    rec.status = ProcessingStatus.REJECTED
    rec.reviewed_by = user.id
    rec.reviewed_at = datetime.now(timezone.utc)
    rec.error_message = reason or rec.error_message
    repo.update(rec)
    repo.add_audit(AuditEntry(
        document_id=document_id, action=ReviewAction.REJECTED, actor=user.id, new_value=reason))
    return rec


@router.get("/audit")
def audit_trail(document_id: UUID, user: User = Depends(current_user)) -> list[AuditEntry]:
    _require(document_id)
    return get_repository().list_audit(document_id)
