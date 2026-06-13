"""Application settings, loaded from environment / .env (see .env.example).

Also bootstraps the import path so the repo-root `shared` package is importable
whether you run from `api/` locally or from the container.
"""
import sys
import pathlib

# Make repo-root `shared` importable: api/app/config.py -> api -> repo root
_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "local"          # local | dev | prod
    bypass_auth: bool = False           # skip JWT validation (dev only)
    log_level: str = "INFO"
    low_confidence_threshold: float = 0.80

    # Storage
    storage_account_name: str = ""
    storage_container_raw: str = "raw"
    storage_container_processed: str = "processed"
    storage_connection_string: str = ""
    # Local-mode fallback: where uploaded PDFs are written when environment=local
    local_storage_dir: str = str(_REPO_ROOT / ".localdata" / "blobs")

    # Service Bus
    servicebus_namespace: str = ""
    servicebus_queue_extraction: str = "extraction"
    servicebus_connection_string: str = ""

    # Document Intelligence
    docintel_endpoint: str = ""
    docintel_key: str = ""

    # SQL
    sql_connection_string: str = ""

    # Azure AI Agent
    azure_ai_endpoint: str = ""
    azure_ai_agent_name: str = ""
    azure_ai_agent_version: str = "1"

    # Entra ID auth
    entra_tenant_id: str = ""
    entra_api_client_id: str = ""
    entra_api_audience: str = ""

    @property
    def is_local(self) -> bool:
        return self.environment == "local"


settings = Settings()
