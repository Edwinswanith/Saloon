import React, { useState, useEffect } from 'react'
import {
  FaArrowLeft,
  FaCloudDownloadAlt,
  FaTimes,
} from 'react-icons/fa'
import './ListOfBills.css'
import { API_BASE_URL } from '../config'
import { apiGet } from '../utils/api'
import { formatLocalDate } from '../utils/dateUtils'
import { useAuth } from '../contexts/AuthContext'

const ListOfBills = ({ setActivePage }) => {
  const { currentBranch } = useAuth()
  const [dateFilter, setDateFilter] = useState('month') // Default to month to show more bills
  const [bills, setBills] = useState([])
  const [loading, setLoading] = useState(true)
  const [totalTransactions, setTotalTransactions] = useState(0)
  const [totalRevenue, setTotalRevenue] = useState(0)
  const [showModal, setShowModal] = useState(false)
  const [selectedBill, setSelectedBill] = useState(null)
  const [billDetails, setBillDetails] = useState(null)
  const [loadingDetails, setLoadingDetails] = useState(false)

  useEffect(() => {
    fetchBills()
  }, [dateFilter, currentBranch])

  // Listen for branch changes
  useEffect(() => {
    const handleBranchChange = () => {
      console.log('[ListOfBills] Branch changed, refreshing bills...')
      fetchBills()
    }
    
    window.addEventListener('branchChanged', handleBranchChange)
    return () => window.removeEventListener('branchChanged', handleBranchChange)
  }, [currentBranch])

  const getDateRange = () => {
    const today = new Date()
    const yesterday = new Date(today)
    yesterday.setDate(yesterday.getDate() - 1)
    const weekStart = new Date(today)
    weekStart.setDate(today.getDate() - today.getDay())
    const monthStart = new Date(today.getFullYear(), today.getMonth(), 1)
    const yearStart = new Date(today.getFullYear(), 0, 1)

    switch (dateFilter) {
      case 'today':
        return { start: formatLocalDate(today), end: formatLocalDate(today) }
      case 'yesterday':
        return { start: formatLocalDate(yesterday), end: formatLocalDate(yesterday) }
      case 'week':
        return { start: formatLocalDate(weekStart), end: formatLocalDate(today) }
      case 'month':
        return { start: formatLocalDate(monthStart), end: formatLocalDate(today) }
      case 'year':
        return { start: formatLocalDate(yearStart), end: formatLocalDate(today) }
      case 'all':
        return { start: null, end: null } // Show all bills
      default:
        return { start: null, end: null } // Show all bills if no filter
    }
  }

  const fetchBills = async () => {
    try {
      setLoading(true)
      const { start, end } = getDateRange()
      const params = new URLSearchParams()
      if (start) params.append('start_date', start)
      if (end) params.append('end_date', end)

      const response = await apiGet(`/api/reports/list-of-bills?${params}`)
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const data = await response.json()
      
      if (Array.isArray(data)) {
        setBills(data)
        setTotalTransactions(data.length)
        setTotalRevenue(data.reduce((sum, bill) => sum + (bill.final_amount || 0), 0))
      } else {
        setBills([])
        setTotalTransactions(0)
        setTotalRevenue(0)
      }
    } catch (error) {
      console.error('Error fetching bills:', error)
      setBills([])
      setTotalTransactions(0)
      setTotalRevenue(0)
    } finally {
      setLoading(false)
    }
  }

  const handleBackToReports = () => {
    if (setActivePage) {
      setActivePage('reports')
    }
  }

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A'
    try {
      // Parse the ISO date string (which is in UTC)
      const date = new Date(dateString)
      // Get local date components to display the correct local date
      // This handles timezone conversion properly
      const day = String(date.getDate()).padStart(2, '0')
      const month = String(date.getMonth() + 1).padStart(2, '0')
      const year = date.getFullYear()
      return `${day}-${month}-${year}`
    } catch (error) {
      console.error('Error formatting date:', dateString, error)
      return 'N/A'
    }
  }

  const formatDateTime = (dateString) => {
    if (!dateString) return 'N/A'
    try {
      const date = new Date(dateString)
      const day = String(date.getDate()).padStart(2, '0')
      const month = String(date.getMonth() + 1).padStart(2, '0')
      const year = date.getFullYear()
      const hours = String(date.getHours()).padStart(2, '0')
      const minutes = String(date.getMinutes()).padStart(2, '0')
      const ampm = hours >= 12 ? 'PM' : 'AM'
      const hour12 = hours % 12 || 12
      return `${day}-${month}-${year} ${hour12}:${minutes} ${ampm}`
    } catch (error) {
      return 'N/A'
    }
  }

  const handleViewDetails = async (bill) => {
    setSelectedBill(bill)
    setShowModal(true)
    setLoadingDetails(true)
    setBillDetails(null)

    try {
      const billId = bill.id
      if (!billId) {
        console.error('Bill ID not found')
        setLoadingDetails(false)
        return
      }

      // Fetch detailed bill information
      const detailsResponse = await apiGet(`/api/bills/${billId}`)
      if (detailsResponse.ok) {
        const details = await detailsResponse.json()
        setBillDetails(details)
      } else {
        // Fallback: use basic bill data
        setBillDetails(bill)
      }
    } catch (error) {
      console.error('Error fetching bill details:', error)
      // Fallback: use basic bill data
      setBillDetails(bill)
    } finally {
      setLoadingDetails(false)
    }
  }

  const formatCurrency = (amount) => {
    return `₹${amount?.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || '0.00'}`
  }

  return (
    <div className="list-of-bills-page">
      <div className="list-of-bills-container">
        {/* Main Report Card */}
        <div className="report-card">
          {/* Back Button */}
          <button className="back-button" onClick={handleBackToReports}>
            <FaArrowLeft />
            Back to Reports Hub
          </button>

          {/* Summary Cards */}
          <div className="summary-cards">
            <div className="summary-card transactions-card">
              <div className="summary-value">{totalTransactions}</div>
              <div className="summary-label">TOTAL TRANSACTIONS</div>
            </div>
            <div className="summary-card revenue-card">
              <div className="summary-value">₹{totalRevenue.toFixed(0)}</div>
              <div className="summary-label">TOTAL REVENUE</div>
            </div>
          </div>

          {/* Filters and Actions */}
          <div className="filters-actions-section">
            <div className="filter-group">
              <select
                className="date-filter-dropdown"
                value={dateFilter}
                onChange={(e) => setDateFilter(e.target.value)}
              >
                <option value="all">All Bills</option>
                <option value="today">Today</option>
                <option value="yesterday">Yesterday</option>
                <option value="week">This Week</option>
                <option value="month">This Month</option>
                <option value="year">This Year</option>
                <option value="custom">Custom Range</option>
              </select>
            </div>

            <button 
              className="download-report-btn"
              onClick={() => {
                // Create CSV content
                const csvContent = [
                  ['Invoice No.', 'Customer', 'Date', 'Payment Mode', 'Subtotal', 'Discount', 'Net', 'Tax', 'Total'],
                  ...bills.map(bill => [
                    bill.bill_number || 'N/A',
                    bill.customer_name || 'Walk-in',
                    formatDate(bill.bill_date),
                    bill.payment_mode || 'N/A',
                    bill.subtotal?.toFixed(2) || '0.00',
                    bill.discount?.toFixed(2) || '0.00',
                    ((bill.subtotal || 0) - (bill.discount || 0)).toFixed(2),
                    bill.tax?.toFixed(2) || '0.00',
                    bill.final_amount?.toFixed(2) || '0.00',
                  ])
                ].map(row => row.join(',')).join('\n')
                
                // Download CSV
                const blob = new Blob([csvContent], { type: 'text/csv' })
                const url = window.URL.createObjectURL(blob)
                const a = document.createElement('a')
                a.href = url
                a.download = `bills-report-${dateFilter}-${new Date().toISOString().split('T')[0]}.csv`
                a.click()
                window.URL.revokeObjectURL(url)
              }}
            >
              <FaCloudDownloadAlt />
              Download Report
            </button>
          </div>

          {/* Bills Table */}
          <div className="table-container">
            <table className="bills-table">
              <thead>
                <tr>
                  <th>Invoice No.</th>
                  <th>Customer</th>
                  <th>Date</th>
                  <th>Payment Mode</th>
                  <th>Subtotal</th>
                  <th>Discount</th>
                  <th>Referral Discount</th>
                  <th>Net</th>
                  <th>Tax</th>
                  <th>Total</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan="11" className="empty-message">
                      Loading bills...
                    </td>
                  </tr>
                ) : bills.length === 0 ? (
                  <tr>
                    <td colSpan="11" className="empty-message">
                      No bills found for this selection.
                    </td>
                  </tr>
                ) : (
                  bills.map((bill, index) => (
                    <tr key={index}>
                      <td>{bill.bill_number || 'N/A'}</td>
                      <td>{bill.customer_name || 'Walk-in'}</td>
                      <td>{formatDate(bill.bill_date)}</td>
                      <td>{bill.payment_mode || 'N/A'}</td>
                      <td>₹{bill.subtotal?.toFixed(2) || '0.00'}</td>
                      <td>₹{bill.discount?.toFixed(2) || '0.00'}</td>
                      <td>₹0.00</td>
                      <td>₹{((bill.subtotal || 0) - (bill.discount || 0)).toFixed(2)}</td>
                      <td>₹{bill.tax?.toFixed(2) || '0.00'}</td>
                      <td>₹{bill.final_amount?.toFixed(2) || '0.00'}</td>
                      <td>
                        <button 
                          className="view-btn"
                          onClick={() => handleViewDetails(bill)}
                        >
                          View
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Bill Details Modal */}
      {showModal && selectedBill && (
        <div className="customer-modal-overlay" onClick={() => setShowModal(false)}>
          <div className="customer-modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="customer-modal-header">
              <h2>Bill Details</h2>
              <button className="customer-modal-close" onClick={() => setShowModal(false)}>
                <FaTimes />
              </button>
            </div>

            <div className="customer-modal-body">
              {loadingDetails ? (
                <div className="customer-modal-loading">Loading bill details...</div>
              ) : (
                <>
                  {/* Bill Information */}
                  <div className="customer-details-section">
                    <h3>Bill Information</h3>
                    <div className="customer-details-grid">
                      <div className="customer-detail-item">
                        <span className="detail-label">Bill Number:</span>
                        <span className="detail-value">{selectedBill.bill_number || 'N/A'}</span>
                      </div>
                      <div className="customer-detail-item">
                        <span className="detail-label">Date:</span>
                        <span className="detail-value">{formatDateTime(selectedBill.bill_date || billDetails?.bill_date)}</span>
                      </div>
                      <div className="customer-detail-item">
                        <span className="detail-label">Customer:</span>
                        <span className="detail-value">{selectedBill.customer_name || billDetails?.customer_name || 'Walk-in'}</span>
                      </div>
                      {selectedBill.customer_mobile && (
                        <div className="customer-detail-item">
                          <span className="detail-label">Customer Mobile:</span>
                          <span className="detail-value">{selectedBill.customer_mobile}</span>
                        </div>
                      )}
                      <div className="customer-detail-item">
                        <span className="detail-label">Payment Mode:</span>
                        <span className="detail-value">{selectedBill.payment_mode || billDetails?.payment_mode || 'N/A'}</span>
                      </div>
                      {billDetails?.booking_status && (
                        <div className="customer-detail-item">
                          <span className="detail-label">Booking Status:</span>
                          <span className="detail-value">{billDetails.booking_status}</span>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Amount Breakdown */}
                  <div className="customer-details-section">
                    <h3>Amount Breakdown</h3>
                    <div className="customer-details-grid">
                      <div className="customer-detail-item">
                        <span className="detail-label">Subtotal:</span>
                        <span className="detail-value">{formatCurrency(selectedBill.subtotal || billDetails?.subtotal || 0)}</span>
                      </div>
                      <div className="customer-detail-item">
                        <span className="detail-label">Discount:</span>
                        <span className="detail-value">{formatCurrency(selectedBill.discount || billDetails?.discount_amount || 0)}</span>
                      </div>
                      <div className="customer-detail-item">
                        <span className="detail-label">Tax:</span>
                        <span className="detail-value">{formatCurrency(selectedBill.tax || billDetails?.tax_amount || 0)}</span>
                      </div>
                      <div className="customer-detail-item">
                        <span className="detail-label">Final Amount:</span>
                        <span className="detail-value revenue-stat">{formatCurrency(selectedBill.final_amount || billDetails?.final_amount || 0)}</span>
                      </div>
                    </div>
                  </div>

                  {/* Bill Items */}
                  {billDetails?.items && Array.isArray(billDetails.items) && billDetails.items.length > 0 && (
                    <div className="customer-details-section">
                      <h3>Bill Items</h3>
                      <div style={{ overflowX: 'auto' }}>
                        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
                          <thead>
                            <tr style={{ background: '#f9fafb', borderBottom: '2px solid #e5e7eb' }}>
                              <th style={{ padding: '8px 12px', textAlign: 'left', fontWeight: 600, color: '#374151' }}>Item</th>
                              <th style={{ padding: '8px 12px', textAlign: 'left', fontWeight: 600, color: '#374151' }}>Type</th>
                              <th style={{ padding: '8px 12px', textAlign: 'right', fontWeight: 600, color: '#374151' }}>Quantity</th>
                              <th style={{ padding: '8px 12px', textAlign: 'right', fontWeight: 600, color: '#374151' }}>Price</th>
                              <th style={{ padding: '8px 12px', textAlign: 'right', fontWeight: 600, color: '#374151' }}>Total</th>
                            </tr>
                          </thead>
                          <tbody>
                            {billDetails.items.map((item, index) => (
                              <tr key={index} style={{ borderBottom: '1px solid #f3f4f6' }}>
                                <td style={{ padding: '8px 12px', color: '#374151' }}>
                                  {item.service_name || item.product_name || item.package_name || item.prepaid_name || 'N/A'}
                                </td>
                                <td style={{ padding: '8px 12px', color: '#6b7280', textTransform: 'capitalize' }}>
                                  {item.item_type || 'N/A'}
                                </td>
                                <td style={{ padding: '8px 12px', textAlign: 'right', color: '#374151' }}>
                                  {item.quantity || 1}
                                </td>
                                <td style={{ padding: '8px 12px', textAlign: 'right', color: '#374151' }}>
                                  {formatCurrency(item.price || 0)}
                                </td>
                                <td style={{ padding: '8px 12px', textAlign: 'right', color: '#374151', fontWeight: 500 }}>
                                  {formatCurrency(item.total || 0)}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default ListOfBills

