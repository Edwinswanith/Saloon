import React, { useState, useEffect } from 'react'
import Header from './Header'
import './Dashboard.css'
import { API_BASE_URL } from '../config'
import { useAuth } from '../contexts/AuthContext'
import { apiGet } from '../utils/api'
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import { PageTransition, StaggerContainer, StaggerItem, HoverScale } from './shared/PageTransition'
import { StatSkeleton, ChartSkeleton, TableSkeleton } from './shared/SkeletonLoaders'
import { EmptyTable } from './shared/EmptyStates'

const Dashboard = () => {
  const { currentBranch } = useAuth()
  const [activeTab, setActiveTab] = useState('staff')
  const [filter, setFilter] = useState('month')
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
  const [topPerformer, setTopPerformer] = useState(null)
  const [staffLeaderboard, setStaffLeaderboard] = useState([])
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
  }, [filter, activeTab, currentBranch])

  // Listen for branch changes
  useEffect(() => {
    const handleBranchChange = () => {
      fetchDashboardData()
    }
    
    window.addEventListener('branchChanged', handleBranchChange)
    return () => window.removeEventListener('branchChanged', handleBranchChange)
  }, [])

  const fetchDashboardData = async () => {
    setLoading(true)
    const dateRange = getDateRange()
    const params = new URLSearchParams(dateRange)

    try {
      // Fetch stats
      const statsRes = await apiGet(`/api/dashboard/stats?${params}`)
      
      if (!statsRes.ok) {
        throw new Error(`HTTP error! status: ${statsRes.status}`)
      }
      
      const statsData = await statsRes.json()

      // Calculate tax from bills (simplified - you may need to adjust based on your tax calculation)
      const taxRes = await apiGet(`/api/bills?start_date=${dateRange.start_date}&end_date=${dateRange.end_date}`)
      
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
        const customersRes = await apiGet(`/api/dashboard/top-customers?${params}&limit=10`)
        if (customersRes.ok) {
          const customersData = await customersRes.json()
          setTopCustomers(customersData || [])
        }

        // Fetch top offerings
        const offeringsRes = await apiGet(`/api/dashboard/top-offerings?${params}&limit=10`)
        if (offeringsRes.ok) {
          const offeringsData = await offeringsRes.json()
          setTopOfferings(offeringsData || [])
        }

        // Fetch revenue breakdown
        const revenueRes = await apiGet(`/api/dashboard/revenue-breakdown?${params}`)
        if (revenueRes.ok) {
          const revenueData = await revenueRes.json()
          setRevenueBreakdown(revenueData.breakdown || {})
        }

        // Fetch payment distribution
        const paymentRes = await apiGet(`/api/dashboard/payment-distribution?${params}`)
        if (paymentRes.ok) {
          const paymentData = await paymentRes.json()
          setPaymentDistribution(paymentData.distribution || [])
        }

        // Fetch client funnel
        const funnelRes = await apiGet(`/api/dashboard/client-funnel?${params}`)
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
        const alertsRes = await apiGet('/api/dashboard/alerts')
        if (alertsRes.ok) {
          const alertsData = await alertsRes.json()
          setAlerts(alertsData || [])
        }
      } else {
        // Fetch staff performance
        const staffRes = await apiGet(`/api/dashboard/staff-performance?${params}`)
        if (staffRes.ok) {
          const staffData = await staffRes.json()
          setStaffPerformance(staffData || [])
        }
        
        // Fetch top performer
        const topPerformerRes = await apiGet(`/api/dashboard/top-performer?${params}`)
        if (topPerformerRes.ok) {
          const performerData = await topPerformerRes.json()
          setTopPerformer(performerData.top_performer)
          setStaffLeaderboard(performerData.leaderboard || [])
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
        setTopPerformer(null)
        setStaffLeaderboard([])
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

  // Professional color scheme
  const COLORS = {
    primary: '#4F46E5',    // Indigo
    success: '#10B981',    // Green
    warning: '#F59E0B',    // Amber
    danger: '#EF4444',     // Red
    info: '#3B82F6',       // Blue
    purple: '#8B5CF6',     // Purple
    pink: '#EC4899',       // Pink
    teal: '#14B8A6',       // Teal
  }

  // Prepare chart data
  const revenueChartData = [
    { name: 'Service', value: revenueBreakdown.service, color: COLORS.primary },
    { name: 'Product', value: revenueBreakdown.product, color: COLORS.success },
    { name: 'Package', value: revenueBreakdown.package, color: COLORS.warning },
    { name: 'Prepaid', value: revenueBreakdown.prepaid, color: COLORS.info },
    { name: 'Membership', value: revenueBreakdown.membership, color: COLORS.purple },
  ].filter(item => item.value > 0)

  const staffChartData = staffPerformance.slice(0, 10).map(staff => ({
    name: staff.staff_name.length > 15 ? staff.staff_name.substring(0, 15) + '...' : staff.staff_name,
    revenue: staff.total_revenue,
    services: staff.total_services,
  }))

  const paymentChartData = paymentDistribution.map(payment => ({
    name: payment.method,
    value: payment.amount,
    color: payment.method === 'Cash' ? COLORS.success :
           payment.method === 'Card' ? COLORS.primary :
           payment.method === 'UPI' ? COLORS.info :
           COLORS.teal,
  })).filter(item => item.value > 0)

  const funnelChartData = [
    { name: 'Leads', value: clientFunnel.totalLeads, color: COLORS.info },
    { name: 'Contacted', value: clientFunnel.contacted, color: COLORS.primary },
    { name: 'Completed', value: clientFunnel.completed, color: COLORS.success },
    { name: 'Lost', value: clientFunnel.lost, color: COLORS.danger },
  ].filter(item => item.value > 0)

  // Custom tooltip for currency formatting
  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      return (
        <div style={{
          backgroundColor: 'white',
          padding: '10px',
          border: '1px solid #ccc',
          borderRadius: '4px',
        }}>
          <p style={{ margin: 0, fontWeight: 'bold' }}>{payload[0].name}</p>
          <p style={{ margin: 0, color: payload[0].color }}>
            {formatCurrency(payload[0].value)}
          </p>
        </div>
      )
    }
    return null
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
    <PageTransition>
      <div className="dashboard">
        {/* Top Header */}
        <Header title="Dashboard" />

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
              <div className="panel-header">Staff Performance (Branch)</div>
              <div className="panel-content">
                {loading ? (
                  <p className="no-data-message">Loading...</p>
                ) : staffPerformance.length === 0 ? (
                  <p className="no-data-message">No staff performance data available</p>
                ) : (
                  <div className="performance-grid">
                    {staffPerformance.slice(0, 5).map((staff, index) => (
                      <div key={staff.staff_id} className="performance-item">
                        <div className="performance-rank">#{index + 1}</div>
                        <div className="performance-details">
                          <h4>{staff.staff_name}</h4>
                          <div className="performance-metrics">
                            <span className="metric">
                              <span className="metric-label">Revenue:</span>
                              <span className="metric-value">{formatCurrency(staff.total_revenue)}</span>
                            </span>
                            <span className="metric">
                              <span className="metric-label">Services:</span>
                              <span className="metric-value">{staff.total_services}</span>
                            </span>
                            <span className="metric">
                              <span className="metric-label">Appointments:</span>
                              <span className="metric-value">{staff.completed_appointments}</span>
                            </span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Top Performer Panel */}
            <div className="staff-panel">
              <div className="panel-header">Top Performer (Company-Wide)</div>
              <div className="panel-content">
                {loading ? (
                  <p className="no-data-message">Loading...</p>
                ) : topPerformer ? (
                  <div className="top-performer-card">
                    <div className="performer-avatar">
                      {topPerformer.staff_name.charAt(0)}
                    </div>
                    <h3 className="performer-name">{topPerformer.staff_name}</h3>
                    <div className="performance-score">
                      <span className="score-value">{topPerformer.performance_score}</span>
                      <span className="score-label">/100</span>
                    </div>
                    <div className="performer-stats">
                      <div className="stat-item">
                        <span className="stat-label">Revenue</span>
                        <span className="stat-value">{formatCurrency(topPerformer.revenue)}</span>
                      </div>
                      <div className="stat-item">
                        <span className="stat-label">Services</span>
                        <span className="stat-value">{topPerformer.service_count}</span>
                      </div>
                      <div className="stat-item">
                        <span className="stat-label">Rating</span>
                        <span className="stat-value">{topPerformer.avg_rating}/5 ⭐</span>
                      </div>
                      <div className="stat-item">
                        <span className="stat-label">Appointments</span>
                        <span className="stat-value">{topPerformer.completed_appointments}</span>
                      </div>
                    </div>
                  </div>
                ) : (
                  <p className="no-data-message">No data available</p>
                )}
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
            {loading ? (
              <StatSkeleton count={6} />
            ) : (
              <StaggerContainer className="stats-grid">
                {displayStats.map((stat, index) => (
                  <StaggerItem key={index}>
                    <HoverScale>
                      <div className={`stat-card stat-${stat.color}`}>
                        <div className="stat-label">{stat.label}</div>
                        <div className="stat-value">{stat.value}</div>
                      </div>
                    </HoverScale>
                  </StaggerItem>
                ))}
              </StaggerContainer>
            )}

          {/* Professional Charts Section */}
          <div className="charts-grid" style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))',
            gap: '20px',
            margin: '20px 0',
          }}>
            {/* Revenue Breakdown Pie Chart */}
            <div className="chart-card" style={{
              backgroundColor: 'white',
              padding: '20px',
              borderRadius: '8px',
              boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
            }}>
              <h3 style={{ marginTop: 0, marginBottom: '15px', fontSize: '16px', fontWeight: '600' }}>
                Revenue Breakdown
              </h3>
              {loading ? (
                <ChartSkeleton height={300} />
              ) : revenueChartData.length === 0 ? (
                <EmptyTable title="No Revenue Data" message="Revenue data will appear here once you have transactions." />
              ) : (
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={revenueChartData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {revenueChartData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip content={<CustomTooltip />} />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              )}
            </div>

            {/* Staff Performance Bar Chart */}
            <div className="chart-card" style={{
              backgroundColor: 'white',
              padding: '20px',
              borderRadius: '8px',
              boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
            }}>
              <h3 style={{ marginTop: 0, marginBottom: '15px', fontSize: '16px', fontWeight: '600' }}>
                Staff Performance (Top 10)
              </h3>
              {loading ? (
                <ChartSkeleton height={300} />
              ) : staffChartData.length === 0 ? (
                <EmptyTable title="No Staff Data" message="Staff performance data will appear here once staff complete services." />
              ) : (
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={staffChartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} />
                    <YAxis />
                    <Tooltip content={<CustomTooltip />} />
                    <Legend />
                    <Bar dataKey="revenue" fill={COLORS.primary} name="Revenue (₹)" />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>

            {/* Payment Distribution Pie Chart */}
            <div className="chart-card" style={{
              backgroundColor: 'white',
              padding: '20px',
              borderRadius: '8px',
              boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
            }}>
              <h3 style={{ marginTop: 0, marginBottom: '15px', fontSize: '16px', fontWeight: '600' }}>
                Payment Distribution
              </h3>
              {loading ? (
                <div style={{ height: '300px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  Loading...
                </div>
              ) : paymentChartData.length === 0 ? (
                <div style={{ height: '300px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  No payment data available
                </div>
              ) : (
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={paymentChartData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {paymentChartData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip content={<CustomTooltip />} />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              )}
            </div>

            {/* Client Funnel Bar Chart */}
            <div className="chart-card" style={{
              backgroundColor: 'white',
              padding: '20px',
              borderRadius: '8px',
              boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
            }}>
              <h3 style={{ marginTop: 0, marginBottom: '15px', fontSize: '16px', fontWeight: '600' }}>
                Client Funnel
              </h3>
              {loading ? (
                <div style={{ height: '300px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  Loading...
                </div>
              ) : funnelChartData.length === 0 ? (
                <div style={{ height: '300px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  No funnel data available
                </div>
              ) : (
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={funnelChartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="value" name="Count">
                      {funnelChartData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>

          {/* Staff Leaderboard Table */}
          <div className="table-section">
            <h2 className="section-title">Staff Leaderboard</h2>
            <div className="table-container">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Rank</th>
                    <th>Staff Name</th>
                    <th>Score</th>
                    <th>Revenue</th>
                    <th>Services</th>
                    <th>Avg Rating</th>
                    <th>Feedback</th>
                    <th>Appointments</th>
                  </tr>
                </thead>
                <tbody>
                  {loading ? (
                    <tr>
                      <td colSpan="8" className="empty-row">Loading...</td>
                    </tr>
                  ) : staffLeaderboard.length === 0 ? (
                    <tr>
                      <td colSpan="8" className="empty-row">No data available</td>
                    </tr>
                  ) : (
                    staffLeaderboard.map((staff, index) => (
                      <tr key={staff.staff_id}>
                        <td><strong>{index + 1}</strong></td>
                        <td>{staff.staff_name}</td>
                        <td><strong style={{color: '#667eea'}}>{staff.performance_score}</strong></td>
                        <td>{formatCurrency(staff.revenue)}</td>
                        <td>{staff.service_count}</td>
                        <td>{staff.avg_rating} ⭐</td>
                        <td>{staff.feedback_count}</td>
                        <td>{staff.completed_appointments}</td>
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
    </PageTransition>
  )
}

export default Dashboard

