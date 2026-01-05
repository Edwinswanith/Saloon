import React, { useState } from 'react'
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
  FaChevronUp,
  FaChevronDown,
  FaStar,
  FaExchangeAlt,
} from 'react-icons/fa'
import { useAuth } from '../contexts/AuthContext'
import './Sidebar.css'

const Sidebar = ({ activePage, setActivePage }) => {
  const { hasAnyRole, canAccess } = useAuth()
  const [expandedItems, setExpandedItems] = useState({
    'salon-settings': true,
    billing: true,
    customers: false,
  })

  const toggleExpand = (item) => {
    setExpandedItems((prev) => ({
      ...prev,
      [item]: !prev[item],
    }))
  }

  const handleNavClick = (itemId) => {
    if (itemId === 'dashboard') {
      setActivePage('dashboard')
    } else if (itemId === 'quick-sale') {
      setActivePage('quick-sale')
    } else if (itemId === 'cash-register') {
      setActivePage('cash-register')
    } else if (itemId === 'appointment') {
      setActivePage('appointment')
    } else if (itemId === 'customer-list') {
      setActivePage('customer-list')
    } else if (itemId === 'lead-management') {
      setActivePage('lead-management')
    } else if (itemId === 'missed-enquiries') {
      setActivePage('missed-enquiries')
    } else if (itemId === 'feedback') {
      setActivePage('feedback')
    } else if (itemId === 'service-recovery') {
      setActivePage('service-recovery')
    } else if (itemId === 'inventory') {
      setActivePage('inventory')
    } else if (itemId === 'reports' || itemId === 'analytics') {
      setActivePage('reports')
    } else if (itemId === 'service') {
      setActivePage('service')
    } else if (itemId === 'package') {
      setActivePage('package')
    } else if (itemId === 'product') {
      setActivePage('product')
    } else if (itemId === 'prepaid') {
      setActivePage('prepaid')
    } else if (itemId === 'settings') {
      setActivePage('settings')
    } else if (itemId === 'staffs') {
      setActivePage('staffs')
    } else if (itemId === 'staff-attendance') {
      setActivePage('staff-attendance')
    } else if (itemId === 'staff-temp-assignment') {
      setActivePage('staff-temp-assignment')
    } else if (itemId === 'asset-management') {
      setActivePage('asset-management')
    } else if (itemId === 'expense') {
      setActivePage('expense')
    } else if (itemId === 'discount-approvals') {
      setActivePage('discount-approvals')
    } else if (itemId === 'approval-codes') {
      setActivePage('approval-codes')
    }
  }

  const menuSections = [
    {
      section: 'ANALYTICS',
      items: [
        { 
          id: 'reports', 
          label: 'Reports & Analytics', 
          icon: <FaChartBar />,
          requiresRole: ['manager', 'owner'] // Only manager and owner can see reports
        }
      ],
    },
    {
      section: 'BILLING',
      items: [
        { 
          id: 'discount-approvals', 
          label: 'Discount Approvals', 
          icon: <FaDollarSign />,
          requiresRole: ['owner'] // Only owner can approve discounts
        },
        { 
          id: 'approval-codes', 
          label: 'Approval Codes', 
          icon: <FaDollarSign />,
          requiresRole: ['owner'] // Only owner can manage approval codes
        }
      ],
    },
    {
      section: 'MASTER',
      items: [
        {
          id: 'salon-settings',
          label: 'Salon Settings',
          icon: <FaClipboardList />,
          subItems: [
            { id: 'service', label: 'Service' },
            { id: 'package', label: 'Package' },
            { id: 'product', label: 'Product' },
            { id: 'prepaid', label: 'Prepaid' },
            { 
              id: 'settings', 
              label: 'Settings',
              requiresRole: ['manager', 'owner'] // Only manager and owner can see settings
            },
          ],
          expanded: expandedItems['salon-settings'],
        },
        { 
          id: 'staffs', 
          label: 'Staffs', 
          icon: <FaUser />,
          requiresRole: ['manager', 'owner'] // Only manager and owner can manage staff
        },
        { 
          id: 'staff-attendance', 
          label: 'Staff Attendance', 
          icon: <FaCheckCircle />,
          requiresRole: ['manager', 'owner'] // Only manager and owner can see attendance
        },
        { 
          id: 'staff-temp-assignment', 
          label: 'Staff Reassignment', 
          icon: <FaExchangeAlt />,
          requiresRole: ['manager', 'owner'] // Only manager and owner can reassign staff
        },
        { 
          id: 'asset-management', 
          label: 'Asset Management', 
          icon: <FaBriefcase />,
          requiresRole: ['manager', 'owner'] // Only manager and owner can manage assets
        },
        { 
          id: 'expense', 
          label: 'Expense', 
          icon: <FaDollarSign />,
          requiresRole: ['manager', 'owner'] // Only manager and owner can manage expenses
        },
      ],
    },
  ]

  const topMenuItems = [
    { id: 'dashboard', label: 'Dashboard', icon: <FaChartBar /> },
    {
      id: 'billing',
      label: 'Billing',
      icon: <FaCreditCard />,
      subItems: [{ id: 'quick-sale', label: 'Quick Sale' }],
      expanded: expandedItems.billing,
    },
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
  ]

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="logo">
          <FaStar />
          Bizzzup
        </div>
      </div>
      <nav className="sidebar-nav">
        {/* Top Menu Items */}
        {topMenuItems
          .filter((item) => {
            // Filter items based on role requirements
            if (item.requiresRole) {
              return hasAnyRole(...item.requiresRole)
            }
            return true
          })
          .map((item) => (
          <div key={item.id}>
            <div
              className={`nav-item ${
                activePage === item.id ? 'active' : ''
              } ${item.subItems ? 'has-submenu' : ''} ${
                item.subItems && expandedItems[item.id] ? 'expanded' : ''
              }`}
              onClick={() => {
                if (item.subItems) {
                  toggleExpand(item.id)
                } else {
                  handleNavClick(item.id)
                }
              }}
            >
              <span className="nav-icon">{item.icon}</span>
              <span className="nav-label">{item.label}</span>
              {item.subItems && (
                <span className="nav-arrow">
                  {expandedItems[item.id] ? <FaChevronUp /> : <FaChevronDown />}
                </span>
              )}
            </div>
            {item.subItems && expandedItems[item.id] && (
              <div className="submenu">
                {item.subItems
                  .filter((subItem) => {
                    // Filter sub-items based on role requirements
                    if (subItem.requiresRole) {
                      return hasAnyRole(...subItem.requiresRole)
                    }
                    return true
                  })
                  .map((subItem) => (
                  <div
                    key={subItem.id}
                    className={`submenu-item ${
                      activePage === subItem.id ? 'active' : ''
                    }`}
                    onClick={() => handleNavClick(subItem.id)}
                  >
                    <span className="submenu-icon">{item.icon}</span>
                    <span className="submenu-label">{subItem.label}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}

        {/* Sectioned Menu Items */}
        {menuSections.map((section, sectionIndex) => (
          <div key={section.section} className="menu-section">
            <div className="section-header">{section.section}</div>
            {section.items
              .filter((item) => {
                // Filter items based on role requirements
                if (item.requiresRole) {
                  return hasAnyRole(...item.requiresRole)
                }
                return true
              })
              .map((item) => (
              <div key={item.id}>
                <div
                  className={`nav-item ${
                    activePage === item.id ? 'active' : ''
                  } ${item.subItems ? 'has-submenu' : ''} ${
                    item.subItems && expandedItems[item.id] ? 'expanded' : ''
                  }`}
                  onClick={() => {
                    if (item.subItems) {
                      toggleExpand(item.id)
                    } else {
                      handleNavClick(item.id)
                    }
                  }}
                >
                  <span className="nav-icon">{item.icon}</span>
                  <span className="nav-label">{item.label}</span>
                  {item.subItems && (
                    <span className="nav-arrow">
                      {expandedItems[item.id] ? <FaChevronUp /> : <FaChevronDown />}
                    </span>
                  )}
                </div>
                {item.subItems && expandedItems[item.id] && (
                  <div className="submenu">
                    {item.subItems.map((subItem) => (
                      <div
                        key={subItem.id}
                        className={`submenu-item ${
                          activePage === subItem.id ? 'active' : ''
                        }`}
                        onClick={() => handleNavClick(subItem.id)}
                      >
                        <span className="submenu-label">{subItem.label}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        ))}
      </nav>
    </aside>
  )
}

export default Sidebar

