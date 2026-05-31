"""Extractor interface + shared helpers.

An Extractor turns raw PDF bytes into a populated `ExtractedDocument` (from the
shared models), with per-field confidence scores. Concrete implementations:
StubExtractor (local) and DocumentIntelligenceExtractor (Azure).
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from shared.models import ExtractedDocument, ExtractedField
from shared.enums import DocumentType


class Extractor(ABC):
    @abstractmethod
    def extract(self, data: bytes, document_type: DocumentType) -> ExtractedDocument:
        """Analyze the document and return populated fields with confidences."""


def min_confidence(doc: ExtractedDocument) -> Optional[float]:
    """Lowest confidence across all populated scalar + line-item fields.

    Drives review triage (documents/min_confidence column and the review queue).
    """
    scores: list[float] = []

    def collect(obj) -> None:
        for value in vars(obj).values():
            if isinstance(value, ExtractedField):
                if value.confidence is not None and value.value not in (None, ""):
                    scores.append(value.confidence)
            elif isinstance(value, list):
                for item in value:
                    if hasattr(item, "__dict__"):
                        collect(item)

    collect(doc)
    return min(scores) if scores else None
