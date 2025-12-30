/**
 * API utility for making authenticated requests with branch support
 */
import { API_BASE_URL } from '../config';
import NProgress from 'nprogress';

/**
 * Get auth token from localStorage
 */
const getAuthToken = () => {
  return localStorage.getItem('auth_token');
};

/**
 * Get current branch ID from localStorage or context
 */
const getBranchId = () => {
  const storedBranch = localStorage.getItem('current_branch');
  if (storedBranch) {
    try {
      const branch = JSON.parse(storedBranch);
      if (branch && branch.id) {
        // Debug log to verify branch ID is being read
        console.log('[API] Using branch ID:', branch.id);
        return branch.id;
      }
    } catch (e) {
      console.error('Error parsing stored branch:', e);
    }
  }
  
  // Fallback: try to get from user data
  const storedUser = localStorage.getItem('auth_user');
  if (storedUser) {
    try {
      const user = JSON.parse(storedUser);
      if (user.branch_id) {
        console.log('[API] Using branch_id from user:', user.branch_id);
        return user.branch_id;
      }
      if (user.branch && user.branch.id) {
        console.log('[API] Using branch.id from user:', user.branch.id);
        return user.branch.id;
      }
    } catch (e) {
      console.error('Error parsing stored user:', e);
    }
  }
  
  console.log('[API] No branch ID found');
  return null;
};

/**
 * Make an authenticated API request with branch support
 * 
 * @param {string} endpoint - API endpoint (without base URL)
 * @param {object} options - Fetch options
 * @returns {Promise<Response>}
 */
export const apiRequest = async (endpoint, options = {}) => {
  const token = getAuthToken();
  const branchId = getBranchId();
  
  // Start progress bar
  NProgress.start();
  
  try {
    // Build headers
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };
    
    // Add auth token if available
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    
    // Add branch ID header if available (for Owner branch switching)
    if (branchId) {
      headers['X-Branch-Id'] = branchId;
      console.log('[API] Added X-Branch-Id header:', branchId);
    } else {
      console.log('[API] No branch ID to add to headers');
    }
    
    // Build full URL
    const url = endpoint.startsWith('http') ? endpoint : `${API_BASE_URL}${endpoint}`;
    
    // Make request
    const response = await fetch(url, {
      ...options,
      headers,
    });
    
    // Complete progress bar
    NProgress.done();
    
    return response;
  } catch (error) {
    // Ensure progress bar completes even on error
    NProgress.done();
    throw error;
  }
};

/**
 * GET request helper
 */
export const apiGet = async (endpoint, options = {}) => {
  return apiRequest(endpoint, {
    ...options,
    method: 'GET',
  });
};

/**
 * POST request helper
 */
export const apiPost = async (endpoint, data, options = {}) => {
  return apiRequest(endpoint, {
    ...options,
    method: 'POST',
    body: JSON.stringify(data),
  });
};

/**
 * PUT request helper
 */
export const apiPut = async (endpoint, data, options = {}) => {
  return apiRequest(endpoint, {
    ...options,
    method: 'PUT',
    body: JSON.stringify(data),
  });
};

/**
 * DELETE request helper
 */
export const apiDelete = async (endpoint, options = {}) => {
  return apiRequest(endpoint, {
    ...options,
    method: 'DELETE',
  });
};

/**
 * Update branch ID in localStorage (called when branch is switched)
 */
export const updateBranchId = (branch) => {
  if (branch) {
    localStorage.setItem('current_branch', JSON.stringify(branch));
  } else {
    localStorage.removeItem('current_branch');
  }
};

