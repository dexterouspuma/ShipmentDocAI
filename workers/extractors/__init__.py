"""Extractor implementations. `build_extractor()` picks one based on environment."""
from __future__ import annotations

import os

from .base import Extractor
from .stub import StubExtractor


def build_extractor() -> Extractor:
    """StubExtractor when no agent endpoint configured, AgentExtractor otherwise.

    When running in-process inside the API, reads from app.config.settings so
    .env values are available. Falls back to os.environ for the standalone worker.
    """
    try:
        from app.config import settings
        endpoint = settings.azure_ai_endpoint
    except ImportError:
        endpoint = os.environ.get("AZURE_AI_ENDPOINT", "")

    if not endpoint:
        return StubExtractor()
    from .agent import AgentExtractor
    return AgentExtractor()
