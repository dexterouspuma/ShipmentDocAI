"""Blob storage abstraction.

`get_storage()` returns a local-folder implementation when ENVIRONMENT=local
(so you can run with zero Azure), and the Azure Blob implementation otherwise.
Both satisfy the same small interface the routers depend on.
"""
from __future__ import annotations

import pathlib
from abc import ABC, abstractmethod

from app.config import settings


class StorageClient(ABC):
    @abstractmethod
    def save_raw(self, blob_name: str, data: bytes) -> str:
        """Persist raw upload bytes; return the blob path/uri stored on the record."""

    @abstractmethod
    def read(self, blob_path: str) -> bytes:
        ...


class LocalStorage(StorageClient):
    """Writes to a local folder. For development only."""

    def __init__(self, base_dir: str):
        self.base = pathlib.Path(base_dir)
        self.base.mkdir(parents=True, exist_ok=True)

    def save_raw(self, blob_name: str, data: bytes) -> str:
        path = self.base / blob_name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return f"local://{blob_name}"

    def read(self, blob_path: str) -> bytes:
        name = blob_path.replace("local://", "")
        return (self.base / name).read_bytes()


class AzureBlobStorage(StorageClient):
    """Azure Blob Storage. Prefers Managed Identity; falls back to conn string."""

    def __init__(self):
        from azure.storage.blob import BlobServiceClient
        if settings.storage_connection_string:
            self._svc = BlobServiceClient.from_connection_string(
                settings.storage_connection_string)
        else:
            from azure.identity import DefaultAzureCredential
            account_url = f"https://{settings.storage_account_name}.blob.core.windows.net"
            self._svc = BlobServiceClient(account_url, credential=DefaultAzureCredential())
        self._container = settings.storage_container_raw

    def save_raw(self, blob_name: str, data: bytes) -> str:
        client = self._svc.get_blob_client(container=self._container, blob=blob_name)
        client.upload_blob(data, overwrite=True)
        return f"{self._container}/{blob_name}"

    def read(self, blob_path: str) -> bytes:
        container, _, name = blob_path.partition("/")
        client = self._svc.get_blob_client(container=container, blob=name)
        return client.download_blob().readall()


_instance: StorageClient | None = None


def get_storage() -> StorageClient:
    global _instance
    if _instance is None:
        if settings.is_local or not settings.storage_account_name and not settings.storage_connection_string:
            _instance = LocalStorage(settings.local_storage_dir)
        else:
            _instance = AzureBlobStorage()
    return _instance
