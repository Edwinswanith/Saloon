import React, { useState, useEffect } from 'react';
import { FaImage, FaTimes, FaCheck, FaUsers, FaPaperPlane, FaBirthdayCake } from 'react-icons/fa';
import { apiGet, apiPost } from '../utils/api';
import { showSuccess, showError } from '../utils/toast.jsx';
import { useAuth } from '../contexts/AuthContext';

const BIRTHDAY_TEMPLATE = `Happy Birthday, {customer_name}! 🎂

Wishing you a wonderful day filled with joy and beautiful moments!

As a special birthday gift from us, enjoy an EXCLUSIVE BIRTHDAY OFFER on any service this month. You deserve to be pampered!

Book your birthday treat:
📞 Call us or walk in anytime

We look forward to making your day even more special.

With warm wishes,
[Salon Name] Team 💆‍♀️`;

const BirthdayCampaign = ({ onCampaignSent }) => {
  const { currentBranch } = useAuth();
  const [selectedMonth, setSelectedMonth] = useState(new Date().getMonth() + 1); // 1-12
  const [messageText, setMessageText] = useState(BIRTHDAY_TEMPLATE);
  const [imageFile, setImageFile] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [imageData, setImageData] = useState(null);
  const [imageMimeType, setImageMimeType] = useState(null);
  const [customers, setCustomers] = useState([]);
  const [selectedCustomers, setSelectedCustomers] = useState(new Set());
  const [loadingCustomers, setLoadingCustomers] = useState(false);
  const [sending, setSending] = useState(false);
  const [showConfirmModal, setShowConfirmModal] = useState(false);

  useEffect(() => {
    if (selectedMonth && currentBranch) {
      fetchBirthdayCustomers();
    }
  }, [selectedMonth, currentBranch]);

  const fetchBirthdayCustomers = async () => {
    try {
      setLoadingCustomers(true);
      const response = await apiGet(`/api/campaigns/birthday-customers?month=${selectedMonth}`);
      if (!response.ok) throw new Error('Failed to fetch birthday customers');
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
      console.error('Error fetching birthday customers:', error);
      showError('Failed to load birthday customers');
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
      const base64String = reader.result.split(',')[1];
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
        name: `Birthday Campaign - ${getMonthName(selectedMonth)}`,
        message_text: messageText,
        image_data: imageData,
        image_mime_type: imageMimeType,
        filter_type: 'birthday',
        customer_ids: Array.from(selectedCustomers),
        campaign_type: 'birthday'
      });

      if (response.ok) {
        const data = await response.json();
        showSuccess(`Birthday campaign sent to ${data.sent_count} customers`);
        
        // Reset form (keep month and template)
        removeImage();
        setSelectedCustomers(new Set());
        
        // Notify parent to refresh campaigns
        if (onCampaignSent) {
          onCampaignSent();
        }
      } else {
        const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));
        showError(errorData.error || 'Failed to send birthday campaign');
      }
    } catch (error) {
      console.error('Error sending birthday campaign:', error);
      showError('Error sending birthday campaign');
    } finally {
      setSending(false);
    }
  };

  const getMonthName = (month) => {
    const months = [
      'January', 'February', 'March', 'April', 'May', 'June',
      'July', 'August', 'September', 'October', 'November', 'December'
    ];
    return months[month - 1];
  };

  const formatDate = (dateString) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  const consentCustomers = customers.filter(c => c.whatsapp_consent);
  const selectedCount = Array.from(selectedCustomers).filter(id => 
    customers.find(c => c.id === id && c.whatsapp_consent)
  ).length;

  return (
    <div className="campaign-container">
      {/* Month Selector Section */}
      <div className="campaign-section">
        <h2>
          <FaBirthdayCake style={{ marginRight: '8px' }} />
          Birthday Month Selection
        </h2>
        
        <div className="form-group">
          <label>Select Month</label>
          <select
            value={selectedMonth}
            onChange={(e) => setSelectedMonth(parseInt(e.target.value))}
            className="filter-select"
          >
            {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12].map(month => (
              <option key={month} value={month}>
                {getMonthName(month)}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Compose Section */}
      <div className="campaign-section">
        <h2>Create Birthday Campaign</h2>
        
        <div className="campaign-form">
          <div className="form-group">
            <label>Birthday Image (Optional)</label>
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
            <label>Birthday Message *</label>
            <textarea
              value={messageText}
              onChange={(e) => setMessageText(e.target.value)}
              placeholder="Birthday message template (use {customer_name} placeholder)"
              rows={10}
              required
            />
            <small style={{ color: 'var(--gray-600)', marginTop: '4px', display: 'block' }}>
              Tip: The {`{customer_name}`} placeholder will be replaced with each customer's name automatically.
            </small>
          </div>
        </div>
      </div>

      {/* Birthday Customers Section */}
      <div className="campaign-section">
        <h2>Birthday Customers - {getMonthName(selectedMonth)}</h2>
        
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
          <div className="loading-state">Loading birthday customers...</div>
        ) : customers.length === 0 ? (
          <div className="empty-state">No customers have birthdays in {getMonthName(selectedMonth)}</div>
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
                    {customer.dob && (
                      <div className="customer-dob" style={{ fontSize: '12px', color: 'var(--gray-600)', marginTop: '2px' }}>
                        Birthday: {formatDate(customer.dob)}
                      </div>
                    )}
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
          <p>{selectedCount} customers will receive this birthday campaign</p>
        </div>
        <button
          onClick={handleSend}
          disabled={sending || selectedCount === 0 || !messageText.trim()}
          className="send-campaign-btn"
        >
          {sending ? 'Sending...' : 'Send Birthday Campaign'}
        </button>
      </div>

      {/* Confirmation Modal */}
      {showConfirmModal && (
        <div className="modal-overlay" onClick={() => setShowConfirmModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Confirm Send Birthday Campaign</h3>
              <button
                type="button"
                className="modal-close-btn"
                onClick={() => setShowConfirmModal(false)}
              >
                <FaTimes />
              </button>
            </div>
            <div className="modal-body">
              <p>Are you sure you want to send this birthday campaign to <strong>{selectedCount} customers</strong>?</p>
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
                Send Birthday Campaign
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default BirthdayCampaign;

