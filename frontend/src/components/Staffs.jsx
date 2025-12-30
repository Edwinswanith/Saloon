import React, { useState, useEffect } from 'react'
import {
  FaBars,
  FaBell,
  FaUser,
  FaList,
  FaEdit,
  FaTrash,
} from 'react-icons/fa'
import './Staffs.css'
import { apiGet, apiPost, apiPut, apiDelete } from '../utils/api'
import { showSuccess, showError, showWarning } from '../utils/toast.jsx'
import { useAuth } from '../contexts/AuthContext'

const Staffs = () => {
  const { getBranchId } = useAuth()
  const [currentPage, setCurrentPage] = useState(1)
  const [staffs, setStaffs] = useState([])
  const [loading, setLoading] = useState(true)
  const [showStaffModal, setShowStaffModal] = useState(false)
  const [showViewModal, setShowViewModal] = useState(false)
  const [editingStaff, setEditingStaff] = useState(null)
  const [viewingStaff, setViewingStaff] = useState(null)
  const [staffFormData, setStaffFormData] = useState({
    mobile: '',
    firstName: '',
    lastName: '',
    email: '',
    salary: '',
    commissionRate: ''
  })

  

  useEffect(() => {
    fetchStaffs()
  }, [])

  const fetchStaffs = async () => {
    try {
      setLoading(true)
      const response = await apiGet('/api/staffs')
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      const data = await response.json()
      setStaffs(data.staffs || [])
    } catch (error) {
      console.error('Error fetching staffs:', error)
      setStaffs([])
    } finally {
      setLoading(false)
    }
  }

  const handleAddStaff = () => {
    setEditingStaff(null)
    setStaffFormData({
      mobile: '',
      firstName: '',
      lastName: '',
      email: '',
      salary: '',
      commissionRate: ''
    })
    setShowStaffModal(true)
  }

  const handleEditStaff = async (staff) => {
    setEditingStaff(staff)
    setStaffFormData({
      mobile: staff.mobile || '',
      firstName: staff.firstName || '',
      lastName: staff.lastName || '',
      email: staff.email || '',
      salary: staff.salary || '',
      commissionRate: staff.commissionRate || ''
    })
    setShowStaffModal(true)
  }

  const handleViewStaff = async (staffId) => {
    try {
      const response = await apiGet(`/api/staffs/${staffId}`)
      if (response.ok) {
        const data = await response.json()
        setViewingStaff(data)
        setShowViewModal(true)
      } else {
        showError('Failed to fetch staff details')
      }
    } catch (error) {
      console.error('Error fetching staff details:', error)
      showError('Error fetching staff details')
    }
  }

  const handleSaveStaff = async () => {
    if (!staffFormData.mobile.trim()) {
      showError('Mobile number is required')
      return
    }
    if (!staffFormData.firstName.trim()) {
      showError('First name is required')
      return
    }

    try {
      const staffData = {
        mobile: staffFormData.mobile.trim(),
        firstName: staffFormData.firstName.trim(),
        lastName: staffFormData.lastName.trim(),
        email: staffFormData.email.trim(),
        salary: parseFloat(staffFormData.salary) || 0,
        commissionRate: parseFloat(staffFormData.commissionRate) || 0,
        status: 'active'
      }

      const response = editingStaff 
        ? await apiPut(`/api/staffs/${editingStaff.id}`, staffData)
        : await apiPost('/api/staffs', staffData)

      if (response.ok) {
        const data = await response.json()
        fetchStaffs()
        setShowStaffModal(false)
        setEditingStaff(null)
        setStaffFormData({
          mobile: '',
          firstName: '',
          lastName: '',
          email: '',
          salary: '',
          commissionRate: ''
        })
        showError(data.message || (editingStaff ? 'Staff updated successfully!' : 'Staff added successfully!'))
      } else {
        const errorData = await response.json().catch(() => ({ error: 'Unknown error' }))
        showError(errorData.error || `Failed to save staff (Status: ${response.status})`)
      }
    } catch (error) {
      console.error('Error saving staff:', error)
      showError(`Error saving staff: ${error.message}`)
    }
  }

  const handleDelete = async (staffId) => {
    if (!window.confirm('Are you sure you want to delete this staff member?')) {
      return
    }
    try {
      const response = await apiDelete(`/api/staffs/${staffId}`)
      if (response.ok) {
        fetchStaffs()
        showSuccess('Staff deleted successfully')
      } else {
        const errorData = await response.json().catch(() => ({ error: 'Unknown error' }))
        showError(errorData.error || 'Failed to delete staff member')
      }
    } catch (error) {
      console.error('Error deleting staff:', error)
      showError(`Error deleting staff member: ${error.message}`)
    }
  }

  return (
    <div className="staffs-page">
      {/* Header */}
      <header className="staffs-header">
        <div className="header-left">
          <button className="menu-icon">
            <FaBars />
          </button>
          <h1 className="header-title">Staffs</h1>
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

      <div className="staffs-container">
        {/* Staff List Card */}
        <div className="staffs-card">
          {/* Section Header */}
          <div className="staffs-section-header">
            <h2 className="section-title">Staff List</h2>
            <button className="add-staff-btn" onClick={handleAddStaff}>Add Staff</button>
          </div>

          {/* Staff Table */}
          <div className="table-container">
            <table className="staffs-table">
              <thead>
                <tr>
                  <th>No.</th>
                  <th>Mobile</th>
                  <th>First Name</th>
                  <th>Last Name</th>
                  <th>Email</th>
                  <th>Salary</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan="7" className="empty-row">Loading...</td>
                  </tr>
                ) : staffs.length === 0 ? (
                  <tr>
                    <td colSpan="7" className="empty-row">No staff members found</td>
                  </tr>
                ) : (
                  staffs.map((staff, index) => (
                    <tr key={staff.id}>
                      <td>{index + 1}</td>
                      <td>+91 {staff.mobile}</td>
                      <td>{staff.firstName}</td>
                      <td>{staff.lastName || '-'}</td>
                      <td>{staff.email || '-'}</td>
                      <td>₹{staff.salary ? staff.salary.toLocaleString() : 'N/A'}</td>
                      <td>
                        <div className="action-icons">
                          <button 
                            className="icon-btn view-btn" 
                            title="View"
                            onClick={() => handleViewStaff(staff.id)}
                          >
                            <FaList />
                          </button>
                          <button 
                            className="icon-btn edit-btn" 
                            title="Edit"
                            onClick={() => handleEditStaff(staff)}
                          >
                            <FaEdit />
                          </button>
                          <button
                            className="icon-btn delete-btn"
                            title="Delete"
                            onClick={() => handleDelete(staff.id)}
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
        </div>
      </div>

      {/* Add/Edit Staff Modal */}
      {showStaffModal && (
        <div className="modal-overlay" onClick={() => setShowStaffModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2>{editingStaff ? 'Edit Staff' : 'Add Staff'}</h2>
            <div className="form-group">
              <label>Mobile Number *</label>
              <input
                type="text"
                value={staffFormData.mobile}
                onChange={(e) => setStaffFormData({ ...staffFormData, mobile: e.target.value })}
                placeholder="Enter mobile number"
                required
              />
            </div>
            <div className="form-group">
              <label>First Name *</label>
              <input
                type="text"
                value={staffFormData.firstName}
                onChange={(e) => setStaffFormData({ ...staffFormData, firstName: e.target.value })}
                placeholder="Enter first name"
                required
              />
            </div>
            <div className="form-group">
              <label>Last Name</label>
              <input
                type="text"
                value={staffFormData.lastName}
                onChange={(e) => setStaffFormData({ ...staffFormData, lastName: e.target.value })}
                placeholder="Enter last name"
              />
            </div>
            <div className="form-group">
              <label>Email</label>
              <input
                type="email"
                value={staffFormData.email}
                onChange={(e) => setStaffFormData({ ...staffFormData, email: e.target.value })}
                placeholder="Enter email address"
              />
            </div>
            <div className="form-group">
              <label>Salary</label>
              <input
                type="number"
                step="0.01"
                value={staffFormData.salary}
                onChange={(e) => setStaffFormData({ ...staffFormData, salary: e.target.value })}
                placeholder="Enter salary"
              />
            </div>
            <div className="form-group">
              <label>Commission Rate (%)</label>
              <input
                type="number"
                step="0.01"
                value={staffFormData.commissionRate}
                onChange={(e) => setStaffFormData({ ...staffFormData, commissionRate: e.target.value })}
                placeholder="Enter commission rate"
              />
            </div>
            <div className="modal-actions">
              <button className="btn-cancel" onClick={() => setShowStaffModal(false)}>Cancel</button>
              <button className="btn-save" onClick={handleSaveStaff}>Save</button>
            </div>
          </div>
        </div>
      )}

      {/* View Staff Modal */}
      {showViewModal && viewingStaff && (
        <div className="modal-overlay" onClick={() => setShowViewModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2>Staff Details</h2>
            <div className="view-details">
              <div className="detail-row">
                <label>Mobile Number:</label>
                <span>+91 {viewingStaff.mobile}</span>
              </div>
              <div className="detail-row">
                <label>First Name:</label>
                <span>{viewingStaff.firstName}</span>
              </div>
              <div className="detail-row">
                <label>Last Name:</label>
                <span>{viewingStaff.lastName || '-'}</span>
              </div>
              <div className="detail-row">
                <label>Email:</label>
                <span>{viewingStaff.email || '-'}</span>
              </div>
              <div className="detail-row">
                <label>Salary:</label>
                <span>₹{viewingStaff.salary ? viewingStaff.salary.toLocaleString() : 'N/A'}</span>
              </div>
              <div className="detail-row">
                <label>Commission Rate:</label>
                <span>{viewingStaff.commissionRate ? `${viewingStaff.commissionRate}%` : 'N/A'}</span>
              </div>
              <div className="detail-row">
                <label>Status:</label>
                <span>{viewingStaff.status || 'active'}</span>
              </div>
            </div>
            <div className="modal-actions">
              <button className="btn-cancel" onClick={() => setShowViewModal(false)}>Close</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default Staffs

