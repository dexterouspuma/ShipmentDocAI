"""Persisted default G/L code mapping (charge-type -> G/L code).

Lets analysts save the codes they enter once and have them pre-fill future
documents. Local mode persists to a JSON file under .localdata so defaults
survive restarts.

NOTE (Azure): a file is per-replica and ephemeral. Before production, back this
with a shared store (a small SQL table or a blob) so all API replicas agree.
"""
from __future__ import annotations

import json
import pathlib
import threading

from app.config import settings

_lock = threading.Lock()


def _path() -> pathlib.Path:
    base = pathlib.Path(settings.local_storage_dir).parent  # .localdata
    base.mkdir(parents=True, exist_ok=True)
    return base / "gl_defaults.json"


def get_defaults() -> dict[str, str]:
    """Saved charge-type -> G/L code defaults (empty if none saved yet)."""
    p = _path()
    if not p.exists():
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return {str(k): str(v) for k, v in data.items() if v}
    except (ValueError, OSError):
        return {}


def save_defaults(mapping: dict[str, str]) -> dict[str, str]:
    """Persist non-empty charge-type -> G/L code entries; returns what was saved."""
    cleaned = {str(k): str(v).strip() for k, v in mapping.items() if str(v).strip()}
    with _lock:
        _path().write_text(json.dumps(cleaned, indent=2), encoding="utf-8")
    return cleaned


def merge_gl_codes(doc_codes: dict[str, str], defaults: dict[str, str] | None = None) -> dict[str, str]:
    """Effective G/L codes: this document's entries override saved defaults."""
    if defaults is None:
        defaults = get_defaults()
    merged = dict(defaults)
    merged.update({k: v for k, v in (doc_codes or {}).items() if v})
    return merged
