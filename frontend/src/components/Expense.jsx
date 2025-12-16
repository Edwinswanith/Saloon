import React, { useState, useEffect } from 'react'
import {
  FaBars,
  FaBell,
  FaUser,
  FaCloudDownloadAlt,
  FaEdit,
  FaTrash,
  FaPlus,
} from 'react-icons/fa'
import './Expense.css'
import { API_BASE_URL } from '../config'

const Expense = () => {
  const [dateFilter, setDateFilter] = useState('current-month')
  const [categoryFilter, setCategoryFilter] = useState('all')
  const [paymentModeFilter, setPaymentModeFilter] = useState('all')
  const [expenses, setExpenses] = useState([])
  const [categories, setCategories] = useState([])
  const [expenseSummary, setExpenseSummary] = useState([])
  const [loading, setLoading] = useState(true)
  const [hoveredCategory, setHoveredCategory] = useState(null)
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
  }, [dateFilter, categoryFilter, paymentModeFilter])

  const fetchCategories = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/expenses/categories`)
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
      
      const response = await fetch(`${API_BASE_URL}/api/expenses?${params}`)
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
      
      const response = await fetch(`${API_BASE_URL}/api/expenses/summary?${params}`)
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
      alert('Expense name is required')
      return
    }
    if (!expenseFormData.category_id) {
      alert('Category is required')
      return
    }
    if (!expenseFormData.amount || parseFloat(expenseFormData.amount) <= 0) {
      alert('Valid amount is required')
      return
    }

    try {
      const url = editingExpense 
        ? `${API_BASE_URL}/api/expenses/${editingExpense.id}`
        : `${API_BASE_URL}/api/expenses`
      const method = editingExpense ? 'PUT' : 'POST'

      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: expenseFormData.name.trim(),
          category_id: expenseFormData.category_id,  // MongoDB ObjectId as string
          amount: parseFloat(expenseFormData.amount),
          payment_mode: expenseFormData.payment_mode,
          expense_date: expenseFormData.expense_date,
          description: expenseFormData.description.trim()
        }),
      })

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
        alert(data.message || (editingExpense ? 'Expense updated successfully!' : 'Expense added successfully!'))
      } else {
        const errorData = await response.json().catch(() => ({ error: 'Unknown error' }))
        alert(errorData.error || `Failed to save expense (Status: ${response.status})`)
      }
    } catch (error) {
      console.error('Error saving expense:', error)
      alert(`Error saving expense: ${error.message}`)
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
      alert('Category name is required')
      return
    }

    try {
      const url = editingCategory 
        ? `${API_BASE_URL}/api/expenses/categories/${editingCategory.id}`
        : `${API_BASE_URL}/api/expenses/categories`
      const method = editingCategory ? 'PUT' : 'POST'

      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: categoryFormData.name.trim(),
          description: categoryFormData.description.trim()
        }),
      })

      if (response.ok) {
        const data = await response.json()
        fetchCategories()
        fetchExpenseSummary()
        setCategoryFormData({ name: '', description: '' })
        setEditingCategory(null)
        setAddingCategory(false)
        alert(data.message || (editingCategory ? 'Category updated successfully!' : 'Category added successfully!'))
      } else {
        const errorData = await response.json().catch(() => ({ error: 'Unknown error' }))
        alert(errorData.error || `Failed to save category (Status: ${response.status})`)
      }
    } catch (error) {
      console.error('Error saving category:', error)
      alert(`Error saving category: ${error.message}`)
    }
  }

  const handleDeleteCategory = async (categoryId) => {
    if (!window.confirm('Are you sure you want to delete this category?')) {
      return
    }
    try {
      const response = await fetch(`${API_BASE_URL}/api/expenses/categories/${categoryId}`, {
        method: 'DELETE',
      })
      if (response.ok) {
        fetchCategories()
        fetchExpenseSummary()
        alert('Category deleted successfully')
      } else {
        const errorData = await response.json().catch(() => ({ error: 'Unknown error' }))
        alert(errorData.error || 'Failed to delete category')
      }
    } catch (error) {
      console.error('Error deleting category:', error)
      alert(`Error deleting category: ${error.message}`)
    }
  }

  const handleDelete = async (expenseId) => {
    if (!window.confirm('Are you sure you want to delete this expense?')) {
      return
    }
    try {
      const response = await fetch(`${API_BASE_URL}/api/expenses/${expenseId}`, {
        method: 'DELETE',
      })
      if (response.ok) {
        fetchExpenses()
        fetchExpenseSummary()
        alert('Expense deleted successfully')
      } else {
        const errorData = await response.json().catch(() => ({ error: 'Unknown error' }))
        alert(errorData.error || 'Failed to delete expense')
      }
    } catch (error) {
      console.error('Error deleting expense:', error)
      alert(`Error deleting expense: ${error.message}`)
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
      alert('Error downloading report. Please try again.')
    }
  }

  const totalExpense = expenses.reduce((sum, expense) => sum + (expense.amount || 0), 0)
  
  // Color palette for categories
  const categoryColors = [
    '#d4a574', '#3b82f6', '#10b981', '#f59e0b', '#ef4444',
    '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16', '#f97316'
  ]

  const renderDonutChart = () => {
    if (!expenseSummary || expenseSummary.length === 0) {
      return (
        <>
          <svg width="200" height="200" viewBox="0 0 200 200">
            <circle
              cx="100"
              cy="100"
              r="80"
              fill="none"
              stroke="#e5e7eb"
              strokeWidth="40"
            />
          </svg>
          <div className="chart-center">
            <div className="chart-amount">₹0</div>
            <div className="chart-label">No data</div>
          </div>
        </>
      )
    }

    const total = expenseSummary.reduce((sum, item) => sum + (item.total_amount || 0), 0)
    if (total === 0) {
      return (
        <>
          <svg width="200" height="200" viewBox="0 0 200 200">
            <circle
              cx="100"
              cy="100"
              r="80"
              fill="none"
              stroke="#e5e7eb"
              strokeWidth="40"
            />
          </svg>
          <div className="chart-center">
            <div className="chart-amount">₹0</div>
            <div className="chart-label">No data</div>
          </div>
        </>
      )
    }

    const circumference = 2 * Math.PI * 80
    let accumulatedLength = 0
    const hoveredItem = hoveredCategory 
      ? expenseSummary.find(item => item.category_name === hoveredCategory)
      : null

    return (
      <>
        <svg width="200" height="200" viewBox="0 0 200 200">
          {expenseSummary.map((item, index) => {
            const percentage = item.total_amount / total
            const dashLength = circumference * percentage
            const isHovered = hoveredCategory === item.category_name
            const color = categoryColors[index % categoryColors.length]
            
            const strokeDasharray = `${dashLength} ${circumference}`
            const strokeDashoffset = -accumulatedLength
            
            accumulatedLength += dashLength
            
            return (
              <circle
                key={item.category_name}
                cx="100"
                cy="100"
                r="80"
                fill="none"
                stroke={color}
                strokeWidth={isHovered ? "45" : "40"}
                strokeDasharray={strokeDasharray}
                strokeDashoffset={strokeDashoffset}
                transform="rotate(-90 100 100)"
                style={{ 
                  transition: 'all 0.3s ease',
                  cursor: 'pointer',
                  opacity: hoveredCategory && !isHovered ? 0.5 : 1
                }}
                onMouseEnter={() => setHoveredCategory(item.category_name)}
                onMouseLeave={() => setHoveredCategory(null)}
              />
            )
          })}
        </svg>
        <div className="chart-center">
          <div className="chart-amount">
            ₹{hoveredItem ? hoveredItem.total_amount.toFixed(0) : total.toFixed(0)}
          </div>
          <div className="chart-label">
            {hoveredItem ? hoveredItem.category_name : 'Total'}
          </div>
        </div>
      </>
    )
  }

  return (
    <div className="expense-page">
      {/* Header */}
      <header className="expense-header">
        <div className="header-left">
          <button className="menu-icon">
            <FaBars />
          </button>
          <h1 className="header-title">Expense</h1>
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
              <div className="donut-chart">
                {renderDonutChart()}
              </div>
              <div className="chart-legend">
                {expenseSummary.length === 0 ? (
                  <div className="legend-item">
                    <span className="legend-color" style={{ background: '#e5e7eb' }}></span>
                    <span className="legend-label">No expenses</span>
                  </div>
                ) : (
                  expenseSummary.map((item, index) => {
                    const isHovered = hoveredCategory === item.category_name
                    const total = expenseSummary.reduce((sum, i) => sum + (i.total_amount || 0), 0)
                    return (
                      <div 
                        key={item.category_name} 
                        className="legend-item"
                        style={{ 
                          opacity: hoveredCategory && !isHovered ? 0.5 : 1,
                          cursor: 'pointer',
                          transition: 'all 0.3s ease'
                        }}
                        onMouseEnter={() => setHoveredCategory(item.category_name)}
                        onMouseLeave={() => setHoveredCategory(null)}
                      >
                        <span 
                          className="legend-color" 
                          style={{ 
                            background: categoryColors[index % categoryColors.length],
                            transform: isHovered ? 'scale(1.2)' : 'scale(1)',
                            transition: 'transform 0.3s ease'
                          }}
                        ></span>
                        <span className="legend-label">
                          {item.category_name} ({((item.total_amount / total) * 100).toFixed(1)}%)
                        </span>
                      </div>
                    )
                  })
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Expense Table */}
        <div className="expense-table-section">
          <div className="table-container">
            <table className="expense-table">
              <thead>
                <tr>
                  <th>No.</th>
                  <th>Expense Category</th>
                  <th>Mode of payment</th>
                  <th>Expense Name</th>
                  <th>Expense Date</th>
                  <th>Expense Total</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan="7" className="empty-row">Loading...</td>
                  </tr>
                ) : expenses.length === 0 ? (
                  <tr>
                    <td colSpan="7" className="empty-row">No expenses found</td>
                  </tr>
                ) : (
                  expenses.map((expense, index) => (
                    <tr key={expense.id}>
                      <td>{index + 1}</td>
                      <td>{expense.category_name || 'N/A'}</td>
                      <td>{expense.payment_mode || 'N/A'}</td>
                      <td>{expense.name}</td>
                      <td>{expense.expense_date ? expense.expense_date.split('T')[0] : 'N/A'}</td>
                      <td>₹{(expense.amount || 0).toFixed(2)}</td>
                      <td>
                        <div className="action-icons">
                          <button 
                            className="icon-btn edit-btn" 
                            title="Edit"
                            onClick={() => handleEditExpense(expense)}
                          >
                            <FaEdit />
                          </button>
                          <button
                            className="icon-btn delete-btn"
                            title="Delete"
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
              <input
                type="date"
                value={expenseFormData.expense_date}
                onChange={(e) => setExpenseFormData({ ...expenseFormData, expense_date: e.target.value })}
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
  )
}

export default Expense

