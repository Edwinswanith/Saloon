import React, { useState, useEffect } from 'react'
import {
  FaBars,
  FaBell,
  FaUser,
  FaArrowLeft,
  FaCloudDownloadAlt,
  FaList,
} from 'react-icons/fa'
import './StaffIncentiveReport.css'
import { API_BASE_URL } from '../config'
import { apiGet } from '../utils/api'

const StaffIncentiveReport = ({ setActivePage }) => {
  const [dateFilter, setDateFilter] = useState('last-30-days')
  const [staffPerformance, setStaffPerformance] = useState([])
  const [loading, setLoading] = useState(true)

  const handleBackToReports = () => {
    if (setActivePage) {
      setActivePage('reports')
    }
  }

  const getDateRange = () => {
    const today = new Date()
    const last7Days = new Date(today)
    last7Days.setDate(today.getDate() - 7)
    const last30Days = new Date(today)
    last30Days.setDate(today.getDate() - 30)
    const last90Days = new Date(today)
    last90Days.setDate(today.getDate() - 90)
    const monthStart = new Date(today.getFullYear(), today.getMonth(), 1)
    const lastMonthStart = new Date(today.getFullYear(), today.getMonth() - 1, 1)
    const lastMonthEnd = new Date(today.getFullYear(), today.getMonth(), 0)

    switch (dateFilter) {
      case 'last-7-days':
        return {
          start_date: last7Days.toISOString().split('T')[0],
          end_date: today.toISOString().split('T')[0],
        }
      case 'last-30-days':
        return {
          start_date: last30Days.toISOString().split('T')[0],
          end_date: today.toISOString().split('T')[0],
        }
      case 'last-90-days':
        return {
          start_date: last90Days.toISOString().split('T')[0],
          end_date: today.toISOString().split('T')[0],
        }
      case 'this-month':
        return {
          start_date: monthStart.toISOString().split('T')[0],
          end_date: today.toISOString().split('T')[0],
        }
      case 'last-month':
        return {
          start_date: lastMonthStart.toISOString().split('T')[0],
          end_date: lastMonthEnd.toISOString().split('T')[0],
        }
      default:
        return {
          start_date: last30Days.toISOString().split('T')[0],
          end_date: today.toISOString().split('T')[0],
        }
    }
  }

  useEffect(() => {
    fetchStaffPerformance()
  }, [dateFilter])

  const fetchStaffPerformance = async () => {
    try {
      setLoading(true)
      const dateRange = getDateRange()
      const params = new URLSearchParams(dateRange)
      
      const response = await apiGet(`/api/reports/staff-incentive?${params}`)
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const data = await response.json()
      
      // Map backend response to frontend format
      const mappedData = (data || []).map((staff, index) => ({
        id: index + 1,
        staffName: staff.staff_name || 'N/A',
        itemCount: staff.item_count || 0,
        service: staff.service || 0,
        package: staff.package || 0,
        product: staff.product || 0,
        prepaid: staff.prepaid || 0,
        membership: staff.membership || 0,
        total: staff.total || staff.total_revenue || 0,
        avgBill: staff.avg_bill || 0,
      }))
      
      setStaffPerformance(mappedData)
    } catch (error) {
      console.error('Error fetching staff performance:', error)
      setStaffPerformance([])
    } finally {
      setLoading(false)
    }
  }

  const handleDownload = () => {
    const csvContent = [
      ['#', 'Staff Name', 'Item Count', 'Service', 'Package', 'Product', 'Prepaid', 'Membership', 'Total', 'Avg. Bill'],
      ...staffPerformance.map((staff, index) => [
        index + 1,
        staff.staffName,
        staff.itemCount,
        staff.service.toFixed(2),
        staff.package.toFixed(2),
        staff.product.toFixed(2),
        staff.prepaid.toFixed(2),
        staff.membership.toFixed(2),
        staff.total.toFixed(2),
        staff.avgBill.toFixed(2),
      ])
    ].map(row => row.join(',')).join('\n')
    
    const blob = new Blob([csvContent], { type: 'text/csv' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `staff-incentive-report-${new Date().toISOString().split('T')[0]}.csv`
    a.click()
    window.URL.revokeObjectURL(url)
  }

  return (
    <div className="staff-incentive-report-page">
      {/* Header */}
      <header className="staff-incentive-report-header">
        <div className="header-left">
          <button className="menu-icon">
            <FaBars />
          </button>
          <h1 className="header-title">Staff Incentive Report</h1>
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

      <div className="staff-incentive-report-container">
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
                  <option value="last-30-days">Last 30 days</option>
                  <option value="last-7-days">Last 7 days</option>
                  <option value="last-90-days">Last 90 days</option>
                  <option value="this-month">This Month</option>
                  <option value="last-month">Last Month</option>
                  <option value="custom">Custom Range</option>
                </select>
              </div>

              <button className="download-report-btn" onClick={handleDownload}>
                <FaCloudDownloadAlt />
                Download Report
              </button>
            </div>
          </div>

          {/* Employee Performance Table */}
          <div className="table-section">
            <h2 className="table-title">Employee Performance</h2>
            <div className="table-container">
              <table className="performance-table">
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
                      <td colSpan="11" className="empty-message">Loading...</td>
                    </tr>
                  ) : staffPerformance.length === 0 ? (
                    <tr>
                      <td colSpan="11" className="empty-message">
                        No staff performance data found for this selection.
                      </td>
                    </tr>
                  ) : (
                    staffPerformance.map((staff, index) => (
                      <tr key={staff.id}>
                        <td>{index + 1}</td>
                        <td className="staff-name">{staff.staffName}</td>
                        <td>{staff.itemCount}</td>
                        <td>{staff.service.toFixed(2)}</td>
                        <td>{staff.package.toFixed(2)}</td>
                        <td>{staff.product.toFixed(2)}</td>
                        <td>{staff.prepaid.toFixed(2)}</td>
                        <td>{staff.membership.toFixed(2)}</td>
                        <td className="total-cell">₹ {staff.total.toFixed(2)}</td>
                        <td className="avg-bill-cell">
                          ₹ {staff.avgBill.toFixed(2)}
                        </td>
                        <td>
                          <button 
                            className="info-btn" 
                            title="View Details"
                            onClick={() => alert(`Staff Performance Details:\n\nStaff: ${staff.staffName}\nItem Count: ${staff.itemCount}\nService: ₹${staff.service.toFixed(2)}\nPackage: ₹${staff.package.toFixed(2)}\nProduct: ₹${staff.product.toFixed(2)}\nPrepaid: ₹${staff.prepaid.toFixed(2)}\nMembership: ₹${staff.membership.toFixed(2)}\nTotal: ₹${staff.total.toFixed(2)}\nAvg. Bill: ₹${staff.avgBill.toFixed(2)}`)}
                          >
                            <FaList />
                          </button>
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
    </div>
  )
}

export default StaffIncentiveReport

