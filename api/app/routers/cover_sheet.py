"""Cover-sheet generation endpoint (analyst picks PDF or Excel)."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

import io

from shared.enums import ProcessingStatus, ReviewAction, CoverSheetFormat
from shared.models import AuditEntry
from app.auth import User, current_user
from app.repository import get_repository
from app.services import cover_sheet

router = APIRouter(prefix="/documents/{document_id}", tags=["cover-sheet"])


@router.post("/cover-sheet")
def generate_cover_sheet(
    document_id: UUID,
    fmt: CoverSheetFormat = CoverSheetFormat.PDF,
    user: User = Depends(current_user),
):
    repo = get_repository()
    rec = repo.get(document_id)
    if rec is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")
    if rec.status not in (ProcessingStatus.APPROVED, ProcessingStatus.COVER_SHEET_GENERATED):
        raise HTTPException(status.HTTP_409_CONFLICT,
                            "Document must be approved before generating a cover sheet")

    data, filename, content_type = cover_sheet.generate(rec, fmt)

    rec.status = ProcessingStatus.COVER_SHEET_GENERATED
    repo.update(rec)
    repo.add_audit(AuditEntry(
        document_id=document_id, action=ReviewAction.GENERATED_COVER_SHEET,
        actor=user.id, new_value=fmt.value))

    return StreamingResponse(
        io.BytesIO(data),
        media_type=content_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
