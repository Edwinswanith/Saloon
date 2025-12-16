import React, { useState, useEffect } from 'react'
import {
  FaBars,
  FaBell,
  FaUser,
  FaArrowLeft,
  FaCloudDownloadAlt,
  FaClock,
} from 'react-icons/fa'
import './PrepaidPackageClients.css'
import { API_BASE_URL } from '../config'

const PrepaidPackageClients = ({ setActivePage }) => {
  const [searchQuery, setSearchQuery] = useState('')
  const [currentPage, setCurrentPage] = useState(1)
  const [clients, setClients] = useState([])
  const [loading, setLoading] = useState(true)
  const [filteredClients, setFilteredClients] = useState([])

  useEffect(() => {
    fetchPrepaidClients()
  }, [])

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
      const response = await fetch(`${API_BASE_URL}/api/reports/prepaid-clients?status=active`)
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

  return (
    <div className="prepaid-package-clients-page">
      {/* Header */}
      <header className="prepaid-package-clients-header">
        <div className="header-left">
          <button className="menu-icon">
            <FaBars />
          </button>
          <h1 className="header-title">Prepaid Package Clients</h1>
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
                        className="action-icon-btn" 
                        title="View Details"
                        onClick={() => {
                          alert(`Prepaid Package Details:\nCustomer: ${client.customerName}\nPhone: ${client.phone}\nPackage: ${client.package}\nPaid: ₹${client.paid}\nBalance: ₹${client.balance}\nExpiry: ${client.expiry}`)
                        }}
                      >
                        <FaClock />
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

export default PrepaidPackageClients

