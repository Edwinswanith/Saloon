import React, { useState, useRef, useEffect } from 'react'
import { createPortal } from 'react-dom'
import { FaChevronDown } from 'react-icons/fa'

/**
 * Compact custom <select> replacement — avoids Chrome's oversized touch picker.
 *
 * Props:
 *   value         current selected value
 *   onChange(val) called with the chosen option's value
 *   options       [{ value, label }] — required
 *   placeholder   shown when no value is selected
 *   className     forwarded to the trigger input for layout (e.g. "table-select", "form-select")
 *   disabled      forwarded
 */
const CompactSelect = ({
  value,
  onChange,
  options = [],
  placeholder = 'Select',
  className = '',
  disabled = false,
  id,
  name,
}) => {
  const [isOpen, setIsOpen] = useState(false)
  const [pos, setPos] = useState({ top: 0, left: 0, width: 0 })
  const triggerRef = useRef(null)
  const dropdownRef = useRef(null)

  const selected = options.find(o => String(o.value) === String(value))
  const label = selected ? selected.label : ''

  const updatePos = () => {
    if (!triggerRef.current) return
    const rect = triggerRef.current.getBoundingClientRect()
    const MIN = 180
    const vw = window.innerWidth
    const width = Math.max(rect.width, Math.min(MIN, vw - 16))
    let left = rect.left
    if (left + width > vw - 8) left = Math.max(8, vw - width - 8)
    setPos({ top: rect.bottom + 2, left, width })
  }

  useEffect(() => {
    if (!isOpen) return
    updatePos()
    const h = () => updatePos()
    window.addEventListener('scroll', h, true)
    window.addEventListener('resize', h)
    return () => {
      window.removeEventListener('scroll', h, true)
      window.removeEventListener('resize', h)
    }
  }, [isOpen])

  useEffect(() => {
    const onOutside = (e) => {
      if (
        triggerRef.current && !triggerRef.current.contains(e.target) &&
        dropdownRef.current && !dropdownRef.current.contains(e.target)
      ) {
        setIsOpen(false)
      }
    }
    document.addEventListener('mousedown', onOutside)
    return () => document.removeEventListener('mousedown', onOutside)
  }, [])

  const choose = (opt) => {
    onChange(opt.value)
    setIsOpen(false)
  }

  return (
    <div style={{ position: 'relative', width: '100%' }}>
      <button
        ref={triggerRef}
        id={id}
        name={name}
        type="button"
        className={className}
        disabled={disabled}
        onClick={() => !disabled && setIsOpen(v => !v)}
        style={{
          width: '100%',
          textAlign: 'left',
          cursor: disabled ? 'not-allowed' : 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: 8,
          paddingRight: 28,
          fontWeight: 400,
          fontFamily: 'inherit',
        }}
      >
        <span style={{
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          whiteSpace: 'nowrap',
          color: label ? 'inherit' : '#9ca3af',
        }}>
          {label || placeholder}
        </span>
        <FaChevronDown
          style={{
            position: 'absolute',
            right: 10,
            top: '50%',
            transform: `translateY(-50%) ${isOpen ? 'rotate(180deg)' : ''}`,
            fontSize: 11,
            color: '#6b7280',
            transition: 'transform 0.15s',
            pointerEvents: 'none',
          }}
        />
      </button>
      {isOpen && createPortal(
        <ul
          ref={dropdownRef}
          style={{
            position: 'fixed',
            top: pos.top,
            left: pos.left,
            width: pos.width,
            margin: 0,
            padding: 4,
            listStyle: 'none',
            background: '#fff',
            border: '1px solid #d1d5db',
            borderRadius: 6,
            boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
            maxHeight: 240,
            overflowY: 'auto',
            zIndex: 100000, // Above any modal backdrop (modals use 10000)
          }}
        >
          {options.length === 0 ? (
            <li style={{ padding: '6px 10px', color: '#9ca3af', fontSize: 13, fontStyle: 'italic' }}>
              No options
            </li>
          ) : options.map(opt => {
            const isSel = String(opt.value) === String(value)
            return (
              <li
                key={String(opt.value)}
                onMouseDown={(e) => { e.preventDefault(); choose(opt) }}
                style={{
                  padding: '6px 10px',
                  fontSize: 13,
                  lineHeight: 1.4,
                  cursor: 'pointer',
                  background: 'transparent',
                  color: '#374151',
                  fontWeight: 400,
                  borderRadius: 4,
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = '#f3f4f6'
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = 'transparent'
                }}
              >
                {opt.label}
                {isSel && (
                  <span style={{ float: 'right', color: '#0d9488', fontSize: 12, fontWeight: 600 }}>✓</span>
                )}
              </li>
            )
          })}
        </ul>,
        document.body
      )}
    </div>
  )
}

export default CompactSelect
