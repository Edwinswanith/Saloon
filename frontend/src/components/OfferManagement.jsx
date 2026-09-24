import React, { useState, useEffect } from 'react'
import { createPortal } from 'react-dom'
import { FaEdit, FaTrash, FaPlus, FaTimes } from 'react-icons/fa'
import './Membership.css'
import { apiGet, apiPost, apiPut, apiDelete } from '../utils/api'
import { useAuth } from '../contexts/AuthContext'
import { showError, showSuccess } from '../utils/toast.jsx'
import CompactSelect from './shared/CompactSelect'
import Header from './Header'

const STATUS_OPTIONS = [
  { value: 'active', label: 'Active' },
  { value: 'inactive', label: 'Inactive' },
]

const TYPE_OPTIONS = [
  { value: 'general', label: 'General (any customer)' },
  { value: 'membership', label: 'Membership Customers Only' },
]

const VALIDITY_PRESET_OPTIONS = [
  { value: 'custom', label: 'Custom dates' },
  { value: '7d', label: '7 days' },
  { value: '15d', label: '15 days' },
  { value: '30d', label: '30 days' },
  { value: '1m', label: '1 month' },
  { value: '3m', label: '3 months' },
  { value: '6m', label: '6 months' },
]

const todayStr = () => new Date().toISOString().slice(0, 10)

const addDuration = (preset) => {
  const start = new Date()
  const end = new Date(start)
  if (preset === '7d') end.setDate(end.getDate() + 7)
  else if (preset === '15d') end.setDate(end.getDate() + 15)
  else if (preset === '30d') end.setDate(end.getDate() + 30)
  else if (preset === '1m') end.setMonth(end.getMonth() + 1)
  else if (preset === '3m') end.setMonth(end.getMonth() + 3)
  else if (preset === '6m') end.setMonth(end.getMonth() + 6)
  return {
    start: start.toISOString().slice(0, 10),
    end: end.toISOString().slice(0, 10),
  }
}

const formatDate = (iso) => {
  if (!iso) return '—'
  try {
    return new Date(iso).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })
  } catch {
    return iso
  }
}

const getLiveState = (offer) => {
  if (offer.is_currently_valid) return { label: 'Live', cls: 'active' }
  const now = new Date()
  const start = offer.start_date ? new Date(offer.start_date) : null
  const end = offer.end_date ? new Date(offer.end_date) : null
  if (start && now < start) return { label: 'Upcoming', cls: 'pending' }
  if (end && now > end) return { label: 'Expired', cls: 'inactive' }
  return { label: '—', cls: 'inactive' }
}

