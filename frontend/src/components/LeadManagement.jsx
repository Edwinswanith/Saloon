import React, { useState, useEffect } from 'react'
import { FaBars, FaCloudUploadAlt, FaPlus, FaDownload, FaEdit, FaTrash, FaChevronDown } from 'react-icons/fa'
import './LeadManagement.css'
import { API_BASE_URL } from '../config'

const LeadManagement = () => {
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [currentPage, setCurrentPage] = useState(1)
  const [leads, setLeads] = useState([])
  const [loading, setLoading] = useState(true)
  const [showLeadModal, setShowLeadModal] = useState(false)
  const [editingLead, setEditingLead] = useState(null)
  const [showUploadModal, setShowUploadModal] = useState(false)
  const [leadFormData, setLeadFormData] = useState({
    name: '',
    mobile: '',
    email: '',
    source: 'Walk-in',
    status: 'new',
    notes: '',
    follow_up_date: ''
  })

  useEffect(() => {
    fetchLeads()
  }, [statusFilter, searchQuery])

  const fetchLeads = async () => {
    try {
      setLoading(true)
      const params = new URLSearchParams()
      if (statusFilter !== 'all') params.append('status', statusFilter)
      if (searchQuery) params.append('search', searchQuery)
      
      const response = await fetch(`${API_BASE_URL}/api/leads?${params}`)
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      const data = await response.json()
      // Backend returns array directly
      setLeads(Array.isArray(data) ? data : (data.leads || []))
    } catch (error) {
      console.error('Error fetching leads:', error)
      setLeads([])
    } finally {
      setLoading(false)
    }
  }

  const handleAddLead = () => {
    setEditingLead(null)
    setLeadFormData({
      name: '',
      mobile: '',
      email: '',
      source: 'Walk-in',
      status: 'new',
      notes: '',
      follow_up_date: ''
    })
    setShowLeadModal(true)
  }

  const handleEditLead = (lead) => {
    setEditingLead(lead)
    setLeadFormData({
      name: lead.name || '',
      mobile: lead.mobile || '',
      email: lead.email || '',
      source: lead.source || 'Walk-in',
      status: lead.status || 'new',
      notes: lead.notes || '',
      follow_up_date: lead.follow_up_date ? lead.follow_up_date.split('T')[0] : ''
    })
    setShowLeadModal(true)
  }

  const handleSaveLead = async () => {
    if (!leadFormData.name || !leadFormData.mobile) {
      alert('Name and Mobile are required')
      return
    }

    try {
      const url = editingLead 
        ? `${API_BASE_URL}/api/leads/${editingLead.id}`
        : `${API_BASE_URL}/api/leads`
      const method = editingLead ? 'PUT' : 'POST'

      const requestBody = {
        name: leadFormData.name.trim(),
        mobile: leadFormData.mobile.trim(),
        email: (leadFormData.email || '').trim(),
        source: leadFormData.source || 'Walk-in',
        status: leadFormData.status || 'new',
        notes: (leadFormData.notes || '').trim(),
      }

      if (leadFormData.follow_up_date) {
        requestBody.follow_up_date = leadFormData.follow_up_date
      }

      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      })

      if (response.ok) {
        const data = await response.json()
        fetchLeads()
        setShowLeadModal(false)
        setEditingLead(null)
        setLeadFormData({
          name: '',
          mobile: '',
          email: '',
          source: 'Walk-in',
          status: 'new',
          notes: '',
          follow_up_date: ''
        })
        alert(data.message || (editingLead ? 'Lead updated successfully!' : 'Lead added successfully!'))
      } else {
        const errorData = await response.json().catch(() => ({ error: 'Unknown error' }))
        alert(errorData.error || `Failed to save lead (Status: ${response.status})`)
      }
    } catch (error) {
      console.error('Error saving lead:', error)
      alert(`Error saving lead: ${error.message}\n\nPlease check if the backend server is running at ${API_BASE_URL}`)
    }
  }

  const handleDelete = async (leadId) => {
    if (!window.confirm('Are you sure you want to delete this lead?')) {
      return
    }
    try {
      const response = await fetch(`${API_BASE_URL}/api/leads/${leadId}`, {
        method: 'DELETE',
      })
      if (response.ok) {
        fetchLeads()
        alert('Lead deleted successfully')
      } else {
        const errorData = await response.json().catch(() => ({ error: 'Unknown error' }))
        alert(errorData.error || 'Failed to delete lead')
      }
    } catch (error) {
      console.error('Error deleting lead:', error)
      alert(`Error deleting lead: ${error.message}`)
    }
  }

  const handleUploadLeads = () => {
    setShowUploadModal(true)
  }

  const handleFileUpload = (e) => {
    const file = e.target.files[0]
    if (!file) return

    const reader = new FileReader()
    reader.onload = async (event) => {
      try {
        const text = event.target.result
        const lines = text.split('\n')
        const headers = lines[0].split(',').map(h => h.trim().toLowerCase())
        
        // Find column indices
        const nameIdx = headers.findIndex(h => h.includes('name'))
        const mobileIdx = headers.findIndex(h => h.includes('mobile'))
        const emailIdx = headers.findIndex(h => h.includes('email'))
        const sourceIdx = headers.findIndex(h => h.includes('source'))
        const statusIdx = headers.findIndex(h => h.includes('status'))
        const notesIdx = headers.findIndex(h => h.includes('notes'))

        if (nameIdx === -1 || mobileIdx === -1) {
          alert('CSV must contain Name and Mobile columns')
          return
        }

        let successCount = 0
        let errorCount = 0

        // Skip header row and process data
        for (let i = 1; i < lines.length; i++) {
          if (!lines[i].trim()) continue
          const values = lines[i].split(',').map(v => v.trim())
          
          const leadData = {
            name: values[nameIdx] || '',
            mobile: values[mobileIdx] || '',
            email: emailIdx >= 0 ? (values[emailIdx] || '') : '',
            source: sourceIdx >= 0 ? (values[sourceIdx] || 'Walk-in') : 'Walk-in',
            status: statusIdx >= 0 ? (values[statusIdx] || 'new') : 'new',
            notes: notesIdx >= 0 ? (values[notesIdx] || '') : '',
          }

          if (leadData.name && leadData.mobile) {
            try {
              const response = await fetch(`${API_BASE_URL}/api/leads`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(leadData),
              })
              if (response.ok) {
                successCount++
              } else {
                errorCount++
              }
            } catch (err) {
              console.error(`Error importing lead ${i}:`, err)
              errorCount++
            }
          }
        }
        
        alert(`Leads imported: ${successCount} successful, ${errorCount} failed`)
        setShowUploadModal(false)
        fetchLeads()
      } catch (error) {
        console.error('Error processing import file:', error)
        alert('Error processing import file')
      }
    }
    reader.readAsText(file)
  }

  const handleDownloadReport = () => {
    // Create CSV content
    const csvContent = [
      ['Name', 'Mobile', 'Email', 'Source', 'Status', 'Date Added', 'Notes'],
      ...leads.map(lead => [
        lead.name || '',
        lead.mobile || '',
        lead.email || '',
        lead.source || '',
        lead.status || '',
        lead.created_at ? new Date(lead.created_at).toLocaleDateString() : '',
        lead.notes || '',
      ])
    ].map(row => row.map(cell => `"${cell}"`).join(',')).join('\n')
    
    // Download CSV
    const blob = new Blob([csvContent], { type: 'text/csv' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `leads-report-${new Date().toISOString().split('T')[0]}.csv`
    a.click()
    window.URL.revokeObjectURL(url)
  }

  const getStatusClass = (status) => {
    const statusMap = {
      new: 'status-new',
      contacted: 'status-contacted',
      'follow-up': 'status-followup',
      completed: 'status-completed',
      lost: 'status-lost',
    }
    return statusMap[status.toLowerCase()] || ''
  }

  return (
    <div className="lead-management-page">
      {/* Header */}
      <header className="lead-management-header">
        <div className="header-left">
          <button className="menu-icon"><FaBars /></button>
          <h1 className="header-title">Lead Management</h1>
        </div>
        <div className="header-right">
          <div className="logo-box">
            <span className="logo-text">IST HAIR STUDIO</span>
          </div>
        </div>
      </header>

      <div className="lead-management-container">
        {/* Lead Management Card */}
        <div className="lead-management-card">
          <div className="card-header">
            <h2 className="card-title">Lead Management</h2>

            {/* Action Bar */}
            <div className="action-bar">
              <div className="status-dropdown-wrapper">
                <select
                  className="status-dropdown"
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                >
                  <option value="all">All Status</option>
                  <option value="new">New</option>
                  <option value="contacted">Contacted</option>
                  <option value="follow-up">Follow-up</option>
                  <option value="completed">Completed</option>
                </select>
                <span className="dropdown-arrow"><FaChevronDown /></span>
              </div>

              <button className="action-btn upload-btn" onClick={handleUploadLeads}>
                <span className="btn-icon"><FaCloudUploadAlt /></span>
                Upload Leads
              </button>

              <button className="action-btn add-btn" onClick={handleAddLead}>
                <span className="btn-icon"><FaPlus /></span>
                Add New Lead
              </button>

              <button className="action-btn download-btn" onClick={handleDownloadReport}>
                <span className="btn-icon"><FaDownload /></span>
                Download Report
              </button>
            </div>
          </div>

          {/* Search Bar */}
          <div className="search-section">
            <input
              type="text"
              className="search-input"
              placeholder="Search by name or mobile..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>

          {/* Leads Table */}
          <div className="table-wrapper">
            <table className="leads-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Mobile</th>
                  <th>Source</th>
                  <th>Status</th>
                  <th>Date Added</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan="6" className="empty-row">Loading...</td>
                  </tr>
                ) : leads.length === 0 ? (
                  <tr>
                    <td colSpan="6" className="empty-row">No leads found</td>
                  </tr>
                ) : (
                  leads.map((lead) => (
                    <tr key={lead.id}>
                      <td>{lead.name}</td>
                      <td>{lead.mobile}</td>
                      <td>
                        <span className="source-badge">{lead.source || 'N/A'}</span>
                      </td>
                      <td>
                        <span className={`status-badge ${getStatusClass(lead.status)}`}>
                          {lead.status}
                        </span>
                      </td>
                      <td>{lead.created_at ? new Date(lead.created_at).toLocaleDateString('en-US', { month: '2-digit', day: '2-digit', year: 'numeric' }) : 'N/A'}</td>
                      <td>
                        <div className="action-icons">
                          <button 
                            className="icon-btn edit-btn" 
                            title="Edit"
                            onClick={() => handleEditLead(lead)}
                          >
                            <FaEdit />
                          </button>
                          <button
                            className="icon-btn delete-btn"
                            title="Delete"
                            onClick={() => handleDelete(lead.id)}
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
              disabled={currentPage === 1}
            >
              First
            </button>
            <button
              className="page-btn"
              onClick={() => setCurrentPage((prev) => Math.max(1, prev - 1))}
              disabled={currentPage === 1}
            >
              Previous
            </button>
            <button className="page-btn active">
              Page {currentPage} of 1
            </button>
            <button
              className="page-btn"
              onClick={() => setCurrentPage((prev) => prev + 1)}
            >
              Next
            </button>
            <button className="page-btn">Last</button>
          </div>
        </div>
      </div>

      {/* Add/Edit Lead Modal */}
      {showLeadModal && (
        <div className="modal-overlay" onClick={() => setShowLeadModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2>{editingLead ? 'Edit Lead' : 'Add New Lead'}</h2>
            <div className="form-group">
              <label>Name *</label>
              <input
                type="text"
                value={leadFormData.name}
                onChange={(e) => setLeadFormData({ ...leadFormData, name: e.target.value })}
                placeholder="Enter full name"
                required
              />
            </div>
            <div className="form-group">
              <label>Mobile *</label>
              <input
                type="text"
                value={leadFormData.mobile}
                onChange={(e) => setLeadFormData({ ...leadFormData, mobile: e.target.value })}
                placeholder="9876543210"
                required
              />
            </div>
            <div className="form-group">
              <label>Email</label>
              <input
                type="email"
                value={leadFormData.email}
                onChange={(e) => setLeadFormData({ ...leadFormData, email: e.target.value })}
                placeholder="email@example.com"
              />
            </div>
            <div className="form-group">
              <label>Source</label>
              <select
                value={leadFormData.source}
                onChange={(e) => setLeadFormData({ ...leadFormData, source: e.target.value })}
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
              <label>Status</label>
              <select
                value={leadFormData.status}
                onChange={(e) => setLeadFormData({ ...leadFormData, status: e.target.value })}
              >
                <option value="new">New</option>
                <option value="contacted">Contacted</option>
                <option value="follow-up">Follow-up</option>
                <option value="completed">Completed</option>
                <option value="lost">Lost</option>
              </select>
            </div>
            <div className="form-group">
              <label>Follow-up Date</label>
              <input
                type="date"
                value={leadFormData.follow_up_date}
                onChange={(e) => setLeadFormData({ ...leadFormData, follow_up_date: e.target.value })}
              />
            </div>
            <div className="form-group">
              <label>Notes</label>
              <textarea
                value={leadFormData.notes}
                onChange={(e) => setLeadFormData({ ...leadFormData, notes: e.target.value })}
                placeholder="Additional notes..."
                rows="3"
              />
            </div>
            <div className="modal-actions">
              <button className="btn-cancel" onClick={() => setShowLeadModal(false)}>Cancel</button>
              <button className="btn-save" onClick={handleSaveLead}>Save</button>
            </div>
          </div>
        </div>
      )}

      {/* Upload Leads Modal */}
      {showUploadModal && (
        <div className="modal-overlay" onClick={() => setShowUploadModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2>Upload Leads</h2>
            <div className="import-instructions">
              <p>Upload a CSV file with the following columns:</p>
              <ul>
                <li>Name (required)</li>
                <li>Mobile (required)</li>
                <li>Email (optional)</li>
                <li>Source (optional)</li>
                <li>Status (optional)</li>
                <li>Notes (optional)</li>
              </ul>
            </div>
            <div className="form-group">
              <label>Select CSV File</label>
              <input
                type="file"
                accept=".csv"
                onChange={handleFileUpload}
              />
            </div>
            <div className="modal-actions">
              <button className="btn-cancel" onClick={() => setShowUploadModal(false)}>Cancel</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default LeadManagement

