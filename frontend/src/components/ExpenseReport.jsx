import React, { useState, useEffect } from 'react'
import {
  FaArrowLeft,
  FaCloudDownloadAlt,
} from 'react-icons/fa'
import './ExpenseReport.css'
import { apiGet } from '../utils/api'
import { showError, showSuccess } from '../utils/toast.jsx'
import { TableSkeleton } from './shared/SkeletonLoaders'
import { EmptyTable } from './shared/EmptyStates'
import { useAuth } from '../contexts/AuthContext'

const ExpenseReport = ({ setActivePage }) => {
  const { currentBranch } = useAuth()
  const [dateFilter, setDateFilter] = useState('current-year')
  const [categoryFilter, setCategoryFilter] = useState('all')
  const [paymentModeFilter, setPaymentModeFilter] = useState('all')
  const [expenses, setExpenses] = useState([])
  const [categories, setCategories] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchCategories()
  }, [])

  useEffect(() => {
    if (categories.length > 0 || categoryFilter === 'all') {
      fetchExpenses()
    }
  }, [dateFilter, categoryFilter, paymentModeFilter, categories.length, currentBranch])

  // Listen for branch changes
  useEffect(() => {
    const handleBranchChange = () => {
      console.log('[ExpenseReport] Branch changed, refreshing expenses...')
      fetchExpenses()
      fetchCategories()
    }
    
    window.addEventListener('branchChanged', handleBranchChange)
    return () => window.removeEventListener('branchChanged', handleBranchChange)
  }, [currentBranch])

  const getDateRange = () => {
    const today = new Date()
    
    switch (dateFilter) {
      case 'current-month':
        const firstDay = new Date(today.getFullYear(), today.getMonth(), 1)
        const lastDay = new Date(today.getFullYear(), today.getMonth() + 1, 0)
        return {
          start_date: firstDay.toISOString().split('T')[0],
          end_date: lastDay.toISOString().split('T')[0]
        }
      case 'last-month':
        const lastMonthFirst = new Date(today.getFullYear(), today.getMonth() - 1, 1)
        const lastMonthLast = new Date(today.getFullYear(), today.getMonth(), 0)
        return {
          start_date: lastMonthFirst.toISOString().split('T')[0],
          end_date: lastMonthLast.toISOString().split('T')[0]
        }
      case 'current-year':
        return {
          start_date: new Date(today.getFullYear(), 0, 1).toISOString().split('T')[0],
          end_date: today.toISOString().split('T')[0]
        }
      default:
        return {}
    }
  }

  const fetchCategories = async () => {
    try {
      const response = await apiGet('/api/expenses/categories')
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      const data = await response.json()
      setCategories(Array.isArray(data) ? data : (data.categories || []))
    } catch (error) {
      console.error('Error fetching expense categories:', error)
      setCategories([])
    }
  }

  const fetchExpenses = async () => {
    try {
      setLoading(true)
      const params = new URLSearchParams()
      
      // Add category filter (convert category name to category_id if needed)
      if (categoryFilter !== 'all' && categories.length > 0) {
        // Find category by name
        const category = categories.find(cat => 
          cat.name.toLowerCase() === categoryFilter.toLowerCase()
        )
        if (category) {
          params.append('category_id', category.id)
        }
      }
      
      if (paymentModeFilter !== 'all') {
        params.append('payment_mode', paymentModeFilter)
      }
      
      // Add date filtering
      const dateRange = getDateRange()
      if (dateRange.start_date) params.append('start_date', dateRange.start_date)
      if (dateRange.end_date) params.append('end_date', dateRange.end_date)
      
      const response = await apiGet(`/api/expenses?${params}`)
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      const data = await response.json()
      setExpenses(Array.isArray(data) ? data : (data.expenses || []))
    } catch (error) {
      console.error('Error fetching expenses:', error)
      showError(`Error fetching expenses: ${error.message}`)
      setExpenses([])
    } finally {
      setLoading(false)
    }
  }

  const handleBackToReports = () => {
    if (setActivePage) {
      setActivePage('reports')
    }
  }

  const handleDownloadReport = () => {
    try {
      const csvContent = [
        ['No.', 'Category', 'Payment Mode', 'Expense Name', 'Date', 'Total'],
        ...expenses.map((expense, index) => [
          index + 1,
          expense.category_name || 'N/A',
          expense.payment_mode || 'N/A',
          expense.name || 'N/A',
          expense.expense_date ? expense.expense_date.split('T')[0] : 'N/A',
          `₹${(expense.amount || 0).toFixed(2)}`,
        ])
      ].map(row => {
        return row.map(cell => {
          const cellStr = String(cell || '')
          if (cellStr.includes(',') || cellStr.includes('"') || cellStr.includes('\n')) {
            return `"${cellStr.replace(/"/g, '""')}"`
          }
          return cellStr
        }).join(',')
      }).join('\n')
      
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      const fileName = `expense-report-${dateFilter}-${new Date().toISOString().split('T')[0]}.csv`
      a.download = fileName
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      window.URL.revokeObjectURL(url)
      showSuccess('Report downloaded successfully')
    } catch (error) {
      console.error('Error downloading report:', error)
      showError(`Error downloading report: ${error.message}`)
    }
  }

  const totalExpense = expenses.reduce((sum, expense) => sum + (expense.amount || 0), 0)

  return (
    <div className="expense-report-page">
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
                {categories.map((cat) => (
                  <option key={cat.id} value={cat.name}>
                    {cat.name}
                  </option>
                ))}
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
            <button className="download-report-btn" onClick={handleDownloadReport}>
              <FaCloudDownloadAlt />
              Download Report
            </button>
            <div className="total-expense-display">
              Total Expense for this period: ₹{totalExpense.toFixed(2)}
            </div>
          </div>

          {/* Expense Table */}
          <div className="table-container">
            {loading ? (
              <TableSkeleton rows={10} columns={6} />
            ) : expenses.length === 0 ? (
              <EmptyTable 
                title="No expenses found" 
                message="No expenses match your current filter selection. Try adjusting the date range or filters."
              />
            ) : (
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
                  {expenses.map((expense, index) => (
                    <tr key={expense.id}>
                      <td>{index + 1}</td>
                      <td>{expense.category_name || 'N/A'}</td>
                      <td>{expense.payment_mode || 'N/A'}</td>
                      <td>{expense.name || 'N/A'}</td>
                      <td>{expense.expense_date ? expense.expense_date.split('T')[0] : 'N/A'}</td>
                      <td>₹{(expense.amount || 0).toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default ExpenseReport

