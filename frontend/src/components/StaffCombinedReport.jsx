import React, { useState, useEffect } from 'react'
import {
  FaArrowLeft,
  FaList,
  FaTimes,
} from 'react-icons/fa'
import './StaffCombinedReport.css'
import { API_BASE_URL } from '../config'
import { apiGet } from '../utils/api'
import { showError } from '../utils/toast.jsx'
import { TableSkeleton } from './shared/SkeletonLoaders'
import { EmptyTable } from './shared/EmptyStates'
import { useAuth } from '../contexts/AuthContext'

const StaffCombinedReport = ({ setActivePage }) => {
  const { currentBranch } = useAuth()
  const [dateFilter, setDateFilter] = useState('last-7-days')
  const [staffSummary, setStaffSummary] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedStaff, setSelectedStaff] = useState(null)
  const [showDetailsModal, setShowDetailsModal] = useState(false)
  const [staffDetails, setStaffDetails] = useState(null)
  const [loadingDetails, setLoadingDetails] = useState(false)

  useEffect(() => {
    fetchStaffSummary()
  }, [dateFilter, currentBranch])

  // Listen for branch changes
  useEffect(() => {
    const handleBranchChange = () => {
      console.log('[StaffCombinedReport] Branch changed, refreshing staff summary...')
      fetchStaffSummary()
    }
    
    window.addEventListener('branchChanged', handleBranchChange)
    return () => window.removeEventListener('branchChanged', handleBranchChange)
  }, [currentBranch])

  const getDateRange = () => {
    const today = new Date()
    
    switch (dateFilter) {
      case 'today':
        return {
          start_date: today.toISOString().split('T')[0],
          end_date: today.toISOString().split('T')[0]
        }
      case 'yesterday':
        const yesterday = new Date(today)
        yesterday.setDate(yesterday.getDate() - 1)
        return {
          start_date: yesterday.toISOString().split('T')[0],
          end_date: yesterday.toISOString().split('T')[0]
        }
      case 'last-7-days':
        const last7Days = new Date(today)
        last7Days.setDate(last7Days.getDate() - 7)
        return {
          start_date: last7Days.toISOString().split('T')[0],
          end_date: today.toISOString().split('T')[0]
        }
      case 'last-30-days':
        const last30Days = new Date(today)
        last30Days.setDate(last30Days.getDate() - 30)
        return {
          start_date: last30Days.toISOString().split('T')[0],
          end_date: today.toISOString().split('T')[0]
        }
      case 'current-month':
        const firstDay = new Date(today.getFullYear(), today.getMonth(), 1)
        const lastDay = new Date(today.getFullYear(), today.getMonth() + 1, 0)
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
      default:
        return {}
    }
  }

  const fetchStaffSummary = async () => {
    try {
      setLoading(true)
      const dateRange = getDateRange()
      const params = new URLSearchParams()
      if (dateRange.start_date) params.append('start_date', dateRange.start_date)
      if (dateRange.end_date) params.append('end_date', dateRange.end_date)
      
      const response = await apiGet(`/api/dashboard/staff-performance?${params}`)
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      const data = await response.json()
      
      // Transform data to match table structure
      // Calculate total bills from services (approximate: 1 bill per service for simplicity)
      // In a real scenario, you'd need to count unique bills
      const transformedData = (Array.isArray(data) ? data : []).map(staff => ({
        id: staff.staff_id,
        staff: staff.staff_name,
        totalSale: staff.total_revenue || 0,
        totalBills: staff.total_services || 0, // Using services as approximate bill count
        avgBillValue: staff.total_services > 0 ? (staff.total_revenue / staff.total_services) : 0,
        totalServices: staff.total_services || 0,
        commissionEarned: staff.commission_earned || 0,
        completedAppointments: staff.completed_appointments || 0
      }))
      
      setStaffSummary(transformedData)
    } catch (error) {
      console.error('Error fetching staff summary:', error)
      showError(`Error fetching staff data: ${error.message}`)
      setStaffSummary([])
    } finally {
      setLoading(false)
    }
  }

  const handleViewDetails = async (staff) => {
    setSelectedStaff(staff)
    setShowDetailsModal(true)
    setLoadingDetails(true)
    
    try {
      const dateRange = getDateRange()
      const params = new URLSearchParams()
      params.append('staff_id', staff.id)
      if (dateRange.start_date) params.append('start_date', dateRange.start_date)
      if (dateRange.end_date) params.append('end_date', dateRange.end_date)
      
      const response = await apiGet(`/api/reports/staff-combined?${params}`)
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      const data = await response.json()
      
      // Find the staff data (should be first item if staff_id filter works)
      const staffData = Array.isArray(data) && data.length > 0 ? data[0] : null
      setStaffDetails(staffData)
    } catch (error) {
      console.error('Error fetching staff details:', error)
      showError(`Error fetching staff details: ${error.message}`)
      setStaffDetails(null)
    } finally {
      setLoadingDetails(false)
    }
  }

  const handleBackToReports = () => {
    if (setActivePage) {
      setActivePage('reports')
    }
  }

  return (
    <div className="staff-combined-report-page">
      <div className="staff-combined-report-container">
        {/* Back Button */}
        <button className="back-button" onClick={handleBackToReports}>
          <FaArrowLeft />
          Back to Reports Hub
        </button>

        {/* Date Filter Section */}
        <div className="filter-card">
          <div className="filter-group">
            <label className="filter-label">Date Range</label>
            <select
              className="filter-dropdown"
              value={dateFilter}
              onChange={(e) => setDateFilter(e.target.value)}
            >
              <option value="today">Today</option>
              <option value="yesterday">Yesterday</option>
              <option value="last-7-days">Last 7 days</option>
              <option value="last-30-days">Last 30 days</option>
              <option value="current-month">Current Month</option>
              <option value="last-month">Last Month</option>
              <option value="custom">Custom Range</option>
            </select>
          </div>
        </div>

        {/* Staff Summary Table */}
        <div className="report-card">
          <h2 className="section-title">Staff Summary</h2>
          <div className="table-container">
            {loading ? (
              <TableSkeleton rows={10} columns={5} />
            ) : staffSummary.length === 0 ? (
              <EmptyTable 
                title="No staff data found" 
                message="No staff performance data available for the selected date range."
              />
            ) : (
              <table className="staff-summary-table">
                <thead>
                  <tr>
                    <th>Staff</th>
                    <th>Total Sale (₹)</th>
                    <th>Total Bills</th>
                    <th>Avg. Bill Value (₹)</th>
                    <th>Details</th>
                  </tr>
                </thead>
                <tbody>
                  {staffSummary.map((staff) => (
                    <tr key={staff.id}>
                      <td className="staff-name">{staff.staff}</td>
                      <td>₹{staff.totalSale.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
                      <td>{staff.totalBills}</td>
                      <td>₹{staff.avgBillValue.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
                      <td>
                        <button 
                          className="details-btn" 
                          title="View Details"
                          onClick={() => handleViewDetails(staff)}
                        >
                          <FaList />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      </div>

      {/* Staff Details Modal */}
      {showDetailsModal && (
        <div className="modal-overlay" onClick={() => setShowDetailsModal(false)}>
          <div className="modal-content staff-details-modal" onClick={(e) => e.stopPropagation()} style={{
            maxWidth: '800px',
            width: '90%',
            maxHeight: '90vh',
            overflow: 'auto'
          }}>
            <div className="modal-header" style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              padding: '20px',
              borderBottom: '1px solid #e5e7eb'
            }}>
              <h2 style={{ margin: 0 }}>Staff Details - {selectedStaff?.staff}</h2>
              <button 
                className="modal-close-btn" 
                onClick={() => setShowDetailsModal(false)}
                style={{
                  background: 'none',
                  border: 'none',
                  fontSize: '20px',
                  cursor: 'pointer',
                  color: '#6b7280'
                }}
              >
                <FaTimes />
              </button>
            </div>
            
            <div className="modal-body" style={{ padding: '20px' }}>
              {loadingDetails ? (
                <div style={{ padding: '40px', textAlign: 'center' }}>
                  <p>Loading details...</p>
                </div>
              ) : staffDetails ? (
                <div className="staff-details-content">
                  <div className="details-summary">
                    <div className="detail-card" style={{
                      background: '#f9fafb',
                      padding: '20px',
                      borderRadius: '8px',
                      marginBottom: '20px'
                    }}>
                      <h3 style={{ marginTop: 0, marginBottom: '16px' }}>Performance Summary</h3>
                      <div className="detail-grid" style={{
                        display: 'grid',
                        gridTemplateColumns: 'repeat(2, 1fr)',
                        gap: '16px'
                      }}>
                        <div className="detail-item" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <span className="detail-label" style={{ fontWeight: '500', color: '#6b7280' }}>Total Revenue:</span>
                          <span className="detail-value" style={{ fontWeight: '600', color: '#1f2937' }}>₹{staffDetails.revenue?.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || '0.00'}</span>
                        </div>
                        <div className="detail-item" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <span className="detail-label" style={{ fontWeight: '500', color: '#6b7280' }}>Services Count:</span>
                          <span className="detail-value" style={{ fontWeight: '600', color: '#1f2937' }}>{staffDetails.services_count || 0}</span>
                        </div>
                        {selectedStaff && (
                          <>
                            <div className="detail-item" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                              <span className="detail-label" style={{ fontWeight: '500', color: '#6b7280' }}>Total Bills:</span>
                              <span className="detail-value" style={{ fontWeight: '600', color: '#1f2937' }}>{selectedStaff.totalBills}</span>
                            </div>
                            <div className="detail-item" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                              <span className="detail-label" style={{ fontWeight: '500', color: '#6b7280' }}>Avg. Bill Value:</span>
                              <span className="detail-value" style={{ fontWeight: '600', color: '#1f2937' }}>₹{selectedStaff.avgBillValue.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
                            </div>
                            <div className="detail-item" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                              <span className="detail-label" style={{ fontWeight: '500', color: '#6b7280' }}>Commission Earned:</span>
                              <span className="detail-value" style={{ fontWeight: '600', color: '#1f2937' }}>₹{selectedStaff.commissionEarned?.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || '0.00'}</span>
                            </div>
                            <div className="detail-item" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                              <span className="detail-label" style={{ fontWeight: '500', color: '#6b7280' }}>Completed Appointments:</span>
                              <span className="detail-value" style={{ fontWeight: '600', color: '#1f2937' }}>{selectedStaff.completedAppointments || 0}</span>
                            </div>
                          </>
                        )}
                      </div>
                    </div>

                    {staffDetails.services && staffDetails.services.length > 0 && (
                      <div className="detail-card" style={{
                        background: '#f9fafb',
                        padding: '20px',
                        borderRadius: '8px'
                      }}>
                        <h3 style={{ marginTop: 0, marginBottom: '16px' }}>Service Details</h3>
                        <div className="services-table-container" style={{ overflowX: 'auto' }}>
                          <table className="services-table" style={{
                            width: '100%',
                            borderCollapse: 'collapse'
                          }}>
                            <thead>
                              <tr style={{ background: '#f3f4f6' }}>
                                <th style={{ padding: '12px', textAlign: 'left', borderBottom: '2px solid #e5e7eb' }}>Service Name</th>
                                <th style={{ padding: '12px', textAlign: 'left', borderBottom: '2px solid #e5e7eb' }}>Bill Number</th>
                                <th style={{ padding: '12px', textAlign: 'left', borderBottom: '2px solid #e5e7eb' }}>Date</th>
                                <th style={{ padding: '12px', textAlign: 'left', borderBottom: '2px solid #e5e7eb' }}>Amount</th>
                              </tr>
                            </thead>
                            <tbody>
                              {staffDetails.services.map((service, index) => (
                                <tr key={index} style={{ borderBottom: '1px solid #e5e7eb' }}>
                                  <td style={{ padding: '12px' }}>{service.service_name || 'N/A'}</td>
                                  <td style={{ padding: '12px' }}>{service.bill_number || 'N/A'}</td>
                                  <td style={{ padding: '12px' }}>{service.date ? service.date.split('T')[0] : 'N/A'}</td>
                                  <td style={{ padding: '12px' }}>₹{(service.amount || 0).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ) : (
                <div style={{ padding: '40px', textAlign: 'center' }}>
                  <p>No detailed information available for this staff member.</p>
                </div>
              )}
            </div>
            
            <div className="modal-footer" style={{
              padding: '20px',
              borderTop: '1px solid #e5e7eb',
              display: 'flex',
              justifyContent: 'flex-end'
            }}>
              <button 
                className="btn-close" 
                onClick={() => setShowDetailsModal(false)}
                style={{
                  padding: '10px 20px',
                  background: '#3b82f6',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  fontWeight: '500'
                }}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default StaffCombinedReport

