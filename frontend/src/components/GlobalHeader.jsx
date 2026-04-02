import React, { useState, useEffect, useRef, useCallback } from 'react';
import { FaBell, FaUser, FaSignOutAlt, FaBars, FaTimes, FaCheckDouble } from 'react-icons/fa';
import { useAuth } from '../contexts/AuthContext';
import { apiGet, apiPut } from '../utils/api';
import Profile from './Profile';
import BranchSelector from './BranchSelector';
import './GlobalHeader.css';

const POLL_INTERVAL = 30000;

const GlobalHeader = ({ onMobileMenuToggle }) => {
  const { user, logout, hasAnyRole } = useAuth();
  const [showProfile, setShowProfile] = useState(false);
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const dropdownRef = useRef(null);

  const isManagerOrOwner = hasAnyRole('manager', 'owner');

  const fetchNotifications = useCallback(async () => {
    if (!isManagerOrOwner) return;
    try {
      const res = await apiGet('/api/notifications/');
      if (res.ok) {
        const data = await res.json();
        setNotifications(data.notifications || []);
        setUnreadCount(data.unread_count || 0);
      }
    } catch {
      // Silent fail for polling
    }
  }, [isManagerOrOwner]);

  useEffect(() => {
    fetchNotifications();
    if (!isManagerOrOwner) return;
    const interval = setInterval(fetchNotifications, POLL_INTERVAL);
    return () => clearInterval(interval);
  }, [fetchNotifications, isManagerOrOwner]);

  useEffect(() => {
    const handleBranchChange = () => fetchNotifications();
    window.addEventListener('branchChanged', handleBranchChange);
    return () => window.removeEventListener('branchChanged', handleBranchChange);
  }, [fetchNotifications]);

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setShowNotifications(false);
      }
    };
    if (showNotifications) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [showNotifications]);

  const handleBellClick = () => {
    setShowNotifications((prev) => !prev);
  };

  const handleNotificationClick = async (notif) => {
    if (!notif.is_read) {
      try {
        await apiPut(`/api/notifications/${notif.id}/read`);
        setNotifications((prev) =>
          prev.map((n) => (n.id === notif.id ? { ...n, is_read: true } : n))
        );
        setUnreadCount((prev) => Math.max(0, prev - 1));
      } catch {
        // ignore
      }
    }

    if (notif.type === 'discount_approval') {
      window.dispatchEvent(new CustomEvent('navigateToPage', { detail: { page: 'discount-approvals' } }));
      setShowNotifications(false);
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await apiPut('/api/notifications/read-all');
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
      setUnreadCount(0);
    } catch {
      // ignore
    }
  };

  const formatTimeAgo = (dateStr) => {
    if (!dateStr) return '';
    const utcStr = dateStr.endsWith('Z') || /[+-]\d{2}:\d{2}$/.test(dateStr) ? dateStr : dateStr + 'Z';
    const diff = Date.now() - new Date(utcStr).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return 'Just now';
    if (mins < 60) return `${mins}m ago`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `${hrs}h ago`;
    const days = Math.floor(hrs / 24);
    return `${days}d ago`;
  };

  const getUserInitials = () => {
    if (!user) return 'U';
    const firstName = user.first_name || '';
    const lastName = user.last_name || '';
    if (firstName && lastName) return `${firstName[0]}${lastName[0]}`.toUpperCase();
    if (firstName) return firstName[0].toUpperCase();
    return 'U';
  };

  return (
    <>
      <header className="global-header">
        <div className="global-header-content">
          {onMobileMenuToggle && (
            <button
              className="mobile-menu-btn"
              onClick={onMobileMenuToggle}
              aria-label="Toggle menu"
            >
              <FaBars size={20} />
            </button>
          )}

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

            <div className="notif-bell-wrapper" ref={dropdownRef}>
              <button
                className={`header-icon bell-icon ${unreadCount > 0 ? 'has-unread' : ''}`}
                onClick={handleBellClick}
                title="Notifications"
              >
                <FaBell size={16} />
                {unreadCount > 0 && (
                  <span className="notif-badge">{unreadCount > 9 ? '9+' : unreadCount}</span>
                )}
              </button>

              {showNotifications && (
                <div className="notif-dropdown">
                  <div className="notif-dropdown-header">
                    <span className="notif-dropdown-title">Notifications</span>
                    {notifications.length > 0 && unreadCount > 0 && (
                      <button className="notif-mark-all" onClick={handleMarkAllRead}>
                        <FaCheckDouble size={12} /> Mark all read
                      </button>
                    )}
                    <button className="notif-dropdown-close" onClick={() => setShowNotifications(false)}>
                      <FaTimes size={14} />
                    </button>
                  </div>

                  <div className="notif-dropdown-body">
                    {!isManagerOrOwner ? (
                      <div className="notif-empty">
                        <FaBell className="notif-empty-icon" />
                        <p>No notifications yet</p>
                      </div>
                    ) : notifications.length === 0 ? (
                      <div className="notif-empty">
                        <FaBell className="notif-empty-icon" />
                        <p>No notifications yet</p>
                      </div>
                    ) : (
                      notifications.map((notif) => (
                        <div
                          key={notif.id}
                          className={`notif-item ${notif.is_read ? 'read' : 'unread'}`}
                          onClick={() => handleNotificationClick(notif)}
                        >
                          <div className="notif-item-dot" />
                          <div className="notif-item-content">
                            <span className="notif-item-title">{notif.title}</span>
                            <span className="notif-item-message">{notif.message}</span>
                            <span className="notif-item-time">{formatTimeAgo(notif.created_at)}</span>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              )}
            </div>

            <button
              className="header-icon user-icon profile-icon-btn"
              onClick={() => setShowProfile(true)}
              title="My Profile"
            >
              {user ? (
                <div className="user-avatar-small">{getUserInitials()}</div>
              ) : (
                <FaUser size={16} />
              )}
            </button>
          </div>
        </div>
      </header>

      <Profile isOpen={showProfile} onClose={() => setShowProfile(false)} />

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
