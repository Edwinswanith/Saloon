import React from 'react'
import {
  FaFileAlt,
  FaGift,
  FaShare,
  FaDownload,
  FaUsers,
  FaKey,
} from 'react-icons/fa'
import { useAuth } from '../contexts/AuthContext'
import './Settings.css'

const Settings = ({ setActivePage }) => {
  const { user } = useAuth()
  const isOwner = user && user.role === 'owner'
  const settingsOptions = [
    {
      id: 1,
      title: 'Membership',
      description: 'Manage your Plan, staff-size, add-ons and billing cycle',
      icon: <FaFileAlt />,
    },
    {
      id: 2,
      title: 'Referral Program',
      description: 'Set rewards and manage the customer referral program',
      icon: <FaShare />,
    },
    {
      id: 3,
      title: 'Tax',
      description: 'Customize tax groups and taxes that align with business needs',
      icon: <FaDownload />,
    },
    {
      id: 4,
      title: 'Manager',
      description: 'Manage your Managers',
      icon: <FaUsers />,
    },
  ]

  // Add Owner Settings option if user is owner
  if (isOwner) {
    settingsOptions.push({
      id: 5,
      title: 'Owner Settings',
      description: 'Update your email address and password',
      icon: <FaKey />,
    })
  }

  return (
    <div className="settings-page">
      <div className="settings-container">
        {/* Main Heading */}
        <h2 className="main-heading">Settings</h2>

        {/* Settings Cards Grid */}
        <div className="settings-grid">
          {settingsOptions.map((option) => (
            <div
              key={option.id}
              className="settings-card"
              onClick={() => {
                if (option.id === 1 && setActivePage) {
                  // Membership card clicked
                  setActivePage('membership')
                } else if (option.id === 2 && setActivePage) {
                  // Referral Program card clicked
                  setActivePage('referral-program')
                } else if (option.id === 3 && setActivePage) {
                  // Tax card clicked
                  setActivePage('tax')
                } else if (option.id === 4 && setActivePage) {
                  // Manager card clicked
                  setActivePage('manager')
                } else if (option.id === 5 && setActivePage) {
                  // Owner Settings card clicked
                  setActivePage('owner-settings')
                }
                // Add other navigation handlers here for other options
              }}
              style={option.id === 1 || option.id === 2 || option.id === 3 || option.id === 4 || option.id === 5 || option.id === 6 ? { cursor: 'pointer' } : {}}
            >
              <div className="card-icon">{option.icon}</div>
              <h3 className="card-title">{option.title}</h3>
              <p className="card-description">{option.description}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default Settings

