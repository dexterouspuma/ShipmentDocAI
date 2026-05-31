import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import type { DocumentRecord } from '../types'

const LOW_CONFIDENCE = 0.8

export default function ReviewQueue() {
  const [docs, setDocs] = useState<DocumentRecord[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [uploading, setUploading] = useState(false)

  function refresh() {
    setLoading(true)
    api.listDocuments()
      .then(setDocs)
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false))
  }

  useEffect(refresh, [])

  async function onUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    setUploading(true)
    try {
      await api.upload(file, 'arrival_notice')
      refresh()
    } catch (err) {
      setError(String(err))
    } finally {
      setUploading(false)
      e.target.value = ''
    }
  }

  return (
    <div className="queue">
      <div className="queue-header">
        <h1>Review Queue</h1>
        <label className="btn">
          {uploading ? 'Uploading…' : 'Upload PDF'}
          <input type="file" accept="application/pdf" onChange={onUpload} hidden />
        </label>
      </div>

      {error && <div className="error">{error}</div>}
      {loading ? <p>Loading…</p> : (
        <table className="grid">
          <thead>
            <tr>
              <th>Document</th><th>Type</th><th>Status</th>
              <th>B/L</th><th>Confidence</th><th>Uploaded</th>
            </tr>
          </thead>
          <tbody>
            {docs.map((d) => {
              const low = d.min_confidence != null && d.min_confidence < LOW_CONFIDENCE
              return (
                <tr key={d.id}>
                  <td><Link to={`/documents/${d.id}`}>{d.original_filename}</Link></td>
                  <td>{d.document_type}</td>
                  <td><span className={`badge ${d.status}`}>{d.status}</span></td>
                  <td>{blValue(d)}</td>
                  <td className={low ? 'low-conf' : ''}>
                    {d.min_confidence != null ? `${Math.round(d.min_confidence * 100)}%` : '—'}
                  </td>
                  <td>{new Date(d.uploaded_at).toLocaleString()}</td>
                </tr>
              )
            })}
            {docs.length === 0 && (
              <tr><td colSpan={6} className="empty">No documents yet. Upload a PDF to start.</td></tr>
            )}
          </tbody>
        </table>
      )}
    </div>
  )
}

function blValue(d: DocumentRecord): string {
  const f = d.extracted?.['bl_number'] as { value?: string } | undefined
  return f?.value ?? '—'
}
