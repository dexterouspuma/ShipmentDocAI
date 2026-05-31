# Arrival Notice — Extraction Schema

> Derived from 5 real samples (Evergreen, KWE, Nippon Express/Air, ONE, DB Schenker).
> Covers ocean FCL, ocean LCL, and air freight modes.
> This schema defines the fields to **label in Azure Document Intelligence Studio**
> when training the custom `arrival-notice` model, and the columns/state in Azure SQL.

## Mode detection
Arrival notices come in 3 modes; some fields differ. Capture `transport_mode` =
`OCEAN_FCL | OCEAN_LCL | AIR`. Air uses flight/AWB fields instead of vessel/voyage.

## Header / document
| Field | Example | Notes |
|---|---|---|
| issuer_name | "EVERGREEN LINE", "Nippon Express U.S.A., Inc." | carrier or forwarder/NVOCC |
| issuer_address | — | |
| issuer_license | "FMC OTI Lic. 001305", "IATA Agent" | optional |
| document_title | "Arrival Notice / Freight Invoice", "Air Freight Arrival Notice" | |
| reference_no | "EVGL-NYC-2026-058813" | issuer's ref |
| issue_date | 25-May-2026 | |

## Vessel & voyage (OCEAN) — or Flight & routing (AIR)
| Field | Ocean example | Air example |
|---|---|---|
| vessel_name / aircraft | "EVER ACE" | airline "All Nippon Airways (NH)" |
| voyage_no / flight_no | "0142-017W" | "NH 8008 / NH 214" |
| service | "AEX – Asia-East North America" | — |
| trade_lane | "Asia – US East Coast (via Suez)" | "NRT → LAX" |
| port_of_loading / origin_airport | "KAOHSIUNG, TAIWAN (TWKHH)" | "TOKYO NARITA (NRT)" |
| port_of_discharge / dest_airport | "NEW YORK / NEW JERSEY (USNYK)" | "LOS ANGELES INTL (LAX)" |
| transshipment_port | "NEW YORK/NJ (USNYK) via MSC" | optional |
| eta | 18-Jun-2026 | 31-May-2026 14:35 PDT |
| terminal / cfs / ramp | "GCT Bayonne…" | "CASS warehouse" |
| last_free_day | 25-Jun-2026 | 05-Jun-2026 |
| bl_type | "Telex Release (Surrendered at Origin)", "Original (3 OBL)" | — |

## Parties (repeating: shipper, consignee, notify/also-notify)
| Field | Notes |
|---|---|
| party_role | SHIPPER / CONSIGNEE / NOTIFY / BROKER |
| name | |
| address | multi-line |
| contact_tel | |
| contact_email | when present |

## Cargo & container
| Field | Example | Notes |
|---|---|---|
| bl_number | "EGLV143026058813" | master BOL |
| mbl_number / hbl_number | "EGLV140604281955" / "KWEORD2026018847" | LCL/NVOCC have both |
| container_no | "EMCU4917832" | may be multiple |
| seal_no | "EVG-772641" | |
| container_size_type | "1 × 40' Standard Dry", "40' HC (Consolidated)" | |
| mawb_no / hawb_no | "205-88847291" / "NX-LAX-2026-09321" | AIR only |
| no_of_pieces / no_of_packages | "1,560 CTNS", "12 PKGS", "84 WOODEN CRATES" | |
| gross_weight | "11,240 KGS" | |
| chargeable_weight | "420.00 KGS" | AIR |
| measurement_cbm | "31.80 CBM" | ocean |
| hs_code | "3926.90 / 3923.10" | may be multiple |
| marks_and_numbers | "ASG / NJ-2026 / C/NOS 1-1560" | |
| goods_description | "PLASTIC HOUSEHOLD GOODS…" | ⚠️ column-bleed in raw text; DI layout needed |
| cargo_value | "USD 94,800.00" | |
| incoterms | "FOB Kaohsiung", "DAP Beverly Hills" | |
| freight_terms | "PREPAID", "PREPAID (Ocean) / COLLECT (Destination)" | |

## Destination charges — LINE ITEMS (repeating table)
| Field | Example |
|---|---|
| charge_description | "Destination THC (Terminal Handling)" |
| basis | "Per Container", "Per CBM", "Per HBL" |
| rate | 450.00 |
| amount | 450.00 |

| Total field | Example |
|---|---|
| total_due | "USD 756.00" |
| total_due_label | "TOTAL DUE UPON DELIVERY" / "TOTAL DUE BEFORE RELEASE" |

## Remarks / terms (free text — capture as block, optionally parse)
- free_time_days, demurrage_rate, storage_rate, payment_instructions, ad_cvd_flag, isf_responsibility — present in "Important Remarks". Capture full `remarks_text`; structured parsing optional/Phase 2.

## Review-UI implications
- `goods_description` and multi-column cargo block are the highest-risk for OCR errors → flag low-confidence for analyst.
- Charges table must be an editable, add/remove-row grid.
- Parties are repeating with role — render as labeled cards.
- Mode toggle (ocean/air) switches which header fields are shown.
