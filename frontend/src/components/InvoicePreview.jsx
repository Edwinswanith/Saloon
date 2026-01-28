import React, { useState, useEffect, useRef } from 'react'
import { FaWhatsapp } from 'react-icons/fa'
import { apiGet } from '../utils/api'
import './InvoicePreview.css'

// Branch information mapping
const BRANCH_INFO = {
  'Main Road': {
    address: [
      '55, Duraisamy Complex,',
      'Manapakkam Main Road,',
      'Chennai – 600125'
    ],
    phone: '044-22520395, 044-66126131'
  },
  'EB': {
    address: [
      '3/238-A, Usha Complex,',
      'Manapakkam,',
      'Chennai – 600125'
    ],
    phone: '044-22521064, 044-43531642'
  },
  'Madanandapuram': {
    address: [
      '6A, Madha Nagar Main Road,',
      'Rajeshwari Avenue,',
      'Near Pon Vidhyashram School, Chennai'
    ],
    phone: '044-48645868'
  },
  'Kolapakkam': {
    address: [
      '67, Near Little Flower School,',
      'PT Nagar, Chennai'
    ],
    phone: '044-49504722'
  },
  'Kovur': {
    address: [
      '1/150, Kundrathur Main Road,',
      'Near Maadha Medical College,',
      'Kovur, Chennai – 600128'
    ],
    phone: '9500186074'
  },
  'DLF': {
    address: [
      '2/914, Krishnaveni Nagar,',
      'Near DLF Back Gate,',
      'Mugalivakkam, Chennai – 600116'
    ],
    phone: '044-48543022, 9840192264'
  }
}

