import React, { useState, useEffect } from 'react'
import {
  FaBars,
  FaBell,
  FaUser,
  FaArrowLeft,
  FaCloudDownloadAlt,
} from 'react-icons/fa'
import './SalesByServiceGroup.css'
import { API_BASE_URL } from '../config'
import { apiGet } from '../utils/api'

const SalesByServiceGroup = ({ setActivePage }) => {
  const [dateFilter, setDateFilter] = useState('today')
  const [salesData, setSalesData] = useState([])
  const [loading, setLoading] = useState(true)

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

    switch (dateFilter) {
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
  }, [dateFilter])

  const fetchSalesData = async () => {
    try {
      setLoading(true)
      const dateRange = getDateRange()
      const params = new URLSearchParams(dateRange)
      
      const response = await apiGet(`/api/reports/sales-by-service-group?${params}`)
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const data = await response.json()
      
      // Map backend response to frontend format
      const enrichedData = (data || []).map(item => ({
        service_group: item.group_name || item.service_group || 'N/A',
        count: item.count || 0,
        net_amount: (item.revenue || 0) / 1.18, // Assuming 18% tax
        tax_amount: (item.revenue || 0) - ((item.revenue || 0) / 1.18),
        total_amount: item.revenue || 0,
        percentage: item.percentage || '0.00'
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
      ['Service Group', 'Count', 'Net Amount', 'Tax Amount', 'Total Amount', 'Percentage'],
      ...salesData.map(item => [
        item.service_group || 'N/A',
        item.count || 0,
        item.net_amount?.toFixed(2) || '0.00',
        item.tax_amount?.toFixed(2) || '0.00',
        item.total_amount?.toFixed(2) || '0.00',
        `${item.percentage}%`,
      ])
    ].map(row => row.join(',')).join('\n')
    
    const blob = new Blob([csvContent], { type: 'text/csv' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `sales-by-service-group-${new Date().toISOString().split('T')[0]}.csv`
    a.click()
    window.URL.revokeObjectURL(url)
  }

  return (
    <div className="sales-by-service-group-page">
      {/* Header */}
      <header className="sales-by-service-group-header">
        <div className="header-left">
          <button className="menu-icon">
            <FaBars />
          </button>
          <h1 className="header-title">Sales by Service Group</h1>
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

      <div className="sales-by-service-group-container">
        {/* Main Report Card */}
        <div className="report-card">
          {/* Control Panel */}
          <div className="control-panel">
            <button className="back-button" onClick={handleBackToReports}>
              <FaArrowLeft />
              Back to Reports Hub
            </button>

            <div className="filters-actions">
              <div className="filter-group">
                <select
                  className="date-filter-dropdown"
                  value={dateFilter}
                  onChange={(e) => setDateFilter(e.target.value)}
                >
                  <option value="today">Today</option>
                  <option value="yesterday">Yesterday</option>
                  <option value="week">This Week</option>
                  <option value="month">This Month</option>
                  <option value="year">This Year</option>
                  <option value="custom">Custom Range</option>
                </select>
              </div>

              <button className="download-report-btn" onClick={handleDownload}>
                <FaCloudDownloadAlt />
                Download Report
              </button>
            </div>
          </div>

          {/* Report Table */}
          <div className="table-container">
            <table className="service-group-table">
              <thead>
                <tr>
                  <th>Service Group</th>
                  <th>Count</th>
                  <th>Net Amount</th>
                  <th>Tax Amount</th>
                  <th>Total Amount</th>
                  <th>Percentage</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan="6" className="empty-message">Loading...</td>
                  </tr>
                ) : salesData.length === 0 ? (
                  <tr>
                    <td colSpan="6" className="empty-message">
                      No sales data found for this selection.
                    </td>
                  </tr>
                ) : (
                  salesData.map((item, index) => (
                    <tr key={index}>
                      <td>{item.service_group || 'N/A'}</td>
                      <td>{item.count || 0}</td>
                      <td>₹{item.net_amount?.toFixed(2) || '0.00'}</td>
                      <td>₹{item.tax_amount?.toFixed(2) || '0.00'}</td>
                      <td>₹{item.total_amount?.toFixed(2) || '0.00'}</td>
                      <td>{item.percentage}%</td>
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

export default SalesByServiceGroup

