import React, { useRef } from 'react'
import DatePicker from 'react-datepicker'
import { FaCalendarAlt } from 'react-icons/fa'
import 'react-datepicker/dist/react-datepicker.css'
import './ClassicDatePicker.css'

/**
 * Compact, consistent date picker used across the app.
 * Wraps react-datepicker with the wrapped input + display + calendar-icon pattern
 * from QuickSale, so every page gets the same look.
 *
 * Props:
 *   value          "YYYY-MM-DD" ISO date string (empty string for no value)
 *   onChange(iso)  called with new ISO date string (or '' if cleared)
 *   placeholder    shown when no date is selected
 *   allowEmpty     allow the field to be cleared (default true)
 *   minDate, maxDate  passed to react-datepicker
 *   disabled
 */
const ClassicDatePicker = ({
  value,
  onChange,
  placeholder = 'Select date',
  allowEmpty = true,
  minDate,
  maxDate,
  disabled = false,
}) => {
  const pickerRef = useRef(null)
  const selected = value ? new Date(value) : null

  const toIso = (d) => {
    if (!d) return ''
    const y = d.getFullYear()
    const m = String(d.getMonth() + 1).padStart(2, '0')
    const day = String(d.getDate()).padStart(2, '0')
    return `${y}-${m}-${day}`
  }

  const displayLabel = selected
    ? `${String(selected.getDate()).padStart(2, '0')}-${String(selected.getMonth() + 1).padStart(2, '0')}-${selected.getFullYear()}`
    : ''

  const openPicker = () => {
    if (disabled) return
    // react-datepicker exposes setOpen via its ref
    if (pickerRef.current && typeof pickerRef.current.setOpen === 'function') {
      pickerRef.current.setOpen(true)
    }
  }

  return (
    <div
      className={`classic-date-wrapper ${disabled ? 'disabled' : ''}`}
      onClick={openPicker}
      role="button"
      tabIndex={disabled ? -1 : 0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault()
          openPicker()
        }
      }}
    >
      <DatePicker
        ref={pickerRef}
        selected={selected}
        onChange={(date) => onChange(date ? toIso(date) : '')}
        dateFormat="dd/MM/yyyy"
        className="classic-date-hidden-input"
        placeholderText={placeholder}
        minDate={minDate}
        maxDate={maxDate}
        disabled={disabled}
        isClearable={false}
        shouldCloseOnSelect={true}
        popperPlacement="bottom-start"
      />
      <span className="classic-date-display">
        {displayLabel || <span className="classic-date-placeholder">{placeholder}</span>}
      </span>
      <span className="classic-date-icon"><FaCalendarAlt /></span>
    </div>
  )
}

export default ClassicDatePicker
