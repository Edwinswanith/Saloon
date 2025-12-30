import React, { useState } from 'react'
import {
  FaBars,
  FaBell,
  FaUser,
  FaArrowLeft,
  FaCloudDownloadAlt,
} from 'react-icons/fa'
import './ExpenseReport.css'
import { apiGet } from '../utils/api'

const ExpenseReport = ({ setActivePage }) => {
  const [dateFilter, setDateFilter] = useState('current-month')
  const [categoryFilter, setCategoryFilter] = useState('all')
  const [paymentModeFilter, setPaymentModeFilter] = useState('all')

  const handleBackToReports = () => {
    if (setActivePage) {
      setActivePage('reports')
    }
  }

  const totalExpense = 0.0

  return (
    <div className="expense-report-page">
      {/* Header */}
      <header className="expense-report-header">
        <div className="header-left">
          <button className="menu-icon">
            <FaBars />
          </button>
          <h1 className="header-title">Expense Report</h1>
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

      <div className="expense-report-container">
        {/* Back Button */}
        <button className="back-button" onClick={handleBackToReports}>
          <FaArrowLeft />
          Back to Reports Hub
        </button>

        {/* Main Report Card */}
        <div className="report-card">
          {/* Filters Section */}
          <div className="filters-section">
            <div className="filter-group">
              <label className="filter-label">Filter by Date</label>
              <select
                className="filter-dropdown"
                value={dateFilter}
                onChange={(e) => setDateFilter(e.target.value)}
              >
                <option value="current-month">Current Month</option>
                <option value="last-month">Last Month</option>
                <option value="current-year">Current Year</option>
                <option value="custom">Custom Range</option>
              </select>
            </div>

            <div className="filter-group">
              <label className="filter-label">Category</label>
              <select
                className="filter-dropdown"
                value={categoryFilter}
                onChange={(e) => setCategoryFilter(e.target.value)}
              >
                <option value="all">All</option>
                <option value="rent">Rent</option>
                <option value="utilities">Utilities</option>
                <option value="supplies">Supplies</option>
                <option value="other">Other</option>
              </select>
            </div>

            <div className="filter-group">
              <label className="filter-label">Payment Mode</label>
              <select
                className="filter-dropdown"
                value={paymentModeFilter}
                onChange={(e) => setPaymentModeFilter(e.target.value)}
              >
                <option value="all">All</option>
                <option value="cash">Cash</option>
                <option value="card">Card</option>
                <option value="upi">UPI</option>
              </select>
            </div>
          </div>

          {/* Report Actions and Summary */}
          <div className="report-actions-summary">
            <button className="download-report-btn">
              <FaCloudDownloadAlt />
              Download Report
            </button>
            <div className="total-expense-display">
              Total Expense for this period: ₹{totalExpense.toFixed(2)}
            </div>
          </div>

          {/* Expense Table */}
          <div className="table-container">
            <table className="expense-report-table">
              <thead>
                <tr>
                  <th>#</th>
                  <th>Category</th>
                  <th>Payment Mode</th>
                  <th>Expense Name</th>
                  <th>Date</th>
                  <th>Total</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td colSpan="6" className="empty-message">
                    No expenses found for this selection.
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ExpenseReport

