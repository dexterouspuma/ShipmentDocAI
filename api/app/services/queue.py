"""Service Bus abstraction for enqueuing extraction jobs.

Local mode just logs the message (and optionally calls an in-process handler) so
the API runs without Azure. Azure mode sends to the real Service Bus queue, which
the separate worker process consumes.
"""
from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from typing import Callable, Optional

from app.config import settings

log = logging.getLogger("queue")


class QueueClient(ABC):
    @abstractmethod
    def enqueue_extraction(self, document_id: str) -> None:
        ...


class LocalQueue(QueueClient):
    """No real queue. Optionally invokes an in-process handler for end-to-end
    local testing without running the separate worker."""

    def __init__(self, handler: Optional[Callable[[str], None]] = None):
        self.handler = handler

    def enqueue_extraction(self, document_id: str) -> None:
        log.info("LocalQueue: extraction enqueued for %s", document_id)
        if self.handler:
            self.handler(document_id)


class AzureServiceBusQueue(QueueClient):
    def __init__(self):
        self._conn = settings.servicebus_connection_string
        self._namespace = settings.servicebus_namespace
        self._queue = settings.servicebus_queue_extraction

    def _client(self):
        from azure.servicebus import ServiceBusClient
        if self._conn:
            return ServiceBusClient.from_connection_string(self._conn)
        from azure.identity import DefaultAzureCredential
        fqdn = f"{self._namespace}.servicebus.windows.net"
        return ServiceBusClient(fqdn, credential=DefaultAzureCredential())

    def enqueue_extraction(self, document_id: str) -> None:
        from azure.servicebus import ServiceBusMessage
        body = json.dumps({"document_id": document_id, "task": "extract"})
        with self._client() as client:
            sender = client.get_queue_sender(queue_name=self._queue)
            with sender:
                sender.send_messages(ServiceBusMessage(body))
        log.info("Enqueued extraction for %s", document_id)


_instance: QueueClient | None = None


def get_queue() -> QueueClient:
    global _instance
    if _instance is None:
        _instance = LocalQueue() if settings.is_local else AzureServiceBusQueue()
    return _instance
