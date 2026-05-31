import { useState } from 'react'
import type { ExtractedField } from '../types'

const LOW_CONFIDENCE = 0.8

interface Props {
  label: string
  fieldPath: string
  field?: ExtractedField
  onSave: (fieldPath: string, value: string) => Promise<void>
  readOnly?: boolean
}

/** One editable extracted field with confidence highlighting. Low-confidence
 *  values are flagged so the analyst checks them; edits are saved (and audited). */
export default function FieldRow({ label, fieldPath, field, onSave, readOnly }: Props) {
  const [value, setValue] = useState(field?.value != null ? String(field.value) : '')
  const [saving, setSaving] = useState(false)
  const [dirty, setDirty] = useState(false)

  const conf = field?.confidence ?? null
  const low = conf != null && conf < LOW_CONFIDENCE

  async function save() {
    if (!dirty) return
    setSaving(true)
    try {
      await onSave(fieldPath, value)
      setDirty(false)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className={`field-row ${low ? 'low' : ''}`}>
      <label className="field-label">
        {label}
        {field?.edited && <span className="edited-tag" title="Edited by analyst">✎</span>}
      </label>
      <div className="field-input">
        <input
          value={value}
          disabled={readOnly}
          onChange={(e) => { setValue(e.target.value); setDirty(true) }}
          onBlur={save}
        />
        <span className={`conf ${low ? 'low' : ''}`} title="Extraction confidence">
          {conf != null ? `${Math.round(conf * 100)}%` : '—'}
        </span>
        {saving && <span className="saving">saving…</span>}
      </div>
    </div>
  )
}
