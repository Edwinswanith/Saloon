import React, { useState, useEffect } from 'react'
import {
  FaBars,
  FaBell,
  FaUser,
} from 'react-icons/fa'
import './LoyaltyProgram.css'
import { API_BASE_URL } from '../config'

const LoyaltyProgram = () => {
  const [settings, setSettings] = useState({
    enabled: false,
    earningRate: 100,
    redemptionRate: 1,
  })
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')

  useEffect(() => {
    fetchSettings()
  }, [])

  const fetchSettings = async () => {
    try {
      setLoading(true)
      const response = await fetch(`${API_BASE_URL}/api/loyalty-program/settings`)
      if (response.ok) {
        const data = await response.json()
        setSettings({
          enabled: data.enabled || false,
          earningRate: data.earningRate || 100,
          redemptionRate: data.redemptionRate || 1,
        })
      }
    } catch (error) {
      console.error('Error fetching loyalty program settings:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleToggle = (e) => {
    setSettings({ ...settings, enabled: e.target.checked })
  }

  const handleInputChange = (field, value) => {
    setSettings({ ...settings, [field]: value })
  }

  const handleSave = async (e) => {
    e.preventDefault()
    setSaving(true)
    setMessage('')

    try {
      const response = await fetch(`${API_BASE_URL}/api/loyalty-program/settings`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          enabled: settings.enabled,
          earningRate: parseFloat(settings.earningRate),
          redemptionRate: parseFloat(settings.redemptionRate),
        }),
      })

      if (response.ok) {
        setMessage('Settings saved successfully!')
        setTimeout(() => setMessage(''), 3000)
      } else {
        const error = await response.json()
        setMessage(error.error || 'Failed to save settings')
      }
    } catch (error) {
      console.error('Error saving loyalty program settings:', error)
      setMessage('Error saving settings')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="loyalty-program-page">
      {/* Header */}
      <header className="loyalty-program-header">
        <div className="header-left">
          <button className="menu-icon">
            <FaBars />
          </button>
          <h1 className="header-title">Loyalty Program</h1>
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

      <div className="loyalty-program-container">
        {/* Settings Card */}
        <div className="loyalty-program-card">
          <h2 className="settings-title">Loyalty Program Settings</h2>
          <p className="settings-description">
            Enable and manage how customers earn and redeem loyalty points.
          </p>

          {loading ? (
            <div className="loading-message">Loading settings...</div>
          ) : (
            <form onSubmit={handleSave} className="loyalty-program-form">
              {/* Enable Toggle */}
              <div className="form-group toggle-group">
                <label htmlFor="enabled" className="toggle-label">
                  Enable Loyalty Program
                </label>
                <div className="toggle-wrapper">
                  <input
                    type="checkbox"
                    id="enabled"
                    checked={settings.enabled}
                    onChange={handleToggle}
                    className="toggle-input"
                  />
                  <label htmlFor="enabled" className="toggle-switch">
                    <span className="toggle-slider"></span>
                  </label>
                </div>
              </div>

              {/* Earning Rate */}
              <div className="form-group">
                <label htmlFor="earningRate">Earning Rate</label>
                <p className="field-note">
                  (Note: Amount a customer must spend to earn 1 point)
                </p>
                <input
                  type="number"
                  id="earningRate"
                  value={settings.earningRate}
                  onChange={(e) =>
                    handleInputChange('earningRate', e.target.value)
                  }
                  min="0.01"
                  step="0.01"
                  required
                  disabled={!settings.enabled}
                  className={!settings.enabled ? 'disabled' : ''}
                />
              </div>

              {/* Redemption Rate */}
              <div className="form-group">
                <label htmlFor="redemptionRate">Redemption Rate</label>
                <p className="field-note">
                  (Note: Number of points needed to redeem for a ₹1 amount)
                </p>
                <input
                  type="number"
                  id="redemptionRate"
                  value={settings.redemptionRate}
                  onChange={(e) =>
                    handleInputChange('redemptionRate', e.target.value)
                  }
                  min="0.01"
                  step="0.01"
                  required
                  disabled={!settings.enabled}
                  className={!settings.enabled ? 'disabled' : ''}
                />
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
                  {saving ? 'Saving...' : 'Save Settings'}
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  )
}

export default LoyaltyProgram

