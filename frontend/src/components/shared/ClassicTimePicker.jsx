import React, { useState, useRef, useEffect } from 'react'
import { createPortal } from 'react-dom'
import { FaClock } from 'react-icons/fa'

/**
 * Analog clock-face time picker.
 * Trigger: compact button showing "HH:MM" with a clock icon.
 * Popup: a round clock face — tap an hour (1-12), then tap a minute (0, 5, 10, ... 55).
 * AM/PM toggle at the top, "Now" + "OK" actions at the bottom.
 *
 * Props:
 *   value           "HH:MM" 24-hour string ('17:30') or ''
 *   onChange(str)   called with new "HH:MM" 24-hour string
 *   placeholder
 *   minuteStep      minute granularity (default 5 → 0, 5, 10, ... 55). Set 1 for every minute.
 *   className       passed to the trigger button
 *   disabled
 */
const ClassicTimePicker = ({
  value,
  onChange,
  placeholder = 'HH:MM',
  minuteStep = 5,
  className = '',
  disabled = false,
}) => {
  const [isOpen, setIsOpen] = useState(false)
  const [mode, setMode] = useState('hour') // 'hour' | 'minute'
  const [pos, setPos] = useState({ top: 0, left: 0 })
  const triggerRef = useRef(null)
  const popupRef = useRef(null)

  // Parse current value — default to now
  const parseValue = () => {
    const m = (value || '').match(/^(\d{1,2}):(\d{1,2})$/)
    if (m) return { h: parseInt(m[1], 10), m: parseInt(m[2], 10) }
    const now = new Date()
    return { h: now.getHours(), m: 0 }
  }
  const { h: curH, m: curM } = parseValue()
  const isPM = curH >= 12
  const displayHour = ((curH % 12) || 12) // 0 → 12, 13 → 1, etc.

  const updatePos = () => {
    if (!triggerRef.current) return
    const rect = triggerRef.current.getBoundingClientRect()
    const POPUP_W = 260
    const POPUP_H = 340
    const vw = window.innerWidth
    const vh = window.innerHeight
    let left = rect.left
    if (left + POPUP_W > vw - 8) left = Math.max(8, vw - POPUP_W - 8)
    let top = rect.bottom + 4
    if (top + POPUP_H > vh - 8) top = Math.max(8, rect.top - POPUP_H - 4)
    setPos({ top, left })
  }

  useEffect(() => {
    if (!isOpen) return
    updatePos()
    setMode('hour') // reset to hour step whenever picker opens
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
        popupRef.current && !popupRef.current.contains(e.target)
      ) {
        setIsOpen(false)
      }
    }
    document.addEventListener('mousedown', onOutside)
    return () => document.removeEventListener('mousedown', onOutside)
  }, [])

  const setTime = (h24, m) => {
    const hh = String(h24).padStart(2, '0')
    const mm = String(m).padStart(2, '0')
    onChange(`${hh}:${mm}`)
  }

  const pickHour = (displayH) => {
    // Convert display hour (1-12) back to 24h based on AM/PM
    let h24 = displayH % 12
    if (isPM) h24 += 12
    setTime(h24, curM)
    setMode('minute')
  }

  const pickMinute = (m) => {
    setTime(curH, m)
    // Keep popup open briefly so user sees the selection, then close
    setTimeout(() => setIsOpen(false), 120)
  }

  const togglePM = (nextIsPM) => {
    if (nextIsPM === isPM) return
    let h24 = curH
    if (nextIsPM && h24 < 12) h24 += 12
    else if (!nextIsPM && h24 >= 12) h24 -= 12
    setTime(h24, curM)
  }

  const setNow = () => {
    const now = new Date()
    const roundedMin = Math.round(now.getMinutes() / minuteStep) * minuteStep
    const clampedMin = Math.min(55, roundedMin)
    setTime(now.getHours(), clampedMin)
  }

  const displayLabel = value && /^\d{1,2}:\d{1,2}$/.test(value) ? value : ''

  // Clock face geometry
  const FACE_SIZE = 220
  const CENTER = FACE_SIZE / 2
  const NUMBER_RADIUS = 90
  const NUMBER_SIZE = 32

  // Numbers to render on the face — hours 1-12 for hour mode, minutes 0/5/10...55 for minute mode
  const hourNumbers = Array.from({ length: 12 }, (_, i) => i + 1)
  const minuteNumbers = Array.from({ length: 12 }, (_, i) => i * 5) // Always 12 around the face for a readable clock

  // Compute position on the circle (angle 0 = 12 o'clock straight up)
  const posOnCircle = (indexOfTwelve) => {
    const angle = (indexOfTwelve / 12) * 2 * Math.PI - Math.PI / 2
    return {
      left: CENTER + NUMBER_RADIUS * Math.cos(angle) - NUMBER_SIZE / 2,
      top: CENTER + NUMBER_RADIUS * Math.sin(angle) - NUMBER_SIZE / 2,
    }
  }

  // Hand angle in degrees (0 = pointing up, clockwise)
  const handAngle = mode === 'hour'
    ? (displayHour % 12) * 30
    : (curM / 5) * 30
  const handHeadPos = mode === 'hour'
    ? posOnCircle(displayHour % 12 === 0 ? 12 : displayHour)
    : posOnCircle(Math.round(curM / 5) === 0 ? 12 : Math.round(curM / 5))

  const numStyleBase = {
    position: 'absolute',
    width: NUMBER_SIZE,
    height: NUMBER_SIZE,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: '50%',
    fontSize: 14,
    fontWeight: 500,
    cursor: 'pointer',
    userSelect: 'none',
    color: '#374151',
    transition: 'background 0.12s, color 0.12s',
    zIndex: 2,
  }

  const activeNumStyle = {
    background: '#0f766e',
    color: '#fff',
    fontWeight: 600,
  }

  return (
    <>
      <button
        ref={triggerRef}
        type="button"
        className={className}
        disabled={disabled}
        onClick={() => !disabled && setIsOpen(v => !v)}
        style={{
          width: '100%',
          minWidth: 96,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: 6,
          padding: '8px 10px',
          border: '1.5px solid #e5e7eb',
          borderRadius: 8,
          background: 'white',
          cursor: disabled ? 'not-allowed' : 'pointer',
          fontWeight: 400,
          fontFamily: 'inherit',
          fontSize: 14,
          color: displayLabel ? '#111827' : '#9ca3af',
          height: 38,
        }}
      >
        <span style={{ flex: 1, textAlign: 'left' }}>{displayLabel || placeholder}</span>
        <FaClock style={{ color: '#0f766e', fontSize: 13, flexShrink: 0 }} />
      </button>
      {isOpen && createPortal(
        <div
          ref={popupRef}
          style={{
            position: 'fixed',
            top: pos.top,
            left: pos.left,
            width: 260,
            background: '#fff',
            border: '1px solid #e5e7eb',
            borderRadius: 14,
            boxShadow: '0 12px 32px rgba(0,0,0,0.14)',
            zIndex: 9999,
            padding: 14,
            userSelect: 'none',
          }}
        >
          {/* Top readout: big HH:MM display + AM/PM toggle */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            marginBottom: 12,
          }}>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 4, fontSize: 28, fontWeight: 700, color: '#111827' }}>
              <span
                onClick={() => setMode('hour')}
                style={{
                  cursor: 'pointer',
                  padding: '2px 8px',
                  borderRadius: 6,
                  background: mode === 'hour' ? '#ecfeff' : 'transparent',
                  color: mode === 'hour' ? '#0f766e' : '#111827',
                  transition: 'background 0.15s',
                }}
              >
                {String(displayHour).padStart(2, '0')}
              </span>
              <span>:</span>
              <span
                onClick={() => setMode('minute')}
                style={{
                  cursor: 'pointer',
                  padding: '2px 8px',
                  borderRadius: 6,
                  background: mode === 'minute' ? '#ecfeff' : 'transparent',
                  color: mode === 'minute' ? '#0f766e' : '#111827',
                  transition: 'background 0.15s',
                }}
              >
                {String(curM).padStart(2, '0')}
              </span>
            </div>
            <div style={{
              display: 'flex',
              flexDirection: 'column',
              border: '1px solid #e5e7eb',
              borderRadius: 6,
              overflow: 'hidden',
              fontSize: 11,
              fontWeight: 600,
            }}>
              <button
                type="button"
                onClick={() => togglePM(false)}
                style={{
                  padding: '3px 10px',
                  border: 'none',
                  background: !isPM ? '#0f766e' : '#fff',
                  color: !isPM ? '#fff' : '#6b7280',
                  cursor: 'pointer',
                  minHeight: 'auto',
                }}
              >
                AM
              </button>
              <button
                type="button"
                onClick={() => togglePM(true)}
                style={{
                  padding: '3px 10px',
                  border: 'none',
                  borderTop: '1px solid #e5e7eb',
                  background: isPM ? '#0f766e' : '#fff',
                  color: isPM ? '#fff' : '#6b7280',
                  cursor: 'pointer',
                  minHeight: 'auto',
                }}
              >
                PM
              </button>
            </div>
          </div>

          {/* Clock face */}
          <div style={{
            position: 'relative',
            width: FACE_SIZE,
            height: FACE_SIZE,
            margin: '0 auto',
            background: '#f8fafc',
            borderRadius: '50%',
            border: '1px solid #e5e7eb',
          }}>
            {/* Center dot */}
            <div style={{
              position: 'absolute',
              left: CENTER - 4,
              top: CENTER - 4,
              width: 8,
              height: 8,
              borderRadius: '50%',
              background: '#0f766e',
              zIndex: 3,
            }} />

            {/* Hand — line from center to selected number */}
            <div style={{
              position: 'absolute',
              left: CENTER,
              top: CENTER - 1,
              width: NUMBER_RADIUS - NUMBER_SIZE / 2,
              height: 2,
              background: '#0f766e',
              transformOrigin: '0 50%',
              transform: `rotate(${handAngle - 90}deg)`,
              zIndex: 1,
              transition: 'transform 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
            }} />

            {/* Hand head — filled circle at the tip */}
            <div style={{
              position: 'absolute',
              left: handHeadPos.left,
              top: handHeadPos.top,
              width: NUMBER_SIZE,
              height: NUMBER_SIZE,
              borderRadius: '50%',
              background: '#0f766e',
              opacity: 0.15,
              zIndex: 1,
              transition: 'left 0.2s cubic-bezier(0.4, 0, 0.2, 1), top 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
            }} />

            {/* Numbers */}
            {mode === 'hour' ? (
              hourNumbers.map((n, i) => {
                const circlePos = posOnCircle(n)
                const isActive = n === displayHour
                return (
                  <div
                    key={n}
                    onClick={() => pickHour(n)}
                    style={{
                      ...numStyleBase,
                      left: circlePos.left,
                      top: circlePos.top,
                      ...(isActive ? activeNumStyle : {}),
                    }}
                  >
                    {n}
                  </div>
                )
              })
            ) : (
              minuteNumbers.map((n, i) => {
                const positionIndex = i === 0 ? 12 : i // put 0 at the top (12 o'clock position)
                const circlePos = posOnCircle(positionIndex)
                const isActive = n === curM
                return (
                  <div
                    key={n}
                    onClick={() => pickMinute(n)}
                    style={{
                      ...numStyleBase,
                      left: circlePos.left,
                      top: circlePos.top,
                      fontSize: 13,
                      ...(isActive ? activeNumStyle : {}),
                    }}
                  >
                    {String(n).padStart(2, '0')}
                  </div>
                )
              })
            )}
          </div>

          {/* Action row */}
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginTop: 12,
            gap: 8,
          }}>
            <button
              type="button"
              onClick={setNow}
              style={{
                padding: '6px 12px',
                border: '1px solid #e5e7eb',
                borderRadius: 6,
                background: '#fff',
                color: '#0f766e',
                fontSize: 12,
                fontWeight: 600,
                cursor: 'pointer',
                minHeight: 'auto',
              }}
            >
              Now
            </button>
            <div style={{ display: 'flex', gap: 6 }}>
              <button
                type="button"
                onClick={() => setIsOpen(false)}
                style={{
                  padding: '6px 14px',
                  border: '1px solid #e5e7eb',
                  borderRadius: 6,
                  background: '#fff',
                  color: '#6b7280',
                  fontSize: 12,
                  fontWeight: 600,
                  cursor: 'pointer',
                  minHeight: 'auto',
                }}
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() => setIsOpen(false)}
                style={{
                  padding: '6px 14px',
                  border: 'none',
                  borderRadius: 6,
                  background: '#0f766e',
                  color: '#fff',
                  fontSize: 12,
                  fontWeight: 600,
                  cursor: 'pointer',
                  minHeight: 'auto',
                }}
              >
                OK
              </button>
            </div>
          </div>
        </div>,
        document.body
      )}
    </>
  )
}

export default ClassicTimePicker
