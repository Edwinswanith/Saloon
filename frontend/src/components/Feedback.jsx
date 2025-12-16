import React, { useState, useEffect } from 'react'
import { FaBars, FaStar, FaPlus } from 'react-icons/fa'
import './Feedback.css'
import { API_BASE_URL } from '../config'

const Feedback = () => {
  const [searchQuery, setSearchQuery] = useState('')
  const [currentPage, setCurrentPage] = useState(1)
  const [feedbacks, setFeedbacks] = useState([])
  const [loading, setLoading] = useState(true)
  const [showFeedbackModal, setShowFeedbackModal] = useState(false)
  const [customers, setCustomers] = useState([])
  const [bills, setBills] = useState([])
  const [feedbackFormData, setFeedbackFormData] = useState({
    customer_id: '',
    bill_id: '',
    rating: 5,
    comment: ''
  })

  useEffect(() => {
    fetchFeedbacks()
    fetchCustomers()
  }, [searchQuery])

  const fetchCustomers = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/customers?per_page=200`)
      const data = await response.json()
      setCustomers(data.customers || [])
    } catch (error) {
      console.error('Error fetching customers:', error)
    }
  }

  const fetchBillsForCustomer = async (customerId) => {
    if (!customerId) {
      setBills([])
      return
    }
    try {
      const response = await fetch(`${API_BASE_URL}/api/reports/list-of-bills`)
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
      
      const response = await fetch(`${API_BASE_URL}/api/feedback?${params}`)
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
      rating: 5,
      comment: ''
    })
    setBills([])
    setShowFeedbackModal(true)
  }

  const handleCustomerChange = (e) => {
    const customerId = e.target.value
    setFeedbackFormData({ ...feedbackFormData, customer_id: customerId, bill_id: '' })
    fetchBillsForCustomer(customerId)
  }

  const handleSaveFeedback = async () => {
    if (!feedbackFormData.customer_id) {
      alert('Please select a customer')
      return
    }

    if (!feedbackFormData.rating || feedbackFormData.rating < 1 || feedbackFormData.rating > 5) {
      alert('Please select a rating between 1 and 5')
      return
    }

    try {
      const response = await fetch(`${API_BASE_URL}/api/feedback`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          customer_id: feedbackFormData.customer_id,  // MongoDB ObjectId as string
          bill_id: feedbackFormData.bill_id || null,  // MongoDB ObjectId as string or null
          rating: parseInt(feedbackFormData.rating),  // Rating is actually a number, keep parseInt
          comment: feedbackFormData.comment.trim()
        }),
      })

      if (response.ok) {
        const data = await response.json()
        alert(data.message || 'Feedback added successfully!')
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
        alert(errorData.error || `Failed to save feedback (Status: ${response.status})`)
      }
    } catch (error) {
      console.error('Error saving feedback:', error)
      alert(`Error saving feedback: ${error.message}\n\nPlease check if the backend server is running at ${API_BASE_URL}`)
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
                onChange={(e) => setFeedbackFormData({ ...feedbackFormData, bill_id: e.target.value })}
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
    </div>
  )
}

export default Feedback

