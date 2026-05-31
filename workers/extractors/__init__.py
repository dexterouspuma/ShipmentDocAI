"""Extractor implementations. `build_extractor()` picks one based on environment."""
from __future__ import annotations

import os

from .base import Extractor
from .stub import StubExtractor


def build_extractor() -> Extractor:
    """StubExtractor locally (no Azure), Document Intelligence otherwise."""
    if os.environ.get("ENVIRONMENT", "local") == "local":
        return StubExtractor()
    from .document_intelligence import DocumentIntelligenceExtractor
    return DocumentIntelligenceExtractor()
