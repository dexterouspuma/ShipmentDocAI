# Cover Sheet Templates

Drop your cover-sheet format(s) here. I'll use them to replace the placeholder
layout in `api/app/services/cover_sheet.py` (currently a generic label/value table).

## What to put here

Provide **either or both** (you chose PDF or Excel, analyst-selectable):

| Format | What to drop in | How it's used |
|---|---|---|
| **Excel** | A real `.xlsx` template with your headings/branding and `{{placeholders}}` in the cells where data goes | Filled in with `openpyxl` — easiest for non-devs to edit later |
| **PDF** | A filled-in sample PDF **and/or** a mockup (even a Word/image) showing exact layout, fonts, logo position | Reproduced with `reportlab` (pixel-positioned) |

Suggested filenames:
```
templates/cover-sheets/
├── cover_sheet_template.xlsx     ← Excel template with {{placeholders}}
├── cover_sheet_sample.pdf        ← a filled example showing target PDF layout
└── logo.png                      ← any logo/branding asset
```

## How placeholders map to data

Use the field names from the schemas (snake_case). Examples:
`{{bl_number}}`, `{{container_no}}`, `{{issuer_name}}`, `{{port_of_loading}}`,
`{{port_of_discharge}}`, `{{eta}}`, `{{gross_weight}}`, `{{total_due}}`,
`{{currency}}`, `{{incoterms}}`, `{{freight_terms}}`.
Full list per document type: see `../../schemas/`.

For repeating sections (charge lines, goods lines) tell me how you want them laid
out — e.g. a table that grows down the page.

## Questions I'll need answered with the format
1. Is the cover sheet the **same** for all document types, or different per type?
2. Does the analyst pick PDF vs Excel each time, or is it fixed by document type?
3. Any fields on the cover sheet that aren't in the schemas yet (we'll add them)?

Once the file(s) are here, tell me "cover sheet format is in" and I'll wire it up.
