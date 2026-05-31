# Shipment Document AI

Azure-deployed app that scans logistics PDFs (Arrival Notices, Commercial
Invoices, Carrier Invoices, Packing Lists, Bills of Lading), extracts structured
data with Azure AI Document Intelligence, routes it to an analyst for review, and
generates a cover sheet (PDF or Excel) on approval.

See [`PHASE1.md`](PHASE1.md) for the full plan and [`schemas/`](schemas/) for the
per-document field schemas.

## Architecture (medium / async)

```
React UI ──▶ FastAPI (api) ──▶ Blob Storage ──▶ Service Bus ──▶ Workers ──▶ Azure SQL
   ▲ Entra ID SSO                                                  │
   └──────────────── review / approve / generate cover sheet ◀────┘
                                              (Azure AI Document Intelligence)
```

## Repo layout

| Path | What |
|---|---|
| `api/` | FastAPI service — upload, list, review, cover-sheet endpoints |
| `workers/` | Queue consumers that call Document Intelligence and persist results |
| `web/` | React + TypeScript analyst review UI |
| `shared/` | Pydantic models + enums shared by api and workers |
| `db/` | SQL schema (DDL) and migrations |
| `infra/` | Bicep templates for all Azure resources |
| `schemas/` | Per-document extraction schemas (field definitions) |
| `samples/` | Sample PDFs (real arrival notices + synthetic placeholders) |
| `docs/` | Additional documentation |

## Local development

Prereqs: Python 3.12, Node 20+, Docker (optional), Azure CLI (for deploy).

```powershell
# Backend API
cd api
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy ..\.env.example .env   # fill in values
uvicorn app.main:app --reload --port 8000

# Worker (separate terminal)
cd workers
pip install -r requirements.txt
python worker.py

# Frontend
cd web
npm install
npm run dev
```

See [`infra/README.md`](infra/README.md) for provisioning Azure resources.

## Status

Phase 1 scaffold in progress. Extraction calls and SQL persistence are wired as
stubs/skeletons pending Azure resource provisioning and custom-model training.
