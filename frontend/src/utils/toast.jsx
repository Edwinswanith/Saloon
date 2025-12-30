/**
 * Toast Notification Utilities
 * Centralized wrapper for react-hot-toast
 * Use these instead of alert() for better UX
 */

import toast from 'react-hot-toast'

/**
 * Show success notification
 * @param {string} message - Success message to display
 * @param {object} options - Additional toast options
 */
export const showSuccess = (message, options = {}) => {
  return toast.success(message, {
    ...options,
    style: {
      background: '#f0fdf4',
      color: '#166534',
      border: '1px solid #86efac',
      ...options.style,
    },
  })
}

/**
 * Show error notification
 * @param {string} message - Error message to display
 * @param {object} options - Additional toast options
 */
export const showError = (message, options = {}) => {
  return toast.error(message, {
    ...options,
    style: {
      background: '#fef2f2',
      color: '#991b1b',
      border: '1px solid #fca5a5',
      ...options.style,
    },
  })
}

/**
 * Show warning notification
 * @param {string} message - Warning message to display
 * @param {object} options - Additional toast options
 */
export const showWarning = (message, options = {}) => {
  return toast(message, {
    icon: '⚠️',
    ...options,
    style: {
      background: '#fffbeb',
      color: '#92400e',
      border: '1px solid #fcd34d',
      ...options.style,
    },
  })
}

/**
 * Show info notification
 * @param {string} message - Info message to display
 * @param {object} options - Additional toast options
 */
export const showInfo = (message, options = {}) => {
  return toast(message, {
    icon: 'ℹ️',
    ...options,
    style: {
      background: '#eff6ff',
      color: '#1e40af',
      border: '1px solid #93c5fd',
      ...options.style,
    },
  })
}

/**
 * Show loading notification
 * @param {string} message - Loading message to display
 * @param {object} options - Additional toast options
 * @returns {string} Toast ID to dismiss later
 */
export const showLoading = (message, options = {}) => {
  return toast.loading(message, options)
}

/**
 * Dismiss a specific toast or all toasts
 * @param {string} toastId - Optional toast ID to dismiss specific toast
 */
export const dismissToast = (toastId) => {
  if (toastId) {
    toast.dismiss(toastId)
  } else {
    toast.dismiss()
  }
}

/**
 * Show promise-based toast (useful for async operations)
 * @param {Promise} promise - Promise to track
 * @param {object} messages - Messages for loading, success, and error states
 * @param {object} options - Additional toast options
 */
export const showPromise = (
  promise,
  messages = {
    loading: 'Loading...',
    success: 'Success!',
    error: 'Error occurred',
  },
  options = {}
) => {
  return toast.promise(promise, messages, options)
}

/**
 * Show confirmation toast with action button
 * @param {string} message - Confirmation message
 * @param {function} onConfirm - Callback when confirmed
 * @param {object} options - Additional toast options
 */
export const showConfirm = (message, onConfirm, options = {}) => {
  return toast(
    (t) => (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        <span>{message}</span>
        <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
          <button
            onClick={() => {
              toast.dismiss(t.id)
            }}
            style={{
              padding: '6px 12px',
              border: '1px solid #d1d5db',
              borderRadius: '4px',
              background: '#fff',
              cursor: 'pointer',
            }}
          >
            Cancel
          </button>
          <button
            onClick={() => {
              onConfirm()
              toast.dismiss(t.id)
            }}
            style={{
              padding: '6px 12px',
              border: 'none',
              borderRadius: '4px',
              background: '#3b82f6',
              color: '#fff',
              cursor: 'pointer',
            }}
          >
            Confirm
          </button>
        </div>
      </div>
    ),
    {
      duration: 10000,
      ...options,
    }
  )
}

// Export the base toast for custom use cases
export default toast

