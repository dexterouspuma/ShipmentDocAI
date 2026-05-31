# Database (Azure SQL)

T-SQL schema for the extracted-document store and review state.

## Files (run in order)
1. `schema.sql` — tables, constraints, indexes
2. `views.sql` — reconciliation + review-queue views

## Design notes
- **Hybrid storage:** relational columns for fields we filter/sort/JOIN on
  (the shipment join keys), plus `extracted_json` (NVARCHAR(MAX), `ISJSON`-checked)
  holding the full `shared.models.ExtractedDocument` for complete fidelity.
- **Child tables** (`document_parties`, `document_charges`, `document_goods_lines`)
  make repeating sections queryable; `ON DELETE CASCADE` keeps them tidy.
- **`min_confidence`** on `documents` lets the review queue surface the riskiest
  documents first.
- **`audit_log`** is an immutable trail of every analyst action (who/what/when).

## Tables
| Table | Purpose |
|---|---|
| `documents` | One row per ingested PDF; lifecycle + denormalized summary + JSON |
| `document_parties` | Shipper / consignee / notify / broker (repeating) |
| `document_charges` | Destination / freight charge lines (repeating) |
| `document_goods_lines` | Invoice / packing-list line items (repeating) |
| `audit_log` | Review actions trail |

## Views
| View | Purpose |
|---|---|
| `vw_shipment_by_bl` | Groups docs sharing a B/L into one shipment; flags missing doc types |
| `vw_review_queue` | Documents awaiting review, for the analyst queue |

## Applying
Against Azure SQL (after provisioning) using `sqlcmd` or Azure Data Studio:
```powershell
sqlcmd -S <server>.database.windows.net -d <db> -G -i schema.sql
sqlcmd -S <server>.database.windows.net -d <db> -G -i views.sql
```
(`-G` = Entra ID auth.) A proper migration tool (e.g. Alembic or DbUp) will be
added when the schema starts changing in production.

> Note: this DDL targets SQL Server / Azure SQL syntax and has not yet been run
> against a live database (no SQL Server available in the scaffold environment).
> Validate on first provision.
