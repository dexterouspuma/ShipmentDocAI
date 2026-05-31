# Commercial Invoice — Extraction Schema

> ⚠️ **PROVISIONAL** — based on synthetic samples + standard trade-document fields.
> Validate/revise against real commercial invoices before training the model.
> Azure has a **prebuilt `invoice` model** — start there; add a custom model only
> if your invoices have fields the prebuilt model misses.

## Header / document
| Field | Example | Notes |
|---|---|---|
| invoice_no | "CI-48213" | |
| invoice_date | 14-Mar-2026 | |
| po_number | "PO-7741" | buyer's purchase order |
| incoterms | "FOB Shanghai", "CIF Long Beach" | term + named place |
| currency | "USD" | |
| country_of_origin | "China" | |
| payment_terms | "Net 30", "T/T in advance" | when present |

## Parties
| Field | Notes |
|---|---|
| seller_name / seller_address | exporter |
| buyer_name / buyer_address | consignee / importer |
| ship_to (if different from buyer) | optional |

## Line items (repeating table)
| Field | Example |
|---|---|
| line_no | 1 |
| description | "LED panel light 60x60" |
| hs_code | "9405.40" |
| quantity | 1200 |
| unit | "PCS" |
| unit_price | 12.50 |
| amount | 15000.00 |

## Totals & summary
| Field | Example |
|---|---|
| subtotal | 42,300.00 |
| discount / freight / insurance | optional, when itemized |
| total_amount | 42,300.00 |
| total_net_weight | "3,200 KG" |
| total_gross_weight | "3,650 KG" |
| total_packages | "85 CTNS" |

## Review-UI implications
- Line items = editable add/remove-row grid.
- Prebuilt invoice model returns most of these with confidence scores → highlight low-confidence.
- HS code + country_of_origin are customs-critical → flag if missing.
