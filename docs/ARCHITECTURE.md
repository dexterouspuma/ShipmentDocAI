# Shipment Document AI — Architecture & Process Flow

Visual reference for the whole system. The diagrams are written in **Mermaid**,
which GitHub renders automatically. To export them as images, see
`C:\Lion\Projects\Supporting Apps\diagram-tools\`.

- [1. End-to-end process flow (with Azure resources)](#1-end-to-end-process-flow)
- [2. Azure resource architecture](#2-azure-resource-architecture)
- [3. Document lifecycle (status states)](#3-document-lifecycle)
- [4. Extraction sequence (who calls what)](#4-extraction-sequence)
- [5. Azure resource reference table](#5-azure-resource-reference-table)

---

## 1. End-to-end process flow

How a document travels from upload to a finished cover sheet, and which Azure
resource handles each step.

```mermaid
flowchart TD
    subgraph User["👤 People"]
        UP["Uploader<br/>(drops PDFs in)"]
        AN["Analyst<br/>(reviews & approves)"]
    end

    subgraph Front["Frontend"]
        UI["React Review UI<br/><i>Azure Static Web Apps</i>"]
    end

    subgraph Compute["Application (Azure Container Apps)"]
        API["FastAPI Service<br/><i>api container · always on</i>"]
        WK["Extraction Worker<br/><i>worker container · scales 0→N</i>"]
    end

    subgraph Data["Storage & Messaging"]
        BLOB[("Blob Storage<br/>raw + processed PDFs")]
        SB{{"Service Bus<br/>extraction queue"}}
        SQL[("Azure SQL<br/>fields + review state")]
    end

    DI["Azure AI Document Intelligence<br/>prebuilt + custom models"]
    AAD["Microsoft Entra ID<br/>(sign-in)"]

    UP -->|upload PDF| UI
    AN -->|review / edit / approve| UI
    AN -.->|sign in| AAD
    UI -->|HTTPS /api| API
    AAD -.->|token| API

    API -->|1 store raw PDF| BLOB
    API -->|2 enqueue job| SB
    SB -->|3 deliver message| WK
    WK -->|4 read PDF| BLOB
    WK -->|5 OCR + extract fields| DI
    DI -->|6 fields + confidence| WK
    WK -->|7 save results + status=extracted| SQL

    API -->|read/update during review| SQL
    UI -->|8 Generate cover sheet| API
    API -->|9 build PDF / Excel| COVER["Cover Sheet<br/>ReportLab / openpyxl"]
    COVER -->|store copy| BLOB
    COVER -->|download| AN

    classDef azure fill:#e7f1ff,stroke:#1f4e79,color:#1f2733;
    classDef people fill:#fff4e5,stroke:#9a6700,color:#1f2733;
    class UI,API,WK,BLOB,SB,SQL,DI,AAD,COVER azure;
    class UP,AN people;
```

**The numbered path:** upload → (1) store → (2) queue → (3-7) worker extracts via
Document Intelligence and saves → analyst reviews → (8-9) generate & download the
cover sheet. The worker is decoupled by the queue, so bursts of documents don't
slow the upload or the UI.

---

## 2. Azure resource architecture

The same system viewed as deployed Azure resources and how they connect.

```mermaid
flowchart LR
    subgraph RG["Resource Group: rg-shipdocai"]
        direction TB

        subgraph CAE["Container Apps Environment"]
            API["api Container App<br/>(external ingress)"]
            WK["worker Container App<br/>(KEDA queue scaling)"]
        end

        ACR["Container Registry<br/>(app images)"]
        BLOB[("Storage Account<br/>Blob: raw / processed")]
        SB{{"Service Bus<br/>Standard · queue"}}
        DI["AI Document Intelligence<br/>S0 (custom models)"]
        SQL[("Azure SQL<br/>S1 database")]
        MI["Managed Identity<br/>(RBAC, no secrets)"]
        LOG["Log Analytics<br/>+ App Insights"]
        SWA["Static Web App<br/>(React UI)"]
    end

    AAD["Microsoft Entra ID"]

    SWA --> API
    API --> BLOB
    API --> SB
    API --> SQL
    SB --> WK
    WK --> BLOB
    WK --> DI
    WK --> SQL
    ACR -.->|pull images| API
    ACR -.->|pull images| WK
    MI -.->|auth to| BLOB
    MI -.->|auth to| SB
    MI -.->|auth to| DI
    MI -.->|auth to| ACR
    API -.->|logs/metrics| LOG
    WK -.->|logs/metrics| LOG
    AAD -.->|validates sign-in| API

    classDef azure fill:#e7f1ff,stroke:#1f4e79,color:#1f2733;
    class API,WK,ACR,BLOB,SB,DI,SQL,MI,LOG,SWA,AAD azure;
