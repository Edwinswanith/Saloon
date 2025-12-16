import React, { useState, useEffect } from 'react'
import {
  FaBars,
  FaBell,
  FaUser,
  FaArrowLeft,
  FaChartLine,
  FaShoppingBasket,
  FaUserPlus,
  FaExchangeAlt,
} from 'react-icons/fa'
import './BusinessGrowthTrendAnalysis.css'
import { API_BASE_URL } from '../config'
const BusinessGrowthTrendAnalysis = ({ setActivePage }) => {
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
  const [hoveredFinancialPoint, setHoveredFinancialPoint] = useState(null)
  const [hoveredClientPoint, setHoveredClientPoint] = useState(null)
  const [tooltipPosition, setTooltipPosition] = useState({ x: 0, y: 0 })

  

  const handleBackToReports = () => {
    if (setActivePage) {
      setActivePage('reports')
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

      const response = await fetch(`${API_BASE_URL}/api/reports/business-growth?${params}`)
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
  }, [dateRange, viewBy])

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


  const maxFinancialValue = Math.max(
    ...financialTrendsData.flatMap((d) => [d.grossRevenue, d.totalServiceValue]),
    600000
  )

  const maxClientValue = Math.max(
    ...clientGrowthData.flatMap((d) => [d.newClients + d.returningVisits]),
    600
  )

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
      {/* Header */}
      <header className="business-growth-header">
        <div className="header-left">
          <button className="menu-icon">
            <FaBars />
          </button>
          <h1 className="header-title">Business Growth & Trend Analysis</h1>
        </div>
        <div className="header-right">
          <div className="logo-box">
            <span className="logo-text">HAIR STUDIO</span>
          </div>
          <button className="header-icon bell-icon">
            <FaBell />
          </button>
          <button className="header-icon user-icon">
            <FaUser />
          </button>
        </div>
      </header>

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
            <div className="chart-container">
              <div className="chart-y-axis">
                <div className="y-axis-label">{formatCurrency(maxFinancialValue)}</div>
                <div className="y-axis-label">{formatCurrency(maxFinancialValue * 0.75)}</div>
                <div className="y-axis-label">{formatCurrency(maxFinancialValue * 0.5)}</div>
                <div className="y-axis-label">{formatCurrency(maxFinancialValue * 0.25)}</div>
                <div className="y-axis-label">₹0</div>
              </div>
              <div 
                className="chart-area-container"
                onMouseLeave={() => setHoveredFinancialPoint(null)}
              >
                <svg
                  className="area-chart"
                  viewBox="0 0 400 200"
                  preserveAspectRatio="none"
                >
                  {/* Grid lines */}
                  {[0, 1, 2, 3, 4].map((i) => (
                    <line
                      key={i}
                      x1="0"
                      y1={i * 50}
                      x2="400"
                      y2={i * 50}
                      stroke="#e5e7eb"
                      strokeWidth="1"
                    />
                  ))}

                  {/* Total Service Value Area */}
                  {financialTrendsData.length > 0 && (
                    <path
                      d={`M 0,200 ${financialTrendsData.map((item, index) => {
                        const x = (index / Math.max(financialTrendsData.length - 1, 1)) * 400
                        const y = 200 - (item.totalServiceValue / maxFinancialValue) * 200
                        return `L ${x},${y}`
                      }).join(' ')} L 400,200 Z`}
                      fill="#1e40af"
                      opacity="0.8"
                    />
                  )}

                  {/* Gross Revenue Area */}
                  {financialTrendsData.length > 0 && (
                    <path
                      d={`M 0,200 ${financialTrendsData.map((item, index) => {
                        const x = (index / Math.max(financialTrendsData.length - 1, 1)) * 400
                        const y = 200 - (item.grossRevenue / maxFinancialValue) * 200
                        return `L ${x},${y}`
                      }).join(' ')} L 400,200 Z`}
                      fill="#14b8a6"
                      opacity="0.8"
                    />
                  )}

                  {/* Interactive hover points */}
                  {financialTrendsData.map((item, index) => {
                    const x = (index / Math.max(financialTrendsData.length - 1, 1)) * 400
                    const grossRevenueY = 200 - (item.grossRevenue / maxFinancialValue) * 200
                    const serviceValueY = 200 - (item.totalServiceValue / maxFinancialValue) * 200
                    
                    return (
                      <g key={index}>
                        {/* Invisible hover area */}
                        <rect
                          x={x - 30}
                          y="0"
                          width="60"
                          height="200"
                          fill="transparent"
                          style={{ cursor: 'pointer' }}
                          onMouseEnter={(e) => {
                            const rect = e.currentTarget.closest('.chart-area-container')?.getBoundingClientRect()
                            if (rect) {
                              const svgRect = e.currentTarget.getBoundingClientRect()
                              setTooltipPosition({
                                x: svgRect.left + svgRect.width / 2,
                                y: svgRect.top
                              })
                            }
                            setHoveredFinancialPoint({
                              month: item.month,
                              grossRevenue: item.grossRevenue,
                              totalServiceValue: item.totalServiceValue,
                              index
                            })
                          }}
                        />
                        {/* Visible point indicators when hovered */}
                        {hoveredFinancialPoint && hoveredFinancialPoint.index === index && (
                          <>
                            <circle
                              cx={x}
                              cy={grossRevenueY}
                              r="4"
                              fill="#14b8a6"
                              stroke="white"
                              strokeWidth="2"
                            />
                            <circle
                              cx={x}
                              cy={serviceValueY}
                              r="4"
                              fill="#1e40af"
                              stroke="white"
                              strokeWidth="2"
                            />
                            <line
                              x1={x}
                              y1="0"
                              x2={x}
                              y2="200"
                              stroke="#94a3b8"
                              strokeWidth="1"
                              strokeDasharray="4,4"
                            />
                          </>
                        )}
                      </g>
                    )
                  })}
                </svg>
                {/* Tooltip */}
                {hoveredFinancialPoint && (
                  <div
                    className="chart-tooltip"
                    style={{
                      left: `${tooltipPosition.x}px`,
                      top: `${tooltipPosition.y - 10}px`,
                      transform: 'translate(-50%, -100%)'
                    }}
                  >
                    <div className="tooltip-title">{hoveredFinancialPoint.month}</div>
                    <div className="tooltip-item">
                      <span className="tooltip-label">Gross Revenue:</span>
                      <span className="tooltip-value">{formatCurrency(hoveredFinancialPoint.grossRevenue)}</span>
                    </div>
                    <div className="tooltip-item">
                      <span className="tooltip-label">Service Value:</span>
                      <span className="tooltip-value">{formatCurrency(hoveredFinancialPoint.totalServiceValue)}</span>
                    </div>
                  </div>
                )}
                <div className="chart-x-axis">
                  {financialTrendsData.map((item, index) => (
                    <div key={index} className="x-axis-label">
                      {item.month}
                    </div>
                  ))}
                </div>
              </div>
            </div>
            <div className="chart-legend">
              <div className="legend-item">
                <span className="legend-color gross-revenue"></span>
                <span>→ Gross Revenue (Collected)</span>
              </div>
              <div className="legend-item">
                <span className="legend-color total-service"></span>
                <span>→ Total Service Value</span>
              </div>
            </div>
          </div>

          {/* Client Growth Engine Chart */}
          <div className="chart-card">
            <h3 className="chart-title">Client Growth Engine (Healthy Growth)</h3>
            <p className="chart-subtitle">
              Analyzing new client acquisition vs. returning client loyalty.
            </p>
            <div className="chart-container">
              <div className="chart-y-axis">
                <div className="y-axis-label">600</div>
                <div className="y-axis-label">450</div>
                <div className="y-axis-label">300</div>
                <div className="y-axis-label">150</div>
                <div className="y-axis-label">0</div>
              </div>
              <div className="chart-bars-container">
                {clientGrowthData.map((item, index) => {
                  const total = item.newClients + item.returningVisits
                  const newClientsHeight =
                    (item.newClients / maxClientValue) * 100
                  const returningHeight =
                    (item.returningVisits / maxClientValue) * 100

                  return (
                    <div 
                      key={index} 
                      className="chart-category"
                      onMouseEnter={(e) => {
                        const rect = e.currentTarget.getBoundingClientRect()
                        setTooltipPosition({
                          x: rect.left + rect.width / 2,
                          y: rect.top
                        })
                        setHoveredClientPoint({
                          month: item.month,
                          newClients: item.newClients,
                          returningVisits: item.returningVisits,
                          total: total,
                          index
                        })
                      }}
                      onMouseLeave={() => setHoveredClientPoint(null)}
                    >
                      <div className="bars-wrapper">
                        <div
                          className="bar returning-clients-bar"
                          style={{ height: `${returningHeight}%` }}
                        >
                          <span className="bar-value">{item.returningVisits}</span>
                        </div>
                        <div
                          className="bar new-clients-bar"
                          style={{ height: `${newClientsHeight}%` }}
                        >
                          <span className="bar-value">{item.newClients}</span>
                        </div>
                      </div>
                      <div className="category-label">{item.month}</div>
                    </div>
                  )
                })}
              </div>
              {/* Tooltip for Client Growth Chart */}
              {hoveredClientPoint && (
                <div
                  className="chart-tooltip"
                  style={{
                    left: `${tooltipPosition.x}px`,
                    top: `${tooltipPosition.y - 10}px`,
                    transform: 'translate(-50%, -100%)'
                  }}
                >
                  <div className="tooltip-title">{hoveredClientPoint.month}</div>
                  <div className="tooltip-item">
                    <span className="tooltip-label">New Clients:</span>
                    <span className="tooltip-value">{hoveredClientPoint.newClients}</span>
                  </div>
                  <div className="tooltip-item">
                    <span className="tooltip-label">Returning Visits:</span>
                    <span className="tooltip-value">{hoveredClientPoint.returningVisits}</span>
                  </div>
                  <div className="tooltip-item">
                    <span className="tooltip-label">Total:</span>
                    <span className="tooltip-value">{hoveredClientPoint.total}</span>
                  </div>
                </div>
              )}
            </div>
            <div className="chart-legend">
              <div className="legend-item">
                <span className="legend-color new-clients"></span>
                <span>■ New Clients Acquired</span>
              </div>
              <div className="legend-item">
                <span className="legend-color returning-clients"></span>
                <span>■ Returning Client Visits</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default BusinessGrowthTrendAnalysis

