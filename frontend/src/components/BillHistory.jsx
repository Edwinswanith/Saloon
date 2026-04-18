import React, { useState, useEffect, useCallback } from 'react'
import {
  FaSearch,
  FaTimes,
  FaWhatsapp,
  FaReceipt,
  FaUser,
  FaPhone,
  FaCalendarAlt,
  FaMoneyBillWave,
} from 'react-icons/fa'
import { apiGet, apiPost } from '../utils/api'
import { PUBLIC_BASE_URL } from '../config'
import { formatLocalDate } from '../utils/dateUtils'
import { useAuth } from '../contexts/AuthContext'
import { useBusiness } from '../contexts/BusinessContext'
import toast from 'react-hot-toast'
import './BillHistory.css'

const BRANCH_INFO = {
  'Main Road': { phone: '044-22520395, 044-66126131' },
  'EB': { phone: '044-22521064, 044-43531642' },
  'Madanandapuram': { phone: '044-48645868' },
  'Kolapakkam': { phone: '044-49504722' },
  'Kovur': { phone: '9500186074' },
  'DLF': { phone: '044-48543022, 9840192264' },
}

const BillHistory = () => {
  const { currentBranch } = useAuth()
  const { businessName: configuredBusinessName } = useBusiness()
  const [bills, setBills] = useState([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [dateFilter, setDateFilter] = useState('today')
  const [customDate, setCustomDate] = useState('')
  const [selectedBill, setSelectedBill] = useState(null)
  const [billDetails, setBillDetails] = useState(null)
  const [loadingDetails, setLoadingDetails] = useState(false)
  const [sendingWhatsApp, setSendingWhatsApp] = useState(false)
  const [pagination, setPagination] = useState({ page: 1, pages: 0, total: 0 })

  const getDateRange = useCallback(() => {
    const today = new Date()
    const yesterday = new Date(today)
    yesterday.setDate(yesterday.getDate() - 1)
    const weekStart = new Date(today)
    weekStart.setDate(today.getDate() - today.getDay())
    const monthStart = new Date(today.getFullYear(), today.getMonth(), 1)

    switch (dateFilter) {
      case 'today':
        return { start: formatLocalDate(today), end: formatLocalDate(today) }
      case 'yesterday':
        return { start: formatLocalDate(yesterday), end: formatLocalDate(yesterday) }
      case 'week':
        return { start: formatLocalDate(weekStart), end: formatLocalDate(today) }
      case 'month':
        return { start: formatLocalDate(monthStart), end: formatLocalDate(today) }
      case 'custom':
        return customDate ? { start: customDate, end: customDate } : { start: null, end: null }
      case 'all':
        return { start: null, end: null }
      default:
        return { start: formatLocalDate(today), end: formatLocalDate(today) }
    }
  }, [dateFilter, customDate])

  const fetchBills = useCallback(async (page = 1) => {
    try {
      setLoading(true)
      const { start, end } = getDateRange()
      const params = new URLSearchParams()
      if (start) params.append('start_date', start)
      if (end) params.append('end_date', end)
      params.append('page', page)
      params.append('per_page', 50)
      params.append('booking_status', 'service-completed')

      const response = await apiGet(`/api/bills?${params}`)
      if (!response.ok) throw new Error('Failed to fetch bills')

      const data = await response.json()
      setBills(data.bills || [])
      setPagination({
        page: data.page || 1,
        pages: data.pages || 0,
        total: data.total || 0,
      })
    } catch (error) {
      console.error('Error fetching bills:', error)
      setBills([])
      setPagination({ page: 1, pages: 0, total: 0 })
    } finally {
      setLoading(false)
    }
  }, [getDateRange])

  useEffect(() => {
    fetchBills(1)
  }, [fetchBills, currentBranch])

  useEffect(() => {
    const handleBranchChange = () => fetchBills(1)
    window.addEventListener('branchChanged', handleBranchChange)
    return () => window.removeEventListener('branchChanged', handleBranchChange)
  }, [fetchBills])

  const filteredBills = bills.filter((bill) => {
    if (!searchQuery.trim()) return true
    const q = searchQuery.toLowerCase()
    return (
      (bill.customer_name || '').toLowerCase().includes(q) ||
      (bill.bill_number || '').toLowerCase().includes(q) ||
      (bill.customer_mobile || '').includes(q)
    )
  })

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A'
    try {
      const date = new Date(dateString)
      const day = String(date.getDate()).padStart(2, '0')
      const month = String(date.getMonth() + 1).padStart(2, '0')
      const year = date.getFullYear()
      return `${day}-${month}-${year}`
    } catch {
      return 'N/A'
    }
  }

  const formatTime = (dateString) => {
    if (!dateString) return ''
    try {
      const date = new Date(dateString)
      const hours = date.getHours()
      const minutes = String(date.getMinutes()).padStart(2, '0')
      const ampm = hours >= 12 ? 'PM' : 'AM'
      const hour12 = hours % 12 || 12
      return `${hour12}:${minutes} ${ampm}`
    } catch {
      return ''
    }
  }

  const formatCurrency = (amount) => {
    return `₹${parseFloat(amount || 0).toLocaleString('en-IN', {
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    })}`
  }

  const handleViewDetails = async (bill) => {
    setSelectedBill(bill)
    setLoadingDetails(true)
    setBillDetails(null)

    try {
      const response = await apiGet(`/api/bills/${bill.id}`)
      if (response.ok) {
        const details = await response.json()
        setBillDetails(details)
      } else {
        setBillDetails(bill)
      }
    } catch {
      setBillDetails(bill)
    } finally {
      setLoadingDetails(false)
    }
  }

  const closeModal = () => {
    setSelectedBill(null)
    setBillDetails(null)
  }

  useEffect(() => {
    if (selectedBill) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = ''
    }
    return () => { document.body.style.overflow = '' }
  }, [selectedBill])

  const handleSendWhatsApp = async () => {
    const details = billDetails || selectedBill
    if (!details) return

    const mobile = details.customer_mobile
    if (!mobile) {
      toast.error('No mobile number available for this customer')
      return
    }

    setSendingWhatsApp(true)
    try {
      let phoneNumber = mobile.replace(/[^0-9]/g, '')
      if (phoneNumber.length === 10) phoneNumber = '91' + phoneNumber

      const customerName = details.customer_name || 'Customer'
      const businessName = configuredBusinessName || 'Priyanka Nature Cure'
      const supportPhone = '8095851126'
      const feedbackLink = `${PUBLIC_BASE_URL}/feedback`

      let signoffPhone = '+91 xyz'
      if (currentBranch?.name) {
        const branchKey = Object.keys(BRANCH_INFO).find(
          (key) => key.toLowerCase() === currentBranch.name.trim().toLowerCase()
        )
        if (branchKey && BRANCH_INFO[branchKey]?.phone) {
          signoffPhone = BRANCH_INFO[branchKey].phone.split(',')[0].trim()
          if (signoffPhone.match(/^\d{10}$/)) signoffPhone = `+91 ${signoffPhone}`
        }
      }

      let invoiceLink = ''
      try {
        const res = await apiPost(`/api/bills/${details.id}/share-link`)
        if (res.ok) {
          const data = await res.json()
          invoiceLink = `${PUBLIC_BASE_URL}/i/${data.share_code}/pdf`
        }
      } catch {
        // Continue without link
      }

      let message = `Dear ${customerName},\n\n`
      message += `Thank you for visiting *${businessName}*!\n\n`
      message += `View your *invoice* here:\n\n`
      if (invoiceLink) message += `${invoiceLink}\n\n`
      message += `Need help or want to book your next visit? Call or WhatsApp us at *${supportPhone}*\n\n`
      message += `We'd love to hear from you! Share your *feedback* here:\n\n`
      message += `${feedbackLink}\n\n`
      message += `Thanks\n${businessName}\n${signoffPhone}`

      const whatsappUrl = `https://wa.me/${phoneNumber}?text=${encodeURIComponent(message)}`
      window.open(whatsappUrl, '_blank')
      toast.success('WhatsApp opened')
    } catch {
      toast.error('Failed to generate WhatsApp link')
    } finally {
      setSendingWhatsApp(false)
    }
  }

  const getPaymentBadgeClass = (mode) => {
    switch (mode?.toLowerCase()) {
      case 'cash': return 'badge-cash'
      case 'upi': return 'badge-upi'
      case 'card': return 'badge-card'
      default: return 'badge-default'
    }
  }

  return (
    <div className="bill-history-page">
      <div className="bill-history-container">
        <div className="bh-header">
          <div className="bh-header-left">
            <FaReceipt className="bh-header-icon" />
            <div>
              <h1 className="bh-title">Bill History</h1>
              <p className="bh-subtitle">{pagination.total} bill{pagination.total !== 1 ? 's' : ''} found</p>
            </div>
          </div>
        </div>

        <div className="bh-filters">
          <div className="bh-filter-top">
            <div className="bh-search-wrap">
              <FaSearch className="bh-search-icon" />
              <input
                type="text"
                placeholder="Search by name, mobile, or bill number..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="bh-search-input"
              />
              {searchQuery && (
                <button className="bh-search-clear" onClick={() => setSearchQuery('')}>
                  <FaTimes />
                </button>
              )}
            </div>

            <select
              className="bh-date-select"
              value={dateFilter}
              onChange={(e) => setDateFilter(e.target.value)}
            >
              <option value="today">Today</option>
              <option value="yesterday">Yesterday</option>
              <option value="week">This Week</option>
              <option value="month">This Month</option>
              <option value="custom">Pick a Date</option>
              <option value="all">All Bills</option>
            </select>
          </div>

          {dateFilter === 'custom' && (
            <div className="bh-filter-row">
              <input
                type="date"
                className="bh-date-picker"
                value={customDate}
                onChange={(e) => setCustomDate(e.target.value)}
              />
            </div>
          )}
        </div>

        <div className="bh-bill-list">
          {loading ? (
            <div className="bh-empty-state">Loading bills...</div>
          ) : filteredBills.length === 0 ? (
            <div className="bh-empty-state">
              <FaReceipt className="bh-empty-icon" />
              <p>No bills found for this selection</p>
            </div>
          ) : (
            filteredBills.map((bill) => (
              <div
                key={bill.id}
                className="bh-bill-card"
                onClick={() => handleViewDetails(bill)}
              >
                <div className="bh-card-top">
                  <div className="bh-card-customer">
                    <FaUser className="bh-card-icon" />
                    <span className="bh-card-name">{bill.customer_name || 'Walk-in'}</span>
                  </div>
                  <span className="bh-card-amount">{formatCurrency(bill.final_amount)}</span>
                </div>
                <div className="bh-card-bottom">
                  <div className="bh-card-meta">
                    <span className="bh-card-date">
                      <FaCalendarAlt /> {formatDate(bill.bill_date)} {formatTime(bill.bill_date)}
                    </span>
                    <span className="bh-card-billno">{bill.bill_number}</span>
                  </div>
                  <span className={`bh-payment-badge ${getPaymentBadgeClass(bill.payment_mode)}`}>
                    {bill.payment_mode || 'N/A'}
                  </span>
                </div>
              </div>
            ))
          )}
        </div>

        {pagination.pages > 1 && (
          <div className="bh-pagination">
            <button
              disabled={pagination.page <= 1}
              onClick={() => fetchBills(pagination.page - 1)}
              className="bh-page-btn"
            >
              Previous
            </button>
            <span className="bh-page-info">
              Page {pagination.page} of {pagination.pages}
            </span>
            <button
              disabled={pagination.page >= pagination.pages}
              onClick={() => fetchBills(pagination.page + 1)}
              className="bh-page-btn"
            >
              Next
            </button>
          </div>
        )}
      </div>

      {selectedBill && (
        <div className="bh-modal-overlay" onClick={closeModal}>
          <div className="bh-modal" onClick={(e) => e.stopPropagation()}>
            <div className="bh-modal-header">
              <h2>Bill Details</h2>
              <button className="bh-modal-close" onClick={closeModal}>
                <FaTimes />
              </button>
            </div>

            <div className="bh-modal-body">
              {loadingDetails ? (
                <div className="bh-modal-loading">Loading bill details...</div>
              ) : (
                <>
                  <div className="bh-detail-section">
                    <h3>Bill Information</h3>
                    <div className="bh-detail-grid">
                      <div className="bh-detail-item">
                        <span className="bh-label">Bill Number</span>
                        <span className="bh-value">{(billDetails || selectedBill).bill_number || 'N/A'}</span>
                      </div>
                      <div className="bh-detail-item">
                        <span className="bh-label">Date</span>
                        <span className="bh-value">
                          {formatDate((billDetails || selectedBill).bill_date)}{' '}
                          {formatTime((billDetails || selectedBill).bill_date)}
                        </span>
                      </div>
                      <div className="bh-detail-item">
                        <span className="bh-label">Customer</span>
                        <span className="bh-value">
                          <FaUser style={{ marginRight: 6, opacity: 0.5 }} />
                          {(billDetails || selectedBill).customer_name || 'Walk-in'}
                        </span>
                      </div>
                      {(billDetails || selectedBill).customer_mobile && (
                        <div className="bh-detail-item">
                          <span className="bh-label">Mobile</span>
                          <span className="bh-value">
                            <FaPhone style={{ marginRight: 6, opacity: 0.5 }} />
                            <a href={`tel:${(billDetails || selectedBill).customer_mobile}`}>
                              {(billDetails || selectedBill).customer_mobile}
                            </a>
                          </span>
                        </div>
                      )}
                      <div className="bh-detail-item">
                        <span className="bh-label">Payment Mode</span>
                        <span className="bh-value">
                          <FaMoneyBillWave style={{ marginRight: 6, opacity: 0.5 }} />
                          {(billDetails || selectedBill).payment_mode || 'N/A'}
                        </span>
                      </div>
                      <div className="bh-detail-item">
                        <span className="bh-label">Status</span>
                        <span className="bh-value bh-status-badge">
                          {(billDetails || selectedBill).booking_status || 'N/A'}
                        </span>
                      </div>
                    </div>
                  </div>

                  {billDetails?.items && billDetails.items.length > 0 && (
                    <div className="bh-detail-section">
                      <h3>Services & Items</h3>
                      <div className="bh-items-list">
                        {billDetails.items.map((item, idx) => (
                          <div key={idx} className="bh-item-row">
                            <div className="bh-item-info">
                              <span className="bh-item-name">
                                {item.service_name || item.product_name || item.package_name || item.name || 'Item'}
                              </span>
                              <span className="bh-item-type">{item.item_type || 'service'}</span>
                              {item.staff_name && (
                                <span className="bh-item-staff">Staff: {item.staff_name}</span>
                              )}
                            </div>
                            <div className="bh-item-pricing">
                              <span className="bh-item-qty">x{item.quantity || 1}</span>
                              <span className="bh-item-total">{formatCurrency(item.total || item.price || 0)}</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className="bh-detail-section">
                    <h3>Amount Breakdown</h3>
                    <div className="bh-amount-breakdown">
                      <div className="bh-amount-row">
                        <span>Subtotal</span>
                        <span>{formatCurrency((billDetails || selectedBill).subtotal)}</span>
                      </div>
                      <div className="bh-amount-row">
                        <span>Discount</span>
                        <span>-{formatCurrency((billDetails || selectedBill).discount_amount)}</span>
                      </div>
                      <div className="bh-amount-row">
                        <span>Tax</span>
                        <span>{formatCurrency((billDetails || selectedBill).tax_amount)}</span>
                      </div>
                      <div className="bh-amount-row bh-amount-total">
                        <span>Total</span>
                        <span>{formatCurrency((billDetails || selectedBill).final_amount)}</span>
                      </div>
                    </div>
                  </div>
                </>
              )}
            </div>

            {!loadingDetails && (
              <div className="bh-modal-actions">
                <button
                  className="bh-action-btn bh-btn-whatsapp"
                  onClick={handleSendWhatsApp}
                  disabled={sendingWhatsApp || !(billDetails || selectedBill)?.customer_mobile}
                  title={!(billDetails || selectedBill)?.customer_mobile ? 'No mobile number available' : ''}
                >
                  <FaWhatsapp />
                  {sendingWhatsApp ? 'Sending...' : 'Send via WhatsApp'}
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default BillHistory
