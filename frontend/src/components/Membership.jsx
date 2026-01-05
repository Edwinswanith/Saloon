import React, { useState, useEffect } from 'react'
import {
  FaBars,
  FaBell,
  FaUser,
  FaEdit,
  FaTrash,
  FaPlus,
} from 'react-icons/fa'
import './Membership.css'
import { API_BASE_URL } from '../config'
import { useAuth } from '../contexts/AuthContext'

const Membership = () => {
  const { currentBranch } = useAuth()
  const [membershipPlans, setMembershipPlans] = useState([])
  const [loading, setLoading] = useState(true)
  const [showAddModal, setShowAddModal] = useState(false)
  const [editingPlan, setEditingPlan] = useState(null)
  const [formData, setFormData] = useState({
    name: '',
    validity: '',
    price: '',
    allocatedDiscount: '',
    status: 'active',
    description: '',
  })

  useEffect(() => {
    fetchMembershipPlans()
  }, [currentBranch])

  // Listen for branch changes
  useEffect(() => {
    const handleBranchChange = () => {
      console.log('[Membership] Branch changed, refreshing membership plans...')
      fetchMembershipPlans()
    }
    
    window.addEventListener('branchChanged', handleBranchChange)
    return () => window.removeEventListener('branchChanged', handleBranchChange)
  }, [currentBranch])

  const fetchMembershipPlans = async () => {
    try {
      setLoading(true)
      const response = await fetch(`${API_BASE_URL}/api/membership-plans`)
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      const data = await response.json()
      // Backend returns array directly, not wrapped in {plans: [...]}
      setMembershipPlans(Array.isArray(data) ? data : (data.plans || []))
    } catch (error) {
      console.error('Error fetching membership plans:', error)
      setMembershipPlans([])
    } finally {
      setLoading(false)
    }
  }

  const handleAddNew = () => {
    setEditingPlan(null)
    setFormData({
      name: '',
      validity: '',
      price: '',
      allocatedDiscount: '',
      status: 'active',
      description: '',
    })
    setShowAddModal(true)
  }

  const handleEdit = (plan) => {
    setEditingPlan(plan)
    setFormData({
      name: plan.name,
      validity: plan.validity,
      price: plan.price,
      allocatedDiscount: plan.allocatedDiscount,
      status: plan.status,
      description: plan.description || '',
    })
    setShowAddModal(true)
  }

  const handleDelete = async (planId) => {
    if (!window.confirm('Are you sure you want to delete this membership plan?')) {
      return
    }

    try {
      const response = await fetch(`${API_BASE_URL}/api/membership-plans/${planId}`, {
        method: 'DELETE',
      })

      if (response.ok) {
        fetchMembershipPlans()
      } else {
        const error = await response.json()
        alert(error.error || 'Failed to delete membership plan')
      }
    } catch (error) {
      console.error('Error deleting membership plan:', error)
      alert('Error deleting membership plan')
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()

    try {
      const url = editingPlan
        ? `${API_BASE_URL}/api/membership-plans/${editingPlan.id}`
        : `${API_BASE_URL}/api/membership-plans`
      
      const method = editingPlan ? 'PUT' : 'POST'

      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: formData.name,
          validity: parseInt(formData.validity),
          price: parseFloat(formData.price),
          allocatedDiscount: parseFloat(formData.allocatedDiscount) || 0,
          status: formData.status,
          description: formData.description,
        }),
      })

      if (response.ok) {
        setShowAddModal(false)
        fetchMembershipPlans()
      } else {
        const error = await response.json()
        alert(error.error || 'Failed to save membership plan')
      }
    } catch (error) {
      console.error('Error saving membership plan:', error)
      alert('Error saving membership plan')
    }
  }

  return (
    <div className="membership-page">
      {/* Header */}
      <header className="membership-header">
        <div className="header-left">
          <button className="menu-icon">
            <FaBars />
          </button>
          <h1 className="header-title">Membership</h1>
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

      <div className="membership-container">
        {/* Membership Card */}
        <div className="membership-card">
          {/* Section Header */}
          <div className="membership-section-header">
            <h2 className="section-title">Membership List</h2>
            <button className="add-membership-btn" onClick={handleAddNew}>
              Add New Membership
            </button>
          </div>

          {/* Membership Table */}
          {loading ? (
            <div className="loading-message">Loading...</div>
          ) : (
            <div className="table-wrapper">
              <table className="membership-table">
                <thead>
                  <tr>
                    <th>No.</th>
                    <th>Name</th>
                    <th>Validity</th>
                    <th>Price (₹)</th>
                    <th>Allocated Discount (%)</th>
                    <th>Status</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {membershipPlans.length === 0 ? (
                    <tr>
                      <td colSpan="7" className="empty-row">
                        No membership plans found
                      </td>
                    </tr>
                  ) : (
                    membershipPlans.map((plan, index) => (
                      <tr key={plan.id}>
                        <td>{index + 1}</td>
                        <td>{plan.name}</td>
                        <td>{plan.validity} days</td>
                        <td>₹{plan.price.toFixed(2)}</td>
                        <td>{plan.allocatedDiscount}%</td>
                        <td>
                          <span className={`status-badge ${plan.status}`}>
                            {plan.status}
                          </span>
                        </td>
                        <td>
                          <div className="action-icons">
                            <button
                              className="icon-btn edit-btn"
                              title="Edit"
                              onClick={() => handleEdit(plan)}
                            >
                              <FaEdit />
                            </button>
                            <button
                              className="icon-btn delete-btn"
                              title="Delete"
                              onClick={() => handleDelete(plan.id)}
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
            <div className="modal-header">
              <h3>{editingPlan ? 'Edit Membership' : 'Add New Membership'}</h3>
              <button
                className="modal-close"
                onClick={() => setShowAddModal(false)}
              >
                ×
              </button>
            </div>
            <form onSubmit={handleSubmit} className="membership-form">
              <div className="form-group">
                <label>Name *</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) =>
                    setFormData({ ...formData, name: e.target.value })
                  }
                  required
                />
              </div>
              <div className="form-group">
                <label>Validity (Days) *</label>
                <input
                  type="number"
                  value={formData.validity}
                  onChange={(e) =>
                    setFormData({ ...formData, validity: e.target.value })
                  }
                  required
                  min="1"
                />
              </div>
              <div className="form-group">
                <label>Price (₹) *</label>
                <input
                  type="number"
                  step="0.01"
                  value={formData.price}
                  onChange={(e) =>
                    setFormData({ ...formData, price: e.target.value })
                  }
                  required
                  min="0"
                />
              </div>
              <div className="form-group">
                <label>Allocated Discount (%)</label>
                <input
                  type="number"
                  step="0.1"
                  value={formData.allocatedDiscount}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      allocatedDiscount: e.target.value,
                    })
                  }
                  min="0"
                  max="100"
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
              <div className="form-group">
                <label>Description</label>
                <textarea
                  value={formData.description}
                  onChange={(e) =>
                    setFormData({ ...formData, description: e.target.value })
                  }
                  rows="3"
                />
              </div>
              <div className="modal-actions">
                <button
                  type="button"
                  className="btn-cancel"
                  onClick={() => setShowAddModal(false)}
                >
                  Cancel
                </button>
                <button type="submit" className="btn-submit">
                  {editingPlan ? 'Update' : 'Create'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

export default Membership

