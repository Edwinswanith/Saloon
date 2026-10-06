import React, { useState, useEffect } from 'react'
import {
  FaArrowLeft,
  FaCloudDownloadAlt,
  FaList,
  FaTimes,
} from 'react-icons/fa'
import './StaffIncentiveReport.css'
import { API_BASE_URL } from '../config'
import { apiGet } from '../utils/api'
import { useAuth } from '../contexts/AuthContext'

const StaffIncentiveReport = ({ setActivePage }) => {
  const { currentBranch } = useAuth()
  const [dateFilter, setDateFilter] = useState('last-30-days')
  const [staffPerformance, setStaffPerformance] = useState([])
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [selectedStaff, setSelectedStaff] = useState(null)

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
  }, [dateFilter, currentBranch])

  // Listen for branch changes
  useEffect(() => {
    const handleBranchChange = () => {
      console.log('[StaffIncentiveReport] Branch changed, refreshing data...')
      fetchStaffPerformance()
    }
    
    window.addEventListener('branchChanged', handleBranchChange)
    return () => window.removeEventListener('branchChanged', handleBranchChange)
  }, [currentBranch])

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
        membership: staff.membership || 0,
        total: staff.total || staff.total_revenue || 0,
        avgBill: staff.avg_bill || 0,
        billCount: staff.bill_count || 0,
        commissionRate: staff.commission_rate || 0,
        commissionEarned: staff.commission_earned || 0,
        incentiveThreshold: staff.incentive_threshold || 0,
        incentiveRate: staff.incentive_rate || 0,
        incentiveBase: staff.incentive_base || 0,
        incentiveEligible: !!staff.incentive_eligible,
        incentiveStatus: staff.incentive_status || 'not_configured',
        incentiveAmount: staff.incentive_amount || 0,
        revenueToTarget: staff.revenue_to_target || 0,
        targetProgressPercent: staff.target_progress_percent || 0,
        variablePay: staff.variable_pay || 0,
        totalEarnings: staff.total_earnings || 0,
        rawData: staff, // Store raw data for modal
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
      ['#', 'Staff Name', 'Bills', 'Items', 'Service', 'Package', 'Product', 'Membership', 'Performance Revenue', 'Target', 'Progress %', 'Commission', 'Incentive Base', 'Incentive', 'Variable Pay'],
      ...staffPerformance.map((staff, index) => [
        index + 1,
        staff.staffName,
        staff.billCount,
        staff.itemCount,
        staff.service.toFixed(2),
        staff.package.toFixed(2),
        staff.product.toFixed(2),
        staff.membership.toFixed(2),
        staff.total.toFixed(2),
        staff.incentiveThreshold.toFixed(2),
        staff.targetProgressPercent.toFixed(2),
        staff.commissionEarned.toFixed(2),
        staff.incentiveBase.toFixed(2),
        staff.incentiveAmount.toFixed(2),
        staff.variablePay.toFixed(2),
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

  const handleViewDetails = (staff) => {
    setSelectedStaff(staff)
    setShowModal(true)
  }

  const formatCurrency = (amount) => {
    return `₹${amount?.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || '0.00'}`
  }

  const formatMoney = (amount) => (
    `\u20b9${Number(amount || 0).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
  )

  const formatPercent = (value) => `${Number(value || 0).toFixed(2)}%`

  const reportTotals = staffPerformance.reduce((totals, staff) => {
    totals.totalRevenue += staff.total
    totals.totalCommission += staff.commissionEarned
    totals.totalIncentive += staff.incentiveAmount
    totals.eligibleCount += staff.incentiveEligible ? 1 : 0
    totals.totalVariablePay += staff.variablePay
    return totals
  }, {
    totalRevenue: 0,
    totalCommission: 0,
    totalIncentive: 0,
    eligibleCount: 0,
    totalVariablePay: 0,
  })

  return (
    <div className="staff-incentive-report-page">
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
                </select>
              </div>

              <button className="download-report-btn" onClick={handleDownload}>
                <FaCloudDownloadAlt />
                Download Report
              </button>
            </div>
          </div>

          <div className="incentive-summary-grid">
            <div className="incentive-summary-card">
              <span>Performance Revenue</span>
              <strong>{formatMoney(reportTotals.totalRevenue)}</strong>
              <small>Staff-attributed revenue in this period.</small>
            </div>
            <div className="incentive-summary-card">
              <span>Commission</span>
              <strong>{formatMoney(reportTotals.totalCommission)}</strong>
              <small>Revenue x staff commission rate.</small>
            </div>
            <div className="incentive-summary-card">
              <span>Incentive Bonus</span>
              <strong>{formatMoney(reportTotals.totalIncentive)}</strong>
              <small>Only revenue above target earns incentive.</small>
            </div>
            <div className="incentive-summary-card">
              <span>Eligible Staff</span>
              <strong>{reportTotals.eligibleCount}</strong>
              <small>Staff who crossed their incentive target.</small>
            </div>
          </div>

          <div className="incentive-rule-note">
            <strong>Calculation rule</strong>
            <span>
              Commission = performance revenue x commission %. Incentive = max(performance revenue - target, 0) x incentive %.
            </span>
          </div>

          <div className="table-section">
            <h2 className="table-title">Staff Incentive Performance</h2>
            <div className="table-container">
              <table className="performance-table incentive-performance-table">
                <thead>
                  <tr>
                    <th>#</th>
                    <th>Staff Name</th>
                    <th>Performance Revenue</th>
                    <th>Target Progress</th>
                    <th>Commission</th>
                    <th>Incentive</th>
                    <th>Variable Pay</th>
                    <th>Info</th>
                  </tr>
                </thead>
                <tbody>
                  {loading ? (
                    <tr>
                      <td colSpan="8" className="empty-message">Loading...</td>
                    </tr>
                  ) : staffPerformance.length === 0 ? (
                    <tr>
                      <td colSpan="8" className="empty-message">
                        No staff performance data found for this selection.
                      </td>
                    </tr>
                  ) : (
                    staffPerformance.map((staff, index) => (
                      <tr key={`incentive-${staff.id}`}>
                        <td>{index + 1}</td>
                        <td className="staff-name">{staff.staffName}</td>
                        <td className="total-cell">{formatMoney(staff.total)}</td>
                        <td>
                          {staff.incentiveStatus === 'not_configured' ? (
                            <span className="muted-cell">Not configured</span>
                          ) : (
                            <div className="target-progress-cell">
                              <div className="target-progress-track">
                                <span style={{ width: `${Math.min(staff.targetProgressPercent, 100)}%` }}></span>
                              </div>
                              <small>{formatPercent(staff.targetProgressPercent)}</small>
                            </div>
                          )}
                        </td>
                        <td>{formatMoney(staff.commissionEarned)}</td>
                        <td>
                          <span className={`incentive-status-pill ${staff.incentiveStatus}`}>
                            {formatMoney(staff.incentiveAmount)}
                          </span>
                        </td>
                        <td className="total-cell">{formatMoney(staff.variablePay)}</td>
                        <td>
                          <button
                            className="info-btn"
                            title="View Details"
                            onClick={() => handleViewDetails(staff)}
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

          {/* Employee Performance Table */}
          <div className="table-section legacy-incentive-table">
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
                    <th>Membership</th>
                    <th>Total</th>
                    <th>Avg. Bill (₹)</th>
                    <th>Incentive</th>
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
                        <td>{staff.membership.toFixed(2)}</td>
                        <td className="total-cell">₹ {staff.total.toFixed(2)}</td>
                        <td className="avg-bill-cell">
                          ₹ {staff.avgBill.toFixed(2)}
                        </td>
                        <td>₹ {staff.incentiveAmount.toFixed(2)}</td>
                        <td>
                          <button 
                            className="info-btn" 
                            title="View Details"
                            onClick={() => alert(`Staff Performance Details:\n\nStaff: ${staff.staffName}\nItem Count: ${staff.itemCount}\nService: ₹${staff.service.toFixed(2)}\nPackage: ₹${staff.package.toFixed(2)}\nProduct: ₹${staff.product.toFixed(2)}\nMembership: ₹${staff.membership.toFixed(2)}\nTotal: ₹${staff.total.toFixed(2)}\nAvg. Bill: ₹${staff.avgBill.toFixed(2)}`)}
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

      {/* Staff Performance Details Modal */}
      {showModal && selectedStaff && (
        <div className="customer-modal-overlay" onClick={() => setShowModal(false)}>
          <div className="customer-modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="customer-modal-header">
              <h2>Staff Performance Details</h2>
              <button className="customer-modal-close" onClick={() => setShowModal(false)}>
                <FaTimes />
              </button>
            </div>

            <div className="customer-modal-body">
              <>
                {/* Staff Information */}
                <div className="customer-details-section">
                  <h3>Staff Information</h3>
                  <div className="customer-details-grid">
                    <div className="customer-detail-item">
                      <span className="detail-label">Staff Name:</span>
                      <span className="detail-value">{selectedStaff.staffName || 'N/A'}</span>
                    </div>
                    <div className="customer-detail-item">
                      <span className="detail-label">Item Count:</span>
                      <span className="detail-value">{selectedStaff.itemCount || 0}</span>
                    </div>
                    {selectedStaff.rawData?.commission_rate !== undefined && (
                      <div className="customer-detail-item">
                        <span className="detail-label">Commission Rate:</span>
                        <span className="detail-value">{selectedStaff.rawData.commission_rate || 0}%</span>
                      </div>
                    )}
                    {selectedStaff.rawData?.incentive_rate !== undefined && (
                      <div className="customer-detail-item">
                        <span className="detail-label">Incentive Rule:</span>
                        <span className="detail-value">
                          {selectedStaff.rawData.incentive_rate || 0}% over {formatMoney(selectedStaff.rawData.incentive_threshold || 50000)}
                        </span>
                      </div>
                    )}
                    {selectedStaff.rawData?.salary !== undefined && (
                      <div className="customer-detail-item">
                        <span className="detail-label">Monthly Salary:</span>
                        <span className="detail-value">{formatMoney(selectedStaff.rawData.salary || 0)}</span>
                      </div>
                    )}
                    {selectedStaff.rawData?.period_salary !== undefined && (
                      <div className="customer-detail-item">
                        <span className="detail-label">Salary For Period:</span>
                        <span className="detail-value">{formatMoney(selectedStaff.rawData.period_salary || 0)}</span>
                      </div>
                    )}
                  </div>
                </div>

                {/* Revenue Breakdown */}
                <div className="customer-details-section">
                  <h3>Revenue Breakdown</h3>
                  <div className="customer-details-grid">
                    <div className="customer-detail-item">
                      <span className="detail-label">Service Revenue:</span>
                      <span className="detail-value">{formatMoney(selectedStaff.service || 0)}</span>
                    </div>
                    <div className="customer-detail-item">
                      <span className="detail-label">Package Revenue:</span>
                      <span className="detail-value">{formatMoney(selectedStaff.package || 0)}</span>
                    </div>
                    <div className="customer-detail-item">
                      <span className="detail-label">Product Revenue:</span>
                      <span className="detail-value">{formatMoney(selectedStaff.product || 0)}</span>
                    </div>
                    <div className="customer-detail-item">
                      <span className="detail-label">Membership Revenue:</span>
                      <span className="detail-value">{formatMoney(selectedStaff.membership || 0)}</span>
                    </div>
                    <div className="customer-detail-item">
                      <span className="detail-label">Total Revenue:</span>
                      <span className="detail-value revenue-stat">{formatMoney(selectedStaff.total || 0)}</span>
                    </div>
                  </div>
                </div>

                {/* Performance Statistics */}
                <div className="customer-details-section">
                  <h3>Performance Statistics</h3>
                  <div className="customer-stats-grid">
                    <div className="customer-stat-card">
                      <div className="stat-label">Total Revenue</div>
                      <div className="stat-value revenue-stat">
                        {formatMoney(selectedStaff.total || 0)}
                      </div>
                      <div className="stat-description">Total revenue generated</div>
                    </div>
                    <div className="customer-stat-card">
                      <div className="stat-label">Average Bill</div>
                      <div className="stat-value">
                        {formatMoney(selectedStaff.avgBill || 0)}
                      </div>
                      <div className="stat-description">Average per transaction</div>
                    </div>
                    <div className="customer-stat-card">
                      <div className="stat-label">Items Sold</div>
                      <div className="stat-value">
                        {selectedStaff.itemCount || 0}
                      </div>
                      <div className="stat-description">Total items processed</div>
                    </div>
                  </div>
                </div>

                {/* Earnings Breakdown */}
                {(selectedStaff.rawData?.commission_earned !== undefined || selectedStaff.rawData?.total_earnings !== undefined) && (
                  <div className="customer-details-section">
                    <h3>Earnings Breakdown</h3>
                    <div className="customer-details-grid">
                      {selectedStaff.rawData?.commission_earned !== undefined && (
                        <div className="customer-detail-item">
                          <span className="detail-label">Commission Earned:</span>
                          <span className="detail-value revenue-stat">
                            {formatMoney(selectedStaff.rawData.commission_earned || 0)}
                          </span>
                        </div>
                      )}
                      {selectedStaff.rawData?.incentive_amount !== undefined && (
                        <div className="customer-detail-item">
                          <span className="detail-label">Incentive Earned:</span>
                          <span className="detail-value revenue-stat">
                            {formatMoney(selectedStaff.rawData.incentive_amount || 0)}
                          </span>
                        </div>
                      )}
                      {selectedStaff.rawData?.incentive_base !== undefined && (
                        <div className="customer-detail-item">
                          <span className="detail-label">Incentive Base:</span>
                          <span className="detail-value">
                            {formatMoney(selectedStaff.rawData.incentive_base || 0)}
                          </span>
                        </div>
                      )}
                      {selectedStaff.rawData?.revenue_to_target !== undefined && (
                        <div className="customer-detail-item">
                          <span className="detail-label">Revenue To Target:</span>
                          <span className="detail-value">
                            {formatMoney(selectedStaff.rawData.revenue_to_target || 0)}
                          </span>
                        </div>
                      )}
                      {selectedStaff.rawData?.variable_pay !== undefined && (
                        <div className="customer-detail-item">
                          <span className="detail-label">Variable Pay:</span>
                          <span className="detail-value revenue-stat">
                            {formatMoney(selectedStaff.rawData.variable_pay || 0)}
                          </span>
                        </div>
                      )}
                      {selectedStaff.rawData?.total_earnings !== undefined && (
                        <div className="customer-detail-item">
                          <span className="detail-label">Total Pay For Period:</span>
                          <span className="detail-value revenue-stat">
                            {formatMoney(selectedStaff.rawData.total_earnings || 0)}
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default StaffIncentiveReport

