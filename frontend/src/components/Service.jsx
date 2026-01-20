import React, { useState, useEffect } from 'react'
import {
  FaEdit,
  FaTrash,
  FaPlus,
  FaArrowsAltV,
  FaChevronDown,
  FaCloudUploadAlt,
  FaSearch,
  FaTimes,
} from 'react-icons/fa'
import './Service.css'
import { apiGet, apiPost, apiPut, apiDelete } from '../utils/api'
import { showSuccess, showError, showWarning } from '../utils/toast.jsx'
import { useAuth } from '../contexts/AuthContext'
import Header from './Header'

const Service = () => {
  const { currentBranch } = useAuth()
  const [searchQuery, setSearchQuery] = useState('')
  const [serviceGroups, setServiceGroups] = useState([])
  const [loading, setLoading] = useState(true)
  const [expandedGroups, setExpandedGroups] = useState({})
  const [servicesByGroup, setServicesByGroup] = useState({})
  const [showGroupModal, setShowGroupModal] = useState(false)
  const [showServiceModal, setShowServiceModal] = useState(false)
  const [showImportModal, setShowImportModal] = useState(false)
  const [editingGroup, setEditingGroup] = useState(null)
  const [editingService, setEditingService] = useState(null)
  const [selectedGroupId, setSelectedGroupId] = useState(null)
  const [showGroupDropdown, setShowGroupDropdown] = useState(false)
  const [groupFormData, setGroupFormData] = useState({ name: '' })
  const [serviceFormData, setServiceFormData] = useState({
    name: '',
    price: '',
    duration: '',
    description: '',
    groupId: ''
  })

  useEffect(() => {
    fetchServiceGroups()
  }, [])

  // Listen for branch changes
  useEffect(() => {
    const handleBranchChange = () => {
      console.log('[Service] Branch changed, refreshing service groups...')
      fetchServiceGroups()
      setServicesByGroup({}) // Clear services cache
    }
    
    window.addEventListener('branchChanged', handleBranchChange)
    return () => window.removeEventListener('branchChanged', handleBranchChange)
  }, [currentBranch])

  useEffect(() => {
    if (Object.keys(expandedGroups).length > 0) {
      Object.keys(expandedGroups).forEach((groupId) => {
        if (expandedGroups[groupId] && !servicesByGroup[groupId]) {
          fetchServicesForGroup(groupId)
        }
      })
    }
  }, [expandedGroups])

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (showGroupDropdown && !event.target.closest('.custom-dropdown-wrapper')) {
        setShowGroupDropdown(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [showGroupDropdown])

  const fetchServiceGroups = async () => {
    try {
      setLoading(true)
      const response = await apiGet('/api/services/groups')
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      const responseData = await response.json()
      console.log('[Service] Service groups API response:', responseData)
      
      // Backend returns {groups: [...]} format
      const groupsList = responseData.groups || (Array.isArray(responseData) ? responseData : [])
      setServiceGroups(groupsList)
      console.log('[Service] Service groups loaded:', groupsList.length)
    } catch (error) {
      console.error('[Service] Error fetching service groups:', error)
      setServiceGroups([])
    } finally {
      setLoading(false)
    }
  }

  const fetchServicesForGroup = async (groupId) => {
    try {
      const response = await apiGet(`/api/services?group_id=${groupId}`)
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      const responseData = await response.json()
      console.log(`[Service] Services for group ${groupId} response:`, responseData)
      
      // Backend returns {data: [...], pagination: {...}}
      const servicesList = responseData.data || (Array.isArray(responseData) ? responseData : (responseData.services || []))
      console.log(`[Service] Loaded ${servicesList.length} services for group ${groupId}`)
      
      setServicesByGroup((prev) => ({
        ...prev,
        [groupId]: servicesList,
      }))
    } catch (error) {
      console.error(`[Service] Error fetching services for group ${groupId}:`, error)
      setServicesByGroup((prev) => ({
        ...prev,
        [groupId]: [],
      }))
    }
  }

  const toggleGroup = (groupId) => {
    setExpandedGroups((prev) => ({
      ...prev,
      [groupId]: !prev[groupId],
    }))
  }

  const handleDeleteGroup = async (groupId) => {
    if (!window.confirm('Are you sure you want to delete this service group?')) {
      return
    }
    try {
      const response = await apiDelete(`/api/services/groups/${groupId}`)
      if (response.ok) {
        fetchServiceGroups()
        showSuccess('Service group deleted successfully')
      } else {
        const errorData = await response.json().catch(() => ({ error: 'Unknown error' }))
        showError(errorData.error || 'Failed to delete service group')
      }
    } catch (error) {
      console.error('Error deleting service group:', error)
      showError(`Error deleting service group: ${error.message}`)
    }
  }

  const handleSaveGroup = async () => {
    if (!groupFormData.name.trim()) {
      showError('Group name is required')
      return
    }

    try {
      const groupData = {
        name: groupFormData.name.trim(),
        displayOrder: editingGroup?.displayOrder || 0
      }

      const response = editingGroup
        ? await apiPut(`/api/services/groups/${editingGroup.id}`, groupData)
        : await apiPost('/api/services/groups', groupData)

      if (response.ok) {
        const data = await response.json()
        fetchServiceGroups()
        setShowGroupModal(false)
        setEditingGroup(null)
        setGroupFormData({ name: '' })
        showSuccess(data.message || (editingGroup ? 'Service group updated successfully!' : 'Service group added successfully!'))
      } else {
        const errorData = await response.json().catch(() => ({ error: 'Unknown error' }))
        showError(errorData.error || `Failed to save service group (Status: ${response.status})`)
      }
    } catch (error) {
      console.error('Error saving service group:', error)
      showError(`Error saving service group: ${error.message}`)
    }
  }

  const handleSaveService = async () => {
    if (!serviceFormData.name.trim()) {
      showError('Service name is required')
      return
    }
    if (!serviceFormData.groupId) {
      showError('Service group is required')
      return
    }
    if (!serviceFormData.price || parseFloat(serviceFormData.price) <= 0) {
      showError('Valid price is required')
      return
    }

    try {
      const serviceData = {
        name: serviceFormData.name.trim(),
        groupId: serviceFormData.groupId,
        price: parseFloat(serviceFormData.price) || 0,
        duration: serviceFormData.duration || null,
        description: serviceFormData.description || '',
        status: 'active'
      }

      const response = editingService
        ? await apiPut(`/api/services/${editingService.id}`, serviceData)
        : await apiPost('/api/services', serviceData)

      if (response.ok) {
        const data = await response.json()
        if (serviceFormData.groupId) {
          fetchServicesForGroup(serviceFormData.groupId)
        }
        fetchServiceGroups()
        setShowServiceModal(false)
        setEditingService(null)
        setSelectedGroupId(null)
        setShowGroupDropdown(false)
        setServiceFormData({
          name: '',
          price: '',
          duration: '',
          description: '',
          groupId: ''
        })
        showSuccess(data.message || (editingService ? 'Service updated successfully!' : 'Service added successfully!'))
      } else {
        const errorData = await response.json().catch(() => ({ error: 'Unknown error' }))
        showError(errorData.error || `Failed to save service (Status: ${response.status})`)
      }
    } catch (error) {
      console.error('Error saving service:', error)
      showError(`Error saving service: ${error.message}`)
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
        const headers = lines[0].split(',').map(h => h.trim().toLowerCase())
        
        // Find column indices
        const nameIdx = headers.findIndex(h => h.includes('name'))
        const groupIdx = headers.findIndex(h => h.includes('group'))
        const priceIdx = headers.findIndex(h => h.includes('price'))
        const durationIdx = headers.findIndex(h => h.includes('duration'))

        if (nameIdx === -1 || priceIdx === -1) {
          showError('CSV must contain Name and Price columns')
          return
        }

        let successCount = 0
        let errorCount = 0

        // Skip header row and process data
        for (let i = 1; i < lines.length; i++) {
          if (!lines[i].trim()) continue
          const values = lines[i].split(',').map(v => v.trim())
          
          const serviceData = {
            name: values[nameIdx] || '',
            price: values[priceIdx] || '0',
            duration: durationIdx >= 0 ? (values[durationIdx] || '') : '',
          }

          // Find or create group
          if (groupIdx >= 0 && values[groupIdx]) {
            const groupName = values[groupIdx]
            // Try to find existing group
            const existingGroup = serviceGroups.find(g => g.name.toLowerCase() === groupName.toLowerCase())
            if (existingGroup) {
              serviceData.groupId = existingGroup.id
            } else {
              // Create new group
              try {
                const groupResponse = await apiPost('/api/services/groups', { name: groupName })
                if (groupResponse.ok) {
                  const groupData = await groupResponse.json()
                  serviceData.groupId = groupData.id
                }
              } catch (err) {
                console.error(`Error creating group ${i}:`, err)
              }
            }
          }

          if (serviceData.name && serviceData.price) {
            try {
              const response = await apiPost('/api/services', serviceData)
              if (response.ok) {
                successCount++
              } else {
                errorCount++
              }
            } catch (err) {
              console.error(`Error importing service ${i}:`, err)
              errorCount++
            }
          }
        }
        
        showError(`Services imported: ${successCount} successful, ${errorCount} failed`)
        setShowImportModal(false)
        fetchServiceGroups()
      } catch (error) {
        console.error('Error processing import file:', error)
        showError('Error processing import file')
      }
    }
    reader.readAsText(file)
  }

  const filteredGroups = serviceGroups.filter((group) =>
    group.name.toLowerCase().includes(searchQuery.toLowerCase())
  )

  return (
    <div className="service-page">
      <Header title="Services" />
      
      <div className="service-container">
        {/* Service Card */}
        <div className="service-card">
          {/* Search and Action Bar */}
          <div className="service-action-bar">
            <div className="search-wrapper">
              <FaSearch className="search-icon" />
              <input
                type="text"
                className="search-input"
                placeholder="Search services or groups..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
              {searchQuery && (
                <button 
                  className="search-clear"
                  onClick={() => setSearchQuery('')}
                  title="Clear search"
                >
                  <FaTimes />
                </button>
              )}
            </div>
            <div className="action-buttons">
              <button className="action-btn import-btn" onClick={() => setShowImportModal(true)}>
                <FaCloudUploadAlt /> Import Services
              </button>
              <button className="action-btn add-btn" onClick={() => {
                setEditingGroup(null)
                setGroupFormData({ name: '' })
                setShowGroupModal(true)
              }}>
                <FaPlus /> Add Service Group
              </button>
            </div>
          </div>

          {/* Service Groups List */}
          <div className="service-groups-list">
            {loading ? (
              <div className="loading-message">Loading service groups...</div>
            ) : filteredGroups.length === 0 ? (
              <div className="empty-message">No service groups found</div>
            ) : (
              filteredGroups.map((group) => (
                <div key={group.id}>
                  <div className="service-group-row">
                    <div className="group-info">
                      <span className="group-name">
                        {group.name} ({group.count})
                      </span>
                    </div>
                    <div className="group-actions">
                      <button
                        className="icon-btn edit-btn"
                        title="Edit"
                        onClick={() => {
                          setEditingGroup(group)
                          setGroupFormData({ name: group.name })
                          setShowGroupModal(true)
                        }}
                      >
                        <FaEdit size={16} color="#3b82f6" />
                      </button>
                      <button
                        className="icon-btn delete-btn"
                        title="Delete"
                        onClick={() => handleDeleteGroup(group.id)}
                      >
                        <FaTrash size={16} color="#ef4444" />
                      </button>
                      <button
                        className="icon-btn add-btn"
                        title="Add Service"
                        onClick={() => {
                          setEditingService(null)
                          setSelectedGroupId(group.id)
                          setServiceFormData({
                            name: '',
                            price: '',
                            duration: '',
                            description: '',
                            groupId: group.id
                          })
                          setShowServiceModal(true)
                        }}
                      >
                        <FaPlus size={16} color="#ffffff" />
                      </button>
                      <button className="icon-btn reorder-btn" title="Reorder">
                        <FaArrowsAltV size={16} color="#6b7280" />
                      </button>
                      <button
                        className={`icon-btn expand-btn ${expandedGroups[group.id] ? 'expanded' : ''}`}
                        title="Expand"
                        onClick={() => toggleGroup(group.id)}
                      >
                        <FaChevronDown size={16} color="#0F766E" />
                      </button>
                    </div>
                  </div>
                  {expandedGroups[group.id] && servicesByGroup[group.id] && (
                    <div className="services-list">
                      {servicesByGroup[group.id].length === 0 ? (
                        <div className="empty-services">No services in this group</div>
                      ) : (
                        <div className="services-grid">
                      {servicesByGroup[group.id].map((service) => (
                            <div key={service.id} className="service-item-card">
                              <div className="service-card-header">
                                <span className="service-card-name">{service.name}</span>
                              </div>
                              <div className="service-card-details">
                                <span className="service-card-price">₹{parseFloat(service.price).toLocaleString('en-IN')}</span>
                                {service.duration && (
                                  <span className="service-card-duration">{service.duration} min</span>
                                )}
                              </div>
                              <div className="service-card-actions">
                            <button
                              className="icon-btn edit-btn"
                              title="Edit"
                              onClick={() => {
                                setEditingService(service)
                                setSelectedGroupId(service.groupId || group.id)
                                setServiceFormData({
                                  name: service.name || '',
                                  price: service.price || '',
                                  duration: service.duration || '',
                                  description: service.description || '',
                                  groupId: service.groupId || group.id
                                })
                                setShowServiceModal(true)
                              }}
                            >
                              <FaEdit size={14} color="#3b82f6" />
                            </button>
                            <button
                              className="icon-btn delete-btn"
                              title="Delete"
                              onClick={async () => {
                                if (!window.confirm('Are you sure you want to delete this service?')) {
                                  return
                                }
                                try {
                                  const response = await apiDelete(`/api/services/${service.id}`)
                                  if (response.ok) {
                                    fetchServicesForGroup(group.id)
                                    fetchServiceGroups()
                                    showSuccess('Service deleted successfully')
                                  } else {
                                    showError('Failed to delete service')
                                  }
                                } catch (error) {
                                  console.error('Error deleting service:', error)
                                  showError('Error deleting service')
                                }
                              }}
                            >
                              <FaTrash size={14} color="#ef4444" />
                            </button>
                          </div>
                        </div>
                      ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Add/Edit Service Group Modal */}
      {showGroupModal && (
        <div className="modal-overlay" onClick={() => setShowGroupModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2>{editingGroup ? 'Edit Service Group' : 'Add Service Group'}</h2>
            <div className="form-group">
              <label>Group Name *</label>
              <input
                type="text"
                value={groupFormData.name}
                onChange={(e) => setGroupFormData({ ...groupFormData, name: e.target.value })}
                placeholder="Enter group name"
                required
              />
            </div>
            <div className="modal-actions">
              <button className="btn-cancel" onClick={() => setShowGroupModal(false)}>Cancel</button>
              <button className="btn-save" onClick={handleSaveGroup}>Save</button>
            </div>
          </div>
        </div>
      )}

      {/* Add/Edit Service Modal */}
      {showServiceModal && (
        <div className="modal-overlay" onClick={() => {
          setShowServiceModal(false)
          setShowGroupDropdown(false)
        }}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2>{editingService ? 'Edit Service' : 'Add Service'}</h2>
            <div className="form-group">
              <label>Service Name *</label>
              <input
                type="text"
                value={serviceFormData.name}
                onChange={(e) => setServiceFormData({ ...serviceFormData, name: e.target.value })}
                placeholder="Enter service name"
                required
              />
            </div>
            <div className="form-group">
              <label>Service Group *</label>
              <div className="custom-dropdown-wrapper">
                <button
                  type="button"
                  className="custom-dropdown-toggle"
                  onClick={() => setShowGroupDropdown(!showGroupDropdown)}
                >
                  <span>
                    {serviceFormData.groupId 
                      ? serviceGroups.find(g => g.id === serviceFormData.groupId)?.name || 'Select Group'
                      : 'Select Group'
                    }
                  </span>
                  <FaChevronDown className={`dropdown-arrow ${showGroupDropdown ? 'open' : ''}`} />
                </button>
                {showGroupDropdown && (
                  <div className="custom-dropdown-menu">
                    <div
                      className={`custom-dropdown-option ${!serviceFormData.groupId ? 'selected' : ''}`}
                      onClick={() => {
                        setServiceFormData({ ...serviceFormData, groupId: '' })
                        setShowGroupDropdown(false)
                      }}
                    >
                      Select Group
                    </div>
                {serviceGroups.map(group => (
                      <div
                        key={group.id}
                        className={`custom-dropdown-option ${serviceFormData.groupId === group.id ? 'selected' : ''}`}
                        onClick={() => {
                          setServiceFormData({ ...serviceFormData, groupId: group.id })
                          setShowGroupDropdown(false)
                        }}
                      >
                        {group.name}
                      </div>
                ))}
                  </div>
                )}
              </div>
            </div>
            <div className="form-group">
              <label>Price *</label>
              <input
                type="number"
                step="0.01"
                value={serviceFormData.price}
                onChange={(e) => setServiceFormData({ ...serviceFormData, price: e.target.value })}
                placeholder="0.00"
                required
              />
            </div>
            <div className="form-group">
              <label>Duration (minutes)</label>
              <input
                type="number"
                value={serviceFormData.duration}
                onChange={(e) => setServiceFormData({ ...serviceFormData, duration: e.target.value })}
                placeholder="30"
              />
            </div>
            <div className="form-group">
              <label>Description</label>
              <textarea
                value={serviceFormData.description}
                onChange={(e) => setServiceFormData({ ...serviceFormData, description: e.target.value })}
                placeholder="Enter service description..."
                rows="3"
              />
            </div>
            <div className="modal-actions">
              <button className="btn-cancel" onClick={() => {
                setShowServiceModal(false)
                setShowGroupDropdown(false)
              }}>Cancel</button>
              <button className="btn-save" onClick={handleSaveService}>Save</button>
            </div>
          </div>
        </div>
      )}

      {/* Import Services Modal */}
      {showImportModal && (
        <div className="modal-overlay" onClick={() => setShowImportModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2>Import Services</h2>
            <div className="import-instructions">
              <p>Upload a CSV file with the following columns:</p>
              <ul>
                <li>Name (required)</li>
                <li>Group (optional - will create if doesn't exist)</li>
                <li>Price (required)</li>
                <li>Duration (optional)</li>
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
    </div>
  )
}

export default Service

