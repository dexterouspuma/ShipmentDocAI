# Packing List — Extraction Schema

> ⚠️ **PROVISIONAL** — based on synthetic samples + standard packing-list fields.
> Validate/revise against real packing lists before training the custom model.

## Header / document
| Field | Example | Notes |
|---|---|---|
| packing_list_no | "PL-48213" | |
| date | 14-Mar-2026 | |
| invoice_ref | "CI-48213" | links to commercial invoice |
| container_no | "TGHU1234567" | |
| seal_no | "228811" | |

## Parties
| Field | Notes |
|---|---|
| shipper_name / shipper_address | |
| consignee_name / consignee_address | |

## Line items (repeating table)
| Field | Example | Notes |
|---|---|---|
| line_no / carton_range | 1, "C/NOS 1-240" | |
| description | "Woven fabric & garments" | |
| qty_per_carton | 200 | |
| cartons | 24 | |
| net_weight_kg | 450.0 | |
| gross_weight_kg | 510.0 | |
| dimensions_cm | "50x40x30" | LxWxH |
| volume_cbm | derived/optional |

## Totals
| Field | Example |
|---|---|
| total_cartons | 240 |
| total_net_weight | "3,200.0 kg" |
| total_gross_weight | "3,650.0 kg" |
| total_volume_cbm | "18.60" |

## Review-UI implications
- Line items = editable add/remove-row grid (often the longest table of all doc types).
- Cross-check `invoice_ref` against the matching commercial invoice (same shipment).
- Weight/volume totals should reconcile with BOL / arrival notice → math-check for analyst.
