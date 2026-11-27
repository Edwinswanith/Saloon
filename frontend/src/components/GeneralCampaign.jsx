import React, { useEffect, useState } from 'react';
import { FaCheck, FaImage, FaPaperPlane, FaTimes, FaUsers } from 'react-icons/fa';
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

const FILTER_TYPE_OPTIONS = [
  { value: 'all', label: 'All Customers' },
  { value: 'top10_revenue', label: 'Top 10 by Revenue' },
  { value: 'top10_visits', label: 'Top 10 by Visits' },
  { value: 'gender_female', label: 'Female Customers' },
  { value: 'gender_male', label: 'Male Customers' },
  { value: 'inactive', label: 'Inactive (60+ days)' },
];

const buildGeneralNotes = () =>
  '[Enter the offer details, validity period, and internal campaign notes]';

const GeneralCampaign = ({ onCampaignSent }) => {
  const { currentBranch } = useAuth();
  const [campaignName, setCampaignName] = useState('');
  const [messageText, setMessageText] = useState(buildGeneralNotes);
  const [imageFile, setImageFile] = useState(null);
  const [imagePreview, setImagePreview] = useState('');
  const [filterType, setFilterType] = useState('all');
  const [customers, setCustomers] = useState([]);
  const [selectedCustomers, setSelectedCustomers] = useState(new Set());
  const [loadingCustomers, setLoadingCustomers] = useState(false);
  const [sending, setSending] = useState(false);
  const [showConfirmModal, setShowConfirmModal] = useState(false);

  useEffect(() => {
    if (!filterType || !currentBranch) return;

    const fetchCustomers = async () => {
      try {
        setLoadingCustomers(true);
        const response = await apiGet(`/api/campaigns/customers?filter=${filterType}`);
        const data = await response.json().catch(() => ({}));
        if (!response.ok) throw new Error(data.error || 'Failed to fetch customers');
        const nextCustomers = data.customers || [];
        setCustomers(nextCustomers);
        setSelectedCustomers(new Set(
          nextCustomers.filter(customer => customer.whatsapp_consent === true).map(customer => customer.id)
        ));
      } catch (error) {
        console.error('Error fetching customers:', error);
        showError(error.message || 'Failed to load customers');
      } finally {
        setLoadingCustomers(false);
      }
    };

    fetchCustomers();
  }, [filterType, currentBranch]);

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
      showError('Enter campaign notes or offer details.');
      return;
    }
    if (/\[[^\]]+\]/.test(messageText)) {
      showError('Replace the bracketed instruction with the actual offer details.');
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
        name: campaignName.trim() || 'Untitled Campaign',
        messageText: messageText.trim(),
        filterType,
        customerIds: Array.from(selectedCustomers),
        campaignType: 'general',
        mediaAssetId,
      });
      setShowConfirmModal(false);
      showSuccess(
        `Campaign started for ${data.eligible_count || 0} customers; ${data.excluded_count || 0} excluded.`
      );
      setCampaignName('');
      setMessageText(buildGeneralNotes());
      removeImage();
      setSelectedCustomers(new Set());
      if (onCampaignSent) onCampaignSent(data);
    } catch (error) {
      console.error('Error starting campaign:', error);
      showError(error.message || 'Campaign could not be started.');
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="campaign-container">
      <div className="campaign-section">
        <h2>Create Campaign</h2>
        <div className="campaign-form">
          <div className="form-group">
            <label>Campaign Name (Optional)</label>
            <input
              type="text"
              value={campaignName}
              onChange={event => setCampaignName(event.target.value)}
              placeholder="e.g., Women's Day Special"
            />
          </div>

          <div className="form-group">
            <label>Promotional Image *</label>
            <div className="image-upload-area">
              {imagePreview ? (
                <div className="image-preview-container">
                  <img src={imagePreview} alt="Campaign preview" className="image-preview" />
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
            <label>Offer Details / Internal Notes *</label>
            <textarea
              value={messageText}
              onChange={event => setMessageText(event.target.value)}
              rows={6}
              required
            />
            <small className="campaign-help-text">
              WhatsApp sends the approved priyanka_promotional_offer template in en_US.
            </small>
          </div>
        </div>
      </div>

      <div className="campaign-section">
        <h2>Target Customers</h2>
        <div className="filter-section">
          <label>Filter Customers</label>
          <CompactSelect
            value={filterType}
            onChange={setFilterType}
            className="filter-select"
            options={FILTER_TYPE_OPTIONS}
            placeholder="All Customers"
          />
        </div>

        <div className="customers-summary">
          <div className="summary-item"><FaUsers /><span>Available: {customers.length}</span></div>
          <div className="summary-item"><FaCheck /><span>Selected: {selection.selected}</span></div>
          <div className="summary-item"><FaCheck /><span>Consented: {selection.consented}</span></div>
          <div className="summary-item selected"><FaPaperPlane /><span>Eligible: {selection.eligible}</span></div>
          <div className="summary-item"><span>No consent: {selection.excludedNoConsent}</span></div>
          <div className="summary-item"><span>Invalid phone: {selection.excludedInvalidPhone}</span></div>
        </div>

        {loadingCustomers ? (
          <div className="loading-state">Loading customers...</div>
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
          {sending ? 'Queueing...' : 'Send Campaign'}
        </button>
      </div>

      {showConfirmModal && (
        <div className="modal-overlay" onClick={() => !sending && setShowConfirmModal(false)}>
          <div className="modal-content" onClick={event => event.stopPropagation()}>
            <div className="modal-header">
              <h3>Confirm Campaign Queue</h3>
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
                <img src={imagePreview} alt="Campaign preview" />
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

export default GeneralCampaign;
