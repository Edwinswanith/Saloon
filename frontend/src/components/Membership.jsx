import React, { useState, useEffect, useMemo } from 'react'
import { createPortal } from 'react-dom'
import {
  FaEdit,
  FaTrash,
  FaPlus,
  FaTimes,
  FaSearch,
  FaCheck,
} from 'react-icons/fa'
import './Membership.css'
import { apiGet, apiPost, apiPut, apiDelete } from '../utils/api'
import { useAuth } from '../contexts/AuthContext'
import { showWarning, showSuccess, showError } from '../utils/toast.jsx'
import CompactSelect from './shared/CompactSelect'

const STATUS_OPTIONS = [
  { value: 'active', label: 'Active' },
  { value: 'inactive', label: 'Inactive' },
]

/**
 * Memberships screen — per-plan master-detail layout.
 *
 * LEFT: list of plans. Click a plan to select it.
 * RIGHT: the selected plan's summary + a flat checkbox list of every active
 *        service. Tick the services this plan should discount, then save.
 *
 * The plan's metadata (name, price, validity, % off, etc.) is still edited in
 * a small modal — `Add New` and the per-row Edit button both open it. Service
 * coverage lives ONLY on the right panel: one place, one save.
 */
const Membership = () => {
  const { currentBranch, branches } = useAuth()
  const [membershipPlans, setMembershipPlans] = useState([])
  const [services, setServices] = useState([])
  const [loading, setLoading] = useState(true)

  // Master-detail selection
  const [selectedPlanId, setSelectedPlanId] = useState(null)
  // Working list of service IDs for the right panel (unsaved edits).
  const [coverageDraftIds, setCoverageDraftIds] = useState([])
  // Snapshot when the plan was selected — used for dirty check + the legacy
  // "covers all → specific" transition warning.
  const [coverageInitialIds, setCoverageInitialIds] = useState([])
  const [coverageSearch, setCoverageSearch] = useState('')
  const [coverageSaving, setCoverageSaving] = useState(false)

  // Metadata modal (create / edit basic plan info — name, price, validity etc.)
  const [showAddModal, setShowAddModal] = useState(false)
  const [editingPlan, setEditingPlan] = useState(null)
  const [formData, setFormData] = useState({
    name: '',
    validity: '',
    price: '',
    allocatedDiscount: '',
    status: 'active',
    description: '',
    branch_id: '',
  })

  useEffect(() => {
    fetchMembershipPlans()
    fetchServices()
  }, [currentBranch])

  // Listen for branch changes
  useEffect(() => {
    const handleBranchChange = () => {
      fetchMembershipPlans()
      fetchServices()
    }
    window.addEventListener('branchChanged', handleBranchChange)
    return () => window.removeEventListener('branchChanged', handleBranchChange)
  }, [currentBranch])

  const fetchServices = async () => {
    try {
      const response = await apiGet('/api/services?per_page=1000')
      if (!response.ok) throw new Error('Failed to fetch services')
      const json = await response.json()
      const list = Array.isArray(json) ? json : (json.data || json.services || [])
      setServices(list)
    } catch (error) {
      console.error('Error fetching services:', error)
      setServices([])
    }
  }

  const fetchMembershipPlans = async () => {
    try {
      setLoading(true)
      const response = await apiGet('/api/membership-plans')
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      const data = await response.json()
      const plans = Array.isArray(data) ? data : (data.plans || [])
      setMembershipPlans(plans)
    } catch (error) {
      console.error('Error fetching membership plans:', error)
      setMembershipPlans([])
    } finally {
      setLoading(false)
    }
  }

  // Pull the currently selected plan from the list (so we always see the
  // freshest values after a save/reload, without separate state).
  const selectedPlan = useMemo(
    () => membershipPlans.find(p => p.id === selectedPlanId) || null,
    [membershipPlans, selectedPlanId]
  )

  // Populate the coverage draft whenever the selected plan changes (or its
  // applicable_services come back updated from a refresh).
  useEffect(() => {
    if (!selectedPlan) {
      setCoverageDraftIds([])
      setCoverageInitialIds([])
      return
    }
    const ids = Array.isArray(selectedPlan.applicable_services)
      ? selectedPlan.applicable_services.map(s => s.id)
      : []
    setCoverageDraftIds(ids)
    setCoverageInitialIds(ids)
    setCoverageSearch('')
  }, [selectedPlanId, selectedPlan])

  const isCoverageDirty = useMemo(() => {
    if (coverageDraftIds.length !== coverageInitialIds.length) return true
    const initialSet = new Set(coverageInitialIds)
    return coverageDraftIds.some(id => !initialSet.has(id))
  }, [coverageDraftIds, coverageInitialIds])

  // Multi-branch produces one Service row per (name × branch). Owners think in
  // terms of "service names" not "service IDs", so we collapse by lowercase
  // name and treat all branch-variants of the same name as a single togglable
  // unit. Ticking a name adds EVERY underlying ID to the coverage list, so the
  // discount applies regardless of which branch's copy of the service ends up
  // on a bill.
  const serviceGroups = useMemo(() => {
    const map = new Map()
    for (const s of services) {
      const rawName = (s.name || '').trim()
      if (!rawName) continue
      const key = rawName.toLowerCase()
      if (!map.has(key)) {
        map.set(key, { name: rawName, ids: [], priceMin: null, priceMax: null, branchCount: 0 })
      }
      const group = map.get(key)
      group.ids.push(s.id)
      const price = parseFloat(s.price)
      if (!Number.isNaN(price)) {
        group.priceMin = group.priceMin == null ? price : Math.min(group.priceMin, price)
        group.priceMax = group.priceMax == null ? price : Math.max(group.priceMax, price)
      }
    }
    // Count distinct non-null branchIds per group (or fall back to ids.length
    // for legacy services without branch attribution).
    for (const s of services) {
      const key = ((s.name || '').trim()).toLowerCase()
      if (!map.has(key)) continue
      const group = map.get(key)
      group._branchSet = group._branchSet || new Set()
      if (s.branchId) group._branchSet.add(s.branchId)
    }
    return Array.from(map.values())
      .map(g => ({
        name: g.name,
        ids: g.ids,
        priceMin: g.priceMin,
        priceMax: g.priceMax,
        branchCount: g._branchSet ? g._branchSet.size : g.ids.length,
      }))
      .sort((a, b) => a.name.localeCompare(b.name))
  }, [services])

  const filteredServiceGroups = useMemo(() => {
    if (!coverageSearch) return serviceGroups
    const q = coverageSearch.toLowerCase()
    return serviceGroups.filter(g => g.name.toLowerCase().includes(q))
  }, [serviceGroups, coverageSearch])

  const draftIdsSet = useMemo(() => new Set(coverageDraftIds), [coverageDraftIds])
  const isGroupChecked = (group) => group.ids.some(id => draftIdsSet.has(id))

  // ── Plan metadata create/edit (modal) ───────────────────────────────────
  const handleAddNew = () => {
    setEditingPlan(null)
    setFormData({
      name: '',
      validity: '',
      price: '',
      allocatedDiscount: '',
      status: 'active',
      description: '',
      branch_id: currentBranch?.id || '',
    })
    setShowAddModal(true)
  }

  const handleEditMeta = (plan) => {
    setEditingPlan(plan)
    setFormData({
      name: plan.name,
      validity: plan.validity,
      price: plan.price,
      allocatedDiscount: plan.allocatedDiscount,
      status: plan.status,
      description: plan.description || '',
      branch_id: plan.branch_id || '',
    })
    setShowAddModal(true)
  }

  const handleSubmitMeta = async (e) => {
    e.preventDefault()
    try {
      const payload = {
        name: formData.name,
        validity: parseInt(formData.validity),
        price: parseFloat(formData.price),
        allocatedDiscount: parseFloat(formData.allocatedDiscount) || 0,
        status: formData.status,
        description: formData.description,
        branch_id: formData.branch_id || null,
      }
      // NOTE: we deliberately do NOT send applicable_service_ids here — the
      // coverage editor on the right panel owns that. This way the modal can
      // never accidentally clear the coverage list.
      const response = editingPlan
        ? await apiPut(`/api/membership-plans/${editingPlan.id}`, payload)
        : await apiPost('/api/membership-plans', payload)

      if (response.ok) {
        const result = await response.json().catch(() => ({}))
        setShowAddModal(false)
        await fetchMembershipPlans()
        // Newly created plan? Auto-select it so the user can immediately
        // configure its services on the right panel.
        if (!editingPlan && result.id) {
          setSelectedPlanId(result.id)
        }
        showSuccess(editingPlan ? 'Plan updated' : 'Plan created — pick the services it covers on the right')
      } else {
        const error = await response.json().catch(() => ({}))
        showError(error.error || 'Failed to save membership plan')
      }
    } catch (error) {
      console.error('Error saving membership plan:', error)
      showError('Error saving membership plan')
    }
  }

  const handleDelete = async (planId) => {
    if (!window.confirm('Delete this membership plan?')) return
    try {
      const response = await apiDelete(`/api/membership-plans/${planId}`)
      if (response.ok) {
        if (selectedPlanId === planId) setSelectedPlanId(null)
        await fetchMembershipPlans()
        showSuccess('Plan deleted')
      } else {
        const error = await response.json().catch(() => ({}))
        showError(error.error || 'Failed to delete membership plan')
      }
    } catch (error) {
      console.error('Error deleting membership plan:', error)
      showError('Error deleting membership plan')
    }
  }

  // ── Coverage editing (right panel) ──────────────────────────────────────
  // Toggling a name flips every underlying branch-variant of that service so
  // the plan covers it consistently across all branches.
  // The decision must mirror the chip's visual `checked` state (`isGroupChecked`
  // uses `.some()`): if ANY variant is currently selected, the chip looks
  // checked, so a click on it must always deselect — even if only some
  // variants are in the draft. Otherwise the user clicks a checked-looking
  // chip and the system mysteriously adds *more* services instead of removing.
  const toggleCoverageGroup = (group) => {
    const anyIn = group.ids.some(id => draftIdsSet.has(id))
    if (anyIn) {
      const removeSet = new Set(group.ids)
      setCoverageDraftIds(prev => prev.filter(id => !removeSet.has(id)))
    } else {
      setCoverageDraftIds(prev => Array.from(new Set([...prev, ...group.ids])))
    }
  }

  const selectAllVisible = () => {
    const visibleIds = filteredServiceGroups.flatMap(g => g.ids)
    setCoverageDraftIds(prev => Array.from(new Set([...prev, ...visibleIds])))
  }

  const clearAllVisible = () => {
    const visibleIds = new Set(filteredServiceGroups.flatMap(g => g.ids))
    setCoverageDraftIds(prev => prev.filter(id => !visibleIds.has(id)))
  }

  const resetCoverage = () => {
    setCoverageDraftIds(coverageInitialIds)
  }

  const saveCoverage = async () => {
    if (!selectedPlan) return

    // Legacy "covers all" → specific-services transition warning.
    if (coverageInitialIds.length === 0 && coverageDraftIds.length > 0) {
      showWarning(
        `This plan was previously covering ALL services. It will now ONLY discount the ${coverageDraftIds.length} service(s) you picked. Existing customers holding this plan will see a smaller discount on services not in the list.`
      )
    }

    setCoverageSaving(true)
    try {
      const response = await apiPut(`/api/membership-plans/${selectedPlan.id}`, {
        applicable_service_ids: coverageDraftIds,
      })
      if (response.ok) {
        await fetchMembershipPlans()
        showSuccess('Coverage saved')
      } else {
        const error = await response.json().catch(() => ({}))
        showError(error.error || 'Failed to save coverage')
      }
    } catch (error) {
      console.error('Error saving coverage:', error)
      showError('Error saving coverage')
    } finally {
      setCoverageSaving(false)
    }
  }

  // ── Render ──────────────────────────────────────────────────────────────
  return (
    <div className="membership-page">
      <div className="membership-container">
        <div className="membership-header-bar">
          <h2 className="membership-page-title">Memberships</h2>
          <button className="add-membership-btn" onClick={handleAddNew}>
            <FaPlus size={12} style={{ marginRight: 6 }} />
            New Plan
          </button>
        </div>

        <div className="membership-master-detail">
          {/* ── LEFT: plan list ─────────────────────────────────────── */}
          <aside className="membership-list-pane">
            <div className="membership-list-pane-title">
              {membershipPlans.length} plan{membershipPlans.length === 1 ? '' : 's'}
            </div>
            {loading ? (
              <div className="membership-pane-empty">Loading…</div>
            ) : membershipPlans.length === 0 ? (
              <div className="membership-pane-empty">
                No membership plans yet. Click <strong>New Plan</strong> to add one.
              </div>
            ) : (
              <ul className="membership-plan-list">
                {membershipPlans.map(plan => {
                  const isActive = selectedPlanId === plan.id
                  const coveredCount = Array.isArray(plan.applicable_services)
                    ? plan.applicable_services.length
                    : 0
                  const coverageLabel = coveredCount === 0
                    ? 'All services'
                    : `${coveredCount} service${coveredCount === 1 ? '' : 's'}`
                  return (
                    <li key={plan.id}>
                      <button
                        className={`membership-plan-row ${isActive ? 'active' : ''}`}
                        onClick={() => setSelectedPlanId(plan.id)}
                      >
                        <div className="membership-plan-row-name">
                          {plan.name}
                          <span className={`status-badge ${plan.status}`}>{plan.status}</span>
                        </div>
                        <div className="membership-plan-row-meta">
                          <span>{plan.allocatedDiscount}% off</span>
                          <span>·</span>
                          <span>{coverageLabel}</span>
                        </div>
                      </button>
                    </li>
                  )
                })}
              </ul>
            )}
          </aside>

          {/* ── RIGHT: coverage editor for the selected plan ────────── */}
          <section className="membership-detail-pane">
            {!selectedPlan ? (
              <div className="membership-detail-empty">
                <div className="membership-detail-empty-icon">🎟</div>
                <div className="membership-detail-empty-title">Pick a plan</div>
                <div className="membership-detail-empty-sub">
                  Select a membership on the left to manage which services it discounts.
                </div>
              </div>
            ) : (
              <>
                {/* Plan summary card */}
                <div className="membership-summary-card">
                  <div className="membership-summary-main">
                    <div className="membership-summary-name">
                      {selectedPlan.name}
                      <span className={`status-badge ${selectedPlan.status}`}>{selectedPlan.status}</span>
                    </div>
                    <div className="membership-summary-meta">
                      <span><strong>{selectedPlan.allocatedDiscount}%</strong> off</span>
                      <span>·</span>
                      <span>₹{Number(selectedPlan.price).toFixed(2)}</span>
                      <span>·</span>
                      <span>{selectedPlan.validity} days</span>
                      <span>·</span>
                      <span>{selectedPlan.branch_name || 'All branches'}</span>
                    </div>
                    {selectedPlan.description && (
                      <div className="membership-summary-desc">{selectedPlan.description}</div>
                    )}
                  </div>
                  <div className="membership-summary-actions">
                    <button
                      className="icon-btn edit-btn"
                      title="Edit plan details"
                      onClick={() => handleEditMeta(selectedPlan)}
                    >
                      <FaEdit /> <span>Edit</span>
                    </button>
                    <button
                      className="icon-btn delete-btn"
                      title="Delete plan"
                      onClick={() => handleDelete(selectedPlan.id)}
                    >
                      <FaTrash /> <span>Delete</span>
                    </button>
                  </div>
                </div>

                {/* Coverage editor */}
                <div className="membership-coverage-section">
                  <div className="membership-coverage-header">
                    <div>
                      <h3 className="membership-coverage-title">Services covered by this plan</h3>
                      <p className="membership-coverage-hint">
                        {(() => {
                          const checkedGroupCount = serviceGroups.filter(isGroupChecked).length
                          if (checkedGroupCount === 0) {
                            return <>No services ticked — this plan applies <strong>no discount</strong> yet. Tick the services it should discount.</>
                          }
                          return <>Tick services this plan should discount. Customers holding this membership will get <strong>{selectedPlan.allocatedDiscount}% off</strong> on the ticked services only.</>
                        })()}
                      </p>
                    </div>
                    <div className="membership-coverage-counter">
                      {serviceGroups.filter(isGroupChecked).length} of {serviceGroups.length} ticked
                    </div>
                  </div>

                  <div className="membership-coverage-toolbar">
                    <div className="membership-search-wrap">
                      <FaSearch className="membership-search-icon" />
                      <input
                        type="text"
                        className="membership-search-input"
                        placeholder="Search services…"
                        value={coverageSearch}
                        onChange={e => setCoverageSearch(e.target.value)}
                      />
                    </div>
                    <button className="membership-link-btn" onClick={selectAllVisible} disabled={filteredServiceGroups.length === 0}>
                      Select all{coverageSearch ? ' visible' : ''}
                    </button>
                    <button className="membership-link-btn" onClick={clearAllVisible} disabled={filteredServiceGroups.length === 0}>
                      Clear all{coverageSearch ? ' visible' : ''}
                    </button>
                  </div>

                  <div className="membership-services-grid">
                    {serviceGroups.length === 0 ? (
                      <div className="membership-pane-empty">
                        No services found. Add services from the Services screen first.
                      </div>
                    ) : filteredServiceGroups.length === 0 ? (
                      <div className="membership-pane-empty">No services match your search.</div>
                    ) : (
                      filteredServiceGroups.map(group => {
                        const checked = isGroupChecked(group)
                        const priceLabel = group.priceMin == null
                          ? null
                          : (group.priceMin === group.priceMax
                            ? `₹${group.priceMin}`
                            : `₹${group.priceMin}–${group.priceMax}`)
                        return (
                          <label
                            key={group.name}
                            className={`membership-service-chip ${checked ? 'checked' : ''}`}
                          >
                            <input
                              type="checkbox"
                              checked={checked}
                              onChange={() => toggleCoverageGroup(group)}
                            />
                            <span className="membership-service-chip-name">
                              {group.name}
                              {group.branchCount > 1 && (
                                <span style={{
                                  marginLeft: 6,
                                  fontSize: 10,
                                  fontWeight: 500,
                                  color: '#9ca3af',
                                }}>
                                  · {group.branchCount} branches
                                </span>
                              )}
                            </span>
                            {priceLabel && (
                              <span className="membership-service-chip-price">{priceLabel}</span>
                            )}
                            {checked && <FaCheck className="membership-service-chip-check" />}
                          </label>
                        )
                      })
                    )}
                  </div>
                </div>

                {/* Save bar — appears only when there are unsaved changes */}
                {isCoverageDirty && (
                  <div className="membership-save-bar">
                    <span>You have unsaved changes</span>
                    <div className="membership-save-bar-actions">
                      <button className="btn-cancel" onClick={resetCoverage} disabled={coverageSaving}>
                        Discard
                      </button>
                      <button className="btn-save" onClick={saveCoverage} disabled={coverageSaving}>
                        {coverageSaving ? 'Saving…' : 'Save Coverage'}
                      </button>
                    </div>
                  </div>
                )}
              </>
            )}
          </section>
        </div>
      </div>

      {/* Plan-metadata modal — basic info only. Service coverage lives on the
          right panel and is NOT touched by this modal. */}
      {showAddModal && createPortal(
        <div className="modal-overlay" onClick={() => setShowAddModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header-wrapper">
              <h2>{editingPlan ? 'Edit Plan' : 'New Membership Plan'}</h2>
              <button
                type="button"
                className="modal-close-button"
                onClick={() => setShowAddModal(false)}
                aria-label="Close modal"
              >
                <FaTimes />
              </button>
            </div>
            <form onSubmit={handleSubmitMeta}>
              <div className="modal-form-fields">
                <div className="form-group">
                  <label>Name *</label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    required
                  />
                </div>
                <div className="form-group">
                  <label>Validity (Days) *</label>
                  <input
                    type="number"
                    value={formData.validity}
                    onChange={(e) => setFormData({ ...formData, validity: e.target.value })}
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
                    onChange={(e) => setFormData({ ...formData, price: e.target.value })}
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
                    onChange={(e) => setFormData({ ...formData, allocatedDiscount: e.target.value })}
                    min="0"
                    max="100"
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
                <div className="form-group">
                  <label>Branch</label>
                  <CompactSelect
                    value={formData.branch_id}
                    onChange={(v) => setFormData({ ...formData, branch_id: v })}
                    options={[{ value: '', label: 'All Branches' }, ...branches.map((b) => ({ value: b.id, label: b.name }))]}
                    placeholder="All Branches"
                  />
                </div>
                <div className="form-group" style={{ gridColumn: '1 / -1' }}>
                  <label>Description</label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    rows="3"
                  />
                </div>
                <div className="form-group" style={{
                  gridColumn: '1 / -1',
                  background: '#f0fdfa',
                  border: '1px solid rgba(13, 148, 136, 0.2)',
                  borderRadius: 6,
                  padding: '10px 12px',
                  fontSize: 12,
                  color: '#0f766e',
                }}>
                  <strong>Tip:</strong> {editingPlan
                    ? 'Pick which services this plan covers on the right panel after closing this modal.'
                    : 'After creating this plan, pick the services it covers on the right panel.'}
                </div>
              </div>
              <div className="modal-actions">
                <button
                  type="button"
                  className="btn-cancel"
                  onClick={() => setShowAddModal(false)}
                >
                  Cancel
                </button>
                <button type="submit" className="btn-save">
                  {editingPlan ? 'Update' : 'Create'}
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

export default Membership
