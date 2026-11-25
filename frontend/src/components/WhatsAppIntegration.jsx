import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { FaCheckCircle, FaExclamationTriangle, FaImage, FaPaperPlane, FaSyncAlt, FaUpload, FaWhatsapp } from 'react-icons/fa'
import Header from './Header'
import { useAuth } from '../contexts/AuthContext'
import { apiGet, apiPost, apiPostForm } from '../utils/api'
import { showError, showSuccess } from '../utils/toast.jsx'
import './WhatsAppIntegration.css'

const MAX_MEDIA_BYTES = 3 * 1024 * 1024
const ALLOWED_MEDIA_TYPES = new Set(['image/jpeg', 'image/png'])

const makeRequestId = () => {
  if (window.crypto?.randomUUID) return window.crypto.randomUUID()
  const bytes = new Uint8Array(16)
  window.crypto.getRandomValues(bytes)
  bytes[6] = (bytes[6] & 0x0f) | 0x40
  bytes[8] = (bytes[8] & 0x3f) | 0x80
  const hex = [...bytes].map(value => value.toString(16).padStart(2, '0')).join('')
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`
}

const readJson = async (response) => {
  const data = await response.json().catch(() => ({}))
  if (!response.ok) throw new Error(data.error || 'The WhatsApp API request failed.')
  return data
}

const formatDate = (value) => {
  if (!value) return '-'
  const parsed = new Date(value)
  return Number.isNaN(parsed.getTime()) ? '-' : parsed.toLocaleString()
}

const StatusBadge = ({ value }) => {
  const normalized = String(value || 'unknown').toLowerCase()
  return <span className={`wa-status wa-status-${normalized}`}>{normalized}</span>
}

const WhatsAppIntegration = () => {
  const { user } = useAuth()
  const [status, setStatus] = useState(null)
  const [recipients, setRecipients] = useState([])
  const [templates, setTemplates] = useState([])
  const [messages, setMessages] = useState([])
  const [mediaAssets, setMediaAssets] = useState([])
  const [selectedFile, setSelectedFile] = useState(null)
  const [selectedPreviewUrl, setSelectedPreviewUrl] = useState('')
  const [uploadingMedia, setUploadingMedia] = useState(false)
  const [mediaError, setMediaError] = useState('')
  const [recipientId, setRecipientId] = useState('')
  const [templateKey, setTemplateKey] = useState('')
  const [mediaAssetId, setMediaAssetId] = useState('')
  const [loading, setLoading] = useState(true)
  const [sending, setSending] = useState(false)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState('')
  const [polling, setPolling] = useState(false)
  const requestIdRef = useRef('')
  const sendingRef = useRef(false)
  const mediaInputRef = useRef(null)
  const mediaObjectUrlsRef = useRef([])

  const isDemoRuntime = status?.runtime === 'demo'
  const approvedTemplates = useMemo(() => templates.filter(item => (
    item.status === 'APPROVED' && (
      isDemoRuntime
        ? item.name === (status?.allowed_template || 'hello_world')
        : item.name !== 'hello_world'
    )
  )), [isDemoRuntime, status?.allowed_template, templates])
  const selectedTemplate = approvedTemplates.find(item => `${item.name}:${item.language}` === templateKey)
  const imageRequired = selectedTemplate?.components?.some(
    component => component?.type === 'HEADER' && component.format === 'IMAGE'
  )

  const loadMessages = useCallback(async () => {
    const response = await apiGet('/api/integrations/whatsapp/messages')
    const data = await readJson(response)
    setMessages(data.messages || [])
  }, [])

  const hydrateMediaAssets = useCallback(async assets => {
    const objectUrls = []
    const hydrated = await Promise.all(assets.map(async asset => {
      try {
        const response = await apiGet(asset.preview_url)
        if (!response.ok) return { ...asset, preview_src: '' }
        const blob = await response.blob()
        const previewSrc = URL.createObjectURL(blob)
        objectUrls.push(previewSrc)
        return { ...asset, preview_src: previewSrc }
      } catch {
        return { ...asset, preview_src: '' }
      }
    }))

    mediaObjectUrlsRef.current.forEach(url => URL.revokeObjectURL(url))
    mediaObjectUrlsRef.current = objectUrls
    setMediaAssets(hydrated)
  }, [])

  const loadMedia = useCallback(async () => {
    const response = await apiGet('/api/integrations/whatsapp/media')
    const data = await readJson(response)
    await hydrateMediaAssets(data.media || [])
  }, [hydrateMediaAssets])

  const loadIntegration = useCallback(async (quiet = false) => {
    if (!quiet) setRefreshing(true)
    setError('')
    try {
      const statusResponse = await apiGet('/api/integrations/whatsapp/status')
      const statusData = await statusResponse.json().catch(() => ({}))
      const [recipientsResponse, templatesResponse, messagesResponse, mediaResponse] = await Promise.all([
        apiGet('/api/integrations/whatsapp/recipients'),
        apiGet('/api/integrations/whatsapp/templates'),
        apiGet('/api/integrations/whatsapp/messages'),
        statusData.media_configured
          ? apiGet('/api/integrations/whatsapp/media')
          : Promise.resolve(null),
      ])
      const [recipientData, templateData, messageData, mediaData] = await Promise.all([
        recipientsResponse.json().catch(() => ({})),
        templatesResponse.json().catch(() => ({})),
        messagesResponse.json().catch(() => ({})),
        mediaResponse?.json().catch(() => ({})) || {},
      ])
      setStatus(statusData)
      setRecipients(recipientData.recipients || [])
      setTemplates(templateData.templates || [])
      setMessages(messageData.messages || [])
      await hydrateMediaAssets(mediaData.media || [])
      const failed = [
        [statusResponse, statusData],
        [recipientsResponse, recipientData],
        [templatesResponse, templateData],
        [messagesResponse, messageData],
        ...(mediaResponse ? [[mediaResponse, mediaData]] : []),
      ]
        .map(([response, data]) => ({ response, data }))
        .find(item => !item.response.ok)
      if (failed) setError(failed.data.error || 'Some WhatsApp integration data could not be loaded.')
    } catch (requestError) {
      setError(requestError.message)
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [hydrateMediaAssets])

  useEffect(() => {
    if (user?.role === 'owner') loadIntegration()
  }, [loadIntegration, user?.role])

  useEffect(() => {
    if (!polling) return undefined
    const startedAt = Date.now()
    const timer = window.setInterval(async () => {
      try {
        await loadMessages()
      } catch (requestError) {
        console.error('WhatsApp message status refresh failed:', requestError)
      }
      if (Date.now() - startedAt >= 120000) setPolling(false)
    }, 8000)
    return () => window.clearInterval(timer)
  }, [loadMessages, polling])

  useEffect(() => {
    if (!recipientId && recipients.length) setRecipientId(recipients[0].id)
  }, [recipientId, recipients])

  useEffect(() => {
    if (!templateKey && approvedTemplates.length) {
      const template = approvedTemplates[0]
      setTemplateKey(`${template.name}:${template.language}`)
    }
  }, [approvedTemplates, templateKey])

  useEffect(() => () => {
    mediaObjectUrlsRef.current.forEach(url => URL.revokeObjectURL(url))
  }, [])

  useEffect(() => () => {
    if (selectedPreviewUrl) URL.revokeObjectURL(selectedPreviewUrl)
  }, [selectedPreviewUrl])

  const handleMediaSelection = event => {
    const file = event.target.files?.[0]
    setMediaError('')
    setSelectedFile(null)
    setSelectedPreviewUrl('')
    if (!file) return
    if (!ALLOWED_MEDIA_TYPES.has(file.type)) {
      const message = 'Choose a JPEG or PNG image.'
      setMediaError(message)
      showError(message)
      event.target.value = ''
      return
    }
    if (file.size > MAX_MEDIA_BYTES) {
      const message = 'Image must be 3 MiB or smaller.'
      setMediaError(message)
      showError(message)
      event.target.value = ''
      return
    }
    setSelectedFile(file)
    setSelectedPreviewUrl(URL.createObjectURL(file))
  }

  const handleMediaUpload = async () => {
    if (!selectedFile || uploadingMedia) return
    setUploadingMedia(true)
    setMediaError('')
    try {
      const formData = new FormData()
      formData.append('file', selectedFile, selectedFile.name)
      const response = await apiPostForm('/api/integrations/whatsapp/media', formData)
      await readJson(response)
      setSelectedFile(null)
      setSelectedPreviewUrl('')
      if (mediaInputRef.current) mediaInputRef.current.value = ''
      await loadMedia()
      showSuccess('Image uploaded securely.')
    } catch (requestError) {
      setMediaError(requestError.message)
      showError(requestError.message)
    } finally {
      setUploadingMedia(false)
    }
  }

  const handleSend = async () => {
    if (sendingRef.current) return
    const [templateName, language] = templateKey.split(':')
    if (!recipientId || !templateName || !language) {
      showError('Select an approved template and test recipient.')
      return
    }
    sendingRef.current = true
    setSending(true)
    if (!requestIdRef.current) requestIdRef.current = makeRequestId()
    try {
      const endpoint = isDemoRuntime
        ? '/api/integrations/whatsapp/messages'
        : '/api/integrations/whatsapp/test-messages'
      const response = await apiPost(endpoint, {
        request_id: requestIdRef.current,
        recipient_id: recipientId,
        template_name: templateName,
        language,
        ...(imageRequired && { media_asset_id: mediaAssetId }),
      })
      const data = await readJson(response)
      setMessages(current => [data.message, ...current.filter(item => item.request_id !== data.message.request_id)])
      if (data.message.status === 'failed' || data.message.status === 'unknown') {
        throw new Error(data.message.error_message || 'Meta message delivery could not be confirmed.')
      }
      requestIdRef.current = ''
      setPolling(true)
      showSuccess(
        data.message.status === 'pending'
          ? 'This test message request is already being processed.'
          : 'Meta accepted the test message. Delivery status will update here.'
      )
    } catch (requestError) {
      showError(requestError.message)
      await loadMessages().catch(() => {})
    } finally {
      sendingRef.current = false
      setSending(false)
    }
  }

  if (user?.role !== 'owner') {
    return (
      <div className="wa-page">
        <Header title="WhatsApp API" />
        <div className="wa-access-denied">Owner access is required.</div>
      </div>
    )
  }

  return (
    <div className="wa-page">
      <Header title="WhatsApp API" />
      <div className="wa-content">
        <div className="wa-heading-row">
          <div>
            <h2><FaWhatsapp aria-hidden="true" /> Meta Cloud API</h2>
            <p>Priyanka Nature Care</p>
          </div>
          <button
            type="button"
            className="wa-icon-button"
            onClick={() => loadIntegration()}
            disabled={refreshing}
            title="Refresh Meta status"
            aria-label="Refresh Meta status"
          >
            <FaSyncAlt className={refreshing ? 'wa-spin' : ''} />
          </button>
        </div>

        {error && (
          <div className="wa-alert wa-alert-error" role="alert">
            <FaExclamationTriangle />
            <span>{error}</span>
          </div>
        )}

        {loading ? (
          <div className="wa-loading">Checking the Meta connection...</div>
        ) : (
          <>
            <section className="wa-summary" aria-label="Connection summary">
              <div className="wa-summary-item">
                <span>Connection</span>
                <strong className={status?.connected ? 'wa-good' : 'wa-bad'}>
                  {status?.connected ? <FaCheckCircle /> : <FaExclamationTriangle />}
                  {status?.connected ? 'Connected' : 'Not connected'}
                </strong>
              </div>
              <div className="wa-summary-item">
                <span>Sender</span>
                <strong>{status?.sender?.verified_name || 'Unavailable'}</strong>
                <small>{status?.sender?.display_phone_number || 'No verified sender'}</small>
              </div>
              <div className="wa-summary-item">
                <span>Graph API</span>
                <strong>{status?.sender?.graph_version || 'Not configured'}</strong>
                <small>{status?.sender?.quality_rating || 'Compatibility not verified'}</small>
                <small>Phone status {status?.sender?.phone_status || 'Unknown'}</small>
              </div>
              <div className="wa-summary-item">
                <span>Webhook</span>
                <strong className={status?.webhook_ready ? 'wa-good' : 'wa-bad'}>
                  {status?.webhook_ready ? 'Verified' : 'Verification pending'}
                </strong>
              </div>
            </section>

            <div className="wa-alert wa-alert-warning">
              <FaExclamationTriangle />
              <span>
                Bulk campaigns are disabled.
                {status?.billing_required && ' Add a valid payment method in Meta WhatsApp Manager.'}
                {status?.send_disabled_reason && (!status.billing_required || !status.connected) &&
                  ` ${status.send_disabled_reason}`}
              </span>
            </div>

            {status?.missing_configuration?.length > 0 && (
              <div className="wa-alert wa-alert-warning">
                <FaExclamationTriangle />
                <span>Missing server configuration: {status.missing_configuration.join(', ')}</span>
              </div>
            )}

            {status?.media_configured ? (
              <section className="wa-section">
              <div className="wa-section-heading">
                <div>
                  <h3><FaImage aria-hidden="true" /> Promotional images</h3>
                  <p>Private JPEG and PNG media, up to 3 MiB.</p>
                </div>
                <span className="wa-count">{mediaAssets.length}</span>
              </div>

              {mediaError && (
                <div className="wa-alert wa-alert-error" role="alert">
                  <FaExclamationTriangle />
                  <span>{mediaError}</span>
                </div>
              )}

              <div className="wa-media-upload">
                <label className="wa-file-control">
                  <span>Image file</span>
                  <input
                    ref={mediaInputRef}
                    type="file"
                    accept="image/jpeg,image/png"
                    onChange={handleMediaSelection}
                    disabled={uploadingMedia}
                  />
                </label>
                <button
                  type="button"
                  className="wa-send-button"
                  onClick={handleMediaUpload}
                  disabled={!selectedFile || uploadingMedia}
                >
                  {uploadingMedia ? <FaSyncAlt className="wa-spin" /> : <FaUpload />}
                  {uploadingMedia ? 'Uploading...' : 'Upload image'}
                </button>
              </div>

              {selectedFile && selectedPreviewUrl && (
                <div className="wa-media-selection">
                  <img src={selectedPreviewUrl} alt="Selected upload preview" />
                  <div>
                    <strong>{selectedFile.name}</strong>
                    <span>{(selectedFile.size / (1024 * 1024)).toFixed(2)} MiB</span>
                  </div>
                </div>
              )}

              {mediaAssets.length ? (
                <div className="wa-media-gallery">
                  {mediaAssets.map(asset => (
                    <article className="wa-media-item" key={asset.id}>
                      <div className="wa-media-image">
                        {asset.preview_src ? (
                          <img src={asset.preview_src} alt={asset.display_filename} />
                        ) : (
                          <FaImage aria-label="Preview unavailable" />
                        )}
                      </div>
                      <div className="wa-media-details">
                        <strong>{asset.display_filename}</strong>
                        <span>{asset.width} x {asset.height} px</span>
                        <span>{(asset.byte_size / (1024 * 1024)).toFixed(2)} MiB</span>
                      </div>
                    </article>
                  ))}
                </div>
              ) : (
                <div className="wa-empty wa-media-empty">No promotional images uploaded.</div>
              )}
              </section>
            ) : (
              <div className="wa-alert wa-alert-warning">
                <FaExclamationTriangle />
                <span>Private promotional-image storage is not configured.</span>
              </div>
            )}

            <section className="wa-section">
              <div className="wa-section-heading">
                <div>
                  <h3>{isDemoRuntime ? 'Controlled demo test' : 'Controlled production test'}</h3>
                  <p>Sends a real WhatsApp message to an opted-in test recipient only when testing is enabled.</p>
                </div>
              </div>
              <div className="wa-send-grid">
                <label>
                  Test recipient
                  <select value={recipientId} onChange={event => {
                    requestIdRef.current = ''
                    setRecipientId(event.target.value)
                  }}>
                    <option value="">Select recipient</option>
                    {recipients.map(recipient => (
                      <option key={recipient.id} value={recipient.id}>
                        {recipient.label} ({recipient.masked_phone})
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  Approved template
                  <select value={templateKey} onChange={event => {
                    requestIdRef.current = ''
                    setTemplateKey(event.target.value)
                  }}>
                    <option value="">Select template</option>
                    {approvedTemplates.map(template => (
                      <option key={`${template.id}-${template.language}`} value={`${template.name}:${template.language}`}>
                        {template.name} ({template.language})
                      </option>
                    ))}
                  </select>
                </label>
                {imageRequired && (
                  <label>
                    Private image
                    <select value={mediaAssetId} onChange={event => {
                      requestIdRef.current = ''
                      setMediaAssetId(event.target.value)
                    }}>
                      <option value="">Select image</option>
                      {mediaAssets.map(asset => (
                        <option key={asset.id} value={asset.id}>{asset.display_filename}</option>
                      ))}
                    </select>
                  </label>
                )}
                <button
                  type="button"
                  className="wa-send-button"
                  onClick={handleSend}
                  disabled={sending || !status?.connected || !recipientId || !selectedTemplate ||
                    !status?.controlled_test_enabled || (imageRequired && !mediaAssetId)}
                >
                  <FaPaperPlane />
                  {sending ? 'Sending...' : 'Send test'}
                </button>
              </div>
            </section>

            <section className="wa-section">
              <div className="wa-section-heading">
                <div>
                  <h3>Templates from Meta</h3>
                  <p>These records are retrieved from the configured WhatsApp Business Account.</p>
                </div>
                <span className="wa-count">{templates.length}</span>
              </div>
              <div className="wa-table-wrap">
                <table className="wa-table">
                  <thead>
                    <tr><th>Name</th><th>Language</th><th>Category</th><th>Status</th></tr>
                  </thead>
                  <tbody>
                    {templates.length ? templates.map(template => (
                      <tr key={`${template.id}-${template.language}`}>
                        <td>{template.name}</td>
                        <td>{template.language || '-'}</td>
                        <td>{template.category}</td>
                        <td><StatusBadge value={template.status} /></td>
                      </tr>
                    )) : (
                      <tr><td colSpan="4" className="wa-empty">No live templates are available.</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            </section>

            <section className="wa-section">
              <div className="wa-section-heading">
                <div>
                  <h3>Real message status</h3>
                  <p>Accepted, sent, delivered, read and failed states come from Meta and signed webhooks.</p>
                </div>
                {polling && <span className="wa-polling"><FaSyncAlt className="wa-spin" /> Updating</span>}
              </div>
              <div className="wa-table-wrap">
                <table className="wa-table">
                  <thead>
                    <tr><th>Sent</th><th>Recipient</th><th>Template</th><th>Status</th><th>Meta message ID</th></tr>
                  </thead>
                  <tbody>
                    {messages.length ? messages.map(message => (
                      <tr key={message.request_id}>
                        <td>{formatDate(message.created_at)}</td>
                        <td>{message.recipient_label} (****{message.recipient_last4})</td>
                        <td>{message.template_name} / {message.language}</td>
                        <td>
                          <StatusBadge value={message.status} />
                          {message.error_message && <small className="wa-row-error">{message.error_message}</small>}
                        </td>
                        <td className="wa-message-id">{message.message_id || '-'}</td>
                      </tr>
                    )) : (
                      <tr><td colSpan="5" className="wa-empty">No messages have been sent.</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            </section>
          </>
        )}
      </div>
    </div>
  )
}

export default WhatsAppIntegration
