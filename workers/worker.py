"""Standalone extraction worker (Azure).

Consumes the Service Bus extraction queue and processes each document. Deployed as
its own Container App that autoscales on queue depth. Reuses the API's repository
and storage so both deployables read/write the same Azure SQL + Blob.

Run:  python worker.py
"""
from __future__ import annotations

import json
import logging
import os
import sys
import pathlib

# Make repo-root `shared` and the api `app` package importable.
_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
for p in (_REPO_ROOT, _REPO_ROOT / "api"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from app.config import settings           # noqa: E402
from app.repository import get_repository  # noqa: E402
from app.services.storage import get_storage  # noqa: E402
from extractors import build_extractor    # noqa: E402
from processor import process_document    # noqa: E402

logging.basicConfig(level=settings.log_level)
log = logging.getLogger("worker")


def _handle(body: str, repo, storage, extractor) -> None:
    msg = json.loads(body)
    document_id = msg["document_id"]
    process_document(document_id, repo=repo, storage=storage, extractor=extractor)


def main() -> None:
    if settings.is_local:
        log.warning("ENVIRONMENT=local: in local mode extraction runs in-process via "
                    "the API. The standalone worker targets Azure Service Bus.")
        return

    from azure.servicebus import ServiceBusClient
    from azure.identity import DefaultAzureCredential

    repo, storage, extractor = get_repository(), get_storage(), build_extractor()
    queue = settings.servicebus_queue_extraction

    if settings.servicebus_connection_string:
        client = ServiceBusClient.from_connection_string(settings.servicebus_connection_string)
    else:
        fqdn = f"{settings.servicebus_namespace}.servicebus.windows.net"
        client = ServiceBusClient(fqdn, credential=DefaultAzureCredential())

    log.info("Worker started; listening on queue '%s'", queue)
    with client:
        receiver = client.get_queue_receiver(queue_name=queue, max_wait_time=30)
        with receiver:
            for message in receiver:
                try:
                    _handle(str(message), repo, storage, extractor)
                    receiver.complete_message(message)
                except Exception:  # noqa: BLE001
                    log.exception("Message processing failed; abandoning for retry")
                    receiver.abandon_message(message)


if __name__ == "__main__":
    main()
