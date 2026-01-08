/**
 * Top 10 Customers Component
 * 
 * A reusable React component for displaying top customers in a table format
 * with export functionality and view details buttons.
 * 
 * Features:
 * - Table with columns: #, Mobile, Customer, Count, Revenue, View Details
 * - Export Full Report button
 * - Loading state
 * - Empty state message
 * - Clickable view buttons that open a modal with customer details
 * - Responsive design
 * 
 * Usage:
 * ```jsx
 * import Top10Customers from './Top10Customers'
 * 
 * <Top10Customers 
 *   customers={customersArray}
 *   loading={false}
 *   formatCurrency={(amount) => `₹ ${amount.toLocaleString('en-IN')}`}
 *   onExport={() => handleExport()}
 * />
 * ```
 */

import React, { useState } from 'react'
import { FaTimes } from 'react-icons/fa'
import { apiGet } from '../utils/api'
import './Top10Customers.css'

const Top10Customers = ({ 
  customers = [],
  loading = false,
  formatCurrency = (amount) => `₹ ${amount.toLocaleString('en-IN', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`,
  onExport = () => {
    // Default: Log export action
    console.log('Export Full Report clicked')
  }
}) => {
  const [showModal, setShowModal] = useState(false)
  const [selectedCustomer, setSelectedCustomer] = useState(null)
  const [customerDetails, setCustomerDetails] = useState(null)
  const [loadingDetails, setLoadingDetails] = useState(false)

  const handleViewDetails = async (customer) => {
    setSelectedCustomer(customer)
    setShowModal(true)
    setLoadingDetails(true)
    setCustomerDetails(null)

    try {
      const customerId = customer.customer_id || customer.id
      if (!customerId) {
        console.error('Customer ID not found')
        setLoadingDetails(false)
        return
      }

      const response = await apiGet(`/api/customers/${customerId}`)
      if (response.ok) {
        const data = await response.json()
        setCustomerDetails(data)
      } else {
        console.error('Failed to fetch customer details')
      }
    } catch (error) {
      console.error('Error fetching customer details:', error)
    } finally {
      setLoadingDetails(false)
    }
  }

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A'
    try {
      const date = new Date(dateString)
      return date.toLocaleDateString('en-IN', {
        day: '2-digit',
        month: 'short',
        year: 'numeric'
      })
    } catch (e) {
      return dateString
    }
  }

  return (
    <div className="top-customers-section">
      <div className="section-header">
        <h2 className="section-title">Top 10 Customer</h2>
        <button 
          className="export-link" 
          onClick={(e) => {
            e.preventDefault()
            onExport()
          }}
        >
          Export Full Report
        </button>
      </div>
      
      <div className="table-container">
        <table className="data-table">
          <thead>
            <tr>
              <th className="text-left col-number">#</th>
              <th className="text-left">Mobile</th>
              <th className="text-left">Customer</th>
              <th className="text-left col-count">Count</th>
              <th className="text-left col-revenue">Revenue</th>
              <th className="text-left">View Details</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan="6" className="empty-row">Loading...</td>
              </tr>
            ) : customers.length === 0 ? (
              <tr>
                <td colSpan="6" className="empty-row">No data available</td>
              </tr>
            ) : (
              customers.map((customer, index) => (
                <tr key={customer.customer_id || customer.id || index}>
                  <td className="text-left col-number">{index + 1}</td>
                  <td className="text-left">{customer.mobile || customer.mobile_number || '-'}</td>
                  <td className="text-left">{customer.customer_name || customer.name || '-'}</td>
                  <td className="text-left col-count">{customer.visit_count || customer.count || 0}</td>
                  <td className="text-left col-revenue">
                    {formatCurrency(customer.total_spent || customer.revenue || 0)}
                  </td>
                  <td className="text-left">
                    <button 
                      className="view-link"
                      onClick={() => handleViewDetails(customer)}
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

      {/* Customer Details Modal */}
      {showModal && (
        <div className="customer-modal-overlay" onClick={() => setShowModal(false)}>
          <div className="customer-modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="customer-modal-header">
              <h2>Customer Details</h2>
              <button className="customer-modal-close" onClick={() => setShowModal(false)}>
                <FaTimes />
              </button>
            </div>

            <div className="customer-modal-body">
              {loadingDetails ? (
                <div className="customer-modal-loading">Loading customer details...</div>
              ) : customerDetails ? (
                <>
                  {/* Basic Customer Information */}
                  <div className="customer-details-section">
                    <h3>Customer Information</h3>
                    <div className="customer-details-grid">
                      <div className="customer-detail-item">
                        <span className="detail-label">Name:</span>
                        <span className="detail-value">
                          {customerDetails.firstName} {customerDetails.lastName}
                        </span>
                      </div>
                      <div className="customer-detail-item">
                        <span className="detail-label">Mobile:</span>
                        <span className="detail-value">{customerDetails.mobile || '-'}</span>
                      </div>
                      <div className="customer-detail-item">
                        <span className="detail-label">Email:</span>
                        <span className="detail-value">{customerDetails.email || '-'}</span>
                      </div>
                      <div className="customer-detail-item">
                        <span className="detail-label">Source:</span>
                        <span className="detail-value">{customerDetails.source || '-'}</span>
                      </div>
                    </div>
                  </div>

                  {/* Why They're in Top 10 */}
                  <div className="customer-details-section">
                    <h3>Top 10 Customer Statistics</h3>
                    <div className="customer-stats-grid">
                      <div className="customer-stat-card">
                        <div className="stat-label">Total Revenue</div>
                        <div className="stat-value revenue-stat">
                          {formatCurrency(selectedCustomer?.total_spent || customerDetails?.total_revenue || 0)}
                        </div>
                        <div className="stat-description">Primary reason for Top 10 ranking</div>
                      </div>
                      <div className="customer-stat-card">
                        <div className="stat-label">Visit Count</div>
                        <div className="stat-value">
                          {selectedCustomer?.visit_count || customerDetails?.total_visits || 0}
                        </div>
                        <div className="stat-description">Number of visits</div>
                      </div>
                      <div className="customer-stat-card">
                        <div className="stat-label">Average per Visit</div>
                        <div className="stat-value">
                          {formatCurrency(
                            selectedCustomer?.average_per_visit || 
                            (selectedCustomer?.total_spent && selectedCustomer?.visit_count
                              ? selectedCustomer.total_spent / selectedCustomer.visit_count
                              : customerDetails?.total_revenue && customerDetails?.total_visits
                              ? customerDetails.total_revenue / customerDetails.total_visits
                              : 0)
                          )}
                        </div>
                        <div className="stat-description">Average spending per visit</div>
                      </div>
                    </div>
                  </div>

                  {/* Additional Statistics */}
                  <div className="customer-details-section">
                    <h3>Additional Information</h3>
                    <div className="customer-details-grid">
                      <div className="customer-detail-item">
                        <span className="detail-label">Membership:</span>
                        <span className="detail-value">
                          {customerDetails.membership?.plan?.name || customerDetails.membership?.name || 'No Membership'}
                        </span>
                      </div>
                      <div className="customer-detail-item">
                        <span className="detail-label">Last Visit:</span>
                        <span className="detail-value">
                          {formatDate(customerDetails.last_visit)}
                        </span>
                      </div>
                    </div>
                  </div>
                </>
              ) : (
                <div className="customer-modal-error">Failed to load customer details</div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default Top10Customers

