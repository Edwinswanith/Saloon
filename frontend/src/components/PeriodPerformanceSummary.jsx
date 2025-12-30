import React, { useState } from 'react'
import {
  FaBars,
  FaUser,
  FaLayerGroup,
  FaMoneyBillWave,
  FaExclamationTriangle,
  FaChartLine,
} from 'react-icons/fa'
import './PeriodPerformanceSummary.css'
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
  Legend,
} from 'recharts'

const PeriodPerformanceSummary = ({ setActivePage }) => {
  const [dateRange, setDateRange] = useState('Last Month')

  // Sample data - replace with actual data from your backend
  const summaryMetrics = {
    totalServiceValue: 256082,
    grossRevenue: 225485,
    totalExpenses: 136829,
    netProfit: 88656,
  }

  const revenueSourcesData = [
    { category: 'Services', value: 180000, percentage: 70 },
    { category: 'Products', value: 45200, percentage: 18 },
    { category: 'Packages', value: 20882, percentage: 8 },
    { category: 'Memberships', value: 10000, percentage: 4 },
  ]

  const paymentDistributionData = [
    { method: 'UPI', amount: 176454 },
    { method: 'Cash', amount: 49031 },
    { method: 'Credit/Debit Card', amount: 0 },
    { method: 'Prepaid/Loyalty', amount: 30597 },
  ]

  const expensesData = [
    { category: 'Salaries', amount: 80000 },
    { category: 'Rent', amount: 35000 },
    { category: 'Product Costs', amount: 15000 },
    { category: 'Utilities & Misc', amount: 6829 },
  ]

  const deductionsData = [
    { category: 'Total Discounts Given', amount: 15500 },
  ]

  const handleBackToReports = () => {
    if (setActivePage) {
      setActivePage('reports-analytics')
    }
  }

  const formatCurrency = (value) => {
    return `₹${value.toLocaleString('en-IN')}`
  }

  const getTotalRevenueSources = () => {
    return revenueSourcesData.reduce((sum, item) => sum + item.value, 0)
  }

  const getRevenuePercentage = (value) => {
    const total = getTotalRevenueSources()
    return ((value / total) * 100).toFixed(1)
  }

  return (
    <div className="period-performance-page">
      {/* Header */}
      <header className="period-performance-header">
        <div className="header-left">
          <button className="menu-icon">
            <FaBars />
          </button>
          <h1 className="header-title">Period Performance Summary</h1>
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

      <div className="period-performance-container">
        <div className="period-performance-content">
          {/* Back Button and Date Range */}
          <div className="controls-section">
            <button className="back-button" onClick={handleBackToReports}>
              ← Back to Reports Hub
            </button>
            <div className="date-range-section">
              <label className="date-range-label">DATE RANGE</label>
              <select
                className="date-range-select"
                value={dateRange}
                onChange={(e) => setDateRange(e.target.value)}
              >
                <option>Last Week</option>
                <option>Last Month</option>
                <option>Last 3 Months</option>
                <option>Last 6 Months</option>
                <option>Last Year</option>
                <option>Custom Range</option>
              </select>
            </div>
          </div>

          {/* Top Summary Metrics */}
          <div className="summary-metrics-grid">
            <div className="metric-card purple">
              <div className="metric-icon">
                <FaLayerGroup />
              </div>
              <div className="metric-info">
                <h2 className="metric-value">
                  {formatCurrency(summaryMetrics.totalServiceValue)}
                </h2>
                <p className="metric-label">TOTAL SERVICE VALUE</p>
              </div>
            </div>

            <div className="metric-card green">
              <div className="metric-icon">
                <FaMoneyBillWave />
              </div>
              <div className="metric-info">
                <h2 className="metric-value">
                  {formatCurrency(summaryMetrics.grossRevenue)}
                </h2>
                <p className="metric-label">GROSS REVENUE</p>
              </div>
            </div>

            <div className="metric-card red">
              <div className="metric-icon">
                <FaExclamationTriangle />
              </div>
              <div className="metric-info">
                <h2 className="metric-value">
                  {formatCurrency(summaryMetrics.totalExpenses)}
                </h2>
                <p className="metric-label">TOTAL EXPENSES</p>
              </div>
            </div>

            <div className="metric-card profit">
              <div className="metric-icon">
                <FaChartLine />
              </div>
              <div className="metric-info">
                <h2 className="metric-value">
                  {formatCurrency(summaryMetrics.netProfit)}
                </h2>
                <p className="metric-label">NET PROFIT</p>
              </div>
            </div>
          </div>

          {/* Main Content Grid */}
          <div className="content-grid">
            {/* Revenue Sources */}
            <div className="content-card">
              <h2 className="card-title">Revenue Sources</h2>
              <div className="revenue-chart">
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={revenueSourcesData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ category, percentage }) => `${category}: ${percentage}%`}
                      outerRadius={100}
                      innerRadius={60}
                      fill="#8884d8"
                      dataKey="value"
                      paddingAngle={2}
                    >
                      {revenueSourcesData.map((entry, index) => {
                        const colors = ['#1e40af', '#3b82f6', '#60a5fa', '#93c5fd']
                        return <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
                      })}
                    </Pie>
                    <Tooltip 
                      contentStyle={{
                        backgroundColor: 'white',
                        border: '1px solid #e5e7eb',
                        borderRadius: '8px',
                        padding: '12px',
                        boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)'
                      }}
                      formatter={(value) => [formatCurrency(value), '']}
                    />
                    <Legend 
                      wrapperStyle={{ paddingTop: '20px' }}
                      iconType="circle"
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Payment Distribution */}
            <div className="content-card">
              <h2 className="card-title">Payment Distribution</h2>
              <div className="payment-list">
                {paymentDistributionData.map((payment, index) => (
                  <div key={index} className="payment-item">
                    <span className="payment-method">{payment.method}</span>
                    <span className="payment-amount">
                      {formatCurrency(payment.amount)}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Expenses & Deductions */}
            <div className="content-card">
              <h2 className="card-title">Expenses & Deductions</h2>
              <div className="expenses-section">
                <h3 className="subsection-title">EXPENSES</h3>
                <div className="expenses-list">
                  {expensesData.map((expense, index) => (
                    <div key={index} className="expense-item">
                      <span className="expense-label">{expense.category}</span>
                      <span className="expense-amount">
                        {formatCurrency(expense.amount)}
                      </span>
                    </div>
                  ))}
                </div>
                <h3 className="subsection-title">DEDUCTIONS</h3>
                <div className="deductions-list">
                  {deductionsData.map((deduction, index) => (
                    <div key={index} className="deduction-item">
                      <span className="deduction-label">
                        {deduction.category}
                      </span>
                      <span className="deduction-amount">
                        {formatCurrency(deduction.amount)}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default PeriodPerformanceSummary
