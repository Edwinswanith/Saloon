import React from 'react'
import { FaInbox, FaSearch, FaExclamationTriangle, FaUserFriends, FaClipboardList } from 'react-icons/fa'

// Empty Table - For empty data tables
export const EmptyTable = ({ title = "No Data Available", message = "There are no records to display at the moment." }) => {
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '60px 20px',
      textAlign: 'center',
      color: '#6b7280'
    }}>
      <div style={{
        width: '80px',
        height: '80px',
        borderRadius: '50%',
        background: 'linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        marginBottom: '24px'
      }}>
        <FaInbox size={36} color="#9ca3af" />
      </div>
      <h3 style={{ 
        fontSize: '18px', 
        fontWeight: '600', 
        color: '#374151', 
        marginBottom: '8px',
        margin: '0 0 8px 0'
      }}>
        {title}
      </h3>
      <p style={{ 
        fontSize: '14px', 
        color: '#6b7280', 
        maxWidth: '400px',
        margin: '0'
      }}>
        {message}
      </p>
    </div>
  )
}

// Empty Search - For no search results
export const EmptySearch = ({ searchQuery = "", message = "Try adjusting your search or filter criteria." }) => {
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '60px 20px',
      textAlign: 'center',
      color: '#6b7280'
    }}>
      <div style={{
        width: '80px',
        height: '80px',
        borderRadius: '50%',
        background: 'linear-gradient(135deg, #fef3c7 0%, #fde68a 100%)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        marginBottom: '24px'
      }}>
        <FaSearch size={32} color="#f59e0b" />
      </div>
      <h3 style={{ 
        fontSize: '18px', 
        fontWeight: '600', 
        color: '#374151', 
        marginBottom: '8px',
        margin: '0 0 8px 0'
      }}>
        No results found {searchQuery && `for "${searchQuery}"`}
      </h3>
      <p style={{ 
        fontSize: '14px', 
        color: '#6b7280', 
        maxWidth: '400px',
        margin: '0'
      }}>
        {message}
      </p>
    </div>
  )
}

// Empty List - For empty lists
export const EmptyList = ({ 
  icon: Icon = FaClipboardList,
  title = "Nothing Here Yet", 
  message = "Items will appear here once you add them.",
  actionText = null,
  onAction = null
}) => {
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '60px 20px',
      textAlign: 'center',
      color: '#6b7280'
    }}>
      <div style={{
        width: '80px',
        height: '80px',
        borderRadius: '50%',
        background: 'linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        marginBottom: '24px'
      }}>
        <Icon size={36} color="#3b82f6" />
      </div>
      <h3 style={{ 
        fontSize: '18px', 
        fontWeight: '600', 
        color: '#374151', 
        marginBottom: '8px',
        margin: '0 0 8px 0'
      }}>
        {title}
      </h3>
      <p style={{ 
        fontSize: '14px', 
        color: '#6b7280', 
        maxWidth: '400px',
        margin: '0 0 16px 0'
      }}>
        {message}
      </p>
      {actionText && onAction && (
        <button
          onClick={onAction}
          style={{
            padding: '10px 20px',
            background: '#3b82f6',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            fontSize: '14px',
            fontWeight: '500',
            cursor: 'pointer',
            transition: 'all 0.2s'
          }}
          onMouseEnter={(e) => e.target.style.background = '#2563eb'}
          onMouseLeave={(e) => e.target.style.background = '#3b82f6'}
        >
          {actionText}
        </button>
      )}
    </div>
  )
}

// Empty Customers - Specific for customer list
export const EmptyCustomers = ({ onAddCustomer = null }) => {
  return (
    <EmptyList
      icon={FaUserFriends}
      title="No Customers Yet"
      message="Start building your customer base by adding your first customer."
      actionText={onAddCustomer ? "Add First Customer" : null}
      onAction={onAddCustomer}
    />
  )
}

// Empty Error State - For errors
export const EmptyError = ({ title = "Something Went Wrong", message = "We encountered an error. Please try again later." }) => {
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '60px 20px',
      textAlign: 'center',
      color: '#6b7280'
    }}>
      <div style={{
        width: '80px',
        height: '80px',
        borderRadius: '50%',
        background: 'linear-gradient(135deg, #fee2e2 0%, #fecaca 100%)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        marginBottom: '24px'
      }}>
        <FaExclamationTriangle size={36} color="#ef4444" />
      </div>
      <h3 style={{ 
        fontSize: '18px', 
        fontWeight: '600', 
        color: '#374151', 
        marginBottom: '8px',
        margin: '0 0 8px 0'
      }}>
        {title}
      </h3>
      <p style={{ 
        fontSize: '14px', 
        color: '#6b7280', 
        maxWidth: '400px',
        margin: '0'
      }}>
        {message}
      </p>
    </div>
  )
}

export default {
  EmptyTable,
  EmptySearch,
  EmptyList,
  EmptyCustomers,
  EmptyError
}

