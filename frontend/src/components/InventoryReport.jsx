import React, { useState } from 'react'
import {
  FaBars,
  FaBell,
  FaUser,
  FaQuestionCircle,
  FaArrowLeft,
  FaFileExcel,
  FaShoppingCart,
  FaShoppingBasket,
  FaBoxOpen,
  FaChartLine,
  FaSearch,
} from 'react-icons/fa'
import './InventoryReport.css'

const InventoryReport = ({ setActivePage }) => {
  const [dateFilter, setDateFilter] = useState('current-month')
  const [searchQuery, setSearchQuery] = useState('')
  const [currentPage, setCurrentPage] = useState(1)

  const handleBackToReports = () => {
    if (setActivePage) {
      setActivePage('reports')
    }
  }

  const summaryCards = [
    {
      id: 1,
      title: 'TOTAL PURCHASES',
      value: 0,
      description: 'Value of New Stock Added',
      icon: <FaShoppingCart />,
      color: 'green',
    },
    {
      id: 2,
      title: 'RETAIL COST (SOLD)',
      value: 0,
      description: 'Cost of Goods Sold',
      icon: <FaShoppingBasket />,
      color: 'blue',
    },
    {
      id: 3,
      title: 'SERVICE CONSUMPTION',
      value: 36,
      description: 'Internal Usage Cost',
      icon: <FaBoxOpen />,
      color: 'orange',
    },
    {
      id: 4,
      title: 'TOTAL STOCK VALUE',
      value: 291933,
      description: 'Value of Assets (Closing)',
      icon: <FaChartLine />,
      color: 'purple',
    },
  ]

  const inventoryItems = [
    {
      id: 1,
      product: 'Hair Loreal Shampoo',
      unit: '500 milliliter',
      opening: 12,
      in: '-',
      retail: '-',
      internal: '-',
      consCost: '-',
      closing: 12,
      value: 6000,
    },
    {
      id: 2,
      product: 'Kanpeki SPF 40',
      unit: '500 milliliter',
      opening: 39.8,
      in: '-',
      retail: '-',
      internal: '-',
      consCost: '-',
      closing: 39.8,
      value: 20298,
    },
    {
      id: 3,
      product: 'jeannot eye contour',
      unit: '501 gram',
      opening: 4,
      in: '-',
      retail: '-',
      internal: 0.02,
      consCost: 36,
      closing: 3.98,
      value: 5964,
    },
    {
      id: 4,
      product: 'Kerafine serum',
      unit: '500 milliliter',
      opening: 47.19,
      in: '-',
      retail: '-',
      internal: '-',
      consCost: '-',
      closing: 47.19,
      value: 47188,
    },
    {
      id: 5,
      product: 'Moroccanoil',
      unit: 'Units',
      opening: 41,
      in: '-',
      retail: '-',
      internal: '-',
      consCost: '-',
      closing: 41,
      value: 155800,
    },
    {
      id: 6,
      product: 'BOTOPLUS POST SHAMPOO 250ML',
      unit: 'Units',
      opening: 4,
      in: '-',
      retail: '-',
      internal: '-',
      consCost: '-',
      closing: 4,
      value: 5196,
    },
    {
      id: 7,
      product: 'BOTOPLUS POST HAIR MASK 250GM',
      unit: 'Units',
      opening: 14,
      in: '-',
      retail: '-',
      internal: '-',
      consCost: '-',
      closing: 14,
      value: 18186,
    },
    {
      id: 8,
      product: 'BOTOPLUS HAIR SEERUM 100 ML',
      unit: 'Units',
      opening: 3,
      in: '-',
      retail: '-',
      internal: '-',
      consCost: '-',
      closing: 3,
      value: 2997,
    },
    {
      id: 9,
      product: 'FACE WASH NEEM WARONES',
      unit: 'Units',
      opening: 22,
      in: '-',
      retail: '-',
      internal: '-',
      consCost: '-',
      closing: 22,
      value: 4378,
    },
    {
      id: 10,
      product: 'FACE WASH VIT C',
      unit: 'Units',
      opening: 8,
      in: '-',
      retail: '-',
      internal: '-',
      consCost: '-',
      closing: 8,
      value: 1592,
    },
    {
      id: 11,
      product: 'FACE WASH KUMKUMATHI WARONES',
      unit: 'Units',
      opening: 2,
      in: '-',
      retail: '-',
      internal: '-',
      consCost: '-',
      closing: 2,
      value: 398,
    },
    {
      id: 12,
      product: 'WARONES SKIN BRIGHTEING',
      unit: 'Units',
      opening: 3,
      in: '-',
      retail: '-',
      internal: '-',
      consCost: '-',
      closing: 3,
      value: 597,
    },
    {
      id: 13,
      product: 'MOISTURIZER VITAMIN C WARONES',
      unit: 'Units',
      opening: 2,
      in: '-',
      retail: '-',
      internal: '-',
      consCost: '-',
      closing: 2,
      value: 398,
    },
    {
      id: 14,
      product: 'FACE SEERUM TEA TREE WARONES',
      unit: 'Units',
      opening: 2,
      in: '-',
      retail: '-',
      internal: '-',
      consCost: '-',
      closing: 2,
      value: 398,
    },
    {
      id: 15,
      product: 'SPF 40 WARONES',
      unit: 'Units',
      opening: 2,
      in: '-',
      retail: '-',
      internal: '-',
      consCost: '-',
      closing: 2,
      value: 398,
    },
    {
      id: 16,
      product: 'FACE & BODY GEL WARONES',
      unit: 'Units',
      opening: 3,
      in: '-',
      retail: '-',
      internal: '-',
      consCost: '-',
      closing: 3,
      value: 597,
    },
    {
      id: 17,
      product: 'CLEAR IN ENHANCING FACE WASH',
      unit: 'Units',
      opening: 2,
      in: '-',
      retail: '-',
      internal: '-',
      consCost: '-',
      closing: 2,
      value: 398,
    },
    {
      id: 18,
      product: 'EYE COUNTOUR LOTUS',
      unit: 'Units',
      opening: 2,
      in: '-',
      retail: '-',
      internal: '-',
      consCost: '-',
      closing: 2,
      value: 1150,
    },
    {
      id: 19,
      product: 'ANTI AGEING CREME LOTUS PROFESSIONAL',
      unit: 'Units',
      opening: 3,
      in: '-',
      retail: '-',
      internal: '-',
      consCost: '-',
      closing: 3,
      value: 2895,
    },
    {
      id: 20,
      product: 'ANTI AGEING SEERUM',
      unit: 'Units',
      opening: 1,
      in: '-',
      retail: '-',
      internal: '-',
      consCost: '-',
      closing: 1,
      value: 995,
    },
  ]

  const totalItems = 41
  const itemsPerPage = 20
  const startItem = (currentPage - 1) * itemsPerPage + 1
  const endItem = Math.min(currentPage * itemsPerPage, totalItems)

  return (
    <div className="inventory-report-page">
      {/* Header */}
      <header className="inventory-report-header">
        <div className="header-left">
          <button className="menu-icon">
            <FaBars />
          </button>
          <h1 className="header-title">Inventory Report</h1>
        </div>
        <div className="header-right">
          <div className="logo-box">
            <span className="logo-text">HAIR STUDIO</span>
          </div>
          <button className="header-icon bell-icon">
            <FaBell />
          </button>
          <button className="header-icon help-icon">
            <FaQuestionCircle />
          </button>
          <button className="header-icon user-icon">
            <FaUser />
          </button>
        </div>
      </header>

      <div className="inventory-report-container">
        {/* Back Button */}
        <button className="back-button" onClick={handleBackToReports}>
          <FaArrowLeft />
          Back to Reports Hub
        </button>

        {/* Summary Cards */}
        <div className="summary-cards-grid">
          {summaryCards.map((card) => (
            <div key={card.id} className={`summary-card ${card.color}`}>
              <div className="card-icon">{card.icon}</div>
              <div className="card-content">
                <div className="card-title">{card.title}</div>
                <div className="card-value">₹{card.value.toLocaleString()}</div>
                <div className="card-description">{card.description}</div>
              </div>
            </div>
          ))}
        </div>

        {/* Stock Movement & Inventory Report Section */}
        <div className="report-section">
          <div className="section-header">
            <h2 className="section-title">Stock Movement & Inventory Report</h2>
            <div className="section-controls">
              <select
                className="date-filter-dropdown"
                value={dateFilter}
                onChange={(e) => setDateFilter(e.target.value)}
              >
                <option value="current-month">Current Month</option>
                <option value="last-month">Last Month</option>
                <option value="current-year">Current Year</option>
                <option value="custom">Custom Range</option>
              </select>
              <div className="search-wrapper">
                <FaSearch className="search-icon" />
                <input
                  type="text"
                  className="search-input"
                  placeholder="Search products..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </div>
              <button className="download-excel-btn">
                <FaFileExcel />
                Download Excel
              </button>
            </div>
          </div>

          {/* Inventory Table */}
          <div className="table-container">
            <table className="inventory-report-table">
              <thead>
                <tr>
                  <th>Product</th>
                  <th>Unit</th>
                  <th>Opening</th>
                  <th>In (+)</th>
                  <th>Retail (-)</th>
                  <th>Internal (-)</th>
                  <th>Cons. Cost</th>
                  <th>Closing</th>
                  <th>Value</th>
                </tr>
              </thead>
              <tbody>
                {inventoryItems.map((item) => (
                  <tr key={item.id}>
                    <td className="product-name">{item.product}</td>
                    <td>{item.unit}</td>
                    <td>{item.opening}</td>
                    <td>{item.in}</td>
                    <td>{item.retail}</td>
                    <td>{item.internal}</td>
                    <td>{item.consCost}</td>
                    <td>{item.closing}</td>
                    <td className="value-cell">₹{item.value.toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="pagination-section">
            <div className="pagination-info">
              Showing {startItem} - {endItem} of {totalItems}
            </div>
            <div className="pagination">
              <button className="page-btn">Prev</button>
              <button className="page-btn active">1</button>
              <button className="page-btn">2</button>
              <button className="page-btn">3</button>
              <button className="page-btn">Next</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default InventoryReport

