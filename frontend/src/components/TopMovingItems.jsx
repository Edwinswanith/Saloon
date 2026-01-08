/**
 * Top Moving Items Component
 * 
 * A reusable React component for displaying top moving items (Services, Packages, Products)
 * in a tabbed table format with trend indicators and status badges.
 * 
 * Features:
 * - Three tabs: Services, Packages, Products
 * - Trend indicators (trending_up, trending_down, minus)
 * - Status badges for packages (High Demand, Stable, Low Demand)
 * - Stock status for products (OK, Low)
 * - Clickable product rows for navigation
 * - Loading and empty states
 * 
 * Usage:
 * ```jsx
 * import TopMovingItems from './TopMovingItems'
 * 
 * <TopMovingItems 
 *   data={topMovingItemsData}
 *   loading={false}
 *   formatCurrency={(amount) => `₹ ${amount.toLocaleString('en-IN')}`}
 *   onProductClick={(product) => navigateToInventory(product)}
 * />
 * ```
 */

import React, { useState } from 'react'
import {
  FaArrowUp,
  FaArrowDown,
  FaMinus,
  FaCheckCircle,
  FaExclamationCircle
} from 'react-icons/fa'
import './TopMovingItems.css'

const TopMovingItems = ({ 
  data = {
    services: [],
    packages: [],
    products: []
  },
  loading = false,
  formatCurrency = (amount) => `₹ ${amount.toLocaleString('en-IN', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`,
  onProductClick = (product) => {
    // Default: Custom event for navigation
    if (window.setActivePage) {
      window.setActivePage('inventory')
    } else {
      window.dispatchEvent(new CustomEvent('navigateToPage', { detail: { page: 'inventory' } }))
    }
  }
}) => {
  const [activeTab, setActiveTab] = useState('services')

  return (
    <div className="top-moving-items-section">
      <div className="section-header">
        <h2 className="section-title">Top Moving Items</h2>
      </div>
      
      {/* Tabs */}
      <div className="tabs">
        <button
          className={`tab ${activeTab === 'services' ? 'active' : ''}`}
          onClick={() => setActiveTab('services')}
        >
          Services
        </button>
        <button
          className={`tab ${activeTab === 'packages' ? 'active' : ''}`}
          onClick={() => setActiveTab('packages')}
        >
          Packages
        </button>
        <button
          className={`tab ${activeTab === 'products' ? 'active' : ''}`}
          onClick={() => setActiveTab('products')}
        >
          Products
        </button>
      </div>

      {/* Services Tab */}
      {activeTab === 'services' && (
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th className="text-left">Service Name</th>
                <th className="text-right">Bills</th>
                <th className="text-right">Revenue</th>
                <th className="text-center">Trend</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan="4" className="empty-row">Loading...</td>
                </tr>
              ) : data.services.length === 0 ? (
                <tr>
                  <td colSpan="4" className="empty-row">No service data available</td>
                </tr>
              ) : (
                data.services.map((service, index) => (
                  <tr key={index}>
                    <td className="text-left">{service.name}</td>
                    <td className="text-right">{service.bills}</td>
                    <td className="text-right revenue-cell">
                      {formatCurrency(service.revenue)}
                    </td>
                    <td className="text-center">
                      {service.trend === 'trending_up' && (
                        <FaArrowUp className="trend-icon trend-up" />
                      )}
                      {service.trend === 'trending_down' && (
                        <FaArrowDown className="trend-icon trend-down" />
                      )}
                      {service.trend === 'minus' && (
                        <FaMinus className="trend-icon trend-neutral" />
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Packages Tab */}
      {activeTab === 'packages' && (
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th className="text-left">Package Name</th>
                <th className="text-right">Sold</th>
                <th className="text-right">Revenue</th>
                <th className="text-left">Status</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan="4" className="empty-row">Loading...</td>
                </tr>
              ) : data.packages.length === 0 ? (
                <tr>
                  <td colSpan="4" className="empty-row">No package sales in this period</td>
                </tr>
              ) : (
                data.packages.map((pkg, index) => (
                  <tr key={index}>
                    <td className="text-left">{pkg.name}</td>
                    <td className="text-right">{pkg.sold}</td>
                    <td className="text-right revenue-cell">
                      {formatCurrency(pkg.revenue)}
                    </td>
                    <td className="text-left">
                      <div className="status-badge">
                        {pkg.status === 'High Demand' && (
                          <>
                            <FaArrowUp className="status-icon status-high" />
                            <span className="status-text status-high">High Demand</span>
                          </>
                        )}
                        {pkg.status === 'Stable' && (
                          <>
                            <FaMinus className="status-icon status-stable" />
                            <span className="status-text status-stable">Stable</span>
                          </>
                        )}
                        {pkg.status === 'Low Demand' && (
                          <>
                            <FaArrowDown className="status-icon status-low" />
                            <span className="status-text status-low">Low Demand</span>
                          </>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Products Tab */}
      {activeTab === 'products' && (
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th className="text-left">Product Name</th>
                <th className="text-right">Sold</th>
                <th className="text-right">Revenue</th>
                <th className="text-left">Stock</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan="4" className="empty-row">Loading...</td>
                </tr>
              ) : data.products.length === 0 ? (
                <tr>
                  <td colSpan="4" className="empty-row">No product data available</td>
                </tr>
              ) : (
                data.products.map((product, index) => (
                  <tr 
                    key={index}
                    onClick={() => onProductClick(product)}
                    className="product-row"
                  >
                    <td className="text-left">{product.name}</td>
                    <td className="text-right">{product.sold}</td>
                    <td className="text-right revenue-cell">
                      {formatCurrency(product.revenue)}
                    </td>
                    <td className="text-left">
                      <div className="stock-badge">
                        {product.stock === 'OK' && (
                          <>
                            <FaCheckCircle className="stock-icon stock-ok" />
                            <span className="stock-text stock-ok">OK</span>
                          </>
                        )}
                        {product.stock === 'Low' && (
                          <>
                            <FaExclamationCircle className="stock-icon stock-low" />
                            <span className="stock-text stock-low">Low</span>
                          </>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

export default TopMovingItems

