import React, { forwardRef, useEffect, useImperativeHandle, useRef } from 'react'
import SignaturePadLib from 'signature_pad'
import './SignaturePad.css'

/**
 * Thin wrapper around signature_pad (used directly, not via a React wrapper
 * package — see the design plan for the reasoning). Exposes clear/undo/
 * isEmpty/exportPNG/getStrokeCount via a ref, and handles the touch-scroll
 * and devicePixelRatio-resize concerns a signature pad needs on a tablet.
 */
const SignaturePad = forwardRef(({ disabled = false, onBeginStroke, onStrokeChange }, ref) => {
  const wrapperRef = useRef(null)
  const canvasRef = useRef(null)
  const padRef = useRef(null)

  // devicePixelRatio-aware resize that preserves existing strokes (vector data,
  // not raster) — a naive canvas resize would otherwise wipe the drawing.
  const resizeCanvas = () => {
    const canvas = canvasRef.current
    const wrapper = wrapperRef.current
    const pad = padRef.current
    if (!canvas || !wrapper || !pad) return

    const data = pad.toData()
    const ratio = Math.max(window.devicePixelRatio || 1, 1)
    canvas.width = wrapper.clientWidth * ratio
    canvas.height = wrapper.clientHeight * ratio
    canvas.getContext('2d').scale(ratio, ratio)
    pad.fromData(data)
  }

  useEffect(() => {
    const canvas = canvasRef.current
    padRef.current = new SignaturePadLib(canvas, {
      backgroundColor: 'rgba(0,0,0,0)',
      penColor: '#0f172a',
      minWidth: 1.2,
      maxWidth: 2.6,
    })
    resizeCanvas()

    const pad = padRef.current
    pad.addEventListener('beginStroke', () => {
      onBeginStroke && onBeginStroke()
    })
    pad.addEventListener('endStroke', () => {
      onStrokeChange && onStrokeChange(pad.toData().length)
    })

    // Belt-and-suspenders touch-scroll fix: touch-action:none (CSS) is the
    // primary fix in modern browsers; this non-passive touchmove listener is
    // a fallback for older tablet WebViews that don't honor touch-action.
    const preventScroll = (e) => {
      if (e.target === canvas) e.preventDefault()
    }
    canvas.addEventListener('touchmove', preventScroll, { passive: false })

    // Only resize the backing store when the CONTAINER's actual CSS size
    // changes (real orientation/layout change) — never on a software
    // keyboard opening/closing, which changes the viewport but not this
    // container's own box if it's unaffected. This is what stops the
    // keyboard from corrupting an in-progress or completed signature.
    const resizeObserver = new ResizeObserver(() => resizeCanvas())
    resizeObserver.observe(wrapperRef.current)

    return () => {
      canvas.removeEventListener('touchmove', preventScroll)
      resizeObserver.disconnect()
      pad.off()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    if (!padRef.current) return
    if (disabled) padRef.current.off()
    else padRef.current.on()
  }, [disabled])

  useImperativeHandle(ref, () => ({
    isEmpty: () => !padRef.current || padRef.current.isEmpty(),
    clear: () => {
      padRef.current?.clear()
      onStrokeChange && onStrokeChange(0)
    },
    undo: () => {
      if (!padRef.current) return
      const data = padRef.current.toData()
      if (!data || data.length === 0) return
      data.pop()
      padRef.current.fromData(data)
      onStrokeChange && onStrokeChange(padRef.current.toData().length)
    },
    getStrokeCount: () => (padRef.current ? padRef.current.toData().length : 0),
    getPointCount: () => {
      if (!padRef.current) return 0
      return padRef.current.toData().reduce((sum, stroke) => sum + (stroke.points?.length || 0), 0)
    },
    exportPNG: () => {
      if (!padRef.current || padRef.current.isEmpty()) return null
      return padRef.current.toDataURL('image/png')
    },
  }))

  return (
    <div className="signature-pad-wrapper" ref={wrapperRef}>
      <canvas ref={canvasRef} className="signature-pad-canvas" />
    </div>
  )
})

SignaturePad.displayName = 'SignaturePad'

export default SignaturePad