const OfferManagement = () => {
  const { currentBranch } = useAuth()
  const [offers, setOffers] = useState([])
  const [loading, setLoading] = useState(true)
  const [showAddModal, setShowAddModal] = useState(false)
  const [editingOffer, setEditingOffer] = useState(null)
  const [validityPreset, setValidityPreset] = useState('30d')
  // Hide soft-deleted (status='inactive') offers from the list by default.
  // The trash icon does a soft delete on the backend; without this filter
  // the row stayed visible and the click looked broken.
  const [showInactive, setShowInactive] = useState(false)
  const [formData, setFormData] = useState({
    name: '',
    offer_type: 'general',
    discount_percentage: '',
    start_date: todayStr(),
    end_date: '',
    status: 'active',
  })

  useEffect(() => {
    fetchOffers()
  }, [currentBranch])

  useEffect(() => {
    const handleBranchChange = () => fetchOffers()
    window.addEventListener('branchChanged', handleBranchChange)
    return () => window.removeEventListener('branchChanged', handleBranchChange)
  }, [])

  const fetchOffers = async () => {
    try {
      setLoading(true)
      const response = await apiGet('/api/offers')
      if (!response.ok) throw new Error('Failed to load offers')
      const data = await response.json()
      setOffers(data.offers || [])
    } catch (error) {
      console.error('Error fetching offers:', error)
      showError('Failed to load offers')
      setOffers([])
    } finally {
      setLoading(false)
    }
  }

  const handleAddNew = () => {
    setEditingOffer(null)
    setValidityPreset('30d')
    const { start, end } = addDuration('30d')
    setFormData({
      name: '',
      offer_type: 'general',
      discount_percentage: '',
      start_date: start,
      end_date: end,
      status: 'active',
    })
    setShowAddModal(true)
  }

  const handleEdit = (offer) => {
    setEditingOffer(offer)
    setValidityPreset('custom')
    setFormData({
      name: offer.name || '',
      offer_type: offer.offer_type || 'general',
      discount_percentage: offer.discount_percentage ?? '',
      start_date: (offer.start_date || '').slice(0, 10),
      end_date: (offer.end_date || '').slice(0, 10),
      status: offer.status || 'active',
    })
    setShowAddModal(true)
  }

  const handleDelete = async (offerId) => {
    if (!window.confirm('Deactivate this offer? It will no longer apply to new bills.')) return
    try {
      const response = await apiDelete(`/api/offers/${offerId}`)
      if (response.ok) {
        showSuccess('Offer deactivated')
        fetchOffers()
      } else {
        const error = await response.json().catch(() => ({}))
        showError(error.error || 'Failed to deactivate offer')
      }
    } catch (error) {
      console.error('Error deactivating offer:', error)
      showError('Error deactivating offer')
    }
  }

  const handleValidityPreset = (preset) => {
    setValidityPreset(preset)
    if (preset === 'custom') return
    const { start, end } = addDuration(preset)
    setFormData(prev => ({ ...prev, start_date: start, end_date: end }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()

    if (!formData.name.trim()) {
      showError('Offer name is required')
      return
    }
    const pct = parseFloat(formData.discount_percentage)
    if (Number.isNaN(pct) || pct < 0 || pct > 100) {
      showError('Discount percentage must be between 0 and 100')
      return
    }
    if (!formData.start_date || !formData.end_date) {
      showError('Start and end dates are required')
      return
    }
    if (new Date(formData.end_date) < new Date(formData.start_date)) {
      showError('End date must be on or after start date')
      return
    }

    const payload = {
      name: formData.name.trim(),
      offer_type: formData.offer_type,
      discount_percentage: pct,
      start_date: formData.start_date,
      end_date: formData.end_date,
      status: formData.status,
    }

    try {
      const response = editingOffer
        ? await apiPut(`/api/offers/${editingOffer.id}`, payload)
        : await apiPost('/api/offers', payload)
      if (response.ok) {
        showSuccess(editingOffer ? 'Offer updated' : 'Offer created')
        setShowAddModal(false)
        fetchOffers()
      } else {
        const error = await response.json().catch(() => ({}))
        showError(error.error || 'Failed to save offer')
      }
    } catch (error) {
      console.error('Error saving offer:', error)
      showError('Error saving offer')
    }
  }

  const visibleOffers = showInactive
    ? offers
    : offers.filter(o => o.status !== 'inactive')
  const inactiveCount = offers.filter(o => o.status === 'inactive').length

  return (
    <div className="membership-page">
      <Header title="Offer Management" />
      <div className="membership-container">
        <div className="membership-card">
          <div className="membership-section-header">
            <h2 className="section-title">Offers</h2>
            <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
              {inactiveCount > 0 && (
                <label style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 6,
                  fontSize: 13,
                  color: '#6b7280',
                  cursor: 'pointer',
                  userSelect: 'none',
                }}>
                  <input
                    type="checkbox"
                    checked={showInactive}
                    onChange={(e) => setShowInactive(e.target.checked)}
                    style={{ margin: 0, cursor: 'pointer' }}
                  />
                  Show inactive ({inactiveCount})
                </label>
              )}
              <button className="add-membership-btn" onClick={handleAddNew}>
                <FaPlus style={{ marginRight: 6 }} /> Add New Offer
              </button>
            </div>
          </div>

          {loading ? (
            <div className="loading-message">Loading...</div>
          ) : (
            <div className="table-wrapper">
              <table className="membership-table">
                <thead>
                  <tr>
                    <th>No.</th>
                    <th>Name</th>
                    <th>Type</th>
                    <th>Discount</th>
                    <th>Start</th>
                    <th>End</th>
                    <th>Status</th>
                    <th>Live</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {visibleOffers.length === 0 ? (
                    <tr>
                      <td colSpan="9" className="empty-row">
                        {offers.length === 0
                          ? 'No offers found. Click "Add New Offer" to create one.'
                          : 'No active offers. Tick "Show inactive" to see deactivated offers.'}
                      </td>
                    </tr>
                  ) : (
                    visibleOffers.map((offer, index) => (
                      <tr key={offer.id}>
                        <td>{index + 1}</td>
                        <td>
                          <div style={{ fontWeight: 600 }}>{offer.name}</div>
                        </td>
                        <td>
                          <span className={`status-badge ${offer.offer_type === 'membership' ? 'active' : 'inactive'}`}>
                            {offer.offer_type === 'membership' ? 'Membership' : 'General'}
                          </span>
                        </td>
                        <td>{Number(offer.discount_percentage || 0).toFixed(2)}%</td>
                        <td>{formatDate(offer.start_date)}</td>
                        <td>{formatDate(offer.end_date)}</td>
                        <td>
                          <span className={`status-badge ${offer.status}`}>{offer.status}</span>
                        </td>
                        <td>
                          {(() => {
                            const live = getLiveState(offer)
                            return <span className={`status-badge ${live.cls}`}>{live.label}</span>
                          })()}
                        </td>
                        <td>
                          <div className="action-icons">
                            <button className="icon-btn edit-btn" title="Edit" onClick={() => handleEdit(offer)}>
                              <FaEdit />
                            </button>
                            <button className="icon-btn delete-btn" title="Deactivate" onClick={() => handleDelete(offer.id)}>
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

      {showAddModal && createPortal(
        <div className="modal-overlay" onClick={() => setShowAddModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header-wrapper">
              <h2>{editingOffer ? 'Edit Offer' : 'Add New Offer'}</h2>
              <button type="button" className="modal-close-button" onClick={() => setShowAddModal(false)} aria-label="Close modal">
                <FaTimes />
              </button>
            </div>
            <form onSubmit={handleSubmit}>
              <div className="modal-form-fields">
                <div className="form-group">
                  <label>Name *</label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder="e.g., Summer Special 20% off"
                    required
                  />
                </div>
                <div className="form-group">
                  <label>Offer Type *</label>
                  <CompactSelect
                    value={formData.offer_type}
                    onChange={(v) => setFormData({ ...formData, offer_type: v })}
                    options={TYPE_OPTIONS}
                    placeholder="Offer type"
                  />
                </div>
                <div className="form-group">
                  <label>Discount (%) *</label>
                  <input
                    type="number"
                    step="0.1"
                    min="0"
                    max="100"
                    value={formData.discount_percentage}
                    onChange={(e) => setFormData({ ...formData, discount_percentage: e.target.value })}
                    required
                  />
                </div>
                <div className="form-group">
                  <label>Validity</label>
                  <CompactSelect
                    value={validityPreset}
                    onChange={handleValidityPreset}
                    options={VALIDITY_PRESET_OPTIONS}
                    placeholder="Validity"
                  />
                </div>
                <div className="form-group">
                  <label>Start Date *</label>
                  <input
                    type="date"
                    value={formData.start_date}
                    onChange={(e) => {
                      setValidityPreset('custom')
                      setFormData({ ...formData, start_date: e.target.value })
                    }}
                    required
                  />
                </div>
                <div className="form-group">
                  <label>End Date *</label>
                  <input
                    type="date"
                    value={formData.end_date}
                    onChange={(e) => {
                      setValidityPreset('custom')
                      setFormData({ ...formData, end_date: e.target.value })
                    }}
                    required
                  />
                </div>
                <div className="form-group">
                  <label>Status</label>
                  <CompactSelect
                    value={formData.status}
                    onChange={(v) => setFormData({ ...formData, status: v })}
                    options={STATUS_OPTIONS}
                    placeholder="Status"
                  />
                </div>
              </div>
              <div className="modal-actions">
                <button type="button" className="btn-cancel" onClick={() => setShowAddModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn-save">
                  {editingOffer ? 'Update' : 'Create'}
                </button>
              </div>
            </form>
          </div>
        </div>,
        document.body
      )}
    </div>
  )
}

export default OfferManagement
