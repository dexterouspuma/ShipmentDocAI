# Extraction Schemas

The agreed field list for each document type. Single source of truth that keeps
Azure Document Intelligence labeling, Azure SQL columns, the FastAPI worker's
JSON mapping, the React review UI, and cover-sheet generation all in sync.

| Schema | Status | Model approach |
|---|---|---|
| [arrival_notice_schema.md](arrival_notice_schema.md) | ✅ from REAL samples | Custom model (ocean + air modes) |
| [commercial_invoice_schema.md](commercial_invoice_schema.md) | ⚠️ provisional (synthetic) | Prebuilt `invoice` first, custom if needed |
| [carrier_invoice_schema.md](carrier_invoice_schema.md) | ⚠️ provisional (synthetic) | Custom model |
| [packing_list_schema.md](packing_list_schema.md) | ⚠️ provisional (synthetic) | Custom model |
| [bol_schema.md](bol_schema.md) | ⚠️ provisional (synthetic) | Custom model |

> Provisional schemas were derived from synthetic samples + standard trade-document
> fields. Revisit against real documents before training those models.

## Cross-document relationships (the join keys)
These documents describe the **same shipment** from different angles. The app
should reconcile them on shared keys:

- **`bl_number`** — the master key. Appears on BOL, arrival notice, and carrier invoice.
- **`invoice_ref`** — links packing list ↔ commercial invoice.
- **`container_no` / `seal_no`** — appear across BOL, arrival notice, packing list.
- **weights & CBM** — should reconcile across packing list, BOL, arrival notice (math-check for analyst).

This reconciliation is what lets an analyst review a whole shipment as a unit and
is the foundation for Phase-2 SaaS hand-off.

## Conventions
- Field names: `snake_case`, consistent across all layers.
- Repeating tables (line items, charges, containers, parties) → editable
  add/remove-row grids in the UI; child tables in SQL.
- Every extracted field carries a **confidence score**; the UI highlights
  low-confidence values for analyst attention.
