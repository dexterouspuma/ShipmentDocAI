# Analyst Review UI (React + TypeScript)

Vite + React + TypeScript app for the analyst review workflow:
queue → side-by-side PDF + editable fields (confidence highlighting) →
approve / reject → generate cover sheet (PDF or Excel).

## Run (local)
The backend API must be running on `http://localhost:8000` (see repo README).
Vite proxies `/api` → the backend, so the browser uses a single origin.

```powershell
cd web
npm install
npm run dev      # http://localhost:5173
```

## Structure
| Path | What |
|---|---|
| `src/api/client.ts` | Typed calls to the FastAPI backend |
| `src/types.ts` | TypeScript mirror of the backend models |
| `src/components/ReviewQueue.tsx` | Queue list + upload, low-confidence flag |
| `src/components/DocumentReview.tsx` | Side-by-side PDF + fields, approve/reject, cover sheet |
| `src/components/FieldRow.tsx` | One editable field with confidence highlighting |

## Notes / pending
- **PDF viewer** uses the browser-native `<iframe>` against `/documents/{id}/file`.
  Upgrade to `react-pdf` later for click-to-highlight using the `bbox`/`page`
  metadata each field already carries.
- **Auth:** `client.ts` attaches a Bearer token from `localStorage` if present.
  Wire **MSAL** (Microsoft Entra ID) for real sign-in before production; local dev
  needs no token because the API bypasses auth in local mode.
- **Line-item editing:** charges/goods tables are currently read-only in the UI;
  make them add/remove-row editable grids next (the backend models already support this).
