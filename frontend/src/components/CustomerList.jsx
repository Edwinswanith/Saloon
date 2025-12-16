import React, { useState, useEffect } from 'react'
import { FaBars, FaClipboard, FaEdit, FaTrash } from 'react-icons/fa'
import './CustomerList.css'
import { API_BASE_URL } from '../config'

const CustomerList = () => {
  const [searchQuery, setSearchQuery] = useState('')
  const [currentPage, setCurrentPage] = useState(1)
  const [customers, setCustomers] = useState([])
  const [loading, setLoading] = useState(true)
  const [totalPages, setTotalPages] = useState(1)
  const [totalCustomers, setTotalCustomers] = useState(0)
  const [showCustomerModal, setShowCustomerModal] = useState(false)
  const [showSourcesModal, setShowSourcesModal] = useState(false)
  const [showImportModal, setShowImportModal] = useState(false)
  const [editingCustomer, setEditingCustomer] = useState(null)
  const [viewingCustomer, setViewingCustomer] = useState(null)
  const [customerFormData, setCustomerFormData] = useState({
    mobile: '',
    firstName: '',
    lastName: '',
    email: '',
    source: 'Walk-in',
    gender: '',
    dob: '',
    dobRange: '',
  })

  useEffect(() => {
    fetchCustomers()
  }, [currentPage, searchQuery])

  const fetchCustomers = async () => {
    try {
      setLoading(true)
      const params = new URLSearchParams({
        page: currentPage.toString(),
        per_page: '10',
      })
      if (searchQuery) {
        params.append('search', searchQuery)
      }
      const response = await fetch(`${API_BASE_URL}/api/customers?${params}`)
      const data = await response.json()
      // Map customer data to match expected format
      const mappedCustomers = (data.customers || []).map(customer => ({
        id: customer.id,
        mobile: customer.mobile || '',
        firstName: customer.firstName || customer.first_name || '',
        lastName: customer.lastName || customer.last_name || '',
        email: customer.email || '',
        source: customer.source || 'Walk-in',
        gender: customer.gender || '',
        dob: customer.dob || '',
        dobRange: customer.dobRange || customer.dob_range || '',
        loyaltyPoints: customer.loyaltyPoints || customer.loyalty_points || 0,
        referralCode: customer.referralCode || customer.referral_code || '',
        wallet: customer.wallet || customer.wallet_balance || 0,
      }))
      setCustomers(mappedCustomers)
      setTotalPages(data.pages || 1)
      setTotalCustomers(data.total || 0)
    } catch (error) {
      console.error('Error fetching customers:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = (e) => {
    setSearchQuery(e.target.value)
    setCurrentPage(1) // Reset to first page on search
  }

  const copyReferralCode = (code) => {
    navigator.clipboard.writeText(code)
    alert('Referral code copied to clipboard!')
  }

  const handleDownloadClients = () => {
    // Create CSV content
    const csvContent = [
      ['No.', 'Mobile', 'First Name', 'Last Name', 'Source', 'Gender', 'DOB Range', 'Loyalty Points', 'Referral Code', 'Wallet'],
      ...customers.map((customer, index) => [
        (currentPage - 1) * 10 + index + 1,
        `+91 ${customer.mobile}`,
        customer.firstName || '',
        customer.lastName || '',
        customer.source || 'Walk-in',
        customer.gender || '',
        customer.dobRange || '',
        customer.loyaltyPoints || 0,
        customer.referralCode || '',
        customer.wallet || 0,
      ])
    ].map(row => row.join(',')).join('\n')
    
    // Download CSV
    const blob = new Blob([csvContent], { type: 'text/csv' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `customers-${new Date().toISOString().split('T')[0]}.csv`
    a.click()
    window.URL.revokeObjectURL(url)
  }

  const handleManageSources = () => {
    setShowSourcesModal(true)
  }

  const handleImportCustomer = () => {
    setShowImportModal(true)
  }

  const handleAddCustomer = () => {
    setEditingCustomer(null)
    setCustomerFormData({
      mobile: '',
      firstName: '',
      lastName: '',
      email: '',
      source: 'Walk-in',
      gender: '',
      dob: '',
      dobRange: '',
    })
    setShowCustomerModal(true)
  }

  const handleEditCustomer = (customer) => {
    setEditingCustomer(customer)
    setCustomerFormData({
      mobile: customer.mobile || '',
      firstName: customer.firstName || customer.first_name || '',
      lastName: customer.lastName || customer.last_name || '',
      email: customer.email || '',
      source: customer.source || 'Walk-in',
      gender: customer.gender || '',
      dob: customer.dob || '',
      dobRange: customer.dobRange || customer.dob_range || '',
    })
    setShowCustomerModal(true)
  }

  const handleViewCustomer = (customer) => {
    setViewingCustomer(customer)
    // Show customer details in an alert or modal
    alert(`Customer Details:\n\nMobile: +91 ${customer.mobile}\nName: ${customer.firstName || ''} ${customer.lastName || ''}\nEmail: ${customer.email || 'N/A'}\nSource: ${customer.source || 'Walk-in'}\nGender: ${customer.gender || 'N/A'}\nDOB Range: ${customer.dobRange || 'N/A'}\nLoyalty Points: ${customer.loyaltyPoints || 0}\nReferral Code: ${customer.referralCode || 'N/A'}\nWallet: ₹${customer.wallet || 0}`)
  }

  const handleSaveCustomer = async () => {
    if (!customerFormData.mobile || !customerFormData.firstName) {
      alert('Mobile and First Name are required')
      return
    }

    try {
      // Clean mobile number (remove spaces, +91, etc.)
      let cleanMobile = customerFormData.mobile.toString().trim()
      cleanMobile = cleanMobile.replace(/\s+/g, '') // Remove spaces
      cleanMobile = cleanMobile.replace(/^\+91/, '') // Remove +91 prefix
      cleanMobile = cleanMobile.replace(/^91/, '') // Remove 91 prefix
      
      if (cleanMobile.length < 10) {
        alert('Please enter a valid mobile number (at least 10 digits)')
        return
      }

      const url = editingCustomer 
        ? `${API_BASE_URL}/api/customers/${editingCustomer.id}`
        : `${API_BASE_URL}/api/customers`
      const method = editingCustomer ? 'PUT' : 'POST'

      const requestBody = {
        mobile: cleanMobile,
        firstName: customerFormData.firstName.trim(),
        lastName: (customerFormData.lastName || '').trim(),
        email: (customerFormData.email || '').trim(),
        source: customerFormData.source || 'Walk-in',
        gender: customerFormData.gender || '',
        dobRange: customerFormData.dobRange || '',
      }

      // Only include dob if it's provided and not empty
      // Ensure date is in YYYY-MM-DD format
      if (customerFormData.dob) {
        // If date is in DD-MM-YYYY format, convert it
        let dobValue = customerFormData.dob
        if (dobValue.includes('-') && dobValue.split('-')[0].length === 2) {
          // Assume DD-MM-YYYY format, convert to YYYY-MM-DD
          const parts = dobValue.split('-')
          if (parts.length === 3) {
            dobValue = `${parts[2]}-${parts[1]}-${parts[0]}`
          }
        }
        requestBody.dob = dobValue
      }

      console.log('Sending request to:', url)
      console.log('Request method:', method)
      console.log('Request body:', requestBody)

      const response = await fetch(url, {
        method,
        headers: { 
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
        mode: 'cors', // Explicitly set CORS mode
      })

      console.log('Response status:', response.status)
      console.log('Response ok:', response.ok)

      if (response.ok) {
        const data = await response.json()
        const isEdit = !!editingCustomer
        fetchCustomers()
        setShowCustomerModal(false)
        setEditingCustomer(null)
        setCustomerFormData({
          mobile: '',
          firstName: '',
          lastName: '',
          email: '',
          source: 'Walk-in',
          gender: '',
          dob: '',
          dobRange: '',
        })
        alert(data.message || (isEdit ? 'Customer updated successfully!' : 'Customer added successfully!'))
      } else {
        let errorData
        try {
          errorData = await response.json()
        } catch (e) {
          errorData = { error: `HTTP ${response.status}: ${response.statusText}` }
        }
        console.error('Error response:', errorData)
        alert(errorData.error || `Failed to save customer (Status: ${response.status})`)
      }
    } catch (error) {
      console.error('Error saving customer:', error)
      console.error('Error details:', {
        name: error.name,
        message: error.message,
        stack: error.stack
      })
      alert(`Error saving customer: ${error.message}\n\nPlease check:\n1. Backend server is running at ${API_BASE_URL}\n2. Check browser console for details`)
    }
  }

  const handleImportFile = (e) => {
    const file = e.target.files[0]
    if (!file) return

    const reader = new FileReader()
    reader.onload = async (event) => {
      try {
        const text = event.target.result
        const lines = text.split('\n')
        const headers = lines[0].split(',').map(h => h.trim())
        
        // Skip header row and process data
        for (let i = 1; i < lines.length; i++) {
          if (!lines[i].trim()) continue
          const values = lines[i].split(',').map(v => v.trim())
          const customerData = {
            mobile: values[0] || '',
            first_name: values[1] || '',
            last_name: values[2] || '',
            email: values[3] || '',
            source: values[4] || 'Walk-in',
            gender: values[5] || '',
            dob_range: values[6] || '',
          }

          if (customerData.mobile && customerData.first_name) {
            try {
              await fetch(`${API_BASE_URL}/api/customers`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(customerData),
              })
            } catch (err) {
              console.error(`Error importing customer ${i}:`, err)
            }
          }
        }
        
        alert('Customers imported successfully!')
        setShowImportModal(false)
        fetchCustomers()
      } catch (error) {
        console.error('Error processing import file:', error)
        alert('Error processing import file')
      }
    }
    reader.readAsText(file)
  }

  const handleDelete = async (customerId) => {
    if (!window.confirm('Are you sure you want to delete this customer?')) {
      return
    }
    try {
      const response = await fetch(`${API_BASE_URL}/api/customers/${customerId}`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        },
      })
      
      if (response.ok) {
        const data = await response.json()
        alert(data.message || 'Customer deleted successfully')
        fetchCustomers() // Refresh the list
      } else {
        const errorData = await response.json().catch(() => ({ error: 'Unknown error' }))
        alert(errorData.error || `Failed to delete customer (Status: ${response.status})`)
      }
    } catch (error) {
      console.error('Error deleting customer:', error)
      alert(`Error deleting customer: ${error.message}. Please check if the backend server is running.`)
    }
  }

  return (
    <div className="customer-list-page">
      {/* Header */}
      <header className="customer-list-header">
        <div className="header-left">
          <button className="menu-icon"><FaBars /></button>
          <h1 className="header-title">Customers</h1>
        </div>
        <div className="header-right">
          <div className="logo-box">
            <span className="logo-text">HAIR STUDIO</span>
          </div>
        </div>
      </header>

      <div className="customer-list-container">
        {/* Customer List Card */}
        <div className="customer-list-card">
          <h2 className="card-title">Customer List</h2>

          {/* Action Buttons */}
          <div className="action-buttons">
            <button className="action-btn download-btn" onClick={handleDownloadClients}>
              Download Clients
            </button>
            <button className="action-btn manage-btn" onClick={handleManageSources}>Manage Sources</button>
            <button className="action-btn import-btn" onClick={handleImportCustomer}>Import Customer</button>
            <button className="action-btn add-btn" onClick={handleAddCustomer}>Add Customer</button>
          </div>

          {/* Search Bar */}
          <div className="search-section">
            <input
              type="text"
              className="search-input"
              placeholder="Search customer"
              value={searchQuery}
              onChange={handleSearch}
            />
          </div>

          {/* Customer Table */}
          <div className="table-wrapper">
            <table className="customer-table">
              <thead>
                <tr>
                  <th>No.</th>
                  <th>Mobile</th>
                  <th>First Name</th>
                  <th>Last Name</th>
                  <th>Source</th>
                  <th>Gender</th>
                  <th>DOB Range</th>
                  <th>Loyalty Points</th>
                  <th>Referral Code</th>
                  <th>Wallet</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan="11" className="empty-row">Loading...</td>
                  </tr>
                ) : customers.length === 0 ? (
                  <tr>
                    <td colSpan="11" className="empty-row">No customers found</td>
                  </tr>
                ) : (
                  customers.map((customer, index) => (
                    <tr key={customer.id}>
                      <td>{(currentPage - 1) * 10 + index + 1}</td>
                      <td>+91 {customer.mobile}</td>
                      <td>{customer.firstName}</td>
                      <td>{customer.lastName || '-'}</td>
                      <td>
                        <span className="source-badge">{customer.source || 'Walk-in'}</span>
                      </td>
                      <td>{customer.gender || '-'}</td>
                      <td>{customer.dobRange || '-'}</td>
                      <td>{customer.loyaltyPoints || 0}</td>
                      <td>
                        <div className="referral-code-cell">
                          <span>{customer.referralCode || '-'}</span>
                          {customer.referralCode && (
                            <button
                              className="copy-btn"
                              onClick={() => copyReferralCode(customer.referralCode)}
                            >
                              Copy
                            </button>
                          )}
                        </div>
                      </td>
                      <td>₹{(customer.wallet || 0).toLocaleString()}</td>
                      <td>
                        <div className="action-icons">
                          <button 
                            className="icon-btn view-btn" 
                            title="View"
                            onClick={() => handleViewCustomer(customer)}
                          >
                            <FaClipboard />
                          </button>
                          <button 
                            className="icon-btn edit-btn" 
                            title="Edit"
                            onClick={() => handleEditCustomer(customer)}
                          >
                            <FaEdit />
                          </button>
                          <button
                            className="icon-btn delete-btn"
                            title="Delete"
                            onClick={() => handleDelete(customer.id)}
                          >
                            <FaTrash />
                          </button>
                        </div>
                      </td>
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
              disabled={currentPage === 1 || loading}
            >
              First
            </button>
            <button
              className="page-btn"
              onClick={() => setCurrentPage((prev) => Math.max(1, prev - 1))}
              disabled={currentPage === 1 || loading}
            >
              Previous
            </button>
            <button className="page-btn active">
              Page {currentPage} of {totalPages} ({totalCustomers} total)
            </button>
            <button
              className="page-btn"
              onClick={() => setCurrentPage((prev) => Math.min(totalPages, prev + 1))}
              disabled={currentPage >= totalPages || loading}
            >
              Next
            </button>
            <button
              className="page-btn"
              onClick={() => setCurrentPage(totalPages)}
              disabled={currentPage >= totalPages || loading}
            >
              Last
            </button>
          </div>
        </div>
      </div>

      {/* Add/Edit Customer Modal */}
      {showCustomerModal && (
        <div className="modal-overlay" onClick={() => setShowCustomerModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2>{editingCustomer ? 'Edit Customer' : 'Add Customer'}</h2>
            <div className="form-group">
              <label>Mobile *</label>
              <input
                type="text"
                value={customerFormData.mobile}
                onChange={(e) => setCustomerFormData({ ...customerFormData, mobile: e.target.value })}
                placeholder="9876543210"
                required
              />
            </div>
            <div className="form-group">
              <label>First Name *</label>
              <input
                type="text"
                value={customerFormData.firstName}
                onChange={(e) => setCustomerFormData({ ...customerFormData, firstName: e.target.value })}
                required
              />
            </div>
            <div className="form-group">
              <label>Last Name</label>
              <input
                type="text"
                value={customerFormData.lastName}
                onChange={(e) => setCustomerFormData({ ...customerFormData, lastName: e.target.value })}
              />
            </div>
            <div className="form-group">
              <label>Email</label>
              <input
                type="email"
                value={customerFormData.email}
                onChange={(e) => setCustomerFormData({ ...customerFormData, email: e.target.value })}
              />
            </div>
            <div className="form-group">
              <label>Source</label>
              <select
                value={customerFormData.source}
                onChange={(e) => setCustomerFormData({ ...customerFormData, source: e.target.value })}
              >
                <option value="Walk-in">Walk-in</option>
                <option value="Facebook">Facebook</option>
                <option value="Instagram">Instagram</option>
                <option value="Referral">Referral</option>
                <option value="Google">Google</option>
                <option value="Other">Other</option>
              </select>
            </div>
            <div className="form-group">
              <label>Gender</label>
              <select
                value={customerFormData.gender}
                onChange={(e) => setCustomerFormData({ ...customerFormData, gender: e.target.value })}
              >
                <option value="">Select Gender</option>
                <option value="Male">Male</option>
                <option value="Female">Female</option>
                <option value="Other">Other</option>
              </select>
            </div>
            <div className="form-group">
              <label>DOB Range</label>
              <select
                value={customerFormData.dobRange}
                onChange={(e) => setCustomerFormData({ ...customerFormData, dobRange: e.target.value })}
              >
                <option value="">Select Range</option>
                <option value="Young">Young</option>
                <option value="Mid">Mid</option>
                <option value="Old">Old</option>
              </select>
            </div>
            <div className="form-group">
              <label>Date of Birth</label>
              <input
                type="date"
                value={customerFormData.dob}
                onChange={(e) => setCustomerFormData({ ...customerFormData, dob: e.target.value })}
              />
            </div>
            <div className="modal-actions">
              <button className="btn-cancel" onClick={() => setShowCustomerModal(false)}>Cancel</button>
              <button className="btn-save" onClick={handleSaveCustomer}>Save</button>
            </div>
          </div>
        </div>
      )}

      {/* Manage Sources Modal */}
      {showSourcesModal && (
        <div className="modal-overlay" onClick={() => setShowSourcesModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2>Manage Customer Sources</h2>
            <div className="sources-list">
              <p>Available Sources:</p>
              <ul>
                <li>Walk-in</li>
                <li>Facebook</li>
                <li>Instagram</li>
                <li>Referral</li>
                <li>Google</li>
                <li>Other</li>
              </ul>
              <p style={{ fontSize: '12px', color: '#666', marginTop: '10px' }}>
                Note: Source management will be enhanced in future updates.
              </p>
            </div>
            <div className="modal-actions">
              <button className="btn-cancel" onClick={() => setShowSourcesModal(false)}>Close</button>
            </div>
          </div>
        </div>
      )}

      {/* Import Customer Modal */}
      {showImportModal && (
        <div className="modal-overlay" onClick={() => setShowImportModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2>Import Customers</h2>
            <div className="import-instructions">
              <p>Upload a CSV file with the following columns:</p>
              <ul>
                <li>Mobile (required)</li>
                <li>First Name (required)</li>
                <li>Last Name</li>
                <li>Email</li>
                <li>Source</li>
                <li>Gender</li>
                <li>DOB Range</li>
              </ul>
            </div>
            <div className="form-group">
              <label>Select CSV File</label>
              <input
                type="file"
                accept=".csv"
                onChange={handleImportFile}
              />
            </div>
            <div className="modal-actions">
              <button className="btn-cancel" onClick={() => setShowImportModal(false)}>Cancel</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default CustomerList

