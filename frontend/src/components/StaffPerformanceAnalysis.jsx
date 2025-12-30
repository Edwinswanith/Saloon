import React, { useState, useEffect } from 'react'
import {
  FaBars,
  FaUser,
  FaStar,
  FaShoppingBag,
  FaBox,
  FaUserFriends,
  FaArrowLeft,
  FaDownload,
  FaSync,
  FaCheckCircle,
} from 'react-icons/fa'
import * as XLSX from 'xlsx'
import './StaffPerformanceAnalysis.css'
import { API_BASE_URL } from '../config'
import { apiGet } from '../utils/api'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'

const StaffPerformanceAnalysis = ({ setActivePage }) => {
  const [dateRange, setDateRange] = useState('Last 30 Days')
  const [loading, setLoading] = useState(false)
  const [performanceData, setPerformanceData] = useState({
    topPerformerRevenue: {
      name: 'N/A',
      value: '₹0.00',
      label: 'TOP PERFORMER (REVENUE)',
    },
    topServiceSeller: {
      name: 'N/A',
      value: '0 items',
      label: 'TOP SERVICE SELLER',
    },
    topRetailSeller: {
      name: 'N/A',
      value: '0 items',
      label: 'TOP RETAIL SELLER',
    },
    busiestStaff: {
      name: 'N/A',
      value: '0 items',
      label: 'BUSIEST STAFF (ITEMS)',
    },
  })
  const [revenueBreakdownData, setRevenueBreakdownData] = useState([])
  const [staffLeaderboardData, setStaffLeaderboardData] = useState([])

  


  const handleBackToReports = () => {
    if (setActivePage) {
      setActivePage('reports')
    }
  }

  const getDateRangeForAPI = () => {
    const today = new Date()
    let startDate, endDate

    switch (dateRange) {
      case 'Last 7 Days':
        startDate = new Date(today)
        startDate.setDate(today.getDate() - 7)
        endDate = new Date(today)
        break
      case 'Last 30 Days':
        startDate = new Date(today)
        startDate.setDate(today.getDate() - 30)
        endDate = new Date(today)
        break
      case 'Last 3 Months':
        startDate = new Date(today)
        startDate.setMonth(today.getMonth() - 3)
        endDate = new Date(today)
        break
      case 'Last 6 Months':
        startDate = new Date(today)
        startDate.setMonth(today.getMonth() - 6)
        endDate = new Date(today)
        break
      case 'Last Year':
        startDate = new Date(today.getFullYear() - 1, 0, 1)
        endDate = new Date(today)
        break
      default:
        startDate = new Date(today)
        startDate.setDate(today.getDate() - 30)
        endDate = new Date(today)
    }

    // Set time to start of day for start_date and end of day for end_date
    startDate.setHours(0, 0, 0, 0)
    endDate.setHours(23, 59, 59, 999)

    return {
      start_date: startDate.toISOString().split('T')[0],
      end_date: endDate.toISOString().split('T')[0]
    }
  }

  const fetchStaffPerformanceData = async () => {
    try {
      setLoading(true)
      const dateRangeParams = getDateRangeForAPI()
      const params = new URLSearchParams({
        start_date: dateRangeParams.start_date,
        end_date: dateRangeParams.end_date
      })

      // Fetch staff performance data
      const response = await apiGet(`/api/reports/staff-performance?${params}`)
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      const data = await response.json()

      if (Array.isArray(data) && data.length > 0) {
        // Sort data by total_revenue descending before processing
        data.sort((a, b) => (b.total_revenue || 0) - (a.total_revenue || 0))
        // Process data for revenue breakdown
        const breakdownData = data.map((staff, index) => {
          return {
            staff: staff.staff_name || 'Unknown',
            membership: staff.membership_revenue || 0,
            package: staff.package_revenue || 0,
            prepaid: staff.prepaid_revenue || 0,
            product: staff.product_revenue || 0,
            service: staff.service_revenue || 0,
            total: staff.total_revenue || 0,
          }
        })

        setRevenueBreakdownData(breakdownData)

        // Process leaderboard data
        const leaderboardData = data.map((staff, index) => {
          const name = staff.staff_name || 'Unknown'
          // Generate initials safely
          let initials = 'N/A'
          if (name && name.trim()) {
            const nameParts = name.trim().split(/\s+/).filter(part => part.length > 0)
            if (nameParts.length === 1) {
              initials = nameParts[0].substring(0, 2).toUpperCase()
            } else if (nameParts.length >= 2) {
              initials = (nameParts[0][0] + nameParts[nameParts.length - 1][0]).toUpperCase()
            } else {
              initials = name.substring(0, 2).toUpperCase()
            }
          }
          
          const colors = ['#FF6B6B', '#9B59B6', '#2ECC71', '#F39C12', '#3498DB', '#E74C3C', '#1ABC9C', '#F97316', '#8B5CF6', '#EC4899']
          
          return {
            id: index + 1,
            name: name,
            initial: initials,
            color: colors[index % colors.length],
            itemCount: Number(staff.total_services) || 0,
            service: Number(staff.service_revenue) || 0,
            package: Number(staff.package_revenue) || 0,
            prepaid: Number(staff.prepaid_revenue) || 0,
            product: Number(staff.product_revenue) || 0,
            membership: Number(staff.membership_revenue) || 0,
            totalRevenue: Number(staff.total_revenue) || 0,
          }
        })

        // Sort by total revenue descending
        leaderboardData.sort((a, b) => b.totalRevenue - a.totalRevenue)
        
        // Reassign IDs after sorting
        leaderboardData.forEach((staff, index) => {
          staff.id = index + 1
        })

        setStaffLeaderboardData(leaderboardData)

        // Set top performers
        if (data.length > 0) {
          const topPerformer = data[0]
          setPerformanceData({
            topPerformerRevenue: {
              name: topPerformer.staff_name || 'N/A',
              value: formatCurrency(topPerformer.total_revenue || 0),
              label: 'TOP PERFORMER (REVENUE)',
            },
            topServiceSeller: {
              name: topPerformer.staff_name || 'N/A',
              value: `${topPerformer.total_services || 0} items`,
              label: 'TOP SERVICE SELLER',
            },
            topRetailSeller: {
              name: data.length > 1 ? (data[1].staff_name || 'N/A') : 'N/A',
              value: data.length > 1 ? `${data[1].total_services || 0} items` : '0 items',
              label: 'TOP RETAIL SELLER',
            },
            busiestStaff: {
              name: topPerformer.staff_name || 'N/A',
              value: `${topPerformer.total_services || 0} items`,
              label: 'BUSIEST STAFF (ITEMS)',
            },
          })
        }
      }
    } catch (error) {
      console.error('Error fetching staff performance data:', error)
      // Keep default/empty data on error
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchStaffPerformanceData()
  }, [dateRange])

  const formatCurrency = (value) => {
    return `₹${value.toLocaleString('en-IN', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })}`
  }

  const handleExportData = () => {
    if (!revenueBreakdownData || revenueBreakdownData.length === 0) {
      alert('No data available to export')
      return
    }

    // Prepare data for export
    const exportData = revenueBreakdownData.map((staff) => ({
      'Staff Name': staff.staff,
      'Service Revenue': staff.service,
      'Package Revenue': staff.package,
      'Prepaid Revenue': staff.prepaid,
      'Product Revenue': staff.product,
      'Membership Revenue': staff.membership,
      'Total Revenue': staff.total,
    }))

    // Create workbook and worksheet
    const ws = XLSX.utils.json_to_sheet(exportData)
    const wb = XLSX.utils.book_new()
    XLSX.utils.book_append_sheet(wb, ws, 'Revenue Breakdown')

    // Generate filename with current date
    const date = new Date().toISOString().split('T')[0]
    const filename = `Revenue_Breakdown_${date}.xlsx`

    // Write file
    XLSX.writeFile(wb, filename)
  }

  const getMaxRevenue = () => {
    if (!revenueBreakdownData || revenueBreakdownData.length === 0) {
      return 1 // Return 1 to avoid division by zero
    }
    const max = Math.max(...revenueBreakdownData.map((item) => item.total || 0))
    return max > 0 ? max : 1 // Ensure at least 1 to avoid division by zero
  }

  return (
    <div className="staff-performance-page">
      {/* Header */}
      <header className="staff-performance-header">
        <div className="header-left">
          <button className="menu-icon">
            <FaBars />
          </button>
          <h1 className="header-title">Staff Performance Analysis</h1>
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

      <div className="staff-performance-container">
        {loading && (
          <div style={{ textAlign: 'center', padding: '20px', color: '#6b7280' }}>
            Loading data...
          </div>
        )}
        <div className="staff-performance-content">
          {/* Back Button and Date Range */}
          <div className="controls-section">
            <button className="back-button" onClick={handleBackToReports}>
              <FaArrowLeft />
              Back to Reports Hub
            </button>
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
                <option>Last 6 Months</option>
                <option>Last Year</option>
                <option>Custom Range</option>
              </select>
            </div>
          </div>

          {/* Top Performers Cards */}
          <div className="top-performers-grid">
            <div className="performer-card">
              <div className="performer-icon star">
                <FaStar />
              </div>
              <div className="performer-info">
                <h3 className="performer-name">
                  {performanceData.topPerformerRevenue.name}
                </h3>
                <p className="performer-label">
                  {performanceData.topPerformerRevenue.label}
                </p>
              </div>
            </div>

            <div className="performer-card">
              <div className="performer-icon service">
                <FaShoppingBag />
              </div>
              <div className="performer-info">
                <h3 className="performer-name">
                  {performanceData.topServiceSeller.name}
                </h3>
                <p className="performer-label">
                  {performanceData.topServiceSeller.label}
                </p>
              </div>
            </div>

            <div className="performer-card">
              <div className="performer-icon retail">
                <FaBox />
              </div>
              <div className="performer-info">
                <h3 className="performer-name">
                  {performanceData.topRetailSeller.name}
                </h3>
                <p className="performer-label">
                  {performanceData.topRetailSeller.label}
                </p>
              </div>
            </div>

            <div className="performer-card">
              <div className="performer-icon busiest">
                <FaUserFriends />
              </div>
              <div className="performer-info">
                <h3 className="performer-name">
                  {performanceData.busiestStaff.name}
                </h3>
                <p className="performer-label">
                  {performanceData.busiestStaff.label}
                </p>
              </div>
            </div>
          </div>

          {/* Revenue Breakdown Chart */}
          <div className="chart-section">
            <div className="chart-section-header">
              <h2 className="section-title">
                Revenue Breakdown by Staff
              </h2>
              <div className="chart-actions">
                <button 
                  className="action-btn refresh-btn"
                  onClick={fetchStaffPerformanceData}
                  title="Refresh Data"
                >
                  <FaSync />
                  Refresh
                </button>
                <button 
                  className="action-btn download-btn"
                  onClick={handleExportData}
                  title="Export to Excel"
                >
                  <FaDownload />
                  Export
                </button>
              </div>
            </div>
            <div className="chart-container">
              {loading ? (
                <div style={{ height: '400px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  Loading...
                </div>
              ) : revenueBreakdownData && revenueBreakdownData.length > 0 ? (
                <ResponsiveContainer width="100%" height={400}>
                  <BarChart data={revenueBreakdownData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                    <XAxis 
                      dataKey="staff" 
                      tick={{ fontSize: 12, fill: '#6b7280' }}
                      stroke="#9ca3af"
                      angle={-45}
                      textAnchor="end"
                      height={100}
                    />
                    <YAxis 
                      tick={{ fontSize: 12, fill: '#6b7280' }}
                      stroke="#9ca3af"
                      tickFormatter={(value) => value >= 1000 ? `₹${(value / 1000).toFixed(0)}k` : `₹${value}`}
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
                      cursor={{ fill: 'rgba(0, 0, 0, 0.05)' }}
                    />
                    <Legend 
                      wrapperStyle={{ paddingTop: '20px' }}
                      iconType="square"
                    />
                    <Bar dataKey="service" stackId="a" fill="#4f46e5" name="Service" radius={[0, 0, 0, 0]} />
                    <Bar dataKey="product" stackId="a" fill="#06b6d4" name="Product" radius={[0, 0, 0, 0]} />
                    <Bar dataKey="prepaid" stackId="a" fill="#f59e0b" name="Prepaid" radius={[0, 0, 0, 0]} />
                    <Bar dataKey="package" stackId="a" fill="#10b981" name="Package" radius={[0, 0, 0, 0]} />
                    <Bar dataKey="membership" stackId="a" fill="#8b5cf6" name="Membership" radius={[4, 4, 0, 0]} />
                  </BarChart>
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
                  No data available for the selected period
                </div>
              )}
            </div>
          </div>

          {/* Staff Leaderboard Table */}
          <div className="leaderboard-section">
            <h2 className="section-title">Staff Leaderboard</h2>
            <div className="table-container">
              <table className="leaderboard-table">
                <thead>
                  <tr>
                    <th className="text-left">Staff</th>
                    <th className="text-center">Item Count</th>
                    <th className="text-right">Service</th>
                    <th className="text-right">Package</th>
                    <th className="text-right">Prepaid</th>
                    <th className="text-right">Product</th>
                    <th className="text-right">Membership</th>
                    <th className="text-right">Total Revenue</th>
                  </tr>
                </thead>
                <tbody>
                  {staffLeaderboardData && staffLeaderboardData.length > 0 ? (
                    staffLeaderboardData.map((staff) => (
                      <tr key={staff.id}>
                        <td>
                          <div className="staff-cell">
                            <div
                              className="staff-avatar"
                              style={{ backgroundColor: staff.color }}
                            >
                              {staff.initial || 'N/A'}
                            </div>
                            <span className="staff-name">{staff.name || 'Unknown'}</span>
                          </div>
                        </td>
                        <td className="text-center">{staff.itemCount || 0}</td>
                        <td className="text-right">
                          {formatCurrency(staff.service || 0)}
                        </td>
                        <td className="text-right">
                          {formatCurrency(staff.package || 0)}
                        </td>
                        <td className="text-right">
                          {formatCurrency(staff.prepaid || 0)}
                        </td>
                        <td className="text-right">
                          {formatCurrency(staff.product || 0)}
                        </td>
                        <td className="text-right">
                          {formatCurrency(staff.membership || 0)}
                        </td>
                        <td className="text-right total-revenue">
                          {formatCurrency(staff.totalRevenue || 0)}
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan="8" style={{ textAlign: 'center', padding: '40px 20px', color: '#6b7280' }}>
                        {loading ? 'Loading data...' : 'No staff data available for the selected period'}
                      </td>
                    </tr>
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

export default StaffPerformanceAnalysis
