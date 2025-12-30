import React, { useState } from 'react'
import {
  FaBars,
  FaBell,
  FaUser,
  FaArrowLeft,
  FaList,
} from 'react-icons/fa'
import './StaffCombinedReport.css'
import { API_BASE_URL } from '../config'
import { apiGet } from '../utils/api'  
const StaffCombinedReport = ({ setActivePage }) => {
  const [dateFilter, setDateFilter] = useState('last-7-days')

  const handleBackToReports = () => {
    if (setActivePage) {
      setActivePage('reports')
    }
  }

  const staffSummary = [
    {
      id: 1,
      staff: 'Ajay',
      totalSale: 2346,
      totalBills: 2,
      avgBillValue: 1173.22,
    },
    {
      id: 2,
      staff: 'Ashok',
      totalSale: 1500,
      totalBills: 3,
      avgBillValue: 500.0,
    },
    {
      id: 3,
      staff: 'Deepika',
      totalSale: 3200,
      totalBills: 4,
      avgBillValue: 800.0,
    },
    {
      id: 4,
      staff: 'Rama',
      totalSale: 4500,
      totalBills: 5,
      avgBillValue: 900.0,
    },
    {
      id: 5,
      staff: 'Aman',
      totalSale: 2800,
      totalBills: 3,
      avgBillValue: 933.33,
    },
  ]

  return (
    <div className="staff-combined-report-page">
      {/* Header */}
      <header className="staff-combined-report-header">
        <div className="header-left">
          <button className="menu-icon">
            <FaBars />
          </button>
          <h1 className="header-title">Staff Combined Report</h1>
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

      <div className="staff-combined-report-container">
        {/* Back Button */}
        <button className="back-button" onClick={handleBackToReports}>
          <FaArrowLeft />
          Back to Reports Hub
        </button>

        {/* Date Filter Section */}
        <div className="filter-card">
          <div className="filter-group">
            <label className="filter-label">Date Range</label>
            <select
              className="filter-dropdown"
              value={dateFilter}
              onChange={(e) => setDateFilter(e.target.value)}
            >
              <option value="today">Today</option>
              <option value="yesterday">Yesterday</option>
              <option value="last-7-days">Last 7 days</option>
              <option value="last-30-days">Last 30 days</option>
              <option value="current-month">Current Month</option>
              <option value="last-month">Last Month</option>
              <option value="custom">Custom Range</option>
            </select>
          </div>
        </div>

        {/* Staff Summary Table */}
        <div className="report-card">
          <h2 className="section-title">Staff Summary</h2>
          <div className="table-container">
            <table className="staff-summary-table">
              <thead>
                <tr>
                  <th>Staff</th>
                  <th>Total Sale (₹)</th>
                  <th>Total Bills</th>
                  <th>Avg. Bill Value (₹)</th>
                  <th>Details</th>
                </tr>
              </thead>
              <tbody>
                {staffSummary.length > 0 ? (
                  staffSummary.map((staff) => (
                    <tr key={staff.id}>
                      <td className="staff-name">{staff.staff}</td>
                      <td>{staff.totalSale.toLocaleString()}</td>
                      <td>{staff.totalBills}</td>
                      <td>{staff.avgBillValue.toFixed(2)}</td>
                      <td>
                        <button className="details-btn" title="View Details">
                          <FaList />
                        </button>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="5" className="empty-message">
                      No staff data found for this selection.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  )
}

export default StaffCombinedReport

