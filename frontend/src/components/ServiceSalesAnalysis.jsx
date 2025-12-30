import React, { useState, useEffect } from 'react'
import {
  FaBars,
  FaBell,
  FaUser,
  FaArrowLeft,
  FaCloudDownloadAlt,
  FaChevronDown,
} from 'react-icons/fa'
import './ServiceSalesAnalysis.css'
import { API_BASE_URL } from '../config'
import { apiGet } from '../utils/api'

const ServiceSalesAnalysis = ({ setActivePage }) => {
  const [categoryFilter, setCategoryFilter] = useState('all')
  const [dateRangeFilter, setDateRangeFilter] = useState('today')
  const [salesData, setSalesData] = useState([])
  const [loading, setLoading] = useState(true)
  const [serviceGroups, setServiceGroups] = useState([])

  const handleBackToReports = () => {
    if (setActivePage) {
      setActivePage('reports')
    }
  }

  const getDateRange = () => {
    const today = new Date()
    const yesterday = new Date(today)
    yesterday.setDate(yesterday.getDate() - 1)
    const weekStart = new Date(today)
    weekStart.setDate(today.getDate() - today.getDay())
    const monthStart = new Date(today.getFullYear(), today.getMonth(), 1)
    const yearStart = new Date(today.getFullYear(), 0, 1)

    switch (dateRangeFilter) {
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
          end_date: today.toISOString().split('T')[0],
        }
    }
  }

  useEffect(() => {
    fetchSalesData()
    fetchServiceGroups()
  }, [dateRangeFilter, categoryFilter])

  const fetchServiceGroups = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/services/groups`)
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      const data = await response.json()
      // Backend returns {groups: [...]}, so extract the groups array
      setServiceGroups(Array.isArray(data) ? data : (data.groups || []))
    } catch (error) {
      console.error('Error fetching service groups:', error)
      setServiceGroups([]) // Set to empty array on error
    }
  }

  const fetchSalesData = async () => {
    try {
      setLoading(true)
      const dateRange = getDateRange()
      const params = new URLSearchParams(dateRange)
      
      const response = await apiGet(`/api/reports/service-sales-analysis?${params}`)
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const data = await response.json()
      
      let filteredData = data || []
      
      // Filter by category if not 'all'
      if (categoryFilter !== 'all') {
        filteredData = filteredData.filter(item => 
          item.service_group && item.service_group.toLowerCase().includes(categoryFilter.toLowerCase())
        )
      }
      
      // Calculate totals for contribution percentage
      const totalRevenue = filteredData.reduce((sum, item) => sum + (item.revenue || 0), 0)
      
      // Add calculated fields
      const enrichedData = filteredData.map(item => ({
        ...item,
        netAmount: item.revenue || 0,
        tax: (item.revenue || 0) * 0.18, // Assuming 18% tax
        totalRevenue: (item.revenue || 0) * 1.18,
        contribution: totalRevenue > 0 ? ((item.revenue || 0) / totalRevenue * 100).toFixed(2) : '0.00'
      }))
      
      setSalesData(enrichedData)
    } catch (error) {
      console.error('Error fetching sales data:', error)
      setSalesData([])
    } finally {
      setLoading(false)
    }
  }

  const handleDownload = () => {
    const csvContent = [
      ['Item Name', 'Category', 'Qty Sold', 'Net Amount', 'Tax', 'Total Revenue', 'Contribution %'],
      ...salesData.map(item => [
        item.service_name || 'N/A',
        item.service_group || 'N/A',
        item.count || 0,
        item.netAmount?.toFixed(2) || '0.00',
        item.tax?.toFixed(2) || '0.00',
        item.totalRevenue?.toFixed(2) || '0.00',
        `${item.contribution}%`,
      ])
    ].map(row => row.join(',')).join('\n')
    
    const blob = new Blob([csvContent], { type: 'text/csv' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `service-sales-analysis-${new Date().toISOString().split('T')[0]}.csv`
    a.click()
    window.URL.revokeObjectURL(url)
  }

  return (
    <div className="service-sales-analysis-page">
      {/* Header */}
      <header className="service-sales-header">
        <div className="header-left">
          <button className="menu-icon">
            <FaBars />
          </button>
          <h1 className="header-title">Service Sales Analysis</h1>
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

      <div className="service-sales-container">
        {/* Main Report Card */}
        <div className="report-card">
          {/* Back Button */}
          <button className="back-button" onClick={handleBackToReports}>
            <FaArrowLeft />
            Back to Reports Hub
          </button>

          {/* Report Title */}
          <h2 className="report-title">Sales Analysis Report</h2>

          {/* Filters Section */}
          <div className="filters-section">
            <div className="filter-group">
              <label className="filter-label">Category</label>
              <div className="dropdown-wrapper">
                <select
                  className="filter-dropdown"
                  value={categoryFilter}
                  onChange={(e) => setCategoryFilter(e.target.value)}
                >
                  <option value="all">All Categories</option>
                  {Array.isArray(serviceGroups) && serviceGroups.map(group => (
                    <option key={group.id || group.name} value={group.name}>{group.name}</option>
                  ))}
                </select>
                <span className="dropdown-arrow"><FaChevronDown /></span>
              </div>
            </div>

            <div className="filter-group">
              <label className="filter-label">Date Range</label>
              <div className="dropdown-wrapper">
                <select
                  className="filter-dropdown"
                  value={dateRangeFilter}
                  onChange={(e) => setDateRangeFilter(e.target.value)}
                >
                  <option value="today">Today</option>
                  <option value="yesterday">Yesterday</option>
                  <option value="week">This Week</option>
                  <option value="month">This Month</option>
                  <option value="year">This Year</option>
                  <option value="custom">Custom Range</option>
                </select>
                <span className="dropdown-arrow"><FaChevronDown /></span>
              </div>
            </div>

            <button className="download-report-btn" onClick={handleDownload}>
              <FaCloudDownloadAlt />
              Download Report
            </button>
          </div>

          {/* Report Table */}
          <div className="table-container">
            <table className="sales-table">
              <thead>
                <tr>
                  <th>Item Name</th>
                  <th>Category</th>
                  <th>Qty Sold</th>
                  <th>Net Amount</th>
                  <th>Tax</th>
                  <th>Total Revenue</th>
                  <th>Contribution</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan="7" className="empty-message">Loading...</td>
                  </tr>
                ) : salesData.length === 0 ? (
                  <tr>
                    <td colSpan="7" className="empty-message">
                      No sales found for this selection.
                    </td>
                  </tr>
                ) : (
                  salesData.map((item, index) => (
                    <tr key={index}>
                      <td>{item.service_name || 'N/A'}</td>
                      <td>{item.service_group || 'N/A'}</td>
                      <td>{item.count || 0}</td>
                      <td>₹{item.netAmount?.toFixed(2) || '0.00'}</td>
                      <td>₹{item.tax?.toFixed(2) || '0.00'}</td>
                      <td>₹{item.totalRevenue?.toFixed(2) || '0.00'}</td>
                      <td>{item.contribution}%</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ServiceSalesAnalysis

