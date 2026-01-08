import React, { useState, useEffect } from 'react'
import {
  FaCloudUploadAlt,
  FaPlus,
  FaCloudDownloadAlt,
  FaEdit,
  FaTrash,
} from 'react-icons/fa'
import * as XLSX from 'xlsx'
import './AssetManagement.css'
import { API_BASE_URL } from '../config'
import { useAuth } from '../contexts/AuthContext'

const AssetManagement = () => {
  const { currentBranch } = useAuth()
  const [assets, setAssets] = useState([])
  const [loading, setLoading] = useState(true)
  const [showAssetModal, setShowAssetModal] = useState(false)
  const [showUploadModal, setShowUploadModal] = useState(false)
  const [editingAsset, setEditingAsset] = useState(null)
  const [assetFormData, setAssetFormData] = useState({
    name: '',
    category: '',
    location: '',
    purchase_price: '',
    purchase_date: '',
    current_value: '',
    depreciation_rate: '',
    status: 'active',
    description: ''
  })


  useEffect(() => {
    fetchAssets()
  }, [currentBranch])

  // Listen for branch changes
  useEffect(() => {
    const handleBranchChange = () => {
      console.log('[AssetManagement] Branch changed, refreshing assets...')
      fetchAssets()
    }
    
    window.addEventListener('branchChanged', handleBranchChange)
    return () => window.removeEventListener('branchChanged', handleBranchChange)
  }, [currentBranch])

  const fetchAssets = async () => {
    try {
      setLoading(true)
      const response = await fetch(`${API_BASE_URL}/api/assets`)
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      const data = await response.json()
      // Backend returns array directly
      setAssets(Array.isArray(data) ? data : (data.assets || []))
    } catch (error) {
      console.error('Error fetching assets:', error)
      setAssets([])
    } finally {
      setLoading(false)
    }
  }

  const handleAddAsset = () => {
    setEditingAsset(null)
    setAssetFormData({
      name: '',
      category: '',
      location: '',
      purchase_price: '',
      purchase_date: '',
      current_value: '',
      depreciation_rate: '',
      status: 'active',
      description: ''
    })
    setShowAssetModal(true)
  }

  const handleEditAsset = async (asset) => {
    setEditingAsset(asset)
    setAssetFormData({
      name: asset.name || '',
      category: asset.category || '',
      location: asset.location || '',
      purchase_price: asset.purchase_price || '',
      purchase_date: asset.purchase_date ? asset.purchase_date.split('T')[0] : '',
      current_value: asset.current_value || '',
      depreciation_rate: asset.depreciation_rate || '',
      status: asset.status || 'active',
      description: asset.description || ''
    })
    setShowAssetModal(true)
  }

  const handleSaveAsset = async () => {
    if (!assetFormData.name.trim()) {
      alert('Asset name is required')
      return
    }

    try {
      const url = editingAsset 
        ? `${API_BASE_URL}/api/assets/${editingAsset.id}`
        : `${API_BASE_URL}/api/assets`
      const method = editingAsset ? 'PUT' : 'POST'

      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: assetFormData.name.trim(),
          category: assetFormData.category.trim(),
          location: assetFormData.location.trim(),
          purchase_price: parseFloat(assetFormData.purchase_price) || 0,
          purchase_date: assetFormData.purchase_date || null,
          current_value: parseFloat(assetFormData.current_value) || null,
          depreciation_rate: parseFloat(assetFormData.depreciation_rate) || null,
          status: assetFormData.status,
          description: assetFormData.description.trim()
        }),
      })

      if (response.ok) {
        const data = await response.json()
        fetchAssets()
        setShowAssetModal(false)
        setEditingAsset(null)
        setAssetFormData({
          name: '',
          category: '',
          location: '',
          purchase_price: '',
          purchase_date: '',
          current_value: '',
          depreciation_rate: '',
          status: 'active',
          description: ''
        })
        alert(data.message || (editingAsset ? 'Asset updated successfully!' : 'Asset added successfully!'))
      } else {
        const errorData = await response.json().catch(() => ({ error: 'Unknown error' }))
        alert(errorData.error || `Failed to save asset (Status: ${response.status})`)
      }
    } catch (error) {
      console.error('Error saving asset:', error)
      alert(`Error saving asset: ${error.message}`)
    }
  }

  const handleDelete = async (assetId) => {
    if (!window.confirm('Are you sure you want to delete this asset?')) {
      return
    }
    try {
      const response = await fetch(`${API_BASE_URL}/api/assets/${assetId}`, {
        method: 'DELETE',
      })
      if (response.ok) {
        fetchAssets()
        alert('Asset deleted successfully')
      } else {
        const errorData = await response.json().catch(() => ({ error: 'Unknown error' }))
        alert(errorData.error || 'Failed to delete asset')
      }
    } catch (error) {
      console.error('Error deleting asset:', error)
      alert(`Error deleting asset: ${error.message}`)
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
            const workbook = XLSX.read(data, { type: 'binary' })
            const sheetName = workbook.SheetNames[0]
            const worksheet = workbook.Sheets[sheetName]
            rows = XLSX.utils.sheet_to_json(worksheet, { header: 1, defval: '' })
          } else {
            const text = data
            const lines = text.split('\n')
            rows = lines.map(line => {
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

  const handleUploadFile = async (e) => {
    const file = e.target.files[0]
    if (!file) return

    try {
      const rows = await parseFile(file)
      if (rows.length < 2) {
        alert('File must contain at least a header row and one data row')
        return
      }

      const headers = rows[0].map(h => String(h).trim().toLowerCase())
      
      const nameIdx = headers.findIndex(h => h.includes('name'))
      const categoryIdx = headers.findIndex(h => h.includes('category'))
      const locationIdx = headers.findIndex(h => h.includes('location') || h.includes('owner'))
      const priceIdx = headers.findIndex(h => h.includes('price') || h.includes('purchase'))
      const dateIdx = headers.findIndex(h => h.includes('date') || h.includes('purchase date'))
      const statusIdx = headers.findIndex(h => h.includes('status'))

      if (nameIdx === -1) {
        alert('File must contain Name column')
        return
      }

      let successCount = 0
      let errorCount = 0

      for (let i = 1; i < rows.length; i++) {
        if (!rows[i] || rows[i].length === 0) continue
        
        const values = rows[i]
        const assetData = {
          name: String(values[nameIdx] || '').trim(),
          category: categoryIdx >= 0 ? String(values[categoryIdx] || '').trim() : '',
          location: locationIdx >= 0 ? String(values[locationIdx] || '').trim() : '',
          purchase_price: priceIdx >= 0 ? parseFloat(values[priceIdx] || '0') : 0,
          purchase_date: dateIdx >= 0 ? String(values[dateIdx] || '').trim() : null,
          status: statusIdx >= 0 ? String(values[statusIdx] || 'active').trim().toLowerCase() : 'active',
        }

        if (assetData.name) {
          try {
            const response = await fetch(`${API_BASE_URL}/api/assets`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify(assetData),
            })
            if (response.ok) {
              successCount++
            } else {
              errorCount++
            }
          } catch (err) {
            console.error(`Error importing asset ${i}:`, err)
            errorCount++
          }
        } else {
          errorCount++
        }
      }
      
      alert(`Assets imported: ${successCount} successful, ${errorCount} failed`)
      setShowUploadModal(false)
      fetchAssets()
    } catch (error) {
      console.error('Error processing import file:', error)
      alert(`Error processing import file: ${error.message}`)
    }
  }

  const handleDownloadReport = () => {
    try {
      const csvContent = [
        ['Asset Name', 'Category', 'Owner/Location', 'Purchase Price', 'Purchase Date', 'Current Value', 'Status'],
        ...assets.map(asset => [
          asset.name || 'N/A',
          asset.category || 'N/A',
          asset.location || 'Unassigned',
          asset.purchase_price ? `₹${asset.purchase_price.toFixed(2)}` : 'N/A',
          asset.purchase_date ? asset.purchase_date.split('T')[0] : 'N/A',
          asset.current_value ? `₹${asset.current_value.toFixed(2)}` : 'N/A',
          asset.status || 'active',
        ])
      ].map(row => {
        return row.map(cell => {
          const cellStr = String(cell || '')
          if (cellStr.includes(',') || cellStr.includes('"') || cellStr.includes('\n')) {
            return `"${cellStr.replace(/"/g, '""')}"`
          }
          return cellStr
        }).join(',')
      }).join('\n')
      
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      const fileName = `assets-report-${new Date().toISOString().split('T')[0]}.csv`
      a.download = fileName
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      window.URL.revokeObjectURL(url)
    } catch (error) {
      console.error('Error downloading report:', error)
      alert('Error downloading report. Please try again.')
    }
  }

  return (
    <div className="asset-management-page">
      <div className="asset-management-container">
        {/* Asset Management Card */}
        <div className="asset-management-card">
          {/* Section Header */}
          <div className="asset-section-header">
            <h2 className="section-title">Asset Management</h2>
            <div className="action-buttons">
              <button className="action-btn upload-btn" onClick={() => setShowUploadModal(true)}>
                <FaCloudUploadAlt />
                Upload Assets
              </button>
              <button className="action-btn add-btn" onClick={handleAddAsset}>
                <FaPlus />
                Add New Asset
              </button>
              <button className="action-btn download-btn" onClick={handleDownloadReport}>
                <FaCloudDownloadAlt />
                Download Report
              </button>
            </div>
          </div>

          {/* Asset Table */}
          <div className="table-container">
            <table className="asset-table">
              <thead>
                <tr>
                  <th>Asset Name</th>
                  <th>Owner</th>
                  <th>Qty</th>
                  <th>Purchase Price</th>
                  <th>Warranty Expiry</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan="7" className="empty-row">Loading...</td>
                  </tr>
                ) : assets.length === 0 ? (
                  <tr>
                    <td colSpan="7" className="empty-row">No assets found</td>
                  </tr>
                ) : (
                  assets.map((asset) => (
                    <tr key={asset.id}>
                      <td className="asset-name">{asset.name}</td>
                      <td>{asset.location || 'Unassigned'}</td>
                      <td>-</td>
                      <td>₹{(asset.purchase_price || 0).toFixed(2)}</td>
                      <td>{asset.purchase_date ? asset.purchase_date.split('T')[0] : 'N/A'}</td>
                      <td>
                        <span
                          className={`status-badge ${asset.status || 'active'}`}
                        >
                          {asset.status || 'active'}
                        </span>
                      </td>
                      <td>
                        <div className="action-icons">
                          <button 
                            className="icon-btn edit-btn" 
                            title="Edit"
                            onClick={() => handleEditAsset(asset)}
                          >
                            <FaEdit />
                          </button>
                          <button
                            className="icon-btn delete-btn"
                            title="Delete"
                            onClick={() => handleDelete(asset.id)}
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

      {/* Add/Edit Asset Modal */}
      {showAssetModal && (
        <div className="modal-overlay" onClick={() => setShowAssetModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2>{editingAsset ? 'Edit Asset' : 'Add New Asset'}</h2>
            <div className="form-group">
              <label>Asset Name *</label>
              <input
                type="text"
                value={assetFormData.name}
                onChange={(e) => setAssetFormData({ ...assetFormData, name: e.target.value })}
                placeholder="Enter asset name"
                required
              />
            </div>
            <div className="form-group">
              <label>Category</label>
              <input
                type="text"
                value={assetFormData.category}
                onChange={(e) => setAssetFormData({ ...assetFormData, category: e.target.value })}
                placeholder="Enter category"
              />
            </div>
            <div className="form-group">
              <label>Owner/Location</label>
              <input
                type="text"
                value={assetFormData.location}
                onChange={(e) => setAssetFormData({ ...assetFormData, location: e.target.value })}
                placeholder="Enter location or owner"
              />
            </div>
            <div className="form-group">
              <label>Purchase Price</label>
              <input
                type="number"
                step="0.01"
                value={assetFormData.purchase_price}
                onChange={(e) => setAssetFormData({ ...assetFormData, purchase_price: e.target.value })}
                placeholder="0.00"
              />
            </div>
            <div className="form-group">
              <label>Purchase Date</label>
              <input
                type="date"
                value={assetFormData.purchase_date}
                onChange={(e) => setAssetFormData({ ...assetFormData, purchase_date: e.target.value })}
              />
            </div>
            <div className="form-group">
              <label>Current Value</label>
              <input
                type="number"
                step="0.01"
                value={assetFormData.current_value}
                onChange={(e) => setAssetFormData({ ...assetFormData, current_value: e.target.value })}
                placeholder="0.00"
              />
            </div>
            <div className="form-group">
              <label>Depreciation Rate (%)</label>
              <input
                type="number"
                step="0.01"
                value={assetFormData.depreciation_rate}
                onChange={(e) => setAssetFormData({ ...assetFormData, depreciation_rate: e.target.value })}
                placeholder="0.00"
              />
            </div>
            <div className="form-group">
              <label>Status</label>
              <select
                value={assetFormData.status}
                onChange={(e) => setAssetFormData({ ...assetFormData, status: e.target.value })}
              >
                <option value="active">Active</option>
                <option value="disposed">Disposed</option>
                <option value="maintenance">Maintenance</option>
              </select>
            </div>
            <div className="form-group">
              <label>Description</label>
              <textarea
                value={assetFormData.description}
                onChange={(e) => setAssetFormData({ ...assetFormData, description: e.target.value })}
                placeholder="Enter asset description..."
                rows="3"
              />
            </div>
            <div className="modal-actions">
              <button className="btn-cancel" onClick={() => setShowAssetModal(false)}>Cancel</button>
              <button className="btn-save" onClick={handleSaveAsset}>Save</button>
            </div>
          </div>
        </div>
      )}

      {/* Upload Assets Modal */}
      {showUploadModal && (
        <div className="modal-overlay" onClick={() => setShowUploadModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2>Upload Assets</h2>
            <div className="import-instructions">
              <p>Upload a CSV or Excel file (.csv, .xlsx, .xls) with the following columns:</p>
              <ul>
                <li>Name (required)</li>
                <li>Category (optional)</li>
                <li>Location/Owner (optional)</li>
                <li>Purchase Price (optional)</li>
                <li>Purchase Date (optional - format: YYYY-MM-DD)</li>
                <li>Status (optional - active/disposed/maintenance)</li>
              </ul>
            </div>
            <div className="form-group">
              <label>Select File</label>
              <input
                type="file"
                accept=".csv,.xlsx,.xls"
                onChange={handleUploadFile}
              />
            </div>
            <div className="modal-actions">
              <button className="btn-cancel" onClick={() => setShowUploadModal(false)}>Cancel</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default AssetManagement

