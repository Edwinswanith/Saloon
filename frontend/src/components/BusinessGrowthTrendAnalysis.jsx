import React, { useState, useEffect } from 'react'
import {
  FaArrowLeft,
  FaChartLine,
  FaShoppingBasket,
  FaUserPlus,
  FaExchangeAlt,
} from 'react-icons/fa'
import './BusinessGrowthTrendAnalysis.css'
import { API_BASE_URL } from '../config'
import { apiGet } from '../utils/api'
import { useAuth } from '../contexts/AuthContext'
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
const BusinessGrowthTrendAnalysis = ({ setActivePage }) => {
  const { currentBranch } = useAuth()
  const [dateRange, setDateRange] = useState('last-3-years')
  const [viewBy, setViewBy] = useState('monthly')
  const [loading, setLoading] = useState(false)
  const [kpiData, setKpiData] = useState(null)
  const [financialTrendsData, setFinancialTrendsData] = useState([
    { month: 'Jan', grossRevenue: 150000, totalServiceValue: 200000 },
    { month: 'Feb', grossRevenue: 300000, totalServiceValue: 400000 },
    { month: 'Mar', grossRevenue: 500000, totalServiceValue: 550000 },
  ])
  const [clientGrowthData, setClientGrowthData] = useState([
    { month: 'Jan', newClients: 50, returningVisits: 450 },
    { month: 'Feb', newClients: 50, returningVisits: 450 },
    { month: 'Mar', newClients: 50, returningVisits: 450 },
  ])

  

  const handleBackToReports = () => {
    if (setActivePage) {
      setActivePage('reports-analytics')
    }
  }

  const getDateRangeForAPI = () => {
    const today = new Date()
    let startDate, endDate

    switch (dateRange) {
      case 'last-year':
        startDate = new Date(today.getFullYear() - 1, 0, 1)
        endDate = new Date(today.getFullYear() - 1, 11, 31)
        break
      case 'last-2-years':
        startDate = new Date(today.getFullYear() - 2, 0, 1)
        endDate = today
        break
      case 'last-3-years':
        startDate = new Date(today.getFullYear() - 3, 0, 1)
        endDate = today
        break
      case 'last-5-years':
        startDate = new Date(today.getFullYear() - 5, 0, 1)
        endDate = today
        break
      default:
        startDate = new Date(today.getFullYear() - 3, 0, 1)
        endDate = today
    }

    return {
      start_date: startDate.toISOString().split('T')[0],
      end_date: endDate.toISOString().split('T')[0]
    }
  }

  const fetchBusinessGrowthData = async () => {
    try {
      setLoading(true)
      const dateRangeParams = getDateRangeForAPI()
      const params = new URLSearchParams({
        start_date: dateRangeParams.start_date,
        end_date: dateRangeParams.end_date
      })

      const response = await apiGet(`/api/reports/business-growth?${params}`)
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      const data = await response.json()

      // Process the data for charts
      if (Array.isArray(data) && data.length > 0) {
        // Calculate KPIs (Year-over-Year growth)
        // For now, using mock data - can be enhanced with actual calculations
        // Process financial trends data
        const processedFinancialData = data.map((item, index) => ({
          month: new Date(item.month + '-01').toLocaleDateString('en-US', { month: 'short' }),
          grossRevenue: item.revenue || 0,
          totalServiceValue: (item.revenue || 0) * 1.2 // Approximate service value
        }))
        setFinancialTrendsData(processedFinancialData)
      }
    } catch (error) {
      console.error('Error fetching business growth data:', error)
      // Keep default data on error
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchBusinessGrowthData()
  }, [dateRange, viewBy, currentBranch])

  // Listen for branch changes
  useEffect(() => {
    const handleBranchChange = () => {
      console.log('[BusinessGrowthTrendAnalysis] Branch changed, refreshing data...')
      fetchBusinessGrowthData()
    }
    
    window.addEventListener('branchChanged', handleBranchChange)
    return () => window.removeEventListener('branchChanged', handleBranchChange)
  }, [currentBranch])

  const kpiCards = [
    {
      id: 1,
      title: 'REVENUE GROWTH (YOY)',
      value: '+15.5',
      unit: '%',
      icon: <FaChartLine />,
      color: 'green',
    },
    {
      id: 2,
      title: 'AVG. BILL VALUE GROWTH (YOY)',
      value: '+4.2',
      unit: '%',
      icon: <FaShoppingBasket />,
      color: 'blue',
    },
    {
      id: 3,
      title: 'NEW CLIENT GROWTH (YOY)',
      value: '+8.0',
      unit: '%',
      icon: <FaUserPlus />,
      color: 'orange',
    },
    {
      id: 4,
      title: 'TOTAL TRANSACTIONS GROWTH (YOY)',
      value: '+22.1',
      unit: '%',
      icon: <FaExchangeAlt />,
      color: 'purple',
    },
  ]



  const formatCurrency = (value) => {
    if (value >= 100000) {
      return `₹${(value / 100000).toFixed(1)}L`
    } else if (value >= 1000) {
      return `₹${(value / 1000).toFixed(1)}K`
    }
    return `₹${value.toFixed(0)}`
  }

  return (
    <div className="business-growth-trend-analysis-page">
      <div className="business-growth-container">
        {loading && (
          <div style={{ textAlign: 'center', padding: '20px', color: '#6b7280' }}>
            Loading data...
          </div>
        )}
        {/* Back Button and Filters */}
        <div className="top-controls">
          <button className="back-button" onClick={handleBackToReports}>
            <FaArrowLeft />
            Back to Reports Hub
          </button>

          <div className="filters-section">
            <div className="filter-group">
              <label className="filter-label">DATE RANGE</label>
              <select
                className="filter-dropdown"
                value={dateRange}
                onChange={(e) => setDateRange(e.target.value)}
              >
                <option value="last-year">Last Year</option>
                <option value="last-2-years">Last 2 Years</option>
                <option value="last-3-years">Last 3 Years</option>
                <option value="last-5-years">Last 5 Years</option>
                <option value="custom">Custom Range</option>
              </select>
            </div>

            <div className="filter-group">
              <label className="filter-label">VIEW BY</label>
              <select
                className="filter-dropdown"
                value={viewBy}
                onChange={(e) => setViewBy(e.target.value)}
              >
                <option value="daily">Daily</option>
                <option value="weekly">Weekly</option>
                <option value="monthly">Monthly</option>
                <option value="yearly">Yearly</option>
              </select>
            </div>
          </div>
        </div>

        {/* KPI Cards */}
        <div className="kpi-cards-grid">
          {kpiCards.map((card) => (
            <div key={card.id} className={`kpi-card ${card.color}`}>
              <div className="kpi-icon">{card.icon}</div>
              <div className="kpi-content">
                <div className="kpi-title">{card.title}</div>
                <div className="kpi-value">
                  {card.value}
                  <span className="kpi-unit">{card.unit}</span>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Charts Section */}
        <div className="charts-section">
          {/* Financial Trends Chart */}
          <div className="chart-card">
            <h3 className="chart-title">Financial Trends (Healthy Growth)</h3>
            <p className="chart-subtitle">
              Comparing the value of services rendered vs. actual revenue
              collected.
            </p>
            <div className="chart-area-container">
              {loading ? (
                <div style={{ height: '300px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  Loading...
                </div>
              ) : financialTrendsData.length === 0 ? (
                <div style={{ height: '300px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  No data available
                </div>
              ) : (
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={financialTrendsData}>
                    <defs>
                      <linearGradient id="colorRevenue" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#14b8a6" stopOpacity={0.8}/>
                        <stop offset="95%" stopColor="#14b8a6" stopOpacity={0.1}/>
                      </linearGradient>
                      <linearGradient id="colorService" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#1e40af" stopOpacity={0.8}/>
                        <stop offset="95%" stopColor="#1e40af" stopOpacity={0.1}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                    <XAxis 
                      dataKey="month" 
                      tick={{ fontSize: 12, fill: '#6b7280' }}
                      stroke="#9ca3af"
                    />
                    <YAxis 
                      tick={{ fontSize: 12, fill: '#6b7280' }}
                      stroke="#9ca3af"
                      tickFormatter={(value) => formatCurrency(value)}
                    />
                    <Tooltip 
                      contentStyle={{
                        backgroundColor: 'white',
                        border: '1px solid #e5e7eb',
                        borderRadius: '8px',
                        padding: '12px',
                        boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)'
                      }}
                      formatter={(value) => [formatCurrency(value), '']}
                      labelStyle={{ fontWeight: 600, marginBottom: '8px' }}
                    />
                    <Legend 
                      wrapperStyle={{ paddingTop: '20px' }}
                      iconType="line"
                    />
                    <Area 
                      type="monotone" 
                      dataKey="totalServiceValue" 
                      stroke="#1e40af" 
                      strokeWidth={2}
                      fillOpacity={1} 
                      fill="url(#colorService)" 
                      name="Total Service Value"
                    />
                    <Area 
                      type="monotone" 
                      dataKey="grossRevenue" 
                      stroke="#14b8a6" 
                      strokeWidth={2}
                      fillOpacity={1} 
                      fill="url(#colorRevenue)" 
                      name="Gross Revenue (Collected)"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>

          {/* Client Growth Engine Chart */}
          <div className="chart-card">
            <h3 className="chart-title">Client Growth Engine (Healthy Growth)</h3>
            <p className="chart-subtitle">
              Analyzing new client acquisition vs. returning client loyalty.
            </p>
            <div className="chart-bars-container">
              {loading ? (
                <div style={{ height: '300px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  Loading...
                </div>
              ) : clientGrowthData.length === 0 ? (
                <div style={{ height: '300px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  No data available
                </div>
              ) : (
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={clientGrowthData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                    <XAxis 
                      dataKey="month" 
                      tick={{ fontSize: 12, fill: '#6b7280' }}
                      stroke="#9ca3af"
                    />
                    <YAxis 
                      tick={{ fontSize: 12, fill: '#6b7280' }}
                      stroke="#9ca3af"
                    />
                    <Tooltip 
                      contentStyle={{
                        backgroundColor: 'white',
                        border: '1px solid #e5e7eb',
                        borderRadius: '8px',
                        padding: '12px',
                        boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)'
                      }}
                      cursor={{ fill: 'rgba(0, 0, 0, 0.05)' }}
                    />
                    <Legend 
                      wrapperStyle={{ paddingTop: '20px' }}
                      iconType="square"
                    />
                    <Bar 
                      dataKey="returningVisits" 
                      stackId="a" 
                      fill="#16a34a" 
                      name="Returning Client Visits"
                      radius={[0, 0, 0, 0]}
                    />
                    <Bar 
                      dataKey="newClients" 
                      stackId="a" 
                      fill="#86efac" 
                      name="New Clients Acquired"
                      radius={[4, 4, 0, 0]}
                    />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default BusinessGrowthTrendAnalysis

