import React, { useState, useEffect } from 'react'
import { FaBars, FaBell, FaUser } from 'react-icons/fa'
import './Dashboard.css'
import { API_BASE_URL } from '../config'

const Dashboard = () => {
  const [activeTab, setActiveTab] = useState('staff')
  const [filter, setFilter] = useState('yesterday')
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState({
    totalTax: 0,
    grossRevenue: 0,
    avgBillValue: 0,
    transactions: 0,
    expenses: 0,
    deletedBills: 0,
    deletedBillsAmount: 0,
  })
  const [staffPerformance, setStaffPerformance] = useState([])
  const [topCustomers, setTopCustomers] = useState([])
  const [topOfferings, setTopOfferings] = useState([])
  const [revenueBreakdown, setRevenueBreakdown] = useState({
    service: 0,
    product: 0,
    package: 0,
    prepaid: 0,
    membership: 0,
  })
  const [paymentDistribution, setPaymentDistribution] = useState([])
  const [clientFunnel, setClientFunnel] = useState({
    newClients: 0,
    returningClients: 0,
    totalLeads: 0,
    contacted: 0,
    followups: 0,
    completed: 0,
    lost: 0,
  })
  const [alerts, setAlerts] = useState([])

  const getDateRange = () => {
    const today = new Date()
    const yesterday = new Date(today)
    yesterday.setDate(yesterday.getDate() - 1)
    const weekStart = new Date(today)
    weekStart.setDate(today.getDate() - today.getDay())
    const monthStart = new Date(today.getFullYear(), today.getMonth(), 1)
    const yearStart = new Date(today.getFullYear(), 0, 1)

    switch (filter) {
      case 'today':
        return {
          start_date: today.toISOString().split('T')[0],
          end_date: today.toISOString().split('T')[0],
        }
      case 'yesterday':
        return {
          start_date: yesterday.toISOString().split('T')[0],
          end_date: yesterday.toISOString().split('T')[0],
        }
      case 'week':
        return {
          start_date: weekStart.toISOString().split('T')[0],
          end_date: today.toISOString().split('T')[0],
        }
      case 'month':
        return {
          start_date: monthStart.toISOString().split('T')[0],
          end_date: today.toISOString().split('T')[0],
        }
      case 'year':
        return {
          start_date: yearStart.toISOString().split('T')[0],
          end_date: today.toISOString().split('T')[0],
        }
      default:
        return {
          start_date: yesterday.toISOString().split('T')[0],
          end_date: yesterday.toISOString().split('T')[0],
        }
    }
  }

  useEffect(() => {
    fetchDashboardData()
  }, [filter, activeTab])

  const fetchDashboardData = async () => {
    setLoading(true)
    const dateRange = getDateRange()
    const params = new URLSearchParams(dateRange)

    try {
      // Fetch stats
      const statsRes = await fetch(`${API_BASE_URL}/api/dashboard/stats?${params}`, {
        headers: {
          'Content-Type': 'application/json',
        },
      })
      
      if (!statsRes.ok) {
        throw new Error(`HTTP error! status: ${statsRes.status}`)
      }
      
      const statsData = await statsRes.json()

      // Calculate tax from bills (simplified - you may need to adjust based on your tax calculation)
      const taxRes = await fetch(`${API_BASE_URL}/api/bills?start_date=${dateRange.start_date}&end_date=${dateRange.end_date}`, {
        headers: {
          'Content-Type': 'application/json',
        },
      })
      
      if (!taxRes.ok) {
        throw new Error(`HTTP error! status: ${taxRes.status}`)
      }
      
      const billsData = await taxRes.json()
      const totalTax = billsData.bills?.reduce((sum, bill) => sum + (bill.tax_amount || 0), 0) || 0
      const deletedBills = billsData.bills?.filter(b => b.is_deleted) || []
      const deletedBillsCount = deletedBills.length
      const deletedBillsAmount = deletedBills.reduce((sum, b) => sum + (b.final_amount || 0), 0)

      setStats({
        totalTax: totalTax,
        grossRevenue: statsData.revenue?.total || 0,
        avgBillValue: statsData.revenue?.average_per_transaction || 0,
        transactions: statsData.transactions?.total || 0,
        expenses: statsData.expenses?.total || 0,
        deletedBills: deletedBillsCount,
        deletedBillsAmount: deletedBillsAmount,
      })

      if (activeTab === 'sales') {
        // Fetch top customers
        const customersRes = await fetch(`${API_BASE_URL}/api/dashboard/top-customers?${params}&limit=10`, {
          headers: { 'Content-Type': 'application/json' },
        })
        if (customersRes.ok) {
          const customersData = await customersRes.json()
          setTopCustomers(customersData || [])
        }

        // Fetch top offerings
        const offeringsRes = await fetch(`${API_BASE_URL}/api/dashboard/top-offerings?${params}&limit=10`, {
          headers: { 'Content-Type': 'application/json' },
        })
        if (offeringsRes.ok) {
          const offeringsData = await offeringsRes.json()
          setTopOfferings(offeringsData || [])
        }

        // Fetch revenue breakdown
        const revenueRes = await fetch(`${API_BASE_URL}/api/dashboard/revenue-breakdown?${params}`, {
          headers: { 'Content-Type': 'application/json' },
        })
        if (revenueRes.ok) {
          const revenueData = await revenueRes.json()
          setRevenueBreakdown(revenueData.breakdown || {})
        }

        // Fetch payment distribution
        const paymentRes = await fetch(`${API_BASE_URL}/api/dashboard/payment-distribution?${params}`, {
          headers: { 'Content-Type': 'application/json' },
        })
        if (paymentRes.ok) {
          const paymentData = await paymentRes.json()
          setPaymentDistribution(paymentData.distribution || [])
        }

        // Fetch client funnel
        const funnelRes = await fetch(`${API_BASE_URL}/api/dashboard/client-funnel?${params}`, {
          headers: { 'Content-Type': 'application/json' },
        })
        if (funnelRes.ok) {
          const funnelData = await funnelRes.json()
          setClientFunnel({
            newClients: funnelData.customers?.new || 0,
            returningClients: funnelData.customers?.returning || 0,
            totalLeads: funnelData.leads?.total || 0,
            contacted: 0, // Need to fetch from leads API
            followups: 0, // Need to fetch from leads API
            completed: funnelData.leads?.converted || 0,
            lost: 0, // Need to fetch from leads API
          })
        }

        // Fetch alerts
        const alertsRes = await fetch(`${API_BASE_URL}/api/dashboard/alerts`, {
          headers: { 'Content-Type': 'application/json' },
        })
        if (alertsRes.ok) {
          const alertsData = await alertsRes.json()
          setAlerts(alertsData || [])
        }
      } else {
        // Fetch staff performance
        const staffRes = await fetch(`${API_BASE_URL}/api/dashboard/staff-performance?${params}`, {
          headers: { 'Content-Type': 'application/json' },
        })
        if (staffRes.ok) {
          const staffData = await staffRes.json()
          setStaffPerformance(staffData || [])
        }
      }
    } catch (error) {
      console.error('Error fetching dashboard data:', error)
      console.error('Error details:', {
        name: error.name,
        message: error.message,
        stack: error.stack
      })
      
      if (error.message && error.message.includes('Failed to fetch')) {
        console.error(`Cannot connect to backend server at ${API_BASE_URL}. Please ensure the server is running.`)
        // Set default values to prevent UI from breaking
        setStats({
          totalTax: 0,
          grossRevenue: 0,
          avgBillValue: 0,
          transactions: 0,
          expenses: 0,
          deletedBills: 0,
          deletedBillsAmount: 0,
        })
        setStaffPerformance([])
        setTopCustomers([])
        setTopOfferings([])
        setRevenueBreakdown({
          service: 0,
          product: 0,
          package: 0,
          prepaid: 0,
          membership: 0,
        })
        setPaymentDistribution([])
        setClientFunnel({
          newClients: 0,
          returningClients: 0,
          totalLeads: 0,
          contacted: 0,
          followups: 0,
          completed: 0,
          lost: 0,
        })
        setAlerts([{
          type: 'server_error',
          severity: 'error',
          message: `Cannot connect to backend server. Please ensure the server is running at ${API_BASE_URL}`,
        }])
      } else if (error.message && error.message.includes('Unexpected token')) {
        console.error('Server returned HTML instead of JSON. Make sure the backend server is running and routes are correct.')
      }
    } finally {
      setLoading(false)
    }
  }

  const formatCurrency = (amount) => {
    return `₹ ${amount.toLocaleString('en-IN', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`
  }

  const displayStats = [
    { label: 'Total Tax Collected', value: formatCurrency(stats.totalTax), color: 'blue' },
    { label: 'Gross Revenue', value: formatCurrency(stats.grossRevenue), color: 'green' },
    { label: 'Avg. Bill Value', value: formatCurrency(stats.avgBillValue), color: 'yellow' },
    { label: 'Transactions', value: stats.transactions.toString(), color: 'gray' },
    { label: 'Expenses', value: formatCurrency(stats.expenses), color: 'red' },
    { label: 'Deleted Bills', value: `${stats.deletedBills} (${formatCurrency(stats.deletedBillsAmount)})`, color: 'dark-red' },
  ]

  return (
    <div className="dashboard">
      {/* Top Header */}
      <header className="dashboard-header">
        <div className="header-left">
          <button className="menu-icon"><FaBars /></button>
          <h1 className="header-title">Dashboard</h1>
        </div>
        <div className="header-right">
          <div className="logo-box">
            <span className="logo-text">HAIR STUDIO</span>
          </div>
          <button className="header-icon bell-icon"><FaBell /></button>
          <button className="header-icon user-icon"><FaUser /></button>
        </div>
      </header>

      {/* Tabs and Filter */}
      <div className="tabs-filter-section">
        <div className="tabs">
          <button
            className={`tab ${activeTab === 'sales' ? 'active' : ''}`}
            onClick={() => setActiveTab('sales')}
          >
            Sales
          </button>
          <button
            className={`tab ${activeTab === 'staff' ? 'active' : ''}`}
            onClick={() => setActiveTab('staff')}
          >
            Staff
          </button>
        </div>
        <div className="filter-section">
          <label className="filter-label">Filter:</label>
          <select
            className="filter-dropdown"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
          >
            <option value="today">Today</option>
            <option value="yesterday">Yesterday</option>
            <option value="week">This Week</option>
            <option value="month">This Month</option>
            <option value="year">This Year</option>
          </select>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="dashboard-content">
        {activeTab === 'staff' ? (
          <div className="staff-dashboard">
            {/* Staff Performance Panel */}
            <div className="staff-panel">
              <div className="panel-header">Staff Performance</div>
              <div className="panel-content empty-content"></div>
            </div>

            {/* Top Performer Panel */}
            <div className="staff-panel">
              <div className="panel-header">Top Performer</div>
              <div className="panel-content">
                <p className="no-data-message">No data found</p>
              </div>
            </div>

            {/* Employee Performance Table */}
            <div className="staff-panel full-width">
              <div className="panel-header">Employee Performance</div>
              <div className="panel-content">
                <div className="table-container">
                  <table className="employee-table">
                    <thead>
                      <tr>
                        <th>#</th>
                        <th>Staff Name</th>
                        <th>Item Count</th>
                        <th>Service</th>
                        <th>Package</th>
                        <th>Product</th>
                        <th>Prepaid</th>
                        <th>Membership</th>
                        <th>Total</th>
                        <th>Avg. Bill (₹)</th>
                        <th>Info</th>
                      </tr>
                    </thead>
                    <tbody>
                      {loading ? (
                        <tr>
                          <td colSpan="11" className="empty-row">Loading...</td>
                        </tr>
                      ) : staffPerformance.length === 0 ? (
                        <tr>
                          <td colSpan="11" className="empty-row">No data available</td>
                        </tr>
                      ) : (
                        staffPerformance.map((staff, index) => (
                          <tr key={staff.staff_id}>
                            <td>{index + 1}</td>
                            <td>{staff.staff_name}</td>
                            <td>{staff.total_services}</td>
                            <td>-</td>
                            <td>-</td>
                            <td>-</td>
                            <td>-</td>
                            <td>-</td>
                            <td>{formatCurrency(staff.total_revenue)}</td>
                            <td>{formatCurrency(staff.total_revenue / (staff.total_services || 1))}</td>
                            <td>
                              <button className="info-btn">Info</button>
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <>
            <div className="dashboard-main">
            {/* Statistics Cards */}
            <div className="stats-grid">
              {displayStats.map((stat, index) => (
                <div key={index} className={`stat-card stat-${stat.color}`}>
                  <div className="stat-label">{stat.label}</div>
                  <div className="stat-value">{loading ? 'Loading...' : stat.value}</div>
                </div>
              ))}
            </div>

          {/* Staff Leaderboard Table */}
          <div className="table-section">
            <h2 className="section-title">Staff Leaderboard</h2>
            <div className="table-container">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Staff Name</th>
                    <th>Item Count</th>
                    <th>Service</th>
                    <th>Package</th>
                    <th>Product</th>
                    <th>Prepaid</th>
                    <th>Membership</th>
                    <th>Total</th>
                  </tr>
                </thead>
                <tbody>
                  {loading ? (
                    <tr>
                      <td colSpan="8" className="empty-row">Loading...</td>
                    </tr>
                  ) : staffPerformance.length === 0 ? (
                    <tr>
                      <td colSpan="8" className="empty-row">No data available</td>
                    </tr>
                  ) : (
                    staffPerformance.map((staff, index) => (
                      <tr key={staff.staff_id}>
                        <td>{staff.staff_name}</td>
                        <td>{staff.total_services}</td>
                        <td>-</td>
                        <td>-</td>
                        <td>-</td>
                        <td>-</td>
                        <td>-</td>
                        <td>{formatCurrency(staff.total_revenue)}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Top 10 Customer */}
          <div className="table-section">
            <div className="section-header">
              <h2 className="section-title">Top 10 Customer</h2>
              <button 
                className="export-link" 
                onClick={(e) => {
                  e.preventDefault()
                  // TODO: Implement export functionality
                }}
                style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'inherit', textDecoration: 'underline' }}
              >
                Export Full Report
              </button>
            </div>
            <div className="table-container">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>#</th>
                    <th>Mobile</th>
                    <th>Customer</th>
                    <th>Count</th>
                    <th>Revenue</th>
                    <th>View Details</th>
                  </tr>
                </thead>
                <tbody>
                  {loading ? (
                    <tr>
                      <td colSpan="6" className="empty-row">Loading...</td>
                    </tr>
                  ) : topCustomers.length === 0 ? (
                    <tr>
                      <td colSpan="6" className="empty-row">No data available</td>
                    </tr>
                  ) : (
                    topCustomers.map((customer, index) => (
                      <tr key={customer.customer_id}>
                        <td>{index + 1}</td>
                        <td>{customer.mobile}</td>
                        <td>{customer.customer_name}</td>
                        <td>{customer.visit_count}</td>
                        <td>{formatCurrency(customer.total_spent)}</td>
                        <td>
                          <button className="view-link">View</button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Top 10 Offering Group */}
          <div className="table-section">
            <div className="section-header">
              <h2 className="section-title">Top 10 Offering Group</h2>
              <button 
                className="export-link" 
                onClick={(e) => {
                  e.preventDefault()
                  // TODO: Implement export functionality
                }}
                style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'inherit', textDecoration: 'underline' }}
              >
                Export Full Report
              </button>
            </div>
            <div className="table-container">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>#</th>
                    <th>Offering Group</th>
                    <th>Count</th>
                    <th>Revenue</th>
                    <th>View Details</th>
                  </tr>
                </thead>
                <tbody>
                  {loading ? (
                    <tr>
                      <td colSpan="5" className="empty-row">Loading...</td>
                    </tr>
                  ) : topOfferings.length === 0 ? (
                    <tr>
                      <td colSpan="5" className="empty-row">No data available</td>
                    </tr>
                  ) : (
                    topOfferings.slice(0, 10).map((offering, index) => (
                      <tr key={index}>
                        <td>{index + 1}</td>
                        <td>{offering.name}</td>
                        <td>{offering.quantity}</td>
                        <td>{formatCurrency(offering.revenue)}</td>
                        <td>
                          <button className="view-link">View</button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Top 10 Offerings */}
          <div className="table-section">
            <div className="section-header">
              <h2 className="section-title">Top 10 Offerings</h2>
              <button 
                className="export-link" 
                onClick={(e) => {
                  e.preventDefault()
                  // TODO: Implement export functionality
                }}
                style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'inherit', textDecoration: 'underline' }}
              >
                Export Full Report
              </button>
            </div>
            <div className="table-container">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>#</th>
                    <th>Offering</th>
                    <th>Count</th>
                    <th>Revenue</th>
                    <th>View Clients</th>
                  </tr>
                </thead>
                <tbody>
                  {loading ? (
                    <tr>
                      <td colSpan="5" className="empty-row">Loading...</td>
                    </tr>
                  ) : topOfferings.length === 0 ? (
                    <tr>
                      <td colSpan="5" className="empty-row">No data available</td>
                    </tr>
                  ) : (
                    topOfferings.slice(0, 10).map((offering, index) => (
                      <tr key={index}>
                        <td>{index + 1}</td>
                        <td>{offering.name}</td>
                        <td>{offering.quantity}</td>
                        <td>{formatCurrency(offering.revenue)}</td>
                        <td>
                          <button className="view-link">View</button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
            </div>
            </div>

            {/* Right Sidebar */}
            <aside className="dashboard-sidebar">
              {/* Revenue & Payments */}
              <div className="sidebar-card">
                <h3 className="sidebar-title">Revenue & Payments</h3>

                <div className="revenue-section">
                  <h4 className="subsection-title">REVENUE SOURCES:</h4>
                  <ul className="revenue-list">
                    <li className="revenue-item">
                      <span>Service Revenue:</span>
                      <span className="amount">{loading ? 'Loading...' : formatCurrency(revenueBreakdown.service?.amount || 0)}</span>
                    </li>
                    <li className="revenue-item">
                      <span>Retail Product Sales:</span>
                      <span className="amount">{loading ? 'Loading...' : formatCurrency(revenueBreakdown.product?.amount || 0)}</span>
                    </li>
                    <li className="revenue-item">
                      <span>Package Sales:</span>
                      <span className="amount">{loading ? 'Loading...' : formatCurrency(revenueBreakdown.package?.amount || 0)}</span>
                    </li>
                    <li className="revenue-item">
                      <span>Membership Sales:</span>
                      <span className="amount">{loading ? 'Loading...' : formatCurrency(revenueBreakdown.membership?.amount || 0)}</span>
                    </li>
                    <li className="revenue-item">
                      <span>Prepaid Packages Sold:</span>
                      <span className="amount">{loading ? 'Loading...' : formatCurrency(revenueBreakdown.prepaid?.amount || 0)}</span>
                    </li>
                  </ul>
                </div>

                <div className="payment-section">
                  <h4 className="subsection-title">PAYMENT DISTRIBUTION:</h4>
                  <ul className="payment-list">
                    {loading ? (
                      <li className="payment-item">Loading...</li>
                    ) : paymentDistribution.length === 0 ? (
                      <li className="payment-item">No payment data</li>
                    ) : (
                      paymentDistribution.map((payment, index) => (
                        <li key={index} className="payment-item">
                          <span>{payment.payment_mode}:</span>
                          <span className="amount">{formatCurrency(payment.amount)}</span>
                        </li>
                      ))
                    )}
                  </ul>
                </div>
              </div>

              {/* Client Source */}
              <div className="sidebar-card">
                <h3 className="sidebar-title">Client Source</h3>
                <div className="client-source-content">
                  <p className="empty-message">No data available</p>
                </div>
              </div>

              {/* Client & Lead Funnel */}
              <div className="sidebar-card">
                <h3 className="sidebar-title">Client & Lead Funnel</h3>
                <div className="client-metrics">
                  <div className="metric-card">
                    <div className="metric-value">{loading ? '...' : clientFunnel.newClients}</div>
                    <div className="metric-label">New Clients</div>
                  </div>
                  <div className="metric-card">
                    <div className="metric-value">{loading ? '...' : clientFunnel.returningClients}</div>
                    <div className="metric-label">Returning Clients</div>
                  </div>
                </div>
                <div className="divider"></div>
                <div className="lead-funnel-section">
                  <h4 className="subsection-title">TODAY'S LEAD FUNNEL</h4>
                  <ul className="funnel-list">
                    <li className="funnel-item">
                      <span>Total Leads Generated</span>
                      <span className="funnel-value">{loading ? '...' : clientFunnel.totalLeads}</span>
                    </li>
                    <li className="funnel-item">
                      <span>Contacted</span>
                      <span className="funnel-value">{loading ? '...' : clientFunnel.contacted}</span>
                    </li>
                    <li className="funnel-item">
                      <span>Follow-ups Scheduled</span>
                      <span className="funnel-value">{loading ? '...' : clientFunnel.followups}</span>
                    </li>
                    <li className="funnel-item">
                      <span>Completed</span>
                      <span className="funnel-value completed">{loading ? '...' : clientFunnel.completed}</span>
                    </li>
                    <li className="funnel-item">
                      <span>Lost</span>
                      <span className="funnel-value lost">{loading ? '...' : clientFunnel.lost}</span>
                    </li>
                  </ul>
                </div>
              </div>

              {/* Operational Alerts */}
              <div className="sidebar-card">
                <h3 className="sidebar-title">Operational Alerts</h3>
                <ul className="alerts-list">
                  {loading ? (
                    <li className="alert-item">Loading alerts...</li>
                  ) : alerts.length === 0 ? (
                    <li className="alert-item">No alerts</li>
                  ) : (
                    alerts.map((alert, index) => (
                      <li key={index} className="alert-item">
                        <span>{alert.message}</span>
                        <span className={`alert-value ${alert.severity}`}>
                          {alert.count}
                        </span>
                      </li>
                    ))
                  )}
                </ul>
              </div>
            </aside>
          </>
        )}
      </div>
    </div>
  )
}

export default Dashboard

