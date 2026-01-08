import React, { useState, useEffect } from 'react'
import './ReferralProgram.css'
import { API_BASE_URL } from '../config'

const ReferralProgram = () => {
  const [settings, setSettings] = useState({
    enabled: false,
    rewardType: 'percentage',
    referrerRewardPercentage: 5,
    refereeRewardPercentage: 5,
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
      const response = await fetch(`${API_BASE_URL}/api/referral-program/settings`)
      if (response.ok) {
        const data = await response.json()
        setSettings({
          enabled: data.enabled || false,
          rewardType: data.rewardType || 'percentage',
          referrerRewardPercentage: data.referrerRewardPercentage || 5,
          refereeRewardPercentage: data.refereeRewardPercentage || 5,
        })
      }
    } catch (error) {
      console.error('Error fetching referral program settings:', error)
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
      const response = await fetch(`${API_BASE_URL}/api/referral-program/settings`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          enabled: settings.enabled,
          rewardType: settings.rewardType,
          referrerRewardPercentage: parseFloat(settings.referrerRewardPercentage),
          refereeRewardPercentage: parseFloat(settings.refereeRewardPercentage),
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
      console.error('Error saving referral program settings:', error)
      setMessage('Error saving settings')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="referral-program-page">
      <div className="referral-program-container">
        {/* Settings Card */}
        <div className="referral-program-card">
          <h2 className="settings-title">Referral Program Settings</h2>

          {loading ? (
            <div className="loading-message">Loading settings...</div>
          ) : (
            <form onSubmit={handleSave} className="referral-program-form">
              {/* Enable Toggle */}
              <div className="form-group toggle-group">
                <label htmlFor="enabled" className="toggle-label">
                  Enable Program
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
                  {settings.enabled && (
                    <span className="program-status">Program is Active</span>
                  )}
                </div>
              </div>

              {/* Reward Type */}
              <div className="form-group">
                <label htmlFor="rewardType">Reward Type</label>
                <select
                  id="rewardType"
                  value={settings.rewardType}
                  onChange={(e) =>
                    handleInputChange('rewardType', e.target.value)
                  }
                  disabled={!settings.enabled}
                  className={!settings.enabled ? 'disabled' : ''}
                >
                  <option value="percentage">Percentage (%)</option>
                  <option value="fixed">Fixed Amount</option>
                </select>
              </div>

              {/* Referrer Reward */}
              <div className="form-group">
                <label htmlFor="referrerRewardPercentage">
                  Referrer Reward ({settings.rewardType === 'percentage' ? '%' : '₹'})
                </label>
                <p className="field-note">
                  Bonus credited to the existing customer's wallet.
                </p>
                <input
                  type="number"
                  id="referrerRewardPercentage"
                  value={settings.referrerRewardPercentage}
                  onChange={(e) =>
                    handleInputChange('referrerRewardPercentage', e.target.value)
                  }
                  min="0"
                  max={settings.rewardType === 'percentage' ? '100' : undefined}
                  step={settings.rewardType === 'percentage' ? '0.1' : '1'}
                  required
                  disabled={!settings.enabled}
                  className={!settings.enabled ? 'disabled' : ''}
                />
              </div>

              {/* Referee Reward */}
              <div className="form-group">
                <label htmlFor="refereeRewardPercentage">
                  Referee Reward ({settings.rewardType === 'percentage' ? '%' : '₹'})
                </label>
                <p className="field-note">
                  Discount applied to the new customer's first bill.
                </p>
                <input
                  type="number"
                  id="refereeRewardPercentage"
                  value={settings.refereeRewardPercentage}
                  onChange={(e) =>
                    handleInputChange('refereeRewardPercentage', e.target.value)
                  }
                  min="0"
                  max={settings.rewardType === 'percentage' ? '100' : undefined}
                  step={settings.rewardType === 'percentage' ? '0.1' : '1'}
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

export default ReferralProgram

