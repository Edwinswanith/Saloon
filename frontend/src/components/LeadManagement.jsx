import React, { useState, useEffect } from 'react'
import { FaCloudUploadAlt, FaPlus, FaDownload, FaEdit, FaTrash, FaChevronDown } from 'react-icons/fa'
import { Modal, Input, Select, DatePicker, Button, Form } from 'antd'
import dayjs from 'dayjs'
import './LeadManagement.css'
import { apiGet, apiPost, apiPut, apiDelete } from '../utils/api'
import { showSuccess, showError, showWarning } from '../utils/toast.jsx'
import { useAuth } from '../contexts/AuthContext'

const { TextArea } = Input

const LeadManagement = () => {
  const { currentBranch } = useAuth()
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
  }, [statusFilter, searchQuery, currentBranch])

  // Listen for branch changes
  useEffect(() => {
    const handleBranchChange = () => {
      console.log('[LeadManagement] Branch changed, refreshing leads...')
      fetchLeads()
    }
    
    window.addEventListener('branchChanged', handleBranchChange)
    return () => window.removeEventListener('branchChanged', handleBranchChange)
  }, [currentBranch])

  const fetchLeads = async () => {
    try {
      setLoading(true)
      const params = new URLSearchParams()
      if (statusFilter !== 'all') params.append('status', statusFilter)
      if (searchQuery) params.append('search', searchQuery)
      
      const endpoint = `/api/leads${params.toString() ? `?${params.toString()}` : ''}`
      const response = await apiGet(endpoint)
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
      showWarning('Name and Mobile are required')
      return
    }

    try {
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

      const response = editingLead 
        ? await apiPut(`/api/leads/${editingLead.id}`, requestBody)
        : await apiPost('/api/leads', requestBody)

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
        showSuccess(data.message || (editingLead ? 'Lead updated successfully!' : 'Lead added successfully!'))
      } else {
        const errorData = await response.json().catch(() => ({ error: 'Unknown error' }))
        showError(errorData.error || `Failed to save lead (Status: ${response.status})`)
      }
    } catch (error) {
      console.error('Error saving lead:', error)
      showError(`Error saving lead: ${error.message}. Please check if the backend server is running.`)
    }
  }

  const handleDelete = async (leadId) => {
    if (!window.confirm('Are you sure you want to delete this lead?')) {
      return
    }
    try {
      const response = await apiDelete(`/api/leads/${leadId}`)
      if (response.ok) {
        fetchLeads()
        showSuccess('Lead deleted successfully')
      } else {
        const errorData = await response.json().catch(() => ({ error: 'Unknown error' }))
        showError(errorData.error || 'Failed to delete lead')
      }
    } catch (error) {
      console.error('Error deleting lead:', error)
      showError(`Error deleting lead: ${error.message}`)
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
          showError('CSV must contain Name and Mobile columns')
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
              const response = await apiPost('/api/leads', leadData)
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
        
        showSuccess(`Leads imported: ${successCount} successful, ${errorCount} failed`)
        setShowUploadModal(false)
        fetchLeads()
      } catch (error) {
        console.error('Error processing import file:', error)
        showError('Error processing import file. Please check the format and try again.')
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

      {/* Add/Edit Lead Modal - Ant Design */}
      <Modal
        title={editingLead ? 'Edit Lead' : 'Add New Lead'}
        open={showLeadModal}
        onCancel={() => setShowLeadModal(false)}
        footer={[
          <Button key="cancel" onClick={() => setShowLeadModal(false)}>
            Cancel
          </Button>,
          <Button key="submit" type="primary" onClick={handleSaveLead}>
            Save
          </Button>,
        ]}
        width={600}
      >
        <Form layout="vertical" style={{ marginTop: 24 }}>
          <Form.Item
            label="Name"
            required
            tooltip="Full name of the lead"
          >
            <Input
              placeholder="Enter full name"
              value={leadFormData.name}
              onChange={(e) => setLeadFormData({ ...leadFormData, name: e.target.value })}
            />
          </Form.Item>

          <Form.Item
            label="Mobile"
            required
            tooltip="10-digit mobile number"
          >
            <Input
              placeholder="9876543210"
              value={leadFormData.mobile}
              onChange={(e) => setLeadFormData({ ...leadFormData, mobile: e.target.value })}
            />
          </Form.Item>

          <Form.Item label="Email">
            <Input
              type="email"
              placeholder="email@example.com"
              value={leadFormData.email}
              onChange={(e) => setLeadFormData({ ...leadFormData, email: e.target.value })}
            />
          </Form.Item>

          <Form.Item label="Source">
            <Select
              value={leadFormData.source}
              onChange={(value) => setLeadFormData({ ...leadFormData, source: value })}
            >
              <Select.Option value="Walk-in">Walk-in</Select.Option>
              <Select.Option value="Facebook">Facebook</Select.Option>
              <Select.Option value="Instagram">Instagram</Select.Option>
              <Select.Option value="Referral">Referral</Select.Option>
              <Select.Option value="Google">Google</Select.Option>
              <Select.Option value="Other">Other</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item label="Status">
            <Select
              value={leadFormData.status}
              onChange={(value) => setLeadFormData({ ...leadFormData, status: value })}
            >
              <Select.Option value="new">New</Select.Option>
              <Select.Option value="contacted">Contacted</Select.Option>
              <Select.Option value="follow-up">Follow-up</Select.Option>
              <Select.Option value="completed">Completed</Select.Option>
              <Select.Option value="lost">Lost</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item label="Follow-up Date">
            <DatePicker
              style={{ width: '100%' }}
              format="DD/MM/YYYY"
              value={leadFormData.follow_up_date ? dayjs(leadFormData.follow_up_date) : null}
              onChange={(date, dateString) => {
                setLeadFormData({ 
                  ...leadFormData, 
                  follow_up_date: date ? date.format('YYYY-MM-DD') : '' 
                })
              }}
            />
          </Form.Item>

          <Form.Item label="Notes">
            <TextArea
              rows={3}
              placeholder="Additional notes..."
              value={leadFormData.notes}
              onChange={(e) => setLeadFormData({ ...leadFormData, notes: e.target.value })}
            />
          </Form.Item>
        </Form>
      </Modal>

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

