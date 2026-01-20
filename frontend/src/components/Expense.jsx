import React, { useState, useEffect } from 'react'
import {
  FaCloudDownloadAlt,
  FaEdit,
  FaTrash,
  FaPlus,
} from 'react-icons/fa'
import Header from './Header'
import './Expense.css'
import { apiGet, apiPost, apiPut, apiDelete } from '../utils/api'
import { showSuccess, showError, showWarning } from '../utils/toast.jsx'
import { useAuth } from '../contexts/AuthContext'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  Legend,
  Cell,
} from 'recharts'
import DatePicker from 'react-datepicker'
import 'react-datepicker/dist/react-datepicker.css'
import { PageTransition } from './shared/PageTransition'
import { TableSkeleton, ChartSkeleton } from './shared/SkeletonLoaders'
import { EmptyTable } from './shared/EmptyStates'

const Expense = () => {
  const { currentBranch } = useAuth()
  const [dateFilter, setDateFilter] = useState('current-month')
  const [categoryFilter, setCategoryFilter] = useState('all')
  const [paymentModeFilter, setPaymentModeFilter] = useState('all')
  const [expenses, setExpenses] = useState([])
  const [categories, setCategories] = useState([])
  const [expenseSummary, setExpenseSummary] = useState([])
  const [loading, setLoading] = useState(true)
  const [showExpenseModal, setShowExpenseModal] = useState(false)
  const [showCategoryModal, setShowCategoryModal] = useState(false)
  const [editingExpense, setEditingExpense] = useState(null)
  const [editingCategory, setEditingCategory] = useState(null)
  const [addingCategory, setAddingCategory] = useState(false)
  const [expenseFormData, setExpenseFormData] = useState({
    name: '',
    category_id: '',
    amount: '',
    payment_mode: 'cash',
    expense_date: new Date().toISOString().split('T')[0],
    description: ''
  })
  const [categoryFormData, setCategoryFormData] = useState({
    name: '',
    description: ''
  })

  useEffect(() => {
    fetchCategories()
    fetchExpenses()
    fetchExpenseSummary()
  }, [dateFilter, categoryFilter, paymentModeFilter, currentBranch])

  // Listen for branch changes
  useEffect(() => {
    const handleBranchChange = () => {
      console.log('[Expense] Branch changed, refreshing data...')
      fetchCategories()
      fetchExpenses()
      fetchExpenseSummary()
    }
    
    window.addEventListener('branchChanged', handleBranchChange)
    return () => window.removeEventListener('branchChanged', handleBranchChange)
  }, [currentBranch])

  const fetchCategories = async () => {
    try {
      const response = await apiGet('/api/expenses/categories')
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      const data = await response.json()
      // Backend returns array directly
      setCategories(Array.isArray(data) ? data : (data.categories || []))
    } catch (error) {
      console.error('Error fetching expense categories:', error)
      setCategories([])
    }
  }

  const getDateRange = () => {
    const today = new Date()
    const firstDay = new Date(today.getFullYear(), today.getMonth(), 1)
    const lastDay = new Date(today.getFullYear(), today.getMonth() + 1, 0)
    
    switch (dateFilter) {
      case 'current-month':
        return {
          start_date: firstDay.toISOString().split('T')[0],
          end_date: lastDay.toISOString().split('T')[0]
        }
      case 'last-month':
        // Correctly handle year transition (e.g., if current month is January, last month is December of previous year)
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

  const fetchExpenses = async () => {
    try {
      setLoading(true)
      const params = new URLSearchParams()
      if (categoryFilter !== 'all') params.append('category_id', categoryFilter)
      if (paymentModeFilter !== 'all') params.append('payment_mode', paymentModeFilter)
      
      // Add date filtering
      const dateRange = getDateRange()
      if (dateRange.start_date) params.append('start_date', dateRange.start_date)
      if (dateRange.end_date) params.append('end_date', dateRange.end_date)
      
      const response = await apiGet(`/api/expenses?${params}`)
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      const data = await response.json()
      // Backend returns array directly
      setExpenses(Array.isArray(data) ? data : (data.expenses || []))
    } catch (error) {
      console.error('Error fetching expenses:', error)
      setExpenses([])
    } finally {
      setLoading(false)
    }
  }

  const fetchExpenseSummary = async () => {
    try {
      const dateRange = getDateRange()
      const params = new URLSearchParams()
      if (dateRange.start_date) params.append('start_date', dateRange.start_date)
      if (dateRange.end_date) params.append('end_date', dateRange.end_date)
      
      const response = await apiGet(`/api/expenses/summary?${params}`)
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      const data = await response.json()
      setExpenseSummary(data.summary || [])
    } catch (error) {
      console.error('Error fetching expense summary:', error)
      setExpenseSummary([])
    }
  }

  const handleAddExpense = () => {
    setEditingExpense(null)
    setExpenseFormData({
      name: '',
      category_id: '',
      amount: '',
      payment_mode: 'cash',
      expense_date: new Date().toISOString().split('T')[0],
      description: ''
    })
    setShowExpenseModal(true)
  }

  const handleEditExpense = async (expense) => {
    setEditingExpense(expense)
    setExpenseFormData({
      name: expense.name || '',
      category_id: expense.category_id || '',
      amount: expense.amount || '',
      payment_mode: expense.payment_mode || 'cash',
      expense_date: expense.expense_date ? expense.expense_date.split('T')[0] : new Date().toISOString().split('T')[0],
      description: expense.description || ''
    })
    setShowExpenseModal(true)
  }

  const handleSaveExpense = async () => {
    if (!expenseFormData.name.trim()) {
      showError('Expense name is required')
      return
    }
    if (!expenseFormData.category_id) {
      showError('Category is required')
      return
    }
    if (!expenseFormData.amount || parseFloat(expenseFormData.amount) <= 0) {
      showError('Valid amount is required')
      return
    }

    try {
      const url = editingExpense 
        ? `/api/expenses/${editingExpense.id}`
        : '/api/expenses'
      
      const requestData = {
        name: expenseFormData.name.trim(),
        category_id: expenseFormData.category_id,  // MongoDB ObjectId as string
        amount: parseFloat(expenseFormData.amount),
        payment_mode: expenseFormData.payment_mode,
        expense_date: expenseFormData.expense_date,
        description: expenseFormData.description.trim()
      }

      const response = editingExpense 
        ? await apiPut(url, requestData)
        : await apiPost(url, requestData)

      if (response.ok) {
        const data = await response.json()
        fetchExpenses()
        fetchExpenseSummary()
        setShowExpenseModal(false)
        setEditingExpense(null)
        setExpenseFormData({
          name: '',
          category_id: '',
          amount: '',
          payment_mode: 'cash',
          expense_date: new Date().toISOString().split('T')[0],
          description: ''
        })
        showError(data.message || (editingExpense ? 'Expense updated successfully!' : 'Expense added successfully!'))
      } else {
        const errorData = await response.json().catch(() => ({ error: 'Unknown error' }))
        showError(errorData.error || `Failed to save expense (Status: ${response.status})`)
      }
    } catch (error) {
      console.error('Error saving expense:', error)
      showError(`Error saving expense: ${error.message}`)
    }
  }

  const handleManageCategory = () => {
    setShowCategoryModal(true)
  }

  const handleAddCategory = () => {
    setEditingCategory(null)
    setAddingCategory(true)
    setCategoryFormData({ name: '', description: '' })
  }

  const handleEditCategory = (category) => {
    setEditingCategory(category)
    setAddingCategory(false)
    setCategoryFormData({
      name: category.name || '',
      description: category.description || ''
    })
  }

  const handleSaveCategory = async () => {
    if (!categoryFormData.name.trim()) {
      showError('Category name is required')
      return
    }

    try {
      const url = editingCategory 
        ? `/api/expenses/categories/${editingCategory.id}`
        : '/api/expenses/categories'
      
      const requestData = {
        name: categoryFormData.name.trim(),
        description: categoryFormData.description.trim()
      }

      const response = editingCategory 
        ? await apiPut(url, requestData)
        : await apiPost(url, requestData)

      if (response.ok) {
        const data = await response.json()
        fetchCategories()
        fetchExpenseSummary()
        setCategoryFormData({ name: '', description: '' })
        setEditingCategory(null)
        setAddingCategory(false)
        showError(data.message || (editingCategory ? 'Category updated successfully!' : 'Category added successfully!'))
      } else {
        const errorData = await response.json().catch(() => ({ error: 'Unknown error' }))
        showError(errorData.error || `Failed to save category (Status: ${response.status})`)
      }
    } catch (error) {
      console.error('Error saving category:', error)
      showError(`Error saving category: ${error.message}`)
    }
  }

  const handleDeleteCategory = async (categoryId) => {
    if (!window.confirm('Are you sure you want to delete this category?')) {
      return
    }
    try {
      const response = await apiDelete(`/api/expenses/categories/${categoryId}`)
      if (response.ok) {
        fetchCategories()
        fetchExpenseSummary()
        showSuccess('Category deleted successfully')
      } else {
        const errorData = await response.json().catch(() => ({ error: 'Unknown error' }))
        showError(errorData.error || 'Failed to delete category')
      }
    } catch (error) {
      console.error('Error deleting category:', error)
      showError(`Error deleting category: ${error.message}`)
    }
  }

  const handleDelete = async (expenseId) => {
    if (!window.confirm('Are you sure you want to delete this expense?')) {
      return
    }
    try {
      const response = await apiDelete(`/api/expenses/${expenseId}`)
      if (response.ok) {
        fetchExpenses()
        fetchExpenseSummary()
        showSuccess('Expense deleted successfully')
      } else {
        const errorData = await response.json().catch(() => ({ error: 'Unknown error' }))
        showError(errorData.error || 'Failed to delete expense')
      }
    } catch (error) {
      console.error('Error deleting expense:', error)
      showError(`Error deleting expense: ${error.message}`)
    }
  }

  const handleDownloadReport = () => {
    try {
      const csvContent = [
        ['No.', 'Expense Category', 'Mode of Payment', 'Expense Name', 'Expense Date', 'Expense Total'],
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
      const fileName = `expenses-report-${dateFilter}-${new Date().toISOString().split('T')[0]}.csv`
      a.download = fileName
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      window.URL.revokeObjectURL(url)
    } catch (error) {
      console.error('Error downloading report:', error)
      showError('Error downloading report. Please try again.')
    }
  }

  const totalExpense = expenses.reduce((sum, expense) => sum + (expense.amount || 0), 0)
  
  // Color palette for categories - matching Business Growth style
  const categoryColors = [
    '#d4a574', '#3b82f6', '#10b981', '#f59e0b', '#ef4444',
    '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16', '#f97316'
  ]

  // Format currency for display
  const formatCurrency = (value) => {
    return `Rs ${value.toLocaleString('en-IN')}`
  }

  // Custom tooltip for the chart
  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      return (
        <div style={{
          backgroundColor: 'white',
          border: '1px solid #e5e7eb',
          borderRadius: '8px',
          padding: '12px',
          boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)'
        }}>
          <p style={{ margin: 0, fontWeight: '600', color: '#1f2937' }}>
            {payload[0].payload.name}
          </p>
          <p style={{ margin: '4px 0 0 0', color: '#6b7280' }}>
            {formatCurrency(payload[0].value)}
          </p>
          <p style={{ margin: '4px 0 0 0', color: '#6b7280', fontSize: '12px' }}>
            {payload[0].payload.percentage}%
          </p>
        </div>
      )
    }
    return null
  }

  const renderDonutChart = () => {
    if (!expenseSummary || expenseSummary.length === 0) {
      return (
        <div style={{ 
          height: '300px', 
          display: 'flex', 
          flexDirection: 'column',
          alignItems: 'center', 
          justifyContent: 'center',
          color: '#9ca3af'
        }}>
          <p style={{ fontSize: '16px', margin: 0 }}>No expense data</p>
          <p style={{ fontSize: '14px', margin: '8px 0 0 0' }}>Add expenses to see breakdown</p>
        </div>
      )
    }

    const total = expenseSummary.reduce((sum, item) => sum + (item.total_amount || 0), 0)
    if (total === 0) {
      return (
        <div style={{ 
          height: '300px', 
          display: 'flex', 
          flexDirection: 'column',
          alignItems: 'center', 
          justifyContent: 'center',
          color: '#9ca3af'
        }}>
          <p style={{ fontSize: '16px', margin: 0 }}>Rs 0</p>
          <p style={{ fontSize: '14px', margin: '8px 0 0 0' }}>No expenses recorded</p>
        </div>
      )
    }

    // Transform data for Recharts Bar Chart
    const chartData = expenseSummary.map((item, index) => ({
      name: item.category_name,
      amount: item.total_amount,
      percentage: ((item.total_amount / total) * 100).toFixed(1),
      color: categoryColors[index % categoryColors.length]
    }))

    return (
      <ResponsiveContainer width="100%" height={300}>
        <BarChart
          data={chartData}
          margin={{ top: 20, right: 30, left: 20, bottom: 60 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis 
            dataKey="name" 
            angle={-45}
            textAnchor="end"
            height={80}
            tick={{ fontSize: 12 }}
            interval={0}
          />
          <YAxis 
            tick={{ fontSize: 12 }}
            tickFormatter={(value) => `₹${(value / 1000).toFixed(0)}k`}
          />
          <Tooltip 
            content={<CustomTooltip />}
            formatter={(value) => formatCurrency(value)}
          />
          <Legend />
          <Bar 
            dataKey="amount" 
            radius={[8, 8, 0, 0]}
          >
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    )
  }

  return (
    <PageTransition>
      <div className="expense-page">
        {/* Header */}
        <Header title="Expense" />

      <div className="expense-container">
        <div className="expense-layout">
          {/* Left Panel - Filters */}
          <div className="expense-filters-panel">
            <h2 className="panel-title">Expense List</h2>
            <div className="filters">
              <div className="filter-group">
                <label className="filter-label">Filter by date:</label>
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
                <label className="filter-label">Filter by category:</label>
                <select
                  className="filter-dropdown"
                  value={categoryFilter}
                  onChange={(e) => setCategoryFilter(e.target.value)}
                >
                  <option value="all">All</option>
                  {categories.map((cat) => (
                    <option key={cat.id} value={cat.id}>
                      {cat.name}
                    </option>
                  ))}
                </select>
              </div>
              <div className="filter-group">
                <label className="filter-label">Filter by mode of payment:</label>
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
            <div className="total-expense">
              <strong>Total Expense: ₹{totalExpense.toFixed(2)}</strong>
            </div>
          </div>

          {/* Right Panel - Summary and Actions */}
          <div className="expense-summary-panel">
            <div className="summary-actions">
              <button className="action-btn manage-btn" onClick={handleManageCategory}>
                Manage Expense Category
              </button>
              <button className="action-btn add-btn" onClick={handleAddExpense}>
                <FaPlus />
                Add New Expense
              </button>
              <button className="action-btn download-btn" onClick={handleDownloadReport}>
                <FaCloudDownloadAlt />
                Download Report
              </button>
            </div>
            <div className="chart-container">
              {renderDonutChart()}
            </div>
          </div>
        </div>

        {/* Expense Table */}
        <div className="expense-table-section">
          <div className="expense-table-header">
            <h3 className="expense-table-title">
              Expense Records
              {!loading && expenses.length > 0 && (
                <span className="expense-count-badge">{expenses.length} items</span>
              )}
            </h3>
          </div>
          <div className="table-container">
            <table className="expense-table">
              <thead>
                <tr>
                  <th>No.</th>
                  <th>Category</th>
                  <th>Payment</th>
                  <th>Expense Name</th>
                  <th>Date</th>
                  <th>Amount</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan="7" className="empty-row">Loading expenses...</td>
                  </tr>
                ) : expenses.length === 0 ? (
                  <tr>
                    <td colSpan="7" className="empty-row">No expenses found for the selected filters</td>
                  </tr>
                ) : (
                  expenses.map((expense, index) => (
                    <tr key={expense.id}>
                      <td style={{ fontWeight: 500, color: '#6b7280' }}>{index + 1}</td>
                      <td>
                        <span className={`category-badge ${(expense.category_name || '').toLowerCase().replace(/\s+/g, '-')}`}>
                          {expense.category_name || 'N/A'}
                        </span>
                      </td>
                      <td>
                        <span className={`payment-badge ${(expense.payment_mode || '').toLowerCase()}`}>
                          {expense.payment_mode || 'N/A'}
                        </span>
                      </td>
                      <td style={{ fontWeight: 500 }}>{expense.name}</td>
                      <td style={{ color: '#6b7280' }}>
                        {expense.expense_date ? new Date(expense.expense_date).toLocaleDateString('en-IN', {
                          day: '2-digit',
                          month: 'short',
                          year: 'numeric'
                        }) : 'N/A'}
                      </td>
                      <td>
                        <span className="expense-amount">₹{(expense.amount || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
                      </td>
                      <td>
                        <div className="action-icons">
                          <button
                            className="icon-btn edit-btn"
                            title="Edit expense"
                            onClick={() => handleEditExpense(expense)}
                          >
                            <FaEdit />
                          </button>
                          <button
                            className="icon-btn delete-btn"
                            title="Delete expense"
                            onClick={() => handleDelete(expense.id)}
                          >
                            <FaTrash />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Add/Edit Expense Modal */}
      {showExpenseModal && (
        <div className="modal-overlay" onClick={() => setShowExpenseModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2>{editingExpense ? 'Edit Expense' : 'Add New Expense'}</h2>
            <div className="form-group">
              <label>Expense Name *</label>
              <input
                type="text"
                value={expenseFormData.name}
                onChange={(e) => setExpenseFormData({ ...expenseFormData, name: e.target.value })}
                placeholder="Enter expense name"
                required
              />
            </div>
            <div className="form-group">
              <label>Category *</label>
              <select
                value={expenseFormData.category_id}
                onChange={(e) => setExpenseFormData({ ...expenseFormData, category_id: e.target.value })}
                required
              >
                <option value="">Select category</option>
                {categories.map((cat) => (
                  <option key={cat.id} value={cat.id}>
                    {cat.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label>Amount *</label>
              <input
                type="number"
                step="0.01"
                value={expenseFormData.amount}
                onChange={(e) => setExpenseFormData({ ...expenseFormData, amount: e.target.value })}
                placeholder="0.00"
                required
              />
            </div>
            <div className="form-group">
              <label>Payment Mode</label>
              <select
                value={expenseFormData.payment_mode}
                onChange={(e) => setExpenseFormData({ ...expenseFormData, payment_mode: e.target.value })}
              >
                <option value="cash">Cash</option>
                <option value="card">Card</option>
                <option value="upi">UPI</option>
              </select>
            </div>
            <div className="form-group">
              <label>Expense Date *</label>
              <DatePicker
                selected={expenseFormData.expense_date}
                onChange={(date) => setExpenseFormData({ ...expenseFormData, expense_date: date })}
                dateFormat="dd/MM/yyyy"
                maxDate={new Date()}
                placeholderText="Select expense date"
                required
              />
            </div>
            <div className="form-group">
              <label>Description</label>
              <textarea
                value={expenseFormData.description}
                onChange={(e) => setExpenseFormData({ ...expenseFormData, description: e.target.value })}
                placeholder="Enter expense description..."
                rows="3"
              />
            </div>
            <div className="modal-actions">
              <button className="btn-cancel" onClick={() => setShowExpenseModal(false)}>Cancel</button>
              <button className="btn-save" onClick={handleSaveExpense}>Save</button>
            </div>
          </div>
        </div>
      )}

      {/* Manage Expense Category Modal */}
      {showCategoryModal && (
        <div className="modal-overlay" onClick={() => setShowCategoryModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '700px' }}>
            <h2>Manage Expense Categories</h2>
            <div style={{ marginBottom: '20px' }}>
              {!addingCategory && !editingCategory && (
                <button 
                  className="btn-save" 
                  onClick={handleAddCategory}
                  style={{ marginBottom: '16px' }}
                >
                  <FaPlus /> Add New Category
                </button>
              )}
              {(addingCategory || editingCategory) && (
                <div className="form-group">
                  <label>Category Name *</label>
                  <input
                    type="text"
                    value={categoryFormData.name}
                    onChange={(e) => setCategoryFormData({ ...categoryFormData, name: e.target.value })}
                    placeholder="Enter category name"
                  />
                  <label style={{ marginTop: '12px' }}>Description</label>
                  <textarea
                    value={categoryFormData.description}
                    onChange={(e) => setCategoryFormData({ ...categoryFormData, description: e.target.value })}
                    placeholder="Enter category description..."
                    rows="2"
                  />
                  <div style={{ display: 'flex', gap: '8px', marginTop: '12px' }}>
                    <button className="btn-save" onClick={handleSaveCategory}>Save</button>
                    <button className="btn-cancel" onClick={() => {
                      setEditingCategory(null)
                      setAddingCategory(false)
                      setCategoryFormData({ name: '', description: '' })
                    }}>Cancel</button>
                  </div>
                </div>
              )}
            </div>
            <div style={{ maxHeight: '300px', overflowY: 'auto', border: '1px solid #e5e7eb', borderRadius: '6px', padding: '12px' }}>
              <h3 style={{ marginTop: 0, marginBottom: '12px', fontSize: '16px' }}>Existing Categories</h3>
              {categories.length === 0 ? (
                <p style={{ color: '#6b7280', fontSize: '14px' }}>No categories found</p>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {categories.map((cat) => (
                    <div key={cat.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px', background: '#f9fafb', borderRadius: '4px' }}>
                      <div>
                        <strong>{cat.name}</strong>
                        {cat.description && <p style={{ margin: '4px 0 0 0', fontSize: '12px', color: '#6b7280' }}>{cat.description}</p>}
                      </div>
                      <div style={{ display: 'flex', gap: '8px' }}>
                        <button 
                          className="icon-btn edit-btn" 
                          title="Edit"
                          onClick={() => handleEditCategory(cat)}
                          style={{ width: '32px', height: '32px' }}
                        >
                          <FaEdit />
                        </button>
                        <button
                          className="icon-btn delete-btn"
                          title="Delete"
                          onClick={() => handleDeleteCategory(cat.id)}
                          style={{ width: '32px', height: '32px' }}
                        >
                          <FaTrash />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
            <div className="modal-actions">
              <button className="btn-cancel" onClick={() => {
                setShowCategoryModal(false)
                setEditingCategory(null)
                setAddingCategory(false)
                setCategoryFormData({ name: '', description: '' })
              }}>Close</button>
            </div>
          </div>
        </div>
      )}
    </div>
    </PageTransition>
  )
}

export default Expense

