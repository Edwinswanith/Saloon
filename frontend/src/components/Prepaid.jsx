import React, { useState, useEffect } from 'react'
import {
  FaEdit,
  FaTrash,
  FaPlus,
  FaArrowsAltV,
  FaChevronDown,
  FaCloudUploadAlt,
} from 'react-icons/fa'
import * as XLSX from 'xlsx'
import './Prepaid.css'
import { API_BASE_URL } from '../config'
import { useAuth } from '../contexts/AuthContext'

const Prepaid = () => {
  const { currentBranch } = useAuth()
  const [searchQuery, setSearchQuery] = useState('')
  const [prepaidGroups, setPrepaidGroups] = useState([])
  const [loading, setLoading] = useState(true)
  const [showGroupModal, setShowGroupModal] = useState(false)
  const [showImportModal, setShowImportModal] = useState(false)
  const [editingGroup, setEditingGroup] = useState(null)
  const [groupFormData, setGroupFormData] = useState({ name: '' })

  useEffect(() => {
    fetchPrepaidGroups()
  }, [currentBranch])

  // Listen for branch changes
  useEffect(() => {
    const handleBranchChange = () => {
      console.log('[Prepaid] Branch changed, refreshing prepaid groups...')
      fetchPrepaidGroups()
    }
    
    window.addEventListener('branchChanged', handleBranchChange)
    return () => window.removeEventListener('branchChanged', handleBranchChange)
  }, [currentBranch])

  const fetchPrepaidGroups = async () => {
    try {
      setLoading(true)
      const response = await fetch(`${API_BASE_URL}/api/prepaid/groups`)
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      const data = await response.json()
      // Backend returns array directly
      setPrepaidGroups(Array.isArray(data) ? data : (data.groups || []))
    } catch (error) {
      console.error('Error fetching prepaid groups:', error)
      setPrepaidGroups([])
    } finally {
      setLoading(false)
    }
  }

  const handleAddGroup = () => {
    setEditingGroup(null)
    setGroupFormData({ name: '' })
    setShowGroupModal(true)
  }

  const handleEditGroup = (group) => {
    setEditingGroup(group)
    setGroupFormData({ name: group.name })
    setShowGroupModal(true)
  }

  const handleSaveGroup = async () => {
    if (!groupFormData.name.trim()) {
      alert('Group name is required')
      return
    }

    try {
      const url = editingGroup 
        ? `${API_BASE_URL}/api/prepaid/groups/${editingGroup.id}`
        : `${API_BASE_URL}/api/prepaid/groups`
      const method = editingGroup ? 'PUT' : 'POST'

      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: groupFormData.name.trim()
        }),
      })

      if (response.ok) {
        const data = await response.json()
        fetchPrepaidGroups()
        setShowGroupModal(false)
        setEditingGroup(null)
        setGroupFormData({ name: '' })
        alert(data.message || (editingGroup ? 'Prepaid group updated successfully!' : 'Prepaid group added successfully!'))
      } else {
        const errorData = await response.json().catch(() => ({ error: 'Unknown error' }))
        alert(errorData.error || `Failed to save prepaid group (Status: ${response.status})`)
      }
    } catch (error) {
      console.error('Error saving prepaid group:', error)
      alert(`Error saving prepaid group: ${error.message}`)
    }
  }

  const handleDeleteGroup = async (groupId) => {
    if (!window.confirm('Are you sure you want to delete this prepaid group?')) {
      return
    }
    try {
      const response = await fetch(`${API_BASE_URL}/api/prepaid/groups/${groupId}`, {
        method: 'DELETE',
      })
      if (response.ok) {
        fetchPrepaidGroups()
        alert('Prepaid group deleted successfully')
      } else {
        const error = await response.json().catch(() => ({ error: 'Unknown error' }))
        alert(error.error || 'Failed to delete prepaid group')
      }
    } catch (error) {
      console.error('Error deleting prepaid group:', error)
      alert(`Error deleting prepaid group: ${error.message}`)
    }
  }

  const parseFile = async (file) => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.onload = (e) => {
        try {
          const data = e.target.result
          let rows = []

          if (file.name.endsWith('.xlsx') || file.name.endsWith('.xls')) {
            // Parse Excel file
            const workbook = XLSX.read(data, { type: 'binary' })
            const sheetName = workbook.SheetNames[0]
            const worksheet = workbook.Sheets[sheetName]
            rows = XLSX.utils.sheet_to_json(worksheet, { header: 1, defval: '' })
          } else {
            // Parse CSV file
            const text = data
            const lines = text.split('\n')
            rows = lines.map(line => {
              // Handle CSV with quoted values
              const values = []
              let current = ''
              let inQuotes = false
              for (let i = 0; i < line.length; i++) {
                const char = line[i]
                if (char === '"') {
                  inQuotes = !inQuotes
                } else if (char === ',' && !inQuotes) {
                  values.push(current.trim())
                  current = ''
                } else {
                  current += char
                }
              }
              values.push(current.trim())
              return values
            })
          }

          resolve(rows)
        } catch (error) {
          reject(error)
        }
      }
      reader.onerror = reject

      if (file.name.endsWith('.xlsx') || file.name.endsWith('.xls')) {
        reader.readAsBinaryString(file)
      } else {
        reader.readAsText(file)
      }
    })
  }

  const handleImportFile = async (e) => {
    const file = e.target.files[0]
    if (!file) return

    try {
      const rows = await parseFile(file)
      if (rows.length < 2) {
        alert('File must contain at least a header row and one data row')
        return
      }

      const headers = rows[0].map(h => String(h).trim().toLowerCase())
      
      // Find column indices
      const nameIdx = headers.findIndex(h => h.includes('name'))
      const groupIdx = headers.findIndex(h => h.includes('group'))
      const priceIdx = headers.findIndex(h => h.includes('price'))
      const expiryIdx = headers.findIndex(h => h.includes('expiry') || h.includes('expire'))

      if (nameIdx === -1 || priceIdx === -1) {
        alert('File must contain Name and Price columns')
        return
      }

      let successCount = 0
      let errorCount = 0

      // Process data rows
      for (let i = 1; i < rows.length; i++) {
        if (!rows[i] || rows[i].length === 0) continue
        
        const values = rows[i]
        const prepaidData = {
          name: String(values[nameIdx] || '').trim(),
          price: parseFloat(values[priceIdx] || '0'),
          group_id: null,
          expiry_date: null
        }

        // Find or create group
        if (groupIdx >= 0 && values[groupIdx]) {
          const groupName = String(values[groupIdx]).trim()
          const existingGroup = prepaidGroups.find(g => g.name.toLowerCase() === groupName.toLowerCase())
          if (existingGroup) {
            prepaidData.group_id = existingGroup.id
          } else {
            // Create new group
            try {
              const groupResponse = await fetch(`${API_BASE_URL}/api/prepaid/groups`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: groupName }),
              })
              if (groupResponse.ok) {
                const groupData = await groupResponse.json()
                prepaidData.group_id = groupData.id || groupData.data?.id
                // Refresh groups
                fetchPrepaidGroups()
              }
            } catch (err) {
              console.error(`Error creating group ${i}:`, err)
            }
          }
        }

        // Handle expiry date
        if (expiryIdx >= 0 && values[expiryIdx]) {
          const expiryStr = String(values[expiryIdx]).trim()
          if (expiryStr) {
            try {
              // Try to parse date (supports various formats)
              const expiryDate = new Date(expiryStr)
              if (!isNaN(expiryDate.getTime())) {
                prepaidData.expiry_date = expiryDate.toISOString()
              }
            } catch (err) {
              console.error(`Error parsing expiry date ${i}:`, err)
            }
          }
        }

        if (prepaidData.name && prepaidData.price > 0) {
          try {
            const response = await fetch(`${API_BASE_URL}/api/prepaid/packages`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify(prepaidData),
            })
            if (response.ok) {
              successCount++
            } else {
              errorCount++
            }
          } catch (err) {
            console.error(`Error importing prepaid package ${i}:`, err)
            errorCount++
          }
        } else {
          errorCount++
        }
      }
      
      alert(`Prepaid packages imported: ${successCount} successful, ${errorCount} failed`)
      setShowImportModal(false)
      fetchPrepaidGroups()
    } catch (error) {
      console.error('Error processing import file:', error)
      alert(`Error processing import file: ${error.message}`)
    }
  }

  return (
    <div className="prepaid-page">
      <div className="prepaid-container">
        {/* Prepaid Card */}
        <div className="prepaid-card">
          {/* Section Header */}
          <div className="prepaid-section-header">
            <h2 className="section-title">Prepaid List</h2>
            <div className="action-buttons">
              <button className="action-btn import-btn" onClick={() => setShowImportModal(true)}>
                <FaCloudUploadAlt /> Import Prepaid
              </button>
              <button className="action-btn add-btn" onClick={handleAddGroup}>Add Prepaid Group</button>
            </div>
          </div>

          {/* Prepaid Groups List */}
          <div className="prepaid-groups-list">
            {loading ? (
              <div className="loading-message">Loading prepaid groups...</div>
            ) : prepaidGroups.length === 0 ? (
              <div className="empty-message">No prepaid groups found</div>
            ) : (
              prepaidGroups.map((group) => (
                <div key={group.id} className="prepaid-group-row">
                  <div className="group-info">
                    <span className="group-name">{group.name}</span>
                  </div>
                  <div className="group-actions">
                    <button 
                      className="icon-btn edit-btn" 
                      title="Edit"
                      onClick={() => handleEditGroup(group)}
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
                      title="Add"
                      onClick={() => alert('Add prepaid package functionality coming soon')}
                    >
                      <FaPlus />
                    </button>
                    <button className="icon-btn reorder-btn" title="Reorder">
                      <FaArrowsAltV />
                    </button>
                    <button className="icon-btn expand-btn" title="Expand">
                      <FaChevronDown />
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Add/Edit Prepaid Group Modal */}
      {showGroupModal && (
        <div className="modal-overlay" onClick={() => setShowGroupModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2>{editingGroup ? 'Edit Prepaid Group' : 'Add Prepaid Group'}</h2>
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

      {/* Import Prepaid Modal */}
      {showImportModal && (
        <div className="modal-overlay" onClick={() => setShowImportModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2>Import Prepaid Packages</h2>
            <div className="import-instructions">
              <p>Upload a CSV or Excel file (.csv, .xlsx, .xls) with the following columns:</p>
              <ul>
                <li>Name (required)</li>
                <li>Group (optional - will create if doesn't exist)</li>
                <li>Price (required)</li>
                <li>Expiry Date (optional - format: YYYY-MM-DD or any valid date format)</li>
              </ul>
            </div>
            <div className="form-group">
              <label>Select File</label>
              <input
                type="file"
                accept=".csv,.xlsx,.xls"
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

export default Prepaid

