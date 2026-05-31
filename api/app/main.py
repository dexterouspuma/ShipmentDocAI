"""FastAPI application entry point."""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import documents, review, cover_sheet, freight_coding

logging.basicConfig(level=settings.log_level)

app = FastAPI(
    title="Shipment Document AI",
    version="0.1.0",
    description="Ingest logistics PDFs, extract data, analyst review, cover sheets.",
)

# Frontend dev server / Static Web App origin. Tighten for production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"] if settings.is_local else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents.router)
app.include_router(review.router)
app.include_router(cover_sheet.router)
app.include_router(freight_coding.router)


def _wire_local_extraction() -> None:
    """In local mode, run extraction in-process so uploads become 'extracted'
    without the standalone worker. In Azure, the worker consumes Service Bus.

    Wired at import time (not a startup event) so it applies whether or not the
    TestClient is used as a context manager."""
    if not settings.is_local:
        return
    import sys
    import pathlib
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "workers"))
    from extractors import build_extractor
    from processor import process_document
    from app.repository import get_repository
    from app.services.storage import get_storage
    from app.services.queue import get_queue

    extractor = build_extractor()

    def handler(document_id: str) -> None:
        process_document(document_id, repo=get_repository(),
                         storage=get_storage(), extractor=extractor)

    q = get_queue()
    if hasattr(q, "handler"):
        q.handler = handler  # LocalQueue runs this on enqueue


_wire_local_extraction()


@app.get("/health", tags=["meta"])
def health() -> dict:
    return {"status": "ok", "environment": settings.environment}
