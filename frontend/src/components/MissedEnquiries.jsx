import React, { useState, useEffect } from 'react';
import { apiGet, apiPost, apiPut } from '../utils/api';
import Header from './Header';
import './MissedEnquiries.css';
import { useAuth } from '../contexts/AuthContext';

const MissedEnquiries = () => {
  const { currentBranch } = useAuth()
  const [enquiries, setEnquiries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingEnquiry, setEditingEnquiry] = useState(null);
  const [stats, setStats] = useState({ total: 0, open: 0, converted: 0, lost: 0, conversion_rate: 0 });
  const [reminders, setReminders] = useState([]);
  const [filters, setFilters] = useState({
    status: '',
    enquiry_type: '',
    start_date: '',
    end_date: ''
  });

  const [formData, setFormData] = useState({
    customer_name: '',
    customer_phone: '',
    enquiry_type: 'walk-in',
    requested_service: '',
    reason_not_delivered: '',
    follow_up_date: '',
    status: 'open',
    notes: ''
  });

  useEffect(() => {
    fetchEnquiries();
    fetchStats();
    fetchReminders();
  }, [filters, currentBranch]);

  // Listen for branch changes
  useEffect(() => {
    const handleBranchChange = () => {
      console.log('[MissedEnquiries] Branch changed, refreshing data...')
      fetchEnquiries()
      fetchStats()
      fetchReminders()
    }
    
    window.addEventListener('branchChanged', handleBranchChange)
    return () => window.removeEventListener('branchChanged', handleBranchChange)
  }, [currentBranch])

  const fetchEnquiries = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (filters.status) params.append('status', filters.status);
      if (filters.enquiry_type) params.append('enquiry_type', filters.enquiry_type);
      if (filters.start_date) params.append('start_date', filters.start_date);
      if (filters.end_date) params.append('end_date', filters.end_date);

      const response = await apiGet(`/api/missed-enquiries?${params}`);
      if (response.ok) {
        const data = await response.json();
        setEnquiries(data.enquiries || []);
      } else {
        console.error('Error fetching enquiries:', response.status, response.statusText);
      }
    } catch (error) {
      console.error('Error fetching enquiries:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await apiGet('/api/missed-enquiries/stats');
      if (response.ok) {
        const data = await response.json();
        setStats(data.stats || stats);
      } else {
        console.error('Error fetching stats:', response.status, response.statusText);
      }
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  const fetchReminders = async () => {
    try {
      const response = await apiGet('/api/missed-enquiries/reminders');
      if (response.ok) {
        const data = await response.json();
        setReminders(data.enquiries || []);
      } else {
        console.error('Error fetching reminders:', response.status, response.statusText);
      }
    } catch (error) {
      console.error('Error fetching reminders:', error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      let response;
      if (editingEnquiry) {
        response = await apiPut(`/api/missed-enquiries/${editingEnquiry.id}`, formData);
      } else {
        response = await apiPost('/api/missed-enquiries', formData);
      }
      
      if (response.ok) {
        setShowModal(false);
        setEditingEnquiry(null);
        resetForm();
        fetchEnquiries();
        fetchStats();
      } else {
        const errorData = await response.json().catch(() => ({}));
        console.error('Error saving enquiry:', response.status, errorData);
        alert('Failed to save enquiry. Please try again.');
      }
    } catch (error) {
      console.error('Error saving enquiry:', error);
      alert('Failed to save enquiry. Please try again.');
    }
  };

  const handleConvert = async (enquiryId) => {
    // Placeholder - would open appointment booking modal
    alert('Convert to Appointment feature - to be integrated with Appointment booking');
  };

  const resetForm = () => {
    setFormData({
      customer_name: '',
      customer_phone: '',
      enquiry_type: 'walk-in',
      requested_service: '',
      reason_not_delivered: '',
      follow_up_date: '',
      status: 'open',
      notes: ''
    });
  };

  const openEditModal = (enquiry) => {
    setEditingEnquiry(enquiry);
    setFormData({
      customer_name: enquiry.customer_name || '',
      customer_phone: enquiry.customer_phone || '',
      enquiry_type: enquiry.enquiry_type || 'walk-in',
      requested_service: enquiry.requested_service || '',
      reason_not_delivered: enquiry.reason_not_delivered || '',
      follow_up_date: enquiry.follow_up_date || '',
      status: enquiry.status || 'open',
      notes: enquiry.notes || ''
    });
    setShowModal(true);
  };

  return (
    <div className="missed-enquiries-page">
      <Header title="Missed Enquiries" />
      <div className="page-content">
        {/* Statistics Cards */}
        <div className="stats-grid">
          <div className="stat-card">
            <h3>Total</h3>
            <p className="stat-value">{stats.total}</p>
          </div>
          <div className="stat-card">
            <h3>Open</h3>
            <p className="stat-value">{stats.open}</p>
          </div>
          <div className="stat-card">
            <h3>Converted</h3>
            <p className="stat-value">{stats.converted}</p>
          </div>
          <div className="stat-card">
            <h3>Lost</h3>
            <p className="stat-value">{stats.lost}</p>
          </div>
          <div className="stat-card">
            <h3>Conversion Rate</h3>
            <p className="stat-value">{stats.conversion_rate}%</p>
          </div>
        </div>

        {/* Follow-up Reminders */}
        {reminders.length > 0 && (
          <div className="reminders-section">
            <h2>Follow-up Reminders</h2>
            <div className="reminders-list">
              {reminders.map(reminder => (
                <div key={reminder.id} className="reminder-item">
                  <span>{reminder.customer_name} - {reminder.customer_phone}</span>
                  <span>Follow-up: {reminder.follow_up_date}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Filters */}
        <div className="filters-section">
          <select value={filters.status} onChange={(e) => setFilters({...filters, status: e.target.value})}>
            <option value="">All Status</option>
            <option value="open">Open</option>
            <option value="converted">Converted</option>
            <option value="lost">Lost</option>
          </select>
          <select value={filters.enquiry_type} onChange={(e) => setFilters({...filters, enquiry_type: e.target.value})}>
            <option value="">All Types</option>
            <option value="walk-in">Walk-in</option>
            <option value="call">Call</option>
            <option value="whatsapp">WhatsApp</option>
            <option value="other">Other</option>
          </select>
          <input
            type="date"
            value={filters.start_date}
            onChange={(e) => setFilters({...filters, start_date: e.target.value})}
            placeholder="Start Date"
          />
          <input
            type="date"
            value={filters.end_date}
            onChange={(e) => setFilters({...filters, end_date: e.target.value})}
            placeholder="End Date"
          />
          <button onClick={() => setShowModal(true)} className="btn-primary">Add Enquiry</button>
        </div>

        {/* Enquiries List */}
        <div className="enquiries-table">
          <table>
            <thead>
              <tr>
                <th>Customer</th>
                <th>Phone</th>
                <th>Type</th>
                <th>Requested</th>
                <th>Reason</th>
                <th>Follow-up</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan="8">Loading...</td></tr>
              ) : enquiries.length === 0 ? (
                <tr><td colSpan="8">No enquiries found</td></tr>
              ) : (
                enquiries.map(enquiry => (
                  <tr key={enquiry.id}>
                    <td>{enquiry.customer_name}</td>
                    <td>{enquiry.customer_phone}</td>
                    <td>{enquiry.enquiry_type}</td>
                    <td>{enquiry.requested_service || '-'}</td>
                    <td>{enquiry.reason_not_delivered || '-'}</td>
                    <td>{enquiry.follow_up_date || '-'}</td>
                    <td>
                      <span className={`status-badge status-${enquiry.status}`}>
                        {enquiry.status}
                      </span>
                    </td>
                    <td>
                      <button onClick={() => openEditModal(enquiry)}>Edit</button>
                      {enquiry.status === 'open' && (
                        <button onClick={() => handleConvert(enquiry.id)} className="btn-convert">
                          Convert to Booking
                        </button>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Create/Edit Modal */}
        {showModal && (
          <div className="modal-overlay" onClick={() => { setShowModal(false); setEditingEnquiry(null); resetForm(); }}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
              <h2>{editingEnquiry ? 'Edit Enquiry' : 'New Missed Enquiry'}</h2>
              <form onSubmit={handleSubmit}>
                <div className="form-group">
                  <label>Customer Name *</label>
                  <input
                    type="text"
                    value={formData.customer_name}
                    onChange={(e) => setFormData({...formData, customer_name: e.target.value})}
                    required
                  />
                </div>
                <div className="form-group">
                  <label>Customer Phone *</label>
                  <input
                    type="tel"
                    value={formData.customer_phone}
                    onChange={(e) => setFormData({...formData, customer_phone: e.target.value})}
                    required
                  />
                </div>
                <div className="form-group">
                  <label>Enquiry Type</label>
                  <select
                    value={formData.enquiry_type}
                    onChange={(e) => setFormData({...formData, enquiry_type: e.target.value})}
                  >
                    <option value="walk-in">Walk-in</option>
                    <option value="call">Call</option>
                    <option value="whatsapp">WhatsApp</option>
                    <option value="other">Other</option>
                  </select>
                </div>
                <div className="form-group">
                  <label>Requested Service</label>
                  <input
                    type="text"
                    value={formData.requested_service}
                    onChange={(e) => setFormData({...formData, requested_service: e.target.value})}
                    placeholder="e.g., Haircut, Facial, Hair Color"
                  />
                </div>
                <div className="form-group">
                  <label>Reason Not Delivered</label>
                  <textarea
                    value={formData.reason_not_delivered}
                    onChange={(e) => setFormData({...formData, reason_not_delivered: e.target.value})}
                  />
                </div>
                <div className="form-group">
                  <label>Follow-up Date</label>
                  <input
                    type="date"
                    value={formData.follow_up_date}
                    onChange={(e) => setFormData({...formData, follow_up_date: e.target.value})}
                  />
                </div>
                <div className="form-group">
                  <label>Status</label>
                  <select
                    value={formData.status}
                    onChange={(e) => setFormData({...formData, status: e.target.value})}
                  >
                    <option value="open">Open</option>
                    <option value="converted">Converted</option>
                    <option value="lost">Lost</option>
                  </select>
                </div>
                <div className="form-group">
                  <label>Notes</label>
                  <textarea
                    value={formData.notes}
                    onChange={(e) => setFormData({...formData, notes: e.target.value})}
                  />
                </div>
                <div className="modal-actions">
                  <button type="button" onClick={() => { setShowModal(false); setEditingEnquiry(null); resetForm(); }}>
                    Cancel
                  </button>
                  <button type="submit" className="btn-primary">Save</button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default MissedEnquiries;

