import React, { createContext, useState, useContext, useEffect } from 'react';
import { API_BASE_URL } from '../config';

// Create the AuthContext
const AuthContext = createContext(null);

// Custom hook to use the AuthContext
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// AuthProvider component
export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [currentBranch, setCurrentBranch] = useState(null);
  const [branches, setBranches] = useState([]);

  // Initialize authentication state from localStorage on mount
  useEffect(() => {
    const initAuth = async () => {
      try {
        const storedToken = localStorage.getItem('auth_token');
        const storedUser = localStorage.getItem('auth_user');
        const storedBranch = localStorage.getItem('current_branch');

        if (storedToken && storedUser) {
          setToken(storedToken);
          const userData = JSON.parse(storedUser);
          setUser(userData);
          setIsAuthenticated(true);

          // Validate token by fetching current user info
          await validateToken(storedToken);
          
          // Load branches if user is authenticated
          if (userData && userData.role === 'owner') {
            await fetchBranches();
          }
          
          // Set current branch from storage or user's branch
          if (storedBranch) {
            const branchData = JSON.parse(storedBranch);
            setCurrentBranch(branchData);
          } else if (userData && userData.branch) {
            setCurrentBranch(userData.branch);
            localStorage.setItem('current_branch', JSON.stringify(userData.branch));
          } else if (userData && userData.branch_id) {
            // If only branch_id is available, fetch branch details
            await fetchBranches();
            const branch = branches.find(b => b.id === userData.branch_id);
            if (branch) {
              setCurrentBranch(branch);
              localStorage.setItem('current_branch', JSON.stringify(branch));
            }
          }
        }
      } catch (error) {
        console.error('Auth initialization error:', error);
        // Clear invalid auth data
        logout();
      } finally {
        setLoading(false);
      }
    };

    initAuth();
  }, []);

  // Validate token with backend
  const validateToken = async (authToken) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/auth/me`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Token validation failed');
      }

      const data = await response.json();

      // Update user data with latest from server
      setUser(data.user);
      localStorage.setItem('auth_user', JSON.stringify(data.user));

      return data.user;
    } catch (error) {
      console.error('Token validation error:', error);
      // Token is invalid, clear auth
      logout();
      throw error;
    }
  };

  // Login function
  const login = async (loginData) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(loginData),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || data.message || 'Login failed');
      }

      // Store token and user data
      setToken(data.token);
      setUser(data.user);
      setIsAuthenticated(true);

      localStorage.setItem('auth_token', data.token);
      localStorage.setItem('auth_user', JSON.stringify(data.user));
      
      // Set branch from login response (prioritize branch object, then branch_id)
      if (data.branch) {
        // Use branch from response (most complete)
        setCurrentBranch(data.branch);
        localStorage.setItem('current_branch', JSON.stringify(data.branch));
      } else if (data.user.branch) {
        // Fallback to user.branch
        setCurrentBranch(data.user.branch);
        localStorage.setItem('current_branch', JSON.stringify(data.user.branch));
      } else if (data.branch_id || data.user.branch_id) {
        // If only branch_id is available, fetch branch details
        const branchId = data.branch_id || data.user.branch_id;
        if (data.user.role === 'owner') {
          // Owner can access all branches, fetch list
          await fetchBranches();
          const branch = branches.find(b => b.id === branchId);
          if (branch) {
            setCurrentBranch(branch);
            localStorage.setItem('current_branch', JSON.stringify(branch));
          } else {
            // Store branch_id if branch details not available
            setCurrentBranch({ id: branchId, name: 'Branch' });
            localStorage.setItem('current_branch', JSON.stringify({ id: branchId, name: 'Branch' }));
          }
        } else {
          // For staff/manager, store branch_id
          setCurrentBranch({ id: branchId, name: 'Branch' });
          localStorage.setItem('current_branch', JSON.stringify({ id: branchId, name: 'Branch' }));
        }
      }
      
      // Fetch branches if user is Owner (if not already fetched)
      if (data.user.role === 'owner' && branches.length === 0) {
        await fetchBranches();
      }

      return { success: true, user: data.user, role: data.role };
    } catch (error) {
      console.error('Login error:', error);
      return { success: false, error: error.message };
    }
  };

  // Logout function
  const logout = async () => {
    try {
      // Call logout endpoint if token exists
      if (token) {
        await fetch(`${API_BASE_URL}/api/auth/logout`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        });
      }
    } catch (error) {
      console.error('Logout API error:', error);
      // Continue with client-side logout even if API call fails
    } finally {
      // Clear all auth state
      setToken(null);
      setUser(null);
      setIsAuthenticated(false);
      setCurrentBranch(null);
      setBranches([]);
      localStorage.removeItem('auth_token');
      localStorage.removeItem('auth_user');
      localStorage.removeItem('current_branch');
    }
  };

  // Update user function (for profile updates)
  const updateUser = (newUserData) => {
    setUser(newUserData);
    localStorage.setItem('auth_user', JSON.stringify(newUserData));
  };

  // Change password function
  const changePassword = async (oldPassword, newPassword) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/auth/change-password`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          old_password: oldPassword,
          new_password: newPassword,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || data.message || 'Password change failed');
      }

      return { success: true, message: data.message };
    } catch (error) {
      console.error('Change password error:', error);
      return { success: false, error: error.message };
    }
  };

  // Check if user has specific role
  const hasRole = (requiredRole) => {
    if (!user || !user.role) return false;

    // Owner has access to everything
    if (user.role === 'owner') return true;

    // Manager has access to manager and staff roles
    if (user.role === 'manager' && (requiredRole === 'manager' || requiredRole === 'staff')) {
      return true;
    }

    // Exact role match
    return user.role === requiredRole;
  };

  // Check if user has any of the specified roles
  const hasAnyRole = (...roles) => {
    if (!user || !user.role) return false;

    // Owner has access to everything
    if (user.role === 'owner') return true;

    return roles.includes(user.role);
  };

  // Check if user can access specific features
  const canAccess = (feature) => {
    if (!user || !user.role) return false;

    // Owner can access everything
    if (user.role === 'owner') return true;

    // Define access rules for each feature
    const accessRules = {
      // Reports and Analytics
      'reports': ['manager', 'owner'],
      'analytics': ['manager', 'owner'],
      'financial_reports': ['manager', 'owner'],
      'staff_reports': ['manager', 'owner'],
      'export_data': ['manager', 'owner'],

      // Settings and Configuration
      'settings': ['manager', 'owner'],
      'tax_settings': ['owner'],
      'loyalty_settings': ['owner'],
      'membership_settings': ['owner'],

      // Staff Management
      'manage_staff': ['manager', 'owner'],
      'staff_attendance': ['manager', 'owner'],
      'staff_incentives': ['manager', 'owner'],

      // Discount Management - Owner only
      'apply_discounts': ['owner'],
      'approve_discounts': ['owner'],
      'view_discount_approvals': ['owner'],

      // Manager Functions
      'view_manager_dashboard': ['manager', 'owner'],
      'manage_managers': ['owner'],

      // Basic Operations (all roles)
      'create_bills': ['staff', 'manager', 'owner'],
      'create_appointments': ['staff', 'manager', 'owner'],
      'manage_customers': ['staff', 'manager', 'owner'],
      'manage_inventory': ['staff', 'manager', 'owner'],
    };

    const allowedRoles = accessRules[feature];
    if (!allowedRoles) {
      // If feature is not defined, deny access by default
      return false;
    }

    return allowedRoles.includes(user.role);
  };

  // Get maximum discount percentage user can apply - Only owner can apply discounts
  const getMaxDiscountPercent = () => {
    if (!user || !user.role) return 0;

    const discountLimits = {
      'staff': 0,      // No discount access
      'manager': 0,    // No discount access
      'owner': 100,    // Unlimited (only owner)
    };

    return discountLimits[user.role] || 0;
  };
  
  // Fetch all branches (Owner only)
  const fetchBranches = async () => {
    try {
      if (!token) return;
      
      const response = await fetch(`${API_BASE_URL}/api/branches`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch branches');
      }

      const data = await response.json();
      setBranches(data);
      return data;
    } catch (error) {
      console.error('Fetch branches error:', error);
      return [];
    }
  };
  
  // Switch branch (Owner only)
  const switchBranch = async (branchId) => {
    try {
      if (!token || !user || user.role !== 'owner') {
        throw new Error('Only Owner can switch branches');
      }
      
      const response = await fetch(`${API_BASE_URL}/api/auth/switch-branch`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ branch_id: branchId }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Failed to switch branch');
      }

      // Update current branch
      if (data.branch) {
        setCurrentBranch(data.branch);
        localStorage.setItem('current_branch', JSON.stringify(data.branch));
      }
      
      return { success: true, branch: data.branch };
    } catch (error) {
      console.error('Switch branch error:', error);
      return { success: false, error: error.message };
    }
  };
  
  // Get branch ID for API requests
  const getBranchId = () => {
    if (currentBranch) {
      return currentBranch.id;
    }
    if (user && user.branch_id) {
      return user.branch_id;
    }
    if (user && user.branch && user.branch.id) {
      return user.branch.id;
    }
    return null;
  };

  // Context value
  const value = {
    user,
    token,
    loading,
    isAuthenticated,
    currentBranch,
    branches,
    login,
    logout,
    updateUser,
    changePassword,
    validateToken,
    hasRole,
    hasAnyRole,
    canAccess,
    getMaxDiscountPercent,
    fetchBranches,
    switchBranch,
    getBranchId,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

// HOC for protected components
export const withAuth = (Component) => {
  return (props) => {
    const auth = useAuth();

    if (auth.loading) {
      return (
        <div style={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          height: '100vh'
        }}>
          <div>Loading...</div>
        </div>
      );
    }

    if (!auth.isAuthenticated) {
      return (
        <div style={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          height: '100vh'
        }}>
          <div>Please log in to access this page.</div>
        </div>
      );
    }

    return <Component {...props} auth={auth} />;
  };
};

// Component for role-based rendering
export const RequireRole = ({ roles, children, fallback = null }) => {
  const { hasAnyRole } = useAuth();

  if (!hasAnyRole(...roles)) {
    return fallback;
  }

  return <>{children}</>;
};

// Component for feature-based rendering
export const RequireFeature = ({ feature, children, fallback = null }) => {
  const { canAccess } = useAuth();

  if (!canAccess(feature)) {
    return fallback;
  }

  return <>{children}</>;
};

export default AuthContext;
