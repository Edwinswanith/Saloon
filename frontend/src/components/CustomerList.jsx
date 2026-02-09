import React, { useState, useEffect } from 'react'
import { FaClipboard, FaEdit, FaTrash } from 'react-icons/fa'
import './CustomerList.css'
import { API_BASE_URL } from '../config'
import { useAuth } from '../contexts/AuthContext'
import { apiGet, apiPost, apiPut, apiDelete } from '../utils/api'
import { showSuccess, showError, showWarning, showInfo } from '../utils/toast.jsx'
import DatePicker from 'react-datepicker'
import 'react-datepicker/dist/react-datepicker.css'
import { PageTransition } from './shared/PageTransition'
import { TableSkeleton } from './shared/SkeletonLoaders'
import { EmptyCustomers, EmptySearch } from './shared/EmptyStates'

const CustomerList = () => {
  const { currentBranch, user } = useAuth()
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
  const [mergeMode, setMergeMode] = useState(false)
  const [selectedForMerge, setSelectedForMerge] = useState([])
  const [mergePreview, setMergePreview] = useState(null)
  const [showMergePreviewModal, setShowMergePreviewModal] = useState(false)
  const [mergeLoading, setMergeLoading] = useState(false)
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
  }, [currentPage, searchQuery, currentBranch])

  // Listen for branch changes
  useEffect(() => {
    const handleBranchChange = () => {
      setCurrentPage(1) // Reset to first page
      fetchCustomers()
    }
    
    window.addEventListener('branchChanged', handleBranchChange)
    return () => window.removeEventListener('branchChanged', handleBranchChange)
  }, [])

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
      const response = await apiGet(`/api/customers?${params}`)
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
        referralCode: customer.referralCode || customer.referral_code || ''
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
    showSuccess('Referral code copied to clipboard!')
  }

  const handleDownloadClients = () => {
    // Create CSV content
    const csvContent = [
      ['No.', 'Mobile', 'First Name', 'Last Name', 'Source', 'Gender', 'DOB Range', 'Referral Code'],
      ...customers.map((customer, index) => [
        (currentPage - 1) * 10 + index + 1,
        `+91 ${customer.mobile}`,
        customer.firstName || '',
        customer.lastName || '',
        customer.source || 'Walk-in',
        customer.gender || '',
        customer.dobRange || '',
        customer.referralCode || ''
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
    // Show customer details in a toast
    showInfo(`${customer.firstName} ${customer.lastName} | Mobile: +91 ${customer.mobile}`)
  }

  const handleSaveCustomer = async () => {
    if (!customerFormData.mobile || !customerFormData.firstName) {
      showWarning('Mobile and First Name are required')
      return
    }

    try {
      // Clean mobile number (remove spaces, +91, etc.)
      let cleanMobile = customerFormData.mobile.toString().trim()
      cleanMobile = cleanMobile.replace(/\s+/g, '') // Remove spaces
      cleanMobile = cleanMobile.replace(/^\+91/, '') // Remove +91 prefix
      cleanMobile = cleanMobile.replace(/^91/, '') // Remove 91 prefix
      
      if (cleanMobile.length < 10) {
        showWarning('Please enter a valid mobile number (at least 10 digits)')
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

      const response = editingCustomer 
        ? await apiPut(url.replace(API_BASE_URL, ''), requestBody)
        : await apiPost(url.replace(API_BASE_URL, ''), requestBody)

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
        if (!isEdit && data.created === false) {
          showWarning(`Customer already exists — ${data.customerName || data.message}`)
        } else {
          showSuccess(data.message || (isEdit ? 'Customer updated successfully!' : 'Customer added successfully!'))
        }
      } else {
        let errorData
        try {
          errorData = await response.json()
        } catch (e) {
          errorData = { error: `HTTP ${response.status}: ${response.statusText}` }
        }
        console.error('Error response:', errorData)
        showError(errorData.error || `Failed to save customer (Status: ${response.status})`)
      }
    } catch (error) {
      console.error('Error saving customer:', error)
      console.error('Error details:', {
        name: error.name,
        message: error.message,
        stack: error.stack
      })
      showError(`Error saving customer: ${error.message}. Please check if the backend server is running.`)
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
              await apiPost('/api/customers', customerData)
            } catch (err) {
              console.error(`Error importing customer ${i}:`, err)
            }
          }
        }
        
        showSuccess('Customers imported successfully!')
        setShowImportModal(false)
        fetchCustomers()
      } catch (error) {
        console.error('Error processing import file:', error)
        showError('Error processing import file. Please check the format and try again.')
      }
    }
    reader.readAsText(file)
  }

  const handleDelete = async (customerId) => {
    if (!window.confirm('Are you sure you want to delete this customer?')) {
      return
    }
    try {
      const response = await apiDelete(`/api/customers/${customerId}`)
      
      if (response.ok) {
        const data = await response.json()
        showSuccess(data.message || 'Customer deleted successfully')
        fetchCustomers() // Refresh the list
      } else {
        const errorData = await response.json().catch(() => ({ error: 'Unknown error' }))
        showError(errorData.error || `Failed to delete customer (Status: ${response.status})`)
      }
    } catch (error) {
      console.error('Error deleting customer:', error)
      showError(`Error deleting customer: ${error.message}. Please check if the backend server is running.`)
    }
  }

  const handleMergeToggle = (customerId) => {
    setSelectedForMerge(prev => {
      if (prev.includes(customerId)) {
        return prev.filter(id => id !== customerId)
      }
      if (prev.length >= 2) return prev
      return [...prev, customerId]
    })
  }

  const handleMergePreview = async () => {
    if (selectedForMerge.length !== 2) return
    setMergeLoading(true)
    try {
      const response = await apiPost('/api/customers/merge/preview', {
        primary_id: selectedForMerge[0],
        secondary_id: selectedForMerge[1]
      })
      if (response.ok) {
        const data = await response.json()
        setMergePreview(data)
        setShowMergePreviewModal(true)
      } else {
        const err = await response.json()
        showError(err.error || 'Failed to preview merge')
      }
    } catch (error) {
      showError('Error previewing merge: ' + error.message)
    } finally {
      setMergeLoading(false)
    }
  }

  const handleSwapMerge = () => {
    if (!mergePreview) return
    setMergePreview({
      ...mergePreview,
      primary: mergePreview.secondary,
      secondary: mergePreview.primary,
      primaryRecords: mergePreview.secondaryRecords,
      secondaryRecords: mergePreview.primaryRecords,
    })
  }

  const handleExecuteMerge = async () => {
    if (!mergePreview) return
    if (!window.confirm('This merge cannot be undone. All records from the secondary customer will be moved to the primary customer. Continue?')) {
      return
    }
    setMergeLoading(true)
    try {
      const response = await apiPost('/api/customers/merge/execute', {
        primary_id: mergePreview.primary.id,
        secondary_id: mergePreview.secondary.id
      })
      if (response.ok) {
        const data = await response.json()
        showSuccess(data.message || 'Customers merged successfully')
        setShowMergePreviewModal(false)
        setMergeMode(false)
        setSelectedForMerge([])
        setMergePreview(null)
        fetchCustomers()
      } else {
        const err = await response.json()
        showError(err.error || 'Failed to merge customers')
      }
    } catch (error) {
      showError('Error merging customers: ' + error.message)
    } finally {
      setMergeLoading(false)
    }
  }

  return (
    <PageTransition>
      <div className="customer-list-page">
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
            {(user?.role === 'owner' || user?.role === 'manager') && (
              <button
                className={`action-btn ${mergeMode ? 'merge-active-btn' : 'merge-btn'}`}
                onClick={() => {
                  setMergeMode(!mergeMode)
                  setSelectedForMerge([])
                }}
              >
                {mergeMode ? 'Cancel Merge' : 'Merge Customers'}
              </button>
            )}
          </div>

          {/* Merge Action Bar */}
          {mergeMode && selectedForMerge.length === 2 && (
            <div className="merge-action-bar">
              <span>2 customers selected for merge</span>
              <button className="btn-save" onClick={handleMergePreview} disabled={mergeLoading}>
                {mergeLoading ? 'Loading...' : 'Preview Merge'}
              </button>
            </div>
          )}
          {mergeMode && selectedForMerge.length < 2 && (
            <div className="merge-action-bar merge-hint">
              <span>Select 2 customers to merge ({selectedForMerge.length}/2 selected)</span>
            </div>
          )}

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
                  {mergeMode && <th style={{width: '40px'}}>Select</th>}
                  <th>No.</th>
                  <th>Mobile</th>
                  <th>First Name</th>
                  <th>Last Name</th>
                  <th>Source</th>
                  <th>Gender</th>
                  <th>DOB Range</th>
                  <th>Referral Code</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan={mergeMode ? 10 : 9} style={{ padding: 0, border: 'none' }}>
                      <TableSkeleton rows={10} columns={mergeMode ? 10 : 9} />
                    </td>
                  </tr>
                ) : customers.length === 0 ? (
                  <tr>
                    <td colSpan={mergeMode ? 10 : 9} style={{ padding: 0, border: 'none' }}>
                      {searchQuery ? (
                        <EmptySearch searchQuery={searchQuery} message="Try adjusting your search query." />
                      ) : (
                        <EmptyCustomers onAddCustomer={handleAddCustomer} />
                      )}
                    </td>
                  </tr>
                ) : (
                  customers.map((customer, index) => (
                    <tr key={customer.id} className={selectedForMerge.includes(customer.id) ? 'merge-selected-row' : ''}>
                      {mergeMode && (
                        <td>
                          <input
                            type="checkbox"
                            checked={selectedForMerge.includes(customer.id)}
                            disabled={selectedForMerge.length >= 2 && !selectedForMerge.includes(customer.id)}
                            onChange={() => handleMergeToggle(customer.id)}
                          />
                        </td>
                      )}
                      <td>{(currentPage - 1) * 10 + index + 1}</td>
                      <td>+91 {customer.mobile}</td>
                      <td>{customer.firstName}</td>
                      <td>{customer.lastName || '-'}</td>
                      <td>
                        <span className="source-badge">{customer.source || 'Walk-in'}</span>
                      </td>
                      <td>{customer.gender || '-'}</td>
                      <td>{customer.dobRange || '-'}</td>
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
              <DatePicker
                selected={customerFormData.dob ? new Date(customerFormData.dob) : null}
                onChange={(date) => setCustomerFormData({ ...customerFormData, dob: date ? date.toISOString().split('T')[0] : '' })}
                dateFormat="dd/MM/yyyy"
                placeholderText="Select date of birth"
                showYearDropdown
                scrollableYearDropdown
                yearDropdownItemNumber={100}
                maxDate={new Date()}
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

      {/* Merge Preview Modal */}
      {showMergePreviewModal && mergePreview && (
        <div className="modal-overlay" onClick={() => setShowMergePreviewModal(false)}>
          <div className="modal-content merge-preview-modal" onClick={(e) => e.stopPropagation()}>
            <h2>Merge Customers Preview</h2>

            <div className="merge-comparison">
              <div className="merge-card merge-primary">
                <h3>Primary (Keep)</h3>
                <div className="merge-card-details">
                  <p><strong>Name:</strong> {mergePreview.primary.firstName} {mergePreview.primary.lastName}</p>
                  <p><strong>Mobile:</strong> +91 {mergePreview.primary.mobile}</p>
                  <p><strong>Email:</strong> {mergePreview.primary.email || '-'}</p>
                  <p><strong>Visits:</strong> {mergePreview.primary.totalVisits}</p>
                  <p><strong>Total Spent:</strong> ₹{mergePreview.primary.totalSpent?.toLocaleString('en-IN')}</p>
                  <p><strong>Records:</strong> {Object.values(mergePreview.primaryRecords).reduce((a, b) => a + b, 0)}</p>
                </div>
              </div>

              <button className="merge-swap-btn" onClick={handleSwapMerge} title="Swap primary and secondary">
                ⇄
              </button>

              <div className="merge-card merge-secondary">
                <h3>Secondary (Merge Into Primary)</h3>
                <div className="merge-card-details">
                  <p><strong>Name:</strong> {mergePreview.secondary.firstName} {mergePreview.secondary.lastName}</p>
                  <p><strong>Mobile:</strong> +91 {mergePreview.secondary.mobile}</p>
                  <p><strong>Email:</strong> {mergePreview.secondary.email || '-'}</p>
                  <p><strong>Visits:</strong> {mergePreview.secondary.totalVisits}</p>
                  <p><strong>Total Spent:</strong> ₹{mergePreview.secondary.totalSpent?.toLocaleString('en-IN')}</p>
                  <p><strong>Records:</strong> {Object.values(mergePreview.secondaryRecords).reduce((a, b) => a + b, 0)}</p>
                </div>
              </div>
            </div>

            <div className="merge-records-summary">
              <h4>Records to move from secondary to primary:</h4>
              <table className="merge-stats-table">
                <tbody>
                  {Object.entries(mergePreview.secondaryRecords).map(([key, count]) => (
                    count > 0 && (
                      <tr key={key}>
                        <td>{key.replace(/([A-Z])/g, ' $1').replace(/^./, s => s.toUpperCase())}</td>
                        <td>{count}</td>
                      </tr>
                    )
                  ))}
                  {Object.values(mergePreview.secondaryRecords).every(v => v === 0) && (
                    <tr><td colSpan="2">No records to move</td></tr>
                  )}
                </tbody>
              </table>
            </div>

            <div className="merge-warning">
              This action cannot be undone. The secondary customer's mobile ({mergePreview.secondary.mobile}) will be saved as a secondary mobile on the primary customer. All records will be moved to the primary customer.
            </div>

            <div className="modal-actions">
              <button className="btn-cancel" onClick={() => setShowMergePreviewModal(false)}>Cancel</button>
              <button className="btn-save merge-confirm-btn" onClick={handleExecuteMerge} disabled={mergeLoading}>
                {mergeLoading ? 'Merging...' : 'Confirm Merge'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
    </PageTransition>
  )
}

export default CustomerList

