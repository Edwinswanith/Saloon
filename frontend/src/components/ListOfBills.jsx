import React, { useState, useEffect } from 'react'
import {
  FaBars,
  FaBell,
  FaUser,
  FaArrowLeft,
  FaCloudDownloadAlt,
} from 'react-icons/fa'
import './ListOfBills.css'
import { API_BASE_URL } from '../config'
import { apiGet } from '../utils/api'
import { useAuth } from '../contexts/AuthContext'

const ListOfBills = ({ setActivePage }) => {
  const { currentBranch } = useAuth()
  const [dateFilter, setDateFilter] = useState('month') // Default to month to show more bills
  const [bills, setBills] = useState([])
  const [loading, setLoading] = useState(true)
  const [totalTransactions, setTotalTransactions] = useState(0)
  const [totalRevenue, setTotalRevenue] = useState(0)

  useEffect(() => {
    fetchBills()
  }, [dateFilter, currentBranch])

  // Listen for branch changes
  useEffect(() => {
    const handleBranchChange = () => {
      console.log('[ListOfBills] Branch changed, refreshing bills...')
      fetchBills()
    }
    
    window.addEventListener('branchChanged', handleBranchChange)
    return () => window.removeEventListener('branchChanged', handleBranchChange)
  }, [currentBranch])

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
        return { start: today.toISOString().split('T')[0], end: today.toISOString().split('T')[0] }
      case 'yesterday':
        return { start: yesterday.toISOString().split('T')[0], end: yesterday.toISOString().split('T')[0] }
      case 'week':
        return { start: weekStart.toISOString().split('T')[0], end: today.toISOString().split('T')[0] }
      case 'month':
        return { start: monthStart.toISOString().split('T')[0], end: today.toISOString().split('T')[0] }
      case 'year':
        return { start: yearStart.toISOString().split('T')[0], end: today.toISOString().split('T')[0] }
      case 'all':
        return { start: null, end: null } // Show all bills
      default:
        return { start: null, end: null } // Show all bills if no filter
    }
  }

  const fetchBills = async () => {
    try {
      setLoading(true)
      const { start, end } = getDateRange()
      const params = new URLSearchParams()
      if (start) params.append('start_date', start)
      if (end) params.append('end_date', end)

      const response = await apiGet(`/api/reports/list-of-bills?${params}`)
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const data = await response.json()
      
      if (Array.isArray(data)) {
        setBills(data)
        setTotalTransactions(data.length)
        setTotalRevenue(data.reduce((sum, bill) => sum + (bill.final_amount || 0), 0))
      } else {
        setBills([])
        setTotalTransactions(0)
        setTotalRevenue(0)
      }
    } catch (error) {
      console.error('Error fetching bills:', error)
      setBills([])
      setTotalTransactions(0)
      setTotalRevenue(0)
    } finally {
      setLoading(false)
    }
  }

  const handleBackToReports = () => {
    if (setActivePage) {
      setActivePage('reports')
    }
  }

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A'
    const date = new Date(dateString)
    const day = String(date.getDate()).padStart(2, '0')
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const year = date.getFullYear()
    return `${day}-${month}-${year}`
  }

  return (
    <div className="list-of-bills-page">
      {/* Header */}
      <header className="list-of-bills-header">
        <div className="header-left">
          <button className="menu-icon">
            <FaBars />
          </button>
          <h1 className="header-title">List of Bills</h1>
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

      <div className="list-of-bills-container">
        {/* Main Report Card */}
        <div className="report-card">
          {/* Back Button */}
          <button className="back-button" onClick={handleBackToReports}>
            <FaArrowLeft />
            Back to Reports Hub
          </button>

          {/* Summary Cards */}
          <div className="summary-cards">
            <div className="summary-card transactions-card">
              <div className="summary-value">{totalTransactions}</div>
              <div className="summary-label">TOTAL TRANSACTIONS</div>
            </div>
            <div className="summary-card revenue-card">
              <div className="summary-value">₹{totalRevenue.toFixed(0)}</div>
              <div className="summary-label">TOTAL REVENUE</div>
            </div>
          </div>

          {/* Filters and Actions */}
          <div className="filters-actions-section">
            <div className="filter-group">
              <select
                className="date-filter-dropdown"
                value={dateFilter}
                onChange={(e) => setDateFilter(e.target.value)}
              >
                <option value="all">All Bills</option>
                <option value="today">Today</option>
                <option value="yesterday">Yesterday</option>
                <option value="week">This Week</option>
                <option value="month">This Month</option>
                <option value="year">This Year</option>
                <option value="custom">Custom Range</option>
              </select>
            </div>

            <button 
              className="download-report-btn"
              onClick={() => {
                // Create CSV content
                const csvContent = [
                  ['Invoice No.', 'Customer', 'Date', 'Payment Mode', 'Subtotal', 'Discount', 'Net', 'Tax', 'Total'],
                  ...bills.map(bill => [
                    bill.bill_number || 'N/A',
                    bill.customer_name || 'Walk-in',
                    formatDate(bill.bill_date),
                    bill.payment_mode || 'N/A',
                    bill.subtotal?.toFixed(2) || '0.00',
                    bill.discount?.toFixed(2) || '0.00',
                    ((bill.subtotal || 0) - (bill.discount || 0)).toFixed(2),
                    bill.tax?.toFixed(2) || '0.00',
                    bill.final_amount?.toFixed(2) || '0.00',
                  ])
                ].map(row => row.join(',')).join('\n')
                
                // Download CSV
                const blob = new Blob([csvContent], { type: 'text/csv' })
                const url = window.URL.createObjectURL(blob)
                const a = document.createElement('a')
                a.href = url
                a.download = `bills-report-${dateFilter}-${new Date().toISOString().split('T')[0]}.csv`
                a.click()
                window.URL.revokeObjectURL(url)
              }}
            >
              <FaCloudDownloadAlt />
              Download Report
            </button>
          </div>

          {/* Bills Table */}
          <div className="table-container">
            <table className="bills-table">
              <thead>
                <tr>
                  <th>Invoice No.</th>
                  <th>Customer</th>
                  <th>Date</th>
                  <th>Payment Mode</th>
                  <th>Subtotal</th>
                  <th>Discount</th>
                  <th>Referral Discount</th>
                  <th>Net</th>
                  <th>Tax</th>
                  <th>Total</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan="11" className="empty-message">
                      Loading bills...
                    </td>
                  </tr>
                ) : bills.length === 0 ? (
                  <tr>
                    <td colSpan="11" className="empty-message">
                      No bills found for this selection.
                    </td>
                  </tr>
                ) : (
                  bills.map((bill, index) => (
                    <tr key={index}>
                      <td>{bill.bill_number || 'N/A'}</td>
                      <td>{bill.customer_name || 'Walk-in'}</td>
                      <td>{formatDate(bill.bill_date)}</td>
                      <td>{bill.payment_mode || 'N/A'}</td>
                      <td>₹{bill.subtotal?.toFixed(2) || '0.00'}</td>
                      <td>₹{bill.discount?.toFixed(2) || '0.00'}</td>
                      <td>₹0.00</td>
                      <td>₹{((bill.subtotal || 0) - (bill.discount || 0)).toFixed(2)}</td>
                      <td>₹{bill.tax?.toFixed(2) || '0.00'}</td>
                      <td>₹{bill.final_amount?.toFixed(2) || '0.00'}</td>
                      <td>
                        <button 
                          className="action-btn"
                          onClick={() => {
                            alert(`Bill Details:\nBill Number: ${bill.bill_number}\nCustomer: ${bill.customer_name}\nDate: ${formatDate(bill.bill_date)}\nFinal Amount: ₹${bill.final_amount?.toFixed(2) || '0.00'}`)
                          }}
                        >
                          View
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
  )
}

export default ListOfBills

