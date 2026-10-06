import React, { useState, useEffect } from 'react'
import {
  FaCheck,
  FaCloudDownloadAlt,
  FaCalendarAlt,
  FaRegCalendarTimes,
  FaClock,
  FaInfoCircle,
  FaUserCheck,
  FaUserTimes,
  FaUsers,
} from 'react-icons/fa'
import './StaffAttendance.css'
import { apiGet, apiPost } from '../utils/api'
import { useAuth } from '../contexts/AuthContext'
import ClassicDatePicker from './shared/ClassicDatePicker'

const StaffAttendance = () => {
  const { currentBranch, user } = useAuth()
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0])
  const [staffAttendance, setStaffAttendance] = useState([])
  const [staffMembers, setStaffMembers] = useState([])
  const [myAttendance, setMyAttendance] = useState(null)
  const [statusFilter, setStatusFilter] = useState('all')
  const [loading, setLoading] = useState(true)
  const [submittingLeave, setSubmittingLeave] = useState(false)
  const [leaveForm, setLeaveForm] = useState({
    date: new Date().toISOString().split('T')[0],
    leave_type: 'casual',
    reason: ''
  })

  useEffect(() => {
    if (user?.role === 'staff') {
      fetchMyAttendance()
    } else {
      fetchStaff()
    }
  }, [currentBranch, user])

  useEffect(() => {
    if (user?.role !== 'staff' && staffMembers.length > 0) {
      fetchAttendance()
    }
  }, [selectedDate, staffMembers, currentBranch, user])

  // Listen for branch changes
  useEffect(() => {
    const handleBranchChange = () => {
      console.log('[StaffAttendance] Branch changed, refreshing data...')
      if (user?.role === 'staff') {
        fetchMyAttendance()
      } else {
        fetchStaff()
      }
    }
    
    window.addEventListener('branchChanged', handleBranchChange)
    return () => window.removeEventListener('branchChanged', handleBranchChange)
  }, [currentBranch])

  const fetchMyAttendance = async () => {
    try {
      setLoading(true)
      const response = await apiGet('/api/attendance/me')
      const data = await response.json()
      setMyAttendance(data)
    } catch (error) {
      console.error('Error fetching my attendance:', error)
      setMyAttendance(null)
    } finally {
      setLoading(false)
    }
  }

  const handleSelfAttendance = async (action) => {
    try {
      const response = await apiPost(`/api/attendance/me/${action}`, {})
      const data = await response.json()
      if (!response.ok) {
        alert(data.error || 'Attendance action failed')
        return
      }
      await fetchMyAttendance()
    } catch (error) {
      console.error('Error updating my attendance:', error)
      alert(error.message)
    }
  }

  const handleSelfLeave = async () => {
    const reason = leaveForm.reason.trim()
    if (!reason) {
      alert('Please enter a short leave reason')
      return
    }

    try {
      setSubmittingLeave(true)
      const response = await apiPost('/api/attendance/me/leave', {
        date: leaveForm.date,
        leave_type: leaveForm.leave_type,
        reason
      })
      const data = await response.json()
      if (!response.ok) {
        alert(data.error || 'Leave entry failed')
        return
      }
      setLeaveForm({
        date: new Date().toISOString().split('T')[0],
        leave_type: 'casual',
        reason: ''
      })
      await fetchMyAttendance()
    } catch (error) {
      console.error('Error recording leave:', error)
      alert(error.message)
    } finally {
      setSubmittingLeave(false)
    }
  }

  const fetchStaff = async () => {
    try {
      const response = await apiGet('/api/staffs')
      const data = await response.json()
      setStaffMembers(data.staffs || [])
    } catch (error) {
      console.error('Error fetching staff:', error)
    }
  }

  const fetchAttendance = async () => {
    try {
      setLoading(true)
      const response = await apiGet(`/api/attendance?date=${selectedDate}`)
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      const data = await response.json()
      
      // Backend returns array directly
      const attendanceRecords = Array.isArray(data) ? data : (data.attendance || [])
      
      // Combine staff with attendance data
      const attendanceMap = {}
      attendanceRecords.forEach((att) => {
        attendanceMap[att.staff_id] = att
      })

      const combined = staffMembers.map((staff) => ({
        id: staff.id,
        name: `${staff.firstName} ${staff.lastName}`,
        attendance: attendanceMap[staff.id] || null,
        status: attendanceMap[staff.id]?.status || 'Not Marked',
        monthlySummary: { present: 0, absent: 0, leave: 0 }, // TODO: fetch from API
      }))

      setStaffAttendance(combined)
    } catch (error) {
      console.error('Error fetching attendance:', error)
      setStaffAttendance([])
    } finally {
      setLoading(false)
    }
  }

  const markAttendance = async (staffId, status) => {
    try {
      // Ensure staffId is a string (MongoDB ObjectId)
      const staffIdStr = String(staffId)
      let notes = ''
      if (status === 'leave') {
        const reason = window.prompt('Enter leave reason for owner/manager record:')
        if (reason === null) return
        notes = reason.trim()
        if (!notes) {
          alert('Leave reason is required')
          return
        }
      } else if (status === 'absent') {
        const reason = window.prompt('Optional note for absence:', '')
        if (reason === null) return
        notes = reason.trim()
      }
      
      const response = await apiPost('/api/attendance/mark', {
        staff_id: staffIdStr,
        attendance_date: selectedDate,
        status: status,
        notes,
      })
      
      const data = await response.json()
      
      if (response.ok) {
        // Show success message
        console.log('Attendance marked successfully:', data)
        // Refresh attendance data
        await fetchAttendance()
      } else {
        // Show actual error message from backend
        const errorMsg = data.error || 'Failed to mark attendance'
        console.error('Failed to mark attendance:', errorMsg)
        alert(`Failed to mark attendance: ${errorMsg}`)
      }
    } catch (error) {
      console.error('Error marking attendance:', error)
      alert(`Error marking attendance: ${error.message}`)
    }
  }

  const markAllPresent = async () => {
    if (!window.confirm('Mark all staff as present for today?')) {
      return
    }
    try {
      await Promise.all(
        staffMembers.map((staff) =>
          markAttendance(staff.id, 'present')
        )
      )
      fetchAttendance()
    } catch (error) {
      console.error('Error marking all present:', error)
      alert('Error marking all present')
    }
  }

  const formatDate = (dateString) => {
    const date = new Date(dateString)
    const day = String(date.getDate()).padStart(2, '0')
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const year = date.getFullYear()
    return `${day}-${month}-${year}`
  }

  const formatDateDisplay = (dateString) => {
    const date = new Date(dateString)
    const day = date.getDate()
    const month = date.toLocaleString('default', { month: 'short' })
    const year = date.getFullYear().toString().slice(-2)
    return `${day} ${month}, ${year}`
  }

  const getSelectedMonthName = () => {
    const date = new Date(selectedDate)
    return date.toLocaleString('default', { month: 'long' })
  }

  const getStatusKey = (status) => (status || 'Not Marked').toLowerCase().replace(/\s+/g, '-')

  const getInitials = (name = '') => {
    const parts = name.trim().split(/\s+/).filter(Boolean)
    if (parts.length === 0) return 'ST'
    return parts.slice(0, 2).map(part => part[0]).join('').toUpperCase()
  }

  const attendanceOverview = staffAttendance.reduce((summary, staff) => {
    const statusKey = getStatusKey(staff.status)
    summary.total += 1
    if (statusKey === 'present') summary.present += 1
    else if (statusKey === 'absent') summary.absent += 1
    else if (statusKey === 'leave') summary.leave += 1
    else summary.notMarked += 1

    if (staff.attendance?.check_in_time) summary.checkedIn += 1
    if (staff.attendance?.check_in_time && !staff.attendance?.check_out_time) summary.pendingCheckout += 1
    return summary
  }, {
    total: 0,
    present: 0,
    absent: 0,
    leave: 0,
    notMarked: 0,
    checkedIn: 0,
    pendingCheckout: 0,
  })

  const filteredAttendance = statusFilter === 'all'
    ? staffAttendance
    : staffAttendance.filter(staff => getStatusKey(staff.status) === statusFilter)

  const overviewCards = [
    { key: 'total', label: 'Total Staff', value: attendanceOverview.total, icon: <FaUsers />, tone: 'total' },
    { key: 'present', label: 'Present', value: attendanceOverview.present, icon: <FaUserCheck />, tone: 'present' },
    { key: 'leave', label: 'Leave', value: attendanceOverview.leave, icon: <FaRegCalendarTimes />, tone: 'leave' },
    { key: 'absent', label: 'Absent', value: attendanceOverview.absent, icon: <FaUserTimes />, tone: 'absent' },
    { key: 'not-marked', label: 'Not Marked', value: attendanceOverview.notMarked, icon: <FaInfoCircle />, tone: 'not-marked' },
  ]

  const statusFilters = [
    { key: 'all', label: 'All', count: attendanceOverview.total },
    { key: 'present', label: 'Present', count: attendanceOverview.present },
    { key: 'leave', label: 'Leave', count: attendanceOverview.leave },
    { key: 'absent', label: 'Absent', count: attendanceOverview.absent },
    { key: 'not-marked', label: 'Not Marked', count: attendanceOverview.notMarked },
  ]

  const handleDownloadReport = () => {
    try {
      // Create CSV content
      const csvContent = [
        ['Staff Member', 'Date', 'Status', 'Check-In Time', 'Check-Out Time', 'Reason / Notes'],
        ...staffAttendance.map(staff => [
          staff.name || 'N/A',
          formatDate(selectedDate),
          staff.status || 'Not Marked',
          staff.attendance?.check_in_time || 'N/A',
          staff.attendance?.check_out_time || 'N/A',
          staff.attendance?.notes || '',
        ])
      ].map(row => {
        // Escape commas and quotes in CSV
        return row.map(cell => {
          const cellStr = String(cell || '')
          if (cellStr.includes(',') || cellStr.includes('"') || cellStr.includes('\n')) {
            return `"${cellStr.replace(/"/g, '""')}"`
          }
          return cellStr
        }).join(',')
      }).join('\n')
      
      // Download CSV
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      const fileName = `staff-attendance-${selectedDate}-${new Date().toISOString().split('T')[0]}.csv`
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

  if (user?.role === 'staff') {
    return (
      <div className="staff-attendance-page">
        <div className="staff-attendance-container">
          <div className="staff-attendance-card">
            <div className="attendance-top-section">
              <h2 className="section-title">My Attendance</h2>
              <div className="top-actions">
                <button
                  className="mark-all-btn"
                  onClick={() => handleSelfAttendance('check-in')}
                  disabled={loading || myAttendance?.today?.check_in_time}
                >
                  <FaCheck />
                  Check In
                </button>
                <button
                  className="download-btn"
                  onClick={() => handleSelfAttendance('check-out')}
                  disabled={loading || !myAttendance?.today?.check_in_time || myAttendance?.today?.check_out_time}
                >
                  <FaCalendarAlt />
                  Check Out
                </button>
              </div>
            </div>

            <div className="my-attendance-summary">
              <div className="attendance-summary-card">
                <span>Today Status</span>
                <strong>{myAttendance?.today?.status || 'not_marked'}</strong>
              </div>
              <div className="attendance-summary-card">
                <span>Check In</span>
                <strong>{myAttendance?.today?.check_in_time || '-'}</strong>
              </div>
              <div className="attendance-summary-card">
                <span>Check Out</span>
                <strong>{myAttendance?.today?.check_out_time || '-'}</strong>
              </div>
              <div className="attendance-summary-card">
                <span>Today Note</span>
                <strong className="attendance-note-value">{myAttendance?.today?.notes || '-'}</strong>
              </div>
            </div>

            <div className="leave-entry-panel">
              <div className="leave-entry-header">
                <h3>Apply Leave</h3>
              </div>
              <div className="leave-entry-form">
                <div className="leave-field">
                  <label>Date</label>
                  <ClassicDatePicker
                    value={leaveForm.date}
                    onChange={(v) => v && setLeaveForm({ ...leaveForm, date: v })}
                    placeholder="Leave date"
                    allowEmpty={false}
                  />
                </div>
                <div className="leave-field">
                  <label>Type</label>
                  <select
                    value={leaveForm.leave_type}
                    onChange={(e) => setLeaveForm({ ...leaveForm, leave_type: e.target.value })}
                  >
                    <option value="casual">Casual</option>
                    <option value="sick">Sick</option>
                    <option value="vacation">Vacation</option>
                    <option value="emergency">Emergency</option>
                    <option value="other">Other</option>
                  </select>
                </div>
                <div className="leave-field leave-reason-field">
                  <label>Reason</label>
                  <input
                    type="text"
                    value={leaveForm.reason}
                    onChange={(e) => setLeaveForm({ ...leaveForm, reason: e.target.value })}
                    placeholder="Short reason for leave"
                    maxLength="180"
                  />
                </div>
                <button
                  className="leave-submit-btn"
                  onClick={handleSelfLeave}
                  disabled={submittingLeave || loading}
                >
                  <FaRegCalendarTimes />
                  {submittingLeave ? 'Saving...' : 'Apply Leave'}
                </button>
              </div>
            </div>

            <div className="table-container">
              <table className="attendance-table">
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Status</th>
                    <th>Check-In</th>
                    <th>Check-Out</th>
                    <th>Notes</th>
                  </tr>
                </thead>
                <tbody>
                  {loading ? (
                    <tr><td colSpan="5" className="empty-row">Loading...</td></tr>
                  ) : (myAttendance?.records || []).length === 0 ? (
                    <tr><td colSpan="5" className="empty-row">No attendance records found</td></tr>
                  ) : (
                    myAttendance.records.map(record => (
                      <tr key={record.id}>
                        <td>{record.attendance_date}</td>
                        <td>{record.status}</td>
                        <td>{record.check_in_time || '-'}</td>
                        <td>{record.check_out_time || '-'}</td>
                        <td>{record.notes || '-'}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="staff-attendance-page">
      <div className="staff-attendance-container">
        <div className="staff-attendance-card owner-attendance-card">
          <div className="owner-attendance-header">
            <div className="owner-attendance-title-block">
              <h2 className="section-title">Staff Attendance</h2>
              <div className="owner-attendance-date">
                <FaCalendarAlt />
                {formatDateDisplay(selectedDate)}
              </div>
            </div>
            <div className="top-actions">
              <div className="date-picker-wrapper owner-date-filter">
                <label className="date-label">Date:</label>
                <ClassicDatePicker
                  value={selectedDate}
                  onChange={(v) => v && setSelectedDate(v)}
                  placeholder="Select date"
                  allowEmpty={false}
                />
              </div>
              <button className="mark-all-btn" onClick={markAllPresent}>
                <FaCheck />
                Mark All Present
              </button>
              <button className="download-btn" onClick={handleDownloadReport}>
                <FaCloudDownloadAlt />
                Download Report
              </button>
            </div>
          </div>

          <div className="attendance-overview-grid">
            {overviewCards.map(card => (
              <button
                key={card.key}
                type="button"
                className={`attendance-overview-card ${card.tone} ${statusFilter === card.key ? 'active' : ''}`}
                onClick={() => setStatusFilter(card.key)}
              >
                <span className="overview-card-icon">{card.icon}</span>
                <span className="overview-card-label">{card.label}</span>
                <strong>{card.value}</strong>
              </button>
            ))}
          </div>

          <div className="attendance-board-toolbar">
            <div className="attendance-filter-pills">
              {statusFilters.map(filter => (
                <button
                  key={filter.key}
                  type="button"
                  className={`attendance-filter-pill ${statusFilter === filter.key ? 'active' : ''}`}
                  onClick={() => setStatusFilter(filter.key)}
                >
                  {filter.label}
                  <span>{filter.count}</span>
                </button>
              ))}
            </div>
            <div className="attendance-time-summary">
              <span><FaClock /> Checked in: {attendanceOverview.checkedIn}</span>
              <span>Pending checkout: {attendanceOverview.pendingCheckout}</span>
            </div>
          </div>

          <div className="table-container owner-attendance-table-wrap">
            <table className="attendance-table owner-attendance-table">
              <thead>
                <tr>
                  <th>Staff</th>
                  <th>Status</th>
                  <th>Check-In</th>
                  <th>Check-Out</th>
                  <th>Leave / Notes</th>
                  <th>Quick Mark</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan="6" className="empty-row">Loading...</td>
                  </tr>
                ) : filteredAttendance.length === 0 ? (
                  <tr>
                    <td colSpan="6" className="empty-row">No staff found for this selection</td>
                  </tr>
                ) : (
                  filteredAttendance.map((staff) => {
                    const statusKey = getStatusKey(staff.status)
                    return (
                    <tr key={staff.id}>
                      <td data-label="Staff" className="staff-name owner-staff-cell">
                        <span className="staff-avatar">{getInitials(staff.name)}</span>
                        <span>
                          <strong>{staff.name}</strong>
                          <small>{staff.attendance ? 'Attendance recorded' : 'No entry yet'}</small>
                        </span>
                      </td>
                      <td data-label="Status">
                        <span className={`status-btn ${statusKey}`}>
                          {staff.status}
                        </span>
                      </td>
                      <td data-label="Check-In">{staff.attendance?.check_in_time || '-'}</td>
                      <td data-label="Check-Out">{staff.attendance?.check_out_time || '-'}</td>
                      <td data-label="Leave / Notes" className="attendance-notes-cell">
                        <div className={`owner-note-box ${staff.attendance?.notes ? 'has-note' : 'empty-note'}`}>
                          {staff.attendance?.notes || 'No note added'}
                        </div>
                      </td>
                      <td data-label="Quick Mark">
                        <div className="action-buttons">
                          <button
                            className="action-btn present-btn"
                            onClick={() => markAttendance(staff.id, 'present')}
                          >
                            Present
                          </button>
                          <button
                            className="action-btn absent-btn"
                            onClick={() => markAttendance(staff.id, 'absent')}
                          >
                            Absent
                          </button>
                          <button
                            className="action-btn leave-btn"
                            onClick={() => markAttendance(staff.id, 'leave')}
                          >
                            Leave
                          </button>
                        </div>
                      </td>
                    </tr>
                    )
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  )
}

export default StaffAttendance

