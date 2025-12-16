import React from 'react'
import {
  FaBars,
  FaBell,
  FaUser,
  FaFileAlt,
  FaGift,
  FaShare,
  FaDownload,
  FaUsers,
} from 'react-icons/fa'
import './Settings.css'

const Settings = ({ setActivePage }) => {
  const settingsOptions = [
    {
      id: 1,
      title: 'Membership',
      description: 'Manage your Plan, staff-size, add-ons and billing cycle',
      icon: <FaFileAlt />,
    },
    {
      id: 2,
      title: 'Loyalty Program',
      description: 'Enable and manage customer loyalty points and rewards',
      icon: <FaGift />,
    },
    {
      id: 3,
      title: 'Referral Program',
      description: 'Set rewards and manage the customer referral program',
      icon: <FaShare />,
    },
    {
      id: 4,
      title: 'Tax',
      description: 'Customize tax groups and taxes that align with business needs',
      icon: <FaDownload />,
    },
    {
      id: 5,
      title: 'Manager',
      description: 'Manage your Managers',
      icon: <FaUsers />,
    },
  ]

  return (
    <div className="settings-page">
      {/* Header */}
      <header className="settings-header">
        <div className="header-left">
          <button className="menu-icon">
            <FaBars />
          </button>
          <h1 className="header-title">Settings</h1>
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
                  // Loyalty Program card clicked
                  setActivePage('loyalty-program')
                } else if (option.id === 3 && setActivePage) {
                  // Referral Program card clicked
                  setActivePage('referral-program')
                } else if (option.id === 4 && setActivePage) {
                  // Tax card clicked
                  setActivePage('tax')
                } else if (option.id === 5 && setActivePage) {
                  // Manager card clicked
                  setActivePage('manager')
                }
                // Add other navigation handlers here for other options
              }}
              style={option.id === 1 || option.id === 2 || option.id === 3 || option.id === 4 || option.id === 5 ? { cursor: 'pointer' } : {}}
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

