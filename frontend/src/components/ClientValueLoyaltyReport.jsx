import React, { useState, useEffect } from 'react'
import {
  FaBars,
  FaUser,
  FaUsers,
  FaPercentage,
  FaMoneyBillWave,
  FaChartLine,
} from 'react-icons/fa'
import './ClientValueLoyaltyReport.css'
import { API_BASE_URL } from '../config'
import { apiGet } from '../utils/api'
import {
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'

const ClientValueLoyaltyReport = ({ setActivePage }) => {
  const [dateRange, setDateRange] = useState('Last 12 Months')
  const [activeTab, setActiveTab] = useState('top-spenders')
  const [loading, setLoading] = useState(true)
  const [summaryMetrics, setSummaryMetrics] = useState({
    totalVIPClients: 0,
    percentageRevenueFromVIPs: 0,
    avgLifetimeValue: 0,
    vipSpendMultiple: 0,
  })
  const [revenueDistributionData, setRevenueDistributionData] = useState([])
  const [topSpendersData, setTopSpendersData] = useState([])
  const [mostFrequentData, setMostFrequentData] = useState([])
  const [newHighValueData, setNewHighValueData] = useState([])

  useEffect(() => {
    fetchClientValueData()
  }, [dateRange])

  const fetchClientValueData = async () => {
    try {
      setLoading(true)
      const dateParams = getDateRangeParams(dateRange)
      
      const params = new URLSearchParams({
        start: dateParams.start_date,
        end: dateParams.end_date,
        top_n: '10'
      })
      
      const response = await apiGet(`/api/analytics/client-revenue-pareto?${params}`)
      
      if (response.ok) {
        const data = await response.json()
        
        // Update summary metrics
        setSummaryMetrics(data.metrics || {
          totalVIPClients: 0,
          percentageRevenueFromVIPs: 0,
          avgLifetimeValue: 0,
          vipSpendMultiple: 0,
        })
        
        // Transform data for chart
        const chartData = (data.clientData || []).map((client, index) => ({
          client_name: client.name,
          revenue: client.revenue,
          cumulative_percentage: client.cumulative_pct || data.cumulativePct[index] || 0,
          color: client.color
        }))
        
        setRevenueDistributionData(chartData)
        
        // Update client lists
        setTopSpendersData(data.topSpenders || [])
        setMostFrequentData(data.mostFrequent || [])
        setNewHighValueData(data.newHighValue || [])
      } else {
        console.error('Failed to fetch client value data:', response.statusText)
      }
    } catch (error) {
      console.error('Error fetching client value data:', error)
    } finally {
      setLoading(false)
    }
  }

  const getDateRangeParams = (range) => {
    const end = new Date()
    let start = new Date()
    
    switch (range) {
      case 'Last 3 Months':
        start.setMonth(start.getMonth() - 3)
        break
      case 'Last 6 Months':
        start.setMonth(start.getMonth() - 6)
        break
      case 'Last 12 Months':
        start.setMonth(start.getMonth() - 12)
        break
      case 'Last Year':
        start.setFullYear(start.getFullYear() - 1)
        break
      case 'All Time':
        start = new Date('2000-01-01')
        break
      default:
        start.setMonth(start.getMonth() - 12)
    }
    
    return {
      start_date: start.toISOString().split('T')[0],
      end_date: end.toISOString().split('T')[0],
    }
  }

  const getActiveTableData = () => {
    switch (activeTab) {
      case 'most-frequent':
        return mostFrequentData
      case 'new-high-value':
        return newHighValueData
      default:
        return topSpendersData
    }
  }

  const handleBackToReports = () => {
    if (setActivePage) {
      setActivePage('reports-analytics')
    }
  }

  const formatCurrency = (value) => {
    return `₹${value.toLocaleString('en-IN')}`
  }

  const formatNumber = (value) => {
    return value.toLocaleString('en-IN')
  }

  const getMaxRevenue = () => {
    if (revenueDistributionData.length === 0) return 60000
    const max = Math.max(...revenueDistributionData.map((d) => d.revenue || 0))
    // Round up to nearest 15k for cleaner axis
    return Math.ceil(max / 15000) * 15000
  }

  const getInitials = (name) => {
    if (!name) return 'N/A'
    const parts = name.trim().split(' ')
    if (parts.length === 1) return parts[0].substring(0, 2).toUpperCase()
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
  }

  const getColorForIndex = (index) => {
    const colors = [
      '#ef4444', '#8b5cf6', '#10b981', '#f59e0b', '#3b82f6',
      '#6366f1', '#ec4899', '#14b8a6', '#f97316', '#9ca3af'
    ]
    return colors[index % colors.length]
  }

  const formatLastVisit = (dateString) => {
    if (!dateString) return 'N/A'
    const date = new Date(dateString)
    const now = new Date()
    const diffTime = Math.abs(now - date)
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
    
    if (diffDays === 0) return 'Today'
    if (diffDays === 1) return '1 day ago'
    if (diffDays < 30) return `${diffDays} days ago`
    if (diffDays < 60) return '1 month ago'
    if (diffDays < 365) return `${Math.floor(diffDays / 30)} months ago`
    return `${Math.floor(diffDays / 365)} year${Math.floor(diffDays / 365) > 1 ? 's' : ''} ago`
  }

  return (
    <div className="client-value-loyalty-page">
      {/* Header */}
      <header className="client-value-loyalty-header">
        <div className="header-left">
          <button className="menu-icon">
            <FaBars />
          </button>
          <h1 className="header-title">Client Value & Loyalty Report</h1>
        </div>
        <div className="header-right">
          <button className="user-icon">
            <FaUser />
          </button>
          <div className="logo-box">
            <span className="logo-text">HAIR STUDIO</span>
          </div>
        </div>
      </header>

      <div className="client-value-loyalty-container">
        <div className="client-value-loyalty-content">
          {/* Back Button and Date Range */}
          <div className="controls-section">
            <button className="back-button" onClick={handleBackToReports}>
              ← Back to Reports Hub
            </button>
            <div className="date-range-section">
              <label className="date-range-label">DATE RANGE</label>
              <select
                className="date-range-select"
                value={dateRange}
                onChange={(e) => setDateRange(e.target.value)}
              >
                <option>Last 3 Months</option>
                <option>Last 6 Months</option>
                <option>Last 12 Months</option>
                <option>Last Year</option>
                <option>All Time</option>
              </select>
            </div>
          </div>

          {/* Loading State */}
          {loading ? (
            <div className="loading-container">
              <div className="loading-spinner"></div>
              <p>Loading client data...</p>
            </div>
          ) : (
            <>
              {/* Top Summary Metrics */}
              <div className="summary-metrics-grid">
                <div className="metric-card orange">
                  <div className="metric-icon">
                    <FaUsers />
                  </div>
                  <div className="metric-info">
                    <h2 className="metric-value">{summaryMetrics.totalVIPClients}</h2>
                    <p className="metric-label">TOTAL VIP CLIENTS</p>
                    <p className="metric-sublabel">Top 10% of spenders</p>
                  </div>
                </div>

                <div className="metric-card red">
                  <div className="metric-icon">
                    <FaPercentage />
                  </div>
                  <div className="metric-info">
                    <h2 className="metric-value">{summaryMetrics.percentageRevenueFromVIPs}%</h2>
                    <p className="metric-label">% REVENUE FROM VIPs</p>
                    <p className="metric-sublabel">Of total revenue from top 20% clients</p>
                  </div>
                </div>

                <div className="metric-card blue">
                  <div className="metric-icon">
                    <FaMoneyBillWave />
                  </div>
                  <div className="metric-info">
                    <h2 className="metric-value">{formatCurrency(summaryMetrics.avgLifetimeValue)}</h2>
                    <p className="metric-label">AVG. LIFETIME VALUE</p>
                    <p className="metric-sublabel">Avg. lifetime spend</p>
                  </div>
                </div>

                <div className="metric-card green">
                  <div className="metric-icon">
                    <FaChartLine />
                  </div>
                  <div className="metric-info">
                    <h2 className="metric-value">{summaryMetrics.vipSpendMultiple}x</h2>
                    <p className="metric-label">VIP SPEND MULTIPLE</p>
                    <p className="metric-sublabel">More than avg. client</p>
                  </div>
                </div>
              </div>

          {/* Revenue Distribution Chart */}
          <div className="chart-section">
            <h2 className="chart-title">Client Revenue Distribution (The 80/20 Rule)</h2>
            <p className="chart-subtitle">
              This chart shows that a small percentage of clients generate a large percentage of revenue.
            </p>
            
            <div className="chart-wrapper">
              {loading ? (
                <div style={{ height: '400px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  Loading...
                </div>
              ) : revenueDistributionData.length > 0 ? (
                <ResponsiveContainer width="100%" height={400}>
                  <ComposedChart data={revenueDistributionData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                    <XAxis 
                      dataKey="client_name" 
                      tick={{ fontSize: 11, fill: '#6b7280' }}
                      stroke="#9ca3af"
                      angle={-45}
                      textAnchor="end"
                      height={100}
                    />
                    <YAxis 
                      yAxisId="left"
                      tick={{ fontSize: 12, fill: '#6b7280' }}
                      stroke="#9ca3af"
                      tickFormatter={(value) => value >= 1000 ? `₹${Math.round(value / 1000)}k` : `₹${value}`}
                    />
                    <YAxis 
                      yAxisId="right"
                      orientation="right"
                      tick={{ fontSize: 12, fill: '#6b7280' }}
                      stroke="#9ca3af"
                      domain={[0, 100]}
                      tickFormatter={(value) => `${value}%`}
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
                        if (name === 'Cumulative %') return [`${value}%`, name]
                        return [formatCurrency(value), name]
                      }}
                      labelStyle={{ fontWeight: 600, marginBottom: '8px' }}
                    />
                    <Legend 
                      wrapperStyle={{ paddingTop: '20px' }}
                    />
                    <Bar 
                      yAxisId="left"
                      dataKey="revenue" 
                      fill="#4f46e5" 
                      name="Revenue"
                      radius={[4, 4, 0, 0]}
                    />
                    <Line 
                      yAxisId="right"
                      type="monotone" 
                      dataKey="cumulative_percentage" 
                      stroke="#f97316" 
                      strokeWidth={2}
                      dot={{ fill: '#f97316', r: 4 }}
                      name="Cumulative %"
                    />
                  </ComposedChart>
                </ResponsiveContainer>
              ) : (
                <div style={{
                  height: '400px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#6b7280',
                  fontSize: '14px'
                }}>
                  No client revenue data available for the selected period.
                </div>
              )}
            </div>
          </div>

          {/* Client Table with Tabs */}
          <div className="table-section">
            <div className="table-tabs">
              <button
                className={`tab-button ${activeTab === 'top-spenders' ? 'active' : ''}`}
                onClick={() => setActiveTab('top-spenders')}
              >
                Top Spenders
              </button>
              <button
                className={`tab-button ${activeTab === 'most-frequent' ? 'active' : ''}`}
                onClick={() => setActiveTab('most-frequent')}
              >
                Most Frequent Visitors
              </button>
              <button
                className={`tab-button ${activeTab === 'new-high-value' ? 'active' : ''}`}
                onClick={() => setActiveTab('new-high-value')}
              >
                New High-Value Clients
              </button>
            </div>

            <div className="client-table-container">
              <table className="client-table">
                <thead>
                  <tr>
                    <th className="text-left">Client</th>
                    <th className="text-center">Total Visits</th>
                    <th className="text-center">Last Visit</th>
                    <th className="text-right">Total Spend</th>
                  </tr>
                </thead>
                <tbody>
                  {getActiveTableData().length > 0 ? (
                    getActiveTableData().map((client, index) => (
                      <tr key={client.id || index}>
                        <td className="client-cell">
                          <div 
                            className="client-avatar" 
                            style={{ backgroundColor: client.color || getColorForIndex(index) }}
                          >
                            {client.initials || getInitials(client.name || client.client_name)}
                          </div>
                          <span className="client-name">{client.name || client.client_name || 'Unknown'}</span>
                        </td>
                        <td className="text-center">{client.totalVisits || client.total_visits || 0}</td>
                        <td className="text-center">
                          {formatLastVisit(client.lastVisit || client.last_visit)}
                        </td>
                        <td className="text-right spend-value">
                          {formatCurrency(client.totalSpend || client.total_spend || 0)}
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan="4" className="text-center no-data-cell">
                        No client data available for the selected period.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}

export default ClientValueLoyaltyReport

