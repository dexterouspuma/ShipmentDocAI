// Mirror of the backend shared models (see shared/models.py). Kept deliberately
// loose where the backend payload is nested JSON.

export type ProcessingStatus =
  | 'uploaded' | 'queued' | 'extracting' | 'extracted' | 'extraction_failed'
  | 'in_review' | 'approved' | 'rejected' | 'cover_sheet_generated'

export type DocumentType =
  | 'arrival_notice' | 'commercial_invoice' | 'carrier_invoice'
  | 'packing_list' | 'bol' | 'unknown'

export interface ExtractedField<T = unknown> {
  value: T | null
  original_value: T | null
  confidence: number | null
  edited: boolean
  bbox?: number[] | null
  page?: number | null
}

export interface Party {
  role: string
  name: ExtractedField<string>
  address: ExtractedField<string>
  contact_tel: ExtractedField<string>
  contact_email: ExtractedField<string>
}

export interface ChargeLine {
  description: ExtractedField<string>
  basis: ExtractedField<string>
  rate: ExtractedField<number>
  amount: ExtractedField<number>
}

export interface ExtractedDocument {
  document_type: DocumentType
  transport_mode: string
  [key: string]: ExtractedField | Party[] | ChargeLine[] | string | unknown
}

export interface DocumentRecord {
  id: string
  original_filename: string
  document_type: DocumentType
  status: ProcessingStatus
  uploaded_at: string
  reviewed_by?: string | null
  page_count?: number | null
  min_confidence?: number | null
  error_message?: string | null
  extracted?: ExtractedDocument | null
}

export interface AuditEntry {
  action: string
  actor: string
  field_name?: string | null
  old_value?: string | null
  new_value?: string | null
  timestamp: string
}

// --- Freight cost-coding (PIDSA worksheet) ---
export interface FreightCoding {
  division: string
  gl_codes: Record<string, string>
  chemistry_kgs: Record<string, number>
  cost_center_alloc: Record<string, Record<string, number>>
  approved_by: string
  manager: string
}

export interface ChargeRow {
  charge_type: string
  label: string
  gl_code: string
  total: number
}

export interface FreightCodingConfig {
  charge_rows: { key: string; label: string; gl_code: string }[]
  cost_centers: string[]
  chemistries: { code: string; label: string }[]
  divisions: string[]
}

export interface FreightCodingResponse {
  coding: FreightCoding
  charge_rows: ChargeRow[]
}
