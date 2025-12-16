import React, { useState } from 'react'
import {
  FaBars,
  FaUser,
  FaChartBar,
  FaClipboardList,
  FaTrash,
  FaChartLine,
  FaCreditCard,
  FaUsers,
  FaDollarSign,
  FaFileAlt,
  FaBox,
  FaCalendarAlt,
  FaCheckCircle,
  FaThumbsUp,
  FaPlus,
  FaBolt,
  FaQuestionCircle,
  FaGift,
  FaExchangeAlt,
} from 'react-icons/fa'
import './ReportsAnalytics.css'

const ReportsAnalytics = ({ setActivePage }) => {
  const [activeTab, setActiveTab] = useState('operational')

  const handleReportClick = (reportId) => {
    // Handle Analytics Dashboard reports first
    if (activeTab === 'analytics') {
      if (reportId === 1) {
        // Business Growth & Trend Analysis
        if (setActivePage) {
          setActivePage('business-growth-trend-analysis')
        }
        return
      } else if (reportId === 2) {
        // Staff Performance Analysis
        if (setActivePage) {
          setActivePage('staff-performance-analysis')
        }
        return
      } else if (reportId === 3) {
        // Period Performance Summary
        if (setActivePage) {
          setActivePage('period-performance-summary')
        }
        return
      } else if (reportId === 4) {
        // Client Value & Loyalty Report
        if (setActivePage) {
          setActivePage('client-value-loyalty-report')
        }
        return
      } else if (reportId === 5) {
        // Customer Behavior Insights
        alert('Customer Behavior Insights is coming soon!')
        return
      } else if (reportId === 6) {
        // Single Visit Client Analysis
        alert('Single Visit Client Analysis is coming soon!')
        return
      } else if (reportId === 7) {
        // Service & Product Performance
        alert('Service & Product Performance is coming soon!')
        return
      } else if (reportId === 8) {
        // Discount & Coupon Analysis
        alert('Discount & Coupon Analysis is coming soon!')
        return
      } else if (reportId === 9) {
        // Retail vs. Service Revenue
        alert('Retail vs. Service Revenue is coming soon!')
        return
      }
    }

    // Handle Operational Reports
    if (activeTab === 'operational') {
      if (reportId === 1) {
        // Service Sales Analysis
        if (setActivePage) {
          setActivePage('service-sales-analysis')
        }
        return
      } else if (reportId === 2) {
        // List of Bills
        if (setActivePage) {
          setActivePage('list-of-bills')
        }
        return
      } else if (reportId === 3) {
        // List of Deleted Bills
        if (setActivePage) {
          setActivePage('list-of-deleted-bills')
        }
        return
      } else if (reportId === 4) {
        // Sales by Service Group
        if (setActivePage) {
          setActivePage('sales-by-service-group')
        }
        return
      } else if (reportId === 5) {
        // Prepaid Package Clients
        if (setActivePage) {
          setActivePage('prepaid-package-clients')
        }
        return
      } else if (reportId === 6) {
        // Membership Clients
        if (setActivePage) {
          setActivePage('membership-clients')
        }
        return
      } else if (reportId === 7) {
        // Staff Performance Report
        if (setActivePage) {
          setActivePage('staff-incentive-report')
        }
        return
      } else if (reportId === 8) {
        // Expense Report
        if (setActivePage) {
          setActivePage('expense-report')
        }
        return
      } else if (reportId === 9) {
        // Inventory & Stock Report
        if (setActivePage) {
          setActivePage('inventory-report')
        }
        return
      } else if (reportId === 10) {
        // Appointment Report
        if (setActivePage) {
          setActivePage('appointments')
        }
        return
      } else if (reportId === 11) {
        // Employee Utilization Report
        if (setActivePage) {
          setActivePage('staff-attendance')
        }
        return
      } else if (reportId === 12) {
        // Client Referral Report
        if (setActivePage) {
          setActivePage('referral-program')
        }
        return
      } else if (reportId === 13) {
        // Staff Performance & Bill Report (Staff Combined Report)
        if (setActivePage) {
          setActivePage('staff-combined-report')
        }
        return
      }
    }

    // Handle Customer Reports
    if (activeTab === 'customer') {
      // TODO: Add customer report pages when created
      return
    }
  }

  const operationalReports = [
    {
      id: 1,
      title: 'Service Sales Analysis',
      description:
        'Analyze the performance of individual services (Good vs Bad performing).',
      icon: <FaChartBar />,
      color: 'blue',
    },
    {
      id: 2,
      title: 'List of Bills',
      description:
        'View and export a detailed list of all bills generated within a specific date range.',
      icon: <FaClipboardList />,
      color: 'dark-blue',
    },
    {
      id: 3,
      title: 'List of Deleted Bills',
      description:
        'View a log of all bills that were deleted, including the reason and value.',
      icon: <FaTrash />,
      color: 'red',
    },
    {
      id: 4,
      title: 'Sales by Service Group',
      description:
        'View a summary of sales categorized by service group for a selected period.',
      icon: <FaChartLine />,
      color: 'blue',
    },
    {
      id: 5,
      title: 'Prepaid Package Clients',
      description:
        'View a list of all clients with active prepaid packages and their remaining balances.',
      icon: <FaCreditCard />,
      color: 'orange',
    },
    {
      id: 6,
      title: 'Membership Clients',
      description:
        'View a list of all clients with active memberships and their expiration dates.',
      icon: <FaUsers />,
      color: 'green',
    },
    {
      id: 7,
      title: 'Staff Performance Report',
      description:
        'Calculate and view commission earned by each staff member for a selected period.',
      icon: <FaDollarSign />,
      color: 'dark-blue',
    },
    {
      id: 8,
      title: 'Expense Report',
      description:
        'View and export a detailed list of all logged expenses, filterable by category.',
      icon: <FaFileAlt />,
      color: 'red',
    },
    {
      id: 9,
      title: 'Inventory & Stock Report',
      description:
        'View current stock levels for all retail products and identify items that are running low.',
      icon: <FaBox />,
      color: 'blue',
    },
    {
      id: 10,
      title: 'Appointment Report',
      description:
        'View a detailed list of all appointments, filterable by status, staff, or service.',
      icon: <FaCalendarAlt />,
      color: 'orange',
    },
    {
      id: 11,
      title: 'Employee Utilization Report',
      description:
        'Analyze staff productivity by showing how much of their available time is booked.',
      icon: <FaCheckCircle />,
      color: 'green',
    },
    {
      id: 12,
      title: 'Client Referral Report',
      description:
        'Track which clients are referring new customers and measure the success of your referral program.',
      icon: <FaThumbsUp />,
      color: 'blue',
    },
    {
      id: 13,
      title: 'Staff Performance & Bill Report',
      description:
        'View staff performance summaries and detailed bill breakdowns.',
      icon: <FaUser />,
      color: 'blue',
    },
  ]

  const customerReports = [
    {
      id: 1,
      title: 'Customer Lifecycle Report',
      description:
        'View active, churn-risk, and defected clients based on their last visit.',
      icon: <FaUsers />,
      color: 'green',
      comingSoon: false,
    },
    {
      id: 2,
      title: 'New vs. Returning Value (Coming Soon)',
      description:
        'Compare revenue, visits, and AOV from new vs. returning clients.',
      icon: <FaPlus />,
      color: 'gray',
      comingSoon: true,
    },
    {
      id: 3,
      title: 'High-Value (VIP) Clients (Coming Soon)',
      description:
        'Identify your top clients by total spending and visit frequency.',
      icon: <FaDollarSign />,
      color: 'gray',
      comingSoon: true,
    },
  ]

  const analyticsDashboard = [
    // Business Performance
    {
      id: 1,
      title: 'Business Growth & Trend Analysis',
      description:
        "Answers 'Is my business growing, and why?' by analyzing long-term revenue and client trends.",
      icon: <FaChartBar />,
      color: 'blue',
      section: 'business',
    },
    {
      id: 2,
      title: 'Staff Performance Analysis',
      description:
        "Answers 'Who are my top-performing staff?' by breaking down revenue by each staff member.",
      icon: <FaBolt />,
      color: 'blue',
      section: 'business',
    },
    {
      id: 3,
      title: 'Period Performance Summary',
      description:
        "Provides a detailed financial summary for a specific period like 'Last Month' or 'Last Week'.",
      icon: <FaChartLine />,
      color: 'orange',
      section: 'business',
    },
    // Client Analytics
    {
      id: 4,
      title: 'Client Value & Loyalty Report',
      description:
        "Answers 'Who are my most valuable clients?' by identifying your VIPs and top spenders.",
      icon: <FaUsers />,
      color: 'green',
      section: 'client',
    },
    {
      id: 5,
      title: 'Customer Behavior Insights',
      description:
        "Answers 'How do my clients behave?' by analyzing visit frequency and service combinations.",
      icon: <FaUser />,
      color: 'red',
      section: 'client',
    },
    {
      id: 6,
      title: 'Single Visit Client Analysis',
      description:
        "Answers 'Why aren't some new clients returning?' by analyzing their first and only visit.",
      icon: <FaQuestionCircle />,
      color: 'dark-blue',
      section: 'client',
    },
    // Sales & Service Analytics
    {
      id: 7,
      title: 'Service & Product Performance',
      description:
        "Answers 'What are my best-selling services?' by analyzing revenue by category and product.",
      icon: <FaFileAlt />,
      color: 'light-blue',
      section: 'sales',
    },
    {
      id: 8,
      title: 'Discount & Coupon Analysis',
      description:
        'Analyzes the impact of discounts on revenue and which coupons are most effective.',
      icon: <FaGift />,
      color: 'yellow',
      section: 'sales',
    },
    {
      id: 9,
      title: 'Retail vs. Service Revenue',
      description:
        'Compares the revenue generated from product sales versus services performed.',
      icon: <FaExchangeAlt />,
      color: 'green',
      section: 'sales',
    },
  ]

  const getReportsForTab = () => {
    switch (activeTab) {
      case 'operational':
        return operationalReports
      case 'customer':
        return customerReports
      case 'analytics':
        return analyticsDashboard
      default:
        return operationalReports
    }
  }

  return (
    <div className="reports-analytics-page">
      {/* Header */}
      <header className="reports-analytics-header">
        <div className="header-left">
          <button className="menu-icon"><FaBars /></button>
          <h1 className="header-title">Reports & Analytics</h1>
        </div>
        <div className="header-right">
          <button className="user-icon"><FaUser /></button>
          <div className="logo-box">
            <span className="logo-text">HAIR STUDIO</span>
          </div>
        </div>
      </header>

      <div className="reports-analytics-container">
        {/* Reports Card */}
        <div className="reports-card">
          {/* Tabs */}
          <div className="reports-tabs">
            <button
              className={`tab ${activeTab === 'operational' ? 'active' : ''}`}
              onClick={() => setActiveTab('operational')}
            >
              Operational Reports
            </button>
            <button
              className={`tab ${activeTab === 'customer' ? 'active' : ''}`}
              onClick={() => setActiveTab('customer')}
            >
              Customer Reports
            </button>
            <button
              className={`tab ${activeTab === 'analytics' ? 'active' : ''}`}
              onClick={() => setActiveTab('analytics')}
            >
              Analytics Dashboard
            </button>
          </div>

          {/* Report Cards Grid */}
          {activeTab === 'analytics' ? (
            <div className="analytics-sections">
              {/* Business Performance */}
              <div className="analytics-section">
                <h3 className="section-title">
                  <FaCheckCircle className="section-icon" />
                  Business Performance
                </h3>
                <div className="reports-grid">
                  {analyticsDashboard
                    .filter((report) => report.section === 'business')
                    .map((report) => (
                      <div 
                        key={report.id} 
                        className="report-card"
                        onClick={() => handleReportClick(report.id)}
                        style={{ cursor: 'pointer' }}
                      >
                        <div className={`report-icon ${report.color}`}>
                          {report.icon}
                        </div>
                        <h3 className="report-title">{report.title}</h3>
                        <p className="report-description">{report.description}</p>
                      </div>
                    ))}
                </div>
              </div>

              {/* Client Analytics */}
              <div className="analytics-section">
                <h3 className="section-title">
                  <FaCheckCircle className="section-icon" />
                  Client Analytics
                </h3>
                <div className="reports-grid">
                  {analyticsDashboard
                    .filter((report) => report.section === 'client')
                    .map((report) => (
                      <div 
                        key={report.id} 
                        className="report-card"
                        onClick={() => handleReportClick(report.id)}
                        style={{ cursor: 'pointer' }}
                      >
                        <div className={`report-icon ${report.color}`}>
                          {report.icon}
                        </div>
                        <h3 className="report-title">{report.title}</h3>
                        <p className="report-description">{report.description}</p>
                      </div>
                    ))}
                </div>
              </div>

              {/* Sales & Service Analytics */}
              <div className="analytics-section">
                <h3 className="section-title">
                  <FaCheckCircle className="section-icon" />
                  Sales & Service Analytics
                </h3>
                <div className="reports-grid">
                  {analyticsDashboard
                    .filter((report) => report.section === 'sales')
                    .map((report) => (
                      <div 
                        key={report.id} 
                        className="report-card"
                        onClick={() => handleReportClick(report.id)}
                        style={{ cursor: 'pointer' }}
                      >
                        <div className={`report-icon ${report.color}`}>
                          {report.icon}
                        </div>
                        <h3 className="report-title">{report.title}</h3>
                        <p className="report-description">{report.description}</p>
                      </div>
                    ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="reports-grid">
              {getReportsForTab().length > 0 ? (
                getReportsForTab().map((report) => (
                  <div
                    key={report.id}
                    className={`report-card ${report.comingSoon ? 'coming-soon' : ''}`}
                    onClick={() => !report.comingSoon && handleReportClick(report.id)}
                    style={!report.comingSoon ? { cursor: 'pointer' } : {}}
                  >
                    <div className={`report-icon ${report.color}`}>
                      {report.icon}
                    </div>
                    <h3 className="report-title">{report.title}</h3>
                    <p className="report-description">{report.description}</p>
                  </div>
                ))
              ) : (
                <div className="empty-state">
                  <p>No reports available for this section.</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default ReportsAnalytics

