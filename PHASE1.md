# Shipment Document AI — Phase 1 Plan

> **Status:** Planning
> **Last updated:** 2026-05-30
> **Goal:** Scan and ingest logistics PDFs (Arrival Notices, Invoices, Packing Lists, Carrier Invoices, BOLs), extract all structured data, route to an analyst for review, and generate a cover sheet (PDF or Excel) on approval.
> **Phase 2 (later):** Send extracted/approved data to external SaaS solutions.

---

## 1. Decisions Locked In

| Decision | Choice |
|---|---|
| Backend language | **Python** (FastAPI) |
| Frontend | **React 18 + TypeScript** |
| Architecture | **Medium** — async queue + autoscaling workers |
| Azure starting point | Subscription + tenant exist, resources ready |
| Cover sheet format | **PDF or Excel** (analyst-selectable) |
| Auth / users | **Internal team only — Entra ID SSO** |
| Document volume | Medium (100–1000 docs/day), built for burst tolerance |

---

## 2. Architecture

```
┌─────────────┐      ┌──────────────┐      ┌─────────────────────┐
│   Analyst   │─SSO─▶│  React UI    │─────▶│   FastAPI Service   │
│  (Entra ID) │      │ (Container   │      │  (Container App)    │
└─────────────┘      │   App)       │      └──────────┬──────────┘
                     └──────────────┘                 │
                                                      ▼
                                         ┌────────────────────────┐
                                         │   Azure Blob Storage   │
                                         │   (raw + processed)    │
                                         └────────────┬───────────┘
                                                      │
                                                      ▼
                                         ┌────────────────────────┐
                                         │  Azure Service Bus     │
                                         │  (extraction queue)    │
                                         └────────────┬───────────┘
                                                      │
                                                      ▼
                                  ┌───────────────────────────────────┐
                                  │  Extraction Workers (Container    │
                                  │  Apps, autoscaling 0→N)           │
                                  │                                   │
                                  │  ┌─────────────────────────────┐  │
                                  │  │ Azure AI Document Intel.    │  │
                                  │  │ • Prebuilt: invoice         │  │
                                  │  │ • Custom: arrival notice    │  │
                                  │  │ • Custom: BOL               │  │
                                  │  │ • Custom: packing list      │  │
                                  │  │ • Custom: carrier invoice   │  │
                                  │  └─────────────────────────────┘  │
                                  └───────────────┬───────────────────┘
                                                  │
                                                  ▼
                                       ┌──────────────────────┐
                                       │  Azure SQL Database  │
                                       │  (extracted fields + │
                                       │   review state)      │
                                       └──────────────────────┘
```

---

## 3. Tech Stack

| Layer | Choice |
|---|---|
| Backend | Python 3.12 + FastAPI |
| Workers | Python (same image, different entrypoint) |
| Frontend | React 18 + TypeScript + Vite |
| UI library | Fluent UI (matches Entra SSO look) or shadcn/ui |
| PDF viewer | `react-pdf` (side-by-side with field panel) |
| Document AI | Azure AI Document Intelligence (custom models + prebuilt invoice) |
| Database | Azure SQL Database (S1 tier to start) |
| Queue | Azure Service Bus Standard |
| Storage | Azure Blob Storage |
| Auth | MSAL (frontend) + FastAPI JWT validation (backend) |
| Hosting | Azure Container Apps |
| IaC | Bicep |
| CI/CD | GitHub Actions → Azure |
| Cover sheets | ReportLab (PDF) + openpyxl (Excel) — analyst picks format |

---

## 4. Phase 1 Roadmap (~6 weeks)

### Milestone 1 — Foundation (Week 1)
- Bicep templates for all Azure resources
- GitHub repo scaffolding (mono-repo: `/api`, `/web`, `/workers`, `/infra`)
- CI/CD pipelines
- Entra ID app registration + MSAL frontend integration

### Milestone 2 — Document AI training (Week 1–2, parallel)
- Collect 5+ samples per doc type
- Label fields in Document Intelligence Studio
- Train 4 custom models (arrival notice, BOL, packing list, carrier invoice)
- Validate accuracy on holdout samples; iterate

### Milestone 3 — Ingestion pipeline (Week 2–3)
- Upload API → Blob → enqueue message
- Worker: dequeue → call Document Intelligence → write to SQL
- Document type auto-detection (route to correct model)
- Retry + dead-letter handling

### Milestone 4 — Review UI (Week 3–4)
- Queue view (pending docs, sortable, filterable)
- Review screen: PDF viewer left, editable extracted fields right
- Field-level confidence scores (highlight low-confidence)
- Approve / reject / send-back-for-rework
- Audit log (who changed what, when)

### Milestone 5 — Cover sheet generation (Week 4–5)
- Build PDF + Excel generators once format(s) provided
- "Generate Cover Sheet" button on approved documents
- Download + auto-store in Blob

### Milestone 6 — UAT + hardening (Week 5–6)
- Load testing
- Error handling polish
- Analyst training session
- Production deployment

---

## 5. What's Needed to Start

1. **5+ sample PDFs per doc type** (Arrival Notice, BOL, Invoice, Packing List, Carrier Invoice) — redacted if needed
2. **Cover sheet format(s)** — PDF mockup and/or Excel template with example data
3. **Azure access** — Contributor role on a resource group, OR someone to run Bicep deploys
4. **Entra ID admin** — permission to register an enterprise app
5. **GitHub org** — where the repo should live

---

## 6. Open Questions (to resolve before/during build)

- **Cover sheet trigger:** Analyst picks PDF vs Excel each time, or determined by document type?
- **Line item handling:** Each invoice/packing-list line as an editable row in the review UI? (assumed yes)
- **Multi-page docs:** Arrival notices spanning multiple PDFs — one shipment or separate?
- **Retention:** How long to keep raw PDFs in Blob? (cost + compliance)

---

## 7. Phase 2 (Out of Scope for Now)

- Send extracted/approved data to external SaaS solutions (TBD which systems, integration method, auth).
- Will consume from the same Service Bus queue / DB built in Phase 1.
