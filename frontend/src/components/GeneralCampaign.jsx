import React, { useState, useEffect } from 'react';
import { FaImage, FaTimes, FaCheck, FaUsers, FaPaperPlane } from 'react-icons/fa';
import { apiGet, apiPost } from '../utils/api';
import { showSuccess, showError } from '../utils/toast.jsx';
import { useAuth } from '../contexts/AuthContext';
import { useBusiness } from '../contexts/BusinessContext';
import CompactSelect from './shared/CompactSelect';

const FILTER_TYPE_OPTIONS = [
  { value: 'all', label: 'All Customers' },
  { value: 'top10_revenue', label: 'Top 10 by Revenue' },
  { value: 'top10_visits', label: 'Top 10 by Visits' },
  { value: 'gender_female', label: 'Female Customers' },
  { value: 'gender_male', label: 'Male Customers' },
  { value: 'inactive', label: 'Inactive (60+ days)' },
];

// Default scaffold for the General campaign — greeting, offer body, CTA, sign-off.
// Uses {customer_name} (replaced per recipient) and {salon_name} (replaced from BusinessContext).
const buildGeneralTemplate = () => `Hi {customer_name}! 🌟

[Write your offer here — what is it, how much off, valid until when]

Book your appointment:
📞 Call us or walk in anytime

With love,
{salon_name} 💆‍♀️`;

