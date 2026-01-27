import React from 'react'
import { FaWhatsapp } from 'react-icons/fa'
import './InvoicePreview.css'

const InvoicePreview = ({ invoiceData, onDownload, onReview }) => {
  if (!invoiceData) {
    return <div className="invoice-loading">Loading invoice data...</div>
  }

  const { invoice_number, customer, branch, items, summary, payment, booking_date, booking_time } = invoiceData

  const formatCurrency = (amount) => {
    return `₹${parseFloat(amount || 0).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
  }

  const formatCurrencyNoDecimals = (amount) => {
    return `₹${parseFloat(amount || 0).toLocaleString('en-IN', { maximumFractionDigits: 0 })}`
  }

  const formatMobileNumber = (mobile) => {
    if (!mobile) return ''
    // Ensure format is +91 [number] with space
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
    // If already formatted, return as is
    if (dateStr.includes(',') && timeStr.includes(' ')) {
      return `${dateStr}, ${timeStr}`
    }
    // Otherwise try to parse and format
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
      
      // Format time (assuming timeStr is in HH:MM format or already formatted)
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

    // Format mobile number - remove +91, spaces, and non-digits, then add 91 prefix
    let phoneNumber = customer.mobile.replace(/[^0-9]/g, '')
    if (phoneNumber.startsWith('91') && phoneNumber.length > 10) {
      phoneNumber = phoneNumber // Already has country code
    } else if (phoneNumber.length === 10) {
      phoneNumber = '91' + phoneNumber
    }

    // Build the message
    const formattedDateTime = formatBookingDateTime(booking_date, booking_time)

    let message = `*Bill Details*\n\n`
    message += `Bill Number: ${invoice_number || 'N/A'}\n`
    message += `Date: ${formattedDateTime}\n\n`

    // Items
    message += `*Items:*\n`
    if (items && items.length > 0) {
      items.forEach(item => {
        message += `${item.name || 'Item'} - Qty: ${item.quantity || 1} - ${formatCurrency(item.total || 0)}\n`
      })
    }
    message += `\n`

    // Summary
    message += `*Summary:*\n`
    message += `Subtotal: ${formatCurrency(summary?.subtotal || 0)}\n`
    if (summary?.discount > 0) {
      message += `Discount: ${formatCurrency(summary.discount)}\n`
    }
    message += `Tax: ${formatCurrency(summary?.tax || 0)}\n`
    message += `*Total: ${formatCurrencyNoDecimals(summary?.total || 0)}*\n\n`

    // Payment
    message += `Payment Mode: ${payment?.source || 'N/A'}\n\n`

    // Footer
    message += `Thank you for your visit!\n`
    message += `${branch?.name || 'SaloonBoost'}`

    // Create WhatsApp URL and open
    const whatsappUrl = `https://wa.me/${phoneNumber}?text=${encodeURIComponent(message)}`
    window.open(whatsappUrl, '_blank')
  }

  return (
    <div className="invoice-preview-container">
      {/* Company Header */}
      <div className="invoice-header-section">
        <div className="company-info">
          <h1 className="company-name">{branch?.name || 'SaloonBoost Demo Account'}</h1>
          {branch?.address && (
            <p className="company-address">{branch.address}{branch.city ? `, ${branch.city}` : ''}</p>
          )}
          {branch?.gstin && (
            <p className="company-gst">GST: GSTIN {branch.gstin}</p>
          )}
          {branch?.phone && (
            <p className="company-phone">Call us for appointment: {branch.phone}</p>
          )}
        </div>
        
        <div className="invoice-meta">
          <p className="invoice-number">Invoice Number: {invoice_number || 'N/A'}</p>
          <p className="wallet-balance">Wallet Balance: {formatCurrency(customer?.wallet_balance || 0)}</p>
          <p className="loyalty-balance">Loyalty Balance: ₹{parseInt(customer?.loyalty_points || 0).toLocaleString('en-IN')}</p>
        </div>
      </div>

      {/* Customer Information */}
      <div className="invoice-customer-section">
        <h3 className="billed-to">Billed to {customer?.name || 'Customer'}</h3>
        {customer?.mobile && (
          <p className="customer-mobile">Mobile: {formatMobileNumber(customer.mobile)}</p>
        )}
        <p className="booking-info">Booking at {formatBookingDateTime(booking_date, booking_time)}</p>
      </div>

      {/* Payment Status */}
      <div className="invoice-payment-section">
        <p className="payment-info">
          <span className="payment-status"><strong>Payment Status:</strong> {payment?.status || 'pending'}</span>
          {payment?.source && (
            <span className="payment-source"><strong>Payment Source:</strong> {payment.source}</span>
          )}
        </p>
      </div>

      {/* Items Table */}
      <div className="invoice-table-wrapper">
        <table className="invoice-items-table">
          <thead>
            <tr>
              <th>Item</th>
              <th>Staff Name</th>
              <th>Type</th>
              <th>Qty</th>
              <th>Price</th>
              <th>Tax</th>
              <th>Discount</th>
              <th>Amt</th>
            </tr>
          </thead>
          <tbody>
            {items && items.length > 0 ? (
              items.map((item, index) => (
                <tr key={index}>
                  <td>{item.name || 'Item'}</td>
                  <td>{item.staff_name || 'N/A'}</td>
                  <td>{item.type ? item.type.charAt(0).toUpperCase() + item.type.slice(1) : 'Service'}</td>
                  <td>{item.quantity || 1}</td>
                  <td>{formatCurrency(item.price || 0)}</td>
                  <td>{formatCurrency(item.tax || 0)}</td>
                  <td>{formatCurrency(item.discount || 0)}</td>
                  <td>{formatCurrency(item.total || 0)}</td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan="8" className="no-items">No items found</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Bill Summary */}
      <div className="invoice-summary-section">
        <div className="summary-row">
          <span className="summary-label">Subtotal:</span>
          <span className="summary-value">{formatCurrency(summary?.subtotal || 0)}</span>
        </div>
        <div className="summary-row">
          <span className="summary-label">Discount:</span>
          <span className="summary-value">{formatCurrency(summary?.discount || 0)}</span>
        </div>
        <div className="summary-row">
        </div>
        <div className="summary-row">
          <span className="summary-label">Net:</span>
          <span className="summary-value">{formatCurrency(summary?.net || 0)}</span>
        </div>
        <div className="summary-row">
          <span className="summary-label">Tax:</span>
          <span className="summary-value">{formatCurrency(summary?.tax || 0)}</span>
        </div>
        <div className="summary-row final-row">
          <span className="summary-label">Total:</span>
          <span className="summary-value">{formatCurrencyNoDecimals(summary?.total || 0)}</span>
        </div>
      </div>

      {/* Action Buttons */}
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

      {/* Footer */}
      <div className="invoice-footer">
        <p className="footer-text">{branch?.name || 'SaloonBoost Demo Account'}</p>
      </div>
    </div>
  )
}

export default InvoicePreview

