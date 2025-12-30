import React, { useState, useEffect } from 'react'
import {
  FaBars,
  FaBell,
  FaUser,
  FaEdit,
  FaTrash,
  FaPlus,
  FaArrowsAltV,
  FaChevronDown,
  FaCloudUploadAlt,
} from 'react-icons/fa'
import './Service.css'
import { API_BASE_URL } from '../config'
import { showSuccess, showError, showWarning } from '../utils/toast.jsx'

const Service = () => {
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

  useEffect(() => {
    if (Object.keys(expandedGroups).length > 0) {
      Object.keys(expandedGroups).forEach((groupId) => {
        if (expandedGroups[groupId] && !servicesByGroup[groupId]) {
          fetchServicesForGroup(groupId)
        }
      })
    }
  }, [expandedGroups])

  const fetchServiceGroups = async () => {
    try {
      setLoading(true)
      const response = await fetch(`${API_BASE_URL}/api/services/groups`)
      const data = await response.json()
      setServiceGroups(data.groups || [])
    } catch (error) {
      console.error('Error fetching service groups:', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchServicesForGroup = async (groupId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/services?group_id=${groupId}`)
      const data = await response.json()
      setServicesByGroup((prev) => ({
        ...prev,
        [groupId]: data.services || [],
      }))
    } catch (error) {
      console.error('Error fetching services:', error)
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
      const response = await fetch(`${API_BASE_URL}/api/services/groups/${groupId}`, {
        method: 'DELETE',
      })
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
      const url = editingGroup 
        ? `${API_BASE_URL}/api/services/groups/${editingGroup.id}`
        : `${API_BASE_URL}/api/services/groups`
      const method = editingGroup ? 'PUT' : 'POST'

      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: groupFormData.name.trim(),
          displayOrder: editingGroup?.displayOrder || 0
        }),
      })

      if (response.ok) {
        const data = await response.json()
        fetchServiceGroups()
        setShowGroupModal(false)
        setEditingGroup(null)
        setGroupFormData({ name: '' })
        showError(data.message || (editingGroup ? 'Service group updated successfully!' : 'Service group added successfully!'))
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
      const url = editingService 
        ? `${API_BASE_URL}/api/services/${editingService.id}`
        : `${API_BASE_URL}/api/services`
      const method = editingService ? 'PUT' : 'POST'

      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: serviceFormData.name.trim(),
          groupId: serviceFormData.groupId,  // MongoDB ObjectId as string
          price: parseFloat(serviceFormData.price) || 0,
          duration: serviceFormData.duration || null,
          description: serviceFormData.description || '',
          status: 'active'
        }),
      })

      if (response.ok) {
        const data = await response.json()
        if (serviceFormData.groupId) {
          fetchServicesForGroup(serviceFormData.groupId)
        }
        fetchServiceGroups()
        setShowServiceModal(false)
        setEditingService(null)
        setSelectedGroupId(null)
        setServiceFormData({
          name: '',
          price: '',
          duration: '',
          description: '',
          groupId: ''
        })
        showError(data.message || (editingService ? 'Service updated successfully!' : 'Service added successfully!'))
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
                const groupResponse = await fetch(`${API_BASE_URL}/api/services/groups`, {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify({ name: groupName }),
                })
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
              const response = await fetch(`${API_BASE_URL}/api/services`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(serviceData),
              })
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
      {/* Header */}
      <header className="service-header">
        <div className="header-left">
          <button className="menu-icon">
            <FaBars />
          </button>
          <h1 className="header-title">Service</h1>
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

      <div className="service-container">
        {/* Service Card */}
        <div className="service-card">
          {/* Search and Action Bar */}
          <div className="service-action-bar">
            <div className="search-wrapper">
              <input
                type="text"
                className="search-input"
                placeholder="Search services"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
            <div className="action-buttons">
              <button className="action-btn import-btn" onClick={() => setShowImportModal(true)}>
                <FaCloudUploadAlt /> Import Services
              </button>
              <button className="action-btn add-btn" onClick={() => {
                setEditingGroup(null)
                setGroupFormData({ name: '' })
                setShowGroupModal(true)
              }}>Add Service Group</button>
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
                        <FaEdit />
                      </button>
                      <button
                        className="icon-btn delete-btn"
                        title="Delete"
                        onClick={() => handleDeleteGroup(group.id)}
                      >
                        <FaTrash />
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
                        <FaPlus />
                      </button>
                      <button className="icon-btn reorder-btn" title="Reorder">
                        <FaArrowsAltV />
                      </button>
                      <button
                        className={`icon-btn expand-btn ${expandedGroups[group.id] ? 'expanded' : ''}`}
                        title="Expand"
                        onClick={() => toggleGroup(group.id)}
                      >
                        <FaChevronDown />
                      </button>
                    </div>
                  </div>
                  {expandedGroups[group.id] && servicesByGroup[group.id] && (
                    <div className="services-list">
                      {servicesByGroup[group.id].map((service) => (
                        <div key={service.id} className="service-item">
                          <span>{service.name} - ₹{service.price}</span>
                          <div className="service-actions">
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
                              <FaEdit />
                            </button>
                            <button 
                              className="icon-btn delete-btn" 
                              title="Delete"
                              onClick={async () => {
                                if (!window.confirm('Are you sure you want to delete this service?')) {
                                  return
                                }
                                try {
                                  const response = await fetch(`${API_BASE_URL}/api/services/${service.id}`, {
                                    method: 'DELETE',
                                  })
                                  if (response.ok) {
                                    fetchServicesForGroup(group.id)
                                    fetchServiceGroups()
                                  } else {
                                    showError('Failed to delete service')
                                  }
                                } catch (error) {
                                  console.error('Error deleting service:', error)
                                  showError('Error deleting service')
                                }
                              }}
                            >
                              <FaTrash />
                            </button>
                          </div>
                        </div>
                      ))}
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
        <div className="modal-overlay" onClick={() => setShowServiceModal(false)}>
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
              <select
                value={serviceFormData.groupId}
                onChange={(e) => setServiceFormData({ ...serviceFormData, groupId: e.target.value })}
                required
              >
                <option value="">Select Group</option>
                {serviceGroups.map(group => (
                  <option key={group.id} value={group.id}>{group.name}</option>
                ))}
              </select>
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
              <button className="btn-cancel" onClick={() => setShowServiceModal(false)}>Cancel</button>
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

