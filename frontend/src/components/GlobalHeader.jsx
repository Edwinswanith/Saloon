import React, { useState } from 'react';
import { FaBell, FaUser, FaSignOutAlt, FaBars } from 'react-icons/fa';
import { useAuth } from '../contexts/AuthContext';
import Profile from './Profile';
import BranchSelector from './BranchSelector';
import './GlobalHeader.css';

const GlobalHeader = ({ onMobileMenuToggle }) => {
  const { user, logout } = useAuth();
  const [showProfile, setShowProfile] = useState(false);
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false);

  const getUserInitials = () => {
    if (!user) return 'U';
    const firstName = user.first_name || '';
    const lastName = user.last_name || '';
    if (firstName && lastName) {
      return `${firstName[0]}${lastName[0]}`.toUpperCase();
    }
    if (firstName) {
      return firstName[0].toUpperCase();
    }
    return 'U';
  };

  return (
    <>
      <header className="global-header">
        <div className="global-header-content">
          {/* Mobile hamburger menu button */}
          {onMobileMenuToggle && (
            <button
              className="mobile-menu-btn"
              onClick={onMobileMenuToggle}
              aria-label="Toggle menu"
            >
              <FaBars size={20} />
            </button>
          )}
          
          {/* Center Banner */}
          <div className="global-header-center">
            <div className="banner-text">
              <span className="banner-main">Priyanka Nature Cure</span>
            </div>
          </div>
          
          <div className="global-header-right">
            <BranchSelector />
            <button 
              className="logo-box logo-logout-btn" 
              onClick={() => setShowLogoutConfirm(true)}
              title="Click to logout"
            >
              <FaSignOutAlt className="logout-icon" size={16} />
              <span className="logo-text">Logout</span>
            </button>
            <button className="header-icon bell-icon" title="Notifications">
              <FaBell size={16} />
            </button>
            <button
              className="header-icon user-icon profile-icon-btn"
              onClick={() => setShowProfile(true)}
              title="My Profile"
            >
              {user ? (
                <div className="user-avatar-small">
                  {getUserInitials()}
                </div>
              ) : (
                <FaUser size={16} />
              )}
            </button>
          </div>
        </div>
      </header>

      <Profile isOpen={showProfile} onClose={() => setShowProfile(false)} />

      {/* Logout Confirmation Modal */}
      {showLogoutConfirm && (
        <div className="logout-overlay" onClick={() => setShowLogoutConfirm(false)}>
          <div className="logout-modal" onClick={(e) => e.stopPropagation()}>
            <div className="logout-modal-header">
              <h3>Confirm Logout</h3>
            </div>
            <div className="logout-modal-body">
              <p>Are you sure you want to logout?</p>
            </div>
            <div className="logout-modal-actions">
              <button
                className="logout-btn-cancel"
                onClick={() => setShowLogoutConfirm(false)}
              >
                Cancel
              </button>
              <button
                className="logout-btn-confirm"
                onClick={async () => {
                  await logout();
                  setShowLogoutConfirm(false);
                }}
              >
                <FaSignOutAlt /> Logout
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default GlobalHeader;

