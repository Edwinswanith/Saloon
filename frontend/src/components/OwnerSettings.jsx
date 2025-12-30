import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { API_BASE_URL } from '../config';
import Header from './Header';
import './OwnerSettings.css';

const OwnerSettings = () => {
  const { user, token } = useAuth();
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: ''
  });
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });

  useEffect(() => {
    // Load current owner email
    if (user && user.email) {
      setFormData(prev => ({ ...prev, email: user.email }));
    }
  }, [user]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    setMessage({ type: '', text: '' }); // Clear message on change
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setMessage({ type: '', text: '' });

    // Validation
    if (formData.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      setMessage({ type: 'error', text: 'Please enter a valid email address' });
      return;
    }

    if (formData.password && formData.password.length < 6) {
      setMessage({ type: 'error', text: 'Password must be at least 6 characters long' });
      return;
    }

    if (formData.password && formData.password !== formData.confirmPassword) {
      setMessage({ type: 'error', text: 'Passwords do not match' });
      return;
    }

    setLoading(true);

    try {
      const updateData = {};
      if (formData.email) {
        updateData.email = formData.email;
      }
      if (formData.password) {
        updateData.password = formData.password;
      }

      const response = await fetch(`${API_BASE_URL}/api/auth/owner/update-credentials`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(updateData)
      });

      const data = await response.json();

      if (response.ok) {
        setMessage({ type: 'success', text: 'Credentials updated successfully!' });
        // Clear password fields
        setFormData(prev => ({ ...prev, password: '', confirmPassword: '' }));
      } else {
        setMessage({ type: 'error', text: data.error || 'Failed to update credentials' });
      }
    } catch (error) {
      console.error('Error updating credentials:', error);
      setMessage({ type: 'error', text: 'An error occurred. Please try again.' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="owner-settings-page">
      <Header title="Owner Settings" />
      
      <div className="owner-settings-container">
        <div className="owner-settings-card">
          <h2 className="owner-settings-title">Update Owner Credentials</h2>
          <p className="owner-settings-subtitle">
            Update your email address and password for login
          </p>

          <form onSubmit={handleSubmit} className="owner-settings-form">
            <div className="form-group">
              <label htmlFor="email" className="form-label">
                Email Address
              </label>
              <input
                type="email"
                id="email"
                name="email"
                className="form-input"
                placeholder="Enter your email address"
                value={formData.email}
                onChange={handleChange}
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="password" className="form-label">
                New Password (optional)
              </label>
              <input
                type="password"
                id="password"
                name="password"
                className="form-input"
                placeholder="Enter new password (min 6 characters)"
                value={formData.password}
                onChange={handleChange}
                minLength={6}
              />
              <small className="form-help-text">
                Leave blank if you don't want to change the password
              </small>
            </div>

            {formData.password && (
              <div className="form-group">
                <label htmlFor="confirmPassword" className="form-label">
                  Confirm New Password
                </label>
                <input
                  type="password"
                  id="confirmPassword"
                  name="confirmPassword"
                  className="form-input"
                  placeholder="Confirm new password"
                  value={formData.confirmPassword}
                  onChange={handleChange}
                  minLength={6}
                />
              </div>
            )}

            {message.text && (
              <div className={`message ${message.type}`}>
                {message.text}
              </div>
            )}

            <button
              type="submit"
              className="submit-button"
              disabled={loading}
            >
              {loading ? 'Updating...' : 'Update Credentials'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default OwnerSettings;

