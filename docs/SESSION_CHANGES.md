# ShipmentDocAI — Session Changes & Lessons Learned

## What Was Changed and Why

---

### 1. Replaced Document Intelligence with Azure AI Agent

**Files changed:**
- `workers/extractors/agent.py` — created new extractor
- `workers/extractors/__init__.py` — switched `build_extractor()` to use agent
- `workers/requirements.txt` — swapped `azure-ai-documentintelligence` for `azure-ai-projects` and `pypdf`
- `api/.env` — replaced `DOCINTEL_*` vars with `AZURE_AI_*` vars

**Why:** The Document Intelligence custom models had never been trained (all `TODO` comments). The user already had a working Azure AI Agent (`TESTAGENT0612`), so we wired that in instead.

**Lesson:** Document Intelligence requires custom model training per document type in Azure AI Studio before it works. An AI Agent with a good prompt can replace this and requires no training setup.

---

### 2. Fixed PDF Extraction — Text Instead of Base64

**File changed:** `workers/extractors/agent.py`

**Problem:** The first version of the agent extractor sent the PDF as a base64-encoded string. The agent is a text-based model — it cannot decode or read raw binary PDF data.

**Fix:** Use `pypdf` to extract readable text from the PDF first, then send that text to the agent.

**Flow:**
```
PDF bytes → pypdf.PdfReader → plain text → agent prompt → JSON response → ExtractedDocument
```

**Lesson:** AI Agents are text-in/text-out. Always extract text from binary files before sending to an agent. For image-heavy PDFs (scanned documents), you would need OCR first (e.g., Azure Document Intelligence's `prebuilt-layout` model just for OCR, then send the text to your agent).

---

### 3. Auth Bypass for Local Dev

**Files changed:**
- `api/app/config.py` — added `bypass_auth: bool = False`
- `api/app/auth.py` — skip JWT validation when `bypass_auth=True`
- `api/.env` — added `BYPASS_AUTH=true`

**Why:** `ENVIRONMENT=dev` enables the real agent but also enables Entra ID JWT validation. Without an Entra app registration set up, every API request returns `401 Unauthorized`.

**Lesson for production:** Remove `BYPASS_AUTH=true` and fill in `ENTRA_TENANT_ID`, `ENTRA_API_CLIENT_ID`, and `ENTRA_API_AUDIENCE` before deploying. Never leave auth bypassed in production.

---

### 4. Local Fallbacks for Azure Services

**Files changed:**
- `api/app/repository.py` — use `InMemoryRepository` when `SQL_CONNECTION_STRING` is empty
- `api/app/services/storage.py` — use `LocalStorage` when storage config is empty
- `api/app/services/queue.py` — use `LocalQueue` when Service Bus config is empty

**Why:** The original code checked `ENVIRONMENT=local` to decide whether to use local fallbacks. When we changed to `ENVIRONMENT=dev` to enable the agent, it tried to connect to Azure SQL, Blob Storage, and Service Bus — all of which have no credentials set.

**Pattern used:** Instead of hard-coding by environment name, check whether the connection string/account is actually configured:
```python
if settings.is_local or not settings.sql_connection_string:
    _instance = InMemoryRepository()
else:
    _instance = AzureSqlRepository()
```

**Lesson:** This pattern lets you use real AI services (agent) while still running storage/DB locally. It's more flexible than a single `ENVIRONMENT` flag that controls everything.

---

### 5. In-Process Extraction Wiring Fix

**File changed:** `api/app/main.py`

**Problem:** `_wire_local_extraction()` only ran when `settings.is_local` was True. In `dev` mode, the extraction job was queued but nothing processed it (the standalone worker needs Azure Service Bus).

**Fix:** Changed the condition to check whether the queue is a `LocalQueue` (no Service Bus configured), regardless of environment:
```python
from app.services.queue import get_queue as _gq, LocalQueue
if not isinstance(_gq(), LocalQueue):
    return
```

**Lesson:** When running without Azure Service Bus locally, the API must handle extraction in-process. This is fine for development — in production the standalone worker handles it via the real queue.

---

### 6. Environment Variables Not Visible to Workers

**Files changed:**
- `api/app/config.py` — added `azure_ai_*` fields to Settings
- `api/app/main.py` — propagate settings into `os.environ`
- `workers/extractors/__init__.py` — import from `app.config` when running in-process

**Problem:** Pydantic-settings reads `.env` files into a `Settings` object but does NOT put those values into `os.environ`. Workers checking `os.environ.get("ENVIRONMENT")` always saw `None` and defaulted to `"local"`, returning the StubExtractor even in dev mode.

**Fix:** When the workers run in-process inside the API, they import from `app.config.settings` directly instead of `os.environ`:
```python
try:
    from app.config import settings
    endpoint = settings.azure_ai_endpoint
except ImportError:
    endpoint = os.environ.get("AZURE_AI_ENDPOINT", "")
```

**Lesson:** Pydantic-settings `.env` values are NOT in `os.environ`. Any code that checks `os.environ` directly (especially in sub-modules or workers) won't see them. Either import the Settings object or explicitly set `os.environ` after settings load.

---

## Current State (End of Session)

| Component | Status |
|---|---|
| API (FastAPI) | Running on `localhost:8000` |
| Frontend (React/Vite) | Running on `localhost:5173` |
| Worker | Not needed — extraction runs in-process |
| Database | In-memory (data lost on restart) |
| Storage | Local folder (`ShipmentDocAI/.localdata/blobs`) |
| AI Extraction | Real — Azure AI Agent (`TESTAGENT0612`) |
| Auth | Bypassed (`BYPASS_AUTH=true`) |

## What's Needed for Production

- [ ] Provision Azure SQL and fill in `SQL_CONNECTION_STRING`
- [ ] Provision Azure Blob Storage and fill in `STORAGE_ACCOUNT_NAME`
- [ ] Provision Azure Service Bus and fill in `SERVICEBUS_NAMESPACE`
- [ ] Register an Entra ID app and fill in `ENTRA_TENANT_ID`, `ENTRA_API_CLIENT_ID`, `ENTRA_API_AUDIENCE`
- [ ] Set `BYPASS_AUTH=false` (or remove it)
- [ ] Set `ENVIRONMENT=prod`
- [ ] Deploy the standalone worker (`workers/worker.py`) separately