const InvoicePreview = ({ invoiceData, billId, onDownload, onReview }) => {
  const [htmlContent, setHtmlContent] = useState('')
  const [loading, setLoading] = useState(false)
  const [useServerHtml, setUseServerHtml] = useState(false)
  const containerRef = useRef(null)

  // Try to fetch server-rendered HTML if billId is provided
  useEffect(() => {
    if (billId && !invoiceData) {
      setLoading(true)
      apiGet(`/api/bills/${billId}/invoice/html`)
        .then(response => {
          if (typeof response === 'string') {
            setHtmlContent(response)
            setUseServerHtml(true)
          }
        })
        .catch(err => {
          console.error('Failed to fetch invoice HTML:', err)
          setUseServerHtml(false)
        })
        .finally(() => {
          setLoading(false)
        })
    }
  }, [billId, invoiceData])

  // Fallback: if no billId but invoiceData provided, use client-side rendering
  if (!billId && !invoiceData) {
    return <div className="invoice-loading">Loading invoice data...</div>
  }

  if (loading) {
    return <div className="invoice-loading">Loading invoice...</div>
  }

  // Set up action handlers for server-rendered HTML
  useEffect(() => {
    if (useServerHtml && htmlContent) {
      window.invoiceActions = {
        review: onReview || (() => {}),
        download: onDownload || (() => {}),
        whatsapp: () => {
          if (invoiceData?.customer?.mobile) {
            const phoneNumber = invoiceData.customer.mobile.replace(/[^0-9]/g, '')
            const whatsappUrl = `https://wa.me/${phoneNumber.startsWith('91') ? phoneNumber : '91' + phoneNumber}`
            window.open(whatsappUrl, '_blank')
          }
        }
      }
      return () => {
        delete window.invoiceActions
      }
    }
  }, [useServerHtml, htmlContent, onReview, onDownload, invoiceData])

  // If we have server-rendered HTML, use it
  if (useServerHtml && htmlContent) {
    return (
      <div
        ref={containerRef}
        className="invoice-preview-wrapper"
        dangerouslySetInnerHTML={{ __html: htmlContent }}
      />
    )
  }

  // Client-side fallback rendering (original implementation)
  if (!invoiceData) {
    return <div className="invoice-loading">Loading invoice data...</div>
  }

  const { invoice_number, customer, branch, items, summary, payment, booking_date, booking_time } = invoiceData

  // Get branch information from mapping
  const getBranchInfo = () => {
    if (!branch?.name) return null
    // Case-insensitive lookup
    const branchName = branch.name.trim()
    const branchKey = Object.keys(BRANCH_INFO).find(
      key => key.toLowerCase() === branchName.toLowerCase()
    )
    return branchKey ? BRANCH_INFO[branchKey] : null
  }

  const branchInfo = getBranchInfo()

  const formatCurrency = (amount) => {
    return `₹${parseFloat(amount || 0).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
  }

  const formatCurrencyNoDecimals = (amount) => {
    return `₹${parseFloat(amount || 0).toLocaleString('en-IN', { maximumFractionDigits: 0 })}`
  }

  const formatMobileNumber = (mobile) => {
    if (!mobile) return ''
    let formatted = mobile.trim()
    if (formatted.startsWith('+91')) {
      if (!formatted.startsWith('+91 ')) {
        formatted = '+91 ' + formatted.substring(3).trim()
      }
    } else if (formatted.startsWith('91')) {
      formatted = '+91 ' + formatted.substring(2).trim()
    } else if (!formatted.startsWith('+')) {
      formatted = '+91 ' + formatted
    }
    return formatted
  }

  const formatBookingDateTime = (dateStr, timeStr) => {
    if (!dateStr || !timeStr || dateStr === 'N/A' || timeStr === 'N/A') {
      return 'N/A'
    }
    if (dateStr.includes(',') && timeStr.includes(' ')) {
      return `${dateStr}, ${timeStr}`
    }
    try {
      const date = new Date(dateStr)
      if (isNaN(date.getTime())) {
        return `${dateStr}, ${timeStr}`
      }
      const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
      const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
      const day = dayNames[date.getDay()]
      const dayNum = String(date.getDate()).padStart(2, '0')
      const month = monthNames[date.getMonth()]
      const year = date.getFullYear()

      let formattedTime = timeStr
      if (timeStr.match(/^\d{1,2}:\d{2}$/)) {
        const [hours, minutes] = timeStr.split(':')
        const hour24 = parseInt(hours)
        const hour12 = hour24 % 12 || 12
        const ampm = hour24 >= 12 ? 'pm' : 'am'
        formattedTime = `${String(hour12).padStart(2, '0')}:${minutes} ${ampm}`
      }

      return `${day}, ${dayNum} ${month}, ${year}, ${formattedTime}`
    } catch (e) {
      return `${dateStr}, ${timeStr}`
    }
  }

  const handleSendWhatsApp = () => {
    if (!customer?.mobile) return

    let phoneNumber = customer.mobile.replace(/[^0-9]/g, '')
    if (phoneNumber.startsWith('91') && phoneNumber.length > 10) {
      phoneNumber = phoneNumber
    } else if (phoneNumber.length === 10) {
      phoneNumber = '91' + phoneNumber
    }

    const formattedDateTime = formatBookingDateTime(booking_date, booking_time)

    let message = `*Bill Details*\n\n`
    message += `Bill Number: ${invoice_number || 'N/A'}\n`
    message += `Date: ${formattedDateTime}\n\n`

    message += `*Items:*\n`
    if (items && items.length > 0) {
      items.forEach(item => {
        message += `${item.name || 'Item'} - Qty: ${item.quantity || 1} - ${formatCurrency(item.total || 0)}\n`
      })
    }
    message += `\n`

    message += `*Summary:*\n`
    message += `Subtotal: ${formatCurrency(summary?.subtotal || 0)}\n`
    if (summary?.discount > 0) {
      message += `Discount: ${formatCurrency(summary.discount)}\n`
    }
    message += `Tax: ${formatCurrency(summary?.tax || 0)}\n`
    message += `*Total: ${formatCurrencyNoDecimals(summary?.total || 0)}*\n\n`

    message += `Payment Mode: ${payment?.source || 'N/A'}\n\n`

    message += `Thank you for your visit!\n`
    message += `${branch?.name || 'SaloonBoost'}`

    const whatsappUrl = `https://wa.me/${phoneNumber}?text=${encodeURIComponent(message)}`
    window.open(whatsappUrl, '_blank')
  }

  return (
    <div className="invoice-preview-container">
      {/* Header Section - Center-Aligned */}
      <div className="invoice-header-section">
        <h1 className="company-name">Priyanka Nature Cure</h1>
        {branchInfo?.address && branchInfo.address.map((line, index) => (
          <p key={index} className="company-address">{line}</p>
        ))}
        {branch?.gstin && (
          <p className="company-gst">GST: GSTIN {branch.gstin}</p>
        )}
        {branchInfo?.phone && (
          <p className="company-phone">Call us for appointment: {branchInfo.phone}</p>
        )}
      </div>

      {/* Customer Meta Section - 2 Columns */}
      <div className="invoice-customer-meta">
        <div className="customer-meta-left">
          <p className="billed-to"><strong>Billed to</strong> {customer?.name || 'Customer'}</p>
          {customer?.mobile && (
            <p className="customer-mobile">
              <strong>Mobile:</strong> <a href={`tel:${customer.mobile}`} className="customer-mobile-link">
                {formatMobileNumber(customer.mobile)}
              </a>
            </p>
          )}
        </div>
        <div className="customer-meta-right">
          <p className="invoice-number">Invoice Number: {invoice_number || 'N/A'}</p>
          <p className="wallet-balance">Wallet Balance: {formatCurrency(customer?.wallet_balance || 0)}</p>
        </div>
      </div>

      {/* Booking Strip */}
      <div className="invoice-booking-strip">
        <span className="booking-label">Booking at</span>
        <span className="booking-datetime">{formatBookingDateTime(booking_date, booking_time)}</span>
      </div>

      {/* Payment Strip */}
      <div className="invoice-payment-strip">
        <div className="payment-row">
          <span className="payment-status-label">Payment Status</span>
          <span className="payment-status-value">{payment?.status || 'pending'}</span>
        </div>
        <div className="payment-row">
          <span className="payment-source-label">Payment Source</span>
          <span className="payment-source-value">
            {(() => {
              const paymentMode = payment?.mode || (payment?.source?.split(':')[0]) || '';
              const paymentAmount = payment?.amount || summary?.total || 0;

              if (!paymentMode) return 'Not paid';

              const formattedMode = paymentMode.charAt(0).toUpperCase() + paymentMode.slice(1).toLowerCase();
              return `${formattedMode}: ${formatCurrencyNoDecimals(paymentAmount)}`;
            })()}
          </span>
        </div>
      </div>

      {/* Items Grid - 8 Columns */}
      <div className="invoice-items-grid">
        <div className="items-grid-header">
          <div className="grid-col-item">Item</div>
          <div className="grid-col-staff">Staff Name</div>
          <div className="grid-col-type">Type</div>
          <div className="grid-col-qty">Qty</div>
          <div className="grid-col-price">Price</div>
          <div className="grid-col-tax">Tax</div>
          <div className="grid-col-discount">Discount</div>
          <div className="grid-col-amt">Amt</div>
        </div>
        {items && items.length > 0 ? (
          items.map((item, index) => (
            <div key={index} className="items-grid-row">
              <div className="grid-col-item">{item.name || 'Item'}</div>
              <div className="grid-col-staff">{item.staff_name || 'N/A'}</div>
              <div className="grid-col-type">{item.type ? item.type.charAt(0).toUpperCase() + item.type.slice(1) : 'Service'}</div>
              <div className="grid-col-qty">{item.quantity || 1}</div>
              <div className="grid-col-price">{formatCurrency(item.price || 0)}</div>
              <div className="grid-col-tax">{formatCurrency(item.tax || 0)}</div>
              <div className="grid-col-discount">{formatCurrency(item.discount || 0)}</div>
              <div className="grid-col-amt">{formatCurrency(item.total || 0)}</div>
            </div>
          ))
        ) : (
          <div className="items-grid-row no-items">
            <div className="grid-col-item">No items found</div>
          </div>
        )}
      </div>

      {/* Summary Section - Right-Aligned Stack */}
      <div className="invoice-summary-section">
        <div className="summary-row">
          <span className="summary-label">Subtotal</span>
          <span className="summary-value">{formatCurrency(summary?.subtotal || 0)}</span>
        </div>
        <div className="summary-row">
          <span className="summary-label">Discount</span>
          <span className="summary-value">{formatCurrency(summary?.discount || 0)}</span>
        </div>
        <div className="summary-row">
          <span className="summary-label">Net</span>
          <span className="summary-value">{formatCurrency(summary?.net || 0)}</span>
        </div>
        <div className="summary-row">
          <span className="summary-label">Tax</span>
          <span className="summary-value">{formatCurrency(summary?.tax || 0)}</span>
        </div>
        <div className="summary-row summary-total">
          <span className="summary-label">Total</span>
          <span className="summary-value">{formatCurrencyNoDecimals(summary?.total || 0)}</span>
        </div>
      </div>

      {/* Contact Footer Section */}
      <div className="invoice-contact-footer">
        <p className="contact-enquiry">For Enquiry Contact – Geethalakshmi: <a href="tel:+919840192264" className="contact-link">+91 9840192264</a></p>
        <p className="contact-website"><a href="https://www.priyankanaturecure.com" target="_blank" rel="noopener noreferrer" className="contact-link">www.priyankanaturecure.com</a></p>
        <p className="contact-email"><strong>Email –</strong> <a href="mailto:priyankanaturecure@gmail.com" className="contact-link">priyankanaturecure@gmail.com</a></p>
      </div>

      {/* Footer Buttons */}
      <div className="invoice-actions-section">
        {onReview && (
          <button className="invoice-action-btn review-btn" onClick={onReview}>
            Review Us
          </button>
        )}
        {customer?.mobile && (
          <button className="invoice-action-btn whatsapp-btn" onClick={handleSendWhatsApp}>
            <FaWhatsapp /> Send via WhatsApp
          </button>
        )}
        {onDownload && (
          <button className="invoice-action-btn download-btn" onClick={onDownload}>
            Download Invoice
          </button>
        )}
      </div>
    </div>
  )
}

export default InvoicePreview
