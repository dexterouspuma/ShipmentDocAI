"""Pytest fixtures and environment setup for the API tests.

Forces ENVIRONMENT=local so tests run against the in-memory repository,
local-folder storage, and the no-op queue — no Azure required.
"""
import os
import pathlib
import sys

os.environ.setdefault("ENVIRONMENT", "local")

# Ensure `app` (api/) is importable when pytest is run from anywhere.
_API_DIR = pathlib.Path(__file__).resolve().parents[1]
if str(_API_DIR) not in sys.path:
    sys.path.insert(0, str(_API_DIR))

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture()
def sample_pdf() -> bytes:
    """A real arrival-notice sample, falling back to any sample PDF."""
    samples = _API_DIR.parent / "samples"
    candidates = sorted((samples / "arrival-notice").glob("*.pdf")) or \
        sorted(samples.rglob("*.pdf"))
    assert candidates, "No sample PDFs found under samples/"
    return candidates[0].read_bytes()
