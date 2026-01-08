import React, { useState, useEffect } from 'react'
import {
  FaChartBar,
  FaBox,
  FaShoppingBag,
  FaArrowLeft,
  FaSpinner,
} from 'react-icons/fa'
import './ServiceProductPerformance.css'
import { API_BASE_URL } from '../config'
import { apiGet } from '../utils/api'
import { useAuth } from '../contexts/AuthContext'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts'

const ServiceProductPerformance = ({ setActivePage }) => {
  const { currentBranch } = useAuth()
  const [dateRange, setDateRange] = useState('Last 12 Months')
  const [categoryFilter, setCategoryFilter] = useState('all')
  const [typeFilter, setTypeFilter] = useState('all')
  const [loading, setLoading] = useState(true)
  const [summaryMetrics, setSummaryMetrics] = useState({
    totalServiceRevenue: 0,
    totalProductRevenue: 0,
    totalUnitsSold: 0,
    avgRevenuePerService: 0,
    avgRevenuePerProduct: 0,
  })
  const [serviceData, setServiceData] = useState([])
  const [productData, setProductData] = useState([])
  const [categoryData, setCategoryData] = useState({ services: [], products: [] })
  const [availableCategories, setAvailableCategories] = useState([])

  useEffect(() => {
    fetchPerformanceData()
  }, [dateRange, categoryFilter, typeFilter, currentBranch])

  // Listen for branch changes
  useEffect(() => {
    const handleBranchChange = () => {
      console.log('[ServiceProductPerformance] Branch changed, refreshing data...')
      fetchPerformanceData()
    }
    
    window.addEventListener('branchChanged', handleBranchChange)
    return () => window.removeEventListener('branchChanged', handleBranchChange)
  }, [currentBranch])

  const fetchPerformanceData = async () => {
    try {
      setLoading(true)
      const dateParams = getDateRangeParams(dateRange)
      
      const params = new URLSearchParams({
        start: dateParams.start_date,
        end: dateParams.end_date,
        category: categoryFilter,
        type: typeFilter
      })
      
      const response = await apiGet(`/api/analytics/service-product-performance?${params}`)
      
      if (response.ok) {
        const data = await response.json()
        
        // Update summary metrics
        setSummaryMetrics(data.summary || {
          totalServiceRevenue: 0,
          totalProductRevenue: 0,
          totalUnitsSold: 0,
          avgRevenuePerService: 0,
          avgRevenuePerProduct: 0,
        })
        
        // Update service and product data
        setServiceData(data.services || [])
        setProductData(data.products || [])
        setCategoryData(data.categories || { services: [], products: [] })
        
        // Extract available categories for filter dropdown
        const categories = new Set()
        data.categories?.services?.forEach(cat => categories.add(cat.category))
        data.categories?.products?.forEach(cat => categories.add(cat.category))
        setAvailableCategories(Array.from(categories).sort())
      } else {
        console.error('Failed to fetch performance data:', response.statusText)
      }
    } catch (error) {
      console.error('Error fetching performance data:', error)
    } finally {
      setLoading(false)
    }
  }

  const getDateRangeParams = (range) => {
    const end = new Date()
    let start = new Date()
    
    switch (range) {
      case 'Last 7 Days':
        start.setDate(start.getDate() - 7)
        break
      case 'Last 30 Days':
        start.setDate(start.getDate() - 30)
        break
      case 'Last 3 Months':
        start.setMonth(start.getMonth() - 3)
        break
      case 'Last 12 Months':
        start.setMonth(start.getMonth() - 12)
        break
      default:
        start.setMonth(start.getMonth() - 12)
    }
    
    return {
      start_date: start.toISOString().split('T')[0],
      end_date: end.toISOString().split('T')[0],
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

  const getColorForIndex = (index) => {
    const colors = [
      '#ef4444', '#8b5cf6', '#10b981', '#f59e0b', '#3b82f6',
      '#6366f1', '#ec4899', '#14b8a6', '#f97316', '#9ca3af',
      '#f43f5e', '#a855f7', '#22c55e', '#eab308', '#0ea5e9'
    ]
    return colors[index % colors.length]
  }

  // Prepare chart data
  const topServicesChart = serviceData.slice(0, 10).map((service, index) => ({
    name: service.name.length > 20 ? service.name.substring(0, 20) + '...' : service.name,
    revenue: service.totalRevenue,
    color: getColorForIndex(index)
  }))

  const topProductsChart = productData.slice(0, 10).map((product, index) => ({
    name: product.name.length > 20 ? product.name.substring(0, 20) + '...' : product.name,
    revenue: product.totalRevenue,
    color: getColorForIndex(index)
  }))

  const categoryChartData = [
    ...categoryData.services.map(cat => ({ ...cat, type: 'Service' })),
    ...categoryData.products.map(cat => ({ ...cat, type: 'Product' }))
  ].sort((a, b) => b.revenue - a.revenue).slice(0, 10)

  // Filter data based on type filter
  const displayServiceData = typeFilter === 'products' ? [] : serviceData
  const displayProductData = typeFilter === 'services' ? [] : productData

  return (
    <div className="service-product-performance-page">
      <div className="service-product-performance-container">
        <div className="service-product-performance-content">
          {/* Back Button and Filters */}
          <div className="controls-section">
            <button className="back-button" onClick={handleBackToReports}>
              <FaArrowLeft /> Back to Reports Hub
            </button>
            <div className="filters-group">
              <div className="date-range-section">
                <label className="date-range-label">DATE RANGE</label>
                <select
                  className="date-range-select"
                  value={dateRange}
                  onChange={(e) => setDateRange(e.target.value)}
                >
                  <option>Last 7 Days</option>
                  <option>Last 30 Days</option>
                  <option>Last 3 Months</option>
                  <option>Last 12 Months</option>
                </select>
              </div>
              <div className="category-filter-section">
                <label className="date-range-label">CATEGORY</label>
                <select
                  className="date-range-select"
                  value={categoryFilter}
                  onChange={(e) => setCategoryFilter(e.target.value)}
                >
                  <option value="all">All Categories</option>
                  {availableCategories.map(cat => (
                    <option key={cat} value={cat}>{cat}</option>
                  ))}
                </select>
              </div>
              <div className="type-filter-section">
                <label className="date-range-label">TYPE</label>
                <select
                  className="date-range-select"
                  value={typeFilter}
                  onChange={(e) => setTypeFilter(e.target.value)}
                >
                  <option value="all">All</option>
                  <option value="services">Services Only</option>
                  <option value="products">Products Only</option>
                </select>
              </div>
            </div>
          </div>

          {/* Loading State */}
          {loading ? (
            <div className="loading-container">
              <FaSpinner className="loading-spinner" />
              <p>Loading performance data...</p>
            </div>
          ) : (
            <>
              {/* Summary Metrics Cards */}
              <div className="summary-metrics-grid">
                <div className="metric-card blue">
                  <div className="metric-icon">
                    <FaChartBar />
                  </div>
                  <div className="metric-info">
                    <h2 className="metric-value">{formatCurrency(summaryMetrics.totalServiceRevenue)}</h2>
                    <p className="metric-label">TOTAL SERVICE REVENUE</p>
                  </div>
                </div>

                <div className="metric-card green">
                  <div className="metric-icon">
                    <FaShoppingBag />
                  </div>
                  <div className="metric-info">
                    <h2 className="metric-value">{formatCurrency(summaryMetrics.totalProductRevenue)}</h2>
                    <p className="metric-label">TOTAL PRODUCT REVENUE</p>
                  </div>
                </div>

                <div className="metric-card orange">
                  <div className="metric-icon">
                    <FaBox />
                  </div>
                  <div className="metric-info">
                    <h2 className="metric-value">{formatNumber(summaryMetrics.totalUnitsSold)}</h2>
                    <p className="metric-label">TOTAL UNITS SOLD</p>
                  </div>
                </div>

                <div className="metric-card purple">
                  <div className="metric-icon">
                    <FaChartBar />
                  </div>
                  <div className="metric-info">
                    <h2 className="metric-value">{formatCurrency(summaryMetrics.avgRevenuePerService)}</h2>
                    <p className="metric-label">AVG. REVENUE PER SERVICE</p>
                  </div>
                </div>

                <div className="metric-card red">
                  <div className="metric-icon">
                    <FaShoppingBag />
                  </div>
                  <div className="metric-info">
                    <h2 className="metric-value">{formatCurrency(summaryMetrics.avgRevenuePerProduct)}</h2>
                    <p className="metric-label">AVG. REVENUE PER PRODUCT</p>
                  </div>
                </div>
              </div>

              {/* Charts Section */}
              <div className="charts-section">
                {/* Top Services Chart */}
                {typeFilter !== 'products' && topServicesChart.length > 0 && (
                  <div className="chart-card">
                    <h3 className="chart-title">Top 10 Services by Revenue</h3>
                    <ResponsiveContainer width="100%" height={400}>
                      <BarChart
                        data={topServicesChart}
                        layout="vertical"
                        margin={{ top: 20, right: 30, left: 100, bottom: 5 }}
                      >
                        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                        <XAxis type="number" tick={{ fontSize: 12, fill: '#6b7280' }} stroke="#9ca3af" />
                        <YAxis
                          dataKey="name"
                          type="category"
                          tick={{ fontSize: 11, fill: '#6b7280' }}
                          stroke="#9ca3af"
                          width={90}
                        />
                        <Tooltip
                          contentStyle={{
                            backgroundColor: 'white',
                            border: '1px solid #e5e7eb',
                            borderRadius: '8px',
                            padding: '12px',
                            boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)'
                          }}
                          formatter={(value) => formatCurrency(value)}
                        />
                        <Bar dataKey="revenue" radius={[0, 4, 4, 0]}>
                          {topServicesChart.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.color} />
                          ))}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                )}

                {/* Top Products Chart */}
                {typeFilter !== 'services' && topProductsChart.length > 0 && (
                  <div className="chart-card">
                    <h3 className="chart-title">Top 10 Products by Revenue</h3>
                    <ResponsiveContainer width="100%" height={400}>
                      <BarChart
                        data={topProductsChart}
                        margin={{ top: 20, right: 30, left: 20, bottom: 60 }}
                      >
                        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                        <XAxis
                          dataKey="name"
                          angle={-45}
                          textAnchor="end"
                          height={100}
                          tick={{ fontSize: 11, fill: '#6b7280' }}
                          stroke="#9ca3af"
                        />
                        <YAxis tick={{ fontSize: 12, fill: '#6b7280' }} stroke="#9ca3af" />
                        <Tooltip
                          contentStyle={{
                            backgroundColor: 'white',
                            border: '1px solid #e5e7eb',
                            borderRadius: '8px',
                            padding: '12px',
                            boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)'
                          }}
                          formatter={(value) => formatCurrency(value)}
                        />
                        <Bar dataKey="revenue" radius={[4, 4, 0, 0]}>
                          {topProductsChart.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.color} />
                          ))}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                )}

                {/* Category Performance Donut Chart */}
                {categoryChartData.length > 0 && (
                  <div className="chart-card">
                    <h3 className="chart-title">Revenue by Category</h3>
                    <ResponsiveContainer width="100%" height={400}>
                      <PieChart>
                        <Pie
                          data={categoryChartData}
                          cx="50%"
                          cy="50%"
                          labelLine={false}
                          label={({ category, percentage }) => `${category}: ${percentage}%`}
                          outerRadius={120}
                          fill="#8884d8"
                          dataKey="revenue"
                        >
                          {categoryChartData.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={getColorForIndex(index)} />
                          ))}
                        </Pie>
                        <Tooltip
                          contentStyle={{
                            backgroundColor: 'white',
                            border: '1px solid #e5e7eb',
                            borderRadius: '8px',
                            padding: '12px',
                            boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)'
                          }}
                          formatter={(value) => formatCurrency(value)}
                        />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                )}
              </div>

              {/* Service Performance Table */}
              {typeFilter !== 'products' && displayServiceData.length > 0 && (
                <div className="table-section">
                  <h3 className="section-title">Service Performance</h3>
                  <div className="table-container">
                    <table className="performance-table">
                      <thead>
                        <tr>
                          <th>Service Name</th>
                          <th>Category</th>
                          <th>Total Bookings</th>
                          <th>Total Revenue</th>
                          <th>Avg. Price</th>
                          <th>Contribution %</th>
                        </tr>
                      </thead>
                      <tbody>
                        {displayServiceData.map((service, index) => (
                          <tr key={service.id || index}>
                            <td className="service-name">{service.name}</td>
                            <td>{service.category || 'Uncategorized'}</td>
                            <td>{formatNumber(service.totalBookings)}</td>
                            <td className="revenue-cell">{formatCurrency(service.totalRevenue)}</td>
                            <td>{formatCurrency(service.avgPrice)}</td>
                            <td className="contribution-cell">{service.contribution}%</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Product Performance Table */}
              {typeFilter !== 'services' && displayProductData.length > 0 && (
                <div className="table-section">
                  <h3 className="section-title">Product Performance</h3>
                  <div className="table-container">
                    <table className="performance-table">
                      <thead>
                        <tr>
                          <th>Product Name</th>
                          <th>Category</th>
                          <th>Units Sold</th>
                          <th>Total Revenue</th>
                          <th>Stock Quantity</th>
                        </tr>
                      </thead>
                      <tbody>
                        {displayProductData.map((product, index) => (
                          <tr key={product.id || index}>
                            <td className="product-name">{product.name}</td>
                            <td>{product.category || 'Uncategorized'}</td>
                            <td>{formatNumber(product.unitsSold)}</td>
                            <td className="revenue-cell">{formatCurrency(product.totalRevenue)}</td>
                            <td className={product.stockQuantity < 10 ? 'low-stock' : ''}>
                              {formatNumber(product.stockQuantity)}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Empty State */}
              {!loading && displayServiceData.length === 0 && displayProductData.length === 0 && (
                <div className="empty-state">
                  <p>No data available for the selected filters.</p>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  )
}

export default ServiceProductPerformance

