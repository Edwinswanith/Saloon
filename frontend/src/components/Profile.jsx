import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { API_BASE_URL } from '../config';
import { FaUser, FaTimes, FaEdit, FaSave, FaEnvelope, FaPhone, FaBuilding, FaShieldAlt } from 'react-icons/fa';
import './Profile.css';

const Profile = ({ isOpen, onClose }) => {
  const { user, token, updateUser } = useAuth();
  const [isEditing, setIsEditing] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [profileData, setProfileData] = useState({
    first_name: '',
    last_name: '',
    email: '',
    mobile: '',
    salon: '',
    role: '',
    user_type: ''
  });

  // Load user data when modal opens
  useEffect(() => {
    if (isOpen && user) {
      setProfileData({
        first_name: user.first_name || '',
        last_name: user.last_name || '',
        email: user.email || '',
        mobile: user.mobile || '',
        salon: user.salon || '',
        role: user.role || '',
        user_type: user.user_type || ''
      });
      setError('');
      setSuccess('');
      setIsEditing(false);
    }
  }, [isOpen, user]);

  // Fetch latest user data from server
  useEffect(() => {
    if (isOpen && token) {
      fetchUserData();
    }
  }, [isOpen, token]);

  const fetchUserData = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/auth/me`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        if (data.user) {
          setProfileData({
            first_name: data.user.first_name || '',
            last_name: data.user.last_name || '',
            email: data.user.email || '',
            mobile: data.user.mobile || '',
            salon: data.user.salon || '',
            role: data.user.role || '',
            user_type: data.user.user_type || ''
          });
          // Update auth context
          if (updateUser) {
            updateUser(data.user);
          }
        }
      }
    } catch (err) {
      console.error('Failed to fetch user data:', err);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setProfileData(prev => ({
      ...prev,
      [name]: value
    }));
    setError('');
    setSuccess('');
  };

  const handleSave = async () => {
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const response = await fetch(`${API_BASE_URL}/api/auth/profile`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          first_name: profileData.first_name,
          last_name: profileData.last_name,
          email: profileData.email,
          mobile: profileData.mobile,
          salon: profileData.salon
        }),
      });

      const data = await response.json();

      if (response.ok) {
        setSuccess('Profile updated successfully!');
        setIsEditing(false);
        
        // Update auth context with new user data
        if (data.user && updateUser) {
          updateUser(data.user);
        }
        
        // Update localStorage
        localStorage.setItem('auth_user', JSON.stringify(data.user));
      } else {
        setError(data.error || data.message || 'Failed to update profile');
      }
    } catch (err) {
      setError('An error occurred while updating profile. Please try again.');
      console.error('Update profile error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    // Reset to original user data
    if (user) {
      setProfileData({
        first_name: user.first_name || '',
        last_name: user.last_name || '',
        email: user.email || '',
        mobile: user.mobile || '',
        salon: user.salon || '',
        role: user.role || '',
        user_type: user.user_type || ''
      });
    }
    setIsEditing(false);
    setError('');
    setSuccess('');
  };

  const getRoleDisplayName = (role) => {
    const roleMap = {
      'staff': 'Staff',
      'manager': 'Manager',
      'owner': 'Owner'
    };
    return roleMap[role] || role;
  };

  if (!isOpen) return null;

  return (
    <div className="profile-overlay" onClick={onClose}>
      <div className="profile-modal" onClick={(e) => e.stopPropagation()}>
        <div className="profile-header">
          <div className="profile-header-left">
            <div className="profile-avatar">
              <FaUser />
            </div>
            <div className="profile-title-section">
              <h2 className="profile-title">My Profile</h2>
              <p className="profile-subtitle">
                {profileData.first_name} {profileData.last_name}
              </p>
            </div>
          </div>
          <button className="profile-close-btn" onClick={onClose}>
            <FaTimes />
          </button>
        </div>

        <div className="profile-content">
          {error && (
            <div className="profile-error">
              <span className="error-icon">⚠</span>
              {error}
            </div>
          )}

          {success && (
            <div className="profile-success">
              <span className="success-icon">✓</span>
              {success}
            </div>
          )}

          <div className="profile-section">
            <div className="profile-section-header">
              <h3>Personal Information</h3>
              {!isEditing && (
                <button
                  className="profile-edit-btn"
                  onClick={() => setIsEditing(true)}
                >
                  <FaEdit /> Edit
                </button>
              )}
            </div>

            <div className="profile-fields">
              <div className="profile-field">
                <label className="profile-label">
                  <FaUser className="field-icon" />
                  First Name
                </label>
                {isEditing ? (
                  <input
                    type="text"
                    name="first_name"
                    className="profile-input"
                    value={profileData.first_name}
                    onChange={handleInputChange}
                    placeholder="Enter first name"
                  />
                ) : (
                  <div className="profile-value">
                    {profileData.first_name || 'Not set'}
                  </div>
                )}
              </div>

              <div className="profile-field">
                <label className="profile-label">
                  <FaUser className="field-icon" />
                  Last Name
                </label>
                {isEditing ? (
                  <input
                    type="text"
                    name="last_name"
                    className="profile-input"
                    value={profileData.last_name}
                    onChange={handleInputChange}
                    placeholder="Enter last name"
                  />
                ) : (
                  <div className="profile-value">
                    {profileData.last_name || 'Not set'}
                  </div>
                )}
              </div>

              <div className="profile-field">
                <label className="profile-label">
                  <FaEnvelope className="field-icon" />
                  Email
                </label>
                {isEditing ? (
                  <input
                    type="email"
                    name="email"
                    className="profile-input"
                    value={profileData.email}
                    onChange={handleInputChange}
                    placeholder="Enter email address"
                  />
                ) : (
                  <div className="profile-value">
                    {profileData.email || 'Not set'}
                  </div>
                )}
              </div>

              <div className="profile-field">
                <label className="profile-label">
                  <FaPhone className="field-icon" />
                  Mobile Number
                </label>
                {isEditing ? (
                  <input
                    type="tel"
                    name="mobile"
                    className="profile-input"
                    value={profileData.mobile}
                    onChange={handleInputChange}
                    placeholder="Enter mobile number"
                  />
                ) : (
                  <div className="profile-value">
                    {profileData.mobile || 'Not set'}
                  </div>
                )}
              </div>

              {profileData.user_type === 'manager' && (
                <div className="profile-field">
                  <label className="profile-label">
                    <FaBuilding className="field-icon" />
                    Salon
                  </label>
                  {isEditing ? (
                    <input
                      type="text"
                      name="salon"
                      className="profile-input"
                      value={profileData.salon}
                      onChange={handleInputChange}
                      placeholder="Enter salon name"
                    />
                  ) : (
                    <div className="profile-value">
                      {profileData.salon || 'Not set'}
                    </div>
                  )}
                </div>
              )}

              <div className="profile-field">
                <label className="profile-label">
                  <FaShieldAlt className="field-icon" />
                  Role
                </label>
                <div className="profile-value profile-role">
                  <span className={`role-badge role-${profileData.role}`}>
                    {getRoleDisplayName(profileData.role)}
                  </span>
                </div>
              </div>
            </div>

            {isEditing && (
              <div className="profile-actions">
                <button
                  className="profile-btn profile-btn-cancel"
                  onClick={handleCancel}
                  disabled={loading}
                >
                  Cancel
                </button>
                <button
                  className="profile-btn profile-btn-save"
                  onClick={handleSave}
                  disabled={loading}
                >
                  {loading ? (
                    <>
                      <span className="loading-spinner-small"></span>
                      Saving...
                    </>
                  ) : (
                    <>
                      <FaSave /> Save Changes
                    </>
                  )}
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Profile;

