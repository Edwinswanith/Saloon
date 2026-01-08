import React, { useState, useEffect } from 'react'
import { FaCalendarAlt, FaCloudDownloadAlt, FaEdit, FaTrash } from 'react-icons/fa'
import './CashRegister.css'
import { API_BASE_URL } from '../config'
import { useAuth } from '../contexts/AuthContext'

const CashRegister = () => {
  const { currentBranch } = useAuth()
  const [viewMode, setViewMode] = useState('daily')
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0])
  const [transactions, setTransactions] = useState([])
  const [summary, setSummary] = useState({ totalIn: 0, totalOut: 0, netFlow: 0 })
  const [loading, setLoading] = useState(true)
  const [showAddModal, setShowAddModal] = useState(false)
  const [transactionType, setTransactionType] = useState('in')
  const [formData, setFormData] = useState({
    amount: '',
    reason: '',
    notes: '',
  })

  useEffect(() => {
    fetchTransactions()
    fetchSummary()
  }, [selectedDate, viewMode, currentBranch])

  // Listen for branch changes
  useEffect(() => {
    const handleBranchChange = () => {
      console.log('[CashRegister] Branch changed, refreshing transactions...')
      fetchTransactions()
      fetchSummary()
    }
    
    window.addEventListener('branchChanged', handleBranchChange)
    return () => window.removeEventListener('branchChanged', handleBranchChange)
  }, [currentBranch])

  const fetchTransactions = async () => {
    try {
      setLoading(true)
      const params = new URLSearchParams({ date: selectedDate })
      const response = await fetch(`${API_BASE_URL}/api/cash/transactions?${params}`)
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const data = await response.json()
      setTransactions(data.transactions || data || [])
    } catch (error) {
      console.error('Error fetching transactions:', error)
      setTransactions([])
    } finally {
      setLoading(false)
    }
  }

  const fetchSummary = async () => {
    try {
      const params = new URLSearchParams({ date: selectedDate })
      const response = await fetch(`${API_BASE_URL}/api/cash/summary?${params}`)
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const data = await response.json()
      setSummary({
        totalIn: data.total_in || data.cash_in || 0,
        totalOut: data.total_out || data.cash_out || 0,
        netFlow: data.net_flow || data.net_cash || 0,
      })
    } catch (error) {
      console.error('Error fetching summary:', error)
      setSummary({ totalIn: 0, totalOut: 0, netFlow: 0 })
    }
  }

  const handleAddTransaction = async (e) => {
    e.preventDefault()
    try {
      const endpoint = transactionType === 'in' ? '/api/cash/in' : '/api/cash/out'
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          amount: parseFloat(formData.amount),
          reason: formData.reason,
          notes: formData.notes,
          transaction_date: selectedDate,
        }),
      })
      if (response.ok) {
        setShowAddModal(false)
        setFormData({ amount: '', reason: '', notes: '' })
        fetchTransactions()
        fetchSummary()
      } else {
        alert('Failed to add transaction')
      }
    } catch (error) {
      console.error('Error adding transaction:', error)
      alert('Error adding transaction')
    }
  }

  const handleDelete = async (transactionId) => {
    if (!window.confirm('Are you sure you want to delete this transaction?')) {
      return
    }
    try {
      const response = await fetch(`${API_BASE_URL}/api/cash/transactions/${transactionId}`, {
        method: 'DELETE',
      })
      if (response.ok) {
        fetchTransactions()
        fetchSummary()
      } else {
        alert('Failed to delete transaction')
      }
    } catch (error) {
      console.error('Error deleting transaction:', error)
      alert('Error deleting transaction')
    }
  }

  const formatDate = (dateString) => {
    const date = new Date(dateString)
    const day = String(date.getDate()).padStart(2, '0')
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const year = date.getFullYear()
    return `${day}-${month}-${year}`
  }

  const formatDisplayDate = (dateString) => {
    const date = new Date(dateString)
    const day = date.getDate()
    const monthNames = [
      'Jan',
      'Feb',
      'Mar',
      'Apr',
      'May',
      'Jun',
      'Jul',
      'Aug',
      'Sep',
      'Oct',
      'Nov',
      'Dec',
    ]
    const month = monthNames[date.getMonth()]
    const year = date.getFullYear()
    return `${day} ${month}, ${year}`
  }

  return (
    <div className="cash-register-page">
      <div className="cash-register-container">
        {/* Control Panel / Filters */}
        <div className="control-panel">
          <div className="view-toggle">
            <button
              className={`toggle-btn ${viewMode === 'daily' ? 'active' : ''}`}
              onClick={() => setViewMode('daily')}
            >
              Daily
            </button>
            <button
              className={`toggle-btn ${viewMode === 'monthly' ? 'active' : ''}`}
              onClick={() => setViewMode('monthly')}
            >
              Monthly
            </button>
          </div>

          <div className="date-filter">
            <label className="date-label">Date:</label>
            <div className="date-input-wrapper">
              <input
                type="date"
                className="date-picker"
                value={selectedDate}
                onChange={(e) => setSelectedDate(e.target.value)}
              />
              <span className="date-display">{formatDate(selectedDate)}</span>
              <span className="calendar-icon"><FaCalendarAlt /></span>
            </div>
          </div>

          <button className="download-btn">
            <span className="cloud-icon"><FaCloudDownloadAlt /></span>
            Download Report
          </button>
        </div>

        {/* Cash Flow Summary Cards */}
        <div className="summary-cards">
          <div className="summary-card cash-in">
            <div className="card-label">Total Cash In</div>
            <div className="card-value">₹{summary.totalIn.toFixed(2)}</div>
          </div>

          <div className="summary-card cash-out">
            <div className="card-label">Total Cash Out</div>
            <div className="card-value">₹{summary.totalOut.toFixed(2)}</div>
          </div>

          <div className="summary-card net-flow">
            <div className="card-label">Net Cash Flow</div>
            <div className="card-value">₹{summary.netFlow.toFixed(2)}</div>
          </div>

          <div className="action-buttons-group">
            <button
              className="action-btn add-cash"
              onClick={() => {
                setTransactionType('in')
                setShowAddModal(true)
              }}
            >
              <span className="arrow-icon">↑</span>
              Add Cash In
            </button>
            <button
              className="action-btn remove-cash"
              onClick={() => {
                setTransactionType('out')
                setShowAddModal(true)
              }}
            >
              <span className="arrow-icon">↓</span>
              Remove Cash Out
            </button>
          </div>
        </div>

        {/* Transactions Section */}
        <div className="transactions-section">
          <h2 className="transactions-title">
            Transactions for {formatDisplayDate(selectedDate)}
          </h2>

          <div className="table-container">
            <table className="transactions-table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Time</th>
                  <th>Type</th>
                  <th>Reason / Notes</th>
                  <th>Amount</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan="6" className="empty-message">Loading...</td>
                  </tr>
                ) : transactions.length === 0 ? (
                  <tr>
                    <td colSpan="6" className="empty-message">
                      No transactions recorded for this period.
                    </td>
                  </tr>
                ) : (
                  transactions.map((transaction) => (
                    <tr key={transaction.id}>
                      <td>{transaction.transaction_date}</td>
                      <td>{transaction.transaction_time || 'N/A'}</td>
                      <td>
                        <span className={`type-badge ${transaction.transaction_type}`}>
                          {transaction.transaction_type === 'in' ? 'Cash In' : 'Cash Out'}
                        </span>
                      </td>
                      <td>{transaction.reason || 'N/A'}</td>
                      <td className={transaction.transaction_type === 'in' ? 'amount-in' : 'amount-out'}>
                        ₹{transaction.amount.toFixed(2)}
                      </td>
                      <td>
                        <div className="action-icons">
                          <button className="icon-btn edit-btn" title="Edit">
                            <FaEdit />
                          </button>
                          <button
                            className="icon-btn delete-btn"
                            title="Delete"
                            onClick={() => handleDelete(transaction.id)}
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

      {/* Add Transaction Modal */}
      {showAddModal && (
        <div className="modal-overlay" onClick={() => setShowAddModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>{transactionType === 'in' ? 'Add Cash In' : 'Add Cash Out'}</h2>
              <button className="close-btn" onClick={() => setShowAddModal(false)}>×</button>
            </div>
            <form onSubmit={handleAddTransaction}>
              <div className="form-group">
                <label>Amount *</label>
                <input
                  type="number"
                  step="0.01"
                  required
                  value={formData.amount}
                  onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label>Reason *</label>
                <input
                  type="text"
                  required
                  value={formData.reason}
                  onChange={(e) => setFormData({ ...formData, reason: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label>Notes</label>
                <textarea
                  value={formData.notes}
                  onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                  rows="3"
                />
              </div>
              <div className="modal-actions">
                <button type="button" onClick={() => setShowAddModal(false)}>Cancel</button>
                <button type="submit">Add Transaction</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

export default CashRegister

