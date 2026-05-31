# Extraction Workers

Consume the Service Bus extraction queue, call Azure AI Document Intelligence,
map results into `shared.models.ExtractedDocument`, and persist them.

## Layout
| Path | What |
|---|---|
| `processor.py` | `process_document(id, *, repo, storage, extractor)` — the injectable core |
| `worker.py` | Standalone Service Bus consumer loop (Azure deployable) |
| `extractors/base.py` | `Extractor` interface + `min_confidence` triage helper |
| `extractors/stub.py` | Local stub returning plausible data (incl. a low-confidence field) |
| `extractors/document_intelligence.py` | Azure Document Intelligence implementation |
| `tests/` | Processor unit tests |

## How it runs in each environment
- **Local:** the API wires `process_document` to its `LocalQueue` handler, so an
  upload is extracted **in-process** with `StubExtractor` — no Azure, no separate
  worker. (See `api/app/main.py` `_wire_local_extraction`.)
- **Azure:** `worker.py` runs as its own Container App, pulls messages from
  Service Bus, and uses `DocumentIntelligenceExtractor` + the Azure SQL repository.
  Autoscales on queue depth.

## Pending before production
- Finalize `_FIELD_MAP` and the charges/line-item mapping in
  `document_intelligence.py` against the **trained custom-model field names**
  (defined when labeling in Document Intelligence Studio).
- Implement `AzureSqlRepository` (see `api/app/repository.py`) so persistence
  writes the relational summary + `extracted_json` + child tables.
