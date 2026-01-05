import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { API_BASE_URL } from '../config';
import { FaExclamationTriangle } from 'react-icons/fa';
import './Login.css';

const Login = ({ onLoginSuccess }) => {
  const { login, isAuthenticated } = useAuth();

  // Form state
  const [userType, setUserType] = useState('staff'); // 'staff', 'manager', or 'owner'
  const [identifier, setIdentifier] = useState(''); // Mobile for staff, email/mobile for manager/owner
  const [password, setPassword] = useState('');
  const [selectedBranch, setSelectedBranch] = useState(''); // Selected branch ID
  const [branches, setBranches] = useState([]);
  const [staffList, setStaffList] = useState([]);
  const [managerList, setManagerList] = useState([]);
  const [ownerList, setOwnerList] = useState([]);
  const [loading, setLoading] = useState(false);
  const [loadingStaff, setLoadingStaff] = useState(false);
  const [loadingManagers, setLoadingManagers] = useState(false);
  const [loadingOwners, setLoadingOwners] = useState(false);
  const [loadingBranches, setLoadingBranches] = useState(false);
  const [error, setError] = useState('');

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated && onLoginSuccess) {
      onLoginSuccess();
    }
  }, [isAuthenticated, onLoginSuccess]);

  // Fetch branches on mount
  useEffect(() => {
    const fetchBranches = async () => {
      setLoadingBranches(true);
      try {
        const response = await fetch(`${API_BASE_URL}/api/branches`, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        });
        
        if (response.ok) {
          const data = await response.json();
          setBranches(data);
          // Auto-select first branch if available
          if (data.length > 0 && !selectedBranch) {
            setSelectedBranch(data[0].id);
          }
        }
      } catch (err) {
        console.error('Failed to fetch branches:', err);
      } finally {
        setLoadingBranches(false);
      }
    };

    fetchBranches();
  }, []);

  // Fetch staff list for dropdown when branch or userType changes
  useEffect(() => {
    const fetchStaffList = async () => {
      if (userType !== 'staff' || !selectedBranch) {
        setStaffList([]);
        return;
      }

      setLoadingStaff(true);
      setError('');
      
      try {
        const url = `${API_BASE_URL}/api/auth/staff-list${selectedBranch ? `?branch_id=${selectedBranch}` : ''}`;
        console.log('Fetching staff list from:', url);
        const response = await fetch(url, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        });
        
        console.log('Staff list response status:', response.status);
        
        if (response.ok) {
          const data = await response.json();
          console.log('Staff list data received:', data);
          const staff = data.staff || [];
          setStaffList(staff);
          
          if (staff.length === 0) {
            console.warn('No staff members found for this branch.');
            setError('');
          }
        } else {
          const errorData = await response.json().catch(() => ({}));
          console.error('Failed to fetch staff list:', errorData);
          setError(errorData.message || 'Failed to load staff list. Please refresh the page.');
        }
      } catch (err) {
        console.error('Failed to fetch staff list:', err);
        setError('Unable to connect to server. Please check your connection and ensure the backend is running.');
      } finally {
        setLoadingStaff(false);
      }
    };

      fetchStaffList();
  }, [userType, selectedBranch]);

  // Fetch manager list for dropdown when branch or userType changes (filter by branch like staff)
  useEffect(() => {
    const fetchManagerList = async () => {
      if (userType !== 'manager' || !selectedBranch) {
        setManagerList([]);
        setIdentifier(''); // Clear manager selection when branch/userType changes
        return;
      }

      setLoadingManagers(true);
      setError('');
      setIdentifier(''); // Clear manager selection when fetching new list
      
      try {
        // Fetch managers filtered by selected branch (same as staff login)
        const url = `${API_BASE_URL}/api/auth/manager-list?role=manager&branch_id=${selectedBranch}`;
        console.log('Fetching manager list from:', url);
        const response = await fetch(url, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        });
        
        if (response.ok) {
          const data = await response.json();
          console.log('Manager list data received:', data);
          const managers = data.managers || [];

          // Enhanced debugging
          console.log(`Managers loaded for branch (${selectedBranch}):`, managers.length);
          console.log('Manager details:', managers.map(m => ({
            name: m.name,
            email: m.email,
            branch_id: m.branch_id,
            branch_name: m.branch_name
          })));

          // Verify all managers belong to selected branch
          const wrongBranch = managers.filter(m => m.branch_id !== selectedBranch);
          if (wrongBranch.length > 0) {
            console.error('ERROR: Found managers from wrong branch:', wrongBranch);
            console.error('Selected branch ID:', selectedBranch);
            console.error('This indicates a backend filtering issue!');
          }

          setManagerList(managers);

          if (managers.length === 0) {
            console.warn('No managers found for this branch.');
            setError('');
          }
        } else {
          const errorData = await response.json().catch(() => ({}));
          console.error('Failed to fetch manager list:', errorData);
          setError(errorData.message || 'Failed to load managers. Please refresh the page.');
        }
      } catch (err) {
        console.error('Failed to fetch manager list:', err);
        setError('Unable to connect to server. Please check your connection.');
      } finally {
        setLoadingManagers(false);
      }
    };

    fetchManagerList();
  }, [userType, selectedBranch]);

  // Fetch owner list for dropdown when userType changes
  useEffect(() => {
    const fetchOwnerList = async () => {
      if (userType !== 'owner') {
        setOwnerList([]);
        return;
      }

      setLoadingOwners(true);
      setError('');
      
      try {
        const url = `${API_BASE_URL}/api/auth/manager-list?role=owner`;
        console.log('Fetching owner list from:', url);
        const response = await fetch(url, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        });
        
        if (response.ok) {
          const data = await response.json();
          console.log('Owner list data received:', data);
          const managers = data.managers || [];
          // Filter to show only owners
          const filteredOwners = managers.filter(m => m.role === 'owner');
          setOwnerList(filteredOwners);
          console.log('Filtered owners:', filteredOwners.length);
        } else {
          const errorData = await response.json().catch(() => ({}));
          console.error('Failed to fetch owner list:', errorData);
        }
      } catch (err) {
        console.error('Failed to fetch owner list:', err);
      } finally {
        setLoadingOwners(false);
      }
    };

    fetchOwnerList();
  }, [userType]);

  // Handle form submission
  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    // Validation
    if (!selectedBranch) {
      setError('Please select a branch');
      return;
    }

    if (!identifier.trim()) {
      if (userType === 'staff') {
        setError('Please select a staff member');
      } else if (userType === 'manager') {
        setError('Please select a manager');
      } else if (userType === 'owner') {
        setError('Please enter your email address');
      }
      return;
    }

    // Password validation is currently disabled for both managers and owners (feature paused)
    // Password field is hidden from UI and validation is skipped in backend

    setLoading(true);

    try {
      // Backend expects 'manager' for both manager and owner login
      const loginData = {
        user_type: userType === 'owner' ? 'manager' : userType,
        identifier: identifier.trim(),
        password: password.trim(),
        role: userType === 'staff' ? 'staff' : (userType === 'owner' ? 'owner' : 'manager'),
        branch_id: selectedBranch, // Send selected branch ID
      };

      const result = await login(loginData);

      if (result.success) {
        // Login successful
        if (onLoginSuccess) {
          onLoginSuccess();
        }
      } else {
        setError(result.error || 'Login failed. Please try again.');
      }
    } catch (err) {
      setError('An unexpected error occurred. Please try again.');
      console.error('Login error:', err);
    } finally {
      setLoading(false);
    }
  };

  // Handle staff selection from dropdown
  const handleStaffSelect = (e) => {
    const mobile = e.target.value;
    setIdentifier(mobile);
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <div className="login-header">
          <div className="login-logo">
            <div className="logo-icon">✂</div>
          </div>
          <h1 className="login-title">Salon Management</h1>
          <p className="login-subtitle">Sign in to your account</p>
        </div>

        <form onSubmit={handleSubmit} className="login-form">
          {/* User Type Selection */}
          <div className="form-group">
            <label className="form-label">Login As</label>
            <div className="user-type-toggle">
              <button
                type="button"
                className={`toggle-btn ${userType === 'staff' ? 'active' : ''}`}
                onClick={() => {
                  setUserType('staff');
                  setIdentifier('');
                  setPassword('');
                  setError('');
                }}
              >
                Staff
              </button>
              <button
                type="button"
                className={`toggle-btn ${userType === 'manager' ? 'active' : ''}`}
                onClick={() => {
                  setUserType('manager');
                  setIdentifier('');
                  setPassword('');
                  setError('');
                }}
              >
                Manager
              </button>
              <button
                type="button"
                className={`toggle-btn ${userType === 'owner' ? 'active' : ''}`}
                onClick={() => {
                  setUserType('owner');
                  setIdentifier('');
                  setPassword('');
                  setError('');
                }}
              >
                Owner
              </button>
            </div>
          </div>

          {/* Branch Selection */}
          <div className="form-group">
            <label htmlFor="branch-select" className="form-label">
              Select Branch
            </label>
            {loadingBranches ? (
              <div className="form-input" style={{ padding: '12px', textAlign: 'center', color: '#666' }}>
                Loading branches...
              </div>
            ) : (
              <select
                id="branch-select"
                className="form-input"
                value={selectedBranch}
                onChange={(e) => {
                  setSelectedBranch(e.target.value);
                  setIdentifier(''); // Clear selection when branch changes
                  setPassword('');
                  setError('');
                }}
                required
                disabled={branches.length === 0}
              >
                <option value="">
                  {branches.length === 0 
                    ? '-- No Branches Available --' 
                    : '-- Select Branch --'}
                </option>
                {branches.map((branch) => (
                  <option key={branch.id} value={branch.id}>
                    {branch.name} - {branch.city}
                  </option>
                ))}
              </select>
            )}
            {branches.length === 0 && !loadingBranches && (
              <p className="form-help-text" style={{ color: '#d32f2f', marginTop: '4px' }}>
                No branches found. Please create branches first.
              </p>
            )}
          </div>

          {/* Staff Selection */}
          {userType === 'staff' && (
            <>
              <div className="form-group">
                <label htmlFor="staff-select" className="form-label">
                  Select Staff Member
                </label>
                {loadingStaff ? (
                  <div className="form-input" style={{ padding: '12px', textAlign: 'center', color: '#666' }}>
                    Loading staff members...
                  </div>
                ) : (
                <select
                  id="staff-select"
                  className="form-input"
                  value={identifier}
                  onChange={handleStaffSelect}
                  required
                    disabled={staffList.length === 0}
                >
                    <option value="">
                      {staffList.length === 0 
                        ? '-- No Staff Available --' 
                        : '-- Select Staff --'}
                    </option>
                  {staffList.map((staff) => (
                    <option key={staff.id} value={staff.mobile}>
                      {staff.name} ({staff.mobile})
                    </option>
                  ))}
                </select>
                )}
                {staffList.length === 0 && !loadingStaff && (
                  <p className="form-help-text" style={{ color: '#d32f2f', marginTop: '4px' }}>
                    No staff members found. Please insert dummy data using: python backend/insert_dummy_auth_data.py
                  </p>
                )}
              </div>

            </>
          )}

          {/* Manager Login */}
          {userType === 'manager' && (
            <>
              <div className="form-group">
                <label htmlFor="manager-select" className="form-label">
                  Select Manager
                </label>
                {loadingManagers ? (
                  <div className="form-input" style={{ padding: '12px', textAlign: 'center', color: '#666' }}>
                    Loading managers...
                  </div>
                ) : (
                  <select
                    id="manager-select"
                  className="form-input"
                  value={identifier}
                    onChange={(e) => {
                      const selectedManager = managerList.find(m => 
                        m.email === e.target.value || m.mobile === e.target.value
                      );
                      if (selectedManager) {
                        setIdentifier(selectedManager.email);
                      } else {
                        setIdentifier(e.target.value);
                      }
                    }}
                  required
                    disabled={managerList.length === 0}
                  >
                    <option value="">
                      {managerList.length === 0 
                        ? '-- No Managers Available --' 
                        : '-- Select Manager --'}
                    </option>
                    {managerList.map((manager) => (
                      <option key={manager.id} value={manager.email}>
                        {manager.name} - {manager.branch_name}
                      </option>
                    ))}
                  </select>
                )}
                {managerList.length === 0 && !loadingManagers && selectedBranch && (
                  <p className="form-help-text" style={{ color: '#d32f2f', marginTop: '4px' }}>
                    No managers found for this branch.
                    <br />
                    <span style={{ fontSize: '0.85em', color: '#666' }}>
                      Please ensure managers are assigned to this branch in the database.
                    </span>
                  </p>
                )}
              </div>

              {/* Password field is currently hidden for managers (feature paused) */}
              {/* Uncomment below to show password field when re-enabling password feature */}
              {/*
              <div className="form-group">
                <label htmlFor="password" className="form-label">
                  Password
                </label>
                <input
                  type="password"
                  id="password"
                  className="form-input"
                  placeholder="Enter your password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
              </div>
              */}
            </>
          )}

          {/* Owner Login */}
          {userType === 'owner' && (
            <>
              <div className="form-group">
                <label htmlFor="owner-email" className="form-label">
                  Enter Email Address
                </label>
                <input
                  type="email"
                  id="owner-email"
                  className="form-input"
                  placeholder="Enter your email address"
                  value={identifier}
                  onChange={(e) => setIdentifier(e.target.value)}
                  required
                />
              </div>

              {/* Password field is currently hidden for owners (feature paused) */}
              {/* Uncomment below to show password field when re-enabling password feature */}
              {/*
              <div className="form-group">
                <label htmlFor="password" className="form-label">
                  Password
                </label>
                <input
                  type="password"
                  id="password"
                  className="form-input"
                  placeholder="Enter your password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
              </div>
              */}
            </>
          )}

          {/* Error Message */}
          {error && (
            <div className="error-message" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <FaExclamationTriangle size={16} color="#ef4444" />
              {error}
            </div>
          )}

          {/* Submit Button */}
          <button
            type="submit"
            className="login-button"
            disabled={loading || !selectedBranch || (userType === 'staff' && staffList.length === 0) || (userType === 'manager' && (!selectedBranch || managerList.length === 0)) || (userType === 'owner' && !identifier.trim())}
          >
            {loading ? (
              <>
                <span className="loading-spinner"></span>
                Signing in...
              </>
            ) : (
              'Sign In'
            )}
          </button>
        </form>

        {/* Footer */}
        <div className="login-footer">
          <p className="footer-text">
            Secure login • Your data is protected
          </p>
        </div>
      </div>

      {/* Background Decoration */}
      <div className="login-background">
        <div className="bg-circle bg-circle-1"></div>
        <div className="bg-circle bg-circle-2"></div>
        <div className="bg-circle bg-circle-3"></div>
      </div>
    </div>
  );
};

export default Login;
