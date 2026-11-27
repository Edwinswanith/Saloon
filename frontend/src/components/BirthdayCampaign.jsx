import React, { useEffect, useState } from 'react';
import { FaBirthdayCake, FaCheck, FaImage, FaPaperPlane, FaTimes, FaUsers } from 'react-icons/fa';
import { apiGet } from '../utils/api';
import {
  MAX_CAMPAIGN_IMAGE_BYTES,
  analyzeCampaignSelection,
  createQueuedCampaign,
  normalizeCampaignPhone,
  uploadCampaignImage,
} from '../utils/campaignQueue';
import { showError, showSuccess } from '../utils/toast.jsx';
import { useAuth } from '../contexts/AuthContext';
import CompactSelect from './shared/CompactSelect';

const MONTHS = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December',
];

const BirthdayCampaign = ({ onCampaignSent }) => {
  const { currentBranch } = useAuth();
  const [selectedMonth, setSelectedMonth] = useState(new Date().getMonth() + 1);
  const [messageText, setMessageText] = useState('Birthday promotional offer campaign');
  const [imageFile, setImageFile] = useState(null);
  const [imagePreview, setImagePreview] = useState('');
  const [customers, setCustomers] = useState([]);
  const [selectedCustomers, setSelectedCustomers] = useState(new Set());
  const [loadingCustomers, setLoadingCustomers] = useState(false);
  const [sending, setSending] = useState(false);
  const [showConfirmModal, setShowConfirmModal] = useState(false);

  const monthName = MONTHS[selectedMonth - 1];

  useEffect(() => {
    if (!selectedMonth || !currentBranch) return;

    const fetchBirthdayCustomers = async () => {
      try {
        setLoadingCustomers(true);
        const response = await apiGet(`/api/campaigns/birthday-customers?month=${selectedMonth}`);
        const data = await response.json().catch(() => ({}));
        if (!response.ok) throw new Error(data.error || 'Failed to fetch birthday customers');
        const nextCustomers = data.customers || [];
        setCustomers(nextCustomers);
        setSelectedCustomers(new Set(
          nextCustomers.filter(customer => customer.whatsapp_consent === true).map(customer => customer.id)
        ));
      } catch (error) {
        console.error('Error fetching birthday customers:', error);
        showError(error.message || 'Failed to load birthday customers');
      } finally {
        setLoadingCustomers(false);
      }
    };

    fetchBirthdayCustomers();
  }, [selectedMonth, currentBranch]);

  const handleImageUpload = (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    if (!['image/jpeg', 'image/png'].includes(file.type)) {
      showError('Select a JPEG or PNG image.');
      event.target.value = '';
      return;
    }
    if (file.size > MAX_CAMPAIGN_IMAGE_BYTES) {
      showError('Image must be 3 MiB or smaller.');
      event.target.value = '';
      return;
    }
    setImageFile(file);
    const reader = new FileReader();
    reader.onload = () => setImagePreview(String(reader.result || ''));
    reader.readAsDataURL(file);
  };

  const removeImage = () => {
    setImageFile(null);
    setImagePreview('');
  };

  const toggleCustomer = (customerId) => {
    setSelectedCustomers(current => {
      const next = new Set(current);
      if (next.has(customerId)) next.delete(customerId);
      else next.add(customerId);
      return next;
    });
  };

  const consentedCustomerIds = customers
    .filter(customer => customer.whatsapp_consent === true)
    .map(customer => customer.id);
  const allConsentedSelected = consentedCustomerIds.length > 0
    && consentedCustomerIds.every(customerId => selectedCustomers.has(customerId));
  const selection = analyzeCampaignSelection(customers, selectedCustomers);

  const toggleSelectAll = () => {
    setSelectedCustomers(allConsentedSelected ? new Set() : new Set(consentedCustomerIds));
  };

  const handleSend = () => {
    if (!messageText.trim()) {
      showError('Enter campaign notes.');
      return;
    }
    if (!imageFile) {
      showError('Upload the promotional image required by the approved template.');
      return;
    }
    if (!selection.selected) {
      showError('Select at least one customer.');
      return;
    }
    if (!selection.eligible) {
      showError('None of the selected customers are eligible for WhatsApp delivery.');
      return;
    }
    setShowConfirmModal(true);
  };

  const submitQueuedCampaign = async () => {
    try {
      setSending(true);
      const mediaAssetId = await uploadCampaignImage(imageFile);
      const data = await createQueuedCampaign({
        name: `Birthday Campaign - ${monthName}`,
        messageText: messageText.trim(),
        filterType: 'birthday',
        customerIds: Array.from(selectedCustomers),
        campaignType: 'birthday',
        mediaAssetId,
      });
      setShowConfirmModal(false);
      showSuccess(
        `Birthday campaign queued for ${data.eligible_count || 0} customers; ${data.excluded_count || 0} excluded.`
      );
      removeImage();
      setSelectedCustomers(new Set());
      if (onCampaignSent) onCampaignSent(data);
    } catch (error) {
      console.error('Error queueing birthday campaign:', error);
      showError(error.message || 'Birthday campaign could not be queued.');
    } finally {
      setSending(false);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return '';
    return new Date(dateString).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  return (
    <div className="campaign-container">
      <div className="campaign-section">
        <h2><FaBirthdayCake className="campaign-heading-icon" />Birthday Month Selection</h2>
        <div className="form-group">
          <label>Select Month</label>
          <CompactSelect
            value={selectedMonth}
            onChange={value => setSelectedMonth(Number(value))}
            className="filter-select"
            options={MONTHS.map((label, index) => ({ value: index + 1, label }))}
            placeholder="Select Month"
          />
        </div>
      </div>

      <div className="campaign-section">
        <h2>Create Birthday Campaign</h2>
        <div className="campaign-form">
          <div className="form-group">
            <label>Promotional Image *</label>
            <div className="image-upload-area">
              {imagePreview ? (
                <div className="image-preview-container">
                  <img src={imagePreview} alt="Birthday campaign preview" className="image-preview" />
                  <button type="button" onClick={removeImage} className="remove-image-btn">
                    <FaTimes /> Remove
                  </button>
                </div>
              ) : (
                <label className="image-upload-label">
                  <FaImage size={24} />
                  <span>Upload JPEG or PNG, up to 3 MiB</span>
                  <input
                    type="file"
                    accept="image/jpeg,image/png"
                    onChange={handleImageUpload}
                    style={{ display: 'none' }}
                  />
                </label>
              )}
            </div>
          </div>

          <div className="form-group">
            <label>Campaign Notes *</label>
            <textarea
              value={messageText}
              onChange={event => setMessageText(event.target.value)}
              rows={5}
              required
            />
            <small className="campaign-help-text">
              WhatsApp sends the approved priyanka_promotional_offer template in en_US.
            </small>
          </div>
        </div>
      </div>

      <div className="campaign-section">
        <h2>Birthday Customers - {monthName}</h2>
        <div className="customers-summary">
          <div className="summary-item"><FaUsers /><span>Available: {customers.length}</span></div>
          <div className="summary-item"><FaCheck /><span>Selected: {selection.selected}</span></div>
          <div className="summary-item"><FaCheck /><span>Consented: {selection.consented}</span></div>
          <div className="summary-item selected"><FaPaperPlane /><span>Eligible: {selection.eligible}</span></div>
          <div className="summary-item"><span>No consent: {selection.excludedNoConsent}</span></div>
          <div className="summary-item"><span>Invalid phone: {selection.excludedInvalidPhone}</span></div>
        </div>

        {loadingCustomers ? (
          <div className="loading-state">Loading birthday customers...</div>
        ) : customers.length === 0 ? (
          <div className="empty-state">No customer birthdays in {monthName}</div>
        ) : (
          <div className="customers-list-container">
            <div className="customers-list-header">
              <button type="button" onClick={toggleSelectAll} className="select-all-btn">
                {allConsentedSelected ? 'Deselect All' : 'Select All Consented'}
              </button>
            </div>
            <div className="customers-list">
              {customers.map(customer => {
                const phoneValid = Boolean(normalizeCampaignPhone(customer.mobile));
                return (
                  <div
                    key={customer.id}
                    className={`customer-item ${selectedCustomers.has(customer.id) ? 'selected' : ''}`}
                    onClick={() => toggleCustomer(customer.id)}
                  >
                    <input
                      type="checkbox"
                      checked={selectedCustomers.has(customer.id)}
                      onClick={event => event.stopPropagation()}
                      onChange={() => toggleCustomer(customer.id)}
                    />
                    <div className="customer-info">
                      <div className="customer-name">{customer.name}</div>
                      <div className="customer-mobile">{customer.mobile}</div>
                      {customer.dob && <div className="customer-dob">Birthday: {formatDate(customer.dob)}</div>}
                      {!customer.whatsapp_consent && (
                        <span className="no-consent-badge">Excluded: No WhatsApp Consent</span>
                      )}
                      {customer.whatsapp_consent && !phoneValid && (
                        <span className="invalid-phone-badge">Excluded: Invalid Phone</span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>

      <div className="campaign-section send-section">
        <div className="send-summary">
          <h3>Ready to Queue</h3>
          <p>
            {selection.eligible} eligible of {selection.selected} selected. {selection.excluded} will be excluded.
          </p>
        </div>
        <button
          type="button"
          onClick={handleSend}
          disabled={sending || !selection.eligible || !messageText.trim() || !imageFile}
          className="send-campaign-btn"
        >
          {sending ? 'Queueing...' : 'Send Birthday Campaign'}
        </button>
      </div>

      {showConfirmModal && (
        <div className="modal-overlay" onClick={() => !sending && setShowConfirmModal(false)}>
          <div className="modal-content" onClick={event => event.stopPropagation()}>
            <div className="modal-header">
              <h3>Confirm Birthday Campaign Queue</h3>
              <button
                type="button"
                className="modal-close-btn"
                onClick={() => setShowConfirmModal(false)}
                disabled={sending}
              >
                <FaTimes />
              </button>
            </div>
            <div className="modal-body">
              <p>This creates one queued campaign. Delivery continues in controlled server batches.</p>
              <div className="campaign-confirmation-grid">
                <span>Selected<strong>{selection.selected}</strong></span>
                <span>Consented<strong>{selection.consented}</strong></span>
                <span>Eligible<strong>{selection.eligible}</strong></span>
                <span>No consent<strong>{selection.excludedNoConsent}</strong></span>
                <span>Invalid phone<strong>{selection.excludedInvalidPhone}</strong></span>
              </div>
              <div className="modal-preview">
                <img src={imagePreview} alt="Birthday campaign preview" />
              </div>
            </div>
            <div className="modal-actions">
              <button
                type="button"
                className="btn-cancel"
                onClick={() => setShowConfirmModal(false)}
                disabled={sending}
              >
                Cancel
              </button>
              <button type="button" className="btn-primary" onClick={submitQueuedCampaign} disabled={sending}>
                {sending ? 'Queueing...' : `Queue for ${selection.eligible} Customers`}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default BirthdayCampaign;
