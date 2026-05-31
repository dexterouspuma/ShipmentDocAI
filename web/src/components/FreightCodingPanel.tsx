import { useEffect, useState } from 'react'
import { api } from '../api/client'
import type { FreightCoding, FreightCodingConfig, ChargeRow } from '../types'

/** Analyst inputs for the freight cost-coding worksheet:
 *  division, cost-center distribution per charge, chemistry KGS, approvals. */
export default function FreightCodingPanel({ documentId, readOnly }: { documentId: string; readOnly?: boolean }) {
  const [config, setConfig] = useState<FreightCodingConfig | null>(null)
  const [chargeRows, setChargeRows] = useState<ChargeRow[]>([])
  const [coding, setCoding] = useState<FreightCoding | null>(null)
  const [saved, setSaved] = useState(false)
  const [defaultsSaved, setDefaultsSaved] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    Promise.all([api.freightConfig(), api.getFreightCoding(documentId)])
      .then(([cfg, resp]) => {
        setConfig(cfg)
        setChargeRows(resp.charge_rows)
        setCoding(resp.coding)
      })
      .catch((e) => setError(String(e)))
  }, [documentId])

  if (error) return <div className="error">{error}</div>
  if (!config || !coding) return <p>Loading coding…</p>

  const codedRows = chargeRows.filter((r) => r.total > 0)

  function setAlloc(chargeType: string, center: string, value: string) {
    setCoding((c) => {
      if (!c) return c
      const alloc = { ...c.cost_center_alloc }
      alloc[chargeType] = { ...(alloc[chargeType] || {}) }
      const n = parseFloat(value)
      if (isNaN(n)) delete alloc[chargeType][center]
      else alloc[chargeType][center] = n
      return { ...c, cost_center_alloc: alloc }
    })
    setSaved(false)
  }

  function setGlCode(chargeType: string, value: string) {
    setCoding((c) => {
      if (!c) return c
      const gl = { ...c.gl_codes }
      if (value.trim() === '') delete gl[chargeType]
      else gl[chargeType] = value.trim()
      return { ...c, gl_codes: gl }
    })
    setSaved(false)
  }

  function setChem(code: string, value: string) {
    setCoding((c) => {
      if (!c) return c
      const kgs = { ...c.chemistry_kgs }
      const n = parseFloat(value)
      if (isNaN(n)) delete kgs[code]
      else kgs[code] = n
      return { ...c, chemistry_kgs: kgs }
    })
    setSaved(false)
  }

  async function save() {
    try {
      await api.saveFreightCoding(documentId, coding!)
      setSaved(true)
    } catch (e) {
      setError(String(e))
    }
  }

  async function saveAsDefaults() {
    try {
      await api.saveGlDefaults(coding!.gl_codes)
      setDefaultsSaved(true)
      setTimeout(() => setDefaultsSaved(false), 2500)
    } catch (e) {
      setError(String(e))
    }
  }

  return (
    <div className="coding-panel">
      <h3>Freight Coding</h3>

      <div className="coding-row">
        <label>Division</label>
        <select value={coding.division} disabled={readOnly}
          onChange={(e) => { setCoding({ ...coding, division: e.target.value }); setSaved(false) }}>
          {config.divisions.map((d) => <option key={d} value={d}>{d}</option>)}
        </select>
      </div>

      <h4>Cost-center allocation</h4>
      {codedRows.length === 0 ? <p className="muted">No coded charges to allocate.</p> : (
        <>
        <table className="lines">
          <thead>
            <tr>
              <th>Charge</th><th>G/L code</th><th>Total</th>
              {config.cost_centers.map((cc) => <th key={cc}>{cc}</th>)}
            </tr>
          </thead>
          <tbody>
            {codedRows.map((row) => (
              <tr key={row.charge_type}>
                <td>{row.label}</td>
                <td>
                  <input className="gl-input" disabled={readOnly}
                    placeholder="G/L"
                    value={coding.gl_codes[row.charge_type] ?? row.gl_code ?? ''}
                    onChange={(e) => setGlCode(row.charge_type, e.target.value)} />
                </td>
                <td>{row.total}</td>
                {config.cost_centers.map((cc) => (
                  <td key={cc}>
                    <input className="cc-input" type="number" disabled={readOnly}
                      value={coding.cost_center_alloc[row.charge_type]?.[cc] ?? ''}
                      onChange={(e) => setAlloc(row.charge_type, cc, e.target.value)} />
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
        <div className="coding-row">
          <p className="muted" style={{ flex: 1 }}>G/L codes pre-fill from saved defaults; edit per document as needed.</p>
          {!readOnly && (
            <button onClick={saveAsDefaults} title="Remember these G/L codes for future documents">
              {defaultsSaved ? 'Defaults saved ✓' : 'Save G/L codes as defaults'}
            </button>
          )}
        </div>
        </>
      )}

      <h4>Chemistry allocation (KGS)</h4>
      <div className="chem-grid">
        {config.chemistries.map((ch) => (
          <div className="chem-item" key={ch.code}>
            <label>{ch.label} <span className="muted">{ch.code}</span></label>
            <input type="number" disabled={readOnly}
              value={coding.chemistry_kgs[ch.code] ?? ''}
              onChange={(e) => setChem(ch.code, e.target.value)} />
          </div>
        ))}
      </div>

      <div className="coding-row">
        <label>Approved by</label>
        <input value={coding.approved_by} disabled={readOnly}
          onChange={(e) => { setCoding({ ...coding, approved_by: e.target.value }); setSaved(false) }} />
        <label>Manager</label>
        <input value={coding.manager} disabled={readOnly}
          onChange={(e) => { setCoding({ ...coding, manager: e.target.value }); setSaved(false) }} />
      </div>

      {!readOnly && (
        <button className="primary" onClick={save}>{saved ? 'Saved ✓' : 'Save coding'}</button>
      )}
    </div>
  )
}
