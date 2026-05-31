import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import type { DocumentRecord, ExtractedField } from '../types'
import FieldRow from './FieldRow'
import FreightCodingPanel from './FreightCodingPanel'

// The scalar fields shown in the review panel, in display order.
const FIELDS: [string, string][] = [
  ['Issuer', 'issuer_name'],
  ['Reference No', 'reference_no'],
  ['Issue Date', 'issue_date'],
  ['B/L Number', 'bl_number'],
  ['Container No', 'container_no'],
  ['Seal No', 'seal_no'],
  ['Port of Loading', 'port_of_loading'],
  ['Port of Discharge', 'port_of_discharge'],
  ['ETA', 'eta'],
  ['Gross Weight', 'gross_weight'],
  ['No. of Packages', 'no_of_packages'],
  ['Goods Description', 'goods_description'],
  ['Incoterms', 'incoterms'],
  ['Freight Terms', 'freight_terms'],
  ['Total Due', 'total_due'],
  ['Currency', 'currency'],
]

export default function DocumentReview() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [doc, setDoc] = useState<DocumentRecord | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    if (!id) return
    api.getDocument(id)
      .then(async (d) => {
        // Move into review state on open (idempotent server-side).
        if (d.status === 'extracted') {
          try { return setDoc(await api.openForReview(id)) } catch { /* fall through */ }
        }
        setDoc(d)
      })
      .catch((e) => setError(String(e)))
  }, [id])

  if (error) return <div className="error">{error}</div>
  if (!doc || !id) return <p>Loading…</p>

  const ex = doc.extracted
  const field = (path: string) => ex?.[path] as ExtractedField | undefined

  async function saveField(path: string, value: string) {
    const updated = await api.editField(id!, path, value)
    setDoc(updated)
  }

  async function approve() {
    setBusy(true)
    try { setDoc(await api.approve(id!)) } catch (e) { setError(String(e)) } finally { setBusy(false) }
  }

  async function reject() {
    const reason = window.prompt('Reason for rejection?') ?? ''
    setBusy(true)
    try { setDoc(await api.reject(id!, reason)) } catch (e) { setError(String(e)) } finally { setBusy(false) }
  }

  const approved = doc.status === 'approved' || doc.status === 'cover_sheet_generated'

  return (
    <div className="review">
      <div className="review-bar">
        <button onClick={() => navigate('/')}>← Queue</button>
        <strong>{doc.original_filename}</strong>
        <span className={`badge ${doc.status}`}>{doc.status}</span>
        <div className="spacer" />
        {!approved && <>
          <button className="primary" disabled={busy} onClick={approve}>Approve</button>
          <button className="danger" disabled={busy} onClick={reject}>Reject</button>
        </>}
        {approved && <>
          <a className="btn" href={api.coverSheetUrl(id, 'pdf')} target="_blank" rel="noreferrer">Cover Sheet (PDF)</a>
          <a className="btn" href={api.coverSheetUrl(id, 'excel')} target="_blank" rel="noreferrer">Cover Sheet (Excel)</a>
        </>}
      </div>

      <div className="review-split">
        {/* Left: original PDF (browser-native viewer). */}
        <div className="pdf-pane">
          <iframe title="source pdf" src={api.fileUrl(id)} />
        </div>

        {/* Right: editable extracted fields. */}
        <div className="fields-pane">
          <h2>Extracted Fields</h2>
          {FIELDS.map(([label, path]) => (
            <FieldRow key={path} label={label} fieldPath={path}
              field={field(path)} onSave={saveField} readOnly={approved} />
          ))}

          {Array.isArray(ex?.['charges']) && (ex!['charges'] as unknown[]).length > 0 && (
            <>
              <h3>Charges</h3>
              <table className="lines">
                <thead><tr><th>Description</th><th>Basis</th><th>Amount</th></tr></thead>
                <tbody>
                  {(ex!['charges'] as Array<Record<string, ExtractedField>>).map((c, i) => (
                    <tr key={i}>
                      <td>{c.description?.value as string ?? ''}</td>
                      <td>{c.basis?.value as string ?? ''}</td>
                      <td>{c.amount?.value as number ?? ''}</td>
                    </tr>
                  ))}
                </tbody>
              </table>

              {/* Freight cost-coding inputs feed the generated coding worksheet. */}
              <FreightCodingPanel documentId={id} readOnly={approved} />
            </>
          )}
        </div>
      </div>
    </div>
  )
}
