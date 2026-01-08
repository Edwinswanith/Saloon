/**
 * Dashboard Statistics Cards Component
 * 
 * A reusable React component for displaying KPI (Key Performance Indicator) cards.
 * This component displays 6 statistics cards in a responsive grid layout.
 * 
 * Features:
 * - 6 KPI Cards: Total Tax, Gross Revenue, Avg Bill Value, Transactions, Expenses, Deleted Bills
 * - Responsive grid layout (6 columns on desktop, 3 on tablet, 2 on mobile, 1 on small screens)
 * - Color-coded cards with light backgrounds
 * - Loading state support
 * - Currency formatting
 * 
 * Usage:
 * ```jsx
 * import DashboardStatsCards from './DashboardStatsCards'
 * 
 * <DashboardStatsCards 
 *   stats={statsObject}
 *   loading={false}
 *   formatCurrency={(amount) => `₹ ${amount.toLocaleString('en-IN')}`}
 * />
 * ```
 */

import React from 'react'
import './DashboardStatsCards.css'

const DashboardStatsCards = ({ 
  stats = {
    totalTax: 0,
    grossRevenue: 0,
    avgBillValue: 0,
    transactions: 0,
    expenses: 0,
    deletedBills: 0,
    deletedBillsAmount: 0,
  },
  loading = false,
  formatCurrency = (amount) => `₹ ${amount.toLocaleString('en-IN', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`
}) => {
  // Prepare statistics data
  const displayStats = [
    { label: 'Total Tax Collected', value: formatCurrency(stats.totalTax), color: 'blue' },
    { label: 'Gross Revenue', value: formatCurrency(stats.grossRevenue), color: 'green' },
    { label: 'Avg. Bill Value', value: formatCurrency(stats.avgBillValue), color: 'yellow' },
    { label: 'Transactions', value: stats.transactions.toString(), color: 'gray' },
    { label: 'Expenses', value: formatCurrency(stats.expenses), color: 'red' },
    { label: 'Deleted Bills', value: `${stats.deletedBills} (${formatCurrency(stats.deletedBillsAmount)})`, color: 'dark-red' },
  ]

  return (
    <div className="stats-cards-container">
      {loading ? (
        <div className="stats-grid">
          {[1, 2, 3, 4, 5, 6].map(i => (
            <div key={i} className="stat-card stat-loading">
              <div className="stat-value">Loading...</div>
              <div className="stat-label">Loading...</div>
            </div>
          ))}
        </div>
      ) : (
        <div className="stats-grid">
          {displayStats.map((stat, index) => (
            <div key={index} className={`stat-card stat-${stat.color}`}>
              <div className="stat-value">{stat.value}</div>
              <div className="stat-label">{stat.label}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default DashboardStatsCards