const GeneralCampaign = ({ onCampaignSent }) => {
  const { currentBranch } = useAuth();
  const { businessName } = useBusiness();
  const [campaignName, setCampaignName] = useState('');
  const [messageText, setMessageText] = useState(() => buildGeneralTemplate());
  const [imageFile, setImageFile] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [imageData, setImageData] = useState(null);
  const [imageMimeType, setImageMimeType] = useState(null);
  const [filterType, setFilterType] = useState('all');
  const [customers, setCustomers] = useState([]);
  const [selectedCustomers, setSelectedCustomers] = useState(new Set());
  const [loadingCustomers, setLoadingCustomers] = useState(false);
  const [sending, setSending] = useState(false);
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [sendQueue, setSendQueue] = useState([]); // [{id, name, mobile, status: 'pending'|'sent'|'skipped'}]
  const [queueIndex, setQueueIndex] = useState(0);
  const [showQueueModal, setShowQueueModal] = useState(false);

  useEffect(() => {
    if (filterType && currentBranch) {
      fetchCustomers();
    }
  }, [filterType, currentBranch]);

  const fetchCustomers = async () => {
    try {
      setLoadingCustomers(true);
      const response = await apiGet(`/api/campaigns/customers?filter=${filterType}`);
      if (!response.ok) throw new Error('Failed to fetch customers');
      const data = await response.json();
      setCustomers(data.customers || []);
      // Auto-select all customers (consent not required for direct WhatsApp send)
      setSelectedCustomers(new Set((data.customers || []).map(c => c.id)));
    } catch (error) {
      console.error('Error fetching customers:', error);
      showError('Failed to load customers');
    } finally {
      setLoadingCustomers(false);
    }
  };

  const handleImageUpload = (e) => {
    const file = e.target.files[0];
    if (!file) return;

    if (!file.type.startsWith('image/')) {
      showError('Please select an image file');
      return;
    }

    if (file.size > 5 * 1024 * 1024) { // 5MB limit
      showError('Image size should be less than 5MB');
      return;
    }

    setImageFile(file);
    setImageMimeType(file.type);

    const reader = new FileReader();
    reader.onloadend = () => {
      const base64String = reader.result.split(',')[1]; // Remove data:image/...;base64, prefix
      setImageData(base64String);
      setImagePreview(reader.result);
    };
    reader.readAsDataURL(file);
  };

  const removeImage = () => {
    setImageFile(null);
    setImagePreview(null);
    setImageData(null);
    setImageMimeType(null);
  };

  const toggleCustomer = (customerId) => {
    const newSelected = new Set(selectedCustomers);
    if (newSelected.has(customerId)) {
      newSelected.delete(customerId);
    } else {
      newSelected.add(customerId);
    }
    setSelectedCustomers(newSelected);
  };

  const toggleSelectAll = () => {
    if (selectedCustomers.size === customers.length) {
      setSelectedCustomers(new Set());
    } else {
      setSelectedCustomers(new Set(customers.map(c => c.id)));
    }
  };

  const handleSend = async () => {
    if (!messageText.trim()) {
      showError('Please enter a message');
      return;
    }

    // Block sending if the bracketed instruction placeholder hasn't been replaced.
    // Matches things like "[Write your offer here ...]" — anything wrapped in [ ].
    if (/\[[^\]]+\]/.test(messageText)) {
      showError('Please replace the [bracketed instruction] in your message with your actual offer text before sending.');
      return;
    }

    if (selectedCustomers.size === 0) {
      showError('Please select at least one customer');
      return;
    }

    setShowConfirmModal(true);
  };

  const formatPhoneNumber = (mobile) => {
    if (!mobile) return '';
    let phone = String(mobile).replace(/[^0-9]/g, '');
    if (phone.length === 10) phone = '91' + phone;
    return phone;
  };

  const buildPersonalizedMessage = (customerName) => {
    const name = (customerName || 'Valued Customer').trim() || 'Valued Customer';
    const salon = (businessName || '').trim() || 'Our Team';
    return messageText
      .replace(/\{customer_name\}/g, name)
      .replace(/\{salon_name\}/g, salon);
  };

  const startSendQueue = () => {
    setShowConfirmModal(false);
    const queue = customers
      .filter(c => selectedCustomers.has(c.id))
      .map(c => ({
        id: c.id,
        name: c.name,
        mobile: c.mobile,
        status: 'pending'
      }));
    if (queue.length === 0) {
      showError('No customers selected');
      return;
    }
    setSendQueue(queue);
    setQueueIndex(0);
    setShowQueueModal(true);
  };

  const sendCurrentToWhatsApp = () => {
    const current = sendQueue[queueIndex];
    if (!current) return;
    const phone = formatPhoneNumber(current.mobile);
    if (!phone) {
      showError(`Invalid mobile number for ${current.name}`);
      markCurrentAsSkipped();
      return;
    }
    const personalized = buildPersonalizedMessage(current.name);
    const url = `https://wa.me/${phone}?text=${encodeURIComponent(personalized)}`;
    const popup = window.open(url, '_blank');
    if (!popup) {
      showError('Popup blocked. Please allow popups for this site and try again.');
      return;
    }
    updateQueueStatus(queueIndex, 'sent');
    advanceQueue();
  };

  const markCurrentAsSkipped = () => {
    updateQueueStatus(queueIndex, 'skipped');
    advanceQueue();
  };

  const updateQueueStatus = (index, status) => {
    setSendQueue(prev => prev.map((item, i) => i === index ? { ...item, status } : item));
  };

  const advanceQueue = () => {
    setQueueIndex(prev => prev + 1);
  };

  const finishQueue = async () => {
    try {
      setSending(true);
      const sentIds = sendQueue.filter(q => q.status === 'sent').map(q => q.id);
      const skippedIds = sendQueue.filter(q => q.status === 'skipped').map(q => q.id);

      const response = await apiPost('/api/campaigns/send', {
        name: campaignName || 'Untitled Campaign',
        message_text: messageText,
        image_data: imageData,
        image_mime_type: imageMimeType,
        filter_type: filterType,
        customer_ids: Array.from(selectedCustomers),
        campaign_type: 'general',
        delivery_method: 'direct_whatsapp',
        sent_customer_ids: sentIds,
        skipped_customer_ids: skippedIds
      });

      if (response.ok) {
        const data = await response.json();
        showSuccess(`Campaign logged: ${data.sent_count} sent, ${data.failed_count} skipped`);

        // Reset form (restore the default template, not an empty box)
        setCampaignName('');
        setMessageText(buildGeneralTemplate());
        removeImage();
        setFilterType('all');
        setSelectedCustomers(new Set());
        setSendQueue([]);
        setQueueIndex(0);
        setShowQueueModal(false);

        if (onCampaignSent) onCampaignSent();
      } else {
        const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));
        showError(errorData.error || 'Failed to log campaign');
      }
    } catch (error) {
      console.error('Error logging campaign:', error);
      showError('Error logging campaign');
    } finally {
      setSending(false);
    }
  };

  const cancelQueue = () => {
    setShowQueueModal(false);
    setSendQueue([]);
    setQueueIndex(0);
  };

  const consentCustomers = customers.filter(c => c.whatsapp_consent);
  const selectedCount = selectedCustomers.size;

  return (
    <div className="campaign-container">
      {/* Compose Section */}
      <div className="campaign-section">
        <h2>Create Campaign</h2>
        
        <div className="campaign-form">
          <div className="form-group">
            <label>Campaign Name (Optional)</label>
            <input
              type="text"
              value={campaignName}
              onChange={(e) => setCampaignName(e.target.value)}
              placeholder="e.g., Women's Day Special"
            />
          </div>

          <div className="form-group">
            <label>Offer Image (Optional)</label>
            <div className="image-upload-area">
              {imagePreview ? (
                <div className="image-preview-container">
                  <img src={imagePreview} alt="Preview" className="image-preview" />
                  <button type="button" onClick={removeImage} className="remove-image-btn">
                    <FaTimes /> Remove
                  </button>
                </div>
              ) : (
                <label className="image-upload-label">
                  <FaImage size={24} />
                  <span>Click to upload image</span>
                  <input
                    type="file"
                    accept="image/*"
                    onChange={handleImageUpload}
                    style={{ display: 'none' }}
                  />
                </label>
              )}
            </div>
          </div>

          <div className="form-group">
            <label>Message *</label>
            <textarea
              value={messageText}
              onChange={(e) => setMessageText(e.target.value)}
              placeholder="Write your promotional message here..."
              rows={10}
              required
            />
            <small style={{ display: 'block', color: 'var(--gray-600)', marginTop: 4 }}>
              Tip: <code>{'{customer_name}'}</code> is replaced with each customer&apos;s name.
              <code style={{ marginLeft: 6 }}>{'{salon_name}'}</code> is replaced with your business name
              ({businessName ? <strong>{businessName}</strong> : '—'}).
            </small>
            <button
              type="button"
              onClick={() => setMessageText(buildGeneralTemplate())}
              style={{
                marginTop: 6,
                background: 'none',
                border: 'none',
                color: '#3b82f6',
                cursor: 'pointer',
                fontSize: 12,
                padding: 0,
              }}
            >
              Reset to default template
            </button>
          </div>
        </div>
      </div>

      {/* Target Customers Section */}
      <div className="campaign-section">
        <h2>Target Customers</h2>
        
        <div className="filter-section">
          <label>Filter Customers</label>
          <CompactSelect
            value={filterType}
            onChange={(v) => setFilterType(v)}
            className="filter-select"
            options={FILTER_TYPE_OPTIONS}
            placeholder="All Customers"
          />
        </div>

        <div className="customers-summary">
          <div className="summary-item">
            <FaUsers />
            <span>Total: {customers.length} customers</span>
          </div>
          <div className="summary-item">
            <FaCheck />
            <span>With WhatsApp Consent: {consentCustomers.length}</span>
          </div>
          <div className="summary-item selected">
            <FaPaperPlane />
            <span>Selected: {selectedCount}</span>
          </div>
        </div>

        {loadingCustomers ? (
          <div className="loading-state">Loading customers...</div>
        ) : (
          <div className="customers-list-container">
            <div className="customers-list-header">
              <button
                type="button"
                onClick={toggleSelectAll}
                className="select-all-btn"
              >
                {selectedCustomers.size === customers.length ? 'Deselect All' : 'Select All'}
              </button>
            </div>
            <div className="customers-list">
              {customers.map(customer => (
                <div
                  key={customer.id}
                  className={`customer-item ${selectedCustomers.has(customer.id) ? 'selected' : ''}`}
                  onClick={() => toggleCustomer(customer.id)}
                >
                  <input
                    type="checkbox"
                    checked={selectedCustomers.has(customer.id)}
                    onChange={() => toggleCustomer(customer.id)}
                  />
                  <div className="customer-info">
                    <div className="customer-name">{customer.name}</div>
                    <div className="customer-mobile">{customer.mobile}</div>
                    {!customer.whatsapp_consent && (
                      <span className="no-consent-badge">No WhatsApp Consent</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Send Section */}
      <div className="campaign-section send-section">
        <div className="send-summary">
          <h3>Ready to Send</h3>
          <p>{selectedCount} customers will receive this campaign</p>
        </div>
        <button
          onClick={handleSend}
          disabled={sending || selectedCount === 0 || !messageText.trim()}
          className="send-campaign-btn"
        >
          {sending ? 'Sending...' : 'Send Campaign'}
        </button>
      </div>

      {/* Confirmation Modal */}
      {showConfirmModal && (
        <div className="modal-overlay" onClick={() => setShowConfirmModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Confirm Send Campaign</h3>
              <button
                type="button"
                className="modal-close-btn"
                onClick={() => setShowConfirmModal(false)}
              >
                <FaTimes />
              </button>
            </div>
            <div className="modal-body">
              <p>Are you sure you want to send this campaign to <strong>{selectedCount} customers</strong>?</p>
              {imagePreview && (
                <div className="modal-preview">
                  <img src={imagePreview} alt="Campaign preview" />
                </div>
              )}
              <div className="modal-message-preview">
                <strong>Message:</strong>
                <p>{messageText}</p>
              </div>
            </div>
            <div className="modal-actions">
              <button
                type="button"
                className="btn-cancel"
                onClick={() => setShowConfirmModal(false)}
              >
                Cancel
              </button>
              <button
                type="button"
                className="btn-primary"
                onClick={startSendQueue}
              >
                Start Sending
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Send Queue Modal */}
      {showQueueModal && (
        <div className="modal-overlay" onClick={() => {}}>
          <div className="modal-content send-queue-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Send via WhatsApp ({queueIndex}/{sendQueue.length})</h3>
              <button type="button" className="modal-close-btn" onClick={cancelQueue}>
                <FaTimes />
              </button>
            </div>
            <div className="modal-body">
              {imagePreview && (
                <div className="queue-image-notice">
                  <img src={imagePreview} alt="Offer" className="queue-image-thumb" />
                  <small>After WhatsApp opens, attach this image manually before sending.</small>
                </div>
              )}

              {queueIndex < sendQueue.length ? (
                <>
                  <div className="queue-current">
                    <div className="queue-current-label">Next customer:</div>
                    <div className="queue-current-name">{sendQueue[queueIndex].name}</div>
                    <div className="queue-current-mobile">{sendQueue[queueIndex].mobile}</div>
                  </div>
                  <div className="queue-message-preview">
                    <strong>Message:</strong>
                    <p>{buildPersonalizedMessage(sendQueue[queueIndex].name)}</p>
                  </div>
                  <div className="queue-progress-list">
                    {sendQueue.map((q, i) => (
                      <div key={q.id} className={`queue-progress-item status-${q.status}${i === queueIndex ? ' current' : ''}`}>
                        <span className="queue-progress-name">{q.name}</span>
                        <span className="queue-progress-status">
                          {q.status === 'sent' ? 'Sent' : q.status === 'skipped' ? 'Skipped' : i === queueIndex ? 'Now' : 'Pending'}
                        </span>
                      </div>
                    ))}
                  </div>
                </>
              ) : (
                <div className="queue-done">
                  <FaCheck size={32} />
                  <p>Done. {sendQueue.filter(q => q.status === 'sent').length} opened in WhatsApp, {sendQueue.filter(q => q.status === 'skipped').length} skipped.</p>
                </div>
              )}
            </div>
            <div className="modal-actions">
              {queueIndex < sendQueue.length ? (
                <>
                  <button type="button" className="btn-cancel" onClick={markCurrentAsSkipped}>
                    Skip
                  </button>
                  <button type="button" className="btn-primary" onClick={sendCurrentToWhatsApp}>
                    Open WhatsApp
                  </button>
                </>
              ) : (
                <>
                  <button type="button" className="btn-cancel" onClick={cancelQueue} disabled={sending}>
                    Close
                  </button>
                  <button type="button" className="btn-primary" onClick={finishQueue} disabled={sending}>
                    {sending ? 'Logging...' : 'Save Campaign'}
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default GeneralCampaign;

