import React, { useState, useEffect } from 'react'
import {
  FaBars,
  FaBell,
  FaUser,
  FaArrowLeft,
  FaCloudDownloadAlt,
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

  return (
    <div className="membership-clients-page">
      {/* Header */}
      <header className="membership-clients-header">
        <div className="header-left">
          <button className="menu-icon">
            <FaBars />
          </button>
          <h1 className="header-title">Membership Clients</h1>
        </div>
        <div className="header-right">
          <div className="logo-box">
            <span className="logo-text">HAIR STUDIO</span>
          </div>
          <button className="header-icon bell-icon">
            <FaBell />
          </button>
          <button className="header-icon user-icon">
            <FaUser />
          </button>
        </div>
      </header>

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
                          className="view-bill-btn"
                          onClick={() => {
                            alert(`Membership Details:\nCustomer: ${client.customerName}\nMobile: ${client.mobile}\nMembership: ${client.membershipName}\nPrice: ₹${client.price}\nDiscount: ${client.discount}%\nExpiry: ${client.expiry}`)
                          }}
                        >
                          View Bill
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
    </div>
  )
}

export default MembershipClients

