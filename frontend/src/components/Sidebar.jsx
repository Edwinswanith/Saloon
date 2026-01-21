import React, { useState, useEffect } from 'react'
import {
  FaChartBar,
  FaCreditCard,
  FaMoneyBillWave,
  FaCalendarAlt,
  FaUsers,
  FaBox,
  FaClipboardList,
  FaUser,
  FaCheckCircle,
  FaBriefcase,
  FaDollarSign,
  FaKey,
  FaChevronUp,
  FaChevronDown,
  FaChevronLeft,
  FaChevronRight,
  FaStar,
  FaExchangeAlt,
  FaTimes,
} from 'react-icons/fa'
import { useAuth } from '../contexts/AuthContext'
import './Sidebar.css'

/**
 * Modern Sidebar Component with Collapse/Expand Functionality
 *
 * @param {string} activePage - Currently active page ID
 * @param {function} setActivePage - Function to set active page
 * @param {function} onToggle - Function called when toggle button is clicked
 * @param {boolean} isCollapsed - Whether sidebar is collapsed (default: false)
 * @param {boolean} isMobileOpen - Whether sidebar is open on mobile (default: false)
 * @param {function} onMobileClose - Function to close sidebar on mobile
 */
const Sidebar = ({
  activePage,
  setActivePage,
  onToggle,
  isCollapsed = false,
  isMobileOpen = false,
  onMobileClose
}) => {
  const { hasAnyRole } = useAuth()
  const [expandedItems, setExpandedItems] = useState({
    'salon-settings': false,
    customers: false,
  })
  
  // Close submenus when sidebar collapses
  useEffect(() => {
    if (isCollapsed) {
      setExpandedItems({
        'salon-settings': false,
        customers: false,
      })
    }
  }, [isCollapsed])

  const toggleExpand = (item) => {
    setExpandedItems((prev) => ({
      ...prev,
      [item]: !prev[item],
    }))
  }

  const handleNavClick = (itemId) => {
    if (setActivePage) {
      setActivePage(itemId)
    }
  }

  // Menu configuration
  const menuConfig = {
    logo: {
      icon: <FaStar />,
      text: 'Priyanka Nature cure'
    },
    dashboardItem: { 
      id: 'dashboard', 
      label: 'Dashboard', 
      icon: <FaChartBar /> 
    },
    billingSection: {
      section: 'BILLING',
      items: [
        { id: 'quick-sale', label: 'Quick Sale', icon: <FaCreditCard /> },
        { id: 'cash-register', label: 'Cash Register', icon: <FaMoneyBillWave /> },
        { id: 'appointment', label: 'Appointment', icon: <FaCalendarAlt /> },
        {
          id: 'customers',
          label: 'Customers',
          icon: <FaUsers />,
          subItems: [
            { id: 'customer-list', label: 'Customer List' },
            { id: 'lead-management', label: 'Lead Management' },
            { id: 'missed-enquiries', label: 'Missed Enquiries' },
            { id: 'feedback', label: 'Feedback' },
            { id: 'service-recovery', label: 'Service Recovery', requiresRole: ['manager', 'owner'] },
          ],
          expanded: expandedItems.customers,
        },
        { id: 'inventory', label: 'Inventory', icon: <FaBox /> },
        { 
          id: 'discount-approvals', 
          label: 'Discount Approvals', 
          icon: <FaDollarSign />,
          requiresRole: ['owner']
        },
        { 
          id: 'approval-codes', 
          label: 'Approval Codes', 
          icon: <FaKey />,
          requiresRole: ['owner']
        }
      ],
    },
    analyticsSection: {
      section: 'ANALYTICS',
      items: [
        { 
          id: 'reports', 
          label: 'Reports & Analytics', 
          icon: <FaChartBar />,
          requiresRole: ['manager', 'owner']
        }
      ],
    },
    masterSection: {
      section: 'MASTER',
      items: [
        {
          id: 'salon-settings',
          label: 'Saloon Settings',
          icon: <FaClipboardList />,
          subItems: [
            { id: 'service', label: 'Service' },
            { id: 'package', label: 'Package' },
            { id: 'product', label: 'Product' },
            { id: 'prepaid', label: 'Prepaid' },
            { 
              id: 'settings', 
              label: 'Settings',
              requiresRole: ['manager', 'owner']
            },
          ],
          expanded: expandedItems['salon-settings'],
        },
        { 
          id: 'staffs', 
          label: 'Staffs', 
          icon: <FaUser />,
          requiresRole: ['manager', 'owner']
        },
        { 
          id: 'staff-attendance', 
          label: 'Staff Attendance', 
          icon: <FaCheckCircle />,
          requiresRole: ['manager', 'owner']
        },
        { 
          id: 'staff-temp-assignment', 
          label: 'Staff Reassignment', 
          icon: <FaExchangeAlt />,
          requiresRole: ['manager', 'owner']
        },
        { 
          id: 'asset-management', 
          label: 'Asset Management', 
          icon: <FaBriefcase />,
          requiresRole: ['manager', 'owner']
        },
        { 
          id: 'expense', 
          label: 'Expense', 
          icon: <FaDollarSign />,
          requiresRole: ['manager', 'owner']
        },
      ],
    },
  }

  const { logo, dashboardItem, billingSection, analyticsSection, masterSection } = menuConfig

  // Update expanded state for menu items
  if (billingSection.items) {
    billingSection.items.forEach(item => {
      if (item.id === 'customers') {
        item.expanded = expandedItems.customers
      }
    })
  }
  if (masterSection.items) {
    masterSection.items.forEach(item => {
      if (item.id === 'salon-settings') {
        item.expanded = expandedItems['salon-settings']
      }
    })
  }

  const renderMenuItem = (item, sectionKey = '') => {
    const itemKey = `${sectionKey}-${item.id}`
    const isActive = activePage === item.id
    const hasSubItems = item.subItems && item.subItems.length > 0
    const isExpanded = item.expanded || expandedItems[item.id]
    const shouldShow = !item.requiresRole || hasAnyRole(...item.requiresRole)

    if (!shouldShow) return null

    return (
      <div key={itemKey}>
        <div
          className={`nav-item ${isActive ? 'active' : ''} ${hasSubItems ? 'has-submenu' : ''} ${hasSubItems && isExpanded ? 'expanded' : ''}`}
          onClick={() => {
            if (isCollapsed && hasSubItems) {
              if (onToggle) onToggle()
              setTimeout(() => toggleExpand(item.id), 100)
            } else if (hasSubItems) {
              toggleExpand(item.id)
            } else {
              handleNavClick(item.id)
            }
          }}
          title={isCollapsed ? item.label : ''}
        >
          <span className="nav-icon">{item.icon}</span>
          <span className="nav-label">{item.label}</span>
          {hasSubItems && !isCollapsed && (
            <span className="nav-arrow">
              {isExpanded ? <FaChevronUp /> : <FaChevronDown />}
            </span>
          )}
        </div>
        {hasSubItems && isExpanded && !isCollapsed && (
          <div className="submenu">
            {item.subItems
              .filter((subItem) => !subItem.requiresRole || hasAnyRole(...subItem.requiresRole))
              .map((subItem) => (
                <div
                  key={subItem.id}
                  className={`submenu-item ${activePage === subItem.id ? 'active' : ''}`}
                  onClick={() => handleNavClick(subItem.id)}
                >
                  <span className="submenu-label">{subItem.label}</span>
                </div>
              ))}
          </div>
        )}
      </div>
    )
  }

  const renderSection = (section, sectionKey) => {
    if (!section || !section.items) return null

    return (
      <div key={sectionKey} className="menu-section">
        {!isCollapsed && section.section && (
          <div className="section-header">{section.section}</div>
        )}
        {section.items.map((item) => renderMenuItem(item, sectionKey))}
      </div>
    )
  }

  return (
    <>
      {/* Mobile backdrop overlay */}
      {isMobileOpen && (
        <div
          className="sidebar-backdrop"
          onClick={onMobileClose}
          aria-hidden="true"
        />
      )}
      <aside className={`sidebar ${isCollapsed ? 'collapsed' : ''} ${isMobileOpen ? 'mobile-open' : ''}`}>
        <div className="sidebar-header">
          {/* Desktop Toggle Button */}
          {onToggle && (
            <button
              className="sidebar-toggle desktop-toggle"
              onClick={onToggle}
              aria-label={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
              title={isCollapsed ? 'Open Menu' : 'Close Menu'}
            >
              {isCollapsed ? <FaChevronRight /> : <FaChevronLeft />}
            </button>
          )}

          {/* Mobile Close Button */}
          {onMobileClose && (
            <button
              className="sidebar-toggle mobile-close"
              onClick={onMobileClose}
              aria-label="Close sidebar"
              title="Close Menu"
            >
              <FaTimes />
            </button>
          )}

          <div className="logo">
            {!isCollapsed && (
              <img
                src="/logo/priyanka logo.png"
                alt="Priyanka Nature Cure"
                className="logo-image"
              />
            )}
          </div>
        </div>
      <nav className="sidebar-nav">
        {/* Dashboard - Standalone (first) */}
        {dashboardItem && (
          <div>
            <div
              className={`nav-item ${activePage === dashboardItem.id ? 'active' : ''}`}
              onClick={() => handleNavClick(dashboardItem.id)}
              title={isCollapsed ? dashboardItem.label : ''}
            >
              <span className="nav-icon">{dashboardItem.icon}</span>
              <span className="nav-label">{dashboardItem.label}</span>
            </div>
          </div>
        )}

        {/* BILLING Section */}
        {renderSection(billingSection, 'billing')}

        {/* ANALYTICS Section */}
        {renderSection(analyticsSection, 'analytics')}

        {/* MASTER Section */}
        {renderSection(masterSection, 'master')}
      </nav>
      </aside>
    </>
  )
}

export default Sidebar
