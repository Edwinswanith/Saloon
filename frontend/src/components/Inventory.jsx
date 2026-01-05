import React, { useState, useEffect } from 'react'
import { FaBars, FaUser, FaEdit, FaTrash } from 'react-icons/fa'
import './Inventory.css'
import { apiGet, apiPost, apiDelete } from '../utils/api'
import { useAuth } from '../contexts/AuthContext'

const Inventory = () => {
  const { currentBranch } = useAuth()
  const [activeTab, setActiveTab] = useState('supplier')
  const [searchQuery, setSearchQuery] = useState('')
  const [suppliers, setSuppliers] = useState([])
  const [loading, setLoading] = useState(true)
  const [showSupplierModal, setShowSupplierModal] = useState(false)
  const [editingSupplier, setEditingSupplier] = useState(null)
  const [supplierFormData, setSupplierFormData] = useState({
    name: '',
    contact_no: '',
    email: '',
    address: '',
    status: 'active',
  })

  useEffect(() => {
    if (activeTab === 'supplier') {
      fetchSuppliers()
    }
  }, [activeTab, searchQuery, currentBranch])

  // Listen for branch changes
  useEffect(() => {
    const handleBranchChange = () => {
      console.log('[Inventory] Branch changed, refreshing data...')
      if (activeTab === 'supplier') {
        fetchSuppliers()
      }
    }
    
    window.addEventListener('branchChanged', handleBranchChange)
    return () => window.removeEventListener('branchChanged', handleBranchChange)
  }, [currentBranch, activeTab])

  const fetchSuppliers = async () => {
    try {
      setLoading(true)
      const params = new URLSearchParams()
      if (searchQuery) params.append('search', searchQuery)
      
      const response = await apiGet(`/api/inventory/suppliers?${params}`)
      const data = await response.json()
      // Backend returns array directly
      setSuppliers(Array.isArray(data) ? data : (data.suppliers || []))
    } catch (error) {
      console.error('Error fetching suppliers:', error)
      setSuppliers([])
    } finally {
      setLoading(false)
    }
  }

  const handleDeleteSupplier = async (supplierId) => {
    if (!window.confirm('Are you sure you want to delete this supplier?')) {
      return
    }
    try {
      const response = await apiDelete(`/api/inventory/suppliers/${supplierId}`)
      if (response.ok) {
        fetchSuppliers()
      } else {
        alert('Failed to delete supplier')
      }
    } catch (error) {
      console.error('Error deleting supplier:', error)
      alert('Error deleting supplier')
    }
  }

  const handleAddSupplier = () => {
    setEditingSupplier(null)
    setSupplierFormData({
      name: '',
      contact_no: '',
      email: '',
      address: '',
      status: 'active',
    })
    setShowSupplierModal(true)
  }

  const handleEditSupplier = (supplier) => {
    setEditingSupplier(supplier)
    setSupplierFormData({
      name: supplier.name || '',
      contact_no: supplier.contact_no || '',
      email: supplier.email || '',
      address: supplier.address || '',
      status: supplier.status || 'active',
    })
    setShowSupplierModal(true)
  }

  const handleSaveSupplier = async () => {
    try {
      const url = editingSupplier 
        ? `/api/inventory/suppliers/${editingSupplier.id}`
        : `/api/inventory/suppliers`

      const response = await apiPost(url, supplierFormData, editingSupplier ? 'PUT' : 'POST')

      if (response.ok) {
        fetchSuppliers()
        setShowSupplierModal(false)
        setEditingSupplier(null)
      } else {
        const error = await response.json()
        alert(error.error || 'Failed to save supplier')
      }
    } catch (error) {
      console.error('Error saving supplier:', error)
      alert('Error saving supplier')
    }
  }

  return (
    <div className="inventory-page">
      {/* Header */}
      <header className="inventory-header">
        <div className="header-left">
          <button className="menu-icon"><FaBars /></button>
          <h1 className="header-title">Inventory</h1>
        </div>
        <div className="header-right">
          <button className="user-icon"><FaUser /></button>
          <div className="logo-box">
            <span className="logo-text">HAIR STUDIO</span>
          </div>
        </div>
      </header>

      <div className="inventory-container">
        {/* Inventory Card */}
        <div className="inventory-card">
          {/* Tabs */}
          <div className="inventory-tabs">
            <button
              className={`tab ${activeTab === 'supplier' ? 'active' : ''}`}
              onClick={() => setActiveTab('supplier')}
            >
              Supplier
            </button>
            <button
              className={`tab ${activeTab === 'orders' ? 'active' : ''}`}
              onClick={() => setActiveTab('orders')}
            >
              Orders
            </button>
            <button
              className={`tab ${activeTab === 'dashboard' ? 'active' : ''}`}
              onClick={() => setActiveTab('dashboard')}
            >
              Inventory Dashboard
            </button>
          </div>

          {/* Search and Action Bar */}
          <div className="search-action-bar">
            <div className="search-section">
              <input
                type="text"
                className="search-input"
                placeholder="Search supplier"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
            <button className="add-supplier-btn" onClick={handleAddSupplier}>Add Supplier</button>
          </div>

          {/* Supplier Table */}
          {activeTab === 'supplier' && (
            <div className="table-wrapper">
              <table className="supplier-table">
                <thead>
                  <tr>
                    <th>No.</th>
                    <th>Name</th>
                    <th>Contact No</th>
                    <th>Address</th>
                    <th>Status</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {loading ? (
                    <tr>
                      <td colSpan="6" className="empty-row">Loading...</td>
                    </tr>
                  ) : suppliers.length === 0 ? (
                    <tr>
                      <td colSpan="6" className="empty-row">No suppliers found</td>
                    </tr>
                  ) : (
                    suppliers.map((supplier, index) => (
                      <tr key={supplier.id}>
                        <td>{index + 1}</td>
                        <td>{supplier.name}</td>
                        <td>{supplier.contact_no || 'N/A'}</td>
                        <td>{supplier.address || 'N/A'}</td>
                        <td>
                          <span className={`status-badge ${supplier.status}`}>
                            {supplier.status}
                          </span>
                        </td>
                        <td>
                          <div className="action-icons">
                            <button 
                              className="icon-btn edit-btn" 
                              title="Edit"
                              onClick={() => handleEditSupplier(supplier)}
                            >
                              <FaEdit />
                            </button>
                            <button
                              className="icon-btn delete-btn"
                              title="Delete"
                              onClick={() => handleDeleteSupplier(supplier.id)}
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

          {/* Orders Tab Content */}
          {activeTab === 'orders' && (
            <div className="tab-content">
              <p className="empty-message">Orders content coming soon...</p>
            </div>
          )}

          {/* Inventory Dashboard Tab Content */}
          {activeTab === 'dashboard' && (
            <div className="tab-content">
              <p className="empty-message">Inventory Dashboard content coming soon...</p>
            </div>
          )}
        </div>
      </div>

      {/* Supplier Modal */}
      {showSupplierModal && (
        <div className="modal-overlay" onClick={() => setShowSupplierModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2>{editingSupplier ? 'Edit Supplier' : 'Add Supplier'}</h2>
            <div className="form-group">
              <label>Name *</label>
              <input
                type="text"
                value={supplierFormData.name}
                onChange={(e) => setSupplierFormData({ ...supplierFormData, name: e.target.value })}
                required
              />
            </div>
            <div className="form-group">
              <label>Contact No</label>
              <input
                type="text"
                value={supplierFormData.contact_no}
                onChange={(e) => setSupplierFormData({ ...supplierFormData, contact_no: e.target.value })}
              />
            </div>
            <div className="form-group">
              <label>Email</label>
              <input
                type="email"
                value={supplierFormData.email}
                onChange={(e) => setSupplierFormData({ ...supplierFormData, email: e.target.value })}
              />
            </div>
            <div className="form-group">
              <label>Address</label>
              <textarea
                value={supplierFormData.address}
                onChange={(e) => setSupplierFormData({ ...supplierFormData, address: e.target.value })}
                rows="3"
              />
            </div>
            <div className="form-group">
              <label>Status</label>
              <select
                value={supplierFormData.status}
                onChange={(e) => setSupplierFormData({ ...supplierFormData, status: e.target.value })}
              >
                <option value="active">Active</option>
                <option value="inactive">Inactive</option>
              </select>
            </div>
            <div className="modal-actions">
              <button className="btn-cancel" onClick={() => setShowSupplierModal(false)}>Cancel</button>
              <button className="btn-save" onClick={handleSaveSupplier}>Save</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default Inventory

