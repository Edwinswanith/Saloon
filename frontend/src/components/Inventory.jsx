import React, { useState, useEffect } from 'react'
import { createPortal } from 'react-dom'
import { FaEdit, FaTrash, FaTimes } from 'react-icons/fa'
import './Inventory.css'
import { apiGet, apiPost, apiPut, apiDelete } from '../utils/api'
import { useAuth } from '../contexts/AuthContext'
import CompactSelect from './shared/CompactSelect'
import { showSuccess, showError } from '../utils/toast.jsx'

const STATUS_OPTIONS = [
  { value: 'active', label: 'Active' },
  { value: 'inactive', label: 'Inactive' },
]

const Inventory = () => {
  const { currentBranch } = useAuth()
  const [activeTab, setActiveTab] = useState('supplier')
  const [searchQuery, setSearchQuery] = useState('')
  const [suppliers, setSuppliers] = useState([])
  const [inventoryProducts, setInventoryProducts] = useState([])
  const [inventorySummary, setInventorySummary] = useState(null)
  const [consumptionLogs, setConsumptionLogs] = useState([])
  const [consumptionSummary, setConsumptionSummary] = useState([])
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
  const [consumptionFormData, setConsumptionFormData] = useState({
    product_id: '',
    quantity: '',
    service_name: '',
    period_label: '',
    reason: '',
    consumption_date: new Date().toISOString().split('T')[0],
  })
  const [editingConsumption, setEditingConsumption] = useState(null)

  const getEmptyConsumptionForm = () => ({
    product_id: '',
    quantity: '',
    service_name: '',
    period_label: '',
    reason: '',
    consumption_date: new Date().toISOString().split('T')[0],
  })

  const formatQuantity = (value, unit = 'units') => {
    const number = Number(value || 0)
    const formatted = Number.isInteger(number)
      ? number.toLocaleString('en-IN')
      : number.toLocaleString('en-IN', { maximumFractionDigits: 3 })
    return `${formatted} ${unit || 'units'}`
  }

  useEffect(() => {
    if (activeTab === 'supplier') {
      fetchSuppliers()
    } else if (activeTab === 'dashboard') {
      fetchInventoryDashboard()
    } else if (activeTab === 'consumption') {
      fetchInventoryDashboard()
      fetchConsumption()
    }
  }, [activeTab, searchQuery, currentBranch])

  // Listen for branch changes
  useEffect(() => {
    const handleBranchChange = () => {
      console.log('[Inventory] Branch changed, refreshing data...')
      if (activeTab === 'supplier') {
        fetchSuppliers()
      } else if (activeTab === 'dashboard') {
        fetchInventoryDashboard()
      } else if (activeTab === 'consumption') {
        fetchInventoryDashboard()
        fetchConsumption()
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

  const fetchInventoryDashboard = async () => {
    try {
      setLoading(true)
      const [productsRes, summaryRes, consumptionSummaryRes] = await Promise.all([
        apiGet('/api/inventory/products'),
        apiGet('/api/inventory/summary'),
        apiGet('/api/inventory/consumption-summary'),
      ])
      const products = await productsRes.json()
      const summary = await summaryRes.json()
      const consumption = await consumptionSummaryRes.json()
      setInventoryProducts(Array.isArray(products) ? products : [])
      setInventorySummary(summary || null)
      setConsumptionSummary(consumption.items || [])
    } catch (error) {
      console.error('Error fetching inventory dashboard:', error)
      setInventoryProducts([])
      setInventorySummary(null)
      setConsumptionSummary([])
    } finally {
      setLoading(false)
    }
  }

  const fetchConsumption = async () => {
    try {
      setLoading(true)
      const response = await apiGet('/api/inventory/consumption')
      const data = await response.json()
      setConsumptionLogs(Array.isArray(data) ? data : [])
    } catch (error) {
      console.error('Error fetching consumption logs:', error)
      setConsumptionLogs([])
    } finally {
      setLoading(false)
    }
  }

  const handleSaveConsumption = async () => {
    try {
      if (!consumptionFormData.product_id) {
        showError('Select a product')
        return
      }
      const quantity = Number.parseFloat(consumptionFormData.quantity)
      if (!Number.isFinite(quantity) || quantity <= 0) {
        showError('Enter a valid quantity')
        return
      }

      const payload = {
        ...consumptionFormData,
        quantity,
        consumption_type: 'service',
      }
      const response = editingConsumption
        ? await apiPut(`/api/inventory/consumption/${editingConsumption.id}`, payload)
        : await apiPost('/api/inventory/consumption', payload)
      const data = await response.json()
      if (!response.ok) {
        showError(data.error || 'Failed to record consumption')
        return
      }

      showSuccess(data.message || (editingConsumption ? 'Consumption updated' : 'Consumption recorded'))
      setConsumptionFormData(getEmptyConsumptionForm())
      setEditingConsumption(null)
      await fetchInventoryDashboard()
      await fetchConsumption()
    } catch (error) {
      console.error('Error saving consumption:', error)
      showError(`Error saving consumption: ${error.message}`)
    }
  }

  const handleEditConsumption = (log) => {
    setEditingConsumption(log)
    setConsumptionFormData({
      product_id: log.product_id || '',
      quantity: log.quantity || '',
      service_name: log.service_name || '',
      period_label: log.period_label || '',
      reason: log.reason || '',
      consumption_date: log.consumption_date || new Date().toISOString().split('T')[0],
    })
  }

  const handleCancelConsumptionEdit = () => {
    setEditingConsumption(null)
    setConsumptionFormData(getEmptyConsumptionForm())
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

      const response = editingSupplier
        ? await apiPut(url, supplierFormData)
        : await apiPost(url, supplierFormData)

      if (response.ok) {
        fetchSuppliers()
        showSuccess(editingSupplier ? 'Supplier updated' : 'Supplier added')
        setShowSupplierModal(false)
        setEditingSupplier(null)
      } else {
        const error = await response.json()
        showError(error.error || 'Failed to save supplier')
      }
    } catch (error) {
      console.error('Error saving supplier:', error)
      showError('Error saving supplier')
    }
  }

  const filteredProducts = inventoryProducts.filter(product => (
    product.name || ''
  ).toLowerCase().includes(searchQuery.toLowerCase()))

  const selectedConsumptionProduct = inventoryProducts.find(
    product => product.id === consumptionFormData.product_id
  )
  const enteredConsumptionQuantity = Number.parseFloat(consumptionFormData.quantity)
  const editingOriginalQuantity = (
    editingConsumption &&
    editingConsumption.product_id === consumptionFormData.product_id
  )
    ? Number(editingConsumption.quantity || 0)
    : 0
  const remainingAfterConsumption = (
    selectedConsumptionProduct &&
    Number.isFinite(enteredConsumptionQuantity) &&
    enteredConsumptionQuantity > 0
  )
    ? Number(selectedConsumptionProduct.stock_quantity || 0) + editingOriginalQuantity - enteredConsumptionQuantity
    : null

  return (
    <div className="inventory-page">
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
            <button
              className={`tab ${activeTab === 'consumption' ? 'active' : ''}`}
              onClick={() => setActiveTab('consumption')}
            >
              Consumption
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
            {activeTab === 'supplier' && (
              <button className="add-supplier-btn" onClick={handleAddSupplier}>Add Supplier</button>
            )}
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
              <div className="inventory-summary-grid">
                <div className="inventory-summary-card">
                  <span>Total Products</span>
                  <strong>{inventorySummary?.total_products || 0}</strong>
                </div>
                <div className="inventory-summary-card">
                  <span>Stock Value</span>
                  <strong>₹{(inventorySummary?.total_stock_value || 0).toLocaleString('en-IN')}</strong>
                </div>
                <div className="inventory-summary-card warning">
                  <span>Low Stock</span>
                  <strong>{inventorySummary?.low_stock_items || 0}</strong>
                </div>
                <div className="inventory-summary-card danger">
                  <span>Out of Stock</span>
                  <strong>{inventorySummary?.out_of_stock_items || 0}</strong>
                </div>
              </div>

              <div className="table-wrapper">
                <table className="supplier-table">
                  <thead>
                    <tr>
                      <th>Product</th>
                      <th>Category</th>
                      <th>Stock</th>
                      <th>Min Stock</th>
                      <th>Cost</th>
                      <th>Stock Value</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {loading ? (
                      <tr><td colSpan="7" className="empty-row">Loading...</td></tr>
                    ) : filteredProducts.length === 0 ? (
                      <tr><td colSpan="7" className="empty-row">No products found</td></tr>
                    ) : (
                      filteredProducts.map(product => (
                        <tr key={product.id}>
                          <td>{product.name}</td>
                          <td>{product.category_name || '-'}</td>
                          <td>{formatQuantity(product.stock_quantity, product.stock_unit)}</td>
                          <td>{formatQuantity(product.min_stock_level, product.stock_unit)}</td>
                          <td>₹{(product.cost || 0).toLocaleString('en-IN')}</td>
                          <td>₹{(product.stock_value || 0).toLocaleString('en-IN')}</td>
                          <td>
                            <span className={`status-badge ${product.low_stock ? 'inactive' : 'active'}`}>
                              {product.low_stock ? 'Low Stock' : 'In Stock'}
                            </span>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {activeTab === 'consumption' && (
            <div className="tab-content">
              <div className="consumption-panel">
                <div className="consumption-form">
                  <div className="form-group">
                    <label>Product</label>
                    <CompactSelect
                      value={consumptionFormData.product_id}
                      onChange={(v) => setConsumptionFormData({ ...consumptionFormData, product_id: v })}
                      options={inventoryProducts.map(product => ({
                        value: product.id,
                        label: `${product.name} (${formatQuantity(product.stock_quantity, product.stock_unit)} left)`
                      }))}
                      placeholder="Select product"
                    />
                  </div>
                  <div className="form-group">
                    <label>Quantity Used</label>
                    <input
                      type="number"
                      min="0.001"
                      step="0.001"
                      value={consumptionFormData.quantity}
                      onChange={(e) => setConsumptionFormData({ ...consumptionFormData, quantity: e.target.value })}
                      placeholder={selectedConsumptionProduct ? `Example: 300 ${selectedConsumptionProduct.stock_unit || 'units'}` : 'Example: 300'}
                    />
                    {selectedConsumptionProduct && (
                      <span className={`consumption-stock-hint ${remainingAfterConsumption !== null && remainingAfterConsumption < 0 ? 'danger' : ''}`}>
                        Current stock: {formatQuantity(selectedConsumptionProduct.stock_quantity, selectedConsumptionProduct.stock_unit)}
                        {remainingAfterConsumption !== null && (
                          <> | After save: {formatQuantity(remainingAfterConsumption, selectedConsumptionProduct.stock_unit)}</>
                        )}
                      </span>
                    )}
                  </div>
                  <div className="form-group">
                    <label>Service / Usage</label>
                    <input
                      type="text"
                      value={consumptionFormData.service_name}
                      onChange={(e) => setConsumptionFormData({ ...consumptionFormData, service_name: e.target.value })}
                      placeholder="Hair spa, facial, cleaning..."
                    />
                  </div>
                  <div className="form-group">
                    <label>Period</label>
                    <input
                      type="text"
                      value={consumptionFormData.period_label}
                      onChange={(e) => setConsumptionFormData({ ...consumptionFormData, period_label: e.target.value })}
                      placeholder="Daily, weekly, monthly"
                    />
                  </div>
                  <div className="form-group">
                    <label>Date</label>
                    <input
                      type="date"
                      value={consumptionFormData.consumption_date}
                      onChange={(e) => setConsumptionFormData({ ...consumptionFormData, consumption_date: e.target.value })}
                    />
                  </div>
                  <div className="form-group full-width">
                    <label>Reason / Notes</label>
                    <input
                      type="text"
                      value={consumptionFormData.reason}
                      onChange={(e) => setConsumptionFormData({ ...consumptionFormData, reason: e.target.value })}
                      placeholder="Optional note"
                    />
                  </div>
                  <div className="consumption-actions">
                    <button className="add-supplier-btn" onClick={handleSaveConsumption}>
                      {editingConsumption ? 'Update Consumption' : 'Record Consumption'}
                    </button>
                    {editingConsumption && (
                      <button className="secondary-action-btn" onClick={handleCancelConsumptionEdit}>
                        Cancel Edit
                      </button>
                    )}
                  </div>
                </div>

                <div className="consumption-summary-list">
                  <h3>Top Consumed Products</h3>
                  {consumptionSummary.length === 0 ? (
                    <p className="empty-message">No consumption data yet.</p>
                  ) : (
                    consumptionSummary.map(item => (
                      <div className="consumption-summary-row" key={item.product_id}>
                        <span>{item.product_name}</span>
                        <strong>{formatQuantity(item.total_quantity, item.unit)}</strong>
                      </div>
                    ))
                  )}
                </div>
              </div>

              <div className="table-wrapper">
                <table className="supplier-table">
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Product</th>
                      <th>Qty Used</th>
                      <th>Service</th>
                      <th>Period</th>
                      <th>Reason</th>
                      <th>Type</th>
                      <th>By</th>
                      <th>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {loading ? (
                      <tr><td colSpan="9" className="empty-row">Loading...</td></tr>
                    ) : consumptionLogs.length === 0 ? (
                      <tr><td colSpan="9" className="empty-row">No consumption records found</td></tr>
                    ) : (
                      consumptionLogs.map(log => (
                        <tr key={log.id}>
                          <td>{log.consumption_date || '-'}</td>
                          <td>{log.product_name}</td>
                          <td>{formatQuantity(log.quantity, log.unit)}</td>
                          <td>{log.service_name || '-'}</td>
                          <td>{log.period_label || '-'}</td>
                          <td>{log.reason || '-'}</td>
                          <td>{log.consumption_type}</td>
                          <td>{log.created_by_name || '-'}</td>
                          <td>
                            <button
                              className="icon-btn edit-btn"
                              title="Edit consumption"
                              onClick={() => handleEditConsumption(log)}
                            >
                              <FaEdit />
                            </button>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Supplier Modal */}
      {showSupplierModal && createPortal(
        <div className="modal-overlay" onClick={() => setShowSupplierModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="std-modal-header">
              <h2>{editingSupplier ? 'Edit Supplier' : 'Add Supplier'}</h2>
              <button
                type="button"
                className="modal-close-btn"
                onClick={() => setShowSupplierModal(false)}
                aria-label="Close"
              >
                <FaTimes />
              </button>
            </div>
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
              <CompactSelect
                className="form-select"
                value={supplierFormData.status}
                onChange={(v) => setSupplierFormData({ ...supplierFormData, status: v })}
                options={STATUS_OPTIONS}
                placeholder="Select status"
              />
            </div>
            <div className="modal-actions">
              <button className="btn-cancel" onClick={() => setShowSupplierModal(false)}>Cancel</button>
              <button className="btn-save" onClick={handleSaveSupplier}>Save</button>
            </div>
          </div>
        </div>,
        document.body
      )}
    </div>
  )
}

export default Inventory

