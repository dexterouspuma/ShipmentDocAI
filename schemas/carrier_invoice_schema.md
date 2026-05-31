# Carrier / Freight Invoice — Extraction Schema

> ⚠️ **PROVISIONAL** — based on synthetic samples + standard freight-invoice fields.
> Validate/revise against real carrier invoices before training the custom model.
> The prebuilt invoice model handles commercial invoices poorly here — carrier
> invoices bill for *transport services*, so a **custom model** is expected.

## Header / document
| Field | Example | Notes |
|---|---|---|
| carrier_name | "OCEAN NETWORK EXPRESS", "MAERSK" | issuer |
| invoice_no | "FRT-448219" | |
| invoice_date | 22-Apr-2026 | |
| bl_number | "ONEY140604281955" | links to shipment |
| booking_no | optional |
| container_no | "TGHU1234567" | may be multiple |
| vessel_voyage | "MV STAR / 17E" | |
| pol / pod | "Shanghai, CN" / "Los Angeles, US" | |
| terms | "Prepaid" / "Collect" | |
| currency | "USD" | |
| due_date | "Net 30" | |

## Parties
| Field | Notes |
|---|---|
| bill_to_name / bill_to_address | who's being billed |
| remit_to | carrier AR / payment address |

## Charge line items (repeating table)
| Field | Example |
|---|---|
| charge_code / description | "Ocean Freight", "BAF", "THC", "Documentation Fee", "Chassis / Drayage" |
| basis | "Per Container", "Per B/L", flat |
| quantity | optional |
| rate | 1850.00 |
| amount | 1850.00 |

Common charge types to expect: Ocean/Air Freight, Bunker Adjustment Factor (BAF),
Terminal Handling (THC), Documentation, Customs Clearance, Chassis/Drayage, Fuel
Surcharge, Security/ISPS, Demurrage/Detention.

## Totals
| Field | Example |
|---|---|
| subtotal | 4,200.00 |
| tax (if any) | 0.00 |
| total_due | 5,180.00 |

## Review-UI implications
- Charges grid = editable add/remove-row; each row has a normalized `charge_code` for Phase-2 cost allocation.
- `bl_number` is the join key to the matching BOL / arrival notice → surface prominently for reconciliation.
- Flag if total_due ≠ sum of line amounts (math-check the analyst sees).
