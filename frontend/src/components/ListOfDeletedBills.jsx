import React, { useState, useEffect } from 'react'
import {
  FaBars,
  FaBell,
  FaUser,
  FaArrowLeft,
  FaCloudDownloadAlt,
} from 'react-icons/fa'
import './ListOfDeletedBills.css'
import { API_BASE_URL } from '../config'
import { apiGet } from '../utils/api'

const ListOfDeletedBills = ({ setActivePage }) => {
  const [dateFilter, setDateFilter] = useState('today')
  const [deletedBills, setDeletedBills] = useState([])
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
    fetchDeletedBills()
  }, [dateFilter])

  const fetchDeletedBills = async () => {
    try {
      setLoading(true)
      const dateRange = getDateRange()
      const params = new URLSearchParams(dateRange)
      
      const response = await apiGet(`/api/reports/deleted-bills?${params}`)
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const data = await response.json()
      setDeletedBills(Array.isArray(data) ? data : [])
    } catch (error) {
      console.error('Error fetching deleted bills:', error)
      setDeletedBills([])
    } finally {
      setLoading(false)
    }
  }

  const handleDownload = () => {
    const csvContent = [
      ['Invoice No.', 'Customer', 'Date', 'Reason', 'Total Amount'],
      ...deletedBills.map(bill => [
        bill.bill_number || 'N/A',
        bill.customer_name || 'Walk-in',
        bill.deleted_at ? new Date(bill.deleted_at).toLocaleDateString() : 'N/A',
        bill.deletion_reason || 'N/A',
        bill.final_amount?.toFixed(2) || '0.00',
      ])
    ].map(row => row.join(',')).join('\n')
    
    const blob = new Blob([csvContent], { type: 'text/csv' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `deleted-bills-${new Date().toISOString().split('T')[0]}.csv`
    a.click()
    window.URL.revokeObjectURL(url)
  }

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A'
    return new Date(dateString).toLocaleDateString()
  }

  return (
    <div className="list-of-deleted-bills-page">
      {/* Header */}
      <header className="list-of-deleted-bills-header">
        <div className="header-left">
          <button className="menu-icon">
            <FaBars />
          </button>
          <h1 className="header-title">List of Deleted Bills</h1>
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

      <div className="list-of-deleted-bills-container">
        {/* Main Report Card */}
        <div className="report-card">
          {/* Back Button */}
          <button className="back-button" onClick={handleBackToReports}>
            <FaArrowLeft />
            Back to Reports Hub
          </button>

          {/* Filters and Actions */}
          <div className="filters-actions-section">
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

          {/* Deleted Bills Table */}
          <div className="table-container">
            <table className="deleted-bills-table">
              <thead>
                <tr>
                  <th>Invoice No.</th>
                  <th>Customer</th>
                  <th>Date</th>
                  <th>Reason</th>
                  <th>Total Amount</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan="6" className="empty-message">Loading...</td>
                  </tr>
                ) : deletedBills.length === 0 ? (
                  <tr>
                    <td colSpan="6" className="empty-message">
                      No deleted bills found for this selection.
                    </td>
                  </tr>
                ) : (
                  deletedBills.map((bill, index) => (
                    <tr key={index}>
                      <td>{bill.bill_number || 'N/A'}</td>
                      <td>{bill.customer_name || 'Walk-in'}</td>
                      <td>{formatDate(bill.deleted_at)}</td>
                      <td>{bill.deletion_reason || 'N/A'}</td>
                      <td>₹{bill.final_amount?.toFixed(2) || '0.00'}</td>
                      <td>
                        <button className="action-btn" onClick={() => alert(`Bill Details:\nInvoice: ${bill.bill_number}\nCustomer: ${bill.customer_name}\nAmount: ₹${bill.final_amount?.toFixed(2) || '0.00'}\nReason: ${bill.deletion_reason || 'N/A'}`)}>
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

export default ListOfDeletedBills

