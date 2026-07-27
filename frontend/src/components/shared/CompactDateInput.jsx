import React from 'react'
import CompactSelect from './CompactSelect'

const MONTH_LABELS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
const MONTH_OPTIONS = MONTH_LABELS.map((label, i) => ({
  value: String(i + 1).padStart(2, '0'),
  label,
}))
const CURRENT_YEAR = new Date().getFullYear()
const YEAR_OPTIONS = Array.from({ length: 6 }, (_, i) => {
  const y = CURRENT_YEAR - 2 + i
  return { value: String(y), label: String(y) }
})

/**
 * Compact date picker replacing native <input type="date">.
 * Renders three small dropdowns (Day / Month / Year) — no huge Chrome touch picker.
 *
 * Props:
 *   value          ISO date string "YYYY-MM-DD" (or empty string)
 *   onChange(iso)  called with new ISO date string
 *   className      passed through to each dropdown's trigger
 *   allowEmpty     if true, includes an "--" option so user can clear the date
 */
const CompactDateInput = ({ value, onChange, className = 'compact-date-part', allowEmpty = false }) => {
  const today = new Date().toISOString().split('T')[0]
  const src = value || (allowEmpty ? '' : today)
  const [dy, dm, dd] = src ? src.split('-') : ['', '', '']

  const yearNum = parseInt(dy, 10) || CURRENT_YEAR
  const monthNum = parseInt(dm, 10) || 1
  const daysInMonth = new Date(yearNum, monthNum, 0).getDate()
  const dayOptions = Array.from({ length: daysInMonth }, (_, i) => ({
    value: String(i + 1).padStart(2, '0'),
    label: String(i + 1).padStart(2, '0'),
  }))

  const setPart = (y, m, d) => {
    if (!y || !m || !d) {
      // Partial state — if allowEmpty and everything empty, clear
      if (allowEmpty && !y && !m && !d) {
        onChange('')
        return
      }
      // Otherwise fill missing with today's parts
      const [ty, tm, td] = today.split('-')
      y = y || ty
      m = m || tm
      d = d || td
    }
    const dim = new Date(parseInt(y, 10), parseInt(m, 10), 0).getDate()
    const dayClamped = Math.min(parseInt(d, 10), dim)
    onChange(`${y}-${m}-${String(dayClamped).padStart(2, '0')}`)
  }

  return (
    <div style={{ display: 'inline-flex', gap: 6, alignItems: 'center', flexWrap: 'wrap' }}>
      <div style={{ width: 70, flexShrink: 0 }}>
        <CompactSelect
          className={className}
          value={dd}
          onChange={(v) => setPart(dy, dm, v)}
          options={dayOptions}
          placeholder="Day"
        />
      </div>
      <div style={{ width: 88, flexShrink: 0 }}>
        <CompactSelect
          className={className}
          value={dm}
          onChange={(v) => setPart(dy, v, dd)}
          options={MONTH_OPTIONS}
          placeholder="Month"
        />
      </div>
      <div style={{ width: 96, flexShrink: 0 }}>
        <CompactSelect
          className={className}
          value={dy}
          onChange={(v) => setPart(v, dm, dd)}
          options={YEAR_OPTIONS}
          placeholder="Year"
        />
      </div>
    </div>
  )
}

export default CompactDateInput
