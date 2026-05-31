# Bill of Lading (BOL) — Extraction Schema

> ⚠️ **PROVISIONAL** — based on synthetic samples + standard ocean B/L fields.
> Validate/revise against real Bills of Lading before training the custom model.
> Note: arrival notices already carry most BOL data; a standalone BOL model is
> useful when the original B/L is the source document.

## Header / document
| Field | Example | Notes |
|---|---|---|
| carrier_name | "EVERGREEN LINE" | |
| bl_number | "EGLV143026058813" | primary key for the shipment |
| booking_no | "7741882" | |
| bl_type | "Original (3 OBL)", "Telex Release", "Seaway" | |
| date_of_issue | 14-Mar-2026 | |
| place_of_issue | optional |
| no_of_originals | "THREE (3)" | |

## Parties
| Field | Notes |
|---|---|
| shipper_name / shipper_address | |
| consignee_name / consignee_address | may be "To Order" |
| notify_party_name / address | |

## Routing & transport
| Field | Example |
|---|---|
| vessel_voyage | "MV STAR / 17E" |
| port_of_loading | "Shanghai, CN" |
| port_of_discharge | "Los Angeles, US" |
| place_of_receipt | optional pre-carriage |
| place_of_delivery | optional on-carriage |

## Container & cargo
| Field | Example | Notes |
|---|---|---|
| container_no | "TGHU1234567" | may be multiple |
| seal_no | "991203" | |
| container_size_type | "40HC", "20GP" | |
| marks_and_numbers | "N/M" | |
| no_of_packages | "84 CTNS / WOODEN CRATES" | |
| goods_description | "Automotive stamped metal parts" | |
| hs_code | "8708.29" | when present |
| gross_weight_kg | "16,890" | |
| measurement_cbm | "22.40" | |

## Freight & charges
| Field | Example |
|---|---|
| freight_terms | "PREPAID" / "COLLECT" |
| freight_charges (if itemized) | optional table |

## Review-UI implications
- `bl_number` is the master join key across arrival notice, carrier invoice, packing list → surface prominently.
- Containers can repeat → support multiple container rows.
- "To Order" consignee and negotiable vs. non-negotiable B/L type matter for release → flag for analyst.