```

**Security model:** the apps authenticate to Storage, Service Bus, Document
Intelligence, and the registry via a **Managed Identity** (no passwords/keys in
config). Defined in `infra/`.

---

## 3. Document lifecycle

The status each document moves through (the `status` field in `shared/enums.py`).

```mermaid
stateDiagram-v2
    [*] --> uploaded: PDF received
    uploaded --> queued: message sent
    queued --> extracting: worker picks up
    extracting --> extracted: fields saved
    extracting --> extraction_failed: error
    extraction_failed --> queued: retry (Service Bus)
    extracted --> in_review: analyst opens
    in_review --> approved: analyst approves
    in_review --> rejected: analyst rejects
    approved --> cover_sheet_generated: sheet created
    cover_sheet_generated --> [*]
    rejected --> [*]
```

---

## 4. Extraction sequence

Who calls what during the automatic extraction step.

```mermaid
sequenceDiagram
    actor U as Uploader
    participant API as FastAPI (api)
    participant BLOB as Blob Storage
    participant SB as Service Bus
    participant WK as Worker
    participant DI as Document Intelligence
    participant SQL as Azure SQL

    U->>API: POST /documents (PDF)
    API->>BLOB: store raw PDF
    API->>SQL: create record (status=queued)
    API->>SB: enqueue {document_id}
    API-->>U: 201 Created
    SB->>WK: deliver message
    WK->>SQL: status = extracting
    WK->>BLOB: read PDF bytes
    WK->>DI: analyze (model by doc type)
    DI-->>WK: fields + confidence scores
    WK->>SQL: save fields, status = extracted
    Note over WK,SQL: low-confidence fields flagged for review
```

---

## 5. Azure resource reference table

| Resource | Azure service | Role in the flow | Starting tier |
|---|---|---|---|
| **API** | Container Apps | Accepts uploads, serves the review API, generates cover sheets | min 1 replica |
| **Worker** | Container Apps | Consumes the queue, runs extraction, persists results | scales 0→5 (KEDA) |
| **Blob Storage** | Storage Account | Stores raw PDFs + generated cover sheets | Standard_LRS |
| **Service Bus** | Service Bus (Standard) | Decouples upload from extraction; retries failures | Standard |
| **Document Intelligence** | Azure AI Document Intelligence | OCR + field extraction (prebuilt invoice + custom models) | S0 |
| **Azure SQL** | SQL Database | Extracted fields, review state, audit log | S1 |
| **Container Registry** | ACR | Holds the api/worker container images | Basic |
| **Managed Identity** | User-assigned Identity | Lets apps reach Azure services without secrets | — |
| **Monitoring** | Log Analytics + App Insights | Logs, metrics, tracing | PerGB2018 |
| **Static Web App** | Static Web Apps | Hosts the React review UI | (planned) |
| **Entra ID** | Microsoft Entra ID | Analyst sign-in / token validation | — |

> Cost scales mostly with **document volume** (Document Intelligence pages) and
> **worker run time**. The worker scaling to zero when idle keeps the bill low
> during quiet periods.
