import React, { useState, useEffect } from 'react'
import { FaBars, FaStar, FaPlus } from 'react-icons/fa'
import './Feedback.css'
import { apiGet, apiPost, apiPut } from '../utils/api'
import { showSuccess, showError, showWarning } from '../utils/toast.jsx'

const Feedback = () => {
  const [searchQuery, setSearchQuery] = useState('')
  const [currentPage, setCurrentPage] = useState(1)
  const [feedbacks, setFeedbacks] = useState([])
  const [loading, setLoading] = useState(true)
  const [showFeedbackModal, setShowFeedbackModal] = useState(false)
  const [showGoogleReviewModal, setShowGoogleReviewModal] = useState(false)
  const [showServiceRecoveryMessage, setShowServiceRecoveryMessage] = useState(false)
  const [lastFeedback, setLastFeedback] = useState(null)
  const [customers, setCustomers] = useState([])
  const [bills, setBills] = useState([])
  const [staffList, setStaffList] = useState([])
  const [feedbackFormData, setFeedbackFormData] = useState({
    customer_id: '',
    bill_id: '',
    staff_id: '',
    rating: 5,
    comment: ''
  })
  
  // PLACEHOLDER: Google Business Profile Review Link
  // TODO: Replace with actual Google Business Profile review link when provided
  const GOOGLE_REVIEW_LINK = '#PLACEHOLDER_GOOGLE_REVIEW_LINK'

  useEffect(() => {
    fetchFeedbacks()
    fetchCustomers()
    fetchStaff()
  }, [searchQuery])

  const fetchCustomers = async () => {
    try {
      const response = await apiGet('/api/customers?per_page=200')
      const data = await response.json()
      setCustomers(data.customers || [])
    } catch (error) {
      console.error('Error fetching customers:', error)
    }
  }

  const fetchStaff = async () => {
    try {
      const response = await apiGet('/api/staffs')
      const data = await response.json()
      setStaffList(data.staffs || [])
    } catch (error) {
      console.error('Error fetching staff:', error)
    }
  }

  const fetchBillsForCustomer = async (customerId) => {
    if (!customerId) {
      setBills([])
      return
    }
    try {
      const response = await apiGet('/api/reports/list-of-bills')
      const data = await response.json()
      const customerBills = Array.isArray(data)
        ? data.filter(bill => bill.customer_id === customerId)
        : []
      setBills(customerBills)
    } catch (error) {
      console.error('Error fetching bills:', error)
      setBills([])
    }
  }

  const fetchFeedbacks = async () => {
    try {
      setLoading(true)
      const params = new URLSearchParams()
      if (searchQuery) params.append('search', searchQuery)
      
      const endpoint = `/api/feedback${params.toString() ? `?${params.toString()}` : ''}`
      const response = await apiGet(endpoint)
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      const data = await response.json()
      // Backend returns array directly
      setFeedbacks(Array.isArray(data) ? data : (data.feedbacks || []))
    } catch (error) {
      console.error('Error fetching feedbacks:', error)
      setFeedbacks([])
    } finally {
      setLoading(false)
    }
  }
  const handleAddFeedback = () => {
    setFeedbackFormData({
      customer_id: '',
      bill_id: '',
      staff_id: '',
      rating: 5,
      comment: ''
    })
    setBills([])
    setShowFeedbackModal(true)
  }

  const handleCustomerChange = (e) => {
    const customerId = e.target.value
    setFeedbackFormData({ ...feedbackFormData, customer_id: customerId, bill_id: '', staff_id: '' })
    fetchBillsForCustomer(customerId)
  }

  const handleBillChange = (e) => {
    const billId = e.target.value
    setFeedbackFormData({ ...feedbackFormData, bill_id: billId })
    
    // Auto-detect staff from bill if available
    if (billId) {
      const selectedBill = bills.find(b => b.id === billId)
      if (selectedBill && selectedBill.staff_id) {
        setFeedbackFormData(prev => ({ ...prev, staff_id: selectedBill.staff_id }))
      }
    }
  }

  const handleSaveFeedback = async () => {
    if (!feedbackFormData.customer_id) {
      showError('Please select a customer')
      return
    }

    if (!feedbackFormData.rating || feedbackFormData.rating < 1 || feedbackFormData.rating > 5) {
      showError('Please select a rating between 1 and 5')
      return
    }

    try {
      const response = await apiPost('/api/feedback', {
          customer_id: feedbackFormData.customer_id,  // MongoDB ObjectId as string
          bill_id: feedbackFormData.bill_id || null,  // MongoDB ObjectId as string or null
          staff_id: feedbackFormData.staff_id || null,  // MongoDB ObjectId as string or null
          rating: parseInt(feedbackFormData.rating),  // Rating is actually a number, keep parseInt
          comment: feedbackFormData.comment.trim()
      })

      if (response.ok) {
        const data = await response.json()
        const feedbackData = data.data || {}
        const rating = feedbackData.rating || feedbackFormData.rating
        
        // Phase 3: Google Review Gating Logic
        if (rating >= 4) {
          // Rating >= 4: Show Google review modal
          setLastFeedback({ id: feedbackData.id, rating })
          setShowGoogleReviewModal(true)
        } else if (rating <= 3) {
          // Rating <= 3: Show service recovery message
          setShowServiceRecoveryMessage(true)
        }
        
        setShowFeedbackModal(false)
        setFeedbackFormData({
          customer_id: '',
          bill_id: '',
          rating: 5,
          comment: ''
        })
        setBills([])
        fetchFeedbacks()
      } else {
        const errorData = await response.json().catch(() => ({ error: 'Unknown error' }))
        showError(errorData.error || `Failed to save feedback (Status: ${response.status})`)
      }
    } catch (error) {
      console.error('Error saving feedback:', error)
      showError(`Error saving feedback: ${error.message}`)
    }
  }

  const renderRating = (rating) => {
    return (
      <div className="rating-display">
        {Array.from({ length: 5 }, (_, i) => (
          <span
            key={i}
            className={`star ${i < rating ? 'filled' : ''}`}
          >
            <FaStar />
          </span>
        ))}
        <span className="rating-number">({rating})</span>
      </div>
    )
  }

  const renderRatingInput = (currentRating, onRatingChange) => {
    return (
      <div className="rating-input">
        {Array.from({ length: 5 }, (_, i) => {
          const rating = i + 1
          return (
            <button
              key={i}
              type="button"
              className={`star-btn ${rating <= currentRating ? 'filled' : ''}`}
              onClick={() => onRatingChange(rating)}
              onMouseEnter={(e) => {
                // Highlight stars on hover
                const stars = e.currentTarget.parentElement.querySelectorAll('.star-btn')
                stars.forEach((star, idx) => {
                  if (idx <= i) {
                    star.classList.add('hover')
                  } else {
                    star.classList.remove('hover')
                  }
                })
              }}
              onMouseLeave={(e) => {
                // Remove hover effect
                const stars = e.currentTarget.parentElement.querySelectorAll('.star-btn')
                stars.forEach(star => star.classList.remove('hover'))
              }}
            >
              <FaStar />
            </button>
          )
        })}
        <span className="rating-label">({currentRating} out of 5)</span>
      </div>
    )
  }

  return (
    <div className="feedback-page">
      {/* Header */}
      <header className="feedback-header">
        <div className="header-left">
          <button className="menu-icon"><FaBars /></button>
          <h1 className="header-title">Feedback</h1>
        </div>
        <div className="header-right">
          <div className="logo-box">
            <span className="logo-text">HAIR STUDIO</span>
          </div>
        </div>
      </header>

      <div className="feedback-container">
        {/* Feedback Card */}
        <div className="feedback-card">
          <div className="card-header">
            <h2 className="card-title">Customer Feedback List</h2>
            <button className="action-btn add-feedback-btn" onClick={handleAddFeedback}>
              <span className="btn-icon"><FaPlus /></span>
              Add Feedback
            </button>
          </div>

          {/* Search Bar */}
          <div className="search-section">
            <input
              type="text"
              className="search-input"
              placeholder="Search customer"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>

          {/* Feedback Table */}
          <div className="table-wrapper">
            <table className="feedback-table">
              <thead>
                <tr>
                  <th>No.</th>
                  <th>Date</th>
                  <th>Customer Name</th>
                  <th>Mobile</th>
                  <th>Rating</th>
                  <th>Feedback</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan="6" className="empty-row">Loading...</td>
                  </tr>
                ) : feedbacks.length === 0 ? (
                  <tr>
                    <td colSpan="6" className="empty-row">No feedback found</td>
                  </tr>
                ) : (
                  feedbacks.map((feedback) => (
                    <tr key={feedback.id}>
                      <td>{feedback.id}</td>
                      <td>{feedback.created_at ? new Date(feedback.created_at).toLocaleDateString() : 'N/A'}</td>
                      <td>{feedback.customer_name || '-'}</td>
                      <td>
                        {feedback.customer_mobile
                          ? `+91 ${feedback.customer_mobile}`
                          : '-'}
                      </td>
                      <td>{renderRating(feedback.rating || 0)}</td>
                      <td className="feedback-text">{feedback.comment || '-'}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="pagination">
            <button
              className="page-btn"
              onClick={() => setCurrentPage(1)}
              disabled={currentPage === 1}
            >
              First
            </button>
            <button
              className="page-btn"
              onClick={() => setCurrentPage((prev) => Math.max(1, prev - 1))}
              disabled={currentPage === 1}
            >
              Previous
            </button>
            <button className="page-btn active">{currentPage}</button>
            <button
              className="page-btn"
              onClick={() => setCurrentPage((prev) => prev + 1)}
            >
              Next
            </button>
            <button className="page-btn">Last</button>
          </div>
        </div>
      </div>

      {/* Add Feedback Modal */}
      {showFeedbackModal && (
        <div className="modal-overlay" onClick={() => setShowFeedbackModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2>Add Customer Feedback</h2>
            <div className="form-group">
              <label>Customer *</label>
              <select
                value={feedbackFormData.customer_id}
                onChange={handleCustomerChange}
                required
              >
                <option value="">Select Customer</option>
                {customers.map(customer => (
                  <option key={customer.id} value={customer.id}>
                    {customer.firstName || customer.first_name} {customer.lastName || customer.last_name} - {customer.mobile}
                  </option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label>Bill (Optional)</label>
              <select
                value={feedbackFormData.bill_id}
                onChange={handleBillChange}
                disabled={!feedbackFormData.customer_id}
              >
                <option value="">No Bill Selected</option>
                {bills.map(bill => (
                  <option key={bill.id} value={bill.id}>
                    {bill.bill_number} - ₹{bill.final_amount} ({new Date(bill.bill_date).toLocaleDateString()})
                  </option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label>Staff Member (Optional)</label>
              <select
                value={feedbackFormData.staff_id}
                onChange={(e) => setFeedbackFormData({ ...feedbackFormData, staff_id: e.target.value })}
              >
                <option value="">Select Staff (Auto-detected from bill)</option>
                {staffList.map(staff => (
                  <option key={staff.id} value={staff.id}>
                    {staff.first_name} {staff.last_name}
                  </option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label>Rating *</label>
              {renderRatingInput(feedbackFormData.rating, (rating) => 
                setFeedbackFormData({ ...feedbackFormData, rating })
              )}
            </div>
            <div className="form-group">
              <label>Comment</label>
              <textarea
                value={feedbackFormData.comment}
                onChange={(e) => setFeedbackFormData({ ...feedbackFormData, comment: e.target.value })}
                placeholder="Enter feedback comment..."
                rows="4"
              />
            </div>
            <div className="modal-actions">
              <button className="btn-cancel" onClick={() => setShowFeedbackModal(false)}>Cancel</button>
              <button className="btn-save" onClick={handleSaveFeedback}>Save Feedback</button>
            </div>
          </div>
        </div>
      )}

      {/* Google Review Modal (Phase 3 - Placeholder) */}
      {showGoogleReviewModal && (
        <div className="modal-overlay" onClick={() => setShowGoogleReviewModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2>Thank You for Your Feedback! ⭐</h2>
            <p>We're thrilled you had a great experience! Would you like to share your review on Google?</p>
            <div className="modal-actions">
              <button className="btn-cancel" onClick={() => setShowGoogleReviewModal(false)}>
                Maybe Later
              </button>
              <button
                className="btn-save"
                onClick={async () => {
                  // Mark review link as clicked
                  if (lastFeedback?.id) {
                    try {
                      await apiPut(`/api/feedback/${lastFeedback.id}/mark-review-clicked`, {});
                    } catch (error) {
                      console.error('Error marking review clicked:', error);
                    }
                  }
                  
                  // PLACEHOLDER: Open Google review link
                  // TODO: Replace GOOGLE_REVIEW_LINK with actual link when provided
                  if (GOOGLE_REVIEW_LINK !== '#PLACEHOLDER_GOOGLE_REVIEW_LINK') {
                    window.open(GOOGLE_REVIEW_LINK, '_blank');
                  } else {
                    showError('Google Review Link not configured yet. Please contact administrator.');
                  }
                  setShowGoogleReviewModal(false);
                }}
              >
                Post to Google
              </button>
            </div>
            <p className="placeholder-note" style={{ fontSize: '12px', color: '#666', marginTop: '10px' }}>
              ⚠️ Google Review integration is in placeholder mode. Link will be activated when provided.
            </p>
          </div>
        </div>
      )}

      {/* Service Recovery Message (Phase 3) */}
      {showServiceRecoveryMessage && (
        <div className="modal-overlay" onClick={() => setShowServiceRecoveryMessage(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2>We're Sorry 😔</h2>
            <p>We're sorry to hear about your experience. A service recovery case has been created and our team will reach out to you shortly to make things right.</p>
            <p>Thank you for helping us improve!</p>
            <div className="modal-actions">
              <button className="btn-save" onClick={() => setShowServiceRecoveryMessage(false)}>
                OK
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default Feedback

