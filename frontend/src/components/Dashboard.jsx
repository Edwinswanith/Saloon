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
import {
  FaCut,
  FaShoppingBag,
  FaBox,
  FaCrown,
  FaCreditCard,
  FaMobileAlt,
  FaMoneyBillWave,
  FaWallet,
  FaChartBar,
  FaBullseye,
  FaPhone,
  FaCalendar,
  FaCheckCircle,
  FaTimesCircle,
  FaCircle,
  FaInfoCircle,
  FaBell,
  FaStar
} from 'react-icons/fa'

const Dashboard = () => {
  const { currentBranch } = useAuth()
  const [activeTab, setActiveTab] = useState('staff')
  const [filter, setFilter] = useState('month')
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear())
  const [selectedMonth, setSelectedMonth] = useState(new Date().getMonth() + 1) // 1-12
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
    
    // Use selected year/month for month and year filters
    const monthStart = new Date(selectedYear, selectedMonth - 1, 1)
    const monthEnd = new Date(selectedYear, selectedMonth, 0) // Last day of selected month
    const yearStart = new Date(selectedYear, 0, 1)
    const yearEnd = new Date(selectedYear, 11, 31, 23, 59, 59) // Last day of selected year

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
        // If selected month/year is current month/year, use today as end date
        // Otherwise, use the last day of the selected month
        const isCurrentMonth = selectedYear === today.getFullYear() && selectedMonth === today.getMonth() + 1
        return {
          start_date: monthStart.toISOString().split('T')[0],
          end_date: isCurrentMonth ? today.toISOString().split('T')[0] : monthEnd.toISOString().split('T')[0],
        }
      case 'year':
        // If selected year is current year, use today as end date
        // Otherwise, use the last day of the selected year
        const isCurrentYear = selectedYear === today.getFullYear()
        return {
          start_date: yearStart.toISOString().split('T')[0],
          end_date: isCurrentYear ? today.toISOString().split('T')[0] : yearEnd.toISOString().split('T')[0],
        }
      default:
        return {
          start_date: yesterday.toISOString().split('T')[0],
          end_date: yesterday.toISOString().split('T')[0],
        }
    }
  }

  useEffect(() => {
    console.log('[Dashboard] Fetching data - filter:', filter, 'year:', selectedYear, 'month:', selectedMonth, 'activeTab:', activeTab, 'currentBranch:', currentBranch?.id || currentBranch)
    fetchDashboardData()
  }, [filter, selectedYear, selectedMonth, activeTab, currentBranch])

  // Listen for branch changes
  useEffect(() => {
    const handleBranchChange = () => {
      console.log('[Dashboard] Branch changed, refreshing data...', currentBranch)
      fetchDashboardData()
    }
    
    window.addEventListener('branchChanged', handleBranchChange)
    return () => window.removeEventListener('branchChanged', handleBranchChange)
  }, [currentBranch])

  const fetchDashboardData = async () => {
    setLoading(true)
    const dateRange = getDateRange()
    const params = new URLSearchParams(dateRange)
    
    // Add timestamp to prevent caching
    params.append('_t', Date.now())

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
        // Fetch staff performance (branch-specific)
        const staffRes = await apiGet(`/api/dashboard/staff-performance?${params}`)
        if (staffRes.ok) {
          const staffData = await staffRes.json()
          console.log('[Dashboard] Staff Performance Data (Branch):', staffData)
          setStaffPerformance(staffData || [])
        } else {
          console.error('[Dashboard] Failed to fetch staff performance:', staffRes.status)
          setStaffPerformance([])
        }
        
        // Fetch top performer (company-wide, not branch-specific)
        const topPerformerRes = await apiGet(`/api/dashboard/top-performer?${params}`)
        if (topPerformerRes.ok) {
          const performerData = await topPerformerRes.json()
          console.log('[Dashboard] Top Performer Data (Company-Wide):', performerData)
          setTopPerformer(performerData.top_performer)
          setStaffLeaderboard(performerData.leaderboard || [])
        } else {
          console.error('[Dashboard] Failed to fetch top performer:', topPerformerRes.status)
          setTopPerformer(null)
          setStaffLeaderboard([])
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
                        <span className="stat-value" style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                          {topPerformer.avg_rating}/5 <FaStar size={14} color="#fbbf24" />
                        </span>
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
              borderRadius: '12px',
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
              borderRadius: '12px',
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
              borderRadius: '12px',
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
              borderRadius: '12px',
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
                        <td><strong>{staff.performance_score}</strong></td>
                        <td>{formatCurrency(staff.revenue)}</td>
                        <td>{staff.service_count}</td>
                        <td style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                          {staff.avg_rating} <FaStar size={14} color="#fbbf24" />
                        </td>
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
              <div className="sidebar-card" style={{
                background: 'white',
                borderRadius: '12px',
                padding: '24px',
                boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
                marginBottom: '20px'
              }}>
                <h3 className="sidebar-title" style={{
                  fontSize: '18px',
                  fontWeight: '600',
                  marginBottom: '20px',
                  color: '#1f2937',
                  borderBottom: '2px solid #e5e7eb',
                  paddingBottom: '12px'
                }}>Revenue & Payments</h3>

                {/* Revenue Sources */}
                <div className="revenue-section" style={{ marginBottom: '24px' }}>
                  <h4 style={{
                    fontSize: '12px',
                    fontWeight: '600',
                    color: '#6b7280',
                    textTransform: 'uppercase',
                    letterSpacing: '0.5px',
                    marginBottom: '16px',
                    marginTop: 0
                  }}>Revenue Sources</h4>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    {[
                      { label: 'Service Revenue', value: revenueBreakdown.service?.amount || 0, icon: <FaCut size={20} />, color: '#3b82f6' },
                      { label: 'Retail Product Sales', value: revenueBreakdown.product?.amount || 0, icon: <FaShoppingBag size={20} />, color: '#10b981' },
                      { label: 'Package Sales', value: revenueBreakdown.package?.amount || 0, icon: <FaBox size={20} />, color: '#f59e0b' },
                      { label: 'Membership Sales', value: revenueBreakdown.membership?.amount || 0, icon: <FaCrown size={20} />, color: '#8b5cf6' },
                      { label: 'Prepaid Packages', value: revenueBreakdown.prepaid?.amount || 0, icon: <FaCreditCard size={20} />, color: '#ec4899' }
                    ].map((item, index) => (
                      <div key={index} style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        padding: '12px 16px',
                        background: item.value > 0 ? '#f9fafb' : '#ffffff',
                        borderRadius: '8px',
                        border: item.value > 0 ? `1px solid ${item.color}20` : '1px solid #e5e7eb',
                        transition: 'all 0.2s'
                      }}
                      onMouseEnter={(e) => {
                        if (item.value > 0) {
                          e.currentTarget.style.background = `${item.color}08`
                          e.currentTarget.style.transform = 'translateX(4px)'
                        }
                      }}
                      onMouseLeave={(e) => {
                        if (item.value > 0) {
                          e.currentTarget.style.background = '#f9fafb'
                          e.currentTarget.style.transform = 'translateX(0)'
                        }
                      }}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                          {item.icon}
                          <span style={{
                            fontSize: '14px',
                            color: item.value > 0 ? '#374151' : '#9ca3af',
                            fontWeight: '500'
                          }}>{item.label}</span>
                        </div>
                        <span style={{
                          fontSize: '15px',
                          fontWeight: '600',
                          color: item.value > 0 ? item.color : '#9ca3af'
                        }}>
                          {loading ? '...' : formatCurrency(item.value)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Payment Distribution */}
                <div className="payment-section">
                  <h4 style={{
                    fontSize: '12px',
                    fontWeight: '600',
                    color: '#6b7280',
                    textTransform: 'uppercase',
                    letterSpacing: '0.5px',
                    marginBottom: '16px',
                    marginTop: 0
                  }}>Payment Distribution</h4>
                  {loading ? (
                    <div style={{ padding: '20px', textAlign: 'center', color: '#9ca3af' }}>Loading...</div>
                  ) : paymentDistribution.length === 0 ? (
                    <div style={{ padding: '20px', textAlign: 'center', color: '#9ca3af' }}>No payment data</div>
                  ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                      {paymentDistribution.map((payment, index) => {
                        const paymentIcons = {
                          'upi': <FaMobileAlt size={20} />,
                          'card': <FaCreditCard size={20} />,
                          'cash': <FaMoneyBillWave size={20} />,
                          'wallet': <FaWallet size={20} />
                        }
                        const paymentColors = {
                          'upi': '#6366f1',
                          'card': '#3b82f6',
                          'cash': '#10b981',
                          'wallet': '#f59e0b'
                        }
                        const mode = payment.payment_mode?.toLowerCase() || 'cash'
                        const icon = paymentIcons[mode] || <FaCreditCard size={20} />
                        const color = paymentColors[mode] || '#3b82f6'
                        
                        return (
                          <div key={index} style={{
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'space-between',
                            padding: '14px 16px',
                            background: '#f9fafb',
                            borderRadius: '8px',
                            border: `1px solid ${color}20`,
                            transition: 'all 0.2s'
                          }}
                          onMouseEnter={(e) => {
                            e.currentTarget.style.background = `${color}08`
                            e.currentTarget.style.transform = 'translateX(4px)'
                          }}
                          onMouseLeave={(e) => {
                            e.currentTarget.style.background = '#f9fafb'
                            e.currentTarget.style.transform = 'translateX(0)'
                          }}
                          >
                            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                              {icon}
                              <span style={{
                                fontSize: '14px',
                                color: '#374151',
                                fontWeight: '600',
                                textTransform: 'capitalize'
                              }}>{payment.payment_mode}</span>
                            </div>
                            <span style={{
                              fontSize: '15px',
                              fontWeight: '700',
                              color: color
                            }}>
                              {formatCurrency(payment.amount)}
                            </span>
                          </div>
                        )
                      })}
                    </div>
                  )}
                </div>
              </div>

              {/* Client Source */}
              <div className="sidebar-card" style={{
                background: 'white',
                borderRadius: '12px',
                padding: '24px',
                boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
                marginBottom: '20px'
              }}>
                <h3 className="sidebar-title" style={{
                  fontSize: '18px',
                  fontWeight: '600',
                  marginBottom: '20px',
                  color: '#1f2937',
                  borderBottom: '2px solid #e5e7eb',
                  paddingBottom: '12px'
                }}>Client Source</h3>
                <div style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  padding: '40px 20px',
                  textAlign: 'center'
                }}>
                  <div style={{
                    width: '64px',
                    height: '64px',
                    borderRadius: '50%',
                    background: 'linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    marginBottom: '16px'
                  }}>
                    <FaChartBar size={32} color="#9ca3af" />
                  </div>
                  <p style={{
                    fontSize: '14px',
                    color: '#6b7280',
                    margin: 0,
                    fontWeight: '500'
                  }}>No data available</p>
                  <p style={{
                    fontSize: '12px',
                    color: '#9ca3af',
                    margin: '8px 0 0 0'
                  }}>Client source data will appear here</p>
                </div>
              </div>

              {/* Client & Lead Funnel */}
              <div className="sidebar-card" style={{
                background: 'white',
                borderRadius: '12px',
                padding: '24px',
                boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
                marginBottom: '20px'
              }}>
                <h3 className="sidebar-title" style={{
                  fontSize: '18px',
                  fontWeight: '600',
                  marginBottom: '20px',
                  color: '#1f2937',
                  borderBottom: '2px solid #e5e7eb',
                  paddingBottom: '12px'
                }}>Client & Lead Funnel</h3>
                
                {/* Client Metrics */}
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: '1fr 1fr',
                  gap: '12px',
                  marginBottom: '24px'
                }}>
                  <div style={{
                    padding: '16px',
                    background: 'linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%)',
                    borderRadius: '10px',
                    border: '1px solid #3b82f620',
                    textAlign: 'center',
                    transition: 'all 0.2s'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.transform = 'translateY(-2px)'
                    e.currentTarget.style.boxShadow = '0 4px 12px rgba(59, 130, 246, 0.15)'
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.transform = 'translateY(0)'
                    e.currentTarget.style.boxShadow = 'none'
                  }}
                  >
                    <div style={{
                      fontSize: '28px',
                      fontWeight: '700',
                      color: '#1e40af',
                      marginBottom: '4px'
                    }}>
                      {loading ? '...' : clientFunnel.newClients}
                    </div>
                    <div style={{
                      fontSize: '12px',
                      color: '#1e40af',
                      fontWeight: '600',
                      textTransform: 'uppercase',
                      letterSpacing: '0.5px'
                    }}>New Clients</div>
                  </div>
                  
                  <div style={{
                    padding: '16px',
                    background: 'linear-gradient(135deg, #dcfce7 0%, #bbf7d0 100%)',
                    borderRadius: '10px',
                    border: '1px solid #10b98120',
                    textAlign: 'center',
                    transition: 'all 0.2s'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.transform = 'translateY(-2px)'
                    e.currentTarget.style.boxShadow = '0 4px 12px rgba(16, 185, 129, 0.15)'
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.transform = 'translateY(0)'
                    e.currentTarget.style.boxShadow = 'none'
                  }}
                  >
                    <div style={{
                      fontSize: '28px',
                      fontWeight: '700',
                      color: '#047857',
                      marginBottom: '4px'
                    }}>
                      {loading ? '...' : clientFunnel.returningClients}
                    </div>
                    <div style={{
                      fontSize: '12px',
                      color: '#047857',
                      fontWeight: '600',
                      textTransform: 'uppercase',
                      letterSpacing: '0.5px'
                    }}>Returning Clients</div>
                  </div>
                </div>

                {/* Divider */}
                <div style={{
                  height: '1px',
                  background: 'linear-gradient(90deg, transparent, #e5e7eb, transparent)',
                  margin: '20px 0'
                }}></div>

                {/* Today's Lead Funnel */}
                <div>
                  <h4 style={{
                    fontSize: '12px',
                    fontWeight: '600',
                    color: '#6b7280',
                    textTransform: 'uppercase',
                    letterSpacing: '0.5px',
                    marginBottom: '16px',
                    marginTop: 0
                  }}>Today's Lead Funnel</h4>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                    {[
                      { label: 'Total Leads Generated', value: clientFunnel.totalLeads, icon: <FaBullseye size={18} />, color: '#3b82f6' },
                      { label: 'Contacted', value: clientFunnel.contacted, icon: <FaPhone size={18} />, color: '#6366f1' },
                      { label: 'Follow-ups Scheduled', value: clientFunnel.followups, icon: <FaCalendar size={18} />, color: '#8b5cf6' },
                      { label: 'Completed', value: clientFunnel.completed, icon: <FaCheckCircle size={18} />, color: '#10b981' },
                      { label: 'Lost', value: clientFunnel.lost, icon: <FaTimesCircle size={18} />, color: '#ef4444' }
                    ].map((item, index) => (
                      <div key={index} style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        padding: '12px 14px',
                        background: '#f9fafb',
                        borderRadius: '8px',
                        border: `1px solid ${item.color}20`,
                        transition: 'all 0.2s'
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.background = `${item.color}08`
                        e.currentTarget.style.transform = 'translateX(4px)'
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.background = '#f9fafb'
                        e.currentTarget.style.transform = 'translateX(0)'
                      }}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                          {item.icon}
                          <span style={{
                            fontSize: '13px',
                            color: '#374151',
                            fontWeight: '500'
                          }}>{item.label}</span>
                        </div>
                        <span style={{
                          fontSize: '15px',
                          fontWeight: '700',
                          color: item.color,
                          minWidth: '40px',
                          textAlign: 'right'
                        }}>
                          {loading ? '...' : item.value}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Operational Alerts */}
              <div className="sidebar-card" style={{
                background: 'white',
                borderRadius: '12px',
                padding: '24px',
                boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
                marginBottom: '20px'
              }}>
                <h3 className="sidebar-title" style={{
                  fontSize: '18px',
                  fontWeight: '600',
                  marginBottom: '20px',
                  color: '#1f2937',
                  borderBottom: '2px solid #e5e7eb',
                  paddingBottom: '12px'
                }}>Operational Alerts</h3>
                {loading ? (
                  <div style={{
                    padding: '20px',
                    textAlign: 'center',
                    color: '#9ca3af',
                    fontSize: '14px'
                  }}>Loading alerts...</div>
                ) : alerts.length === 0 ? (
                  <div style={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    padding: '30px 20px',
                    textAlign: 'center'
                  }}>
                    <div style={{
                      width: '56px',
                      height: '56px',
                      borderRadius: '50%',
                      background: 'linear-gradient(135deg, #fef3c7 0%, #fde68a 100%)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      marginBottom: '12px'
                    }}>
                      <FaBell size={28} color="#f59e0b" />
                    </div>
                    <p style={{
                      fontSize: '14px',
                      color: '#6b7280',
                      margin: 0,
                      fontWeight: '500'
                    }}>No alerts</p>
                    <p style={{
                      fontSize: '12px',
                      color: '#9ca3af',
                      margin: '6px 0 0 0'
                    }}>All systems operational</p>
                  </div>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                    {alerts.map((alert, index) => {
                      const severityColors = {
                        'high': { bg: '#fee2e2', border: '#ef4444', text: '#dc2626', icon: <FaCircle size={18} color="#dc2626" /> },
                        'medium': { bg: '#fef3c7', border: '#f59e0b', text: '#d97706', icon: <FaCircle size={18} color="#d97706" /> },
                        'low': { bg: '#dbeafe', border: '#3b82f6', text: '#2563eb', icon: <FaCircle size={18} color="#2563eb" /> },
                        'info': { bg: '#f3f4f6', border: '#6b7280', text: '#4b5563', icon: <FaInfoCircle size={18} color="#4b5563" /> }
                      }
                      const severity = alert.severity?.toLowerCase() || 'info'
                      const colors = severityColors[severity] || severityColors.info
                      
                      return (
                        <div key={index} style={{
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          padding: '14px 16px',
                          background: colors.bg,
                          borderRadius: '8px',
                          border: `1px solid ${colors.border}40`,
                          transition: 'all 0.2s'
                        }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.transform = 'translateX(4px)'
                          e.currentTarget.style.boxShadow = `0 2px 8px ${colors.border}20`
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.transform = 'translateX(0)'
                          e.currentTarget.style.boxShadow = 'none'
                        }}
                        >
                          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                            {colors.icon}
                            <span style={{
                              fontSize: '13px',
                              color: colors.text,
                              fontWeight: '500'
                            }}>{alert.message}</span>
                          </div>
                          <span style={{
                            fontSize: '16px',
                            fontWeight: '700',
                            color: colors.text,
                            background: 'white',
                            padding: '4px 10px',
                            borderRadius: '12px',
                            minWidth: '32px',
                            textAlign: 'center'
                          }}>
                            {alert.count}
                          </span>
                        </div>
                      )
                    })}
                  </div>
                )}
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

