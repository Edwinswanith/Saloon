import React, { useState, useEffect } from 'react'
import {
  FaExchangeAlt,
  FaCalendar,
  FaUser,
  FaBuilding,
  FaPlus,
  FaTimes,
  FaCheckCircle,
  FaClock,
  FaTimesCircle,
  FaInfoCircle,
  FaUsers,
  FaExclamationTriangle,
  FaChevronDown,
  FaChevronUp,
  FaList
} from 'react-icons/fa'
import './StaffTempAssignment.css'
import { apiGet, apiPost, apiPut, apiDelete } from '../utils/api'
import { showSuccess, showError, showWarning, showConfirm } from '../utils/toast.jsx'
import { useAuth } from '../contexts/AuthContext'
import DatePicker from 'react-datepicker'
import Header from './Header'
import { TableSkeleton } from './shared/SkeletonLoaders'
import { EmptyTable } from './shared/EmptyStates'
import PageTransition from './shared/PageTransition'

const StaffTempAssignment = () => {
  const { getBranchId } = useAuth()
  const [assignments, setAssignments] = useState([])
  const [allStaff, setAllStaff] = useState([])
  const [branches, setBranches] = useState([])
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [coverageData, setCoverageData] = useState(null)
  const [selectedBranch, setSelectedBranch] = useState(null)
  const [viewMode, setViewMode] = useState('dashboard') // 'dashboard' or 'assignments'
  const [expandedBranches, setExpandedBranches] = useState({})
  const [formData, setFormData] = useState({
    staff_id: '',
    temp_branch_id: '',
    start_date: new Date(),
    end_date: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000), // Default 7 days
    reason: 'leave_coverage',
    covering_for_id: '',
    notes: ''
  })

  useEffect(() => {
    fetchData()
  }, [])

  // Listen for branch changes
  useEffect(() => {
    const handleBranchChange = () => {
      console.log('[StaffTempAssignment] Branch changed, refreshing data...')
      fetchData()
    }
    
    window.addEventListener('branchChanged', handleBranchChange)
    return () => window.removeEventListener('branchChanged', handleBranchChange)
  }, [])

  const fetchData = async () => {
    setLoading(true)
    await Promise.all([
      fetchAssignments(),
      fetchStaff(),
      fetchBranches(),
      fetchCoverageDashboard()
    ])
    setLoading(false)
  }

  const fetchCoverageDashboard = async () => {
    try {
      const response = await apiGet('/api/temp-assignments/coverage-dashboard')
      if (response.ok) {
        const data = await response.json()
        setCoverageData(data)
      }
    } catch (error) {
      console.error('Error fetching coverage dashboard:', error)
      setCoverageData(null)
    }
  }

  const fetchAssignments = async () => {
    try {
      const branchId = getBranchId()
      const url = branchId 
        ? `/api/temp-assignments?branch_id=${branchId}&status=active`
        : `/api/temp-assignments?status=active`
      
      const response = await apiGet(url)
      if (response.ok) {
        const data = await response.json()
        setAssignments(data || [])
      }
    } catch (error) {
      console.error('Error fetching assignments:', error)
      setAssignments([])
    }
  }

  const fetchStaff = async () => {
    try {
      const response = await apiGet('/api/staffs')
      if (response.ok) {
        const data = await response.json()
        setAllStaff(data.staffs || [])
      }
    } catch (error) {
      console.error('Error fetching staff:', error)
      setAllStaff([])
    }
  }

  const fetchBranches = async () => {
    try {
      const response = await apiGet('/api/branches')
      if (response.ok) {
        const data = await response.json()
        // Branch endpoint returns array directly, not wrapped in {branches: [...]}
        setBranches(Array.isArray(data) ? data : (data.branches || []))
      }
    } catch (error) {
      console.error('Error fetching branches:', error)
      setBranches([])
    }
  }

  const handleOpenModal = () => {
    setFormData({
      staff_id: '',
      temp_branch_id: '',
      start_date: new Date(),
      end_date: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000),
      reason: 'leave_coverage',
      covering_for_id: '',
      notes: ''
    })
    setShowModal(true)
  }

  const handleCloseModal = () => {
    setShowModal(false)
  }

  const handleCreate = async () => {
    // Validation
    if (!formData.staff_id) {
      showError('Please select a staff member')
      return
    }
    if (!formData.temp_branch_id) {
      showError('Please select a branch to assign to')
      return
    }
    if (formData.start_date >= formData.end_date) {
      showError('End date must be after start date')
      return
    }

    try {
      const response = await apiPost('/api/temp-assignments', {
        staff_id: formData.staff_id,
        temp_branch_id: formData.temp_branch_id,
        start_date: formData.start_date.toISOString(),
        end_date: formData.end_date.toISOString(),
        reason: formData.reason,
        covering_for_id: formData.covering_for_id || null,
        notes: formData.notes
      })

      if (response.ok) {
        const data = await response.json()
        showSuccess(data.message || 'Staff temporarily reassigned successfully')
        // Refresh all data after successful creation
        await Promise.all([
          fetchAssignments(),
          fetchCoverageDashboard(),
          fetchStaff(),
          fetchBranches()
        ])
        handleCloseModal()
      } else {
        const error = await response.json()
        showError(error.error || 'Failed to create assignment')
      }
    } catch (error) {
      console.error('Error creating assignment:', error)
      showError('Error creating assignment')
    }
  }

  const handleCancel = async (assignmentId, staffName) => {
    return new Promise((resolve) => {
      showConfirm(
        `Are you sure you want to cancel the temporary assignment for ${staffName}?`,
        async () => {
          try {
            const response = await apiDelete(`/api/temp-assignments/${assignmentId}`)
            
            if (response.ok) {
              showSuccess('Assignment cancelled successfully')
              await Promise.all([
                fetchAssignments(),
                fetchCoverageDashboard() // Refresh dashboard data
              ])
            } else {
              const error = await response.json()
              showError(error.error || 'Failed to cancel assignment')
            }
            resolve()
          } catch (error) {
            console.error('Error cancelling assignment:', error)
            showError('Error cancelling assignment')
            resolve()
          }
        }
      )
    })
  }

  const getReasonLabel = (reason) => {
    const labels = {
      leave_coverage: 'Leave Coverage',
      training: 'Training',
      support: 'Extra Support',
      event: 'Special Event',
      other: 'Other'
    }
    return labels[reason] || reason
  }

  const getStatusColor = (endDate) => {
    const today = new Date()
    const end = new Date(endDate)
    const daysLeft = Math.ceil((end - today) / (1000 * 60 * 60 * 24))
    
    if (daysLeft < 0) return '#dc3545' // Red - expired
    if (daysLeft <= 3) return '#ffc107' // Yellow - expiring soon
    return '#28a745' // Green - active
  }

  const getDaysRemaining = (endDate) => {
    const today = new Date()
    const end = new Date(endDate)
    const daysLeft = Math.ceil((end - today) / (1000 * 60 * 60 * 24))
    
    if (daysLeft < 0) return 'Expired'
    if (daysLeft === 0) return 'Today'
    if (daysLeft === 1) return '1 day left'
    return `${daysLeft} days left`
  }

  // Get staff available for assignment (from different branches)
  const getAvailableStaff = () => {
    const currentBranchId = getBranchId()
    if (!currentBranchId) return allStaff
    
    // Filter staff from OTHER branches (not the current branch)
    return allStaff.filter(s => !s.isTemp) // Only permanent staff can be reassigned
  }

  // Get branches available for temp assignment
  const getAvailableBranches = () => {
    if (!formData.staff_id) return branches
    
    const selectedStaff = allStaff.find(s => s.id === formData.staff_id)
    if (!selectedStaff) return branches
    
    // Filter out the staff's home branch
    return branches.filter(b => {
      // If staff has no branch, allow all branches
      if (!selectedStaff.branchId) return true
      return b.id !== selectedStaff.branchId
    })
  }

  // Get staff from the temp branch who are on leave and need coverage
  const getStaffNeedingCoverage = () => {
    if (!formData.temp_branch_id) return []
    
    // If we have coverage data, use it to show staff on leave
    if (coverageData && coverageData.leaves_today) {
      // Get leaves for the selected temp branch that are not covered
      const uncoveredLeaves = coverageData.leaves_today.filter(
        leave => leave.branch_id === formData.temp_branch_id && !leave.covered
      )
      
      // Return unique staff from those leaves
      const staffMap = new Map()
      uncoveredLeaves.forEach(leave => {
        if (!staffMap.has(leave.staff_id)) {
          const nameParts = leave.staff_name.split(' ')
          staffMap.set(leave.staff_id, {
            id: leave.staff_id,
            firstName: nameParts[0] || leave.staff_name,
            lastName: nameParts.slice(1).join(' ') || '',
            fullName: leave.staff_name,
            leave_id: leave.leave_id
          })
        }
      })
      
      return Array.from(staffMap.values())
    }
    
    // Fallback: Show all staff from the temp branch if coverage data not available
    const tempBranch = branches.find(b => b.id === formData.temp_branch_id)
    if (!tempBranch) return []
    
    return allStaff
      .filter(s => s.branchId === formData.temp_branch_id && !s.isTemp)
      .map(s => ({
        id: s.id,
        firstName: s.firstName || '',
        lastName: s.lastName || '',
        fullName: `${s.firstName || ''} ${s.lastName || ''}`.trim() || s.firstName || s.lastName || 'Unknown'
      }))
  }

  const toggleBranchExpand = (branchId) => {
    setExpandedBranches(prev => ({
      ...prev,
      [branchId]: !prev[branchId]
    }))
  }

  const handleQuickReassign = (branchId, staffId = null) => {
    setFormData({
      staff_id: '',
      temp_branch_id: branchId,
      start_date: new Date(),
      end_date: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000),
      reason: 'leave_coverage',
      covering_for_id: staffId || '',
      notes: ''
    })
    setShowModal(true)
  }

  const handleReassignFromAvailable = (staffId, branchId) => {
    setFormData({
      staff_id: staffId,
      temp_branch_id: branchId,
      start_date: new Date(),
      end_date: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000),
      reason: 'leave_coverage',
      covering_for_id: '',
      notes: ''
    })
    setShowModal(true)
  }

  // Calculate summary stats from coverage data
  const getSummaryStats = () => {
    if (!coverageData) return { leavesToday: 0, branchesNeeding: 0, availableStaff: 0 }
    
    return {
      leavesToday: coverageData.leaves_today?.length || 0,
      branchesNeeding: coverageData.branches_needing_coverage?.length || 0,
      availableStaff: coverageData.available_staff_by_branch?.reduce((sum, branch) => sum + (branch.available_staff?.length || 0), 0) || 0
    }
  }

  const stats = getSummaryStats()

  return (
    <PageTransition>
      <div className="temp-assignment-page">
        <Header title="Staff Temporary Reassignment" />
        
        <div className="temp-assignment-container">
          {/* Header Section */}
          <div className="temp-assignment-header">
            <div className="header-left">
              <FaExchangeAlt className="header-icon" />
              <div>
                <h2>Temporary Staff Assignments</h2>
                <p>Manage cross-branch staff coverage and temporary reassignments</p>
              </div>
            </div>
            <div className="header-actions">
              <div className="view-toggle">
                <button 
                  className={`toggle-btn ${viewMode === 'dashboard' ? 'active' : ''}`}
                  onClick={() => setViewMode('dashboard')}
                >
                  <FaBuilding /> Coverage Dashboard
                </button>
                <button 
                  className={`toggle-btn ${viewMode === 'assignments' ? 'active' : ''}`}
                  onClick={() => setViewMode('assignments')}
                >
                  <FaList /> All Assignments
                </button>
              </div>
              <button className="btn-add-assignment" onClick={handleOpenModal}>
                <FaPlus /> Reassign Staff
              </button>
            </div>
          </div>

          {viewMode === 'dashboard' ? (
            <>
              {/* Dashboard Summary Cards */}
              <div className="assignment-stats">
                <div className="stat-card">
                  <div className="stat-icon" style={{ backgroundColor: '#ffebee' }}>
                    <FaExclamationTriangle style={{ color: '#f44336' }} />
                  </div>
                  <div className="stat-content">
                    <div className="stat-value">{stats.leavesToday}</div>
                    <div className="stat-label">Staff on Leave Today</div>
                  </div>
                </div>
                <div className="stat-card">
                  <div className="stat-icon" style={{ backgroundColor: '#fff3e0' }}>
                    <FaBuilding style={{ color: '#ff9800' }} />
                  </div>
                  <div className="stat-content">
                    <div className="stat-value">{stats.branchesNeeding}</div>
                    <div className="stat-label">Branches Needing Coverage</div>
                  </div>
                </div>
                <div className="stat-card">
                  <div className="stat-icon" style={{ backgroundColor: '#e8f5e9' }}>
                    <FaUsers style={{ color: '#4caf50' }} />
                  </div>
                  <div className="stat-content">
                    <div className="stat-value">{stats.availableStaff}</div>
                    <div className="stat-label">Available Staff</div>
                  </div>
                </div>
                <div className="stat-card">
                  <div className="stat-icon" style={{ backgroundColor: '#e3f2fd' }}>
                    <FaCheckCircle style={{ color: '#2196f3' }} />
                  </div>
                  <div className="stat-content">
                    <div className="stat-value">{assignments.length}</div>
                    <div className="stat-label">Active Assignments</div>
                  </div>
                </div>
              </div>

              {loading ? (
                <TableSkeleton />
              ) : coverageData ? (
                <>
                  {/* Branches Needing Coverage */}
                  {coverageData.branches_needing_coverage && coverageData.branches_needing_coverage.length > 0 && (
                    <div className="coverage-section">
                      <h3 className="section-title">
                        <FaExclamationTriangle style={{ color: '#f44336', marginRight: '8px' }} />
                        Branches Needing Coverage
                      </h3>
                      <div className="branch-coverage-grid">
                        {coverageData.branches_needing_coverage.map(branch => {
                          const branchLeaves = coverageData.leaves_today.filter(
                            l => l.branch_id === branch.branch_id && !l.covered
                          )
                          return (
                            <div key={branch.branch_id} className="branch-coverage-card">
                              <div className="branch-coverage-header">
                                <div>
                                  <h4>{branch.branch_name}</h4>
                                  <p className="branch-city">{branch.branch_city}</p>
                                </div>
                                <div className="coverage-badge uncovered">
                                  {branch.uncovered_leaves} Uncovered
                                </div>
                              </div>
                              <div className="leaves-list">
                                {branchLeaves.map(leave => (
                                  <div key={leave.leave_id} className="leave-item">
                                    <div className="leave-info">
                                      <FaUser className="leave-icon" />
                                      <div>
                                        <div className="leave-staff-name">{leave.staff_name}</div>
                                        <div className="leave-dates">
                                          {new Date(leave.start_date).toLocaleDateString()} - {new Date(leave.end_date).toLocaleDateString()}
                                        </div>
                                      </div>
                                    </div>
                                    <button 
                                      className="btn-quick-reassign"
                                      onClick={() => handleQuickReassign(branch.branch_id, leave.staff_id)}
                                    >
                                      <FaExchangeAlt /> Assign Coverage
                                    </button>
                                  </div>
                                ))}
                              </div>
                              <button 
                                className="btn-quick-reassign-full"
                                onClick={() => handleQuickReassign(branch.branch_id)}
                              >
                                <FaPlus /> Quick Reassign to This Branch
                              </button>
                            </div>
                          )
                        })}
                      </div>
                    </div>
                  )}

                  {/* Available Staff by Branch */}
                  {coverageData.available_staff_by_branch && coverageData.available_staff_by_branch.length > 0 && (
                    <div className="coverage-section">
                      <h3 className="section-title">
                        <FaUsers style={{ color: '#4caf50', marginRight: '8px' }} />
                        Available Staff by Branch
                      </h3>
                      <div className="available-staff-grid">
                        {coverageData.available_staff_by_branch.map(branch => (
                          <div key={branch.branch_id} className="available-staff-card">
                            <div 
                              className="available-staff-header"
                              onClick={() => toggleBranchExpand(branch.branch_id)}
                            >
                              <div>
                                <h4>{branch.branch_name}</h4>
                                <p className="branch-city">{branch.branch_city}</p>
                              </div>
                              <div className="staff-count-badge">
                                {branch.available_staff.length} Available
                                {expandedBranches[branch.branch_id] ? (
                                  <FaChevronUp style={{ marginLeft: '8px' }} />
                                ) : (
                                  <FaChevronDown style={{ marginLeft: '8px' }} />
                                )}
                              </div>
                            </div>
                            {expandedBranches[branch.branch_id] && (
                              <div className="staff-list">
                                {branch.available_staff.map(staff => (
                                  <div key={staff.staff_id} className="staff-item">
                                    <div className="staff-info">
                                      <div className="staff-avatar-small">
                                        {staff.staff_name.charAt(0)}
                                      </div>
                                      <div>
                                        <div className="staff-name">{staff.staff_name}</div>
                                        <div className="staff-mobile">{staff.mobile}</div>
                                      </div>
                                    </div>
                                    <button 
                                      className="btn-reassign-staff"
                                      onClick={() => handleReassignFromAvailable(staff.staff_id, branch.branch_id)}
                                    >
                                      <FaExchangeAlt /> Reassign
                                    </button>
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Today's Leaves Table */}
                  {coverageData.leaves_today && coverageData.leaves_today.length > 0 && (
                    <div className="coverage-section">
                      <h3 className="section-title">
                        <FaCalendar style={{ color: '#2196f3', marginRight: '8px' }} />
                        Today's Leaves
                      </h3>
                      <div className="assignments-table-wrapper">
                        <table className="assignments-table">
                          <thead>
                            <tr>
                              <th>Staff Member</th>
                              <th>Branch</th>
                              <th>Period</th>
                              <th>Leave Type</th>
                              <th>Coverage Status</th>
                              <th>Actions</th>
                            </tr>
                          </thead>
                          <tbody>
                            {coverageData.leaves_today.map(leave => (
                              <tr key={leave.leave_id}>
                                <td>
                                  <div className="staff-cell">
                                    <div className="staff-avatar">
                                      {leave.staff_name.charAt(0)}
                                    </div>
                                    <div>
                                      <div className="staff-name">{leave.staff_name}</div>
                                    </div>
                                  </div>
                                </td>
                                <td>
                                  <div className="branch-info">
                                    <FaBuilding className="branch-icon" />
                                    <span>{leave.branch_name}</span>
                                  </div>
                                </td>
                                <td>
                                  <div className="date-range">
                                    <FaCalendar className="calendar-icon" />
                                    <span>
                                      {new Date(leave.start_date).toLocaleDateString()} - {new Date(leave.end_date).toLocaleDateString()}
                                    </span>
                                  </div>
                                </td>
                                <td>
                                  <span className="leave-type-badge">{leave.leave_type}</span>
                                </td>
                                <td>
                                  {leave.covered ? (
                                    <div className="coverage-status covered">
                                      <FaCheckCircle /> Covered
                                    </div>
                                  ) : (
                                    <div className="coverage-status uncovered">
                                      <FaExclamationTriangle /> Uncovered
                                    </div>
                                  )}
                                </td>
                                <td>
                                  {!leave.covered && (
                                    <button 
                                      className="btn-quick-reassign"
                                      onClick={() => handleQuickReassign(leave.branch_id, leave.staff_id)}
                                    >
                                      <FaExchangeAlt /> Assign Coverage
                                    </button>
                                  )}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}

                  {coverageData.branches_needing_coverage?.length === 0 && 
                   coverageData.available_staff_by_branch?.length === 0 && 
                   coverageData.leaves_today?.length === 0 && (
                    <EmptyTable 
                      message="No coverage needs today"
                      subtitle="All branches are fully staffed"
                    />
                  )}
                </>
              ) : (
                <EmptyTable 
                  message="Unable to load coverage data"
                  subtitle="Please try refreshing the page"
                />
              )}
            </>
          ) : (
            <>
              {/* All Assignments View */}
              <div className="assignment-stats">
                <div className="stat-card">
                  <div className="stat-icon" style={{ backgroundColor: '#e3f2fd' }}>
                    <FaCheckCircle style={{ color: '#2196f3' }} />
                  </div>
                  <div className="stat-content">
                    <div className="stat-value">{assignments.length}</div>
                    <div className="stat-label">Active Assignments</div>
                  </div>
                </div>
                <div className="stat-card">
                  <div className="stat-icon" style={{ backgroundColor: '#fff3e0' }}>
                    <FaClock style={{ color: '#ff9800' }} />
                  </div>
                  <div className="stat-content">
                    <div className="stat-value">
                      {assignments.filter(a => {
                        const daysLeft = Math.ceil((new Date(a.end_date) - new Date()) / (1000 * 60 * 60 * 24))
                        return daysLeft <= 3 && daysLeft >= 0
                      }).length}
                    </div>
                    <div className="stat-label">Expiring Soon</div>
                  </div>
                </div>
              </div>

              {/* Assignments Table */}
              <div className="assignments-section">
            {loading ? (
              <TableSkeleton />
            ) : assignments.length === 0 ? (
              <EmptyTable 
                message="No active temporary assignments"
                subtitle="Click 'Reassign Staff' to create a new temporary assignment"
              />
            ) : (
              <div className="assignments-table-wrapper">
                <table className="assignments-table">
                  <thead>
                    <tr>
                      <th>Staff Member</th>
                      <th>From Branch</th>
                      <th>To Branch</th>
                      <th>Period</th>
                      <th>Status</th>
                      <th>Reason</th>
                      <th>Covering For</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {assignments.map(assignment => (
                      <tr key={assignment.id}>
                        <td>
                          <div className="staff-cell">
                            <div className="staff-avatar">
                              {assignment.staff_name.charAt(0)}
                            </div>
                            <div>
                              <div className="staff-name">{assignment.staff_name}</div>
                              <div className="staff-mobile">{assignment.staff_mobile}</div>
                            </div>
                          </div>
                        </td>
                        <td>
                          <div className="branch-info">
                            <FaBuilding className="branch-icon" />
                            <div>
                              <div className="branch-name">{assignment.original_branch}</div>
                              <div className="branch-city">{assignment.original_branch_city}</div>
                            </div>
                          </div>
                        </td>
                        <td>
                          <div className="branch-info">
                            <FaBuilding className="branch-icon" />
                            <div>
                              <div className="branch-name">{assignment.temp_branch}</div>
                              <div className="branch-city">{assignment.temp_branch_city}</div>
                            </div>
                          </div>
                        </td>
                        <td>
                          <div className="period-info">
                            <div className="date-range">
                              <FaCalendar className="calendar-icon" />
                              <span>{new Date(assignment.start_date).toLocaleDateString()} - {new Date(assignment.end_date).toLocaleDateString()}</span>
                            </div>
                          </div>
                        </td>
                        <td>
                          <div 
                            className="status-badge"
                            style={{ 
                              backgroundColor: `${getStatusColor(assignment.end_date)}15`,
                              color: getStatusColor(assignment.end_date),
                              border: `1px solid ${getStatusColor(assignment.end_date)}40`
                            }}
                          >
                            {getDaysRemaining(assignment.end_date)}
                          </div>
                        </td>
                        <td>
                          <span className="reason-badge">{getReasonLabel(assignment.reason)}</span>
                        </td>
                        <td>
                          {assignment.covering_for ? (
                            <div className="covering-for">
                              <FaUser className="user-icon" />
                              <span>{assignment.covering_for}</span>
                            </div>
                          ) : (
                            <span className="text-muted">-</span>
                          )}
                        </td>
                        <td>
                          <button 
                            className="btn-cancel"
                            onClick={() => handleCancel(assignment.id, assignment.staff_name)}
                            title="Cancel Assignment"
                          >
                            <FaTimesCircle /> Cancel
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
              </div>
            </>
          )}
        </div>

        {/* Create Assignment Modal */}
        {showModal && (
          <div className="modal-overlay" onClick={handleCloseModal}>
            <div className="modal-content temp-assignment-modal" onClick={(e) => e.stopPropagation()}>
              <div className="modal-header">
                <h3><FaExchangeAlt /> Temporarily Reassign Staff</h3>
                <button className="btn-close-modal" onClick={handleCloseModal}>
                  <FaTimes />
                </button>
              </div>
              
              <div className="modal-body">
                <div className="info-banner">
                  <FaInfoCircle />
                  <span>Temporarily assign a staff member from their home branch to cover another branch</span>
                </div>

                <div className="form-group">
                  <label>Staff Member <span className="required">*</span></label>
                  <select 
                    value={formData.staff_id}
                    onChange={(e) => setFormData({...formData, staff_id: e.target.value, covering_for_id: ''})}
                    className="form-select"
                  >
                    <option value="">Select staff member</option>
                    {getAvailableStaff().map(staff => (
                      <option key={staff.id} value={staff.id}>
                        {staff.firstName} {staff.lastName} - {staff.mobile}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="form-group">
                  <label>Assign To Branch <span className="required">*</span></label>
                  <select 
                    value={formData.temp_branch_id}
                    onChange={(e) => setFormData({...formData, temp_branch_id: e.target.value, covering_for_id: ''})}
                    className="form-select"
                  >
                    <option value="">Select branch</option>
                    {getAvailableBranches().map(branch => (
                      <option key={branch.id} value={branch.id}>
                        {branch.name} - {branch.city}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="form-row">
                  <div className="form-group">
                    <label>Start Date <span className="required">*</span></label>
                    <DatePicker
                      selected={formData.start_date}
                      onChange={(date) => setFormData({...formData, start_date: date})}
                      minDate={new Date()}
                      dateFormat="dd/MM/yyyy"
                      className="form-input"
                    />
                  </div>

                  <div className="form-group">
                    <label>End Date <span className="required">*</span></label>
                    <DatePicker
                      selected={formData.end_date}
                      onChange={(date) => setFormData({...formData, end_date: date})}
                      minDate={formData.start_date}
                      dateFormat="dd/MM/yyyy"
                      className="form-input"
                    />
                  </div>
                </div>

                <div className="form-group">
                  <label>Reason for Assignment</label>
                  <select 
                    value={formData.reason}
                    onChange={(e) => setFormData({...formData, reason: e.target.value})}
                    className="form-select"
                  >
                    <option value="leave_coverage">Leave Coverage</option>
                    <option value="training">Training</option>
                    <option value="support">Extra Support</option>
                    <option value="event">Special Event</option>
                    <option value="other">Other</option>
                  </select>
                </div>

                {formData.reason === 'leave_coverage' && formData.temp_branch_id && (
                  <div className="form-group">
                    <label>Covering For (Optional)</label>
                    <select 
                      value={formData.covering_for_id}
                      onChange={(e) => setFormData({...formData, covering_for_id: e.target.value})}
                      className="form-select"
                    >
                      <option value="">Select staff (optional)</option>
                      {getStaffNeedingCoverage().length > 0 ? (
                        getStaffNeedingCoverage().map(staff => (
                          <option key={staff.id} value={staff.id}>
                            {staff.fullName || `${staff.firstName} ${staff.lastName}`.trim() || staff.firstName || staff.lastName}
                          </option>
                        ))
                      ) : (
                        <option value="" disabled>No staff on leave for this branch</option>
                      )}
                    </select>
                  </div>
                )}

                <div className="form-group">
                  <label>Notes (Optional)</label>
                  <textarea 
                    value={formData.notes}
                    onChange={(e) => setFormData({...formData, notes: e.target.value})}
                    className="form-textarea"
                    rows="3"
                    placeholder="Add any additional notes about this assignment..."
                  />
                </div>
              </div>
              
              <div className="modal-actions">
                <button className="btn-secondary" onClick={handleCloseModal}>
                  Cancel
                </button>
                <button className="btn-primary" onClick={handleCreate}>
                  <FaCheckCircle /> Confirm Assignment
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </PageTransition>
  )
}

export default StaffTempAssignment

