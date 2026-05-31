// Thin API client. All calls go through the Vite proxy (/api -> FastAPI).
// In Azure, an auth token from MSAL would be attached here as a Bearer header.
import type {
  DocumentRecord, AuditEntry, ProcessingStatus,
  FreightCoding, FreightCodingConfig, FreightCodingResponse,
} from '../types'

const BASE = '/api'

async function json<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`${res.status}: ${text}`)
  }
  return res.json() as Promise<T>
}

// Placeholder for MSAL-acquired token; no-op in local dev (API bypasses auth).
function authHeaders(): HeadersInit {
  const token = window.localStorage.getItem('access_token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

export const api = {
  listDocuments(status?: ProcessingStatus): Promise<DocumentRecord[]> {
    const q = status ? `?status_filter=${status}` : ''
    return fetch(`${BASE}/documents${q}`, { headers: authHeaders() }).then(json<DocumentRecord[]>)
  },

  getDocument(id: string): Promise<DocumentRecord> {
    return fetch(`${BASE}/documents/${id}`, { headers: authHeaders() }).then(json<DocumentRecord>)
  },

  fileUrl(id: string): string {
    return `${BASE}/documents/${id}/file`
  },

  upload(file: File, documentType = 'unknown'): Promise<DocumentRecord> {
    const fd = new FormData()
    fd.append('file', file)
    return fetch(`${BASE}/documents?document_type=${documentType}`, {
      method: 'POST', body: fd, headers: authHeaders(),
    }).then(json<DocumentRecord>)
  },

  openForReview(id: string): Promise<DocumentRecord> {
    return fetch(`${BASE}/documents/${id}/open`, { method: 'POST', headers: authHeaders() })
      .then(json<DocumentRecord>)
  },

  editField(id: string, fieldPath: string, newValue: unknown): Promise<DocumentRecord> {
    return fetch(`${BASE}/documents/${id}/fields`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: JSON.stringify({ field_path: fieldPath, new_value: newValue }),
    }).then(json<DocumentRecord>)
  },

  approve(id: string): Promise<DocumentRecord> {
    return fetch(`${BASE}/documents/${id}/approve`, { method: 'POST', headers: authHeaders() })
      .then(json<DocumentRecord>)
  },

  reject(id: string, reason: string): Promise<DocumentRecord> {
    return fetch(`${BASE}/documents/${id}/reject?reason=${encodeURIComponent(reason)}`, {
      method: 'POST', headers: authHeaders(),
    }).then(json<DocumentRecord>)
  },

  audit(id: string): Promise<AuditEntry[]> {
    return fetch(`${BASE}/documents/${id}/audit`, { headers: authHeaders() }).then(json<AuditEntry[]>)
  },

  coverSheetUrl(id: string, fmt: 'pdf' | 'excel'): string {
    return `${BASE}/documents/${id}/cover-sheet?fmt=${fmt}`
  },

  freightConfig(): Promise<FreightCodingConfig> {
    return fetch(`${BASE}/meta/freight-coding-config`, { headers: authHeaders() })
      .then(json<FreightCodingConfig>)
  },

  getFreightCoding(id: string): Promise<FreightCodingResponse> {
    return fetch(`${BASE}/documents/${id}/freight-coding`, { headers: authHeaders() })
      .then(json<FreightCodingResponse>)
  },

  saveFreightCoding(id: string, coding: FreightCoding): Promise<DocumentRecord> {
    return fetch(`${BASE}/documents/${id}/freight-coding`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: JSON.stringify(coding),
    }).then(json<DocumentRecord>)
  },

  saveGlDefaults(glCodes: Record<string, string>): Promise<{ gl_codes: Record<string, string> }> {
    return fetch(`${BASE}/meta/gl-defaults`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: JSON.stringify({ gl_codes: glCodes }),
    }).then(json<{ gl_codes: Record<string, string> }>)
  },
}
