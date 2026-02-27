import React, { useState, useEffect } from 'react'
import {
  FaEdit,
  FaTrash,
  FaPlus,
} from 'react-icons/fa'
import './Manager.css'
import { apiGet, apiPost, apiPut, apiDelete } from '../utils/api'
import { useAuth } from '../contexts/AuthContext'

const Manager = () => {
  const { user, branches, fetchBranches } = useAuth()
  const [managers, setManagers] = useState([])
  const [loading, setLoading] = useState(true)
  const [showAddModal, setShowAddModal] = useState(false)
  const [editingManager, setEditingManager] = useState(null)
  const [formData, setFormData] = useState({
    firstName: '',
    lastName: '',
    email: '',
    mobile: '',
    salon: '',
    status: 'active',
    password: '',
    branch: '',
  })

  useEffect(() => {
    fetchManagers()
    // Fetch branches if user is owner or manager
    if (user && (user.role === 'owner' || user.role === 'manager')) {
      fetchBranches()
    }
  }, [user])

  const fetchManagers = async () => {
    try {
      setLoading(true)
      const response = await apiGet('/api/managers')
      const data = await response.json()
      setManagers(data.managers || [])
    } catch (error) {
      console.error('Error fetching managers:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleAddNew = () => {
    setEditingManager(null)
    setFormData({
      firstName: '',
      lastName: '',
      email: '',
      mobile: '',
      salon: '',
      status: 'active',
      password: '',
      branch: '',
    })
    setShowAddModal(true)
  }

  const handleEdit = (manager) => {
    setEditingManager(manager)
    setFormData({
      firstName: manager.firstName,
      lastName: manager.lastName || '',
      email: manager.email,
      mobile: manager.mobile,
      salon: manager.salon || '',
      status: manager.status,
      password: '',
      branch: manager.branchId || '',
    })
    setShowAddModal(true)
  }

  const handleDelete = async (managerId) => {
    if (!window.confirm('Are you sure you want to delete this manager?')) {
      return
    }

    try {
      const response = await apiDelete(`/api/managers/${managerId}`)

      if (response.ok) {
        fetchManagers()
      } else {
        const error = await response.json()
        alert(error.error || 'Failed to delete manager')
      }
    } catch (error) {
      console.error('Error deleting manager:', error)
      alert('Error deleting manager')
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()

    if (!formData.mobile.trim()) {
      alert('Mobile number is required')
      return
    }
    if (!formData.firstName.trim()) {
      alert('First name is required')
      return
    }
    if (!editingManager && !formData.password.trim()) {
      alert('Password is required')
      return
    }
    if (!editingManager && formData.password.trim().length < 6) {
      alert('Password must be at least 6 characters')
      return
    }

    try {
      const payload = {
        firstName: formData.firstName.trim(),
        lastName: formData.lastName.trim(),
        email: formData.email.trim(),
        mobile: formData.mobile.trim(),
        salon: formData.salon.trim(),
        status: formData.status,
      }

      if (!editingManager) {
        payload.password = formData.password.trim()
      }

      // Add branch_id if owner or manager selected a branch
      if (user && (user.role === 'owner' || user.role === 'manager') && formData.branch) {
        payload.branch_id = formData.branch
      }

      const response = editingManager
        ? await apiPut(`/api/managers/${editingManager.id}`, payload)
        : await apiPost('/api/managers', payload)

      if (response.ok) {
        setShowAddModal(false)
        fetchManagers()
      } else {
        const error = await response.json()
        alert(error.error || 'Failed to save manager')
      }
    } catch (error) {
      console.error('Error saving manager:', error)
      alert('Error saving manager')
    }
  }

  const formatMobile = (mobile) => {
    if (!mobile) return ''
    if (mobile.startsWith('+91')) return mobile
    if (mobile.startsWith('91')) return `+${mobile}`
    return `+91${mobile}`
  }

  return (
    <div className="manager-page">
      <div className="manager-container">
        {/* Manager Management Card */}
        <div className="manager-card">
          {/* Section Header */}
          <div className="manager-section-header">
            <h2 className="section-title">Manager Management</h2>
            <button className="add-manager-btn" onClick={handleAddNew}>
              <FaPlus /> ADD MANAGER
            </button>
          </div>

          {/* Manager Table */}
          {loading ? (
            <div className="loading-message">Loading...</div>
          ) : (
            <div className="table-wrapper">
              <table className="manager-table">
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Email</th>
                    <th>Mobile</th>
                    <th>Saloon</th>
                    <th>Status</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {managers.length === 0 ? (
                    <tr>
                      <td colSpan="6" className="empty-row">
                        No managers found
                      </td>
                    </tr>
                  ) : (
                    managers.map((manager) => (
                      <tr key={manager.id}>
                        <td>{manager.name}</td>
                        <td>{manager.email}</td>
                        <td>{formatMobile(manager.mobile)}</td>
                        <td>{manager.salon || '-'}</td>
                        <td>
                          <span className={`status-badge ${manager.status}`}>
                            {manager.status}
                          </span>
                        </td>
                        <td>
                          <div className="action-icons">
                            <button
                              className="icon-btn edit-btn"
                              title="Edit"
                              onClick={() => handleEdit(manager)}
                            >
                              <FaEdit />
                            </button>
                            <button
                              className="icon-btn delete-btn"
                              title="Delete"
                              onClick={() => handleDelete(manager.id)}
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
          )}
        </div>
      </div>

      {/* Add/Edit Modal */}
      {showAddModal && (
        <div className="modal-overlay" onClick={() => setShowAddModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2>{editingManager ? 'Edit Manager' : 'Add Manager'}</h2>
            <div className="modal-form-container">
              <form onSubmit={handleSubmit}>
                <div className="form-group">
                <label>First Name *</label>
                <input
                  type="text"
                  value={formData.firstName}
                  onChange={(e) =>
                    setFormData({ ...formData, firstName: e.target.value })
                  }
                  required
                />
              </div>
              <div className="form-group">
                <label>Last Name</label>
                <input
                  type="text"
                  value={formData.lastName}
                  onChange={(e) =>
                    setFormData({ ...formData, lastName: e.target.value })
                  }
                />
              </div>
              <div className="form-group">
                <label>Email *</label>
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) =>
                    setFormData({ ...formData, email: e.target.value })
                  }
                  required
                />
              </div>
              <div className="form-group">
                <label>Mobile *</label>
                <input
                  type="tel"
                  value={formData.mobile}
                  onChange={(e) =>
                    setFormData({ ...formData, mobile: e.target.value })
                  }
                  placeholder="9999999999"
                  required
                />
              </div>
              <div className="form-group">
                <label>Saloon</label>
                <input
                  type="text"
                  value={formData.salon}
                  onChange={(e) =>
                    setFormData({ ...formData, salon: e.target.value })
                  }
                  placeholder="Saloon name or account"
                />
              </div>
              <div className="form-group">
                <label>Status</label>
                <select
                  value={formData.status}
                  onChange={(e) =>
                    setFormData({ ...formData, status: e.target.value })
                  }
                >
                  <option value="active">Active</option>
                  <option value="inactive">Inactive</option>
                </select>
              </div>
              {user && (user.role === 'owner' || user.role === 'manager') && (
                <div className="form-group">
                  <label>Branch *</label>
                  <select
                    value={formData.branch}
                    onChange={(e) =>
                      setFormData({ ...formData, branch: e.target.value })
                    }
                    required
                  >
                    <option value="">Select Branch</option>
                    {branches.map((branch) => (
                      <option key={branch.id} value={branch.id}>
                        {branch.name}
                      </option>
                    ))}
                  </select>
                </div>
              )}
              {!editingManager && (
                <div className="form-group">
                  <label>Password *</label>
                  <input
                    type="password"
                    value={formData.password}
                    onChange={(e) =>
                      setFormData({ ...formData, password: e.target.value })
                    }
                    placeholder="Enter initial password (min 6 characters)"
                    required
                    minLength={6}
                  />
                </div>
              )}
              <div className="modal-actions">
                <button
                  type="button"
                  className="btn-cancel"
                  onClick={() => setShowAddModal(false)}
                >
                  Cancel
                </button>
                <button type="submit" className="btn-save">
                  Save
                </button>
              </div>
            </form>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default Manager

