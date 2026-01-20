import React, { useState, useEffect } from 'react'
import Header from './Header'
import './Dashboard.css'
import { API_BASE_URL } from '../config'
import { useAuth } from '../contexts/AuthContext'
import { apiGet } from '../utils/api'
import DashboardStatsCards from './DashboardStatsCards'
import SalesInsights from './SalesInsights'
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
  FaChartBar,
  FaBullseye,
  FaPhone,
  FaCalendar,
  FaCalendarCheck,
  FaCheckCircle,
  FaTimesCircle,
  FaCircle,
  FaInfoCircle,
  FaBell,
  FaStar,
  FaTrophy,
  FaMedal,
  FaDollarSign,
  FaCoins,
  FaHandSparkles,
  FaAward,
  FaClipboardList,
  FaUser,
  FaTimes,
  FaChartLine,
  FaArrowUp,
  FaArrowDown,
  FaMinus,
  FaExclamationCircle
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
  const [revenueBreakdown, setRevenueBreakdown] = useState({
    service: { amount: 0, percentage: 0 },
    product: { amount: 0, percentage: 0 },
    package: { amount: 0, percentage: 0 },
    prepaid: { amount: 0, percentage: 0 },
    membership: { amount: 0, percentage: 0 },
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
  const [showStaffModal, setShowStaffModal] = useState(false)
  const [selectedStaff, setSelectedStaff] = useState(null)
  const [clientSource, setClientSource] = useState([])
  const [showOfferingModal, setShowOfferingModal] = useState(false)
  const [selectedOffering, setSelectedOffering] = useState(null)
  const [offeringClients, setOfferingClients] = useState([])
  const [loadingOfferingClients, setLoadingOfferingClients] = useState(false)

  // Data cache with timestamp and params tracking
  const [dataCache, setDataCache] = useState({
    stats: null,
    sales: null,
    staff: null,
  })

  // Cache expiration time (5 minutes)
  const CACHE_EXPIRY_MS = 5 * 60 * 1000

  // Helper function to check if cache is valid
  const isCacheValid = (cacheEntry, currentParams) => {
    if (!cacheEntry) return false
    
    // Check if cache has expired
    const now = Date.now()
    if (now - cacheEntry.timestamp > CACHE_EXPIRY_MS) {
      return false
    }
    
    // Check if params match
    if (cacheEntry.params) {
      const cacheParams = cacheEntry.params
      const currentParamsStr = JSON.stringify(currentParams)
      const cacheParamsStr = JSON.stringify(cacheParams)
      if (currentParamsStr !== cacheParamsStr) {
        return false
      }
    }
    
    return true
  }

  // Helper function to get cache key params
  const getCacheParams = () => {
    return {
      filter,
      selectedYear,
      selectedMonth,
      branchId: currentBranch?.id || null,
    }
  }

  // Helper function to get local date string (YYYY-MM-DD) in IST/local timezone
  const getLocalDateString = (date) => {
    const year = date.getFullYear()
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const day = String(date.getDate()).padStart(2, '0')
    return `${year}-${month}-${day}`
  }

  // Get date range for current month (used for Top Performer - always shows current month)
  const getCurrentMonthDateRange = () => {
    const today = new Date()
    const currentMonthStart = new Date(today.getFullYear(), today.getMonth(), 1)
    return {
      start_date: getLocalDateString(currentMonthStart),
      end_date: getLocalDateString(today),
    }
  }

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
          start_date: getLocalDateString(today),
          end_date: getLocalDateString(today),
        }
      case 'yesterday':
        return {
          start_date: getLocalDateString(yesterday),
          end_date: getLocalDateString(yesterday),
        }
      case 'week':
        return {
          start_date: getLocalDateString(weekStart),
          end_date: getLocalDateString(today),
        }
      case 'month':
        // If selected month/year is current month/year, use today as end date
        // Otherwise, use the last day of the selected month
        const isCurrentMonth = selectedYear === today.getFullYear() && selectedMonth === today.getMonth() + 1
        return {
          start_date: getLocalDateString(monthStart),
          end_date: isCurrentMonth ? getLocalDateString(today) : getLocalDateString(monthEnd),
        }
      case 'year':
        // If selected year is current year, use today as end date
        // Otherwise, use the last day of the selected year
        const isCurrentYear = selectedYear === today.getFullYear()
        return {
          start_date: getLocalDateString(yearStart),
          end_date: isCurrentYear ? getLocalDateString(today) : getLocalDateString(yearEnd),
        }
      default:
        return {
          start_date: getLocalDateString(yesterday),
          end_date: getLocalDateString(yesterday),
        }
    }
  }

  // Fetch stats data (only needed for sales tab)
  const fetchStatsData = async (params, dateRange) => {
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

      const statsResult = {
        totalTax: totalTax,
        grossRevenue: statsData.revenue?.total || 0,
        avgBillValue: statsData.revenue?.average_per_transaction || 0,
        transactions: statsData.transactions?.total || 0,
        expenses: statsData.expenses?.total || 0,
        deletedBills: deletedBillsCount,
        deletedBillsAmount: deletedBillsAmount,
      }

      setStats(statsResult)
      
      // Cache the stats data
      setDataCache(prev => ({
        ...prev,
        stats: {
          data: statsResult,
          timestamp: Date.now(),
          params: getCacheParams(),
        }
      }))

      return statsResult
    } catch (error) {
      console.error('Error fetching stats data:', error)
      throw error
    }
  }

  // Fetch sales data (only when on sales tab)
  // NOTE: topMovingItems, topCustomers, topOfferings are now lazy-loaded via SalesInsights component
  const fetchSalesData = async (params) => {
    try {
      // Fetch only non-lazy-loaded sales data in parallel
      const [
        revenueBreakdownRes,
        paymentDistributionRes,
        clientFunnelRes,
        clientSourceRes,
        alertsRes
      ] = await Promise.allSettled([
        apiGet(`/api/dashboard/revenue-breakdown?${params}`),
        apiGet(`/api/dashboard/payment-distribution?${params}`),
        apiGet(`/api/dashboard/client-funnel?${params}`),
        apiGet(`/api/dashboard/client-source?${params}`),
        apiGet('/api/dashboard/alerts')
      ])

      // Process revenue breakdown
      let revenueBreakdownData = {}
      if (revenueBreakdownRes.status === 'fulfilled' && revenueBreakdownRes.value.ok) {
        const data = await revenueBreakdownRes.value.json()
        revenueBreakdownData = data.breakdown || {}
      }
      setRevenueBreakdown(revenueBreakdownData)

      // Process payment distribution
      let paymentDistributionData = []
      if (paymentDistributionRes.status === 'fulfilled' && paymentDistributionRes.value.ok) {
        const data = await paymentDistributionRes.value.json()
        paymentDistributionData = data.distribution || []
      }
      setPaymentDistribution(paymentDistributionData)

      // Process client funnel
      let clientFunnelData = {
        newClients: 0,
        returningClients: 0,
        totalLeads: 0,
        contacted: 0,
        followups: 0,
        completed: 0,
        lost: 0,
      }
      if (clientFunnelRes.status === 'fulfilled' && clientFunnelRes.value.ok) {
        const data = await clientFunnelRes.value.json()
        clientFunnelData = {
          newClients: data.customers?.new || 0,
          returningClients: data.customers?.returning || 0,
          totalLeads: data.leads?.total || 0,
          contacted: 0,
          followups: 0,
          completed: data.leads?.converted || 0,
          lost: 0,
        }
      }
      setClientFunnel(clientFunnelData)

      // Process client source
      let clientSourceData = []
      if (clientSourceRes.status === 'fulfilled' && clientSourceRes.value.ok) {
        const data = await clientSourceRes.value.json()
        clientSourceData = data.distribution || []
      }
      setClientSource(clientSourceData)

      // Process alerts
      let alertsData = []
      if (alertsRes.status === 'fulfilled' && alertsRes.value.ok) {
        const data = await alertsRes.value.json()
        alertsData = Array.isArray(data) ? data : []
      }
      setAlerts(alertsData)

      // Cache the sales data (excluding lazy-loaded data)
      setDataCache(prev => ({
        ...prev,
        sales: {
          data: {
            revenueBreakdown: revenueBreakdownData,
            paymentDistribution: paymentDistributionData,
            clientFunnel: clientFunnelData,
            clientSource: clientSourceData,
            alerts: alertsData,
          },
          timestamp: Date.now(),
          params: getCacheParams(),
        }
      }))
    } catch (error) {
      console.error('Error fetching sales data:', error)
      throw error
    }
  }

  // Fetch staff data (only when on staff tab)
  const fetchStaffData = async (params) => {
    try {
      // Fetch staff performance (branch-specific) - uses filtered date range
      let staffPerformanceData = []
      const staffRes = await apiGet(`/api/dashboard/staff-performance?${params}`)
      if (staffRes.ok) {
        staffPerformanceData = await staffRes.json() || []
        console.log('[Dashboard] Staff Performance Data (Branch):', staffPerformanceData)
      } else {
        console.error('[Dashboard] Failed to fetch staff performance:', staffRes.status)
      }
      setStaffPerformance(staffPerformanceData)
      
      // Fetch top performer (company-wide, not branch-specific) - always uses current month
      const currentMonthRange = getCurrentMonthDateRange()
      const topPerformerParams = new URLSearchParams(currentMonthRange)
      topPerformerParams.append('_t', Date.now())
      
      let topPerformerData = null
      let staffLeaderboardData = []
      const topPerformerRes = await apiGet(`/api/dashboard/top-performer?${topPerformerParams}`)
      if (topPerformerRes.ok) {
        const performerData = await topPerformerRes.json()
        console.log('[Dashboard] Top Performer Data (Company-Wide):', performerData)
        topPerformerData = performerData.top_performer
        staffLeaderboardData = performerData.leaderboard || []
      } else {
        console.error('[Dashboard] Failed to fetch top performer:', topPerformerRes.status)
      }
      setTopPerformer(topPerformerData)
      setStaffLeaderboard(staffLeaderboardData)

      // Cache the staff data
      setDataCache(prev => ({
        ...prev,
        staff: {
          data: {
            staffPerformance: staffPerformanceData,
            topPerformer: topPerformerData,
            staffLeaderboard: staffLeaderboardData,
          },
          timestamp: Date.now(),
          params: getCacheParams(),
        }
      }))
    } catch (error) {
      console.error('Error fetching staff data:', error)
      throw error
    }
  }

  // Load data from cache
  const loadFromCache = (cacheKey, cacheEntry) => {
    if (!cacheEntry || !cacheEntry.data) {
      return false
    }

    if (cacheKey === 'stats') {
      setStats(cacheEntry.data)
      return true
    } else if (cacheKey === 'sales') {
      const salesData = cacheEntry.data
      if (salesData.revenueBreakdown !== undefined) setRevenueBreakdown(salesData.revenueBreakdown)
      if (salesData.paymentDistribution !== undefined) setPaymentDistribution(salesData.paymentDistribution)
      if (salesData.clientFunnel !== undefined) setClientFunnel(salesData.clientFunnel)
      if (salesData.clientSource !== undefined) setClientSource(salesData.clientSource)
      if (salesData.alerts !== undefined) setAlerts(salesData.alerts)
      return true
    } else if (cacheKey === 'staff') {
      const staffData = cacheEntry.data
      if (staffData.staffPerformance !== undefined) setStaffPerformance(staffData.staffPerformance)
      if (staffData.topPerformer !== undefined) setTopPerformer(staffData.topPerformer)
      if (staffData.staffLeaderboard !== undefined) setStaffLeaderboard(staffData.staffLeaderboard)
      return true
    }
    return false
  }

  // Effect for sales tab data
  useEffect(() => {
    if (activeTab !== 'sales') return

    const loadSalesData = async () => {
      setLoading(true)
      const dateRange = getDateRange()
      const params = new URLSearchParams(dateRange)
      params.append('_t', Date.now())
      const cacheParams = getCacheParams()

      try {
        // Check cache first
        const cacheEntry = dataCache.sales
        if (isCacheValid(cacheEntry, cacheParams)) {
          console.log('[Dashboard] Using cached sales data')
          loadFromCache('sales', cacheEntry)
          // Also check for cached stats
          const statsCacheEntry = dataCache.stats
          if (isCacheValid(statsCacheEntry, cacheParams)) {
            loadFromCache('stats', statsCacheEntry)
          } else {
            await fetchStatsData(params, dateRange)
          }
          setLoading(false)
          return
        }

        console.log('[Dashboard] Fetching sales data - filter:', filter, 'year:', selectedYear, 'month:', selectedMonth, 'currentBranch:', currentBranch?.id || currentBranch)
        
        // Fetch stats and sales data
        await fetchStatsData(params, dateRange)
        await fetchSalesData(params)
      } catch (error) {
        console.error('Error loading sales data:', error)
        if (error.message && error.message.includes('Failed to fetch')) {
          console.error(`Cannot connect to backend server at ${API_BASE_URL}. Please ensure the server is running.`)
          setAlerts([{
            type: 'server_error',
            severity: 'error',
            message: `Cannot connect to backend server. Please ensure the server is running at ${API_BASE_URL}`,
          }])
        }
      } finally {
        setLoading(false)
      }
    }

    loadSalesData()
  }, [filter, selectedYear, selectedMonth, activeTab, currentBranch])

  // Effect for staff tab data
  useEffect(() => {
    if (activeTab !== 'staff') return

    const loadStaffData = async () => {
      setLoading(true)
      const dateRange = getDateRange()
      const params = new URLSearchParams(dateRange)
      params.append('_t', Date.now())
      const cacheParams = getCacheParams()

      try {
        // Check cache first
        const cacheEntry = dataCache.staff
        if (isCacheValid(cacheEntry, cacheParams)) {
          console.log('[Dashboard] Using cached staff data')
          loadFromCache('staff', cacheEntry)
          setLoading(false)
          return
        }

        console.log('[Dashboard] Fetching staff data - filter:', filter, 'year:', selectedYear, 'month:', selectedMonth, 'currentBranch:', currentBranch?.id || currentBranch)
        
        // Only fetch staff data (no stats/bills needed for staff tab)
        await fetchStaffData(params)
      } catch (error) {
        console.error('Error loading staff data:', error)
        if (error.message && error.message.includes('Failed to fetch')) {
          console.error(`Cannot connect to backend server at ${API_BASE_URL}. Please ensure the server is running.`)
        }
      } finally {
        setLoading(false)
      }
    }

    loadStaffData()
  }, [filter, selectedYear, selectedMonth, activeTab, currentBranch])

  // Listen for branch changes - invalidate cache and refetch
  useEffect(() => {
    const handleBranchChange = () => {
      console.log('[Dashboard] Branch changed, invalidating cache and refreshing data...', currentBranch)
      // Invalidate all cache
      setDataCache({
        stats: null,
        sales: null,
        staff: null,
      })
      // Trigger refetch by changing a dependency (activeTab will trigger the appropriate effect)
      // Force a refetch by toggling activeTab temporarily (but this might cause flicker)
      // Instead, we'll let the existing effects handle it since currentBranch is in their deps
    }
    
    window.addEventListener('branchChanged', handleBranchChange)
    return () => window.removeEventListener('branchChanged', handleBranchChange)
  }, [currentBranch])


  const handleViewOfferingClients = async (offering) => {
    setSelectedOffering(offering)
    setShowOfferingModal(true)
    setLoadingOfferingClients(true)
    setOfferingClients([])

    try {
      const dateRange = getDateRange()
      const params = new URLSearchParams({
        name: offering.name,
        type: offering.type,
        start_date: dateRange.start_date,
        end_date: dateRange.end_date
      })
      
      const response = await apiGet(`/api/dashboard/offering-clients?${params}`)
      if (response.ok) {
        const data = await response.json()
        setOfferingClients(data.clients || [])
      } else {
        console.error('Failed to fetch offering clients')
      }
    } catch (error) {
      console.error('Error fetching offering clients:', error)
    } finally {
      setLoadingOfferingClients(false)
    }
  }

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A'
    try {
      const date = new Date(dateString)
      return date.toLocaleDateString('en-IN', {
        day: '2-digit',
        month: 'short',
        year: 'numeric'
      })
    } catch (e) {
      return dateString
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
    { name: 'Service', value: revenueBreakdown.service?.amount || 0, color: COLORS.primary },
    { name: 'Product', value: revenueBreakdown.product?.amount || 0, color: COLORS.success },
    { name: 'Package', value: revenueBreakdown.package?.amount || 0, color: COLORS.warning },
    { name: 'Prepaid', value: revenueBreakdown.prepaid?.amount || 0, color: COLORS.info },
    { name: 'Membership', value: revenueBreakdown.membership?.amount || 0, color: COLORS.purple },
  ].filter(item => item.value > 0)

  const staffChartData = staffPerformance.slice(0, 10).map(staff => ({
    name: staff.staff_name.length > 15 ? staff.staff_name.substring(0, 15) + '...' : staff.staff_name,
    revenue: staff.total_revenue,
    services: staff.total_services,
    appointments: staff.completed_appointments || 0,
  }))

  // Prepare top performer bar chart data (normalized to 0-100 for visual consistency, but show actual values in tooltips)
  const topPerformerBarData = topPerformer ? (() => {
    // Find max values for normalization (use reasonable max values for better visualization)
    const maxRevenue = Math.max(...staffPerformance.map(s => s.total_revenue), topPerformer.revenue) || 1
    const maxServices = Math.max(...staffPerformance.map(s => s.total_services), topPerformer.service_count) || 1
    const maxAppointments = Math.max(...staffPerformance.map(s => s.completed_appointments || 0), topPerformer.completed_appointments) || 1
    
    return [
      { metric: 'Revenue', value: Math.min((topPerformer.revenue / maxRevenue) * 100, 100), formatted: formatCurrency(topPerformer.revenue), color: '#10b981' },
      { metric: 'Services', value: Math.min((topPerformer.service_count / maxServices) * 100, 100), formatted: topPerformer.service_count, color: '#3b82f6' },
      { metric: 'Rating', value: (topPerformer.avg_rating / 5) * 100, formatted: `${topPerformer.avg_rating}/5`, color: '#d97706' },
      { metric: 'Appointments', value: Math.min((topPerformer.completed_appointments / maxAppointments) * 100, 100), formatted: topPerformer.completed_appointments, color: '#8b5cf6' },
      { metric: 'Score', value: topPerformer.performance_score, formatted: `${topPerformer.performance_score}/100`, color: '#6366f1' },
    ]
  })() : []

  const paymentChartData = paymentDistribution.map(payment => {
    const mode = (payment.payment_mode || 'cash').toLowerCase()
    return {
      name: payment.payment_mode || 'Cash',
      value: payment.amount,
      color: mode === 'cash' ? COLORS.success :
             mode === 'card' ? COLORS.primary :
             mode === 'upi' ? COLORS.info :
             COLORS.teal,
    }
  }).filter(item => item.value > 0)

  const funnelChartData = [
    { name: 'Leads', value: clientFunnel.totalLeads, color: COLORS.info },
    { name: 'Contacted', value: clientFunnel.contacted, color: COLORS.primary },
    { name: 'Completed', value: clientFunnel.completed, color: COLORS.success },
    { name: 'Lost', value: clientFunnel.lost, color: COLORS.danger },
  ].filter(item => item.value > 0)

  const clientSourceChartData = clientSource.map((item, index) => {
    const colors = [
      COLORS.primary,
      COLORS.success,
      COLORS.warning,
      COLORS.info,
      COLORS.purple,
      COLORS.pink,
      COLORS.teal,
      COLORS.danger
    ]
    return {
      name: item.source,
      value: item.count,
      revenue: item.revenue,
      percentage: item.percentage,
      color: colors[index % colors.length]
    }
  }).filter(item => item.value > 0)

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
            <div className="filter-dropdown-wrapper">
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
              <div className="filter-dropdown-icon">
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M4 6L8 10L12 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </div>
            </div>
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
                  <ChartSkeleton height={400} />
                ) : staffPerformance.length === 0 ? (
                  <div style={{ height: '400px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <p className="no-data-message">No staff performance data available</p>
                  </div>
                ) : (
                  <ResponsiveContainer width="100%" height={500}>
                    <BarChart data={staffChartData.slice(0, 8)} margin={{ top: 20, right: 30, left: 20, bottom: 80 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                      <XAxis 
                        dataKey="name" 
                        angle={-45}
                        textAnchor="end"
                        height={100}
                        tick={{ fontSize: 11, fill: '#6b7280' }}
                        stroke="#9ca3af"
                      />
                      <YAxis 
                        tick={{ fontSize: 11, fill: '#6b7280' }}
                        stroke="#9ca3af"
                        tickFormatter={(value) => value >= 1000 ? `${(value / 1000).toFixed(0)}k` : value}
                      />
                      <Tooltip 
                        contentStyle={{
                          backgroundColor: 'white',
                          border: '1px solid #e5e7eb',
                          borderRadius: '8px',
                          padding: '12px',
                          boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)'
                        }}
                        formatter={(value, name) => {
                          if (name === 'Revenue') return [formatCurrency(value), name]
                          return [value, name]
                        }}
                        labelStyle={{ fontWeight: 600, marginBottom: '8px' }}
                        cursor={{ fill: 'rgba(0, 0, 0, 0.05)' }}
                      />
                      <Legend 
                        wrapperStyle={{ paddingTop: '20px' }}
                        iconType="square"
                      />
                      <Bar 
                        dataKey="revenue" 
                        fill="#10b981" 
                        name="Revenue"
                        radius={[4, 4, 0, 0]}
                      />
                      <Bar 
                        dataKey="services" 
                        fill="#3b82f6" 
                        name="Services"
                        radius={[4, 4, 0, 0]}
                      />
                      <Bar 
                        dataKey="appointments" 
                        fill="#8b5cf6" 
                        name="Appointments"
                        radius={[4, 4, 0, 0]}
                      />
                    </BarChart>
                  </ResponsiveContainer>
                )}
              </div>
            </div>

            {/* Top Performer Panel */}
            <div className="staff-panel">
              <div className="panel-header">Top Performer (Company-Wide)</div>
              <div className="panel-content">
                {loading ? (
                  <ChartSkeleton height={400} />
                ) : topPerformer ? (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0px', height: '100%' }}>
                    {/* Top Performer Info Header */}
                    <div style={{ 
                      display: 'flex', 
                      alignItems: 'center', 
                      justifyContent: 'space-between',
                      padding: '4px 8px',
                      background: 'linear-gradient(135deg, #f0fdfa 0%, #ffffff 100%)',
                      borderRadius: '12px',
                      border: '1px solid #0F766E20',
                      marginTop: '-12px'
                    }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                        <div style={{
                          width: '50px',
                          height: '50px',
                          borderRadius: '50%',
                          background: '#0F766E',
                          color: 'white',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          fontSize: '20px',
                          fontWeight: '700',
                          position: 'relative'
                        }}>
                          {topPerformer.staff_name.charAt(0)}
                          <div style={{
                            position: 'absolute',
                            top: '-4px',
                            right: '-4px',
                            width: '20px',
                            height: '20px',
                            background: '#0F766E',
                            borderRadius: '50%',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            border: '2px solid white',
                            fontSize: '10px'
                          }}>
                            <FaCrown />
                          </div>
                        </div>
                        <div>
                          <h3 style={{ margin: 0, fontSize: '16px', fontWeight: '700', color: '#0f172a' }}>
                            {topPerformer.staff_name}
                          </h3>
                          <div style={{
                            display: 'inline-block',
                            padding: '2px 6px',
                            background: '#0F766E',
                            color: 'white',
                            borderRadius: '6px',
                            fontSize: '9px',
                            fontWeight: '600',
                            marginTop: '2px'
                          }}>
                            TOP PERFORMER
                          </div>
                        </div>
                      </div>
                      <div style={{ textAlign: 'right' }}>
                        <div style={{ fontSize: '20px', fontWeight: '700', color: '#0F766E' }}>
                          {topPerformer.performance_score}
                        </div>
                        <div style={{ fontSize: '11px', color: '#6b7280' }}>/100 Score</div>
                      </div>
                    </div>

                    {/* Horizontal Bar Chart */}
                    <div style={{ flex: 1, minHeight: 0, marginTop: '8px', marginBottom: '12px' }}>
                      <ResponsiveContainer width="100%" height={350}>
                        <BarChart 
                          data={topPerformerBarData} 
                          layout="vertical"
                          margin={{ top: 20, right: 30, bottom: 30, left: 90 }}
                        >
                          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                          <XAxis 
                            type="number" 
                            domain={[0, 100]}
                            tick={{ fontSize: 11, fill: '#6b7280' }} 
                            stroke="#9ca3af"
                            tickFormatter={(value) => `${value}%`}
                          />
                          <YAxis 
                            type="category" 
                            dataKey="metric" 
                            tick={{ fontSize: 12, fill: '#6b7280' }}
                            stroke="#9ca3af"
                            width={80}
                          />
                          <Tooltip 
                            contentStyle={{
                              backgroundColor: 'white',
                              border: '1px solid #e5e7eb',
                              borderRadius: '8px',
                              padding: '12px',
                              boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)'
                            }}
                            formatter={(value, name, props) => {
                              return [props.payload.formatted, props.payload.metric]
                            }}
                            labelStyle={{ fontWeight: 600, marginBottom: '8px' }}
                            cursor={{ fill: 'rgba(0, 0, 0, 0.05)' }}
                          />
                          <Bar 
                            dataKey="value" 
                            radius={[0, 4, 4, 0]}
                          >
                            {topPerformerBarData.map((entry, index) => (
                              <Cell key={`cell-${index}`} fill={entry.color} />
                            ))}
                          </Bar>
                        </BarChart>
                      </ResponsiveContainer>
                    </div>

                    {/* Performance Metrics Summary */}
                    <div style={{
                      display: 'grid',
                      gridTemplateColumns: 'repeat(4, 1fr)',
                      gap: '12px',
                      padding: '16px',
                      background: '#f9fafb',
                      borderRadius: '12px'
                    }}>
                      <div style={{ textAlign: 'center' }}>
                        <div style={{ fontSize: '20px', fontWeight: '700', color: '#10b981', marginBottom: '4px' }}>
                          {formatCurrency(topPerformer.revenue)}
                        </div>
                        <div style={{ fontSize: '11px', color: '#6b7280', textTransform: 'uppercase' }}>Revenue</div>
                      </div>
                      <div style={{ textAlign: 'center' }}>
                        <div style={{ fontSize: '20px', fontWeight: '700', color: '#3b82f6', marginBottom: '4px' }}>
                          {topPerformer.service_count}
                        </div>
                        <div style={{ fontSize: '11px', color: '#6b7280', textTransform: 'uppercase' }}>Services</div>
                      </div>
                      <div style={{ textAlign: 'center' }}>
                        <div style={{ fontSize: '20px', fontWeight: '700', color: '#d97706', marginBottom: '4px' }}>
                          {topPerformer.avg_rating}/5
                        </div>
                        <div style={{ fontSize: '11px', color: '#6b7280', textTransform: 'uppercase' }}>Rating</div>
                      </div>
                      <div style={{ textAlign: 'center' }}>
                        <div style={{ fontSize: '20px', fontWeight: '700', color: '#8b5cf6', marginBottom: '4px' }}>
                          {topPerformer.completed_appointments}
                        </div>
                        <div style={{ fontSize: '11px', color: '#6b7280', textTransform: 'uppercase' }}>Appointments</div>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div style={{ height: '400px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <p className="no-data-message">No data available</p>
                  </div>
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
                        <th>
                          <span className="th-content">
                            <span>#</span>
                          </span>
                        </th>
                        <th>
                          <span className="th-content">
                            <span>Staff Name</span>
                          </span>
                        </th>
                        <th>
                          <span className="th-content">
                            <span>Item Count</span>
                          </span>
                        </th>
                        <th>
                          <span className="th-content">
                            <span>Service</span>
                          </span>
                        </th>
                        <th>
                          <span className="th-content">
                            <span>Package</span>
                          </span>
                        </th>
                        <th>
                          <span className="th-content">
                            <span>Product</span>
                          </span>
                        </th>
                        <th>
                          <span className="th-content">
                            <span>Prepaid</span>
                          </span>
                        </th>
                        <th>
                          <span className="th-content">
                            <span>Membership</span>
                          </span>
                        </th>
                        <th>
                          <span className="th-content">
                            <span>Total</span>
                          </span>
                        </th>
                        <th>
                          <span className="th-content">
                            <span>Avg. Bill (₹)</span>
                          </span>
                        </th>
                        <th>
                          <span className="th-content">
                            <span>Info</span>
                          </span>
                        </th>
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
                        staffPerformance.map((staff, index) => {
                          const isTopThree = index < 3
                          const rowClass = index === 0 ? 'row-gold' : index === 1 ? 'row-silver' : index === 2 ? 'row-bronze' : ''
                          return (
                            <tr key={staff.staff_id} className={rowClass}>
                              <td data-label="#">
                                <span className="rank-badge-table">{index + 1}</span>
                              </td>
                              <td data-label="Staff Name">
                                <div className="staff-name-cell">
                                  <FaUser className="staff-icon" />
                                  <span>{staff.staff_name}</span>
                                </div>
                              </td>
                              <td data-label="Item Count">{staff.total_services.toLocaleString()}</td>
                              <td data-label="Service">{staff.service_count ? staff.service_count.toLocaleString() : '-'}</td>
                              <td data-label="Package">{staff.package_count ? staff.package_count.toLocaleString() : '-'}</td>
                              <td data-label="Product">{staff.product_count ? staff.product_count.toLocaleString() : '-'}</td>
                              <td data-label="Prepaid">{staff.prepaid_count ? staff.prepaid_count.toLocaleString() : '-'}</td>
                              <td data-label="Membership">{staff.membership_count ? staff.membership_count.toLocaleString() : '-'}</td>
                              <td className="amount-cell" data-label="Total">{formatCurrency(staff.total_revenue)}</td>
                              <td className="amount-cell" data-label="Avg. Bill">{formatCurrency(staff.total_revenue / (staff.total_services || 1))}</td>
                              <td data-label="Info">
                                <button 
                                  className="info-btn"
                                  onClick={() => {
                                    setSelectedStaff(staff)
                                    setShowStaffModal(true)
                                  }}
                                >
                                  <FaInfoCircle className="info-icon" />
                                  <span>Info</span>
                                </button>
                              </td>
                          </tr>
                          )
                        })
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
            <DashboardStatsCards 
              stats={stats}
              loading={loading}
              formatCurrency={formatCurrency}
            />

            {/* Sales Insights - Tab-based lazy loading */}
            <SalesInsights
              dateRange={getDateRange()}
              formatCurrency={formatCurrency}
            />

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

            {/* Payment Distribution */}
            <div className="chart-card" style={{
              backgroundColor: 'white',
              padding: '20px',
              borderRadius: '12px',
              boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
            }}>
              <h3 style={{ marginTop: 0, marginBottom: '20px', fontSize: '16px', fontWeight: '600' }}>
                Payment Distribution
              </h3>
              {loading ? (
                <div style={{ padding: '20px', textAlign: 'center', color: '#9ca3af' }}>Loading...</div>
              ) : paymentDistribution.length === 0 ? (
                <div style={{ padding: '20px', textAlign: 'center', color: '#9ca3af' }}>No payment data available</div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  {paymentDistribution.map((payment, index) => {
                    const paymentIcons = {
                      'upi': <FaMobileAlt size={20} />,
                      'card': <FaCreditCard size={20} />,
                      'cash': <FaMoneyBillWave size={20} />
                    }
                    const paymentColors = {
                      'upi': '#6366f1',
                      'card': '#3b82f6',
                      'cash': '#10b981'
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
                        border: `1px solid ${color}20`
            }}>
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
                {loading ? (
                  <ChartSkeleton height={250} />
                ) : clientSourceChartData.length === 0 ? (
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
                ) : (
                  <div>
                    <ResponsiveContainer width="100%" height={250}>
                      <PieChart>
                        <Pie
                          data={clientSourceChartData}
                          cx="50%"
                          cy="50%"
                          labelLine={false}
                          label={({ name, percentage }) => `${name}: ${percentage}%`}
                          outerRadius={80}
                          fill="#8884d8"
                          dataKey="value"
                        >
                          {clientSourceChartData.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.color} />
                          ))}
                        </Pie>
                        <Tooltip 
                          content={({ active, payload }) => {
                            if (active && payload && payload.length) {
                              const data = payload[0].payload
                              return (
                                <div style={{
                                  backgroundColor: 'white',
                                  padding: '10px',
                                  border: '1px solid #ccc',
                                  borderRadius: '4px',
                                }}>
                                  <p style={{ margin: 0, fontWeight: 'bold' }}>{data.name}</p>
                                  <p style={{ margin: '4px 0 0 0', color: '#6b7280' }}>
                                    Customers: {data.value}
                                  </p>
                                  <p style={{ margin: '4px 0 0 0', color: data.color }}>
                                    Revenue: {formatCurrency(data.revenue)}
                                  </p>
                                  <p style={{ margin: '4px 0 0 0', color: '#6b7280' }}>
                                    {data.percentage}% of total
                                  </p>
                                </div>
                              )
                            }
                            return null
                          }}
                        />
                        <Legend />
                      </PieChart>
                    </ResponsiveContainer>
                    <div style={{
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '8px',
                      marginTop: '16px',
                      paddingTop: '16px',
                      borderTop: '1px solid #e5e7eb'
                    }}>
                      {clientSourceChartData.slice(0, 5).map((item, index) => (
                        <div key={index} style={{
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          padding: '8px 12px',
                          background: '#f9fafb',
                          borderRadius: '6px'
                        }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <div style={{
                              width: '12px',
                              height: '12px',
                              borderRadius: '2px',
                              background: item.color
                            }}></div>
                            <span style={{
                              fontSize: '13px',
                              color: '#374151',
                              fontWeight: '500'
                            }}>{item.name}</span>
                          </div>
                          <span style={{
                            fontSize: '13px',
                            fontWeight: '600',
                            color: '#6b7280'
                          }}>{item.value} ({item.percentage}%)</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
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

    {/* Staff Detail Modal */}
    {showStaffModal && selectedStaff && (
      <div className="staff-modal-overlay" onClick={() => setShowStaffModal(false)}>
        <div className="staff-modal-content" onClick={(e) => e.stopPropagation()}>
          <div className="staff-modal-header">
            <div className="staff-modal-title-section">
              <div className="staff-modal-avatar">
                {selectedStaff.staff_name.charAt(0)}
              </div>
              <div>
                <h2 className="staff-modal-title">{selectedStaff.staff_name}</h2>
                <p className="staff-modal-subtitle">Performance Details</p>
              </div>
            </div>
            <button 
              className="staff-modal-close"
              onClick={() => setShowStaffModal(false)}
            >
              <FaTimes />
            </button>
          </div>

          <div className="staff-modal-body">
            <div className="staff-modal-grid">
              <div className="staff-modal-card">
                <div className="staff-modal-card-header">
                  <FaDollarSign className="staff-modal-card-icon" />
                  <h3>Revenue</h3>
                </div>
                <div className="staff-modal-card-value">
                  {formatCurrency(selectedStaff.total_revenue)}
                </div>
                {selectedStaff.commission_earned && (
                  <div className="staff-modal-card-subvalue">
                    Commission: {formatCurrency(selectedStaff.commission_earned)}
                  </div>
                )}
              </div>

              <div className="staff-modal-card">
                <div className="staff-modal-card-header">
                  <FaCut className="staff-modal-card-icon" />
                  <h3>Services</h3>
                </div>
                <div className="staff-modal-card-value">
                  {selectedStaff.total_services}
                </div>
                <div className="staff-modal-card-subvalue">
                  Total services completed
                </div>
              </div>

              <div className="staff-modal-card">
                <div className="staff-modal-card-header">
                  <FaCalendar className="staff-modal-card-icon" />
                  <h3>Appointments</h3>
                </div>
                <div className="staff-modal-card-value">
                  {selectedStaff.completed_appointments}
                </div>
                <div className="staff-modal-card-subvalue">
                  Completed appointments
                </div>
              </div>

              <div className="staff-modal-card">
                <div className="staff-modal-card-header">
                  <FaChartLine className="staff-modal-card-icon" />
                  <h3>Average Bill</h3>
                </div>
                <div className="staff-modal-card-value">
                  {formatCurrency(selectedStaff.total_revenue / (selectedStaff.total_services || 1))}
                </div>
                <div className="staff-modal-card-subvalue">
                  Per service
                </div>
              </div>
            </div>

            <div className="staff-modal-section">
              <h3 className="staff-modal-section-title">Performance Summary</h3>
              <div className="staff-modal-summary">
                <div className="staff-modal-summary-item">
                  <span className="summary-label">Staff ID:</span>
                  <span className="summary-value">{selectedStaff.staff_id}</span>
                </div>
                <div className="staff-modal-summary-item">
                  <span className="summary-label">Total Revenue:</span>
                  <span className="summary-value">{formatCurrency(selectedStaff.total_revenue)}</span>
                </div>
                <div className="staff-modal-summary-item">
                  <span className="summary-label">Total Services:</span>
                  <span className="summary-value">{selectedStaff.total_services}</span>
                </div>
                <div className="staff-modal-summary-item">
                  <span className="summary-label">Completed Appointments:</span>
                  <span className="summary-value">{selectedStaff.completed_appointments}</span>
                </div>
                {selectedStaff.commission_earned && (
                  <div className="staff-modal-summary-item">
                    <span className="summary-label">Commission Earned:</span>
                    <span className="summary-value">{formatCurrency(selectedStaff.commission_earned)}</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    )}

    {/* Offering Clients Modal */}
    {showOfferingModal && selectedOffering && (
      <div className="customer-modal-overlay" onClick={() => setShowOfferingModal(false)}>
        <div className="customer-modal-content" onClick={(e) => e.stopPropagation()}>
          <div className="customer-modal-header">
            <h2>Clients for {selectedOffering.name}</h2>
            <button className="customer-modal-close" onClick={() => setShowOfferingModal(false)}>
              <FaTimes />
            </button>
          </div>

          <div className="customer-modal-body">
            {loadingOfferingClients ? (
              <div className="customer-modal-loading">Loading client details...</div>
            ) : offeringClients.length === 0 ? (
              <div className="customer-modal-error">No clients found for this offering</div>
            ) : (
              <>
                {/* Offering Statistics */}
                <div className="customer-details-section">
                  <h3>Offering Information</h3>
                  <div className="customer-details-grid">
                    <div className="customer-detail-item">
                      <span className="detail-label">Name:</span>
                      <span className="detail-value">{selectedOffering.name}</span>
                    </div>
                    <div className="customer-detail-item">
                      <span className="detail-label">Type:</span>
                      <span className="detail-value" style={{ textTransform: 'capitalize' }}>
                        {selectedOffering.type}
                      </span>
                    </div>
                    <div className="customer-detail-item">
                      <span className="detail-label">Total Quantity Sold:</span>
                      <span className="detail-value">{selectedOffering.quantity}</span>
                    </div>
                    <div className="customer-detail-item">
                      <span className="detail-label">Total Revenue:</span>
                      <span className="detail-value" style={{ color: '#10b981', fontWeight: '600' }}>
                        {formatCurrency(selectedOffering.revenue)}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Top Statistics */}
                <div className="customer-details-section">
                  <h3>Client Statistics</h3>
                  <div className="customer-stats-grid">
                    <div className="customer-stat-card">
                      <div className="stat-label">Total Clients</div>
                      <div className="stat-value">
                        {offeringClients.length}
                      </div>
                      <div className="stat-description">Customers who purchased</div>
                    </div>
                    <div className="customer-stat-card">
                      <div className="stat-label">Total Purchases</div>
                      <div className="stat-value">
                        {offeringClients.reduce((sum, client) => sum + (client.purchase_count || 0), 0)}
                      </div>
                      <div className="stat-description">Total times purchased</div>
                    </div>
                    <div className="customer-stat-card">
                      <div className="stat-label">Average per Client</div>
                      <div className="stat-value revenue-stat">
                        {formatCurrency(
                          offeringClients.length > 0
                            ? offeringClients.reduce((sum, client) => sum + (client.total_spent || 0), 0) / offeringClients.length
                            : 0
                        )}
                      </div>
                      <div className="stat-description">Average spending per client</div>
                    </div>
                  </div>
                </div>

                {/* Clients List */}
                <div className="customer-details-section">
                  <h3>Clients List ({offeringClients.length})</h3>
                  <div className="table-container" style={{ marginTop: '1rem' }}>
                    <table className="data-table">
                      <thead>
                        <tr>
                          <th className="text-left col-number">#</th>
                          <th className="text-left">Customer Name</th>
                          <th className="text-left">Mobile</th>
                          <th className="text-left col-count">Purchases</th>
                          <th className="text-left col-revenue">Total Spent</th>
                          <th className="text-left">Last Purchase</th>
                        </tr>
                      </thead>
                      <tbody>
                        {offeringClients.map((client, index) => (
                          <tr key={client.customer_id || index}>
                            <td className="text-left col-number">{index + 1}</td>
                            <td className="text-left">{client.customer_name || '-'}</td>
                            <td className="text-left">{client.mobile || '-'}</td>
                            <td className="text-left col-count">{client.purchase_count || 0}</td>
                            <td className="text-left col-revenue">
                              {formatCurrency(client.total_spent || 0)}
                            </td>
                            <td className="text-left">{formatDate(client.last_purchase_date)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    )}
    </PageTransition>
  )
}

export default Dashboard

