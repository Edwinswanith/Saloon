import React, { useState, useEffect } from 'react'
import {
  FaArrowLeft,
  FaCloudDownloadAlt,
  FaTimes,
} from 'react-icons/fa'
import './MembershipClients.css'
import { API_BASE_URL } from '../config'
import { apiGet } from '../utils/api'
import { useAuth } from '../contexts/AuthContext'

const MembershipClients = ({ setActivePage }) => {
  const { currentBranch } = useAuth()
  const [searchQuery, setSearchQuery] = useState('')
  const [currentPage, setCurrentPage] = useState(1)
  const [clients, setClients] = useState([])
  const [loading, setLoading] = useState(true)
  const [filteredClients, setFilteredClients] = useState([])
  const [showModal, setShowModal] = useState(false)
  const [selectedClient, setSelectedClient] = useState(null)
  const [customerDetails, setCustomerDetails] = useState(null)
  const [loadingDetails, setLoadingDetails] = useState(false)

  useEffect(() => {
    fetchMembershipClients()
  }, [currentBranch])

  // Listen for branch changes
  useEffect(() => {
    const handleBranchChange = () => {
      console.log('[MembershipClients] Branch changed, refreshing data...')
      fetchMembershipClients()
    }
    
    window.addEventListener('branchChanged', handleBranchChange)
    return () => window.removeEventListener('branchChanged', handleBranchChange)
  }, [currentBranch])

  useEffect(() => {
    if (searchQuery) {
      const filtered = clients.filter(client =>
        client.customer_mobile?.includes(searchQuery) ||
        client.customer_name?.toLowerCase().includes(searchQuery.toLowerCase())
      )
      setFilteredClients(filtered)
    } else {
      setFilteredClients(clients)
    }
  }, [searchQuery, clients])

  const fetchMembershipClients = async () => {
    try {
      setLoading(true)
      const response = await apiGet(`/api/reports/membership-clients?status=active`)
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const data = await response.json()
      
      if (Array.isArray(data)) {
        const formattedClients = data.map((client, index) => ({
          id: index + 1,
          mobile: client.customer_mobile || 'N/A',
          customerName: client.customer_name || 'N/A',
          membershipName: client.membership_name || 'N/A',
          purchaseDate: formatDateTime(client.purchase_date),
          price: client.price || 0,
          discount: client.plan?.allocated_discount || 0,
          expiry: getExpiryText(client.expiry_date, client.days_remaining),
          rawData: client, // Store raw data for modal
        }))
        setClients(formattedClients)
        setFilteredClients(formattedClients)
      } else {
        setClients([])
        setFilteredClients([])
      }
    } catch (error) {
      console.error('Error fetching membership clients:', error)
      setClients([])
      setFilteredClients([])
    } finally {
      setLoading(false)
    }
  }

  const formatDateTime = (dateString) => {
    if (!dateString) return 'N/A'
    const date = new Date(dateString)
    const day = String(date.getDate()).padStart(2, '0')
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const year = date.getFullYear()
    const hours = String(date.getHours()).padStart(2, '0')
    const minutes = String(date.getMinutes()).padStart(2, '0')
    const ampm = hours >= 12 ? 'PM' : 'AM'
    const hour12 = hours % 12 || 12
    return `${day}-${month}-${year} ${hour12}:${minutes} ${ampm}`
  }

  const getExpiryText = (expiryDate, daysRemaining) => {
    if (!expiryDate) return 'N/A'
    const expiry = new Date(expiryDate)
    const now = new Date()
    if (expiry < now) {
      return 'Expired'
    }
    return daysRemaining !== undefined ? `${daysRemaining} days left` : `${Math.ceil((expiry - now) / (1000 * 60 * 60 * 24))} days left`
  }

  const handleBackToReports = () => {
    if (setActivePage) {
      setActivePage('reports')
    }
  }

  const itemsPerPage = 10
  const totalPages = Math.ceil(filteredClients.length / itemsPerPage)
  const startIndex = (currentPage - 1) * itemsPerPage
  const endIndex = startIndex + itemsPerPage
  const paginatedClients = filteredClients.slice(startIndex, endIndex)

  const handlePageChange = (page) => {
    if (page >= 1 && page <= totalPages) {
      setCurrentPage(page)
    }
  }

  const handleViewDetails = async (client) => {
    setSelectedClient(client)
    setShowModal(true)
    setLoadingDetails(true)
    setCustomerDetails(null)

    try {
      const mobile = client.mobile
      if (!mobile || mobile === 'N/A') {
        console.error('Customer mobile not found')
        setLoadingDetails(false)
        return
      }

      // Fetch customer by mobile using search parameter
      const customersResponse = await apiGet(`/api/customers?search=${mobile}`)
      if (customersResponse.ok) {
        const customersData = await customersResponse.json()
        const customersList = customersData.customers || customersData
        if (Array.isArray(customersList) && customersList.length > 0) {
          // Find exact mobile match
          const customer = customersList.find(c => c.mobile === mobile) || customersList[0]
          const customerId = customer.id || customer._id
          
          // Fetch detailed customer information
          const detailsResponse = await apiGet(`/api/customers/${customerId}`)
          if (detailsResponse.ok) {
            const details = await detailsResponse.json()
            setCustomerDetails(details)
          } else {
            // Fallback: use basic customer data
            setCustomerDetails(customer)
          }
        } else {
          // No customer found, show membership data only
          setCustomerDetails(null)
        }
      } else {
        console.error('Failed to fetch customer by mobile')
      }
    } catch (error) {
      console.error('Error fetching customer details:', error)
    } finally {
      setLoadingDetails(false)
    }
  }

  const formatCurrency = (amount) => {
    return `₹${amount?.toLocaleString('en-IN', { minimumFractionDigits: 0, maximumFractionDigits: 0 }) || 0}`
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
      return 'N/A'
    }
  }

  return (
    <div className="membership-clients-page">
      <div className="membership-clients-container">
        {/* Main Report Card */}
        <div className="report-card">
          {/* Back Button */}
          <button className="back-button" onClick={handleBackToReports}>
            <FaArrowLeft />
            Back to Reports Hub
          </button>

          {/* Search and Download */}
          <div className="search-download-section">
            <div className="search-wrapper">
              <input
                type="text"
                className="search-input"
                placeholder="Search by Phone Number..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
            <button 
              className="download-report-btn"
              onClick={() => {
                const csvContent = [
                  ['Mobile', 'Customer Name', 'Membership Name', 'Purchase Date', 'Price', 'Discount', 'Expiry'],
                  ...filteredClients.map(client => [
                    client.mobile,
                    client.customerName,
                    client.membershipName,
                    client.purchaseDate,
                    client.price,
                    `${client.discount}%`,
                    client.expiry,
                  ])
                ].map(row => row.join(',')).join('\n')
                
                const blob = new Blob([csvContent], { type: 'text/csv' })
                const url = window.URL.createObjectURL(blob)
                const a = document.createElement('a')
                a.href = url
                a.download = `membership-clients-${new Date().toISOString().split('T')[0]}.csv`
                a.click()
                window.URL.revokeObjectURL(url)
              }}
            >
              <FaCloudDownloadAlt />
              Download Report
            </button>
          </div>

          {/* Clients Table */}
          <div className="table-container">
            <table className="clients-table">
              <thead>
                <tr>
                  <th>Mobile</th>
                  <th>Customer Name</th>
                  <th>Membership Name</th>
                  <th>Purchase Date</th>
                  <th>Price</th>
                  <th>Discount</th>
                  <th>Expiry</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan="8" className="empty-message">Loading...</td>
                  </tr>
                ) : paginatedClients.length === 0 ? (
                  <tr>
                    <td colSpan="8" className="empty-message">No membership clients found.</td>
                  </tr>
                ) : (
                  paginatedClients.map((client) => (
                    <tr key={client.id}>
                      <td>{client.mobile}</td>
                      <td>{client.customerName}</td>
                      <td>{client.membershipName}</td>
                      <td>{client.purchaseDate}</td>
                      <td>₹{client.price.toLocaleString()}</td>
                      <td>{client.discount}%</td>
                      <td
                        className={
                          client.expiry === 'Expired' ? 'expired-status' : ''
                        }
                      >
                        {client.expiry}
                      </td>
                      <td>
                        <button 
                          className="view-btn"
                          onClick={() => handleViewDetails(client)}
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

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="pagination">
              <button 
                className="page-btn" 
                onClick={() => handlePageChange(1)}
                disabled={currentPage === 1}
              >
                First
              </button>
              <button 
                className="page-btn" 
                onClick={() => handlePageChange(currentPage - 1)}
                disabled={currentPage === 1}
              >
                Previous
              </button>
              {Array.from({ length: totalPages }, (_, i) => i + 1).map(page => (
                <button
                  key={page}
                  className={`page-btn ${currentPage === page ? 'active' : ''}`}
                  onClick={() => handlePageChange(page)}
                >
                  {page}
                </button>
              ))}
              <button 
                className="page-btn" 
                onClick={() => handlePageChange(currentPage + 1)}
                disabled={currentPage === totalPages}
              >
                Next
              </button>
              <button 
                className="page-btn" 
                onClick={() => handlePageChange(totalPages)}
                disabled={currentPage === totalPages}
              >
                Last
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Membership Details Modal */}
      {showModal && (
        <div className="customer-modal-overlay" onClick={() => setShowModal(false)}>
          <div className="customer-modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="customer-modal-header">
              <h2>Membership Details</h2>
              <button className="customer-modal-close" onClick={() => setShowModal(false)}>
                <FaTimes />
              </button>
            </div>

            <div className="customer-modal-body">
              {loadingDetails ? (
                <div className="customer-modal-loading">Loading membership details...</div>
              ) : (
                <>
                  {/* Customer Information */}
                  {customerDetails && (
                    <div className="customer-details-section">
                      <h3>Customer Information</h3>
                      <div className="customer-details-grid">
                        <div className="customer-detail-item">
                          <span className="detail-label">Name:</span>
                          <span className="detail-value">
                            {customerDetails.firstName && customerDetails.lastName
                              ? `${customerDetails.firstName} ${customerDetails.lastName}`
                              : selectedClient?.customerName || 'N/A'}
                          </span>
                        </div>
                        <div className="customer-detail-item">
                          <span className="detail-label">Mobile:</span>
                          <span className="detail-value">{selectedClient?.mobile || 'N/A'}</span>
                        </div>
                        {customerDetails.email && (
                          <div className="customer-detail-item">
                            <span className="detail-label">Email:</span>
                            <span className="detail-value">{customerDetails.email || '-'}</span>
                          </div>
                        )}
                        {customerDetails.source && (
                          <div className="customer-detail-item">
                            <span className="detail-label">Source:</span>
                            <span className="detail-value">{customerDetails.source || '-'}</span>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Membership Information */}
                  <div className="customer-details-section">
                    <h3>Membership Information</h3>
                    <div className="customer-details-grid">
                      <div className="customer-detail-item">
                        <span className="detail-label">Membership Name:</span>
                        <span className="detail-value">{selectedClient?.membershipName || 'N/A'}</span>
                      </div>
                      <div className="customer-detail-item">
                        <span className="detail-label">Purchase Date:</span>
                        <span className="detail-value">{selectedClient?.purchaseDate || 'N/A'}</span>
                      </div>
                      <div className="customer-detail-item">
                        <span className="detail-label">Price:</span>
                        <span className="detail-value">{formatCurrency(selectedClient?.price || 0)}</span>
                      </div>
                      <div className="customer-detail-item">
                        <span className="detail-label">Discount:</span>
                        <span className="detail-value">{selectedClient?.discount || 0}%</span>
                      </div>
                      <div className="customer-detail-item">
                        <span className="detail-label">Expiry:</span>
                        <span className={`detail-value ${selectedClient?.expiry === 'Expired' ? 'expired-status' : ''}`}>
                          {selectedClient?.expiry || 'N/A'}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Customer Statistics */}
                  {customerDetails && (customerDetails.total_visits || customerDetails.total_revenue) && (
                    <div className="customer-details-section">
                      <h3>Customer Statistics</h3>
                      <div className="customer-stats-grid">
                        {customerDetails.total_revenue !== undefined && (
                          <div className="customer-stat-card">
                            <div className="stat-label">Total Revenue</div>
                            <div className="stat-value revenue-stat">
                              {formatCurrency(customerDetails.total_revenue)}
                            </div>
                            <div className="stat-description">Total spending</div>
                          </div>
                        )}
                        {customerDetails.total_visits !== undefined && (
                          <div className="customer-stat-card">
                            <div className="stat-label">Total Visits</div>
                            <div className="stat-value">
                              {customerDetails.total_visits || 0}
                            </div>
                            <div className="stat-description">Number of visits</div>
                          </div>
                        )}
                        {customerDetails.last_visit && (
                          <div className="customer-stat-card">
                            <div className="stat-label">Last Visit</div>
                            <div className="stat-value">
                              {formatDate(customerDetails.last_visit)}
                            </div>
                            <div className="stat-description">Most recent visit</div>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Membership Details from Customer */}
                  {customerDetails?.membership && (
                    <div className="customer-details-section">
                      <h3>Active Membership</h3>
                      <div className="customer-details-grid">
                        {customerDetails.membership.plan?.name && (
                          <div className="customer-detail-item">
                            <span className="detail-label">Plan:</span>
                            <span className="detail-value">{customerDetails.membership.plan.name}</span>
                          </div>
                        )}
                        {customerDetails.membership.purchase_date && (
                          <div className="customer-detail-item">
                            <span className="detail-label">Purchase Date:</span>
                            <span className="detail-value">{formatDate(customerDetails.membership.purchase_date)}</span>
                          </div>
                        )}
                        {customerDetails.membership.expiry_date && (
                          <div className="customer-detail-item">
                            <span className="detail-label">Expiry Date:</span>
                            <span className="detail-value">{formatDate(customerDetails.membership.expiry_date)}</span>
                          </div>
                        )}
                        {customerDetails.membership.plan?.allocated_discount !== undefined && (
                          <div className="customer-detail-item">
                            <span className="detail-label">Discount:</span>
                            <span className="detail-value">{customerDetails.membership.plan.allocated_discount}%</span>
                          </div>
                        )}
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

export default MembershipClients

