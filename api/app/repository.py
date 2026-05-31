"""Data-access layer.

Defines the repository interface the routers use, plus an in-memory implementation
so the API runs locally with no database. The Azure SQL implementation (pyodbc
against the schema in db/) is stubbed with TODOs to fill in after provisioning.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional
from uuid import UUID

from shared.models import DocumentRecord, AuditEntry
from shared.enums import ProcessingStatus
from app.config import settings


class Repository(ABC):
    @abstractmethod
    def create(self, record: DocumentRecord) -> DocumentRecord: ...
    @abstractmethod
    def get(self, document_id: UUID) -> Optional[DocumentRecord]: ...
    @abstractmethod
    def list(self, status: Optional[ProcessingStatus] = None) -> list[DocumentRecord]: ...
    @abstractmethod
    def update(self, record: DocumentRecord) -> DocumentRecord: ...
    @abstractmethod
    def add_audit(self, entry: AuditEntry) -> None: ...
    @abstractmethod
    def list_audit(self, document_id: UUID) -> list[AuditEntry]: ...


class InMemoryRepository(Repository):
    """Process-local store. Data is lost on restart — development only."""

    def __init__(self):
        self._docs: dict[UUID, DocumentRecord] = {}
        self._audit: list[AuditEntry] = []

    def create(self, record: DocumentRecord) -> DocumentRecord:
        self._docs[record.id] = record
        return record

    def get(self, document_id: UUID) -> Optional[DocumentRecord]:
        return self._docs.get(document_id)

    def list(self, status: Optional[ProcessingStatus] = None) -> list[DocumentRecord]:
        docs = list(self._docs.values())
        if status:
            docs = [d for d in docs if d.status == status]
        return sorted(docs, key=lambda d: d.uploaded_at, reverse=True)

    def update(self, record: DocumentRecord) -> DocumentRecord:
        self._docs[record.id] = record
        return record

    def add_audit(self, entry: AuditEntry) -> None:
        self._audit.append(entry)

    def list_audit(self, document_id: UUID) -> list[AuditEntry]:
        return [a for a in self._audit if a.document_id == document_id]


class AzureSqlRepository(Repository):
    """pyodbc-backed implementation against db/schema.sql.

    TODO: implement once Azure SQL is provisioned. Map DocumentRecord <-> the
    `documents` row (+ extracted_json), and the child tables for parties/charges/
    goods lines. Use MERGE/UPSERT on update. Keep the same method contract so the
    routers do not change.
    """

    def __init__(self):
        self._conn_str = settings.sql_connection_string
        if not self._conn_str:
            raise RuntimeError("SQL_CONNECTION_STRING required for AzureSqlRepository")

    def create(self, record): raise NotImplementedError("AzureSqlRepository pending provisioning")
    def get(self, document_id): raise NotImplementedError
    def list(self, status=None): raise NotImplementedError
    def update(self, record): raise NotImplementedError
    def add_audit(self, entry): raise NotImplementedError
    def list_audit(self, document_id): raise NotImplementedError


_instance: Repository | None = None


def get_repository() -> Repository:
    global _instance
    if _instance is None:
        _instance = InMemoryRepository() if settings.is_local else AzureSqlRepository()
    return _instance
