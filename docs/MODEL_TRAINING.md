# Model Training & Labeling Guide

How to train the custom Azure AI Document Intelligence models that power
extraction. This is a **checklist for whoever labels the documents** (an analyst
who knows the paperwork — no coding needed).

> **Where this happens:** in **Document Intelligence Studio** —
> https://documentintelligence.ai.azure.com — a Microsoft web app, **separate
> from our app's review UI**. You label here once to *train* the models; our app
> then *uses* the trained models automatically. See [The Studio UI](#the-studio-ui).

---

## Big picture

| Document type | Approach | Training needed? |
|---|---|---|
| Commercial Invoice | Azure **prebuilt-invoice** model | ❌ No — works out of the box |
| Arrival Notice | **Custom Neural** model | ✅ Yes |
| Carrier Invoice | **Custom Neural** model | ✅ Yes |
| Packing List | **Custom Neural** model | ✅ Yes |
| Bill of Lading | **Custom Neural** model | ✅ Yes |

Use **Custom Neural** (not Template) because layouts vary by carrier/vendor.
Minimum 5 samples per type; **10-20 varied samples** strongly recommended.

> ⚠️ **Field names matter.** The field names you type in Studio (the "Studio
> field" column below) must be reported back to the developer to align
> `workers/extractors/document_intelligence.py` (`_FIELD_MAP`). Keep them exactly
> as written here and alignment is automatic.

---

## The Studio UI

When you open a custom-model project in Document Intelligence Studio, the screen
has three main areas:

```
┌──────────────┬─────────────────────────────────┬────────────────────────┐
│  LEFT:       │  CENTER:                         │  RIGHT:                │
│  document    │  the selected document with all  │  your field list       │
│  list        │  OCR-detected text highlighted   │  (the "label" panel)   │
│  (your       │                                  │                        │
│  samples)    │  → drag a box around a value,    │  → click a field name, │
│              │    it gets tagged to a field     │    then the value      │
│              │                                  │                        │
└──────────────┴─────────────────────────────────┴────────────────────────┘
   Top toolbar: Field types (text/number/date/table/signature), Train, Test
```

**How you label one value:** click the field name in the right panel → click/drag
the matching text in the center document → it's now tagged. Repeat for every
field, on every sample. A small colored highlight marks each labeled value.

**Tables** are special: you define a table field with named columns, then tag
each row's cells. Studio learns to return all rows (however many).

---

## Field checklists

For each field: the **Studio field name** to use, its **type**, and **what to
look for** on the document. `*` = especially important (a join key or required).

### Arrival Notice  →  model id e.g. `arrival-notice-v1`

| Studio field | Type | What to label |
|---|---|---|
| `IssuerName` | text | Carrier/forwarder name at top (Evergreen, ONE…) |
| `ReferenceNumber` | text | The issuer's ref no. |
| `IssueDate` | date | Issue/notice date |
| `BLNumber` * | text | Bill of Lading number (master) |
| `MBLNumber` | text | Master B/L (if LCL shows both) |
| `HBLNumber` | text | House B/L (NVOCC/LCL) |
| `ContainerNumber` | text | Container no. |
| `SealNumber` | text | Seal no. |
| `VesselVoyage` | text | Vessel + voyage (ocean) |
| `FlightNumber` | text | Flight no. (air only) |
| `PortOfLoading` | text | POL / origin airport |
| `PortOfDischarge` | text | POD / destination airport |
| `ETA` | text | Estimated arrival |
| `LastFreeDay` | date | Last free day |
| `GrossWeight` | text | Gross weight (keep units) |
| `MeasurementCBM` | text | Volume in CBM |
| `NumberOfPackages` | text | No. of cartons/pieces |
| `HSCode` | text | HS code(s) |
| `GoodsDescription` | text | Cargo description |
| `Incoterms` | text | e.g. FOB Kaohsiung |
| `FreightTerms` | text | Prepaid / Collect |
| `CargoValue` | text | Declared value |
| `TotalDue` | number | Total amount due |
| `Currency` | text | e.g. USD |
| **Table: `Charges`** | table | Columns: `Description`, `Basis`, `Rate`, `Amount` — one row per destination charge |
| `Shipper` | text/region | Shipper name+address block |
| `Consignee` | text/region | Consignee block |
| `NotifyParty` | text/region | Notify party block |

### Carrier / Freight Invoice  →  `carrier-invoice-v1`

| Studio field | Type | What to label |
|---|---|---|
| `IssuerName` | text | Carrier name |
| `ReferenceNumber` | text | Invoice number |
| `IssueDate` | date | Invoice date |
| `BLNumber` * | text | Linked B/L number |
| `ContainerNumber` | text | Container no. |
| `VesselVoyage` | text | Vessel/voyage |
| `PortOfLoading` | text | POL |
| `PortOfDischarge` | text | POD |
| `FreightTerms` | text | Prepaid/Collect |
| `TotalDue` | number | Total due |
| `Currency` | text | Currency |
| **Table: `Charges`** | table | Columns: `Description`, `Basis`, `Rate`, `Amount` |

### Packing List  →  `packing-list-v1`

| Studio field | Type | What to label |
|---|---|---|
| `ReferenceNumber` | text | Packing list no. |
| `IssueDate` | date | Date |
| `InvoiceRef` * | text | Linked commercial invoice no. |
| `ContainerNumber` | text | Container no. |
| `SealNumber` | text | Seal no. |
| `GrossWeight` | text | Total gross weight |
| `Shipper` | text/region | Shipper block |
| `Consignee` | text/region | Consignee block |
| **Table: `GoodsLines`** | table | Columns: `Description`, `QtyPerCarton`, `Cartons`, `NetWeightKg`, `GrossWeightKg`, `DimensionsCm` |

### Bill of Lading  →  `bol-v1`

| Studio field | Type | What to label |
|---|---|---|
| `IssuerName` | text | Carrier name |
| `BLNumber` * | text | B/L number |
| `ReferenceNumber` | text | Booking number |
| `IssueDate` | date | Date of issue |
| `VesselVoyage` | text | Vessel/voyage |
| `PortOfLoading` | text | POL |
| `PortOfDischarge` | text | POD |
| `ContainerNumber` | text | Container no. |
| `SealNumber` | text | Seal no. |
| `NumberOfPackages` | text | No. of packages |
| `GoodsDescription` | text | Goods description |
| `HSCode` | text | HS code |
| `GrossWeight` | text | Gross weight |
| `MeasurementCBM` | text | Measurement (CBM) |
| `FreightTerms` | text | Prepaid/Collect |
| `Shipper` / `Consignee` / `NotifyParty` | text/region | Party blocks |

### Commercial Invoice — **no training**
Use the prebuilt model id `prebuilt-invoice`. It already returns VendorName,
CustomerName, InvoiceId, InvoiceDate, Items (line items), HS-code-like fields,
AmountDue, etc. Set `DOCINTEL_MODEL_INVOICE=prebuilt-invoice` (already the default).

---

## Step-by-step

1. **Create project** in Studio → choose **Custom extraction model** → connect
   your DI resource + the Blob container holding that type's samples.
2. Studio runs **layout/OCR** on all samples automatically.
3. **Add fields** from the checklist above (right panel). Add the **table** field
   with its named columns.
4. **Label every sample**: select field → drag the value. Tag table rows.
5. Click **Train** → choose **Neural** → wait (~20-30 min).
6. Note the **Model ID** it produces.
7. **Test** tab: try a document you didn't train on; check field accuracy +
   confidence. Re-label / add samples / retrain as needed (→ `-v2`).

## Hand back to the developer

After training each model, provide:
1. **The model IDs** (e.g. `arrival-notice-v1`) → go into the worker env vars
   (`DOCINTEL_MODEL_ARRIVAL_NOTICE`, etc.)
2. **Any field-name differences** from this guide → so `_FIELD_MAP` and the
   table mapping (`_map_charges`, goods lines) in
   `workers/extractors/document_intelligence.py` get aligned.

## Optional: auto-detect document type (classifier)
Studio can also train a **classification model** that decides "this PDF is an
arrival notice vs a packing list." Wiring it in lets uploads sort themselves
instead of the user choosing the type. Nice Phase-1.5 enhancement.

## Tips
- **Variety beats volume** — include each carrier/vendor layout you receive.
- **Be consistent** — always label the *same* value for a field across docs.
- **Units** — label the whole value incl. units (e.g. "11,240 KGS") for weight.
- **Multi-value fields** (e.g. two HS codes) — label the whole text as shown.
