import React, { useState, useEffect } from 'react'
import {
  FaBars,
  FaBell,
  FaUser,
  FaEdit,
  FaTrash,
  FaPlus,
  FaCloudUploadAlt,
} from 'react-icons/fa'
import * as XLSX from 'xlsx'
import './Tax.css'
import { API_BASE_URL } from '../config'
const Tax = () => {
  const [settings, setSettings] = useState({
    gstNumber: '',
    servicePricingType: 'inclusive',
    productPricingType: 'exclusive',
    prepaidPricingType: 'inclusive',
  })
  const [taxSlabs, setTaxSlabs] = useState([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')
  const [showSlabModal, setShowSlabModal] = useState(false)
  const [showImportModal, setShowImportModal] = useState(false)
  const [editingSlab, setEditingSlab] = useState(null)
  const [slabFormData, setSlabFormData] = useState({
    name: '',
    rate: '',
    applyToServices: false,
    applyToProducts: false,
    applyToPrepaid: false,
  })

  

  useEffect(() => {
    fetchSettings()
    fetchTaxSlabs()
  }, [])

  const fetchSettings = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/tax/settings`)
      if (response.ok) {
        const data = await response.json()
        setSettings({
          gstNumber: data.gstNumber || '',
          servicePricingType: data.servicePricingType || 'inclusive',
          productPricingType: data.productPricingType || 'exclusive',
          prepaidPricingType: data.prepaidPricingType || 'inclusive',
        })
      }
    } catch (error) {
      console.error('Error fetching tax settings:', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchTaxSlabs = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/tax/slabs`)
      if (response.ok) {
        const data = await response.json()
        setTaxSlabs(data.slabs || [])
      }
    } catch (error) {
      console.error('Error fetching tax slabs:', error)
    }
  }

  const handleSettingsChange = (field, value) => {
    setSettings({ ...settings, [field]: value })
  }

  const handleSaveSettings = async (e) => {
    e.preventDefault()
    setSaving(true)
    setMessage('')

    try {
      const response = await fetch(`${API_BASE_URL}/api/tax/settings`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(settings),
      })

      if (response.ok) {
        setMessage('Tax settings saved successfully!')
        setTimeout(() => setMessage(''), 3000)
      } else {
        const error = await response.json()
        setMessage(error.error || 'Failed to save settings')
      }
    } catch (error) {
      console.error('Error saving tax settings:', error)
      setMessage('Error saving settings')
    } finally {
      setSaving(false)
    }
  }

  const handleAddSlab = () => {
    setEditingSlab(null)
    setSlabFormData({
      name: '',
      rate: '',
      applyToServices: false,
      applyToProducts: false,
      applyToPrepaid: false,
    })
    setShowSlabModal(true)
  }

  const handleEditSlab = (slab) => {
    setEditingSlab(slab)
    setSlabFormData({
      name: slab.name,
      rate: slab.rate,
      applyToServices: slab.applyToServices,
      applyToProducts: slab.applyToProducts,
      applyToPrepaid: slab.applyToPrepaid,
    })
    setShowSlabModal(true)
  }

  const handleDeleteSlab = async (slabId) => {
    if (!window.confirm('Are you sure you want to delete this tax slab?')) {
      return
    }

    try {
      const response = await fetch(`${API_BASE_URL}/api/tax/slabs/${slabId}`, {
        method: 'DELETE',
      })

      if (response.ok) {
        fetchTaxSlabs()
      } else {
        const error = await response.json()
        alert(error.error || 'Failed to delete tax slab')
      }
    } catch (error) {
      console.error('Error deleting tax slab:', error)
      alert('Error deleting tax slab')
    }
  }

  const handleSlabSubmit = async (e) => {
    e.preventDefault()

    try {
      const url = editingSlab
        ? `${API_BASE_URL}/api/tax/slabs/${editingSlab.id}`
        : `${API_BASE_URL}/api/tax/slabs`
      
      const method = editingSlab ? 'PUT' : 'POST'

      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: slabFormData.name,
          rate: parseFloat(slabFormData.rate),
          applyToServices: slabFormData.applyToServices,
          applyToProducts: slabFormData.applyToProducts,
          applyToPrepaid: slabFormData.applyToPrepaid,
        }),
      })

      if (response.ok) {
        setShowSlabModal(false)
        fetchTaxSlabs()
      } else {
        const error = await response.json()
        alert(error.error || 'Failed to save tax slab')
      }
    } catch (error) {
      console.error('Error saving tax slab:', error)
      alert('Error saving tax slab')
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
      const rateIdx = headers.findIndex(h => h.includes('rate'))
      const servicesIdx = headers.findIndex(h => h.includes('service'))
      const productsIdx = headers.findIndex(h => h.includes('product'))
      const prepaidIdx = headers.findIndex(h => h.includes('prepaid') || h.includes('membership'))

      if (nameIdx === -1 || rateIdx === -1) {
        alert('File must contain Name and Rate columns')
        return
      }

      let successCount = 0
      let errorCount = 0

      // Process data rows
      for (let i = 1; i < rows.length; i++) {
        if (!rows[i] || rows[i].length === 0) continue
        
        const values = rows[i]
        const slabData = {
          name: String(values[nameIdx] || '').trim(),
          rate: parseFloat(values[rateIdx] || '0'),
          applyToServices: servicesIdx >= 0 ? 
            (String(values[servicesIdx] || '').toLowerCase().includes('yes') || 
             String(values[servicesIdx] || '').toLowerCase().includes('true') ||
             String(values[servicesIdx] || '').toLowerCase().includes('1')) : false,
          applyToProducts: productsIdx >= 0 ? 
            (String(values[productsIdx] || '').toLowerCase().includes('yes') || 
             String(values[productsIdx] || '').toLowerCase().includes('true') ||
             String(values[productsIdx] || '').toLowerCase().includes('1')) : false,
          applyToPrepaid: prepaidIdx >= 0 ? 
            (String(values[prepaidIdx] || '').toLowerCase().includes('yes') || 
             String(values[prepaidIdx] || '').toLowerCase().includes('true') ||
             String(values[prepaidIdx] || '').toLowerCase().includes('1')) : false,
        }

        if (slabData.name && slabData.rate >= 0) {
          try {
            const response = await fetch(`${API_BASE_URL}/api/tax/slabs`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify(slabData),
            })
            if (response.ok) {
              successCount++
            } else {
              errorCount++
            }
          } catch (err) {
            console.error(`Error importing tax slab ${i}:`, err)
            errorCount++
          }
        } else {
          errorCount++
        }
      }
      
      alert(`Tax slabs imported: ${successCount} successful, ${errorCount} failed`)
      setShowImportModal(false)
      fetchTaxSlabs()
    } catch (error) {
      console.error('Error processing import file:', error)
      alert(`Error processing import file: ${error.message}`)
    }
  }

  return (
    <div className="tax-page">
      {/* Header */}
      <header className="tax-header">
        <div className="header-left">
          <button className="menu-icon">
            <FaBars />
          </button>
          <h1 className="header-title">Tax</h1>
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

      <div className="tax-container">
        {/* Tax Settings Section */}
        <div className="tax-settings-card">
          <h2 className="section-title">Tax Settings</h2>

          {loading ? (
            <div className="loading-message">Loading settings...</div>
          ) : (
            <form onSubmit={handleSaveSettings} className="tax-settings-form">
              {/* GST Details */}
              <div className="form-section">
                <h3 className="subsection-title">GST Details</h3>
                <p className="subsection-description">
                  Configure GST details for the invoice.
                </p>
                <div className="form-group">
                  <label htmlFor="gstNumber">GST Number</label>
                  <input
                    type="text"
                    id="gstNumber"
                    value={settings.gstNumber}
                    onChange={(e) =>
                      handleSettingsChange('gstNumber', e.target.value)
                    }
                    placeholder="Enter GST number"
                  />
                </div>
              </div>

              {/* Pricing Calculation */}
              <div className="form-section">
                <h3 className="subsection-title">Pricing Calculation</h3>
                <p className="subsection-description">
                  Choose whether item prices entered already include tax (Inclusive) or if tax should be added on top (Exclusive).
                </p>
                <div className="form-group">
                  <label htmlFor="servicePricingType">For Services:</label>
                  <select
                    id="servicePricingType"
                    value={settings.servicePricingType}
                    onChange={(e) =>
                      handleSettingsChange('servicePricingType', e.target.value)
                    }
                  >
                    <option value="inclusive">Price Includes Tax (Inclusive)</option>
                    <option value="exclusive">Price Excludes Tax (Exclusive)</option>
                  </select>
                </div>
                <div className="form-group">
                  <label htmlFor="productPricingType">For Products:</label>
                  <select
                    id="productPricingType"
                    value={settings.productPricingType}
                    onChange={(e) =>
                      handleSettingsChange('productPricingType', e.target.value)
                    }
                  >
                    <option value="inclusive">Price Includes Tax (Inclusive)</option>
                    <option value="exclusive">Price Excludes Tax (Exclusive)</option>
                  </select>
                </div>
                <div className="form-group">
                  <label htmlFor="prepaidPricingType">For Prepaid & Memberships:</label>
                  <select
                    id="prepaidPricingType"
                    value={settings.prepaidPricingType}
                    onChange={(e) =>
                      handleSettingsChange('prepaidPricingType', e.target.value)
                    }
                  >
                    <option value="inclusive">Price Includes Tax (Inclusive)</option>
                    <option value="exclusive">Price Excludes Tax (Exclusive)</option>
                  </select>
                </div>
              </div>

              {/* Message */}
              {message && (
                <div
                  className={`message ${
                    message.includes('successfully') ? 'success' : 'error'
                  }`}
                >
                  {message}
                </div>
              )}

              {/* Save Button */}
              <div className="form-actions">
                <button
                  type="submit"
                  className="save-button"
                  disabled={saving}
                >
                  {saving ? 'Saving...' : 'Save Tax Settings'}
                </button>
              </div>
            </form>
          )}
        </div>

        {/* Manage Tax Slabs Section */}
        <div className="tax-slabs-card">
          <div className="slabs-header">
            <div>
              <h2 className="section-title">Manage Tax Slabs</h2>
              <p className="section-description">
                Define tax rates and assign them to categories.
              </p>
            </div>
            <div style={{ display: 'flex', gap: '10px' }}>
              <button className="action-btn import-btn" onClick={() => setShowImportModal(true)} style={{ padding: '8px 16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <FaCloudUploadAlt /> Import Tax Slabs
              </button>
              <button className="add-slab-button" onClick={handleAddSlab}>
                <FaPlus /> Add Tax Slab
              </button>
            </div>
          </div>

          <div className="table-wrapper">
            <table className="tax-slabs-table">
              <thead>
                <tr>
                  <th>Tax Name</th>
                  <th>Rate (%)</th>
                  <th>Apply to Services</th>
                  <th>Apply to Products</th>
                  <th>Apply to Prepaid & Memberships</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {taxSlabs.length === 0 ? (
                  <tr>
                    <td colSpan="6" className="empty-row">
                      No tax slabs found
                    </td>
                  </tr>
                ) : (
                  taxSlabs.map((slab) => (
                    <tr key={slab.id}>
                      <td>{slab.name}</td>
                      <td>{slab.rate}%</td>
                      <td>
                        <span
                          className={`toggle-indicator ${
                            slab.applyToServices ? 'active' : 'inactive'
                          }`}
                        >
                          {slab.applyToServices ? '✓' : '✗'}
                        </span>
                      </td>
                      <td>
                        <span
                          className={`toggle-indicator ${
                            slab.applyToProducts ? 'active' : 'inactive'
                          }`}
                        >
                          {slab.applyToProducts ? '✓' : '✗'}
                        </span>
                      </td>
                      <td>
                        <span
                          className={`toggle-indicator ${
                            slab.applyToPrepaid ? 'active' : 'inactive'
                          }`}
                        >
                          {slab.applyToPrepaid ? '✓' : '✗'}
                        </span>
                      </td>
                      <td>
                        <div className="action-icons">
                          <button
                            className="icon-btn edit-btn"
                            title="Edit"
                            onClick={() => handleEditSlab(slab)}
                          >
                            <FaEdit />
                          </button>
                          <button
                            className="icon-btn delete-btn"
                            title="Delete"
                            onClick={() => handleDeleteSlab(slab.id)}
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

      {/* Add/Edit Tax Slab Modal */}
      {showSlabModal && (
        <div className="modal-overlay" onClick={() => setShowSlabModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>{editingSlab ? 'Edit Tax Slab' : 'Add Tax Slab'}</h3>
              <button
                className="modal-close"
                onClick={() => setShowSlabModal(false)}
              >
                ×
              </button>
            </div>
            <form onSubmit={handleSlabSubmit} className="slab-form">
              <div className="form-group">
                <label>Tax Name *</label>
                <input
                  type="text"
                  value={slabFormData.name}
                  onChange={(e) =>
                    setSlabFormData({ ...slabFormData, name: e.target.value })
                  }
                  required
                />
              </div>
              <div className="form-group">
                <label>Rate (%) *</label>
                <input
                  type="number"
                  value={slabFormData.rate}
                  onChange={(e) =>
                    setSlabFormData({ ...slabFormData, rate: e.target.value })
                  }
                  min="0"
                  max="100"
                  step="0.1"
                  required
                />
              </div>
              <div className="form-group checkbox-group">
                <label>
                  <input
                    type="checkbox"
                    checked={slabFormData.applyToServices}
                    onChange={(e) =>
                      setSlabFormData({
                        ...slabFormData,
                        applyToServices: e.target.checked,
                      })
                    }
                  />
                  Apply to Services
                </label>
              </div>
              <div className="form-group checkbox-group">
                <label>
                  <input
                    type="checkbox"
                    checked={slabFormData.applyToProducts}
                    onChange={(e) =>
                      setSlabFormData({
                        ...slabFormData,
                        applyToProducts: e.target.checked,
                      })
                    }
                  />
                  Apply to Products
                </label>
              </div>
              <div className="form-group checkbox-group">
                <label>
                  <input
                    type="checkbox"
                    checked={slabFormData.applyToPrepaid}
                    onChange={(e) =>
                      setSlabFormData({
                        ...slabFormData,
                        applyToPrepaid: e.target.checked,
                      })
                    }
                  />
                  Apply to Prepaid & Memberships
                </label>
              </div>
              <div className="modal-actions">
                <button
                  type="button"
                  className="btn-cancel"
                  onClick={() => setShowSlabModal(false)}
                >
                  Cancel
                </button>
                <button type="submit" className="btn-submit">
                  {editingSlab ? 'Update' : 'Create'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Import Tax Slabs Modal */}
      {showImportModal && (
        <div className="modal-overlay" onClick={() => setShowImportModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2>Import Tax Slabs</h2>
            <div className="import-instructions">
              <p>Upload a CSV or Excel file (.csv, .xlsx, .xls) with the following columns:</p>
              <ul>
                <li>Name (required)</li>
                <li>Rate (required - percentage)</li>
                <li>Apply to Services (optional - yes/no, true/false, or 1/0)</li>
                <li>Apply to Products (optional - yes/no, true/false, or 1/0)</li>
                <li>Apply to Prepaid (optional - yes/no, true/false, or 1/0)</li>
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

export default Tax

