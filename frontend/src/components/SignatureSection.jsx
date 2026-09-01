import React, { useEffect, useMemo, useRef, useState } from 'react'
import { apiPost } from '../utils/api'
import { API_BASE_URL, PUBLIC_BASE_URL } from '../config'
import { useBusiness } from '../contexts/BusinessContext'
import SignaturePad from './SignaturePad'
import { BRANCH_INFO } from './InvoicePreview'
import './SignatureSection.css'

const SKIP_REASONS = [
  'Customer declined to sign',
  'Customer unable to sign (medical/physical)',
  'Customer left before signing',
]

function genIdempotencyKey() {
  if (window.crypto && window.crypto.randomUUID) return window.crypto.randomUUID()
  return `${Date.now()}-${Math.random().toString(36).slice(2)}`
}

/**
 * Customer Signature panel — sits between the bill details and the
 * Download/WhatsApp actions inside InvoicePreview. Deterministically
 * dismisses any open software keyboard before enabling the pad, and keeps
 * the pad read-only once the bill is finalized (locally, or on reopen).
 */
export default function SignatureSection({ billId, invoiceData, onFinalized }) {
  const { businessName: configuredBusinessName } = useBusiness()
  const sectionRef = useRef(null)
  const padRef = useRef(null)
  const idempotencyKeyRef = useRef(genIdempotencyKey())
  const cachedSignatureRef = useRef(null) // exported PNG cached across retries

  const [strokeCount, setStrokeCount] = useState(0)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)
  const [skipModalOpen, setSkipModalOpen] = useState(false)
  const [skipReason, setSkipReason] = useState(null)
  const [skipNote, setSkipNote] = useState('')
  const [noteFocused, setNoteFocused] = useState(false)
  const [signingEnabled, setSigningEnabled] = useState(false)
  const [downloading, setDownloading] = useState(false)
  const [sendingWhatsApp, setSendingWhatsApp] = useState(false)

  const isFinalized = invoiceData?.invoice_status === 'finalized'
  const signature = invoiceData?.signature
  const pdfReady = invoiceData?.pdf_status === 'ready' || isFinalized // best-effort — see note below

  // --- Keyboard dismissal on entering signing mode ---------------------------
  // Blur whatever text field might be focused elsewhere in the app (e.g. a
  // search box left open before checkout), wait for the viewport to settle
  // back to its keyboard-closed height, THEN scroll the pad into view and
  // only then allow drawing — a stray tap during the dismiss animation must
  // not start a stroke.
  useEffect(() => {
    if (isFinalized) return
    const active = document.activeElement
    if (active && /^(INPUT|TEXTAREA|SELECT)$/.test(active.tagName)) {
      active.blur()
    } else if (active && active.isContentEditable) {
      active.blur()
    }

    let settled = false
    const enable = () => {
      if (settled) return
      settled = true
      sectionRef.current?.scrollIntoView({ block: 'center', behavior: 'smooth' })
      setSigningEnabled(true)
    }

    if (window.visualViewport) {
      const targetHeight = window.innerHeight
      const onResize = () => {
        if (Math.abs(window.visualViewport.height - targetHeight) < 40) {
          window.visualViewport.removeEventListener('resize', onResize)
          enable()
        }
      }
      window.visualViewport.addEventListener('resize', onResize)
      // Fallback in case no resize ever fires (keyboard was already closed)
      const fallback = setTimeout(enable, 350)
      return () => {
        window.visualViewport.removeEventListener('resize', onResize)
        clearTimeout(fallback)
      }
    }
    const fallback = setTimeout(enable, 300)
    return () => clearTimeout(fallback)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isFinalized])

  // Defensive: while signing mode is active, blur any text-entry element that
  // gains focus inside this section (except the explicit skip-note field,
  // and never buttons — Undo/Clear/Confirm/Skip stay keyboard/SR navigable).
  useEffect(() => {
    if (isFinalized || !signingEnabled) return
    const el = sectionRef.current
    if (!el) return
    const handler = (e) => {
      const target = e.target
      const isTextEntry = /^(INPUT|TEXTAREA)$/.test(target.tagName) || target.isContentEditable
      const isSkipNote = target.dataset && target.dataset.skipNote === 'true'
      if (isTextEntry && !isSkipNote) {
        target.blur()
      }
    }
    el.addEventListener('focusin', handler)
    return () => el.removeEventListener('focusin', handler)
  }, [isFinalized, signingEnabled])

  const resetAttempt = () => {
    idempotencyKeyRef.current = genIdempotencyKey()
    cachedSignatureRef.current = null
  }

  const submit = async (body) => {
    setSubmitting(true)
    setError(null)
    try {
      const res = await apiPost(`/api/bills/${billId}/signature`, body)
      const result = await res.json()
      if (!res.ok) {
        if (result.error === 'invoice_changed') {
          setError('This bill changed since it was generated. Please close and reopen the invoice before signing.')
        } else if (result.error === 'already_finalized' || result.error === 'idempotency_key_reused_with_different_payload') {
          // Someone else (or a duplicate tap) already finalized it — reflect that state.
          onFinalized && onFinalized(result)
        } else {
          setError(result.error || 'Could not save the signature. Please try again.')
        }
        return
      }
      onFinalized && onFinalized(result)
    } catch (e) {
      setError('Network error — your signature has not been lost. Tap Retry once you have a connection.')
    } finally {
      setSubmitting(false)
    }
  }

  const handleConfirm = () => {
    if (submitting) return // guards double-submit at the UI layer
    if (!cachedSignatureRef.current) {
      if (!padRef.current || padRef.current.isEmpty()) {
        setError('Please sign before confirming.')
        return
      }
      cachedSignatureRef.current = padRef.current.exportPNG()
    }
    submit({
      action: 'sign',
      signature_image: cachedSignatureRef.current,
      invoice_version: invoiceData.invoice_version,
      snapshot_hash: invoiceData.snapshot_hash,
      idempotency_key: idempotencyKeyRef.current,
      client_stroke_count: padRef.current ? padRef.current.getStrokeCount() : strokeCount,
    })
  }

  const handleSkipSubmit = () => {
    if (submitting) return
    const reason = skipReason + (skipNote.trim() ? ` — ${skipNote.trim()}` : '')
    submit({
      action: 'skip',
      skip_reason: reason,
      invoice_version: invoiceData.invoice_version,
      snapshot_hash: invoiceData.snapshot_hash,
      idempotency_key: idempotencyKeyRef.current,
    })
  }

  const closeSkipModal = () => {
    // Blur the note field and let the keyboard close before restoring the view.
    if (document.activeElement && document.activeElement.dataset?.skipNote === 'true') {
      document.activeElement.blur()
    }
    setTimeout(() => {
      setSkipModalOpen(false)
      setSkipReason(null)
      setSkipNote('')
      sectionRef.current?.scrollIntoView({ block: 'center', behavior: 'smooth' })
    }, 200)
  }

  const handleDownload = async () => {
    if (downloading) return
    setDownloading(true)
    try {
      const sessionAuth = sessionStorage.getItem('auth_token')
      const response = await fetch(`${API_BASE_URL}/api/bills/${billId}/invoice/pdf`, {
        headers: sessionAuth ? { Authorization: `Bearer ${sessionAuth}` } : {},
      })
      if (!response.ok) {
        const body = await response.json().catch(() => ({}))
        setError(body.error === 'invoice_not_finalized'
          ? 'This invoice is not finalized yet.'
          : (body.error || 'Failed to prepare the PDF. Please retry.'))
        return
      }
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `invoice_${invoiceData?.bill_number || billId}.pdf`
      document.body.appendChild(a)
      a.click()
      a.remove()
      window.URL.revokeObjectURL(url)
    } catch (e) {
      setError('Failed to download the PDF. Please retry.')
    } finally {
      setDownloading(false)
    }
  }

  const handleSendWhatsApp = async () => {
    if (sendingWhatsApp) return
    const customer = invoiceData?.customer
    if (!customer?.mobile) return
    setSendingWhatsApp(true)
    try {
      let phoneNumber = customer.mobile.replace(/[^0-9]/g, '')
      if (phoneNumber.length === 10) phoneNumber = '91' + phoneNumber

      const customerName = customer?.name || 'Customer'
      const businessName = configuredBusinessName || 'Priyanka Nature Cure'
      const feedbackLink = `${PUBLIC_BASE_URL}/feedback`

      let signoffPhone = ''
      const branchName = invoiceData?.branch?.name?.trim()
      const branchKey = branchName && Object.keys(BRANCH_INFO).find(k => k.toLowerCase() === branchName.toLowerCase())
      if (branchKey && BRANCH_INFO[branchKey]?.phone) {
        signoffPhone = BRANCH_INFO[branchKey].phone.split(',')[0].trim()
      }

      let invoiceLink = ''
      try {
        const res = await apiPost(`/api/bills/${billId}/share-link`)
        if (res.ok) {
          const data = await res.json()
          invoiceLink = `${PUBLIC_BASE_URL}/i/${data.share_code}/pdf`
        } else {
          const body = await res.json().catch(() => ({}))
          if (body.error === 'invoice_not_finalized') {
            setError('This invoice is not finalized yet.')
            return
          }
        }
      } catch (e) {
        // Fall through to text-only message if link generation fails
      }

      let message = `Dear ${customerName},\n\nThank you for visiting *${businessName}*!\n\n`
      if (invoiceLink) message += `View your *invoice* here:\n\n${invoiceLink}\n\n`
      message += `We'd love to hear from you! Share your *feedback* here:\n\n${feedbackLink}\n\nThanks\n${businessName}`
      if (signoffPhone) message += `\n${signoffPhone}`

      window.open(`https://wa.me/${phoneNumber}?text=${encodeURIComponent(message)}`, '_blank')
    } finally {
      setSendingWhatsApp(false)
    }
  }

  // --- Read-only: already finalized (fresh confirm, or reopening later) -----
  if (isFinalized) {
    return (
      <div className="signature-section" ref={sectionRef}>
        <h3 className="signature-section-heading">Customer Signature</h3>
        {signature?.status === 'signed' && (
          <div className="signature-readonly-box">
            <img src={signature.image} alt="Customer signature" className="signature-readonly-img" />
            <p className="signature-caption">
              Signed by {signature.signed_by_customer_name || invoiceData?.customer?.name || 'Customer'}
              {signature.signed_at ? ` · ${new Date(signature.signed_at).toLocaleString()}` : ''}
            </p>
            {signature.finalized_by_name && (
              <p className="signature-caption-muted">Processed by: {signature.finalized_by_name}</p>
            )}
          </div>
        )}
        {signature?.status === 'skipped' && (
          <div className="signature-readonly-box signature-skipped-box">
            <p className="signature-caption">Signature not collected — {signature.skip_reason}</p>
          </div>
        )}
        {signature?.status === 'not_required' && (
          <div className="signature-readonly-box signature-skipped-box">
            <p className="signature-caption-muted">
              Customer signature was not captured because this invoice was created before signature capture was introduced.
            </p>
          </div>
        )}

        <div className="signature-actions-row">
          <button
            className="invoice-action-btn download-btn"
            onClick={handleDownload}
            disabled={downloading || !pdfReady}
          >
            {downloading ? 'Preparing…' : 'Download Bill'}
          </button>
          <button
            className="invoice-action-btn whatsapp-btn"
            onClick={handleSendWhatsApp}
            disabled={sendingWhatsApp || !pdfReady || !invoiceData?.customer?.mobile}
          >
            {sendingWhatsApp ? 'Opening…' : 'Send via WhatsApp'}
          </button>
        </div>
        {error && <p className="signature-error">{error}</p>}
      </div>
    )
  }

  // --- Live signing state -----------------------------------------------------
  return (
    <div className="signature-section" ref={sectionRef}>
      <h3 className="signature-section-heading">Customer Signature</h3>
      <p className="signature-ack-text">
        {invoiceData?.acknowledgment_statement ||
          'I confirm that I have reviewed the services, products, charges, discounts, taxes, and final amount shown on this invoice.'}
      </p>
      <p className="signature-hint">Finger or stylus</p>

      <SignaturePad
        ref={padRef}
        disabled={!signingEnabled || submitting}
        onStrokeChange={setStrokeCount}
      />

      <div className="signature-controls-row">
        <button
          className="signature-control-btn"
          onClick={() => { padRef.current?.clear(); cachedSignatureRef.current = null }}
          disabled={submitting}
        >
          Clear
        </button>
        <button
          className="signature-control-btn"
          onClick={() => padRef.current?.undo()}
          disabled={submitting}
        >
          Undo
        </button>
      </div>

      <button className="signature-skip-link" onClick={() => setSkipModalOpen(true)} disabled={submitting}>
        Customer unable / refuses to sign
      </button>

      <button
        className="signature-confirm-btn"
        onClick={handleConfirm}
        disabled={submitting || strokeCount === 0}
      >
        {submitting ? 'Saving…' : 'Confirm & Finalize Bill'}
      </button>

      {error && (
        <div className="signature-error-box">
          <p className="signature-error">{error}</p>
          <button className="signature-control-btn" onClick={() => { setError(null); handleConfirm() }}>
            Retry
          </button>
        </div>
      )}

      <div className="signature-actions-row signature-actions-disabled">
        <button className="invoice-action-btn download-btn" disabled>Download Bill</button>
        <button className="invoice-action-btn whatsapp-btn" disabled>Send via WhatsApp</button>
      </div>
      <p className="signature-caption-muted signature-disabled-note">
        Disabled until the customer signature is finalized
      </p>

      {skipModalOpen && (
        <div className="signature-skip-overlay" onClick={closeSkipModal}>
          <div className="signature-skip-modal" onClick={(e) => e.stopPropagation()}>
            <h4>Customer unable / refuses to sign</h4>
            <div className="signature-skip-reasons">
              {SKIP_REASONS.map((reason) => (
                <button
                  key={reason}
                  className={`signature-skip-reason-btn${skipReason === reason ? ' selected' : ''}`}
                  onClick={() => setSkipReason(reason)}
                >
                  {reason}
                </button>
              ))}
            </div>
            <textarea
              data-skip-note="true"
              className={`signature-skip-note${noteFocused ? ' focused' : ''}`}
              placeholder="Optional note (tap to type)"
              value={skipNote}
              onChange={(e) => setSkipNote(e.target.value)}
              onFocus={() => setNoteFocused(true)}
              onBlur={() => setNoteFocused(false)}
            />
            <div className="signature-skip-modal-actions">
              <button className="signature-control-btn" onClick={closeSkipModal} disabled={submitting}>Cancel</button>
              <button
                className="signature-confirm-btn signature-skip-confirm-btn"
                onClick={handleSkipSubmit}
                disabled={submitting || !skipReason}
              >
                {submitting ? 'Saving…' : 'Confirm without signature'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
