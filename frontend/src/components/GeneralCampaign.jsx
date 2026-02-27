import React, { useState, useEffect } from 'react';
import { FaImage, FaTimes, FaCheck, FaUsers, FaPaperPlane } from 'react-icons/fa';
import { apiGet, apiPost } from '../utils/api';
import { showSuccess, showError } from '../utils/toast.jsx';
import { useAuth } from '../contexts/AuthContext';

const GeneralCampaign = ({ onCampaignSent }) => {
  const { currentBranch } = useAuth();
  const [campaignName, setCampaignName] = useState('');
  const [messageText, setMessageText] = useState('');
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
      // Auto-select all customers with WhatsApp consent
      const consentCustomers = new Set(
        data.customers
          .filter(c => c.whatsapp_consent)
          .map(c => c.id)
      );
      setSelectedCustomers(consentCustomers);
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
    const consentCustomers = customers.filter(c => c.whatsapp_consent);
    if (selectedCustomers.size === consentCustomers.length) {
      setSelectedCustomers(new Set());
    } else {
      setSelectedCustomers(new Set(consentCustomers.map(c => c.id)));
    }
  };

  const handleSend = async () => {
    if (!messageText.trim()) {
      showError('Please enter a message');
      return;
    }

    if (selectedCustomers.size === 0) {
      showError('Please select at least one customer');
      return;
    }

    setShowConfirmModal(true);
  };

  const confirmSend = async () => {
    try {
      setSending(true);
      setShowConfirmModal(false);

      const response = await apiPost('/api/campaigns/send', {
        name: campaignName || 'Untitled Campaign',
        message_text: messageText,
        image_data: imageData,
        image_mime_type: imageMimeType,
        filter_type: filterType,
        customer_ids: Array.from(selectedCustomers),
        campaign_type: 'general'
      });

      if (response.ok) {
        const data = await response.json();
        showSuccess(`Campaign sent to ${data.sent_count} customers`);
        
        // Reset form
        setCampaignName('');
        setMessageText('');
        removeImage();
        setFilterType('all');
        setSelectedCustomers(new Set());
        
        // Notify parent to refresh campaigns
        if (onCampaignSent) {
          onCampaignSent();
        }
      } else {
        const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));
        showError(errorData.error || 'Failed to send campaign');
      }
    } catch (error) {
      console.error('Error sending campaign:', error);
      showError('Error sending campaign');
    } finally {
      setSending(false);
    }
  };

  const consentCustomers = customers.filter(c => c.whatsapp_consent);
  const selectedCount = Array.from(selectedCustomers).filter(id => 
    customers.find(c => c.id === id && c.whatsapp_consent)
  ).length;

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
              rows={6}
              required
            />
          </div>
        </div>
      </div>

      {/* Target Customers Section */}
      <div className="campaign-section">
        <h2>Target Customers</h2>
        
        <div className="filter-section">
          <label>Filter Customers</label>
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="filter-select"
          >
            <option value="all">All Customers</option>
            <option value="top10_revenue">Top 10 by Revenue</option>
            <option value="top10_visits">Top 10 by Visits</option>
            <option value="gender_female">Female Customers</option>
            <option value="gender_male">Male Customers</option>
            <option value="inactive">Inactive (60+ days)</option>
          </select>
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
                {selectedCustomers.size === consentCustomers.length ? 'Deselect All' : 'Select All'}
              </button>
            </div>
            <div className="customers-list">
              {customers.map(customer => (
                <div
                  key={customer.id}
                  className={`customer-item ${!customer.whatsapp_consent ? 'no-consent' : ''} ${selectedCustomers.has(customer.id) ? 'selected' : ''}`}
                  onClick={() => customer.whatsapp_consent && toggleCustomer(customer.id)}
                >
                  <input
                    type="checkbox"
                    checked={selectedCustomers.has(customer.id)}
                    onChange={() => customer.whatsapp_consent && toggleCustomer(customer.id)}
                    disabled={!customer.whatsapp_consent}
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
                onClick={confirmSend}
              >
                Send Campaign
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default GeneralCampaign;

