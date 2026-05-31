"""Freight cost-coding endpoints — config for the form, plus get/save inputs."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from pydantic import BaseModel

from shared.models import DocumentRecord, FreightCoding
from app.auth import User, current_user
from app.repository import get_repository
from app.services import freight_coding
from app.services import freight_coding_config as cfg
from app.services import gl_defaults

router = APIRouter(tags=["freight-coding"])


@router.get("/meta/freight-coding-config")
def freight_config(user: User = Depends(current_user)) -> dict:
    """Static lookups the review form renders (charge rows, cost centers, chemistries)."""
    return {
        "charge_rows": [{"key": k, "label": l, "gl_code": cfg.GL_CODE_BY_CHARGE.get(k, "")}
                        for k, l in cfg.CHARGE_ROWS],
        "cost_centers": cfg.COST_CENTERS,
        "chemistries": [{"code": code, "label": label} for label, code in cfg.CHEMISTRY_ROWS],
        "divisions": ["MTY", "OEM"],
    }


class GLDefaults(BaseModel):
    gl_codes: dict[str, str] = {}


@router.get("/meta/gl-defaults")
def get_gl_defaults(user: User = Depends(current_user)) -> GLDefaults:
    """The saved charge-type -> G/L code defaults."""
    return GLDefaults(gl_codes=gl_defaults.get_defaults())


@router.put("/meta/gl-defaults")
def save_gl_defaults(payload: GLDefaults, user: User = Depends(current_user)) -> GLDefaults:
    """Save the analyst's G/L codes as defaults for future documents."""
    return GLDefaults(gl_codes=gl_defaults.save_defaults(payload.gl_codes))


def _require(document_id: UUID) -> DocumentRecord:
    rec = get_repository().get(document_id)
    if rec is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")
    return rec


@router.get("/documents/{document_id}/freight-coding")
def get_freight_coding(document_id: UUID, user: User = Depends(current_user)) -> dict:
    """Saved coding inputs (if any) + the auto-coded charge totals to allocate.

    G/L codes are pre-filled from saved defaults where the document has none."""
    rec = _require(document_id)
    coding = rec.freight_coding or FreightCoding()
    coding.gl_codes = gl_defaults.merge_gl_codes(coding.gl_codes)
    return {
        "coding": coding,
        "charge_rows": freight_coding.charge_totals_for_ui(rec),
    }


@router.put("/documents/{document_id}/freight-coding")
def save_freight_coding(document_id: UUID, coding: FreightCoding,
                        user: User = Depends(current_user)) -> DocumentRecord:
    repo = get_repository()
    rec = _require(document_id)
    rec.freight_coding = coding
    repo.update(rec)
    return rec
