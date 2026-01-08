import React, { useState, useEffect } from 'react'
import {
  FaEdit,
  FaTrash,
  FaChevronDown,
  FaCloudUploadAlt,
} from 'react-icons/fa'
import * as XLSX from 'xlsx'
import './Package.css'
import { API_BASE_URL } from '../config'
import { useAuth } from '../contexts/AuthContext'

const Package = () => {
  const { currentBranch } = useAuth()
  const [packages, setPackages] = useState([])
  const [loading, setLoading] = useState(true)
  const [showPackageModal, setShowPackageModal] = useState(false)
  const [showImportModal, setShowImportModal] = useState(false)
  const [editingPackage, setEditingPackage] = useState(null)
  const [expandedPackages, setExpandedPackages] = useState({}) // Track which packages are expanded
  const [packageFormData, setPackageFormData] = useState({
    name: '',
    price: '',
    description: '',
    services: []
  })
  const [availableServices, setAvailableServices] = useState([])

  const togglePackageExpand = (packageId) => {
    setExpandedPackages(prev => ({
      ...prev,
      [packageId]: !prev[packageId]
    }))
  }

  useEffect(() => {
    fetchPackages()
    fetchServices()
  }, [currentBranch])

  // Listen for branch changes
  useEffect(() => {
    const handleBranchChange = () => {
      console.log('[Package] Branch changed, refreshing packages...')
      fetchPackages()
      fetchServices()
    }
    
    window.addEventListener('branchChanged', handleBranchChange)
    return () => window.removeEventListener('branchChanged', handleBranchChange)
  }, [currentBranch])

  const fetchServices = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/services`)
      const data = await response.json()
      setAvailableServices(data.services || [])
    } catch (error) {
      console.error('Error fetching services:', error)
    }
  }

  const fetchPackages = async () => {
    try {
      setLoading(true)
      const response = await fetch(`${API_BASE_URL}/api/packages`)
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      const data = await response.json()
      // Backend returns array directly
      setPackages(Array.isArray(data) ? data : (data.packages || []))
    } catch (error) {
      console.error('Error fetching packages:', error)
      setPackages([])
    } finally {
      setLoading(false)
    }
  }

  const handleAddPackage = () => {
    setEditingPackage(null)
    setPackageFormData({
      name: '',
      price: '',
      description: '',
      services: []
    })
    setShowPackageModal(true)
  }

  const handleEditPackage = (pkg) => {
    setEditingPackage(pkg)
    setPackageFormData({
      name: pkg.name || '',
      price: pkg.price || '',
      description: pkg.description || '',
      services: pkg.services ? pkg.services.map(s => s.id || s) : []
    })
    setShowPackageModal(true)
  }

  const handleSavePackage = async () => {
    if (!packageFormData.name.trim()) {
      alert('Package name is required')
      return
    }
    if (!packageFormData.price || parseFloat(packageFormData.price) <= 0) {
      alert('Valid price is required')
      return
    }

    try {
      const url = editingPackage 
        ? `${API_BASE_URL}/api/packages/${editingPackage.id}`
        : `${API_BASE_URL}/api/packages`
      const method = editingPackage ? 'PUT' : 'POST'

      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: packageFormData.name.trim(),
          price: parseFloat(packageFormData.price) || 0,
          description: packageFormData.description || '',
          service_ids: packageFormData.services  // MongoDB ObjectIds as strings, don't parse
        }),
      })

      if (response.ok) {
        const data = await response.json()
        fetchPackages()
        setShowPackageModal(false)
        setEditingPackage(null)
        setPackageFormData({
          name: '',
          price: '',
          description: '',
          services: []
        })
        alert(data.message || (editingPackage ? 'Package updated successfully!' : 'Package added successfully!'))
      } else {
        const errorData = await response.json().catch(() => ({ error: 'Unknown error' }))
        alert(errorData.error || `Failed to save package (Status: ${response.status})`)
      }
    } catch (error) {
      console.error('Error saving package:', error)
      alert(`Error saving package: ${error.message}`)
    }
  }

  const handleDelete = async (packageId) => {
    if (!window.confirm('Are you sure you want to delete this package?')) {
      return
    }
    try {
      const response = await fetch(`${API_BASE_URL}/api/packages/${packageId}`, {
        method: 'DELETE',
      })
      if (response.ok) {
        fetchPackages()
        alert('Package deleted successfully')
      } else {
        const errorData = await response.json().catch(() => ({ error: 'Unknown error' }))
        alert(errorData.error || 'Failed to delete package')
      }
    } catch (error) {
      console.error('Error deleting package:', error)
      alert(`Error deleting package: ${error.message}`)
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
      const priceIdx = headers.findIndex(h => h.includes('price'))
      const descriptionIdx = headers.findIndex(h => h.includes('description'))
      const servicesIdx = headers.findIndex(h => h.includes('service'))

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
        const packageData = {
          name: String(values[nameIdx] || '').trim(),
          price: parseFloat(values[priceIdx] || '0'),
          description: descriptionIdx >= 0 ? String(values[descriptionIdx] || '').trim() : '',
          service_ids: []
        }

        // Handle services if provided
        if (servicesIdx >= 0 && values[servicesIdx]) {
          const serviceNames = String(values[servicesIdx]).split(',').map(s => s.trim())
          packageData.service_ids = availableServices
            .filter(s => serviceNames.includes(s.name))
            .map(s => s.id)
        }

        if (packageData.name && packageData.price > 0) {
          try {
            const response = await fetch(`${API_BASE_URL}/api/packages`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify(packageData),
            })
            if (response.ok) {
              successCount++
            } else {
              errorCount++
            }
          } catch (err) {
            console.error(`Error importing package ${i}:`, err)
            errorCount++
          }
        } else {
          errorCount++
        }
      }
      
      alert(`Packages imported: ${successCount} successful, ${errorCount} failed`)
      setShowImportModal(false)
      fetchPackages()
    } catch (error) {
      console.error('Error processing import file:', error)
      alert(`Error processing import file: ${error.message}`)
    }
  }

  return (
    <div className="package-page">
      <div className="package-container">
        {/* Package Card */}
        <div className="package-card">
          {/* Section Header */}
          <div className="package-section-header">
            <h2 className="section-title">Package List</h2>
            <div className="action-buttons">
              <button className="action-btn import-btn" onClick={() => setShowImportModal(true)}>
                <FaCloudUploadAlt /> Import Packages
              </button>
              <button className="add-package-btn" onClick={handleAddPackage}>Add Package</button>
            </div>
          </div>

          {/* Package List */}
          <div className="package-list">
            {loading ? (
              <div className="loading-message">Loading packages...</div>
            ) : packages.length === 0 ? (
              <div className="empty-message">No packages found</div>
            ) : (
              packages.map((pkg) => (
                <div key={pkg.id} className="package-row-container">
                  <div className="package-row">
                    <div className="package-info">
                      <span className="package-name">
                        {pkg.name} (₹{pkg.price.toFixed(2)})
                      </span>
                      {pkg.service_details && pkg.service_details.length > 0 && (
                        <span className="services-count">
                          {pkg.service_details.length} service{pkg.service_details.length > 1 ? 's' : ''}
                        </span>
                      )}
                    </div>
                    <div className="package-actions">
                      <button 
                        className="icon-btn edit-btn" 
                        title="Edit"
                        onClick={() => handleEditPackage(pkg)}
                      >
                        <FaEdit />
                      </button>
                      <button
                        className="icon-btn delete-btn"
                        title="Delete"
                        onClick={() => handleDelete(pkg.id)}
                      >
                        <FaTrash />
                      </button>
                      <button 
                        className={`icon-btn dropdown-btn ${expandedPackages[pkg.id] ? 'expanded' : ''}`}
                        title="Show services"
                        onClick={() => togglePackageExpand(pkg.id)}
                      >
                        <FaChevronDown />
                      </button>
                    </div>
                  </div>
                  
                  {/* Expandable Services List */}
                  {expandedPackages[pkg.id] && pkg.service_details && pkg.service_details.length > 0 && (
                    <div className="package-services-expanded">
                      <h4>Services in this package:</h4>
                      <div className="services-grid">
                        {pkg.service_details.map((service, idx) => (
                          <div key={idx} className="service-card">
                            <div className="service-card-header">
                              <span className="service-card-name">{service.name}</span>
                            </div>
                            <div className="service-card-details">
                              <span className="service-card-price">₹{service.price}</span>
                              <span className="service-card-duration">{service.duration} min</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  {expandedPackages[pkg.id] && (!pkg.service_details || pkg.service_details.length === 0) && (
                    <div className="package-services-expanded">
                      <p className="no-services-message">No services added to this package yet.</p>
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Add/Edit Package Modal */}
      {showPackageModal && (
        <div className="modal-overlay" onClick={() => setShowPackageModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2>{editingPackage ? 'Edit Package' : 'Add Package'}</h2>
            <div className="form-group">
              <label>Package Name *</label>
              <input
                type="text"
                value={packageFormData.name}
                onChange={(e) => setPackageFormData({ ...packageFormData, name: e.target.value })}
                placeholder="Enter package name"
                required
              />
            </div>
            <div className="form-group">
              <label>Price *</label>
              <input
                type="number"
                step="0.01"
                value={packageFormData.price}
                onChange={(e) => setPackageFormData({ ...packageFormData, price: e.target.value })}
                placeholder="0.00"
                required
              />
            </div>
            <div className="form-group">
              <label>Description</label>
              <textarea
                value={packageFormData.description}
                onChange={(e) => setPackageFormData({ ...packageFormData, description: e.target.value })}
                placeholder="Enter package description..."
                rows="3"
              />
            </div>
            <div className="form-group">
              <label>Services</label>
              <select
                multiple
                value={packageFormData.services}
                onChange={(e) => {
                  const selected = Array.from(e.target.selectedOptions, option => option.value)
                  setPackageFormData({ ...packageFormData, services: selected })
                }}
                style={{ minHeight: '100px' }}
              >
                {availableServices.map(service => (
                  <option key={service.id} value={service.id}>
                    {service.name} - ₹{service.price}
                  </option>
                ))}
              </select>
              <small>Hold Ctrl/Cmd to select multiple services</small>
            </div>
            <div className="modal-actions">
              <button className="btn-cancel" onClick={() => setShowPackageModal(false)}>Cancel</button>
              <button className="btn-save" onClick={handleSavePackage}>Save</button>
            </div>
          </div>
        </div>
      )}

      {/* Import Packages Modal */}
      {showImportModal && (
        <div className="modal-overlay" onClick={() => setShowImportModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2>Import Packages</h2>
            <div className="import-instructions">
              <p>Upload a CSV or Excel file (.csv, .xlsx, .xls) with the following columns:</p>
              <ul>
                <li>Name (required)</li>
                <li>Price (required)</li>
                <li>Description (optional)</li>
                <li>Services (optional - comma-separated service names)</li>
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

export default Package

