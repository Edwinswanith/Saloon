import React, { useState, useEffect } from 'react';
import { apiGet, apiPost } from '../utils/api';
import Header from './Header';
import { FaExclamationTriangle, FaCheckCircle, FaTimesCircle } from 'react-icons/fa';
import './CustomerLifecycleReport.css';

const CustomerLifecycleReport = () => {
  const [customers, setCustomers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedCustomers, setSelectedCustomers] = useState([]);
  const [segments, setSegments] = useState({});
  const [filters, setFilters] = useState({ segment: '', min_spent: '', min_visits: '' });
  const [showWhatsAppModal, setShowWhatsAppModal] = useState(false);
  const [templates, setTemplates] = useState([]);
  const [selectedTemplate, setSelectedTemplate] = useState('');
  const [messageText, setMessageText] = useState('');
  const [messages, setMessages] = useState([]);

  // PLACEHOLDER: WhatsApp Integration Status
  const WHATSAPP_ENABLED = false; // Set to true when WhatsApp API is configured
  const WHATSAPP_PLACEHOLDER_MESSAGE = 'WhatsApp integration is in placeholder mode. Will be activated when API credentials are provided.';

  // Refetch data when filters change
  useEffect(() => {
    fetchCustomers();
    fetchSegments();
    fetchTemplates();
    fetchMessages();
  }, [filters]);

  // Listen for branch changes and refetch data
  useEffect(() => {
    const handleBranchChange = (event) => {
      console.log('[Customer Lifecycle] Branch changed, refreshing data...', event.detail);
      
      // Immediately clear all data to prevent mixed data display
      setCustomers([]);
      setSegments({});
      setSelectedCustomers([]);
      
      // Set loading state to show data is refreshing
      setLoading(true);
      
      // Small delay to ensure localStorage is updated with new branch ID
      setTimeout(() => {
        // Verify branch ID is updated before fetching
        const storedBranch = localStorage.getItem('current_branch');
        if (storedBranch) {
          try {
            const branch = JSON.parse(storedBranch);
            console.log(`[Customer Lifecycle] Fetching data for branch: ${branch.name} (${branch.id})`);
          } catch (e) {
            console.error('[Customer Lifecycle] Error parsing branch from localStorage:', e);
          }
        }
        
        // Refetch all data for the new branch
        fetchCustomers();
        fetchSegments();
        fetchTemplates();
        fetchMessages();
      }, 150); // Slightly longer delay to ensure localStorage is fully updated
    };

    // Listen for branch change events
    window.addEventListener('branchChanged', handleBranchChange);

    // Cleanup listener on unmount
    return () => {
      window.removeEventListener('branchChanged', handleBranchChange);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Empty dependency array - we only want to set up the listener once

  const fetchCustomers = async () => {
    try {
      setLoading(true);
      
      // Debug: Check current branch before making request
      const storedBranch = localStorage.getItem('current_branch');
      if (storedBranch) {
        try {
          const branch = JSON.parse(storedBranch);
          console.log(`[Customer Lifecycle Frontend] Fetching customers for branch: ${branch.name} (ID: ${branch.id})`);
        } catch (e) {
          console.error('[Customer Lifecycle Frontend] Error parsing branch:', e);
        }
      } else {
        console.warn('[Customer Lifecycle Frontend] No current_branch in localStorage');
      }
      
      const params = new URLSearchParams();
      if (filters.segment) params.append('segment', filters.segment);
      if (filters.min_spent) params.append('min_spent', filters.min_spent);
      if (filters.min_visits) params.append('min_visits', filters.min_visits);

      const response = await apiGet(`/api/customer-lifecycle/report?${params}`);
      if (response.ok) {
        const data = await response.json();
        // Clear old data first to prevent mixed data display
        setCustomers([]);
        // Set new data - ensure it's an array
        setCustomers(Array.isArray(data.customers) ? data.customers : []);
        console.log(`[Customer Lifecycle Frontend] Loaded ${data.customers?.length || 0} customers`);
        if (data.customers && data.customers.length > 0) {
          console.log(`[Customer Lifecycle Frontend] Sample customers:`, data.customers.slice(0, 3).map(c => ({
            name: `${c.first_name} ${c.last_name}`,
            mobile: c.mobile,
            branch_id: c.branch_id
          })));
        }
      } else {
        console.error('Error fetching customers:', response.status, response.statusText);
        // Clear customers on error to prevent stale data
        setCustomers([]);
      }
    } catch (error) {
      console.error('Error fetching customers:', error);
      // Clear customers on error to prevent stale data
      setCustomers([]);
    } finally {
      setLoading(false);
    }
  };

  const fetchSegments = async () => {
    try {
      const response = await apiGet('/api/customer-lifecycle/segments');
      if (response.ok) {
        const data = await response.json();
        // Clear old segments first
        setSegments({});
        // Set new segments - ensure it's an object
        setSegments(data.segments && typeof data.segments === 'object' ? data.segments : {});
        console.log(`[Customer Lifecycle] Loaded segments for current branch:`, data.segments);
      } else {
        console.error('Error fetching segments:', response.status, response.statusText);
        // Reset segments on error
        setSegments({});
      }
    } catch (error) {
      console.error('Error fetching segments:', error);
      // Reset segments on error
      setSegments({});
    }
  };

  const fetchTemplates = async () => {
    try {
      const response = await apiGet('/api/customer-lifecycle/whatsapp-templates?status=active');
      if (response.ok) {
        const data = await response.json();
        setTemplates(data.templates || []);
      } else {
        console.error('Error fetching templates:', response.status, response.statusText);
      }
    } catch (error) {
      console.error('Error fetching templates:', error);
    }
  };

  const fetchMessages = async () => {
    try {
      const response = await apiGet('/api/customer-lifecycle/whatsapp-messages');
      if (response.ok) {
        const data = await response.json();
        setMessages(data.messages || []);
      } else {
        console.error('Error fetching messages:', response.status, response.statusText);
      }
    } catch (error) {
      console.error('Error fetching messages:', error);
    }
  };

  const handleCustomerSelect = (customerId) => {
    setSelectedCustomers(prev => 
      prev.includes(customerId) 
        ? prev.filter(id => id !== customerId)
        : [...prev, customerId]
    );
  };

  const handleSelectAll = () => {
    if (selectedCustomers.length === customers.length) {
      setSelectedCustomers([]);
    } else {
      setSelectedCustomers(customers.map(c => c.id));
    }
  };

  const handleSendWhatsApp = async () => {
    if (!WHATSAPP_ENABLED) {
      alert(WHATSAPP_PLACEHOLDER_MESSAGE);
      return;
    }

    if (selectedCustomers.length === 0) {
      alert('Please select at least one customer');
      return;
    }

    if (!messageText && !selectedTemplate) {
      alert('Please enter a message or select a template');
      return;
    }

    try {
      const response = await apiPost('/api/customer-lifecycle/send-whatsapp', {
        customer_ids: selectedCustomers,
        message_text: messageText,
        template_id: selectedTemplate || null
      });

      if (response.ok) {
        const data = await response.json();
        alert(`Message sent to ${data.sent} customers. ${data.failed} failed.`);
        setShowWhatsAppModal(false);
        setMessageText('');
        setSelectedTemplate('');
        setSelectedCustomers([]);
        fetchMessages();
      } else {
        const errorData = await response.json().catch(() => ({}));
        console.error('Error sending WhatsApp:', response.status, errorData);
        alert('Error sending messages. ' + WHATSAPP_PLACEHOLDER_MESSAGE);
      }
    } catch (error) {
      console.error('Error sending WhatsApp:', error);
      alert('Error sending messages. ' + WHATSAPP_PLACEHOLDER_MESSAGE);
    }
  };

  const getSegmentBadgeClass = (segment) => {
    const classes = {
      'new': 'badge-new',
      'regular': 'badge-regular',
      'loyal': 'badge-loyal',
      'inactive': 'badge-inactive',
      'high_spending': 'badge-high-spending'
    };
    return classes[segment] || 'badge-custom';
  };

  return (
    <div className="customer-lifecycle-page">
      <Header title="Customer Lifecycle Report" />
      <div className="page-content">
        {/* Segment Statistics */}
        <div className="segments-grid">
          <div className="segment-card">
            <h3>New Customers</h3>
            <p className="segment-value">{segments.new || 0}</p>
          </div>
          <div className="segment-card">
            <h3>Regular</h3>
            <p className="segment-value">{segments.regular || 0}</p>
          </div>
          <div className="segment-card">
            <h3>Loyal</h3>
            <p className="segment-value">{segments.loyal || 0}</p>
          </div>
          <div className="segment-card">
            <h3>Inactive</h3>
            <p className="segment-value">{segments.inactive || 0}</p>
          </div>
          <div className="segment-card">
            <h3>High Spending</h3>
            <p className="segment-value">{segments.high_spending || 0}</p>
          </div>
        </div>

        {/* WhatsApp Placeholder Notice */}
        {!WHATSAPP_ENABLED && (
          <div className="placeholder-notice">
            <p style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <FaExclamationTriangle size={16} color="#f59e0b" /> {WHATSAPP_PLACEHOLDER_MESSAGE}
            </p>
          </div>
        )}

        {/* Filters */}
        <div className="filters-section">
          <input
            type="number"
            value={filters.min_spent}
            onChange={(e) => setFilters({...filters, min_spent: e.target.value})}
            placeholder="Min Spent"
          />
          <input
            type="number"
            value={filters.min_visits}
            onChange={(e) => setFilters({...filters, min_visits: e.target.value})}
            placeholder="Min Visits"
          />
          <button 
            onClick={() => setShowWhatsAppModal(true)} 
            className="btn-primary"
            disabled={!WHATSAPP_ENABLED}
          >
            Send WhatsApp Message
          </button>
        </div>

        {/* Customers Table */}
        <div className="customers-table">
          <div className="table-header">
            <button onClick={handleSelectAll} className="btn-select-all">
              {selectedCustomers.length === customers.length ? 'Deselect All' : 'Select All'}
            </button>
            <span>{selectedCustomers.length} selected</span>
          </div>
          <table>
            <thead>
              <tr>
                <th></th>
                <th>Name</th>
                <th>Mobile</th>
                <th>Last Visit</th>
                <th>Total Visits</th>
                <th>Total Spent</th>
                <th>Segment</th>
                <th>WhatsApp Consent</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan="8">Loading...</td></tr>
              ) : customers.length === 0 ? (
                <tr><td colSpan="8">No customers found</td></tr>
              ) : (
                customers.map(customer => (
                  <tr key={customer.id}>
                    <td>
                      <input
                        type="checkbox"
                        checked={selectedCustomers.includes(customer.id)}
                        onChange={() => handleCustomerSelect(customer.id)}
                      />
                    </td>
                    <td>{customer.first_name} {customer.last_name}</td>
                    <td>{customer.mobile}</td>
                    <td>{customer.last_visit_date || '-'}</td>
                    <td>{customer.total_visits || 0}</td>
                    <td>₹{customer.total_spent?.toFixed(2) || '0.00'}</td>
                    <td>
                      <span className={`segment-badge ${getSegmentBadgeClass(customer.segment)}`}>
                        {customer.segment}
                      </span>
                    </td>
                    <td style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      {customer.whatsapp_consent ? (
                        <>
                          <FaCheckCircle size={14} color="#10b981" /> Yes
                        </>
                      ) : (
                        <>
                          <FaTimesCircle size={14} color="#ef4444" /> No
                        </>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* WhatsApp Modal */}
        {showWhatsAppModal && (
          <div className="modal-overlay" onClick={() => setShowWhatsAppModal(false)}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
              <h2>Send WhatsApp Message</h2>
              {!WHATSAPP_ENABLED && (
                <div className="placeholder-notice">
                  <p style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <FaExclamationTriangle size={16} color="#f59e0b" /> {WHATSAPP_PLACEHOLDER_MESSAGE}
                  </p>
                </div>
              )}
              <div className="form-group">
                <label>Select Template (Optional)</label>
                <select
                  value={selectedTemplate}
                  onChange={(e) => {
                    setSelectedTemplate(e.target.value);
                    const template = templates.find(t => t.id === e.target.value);
                    if (template) setMessageText(template.message_text);
                  }}
                >
                  <option value="">Custom Message</option>
                  {templates.map(template => (
                    <option key={template.id} value={template.id}>{template.name}</option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label>Message Text *</label>
                <textarea
                  value={messageText}
                  onChange={(e) => setMessageText(e.target.value)}
                  rows="5"
                  required
                  disabled={!WHATSAPP_ENABLED}
                />
              </div>
              <div className="modal-actions">
                <button type="button" onClick={() => setShowWhatsAppModal(false)}>Cancel</button>
                <button onClick={handleSendWhatsApp} className="btn-primary" disabled={!WHATSAPP_ENABLED}>
                  Send to {selectedCustomers.length} Customer(s)
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default CustomerLifecycleReport;

