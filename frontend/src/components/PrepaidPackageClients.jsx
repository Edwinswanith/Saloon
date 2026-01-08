import React, { useState, useEffect } from 'react'
import {
  FaArrowLeft,
  FaCloudDownloadAlt,
  FaTimes,
} from 'react-icons/fa'
import './PrepaidPackageClients.css'
import { apiGet } from '../utils/api'
import { API_BASE_URL } from '../config'
import { useAuth } from '../contexts/AuthContext'

const PrepaidPackageClients = ({ setActivePage }) => {
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
    fetchPrepaidClients()
  }, [currentBranch])

  // Listen for branch changes
  useEffect(() => {
    const handleBranchChange = () => {
      console.log('[PrepaidPackageClients] Branch changed, refreshing data...')
      fetchPrepaidClients()
    }
    
    window.addEventListener('branchChanged', handleBranchChange)
    return () => window.removeEventListener('branchChanged', handleBranchChange)
  }, [currentBranch])

  useEffect(() => {
    if (searchQuery) {
      const filtered = clients.filter(client =>
        client.phone?.includes(searchQuery) ||
        client.customerName?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        client.invoice?.includes(searchQuery)
      )
      setFilteredClients(filtered)
    } else {
      setFilteredClients(clients)
    }
  }, [searchQuery, clients])

  const fetchPrepaidClients = async () => {
    try {
      setLoading(true)
      const response = await apiGet(`/api/reports/prepaid-clients?status=active`)
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const data = await response.json()
      
      if (Array.isArray(data)) {
        const formattedClients = data.map((client, index) => ({
          id: index + 1,
          invoice: `INV-${String(index + 1).padStart(6, '0')}`, // Generate invoice number
          date: formatDate(client.purchase_date),
          customerName: client.customer_name || 'N/A',
          phone: client.customer_mobile || 'N/A',
          package: client.package_name || 'N/A',
          soldBy: 'N/A', // Not available in current model
          mode: 'N/A', // Not available in current model
          paid: client.price || 0,
          balance: client.remaining_balance || 0,
          expiry: getExpiryText(client.expiry_date),
          rawData: client, // Store raw data for modal
        }))
        setClients(formattedClients)
        setFilteredClients(formattedClients)
      } else {
        setClients([])
        setFilteredClients([])
      }
    } catch (error) {
      console.error('Error fetching prepaid clients:', error)
      setClients([])
      setFilteredClients([])
    } finally {
      setLoading(false)
    }
  }

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A'
    const date = new Date(dateString)
    const day = String(date.getDate()).padStart(2, '0')
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const year = date.getFullYear()
    return `${day}-${month}-${year}`
  }

  const getExpiryText = (expiryDate) => {
    if (!expiryDate) return 'N/A'
    const expiry = new Date(expiryDate)
    const now = new Date()
    if (expiry < now) {
      return 'Expired'
    }
    const daysLeft = Math.ceil((expiry - now) / (1000 * 60 * 60 * 24))
    return `${daysLeft} days left`
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
      const phone = client.phone
      if (!phone || phone === 'N/A') {
        console.error('Customer phone not found')
        setLoadingDetails(false)
        return
      }

      // Fetch customer by mobile using search parameter
      const customersResponse = await apiGet(`/api/customers?search=${phone}`)
      if (customersResponse.ok) {
        const customersData = await customersResponse.json()
        const customersList = customersData.customers || customersData
        if (Array.isArray(customersList) && customersList.length > 0) {
          // Find exact mobile match
          const customer = customersList.find(c => c.mobile === phone) || customersList[0]
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
          // No customer found, show package data only
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

  const formatDateForModal = (dateString) => {
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
    <div className="prepaid-package-clients-page">
      <div className="prepaid-package-clients-container">
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
                  ['Invoice', 'Date', 'Customer', 'Phone', 'Package', 'Paid', 'Balance', 'Expiry'],
                  ...filteredClients.map(client => [
                    client.invoice,
                    client.date,
                    client.customerName,
                    client.phone,
                    client.package,
                    client.paid,
                    client.balance,
                    client.expiry,
                  ])
                ].map(row => row.join(',')).join('\n')
                
                const blob = new Blob([csvContent], { type: 'text/csv' })
                const url = window.URL.createObjectURL(blob)
                const a = document.createElement('a')
                a.href = url
                a.download = `prepaid-clients-${new Date().toISOString().split('T')[0]}.csv`
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
                  <th>Invoice</th>
                  <th>Date</th>
                  <th>Customer</th>
                  <th>Package</th>
                  <th>Sold By</th>
                  <th>Mode</th>
                  <th>Paid</th>
                  <th>Balance</th>
                  <th>Expiry</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan="10" className="empty-message">Loading...</td>
                  </tr>
                ) : paginatedClients.length === 0 ? (
                  <tr>
                    <td colSpan="10" className="empty-message">No prepaid package clients found.</td>
                  </tr>
                ) : (
                  paginatedClients.map((client) => (
                    <tr key={client.id}>
                      <td>{client.invoice}</td>
                      <td>{client.date}</td>
                      <td>
                        <div className="customer-info">
                          <div className="customer-name">{client.customerName}</div>
                          <div className="customer-phone">{client.phone}</div>
                        </div>
                      </td>
                      <td>{client.package}</td>
                      <td>{client.soldBy}</td>
                      <td>{client.mode}</td>
                      <td>₹{client.paid.toLocaleString()}</td>
                      <td className="balance-cell">
                        <strong>₹{client.balance.toLocaleString()}</strong>
                      </td>
                      <td>{client.expiry}</td>
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

      {/* Prepaid Package Details Modal */}
      {showModal && selectedClient && (
        <div className="customer-modal-overlay" onClick={() => setShowModal(false)}>
          <div className="customer-modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="customer-modal-header">
              <h2>Prepaid Package Details</h2>
              <button className="customer-modal-close" onClick={() => setShowModal(false)}>
                <FaTimes />
              </button>
            </div>

            <div className="customer-modal-body">
              {loadingDetails ? (
                <div className="customer-modal-loading">Loading package details...</div>
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
                          <span className="detail-label">Phone:</span>
                          <span className="detail-value">{selectedClient?.phone || 'N/A'}</span>
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

                  {/* Package Information */}
                  <div className="customer-details-section">
                    <h3>Package Information</h3>
                    <div className="customer-details-grid">
                      <div className="customer-detail-item">
                        <span className="detail-label">Package Name:</span>
                        <span className="detail-value">{selectedClient?.package || 'N/A'}</span>
                      </div>
                      <div className="customer-detail-item">
                        <span className="detail-label">Purchase Date:</span>
                        <span className="detail-value">{selectedClient?.date || 'N/A'}</span>
                      </div>
                      <div className="customer-detail-item">
                        <span className="detail-label">Amount Paid:</span>
                        <span className="detail-value revenue-stat">{formatCurrency(selectedClient?.paid || 0)}</span>
                      </div>
                      <div className="customer-detail-item">
                        <span className="detail-label">Remaining Balance:</span>
                        <span className="detail-value revenue-stat">{formatCurrency(selectedClient?.balance || 0)}</span>
                      </div>
                      <div className="customer-detail-item">
                        <span className="detail-label">Expiry:</span>
                        <span className={`detail-value ${selectedClient?.expiry === 'Expired' ? 'expired-status' : ''}`}>
                          {selectedClient?.expiry || 'N/A'}
                        </span>
                      </div>
                      <div className="customer-detail-item">
                        <span className="detail-label">Invoice:</span>
                        <span className="detail-value">{selectedClient?.invoice || 'N/A'}</span>
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
                              {formatDateForModal(customerDetails.last_visit)}
                            </div>
                            <div className="stat-description">Most recent visit</div>
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

export default PrepaidPackageClients

