/**
 * Sales Insights Component
 * 
 * Tab-based lazy loading component for Dashboard Sales section.
 * Only loads data when user clicks a tab.
 * 
 * Features:
 * - Three tabs: Top Moving Items, Top 10 Customers, Top 10 Offerings
 * - Lazy loading: Only first tab loads on initial render
 * - Per-tab caching (60 seconds TTL)
 * - Skeleton loaders for better UX
 * - Error handling with retry
 * - Mobile-friendly horizontal scrolling tabs
 * - Disables tab switching while loading
 */

import React, { useState, useEffect, useCallback } from 'react'
import { apiGet } from '../utils/api'
import { useAuth } from '../contexts/AuthContext'
import TopMovingItems from './TopMovingItems'
import Top10Customers from './Top10Customers'
import { TableSkeleton } from './shared/SkeletonLoaders'
import { EmptyTable } from './shared/EmptyStates'
import './SalesInsights.css'

const SalesInsights = ({ 
  dateRange = {},
  formatCurrency = (amount) => `₹ ${amount.toLocaleString('en-IN', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`
}) => {
  const { currentBranch } = useAuth()
  const [activeTab, setActiveTab] = useState('top-moving-items')
  
  // Per-tab data cache
  const [tabCache, setTabCache] = useState({
    'top-moving-items': { data: null, timestamp: null, loading: false, error: null, cacheKey: null },
    'top-customers': { data: null, timestamp: null, loading: false, error: null, cacheKey: null },
    'top-offerings': { data: null, timestamp: null, loading: false, error: null, cacheKey: null }
  })

  // Cache TTL: 60 seconds
  const CACHE_TTL_MS = 60 * 1000

  // Generate cache key based on params
  const getCacheKey = useCallback(() => {
    return JSON.stringify({
      start_date: dateRange.start_date,
      end_date: dateRange.end_date,
      branchId: currentBranch?.id || null
    })
  }, [dateRange.start_date, dateRange.end_date, currentBranch?.id])

  // Check if cache is valid
  const isCacheValid = useCallback((cacheEntry, currentKey) => {
    if (!cacheEntry || !cacheEntry.data || !cacheEntry.timestamp) {
      return false
    }
    
    // Check if cache key matches
    if (cacheEntry.cacheKey !== currentKey) {
      return false
    }
    
    // Check if cache has expired
    const now = Date.now()
    if (now - cacheEntry.timestamp > CACHE_TTL_MS) {
      return false
    }
    
    return true
  }, [CACHE_TTL_MS])

  // Fetch data for a specific tab
  const fetchTabData = useCallback(async (tabName) => {
    const currentKey = getCacheKey()
    
    // Check cache first using functional update to avoid stale closure
    let shouldFetch = true
    setTabCache(prev => {
      const cacheEntry = prev[tabName]
      
      // Check cache first
      if (isCacheValid(cacheEntry, currentKey)) {
        console.log(`[SalesInsights] Using cached data for ${tabName}`)
        shouldFetch = false
        return prev // Return unchanged if cache is valid
      }

      // Set loading state
      return {
        ...prev,
        [tabName]: {
          ...prev[tabName],
          loading: true,
          error: null
        }
      }
    })

    if (!shouldFetch) {
      return
    }

    try {
      let endpoint = ''
      let params = new URLSearchParams(dateRange)
      params.append('_t', Date.now())
      
      switch (tabName) {
        case 'top-moving-items':
          endpoint = '/api/dashboard/top-moving-items'
          break
        case 'top-customers':
          endpoint = '/api/dashboard/top-customers'
          params.append('limit', '10')
          break
        case 'top-offerings':
          endpoint = '/api/dashboard/top-offerings'
          params.append('limit', '10')
          break
        default:
          throw new Error(`Unknown tab: ${tabName}`)
      }

      const response = await apiGet(`${endpoint}?${params}`)
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()

      // Update cache with data
      setTabCache(prev => ({
        ...prev,
        [tabName]: {
          data: data,
          timestamp: Date.now(),
          cacheKey: currentKey,
          loading: false,
          error: null
        }
      }))

      console.log(`[SalesInsights] Loaded data for ${tabName}`)
    } catch (error) {
      console.error(`[SalesInsights] Error fetching ${tabName}:`, error)
      setTabCache(prev => ({
        ...prev,
        [tabName]: {
          ...prev[tabName],
          loading: false,
          error: error.message || 'Failed to load data'
        }
      }))
    }
  }, [dateRange, getCacheKey, isCacheValid])

  // Load initial tab data on mount
  useEffect(() => {
    fetchTabData('top-moving-items')
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []) // Only run on mount

  // Handle tab change
  const handleTabChange = useCallback((tabName) => {
    const currentCache = tabCache[tabName]
    if (currentCache?.loading) {
      // Don't allow tab switching while loading
      return
    }
    
    setActiveTab(tabName)
    
    // Fetch data if not cached or cache invalid
    const currentKey = getCacheKey()
    
    if (!isCacheValid(currentCache, currentKey)) {
      fetchTabData(tabName)
    }
  }, [tabCache, getCacheKey, isCacheValid, fetchTabData])

  // Invalidate cache when date range or branch changes
  useEffect(() => {
    const currentKey = getCacheKey()
    
    // Invalidate all caches if key changed
    setTabCache(prev => {
      const updated = { ...prev }
      Object.keys(updated).forEach(tabName => {
        if (updated[tabName].cacheKey && updated[tabName].cacheKey !== currentKey) {
          updated[tabName] = {
            data: null,
            timestamp: null,
            cacheKey: null,
            loading: false,
            error: null
          }
        }
      })
      return updated
    })

    // Reload active tab if cache was invalidated
    const activeCache = tabCache[activeTab]
    if (!isCacheValid(activeCache, currentKey)) {
      fetchTabData(activeTab)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dateRange.start_date, dateRange.end_date, currentBranch?.id])

  // Check if any tab is loading
  const isLoading = Object.values(tabCache).some(cache => cache.loading)

  // Render tab content
  const renderTabContent = () => {
    const cache = tabCache[activeTab]

    if (cache.loading) {
      return <TableSkeleton rows={10} columns={4} />
    }

    if (cache.error) {
      return (
        <div className="sales-insights-error">
          <p>Error: {cache.error}</p>
          <button 
            className="retry-button"
            onClick={() => fetchTabData(activeTab)}
          >
            Retry
          </button>
        </div>
      )
    }

    if (!cache.data) {
      return <EmptyTable title="No Data" message="Click to load data" />
    }

    switch (activeTab) {
      case 'top-moving-items':
        return (
          <TopMovingItems
            data={cache.data}
            loading={false}
            formatCurrency={formatCurrency}
          />
        )
      
      case 'top-customers':
        return (
          <Top10Customers
            customers={Array.isArray(cache.data) ? cache.data : []}
            loading={false}
            formatCurrency={formatCurrency}
            onExport={() => {
              console.log('Export Full Report clicked')
            }}
          />
        )
      
      case 'top-offerings':
        return (
          <div className="table-section">
            <div className="section-header">
              <h2 className="section-title">Top 10 Offerings</h2>
              <button 
                className="export-link" 
                onClick={(e) => {
                  e.preventDefault()
                  console.log('Export Full Report clicked')
                }}
                style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'inherit', textDecoration: 'underline' }}
              >
                Export Full Report
              </button>
            </div>
            <div className="table-container">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>#</th>
                    <th>Offering</th>
                    <th>Count</th>
                    <th>Revenue</th>
                  </tr>
                </thead>
                <tbody>
                  {Array.isArray(cache.data) && cache.data.length > 0 ? (
                    cache.data.slice(0, 10).map((offering, index) => (
                      <tr key={index}>
                        <td>{index + 1}</td>
                        <td>{offering.name}</td>
                        <td>{offering.quantity}</td>
                        <td>{formatCurrency(offering.revenue)}</td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan="4" className="empty-row">No data available</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )
      
      default:
        return <EmptyTable title="Unknown Tab" message="Please select a valid tab" />
    }
  }

  return (
    <div className="sales-insights-section">
      <div className="section-header">
        <h2 className="section-title">Sales Insights</h2>
      </div>

      {/* Tabs */}
      <div className="sales-insights-tabs">
        <button
          className={`sales-insights-tab ${activeTab === 'top-moving-items' ? 'active' : ''} ${isLoading ? 'disabled' : ''}`}
          onClick={() => handleTabChange('top-moving-items')}
          disabled={isLoading}
        >
          Top Moving Items
          {tabCache['top-moving-items']?.loading && (
            <span className="tab-loading-indicator">●</span>
          )}
        </button>
        <button
          className={`sales-insights-tab ${activeTab === 'top-customers' ? 'active' : ''} ${isLoading ? 'disabled' : ''}`}
          onClick={() => handleTabChange('top-customers')}
          disabled={isLoading}
        >
          Top 10 Customers
          {tabCache['top-customers']?.loading && (
            <span className="tab-loading-indicator">●</span>
          )}
        </button>
        <button
          className={`sales-insights-tab ${activeTab === 'top-offerings' ? 'active' : ''} ${isLoading ? 'disabled' : ''}`}
          onClick={() => handleTabChange('top-offerings')}
          disabled={isLoading}
        >
          Top 10 Offerings
          {tabCache['top-offerings']?.loading && (
            <span className="tab-loading-indicator">●</span>
          )}
        </button>
      </div>

      {/* Tab Content */}
      <div className="sales-insights-content">
        {renderTabContent()}
      </div>
    </div>
  )
}

export default SalesInsights

