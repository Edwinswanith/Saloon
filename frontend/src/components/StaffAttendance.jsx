import React, { useState, useEffect } from 'react'
import {
  FaBars,
  FaBell,
  FaUser,
  FaCheck,
  FaCloudDownloadAlt,
  FaCalendarAlt,
} from 'react-icons/fa'
import './StaffAttendance.css'
import { apiGet, apiPost } from '../utils/api'

const StaffAttendance = () => {
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0])
  const [staffAttendance, setStaffAttendance] = useState([])
  const [staffMembers, setStaffMembers] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchStaff()
  }, [])

  useEffect(() => {
    if (staffMembers.length > 0) {
      fetchAttendance()
    }
  }, [selectedDate, staffMembers])

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
      
      const response = await apiPost('/api/attendance/mark', {
        staff_id: staffIdStr,
        attendance_date: selectedDate,
        status: status,
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

  const handleDownloadReport = () => {
    try {
      // Create CSV content
      const csvContent = [
        ['Staff Member', 'Date', 'Status', 'Check-In Time', 'Check-Out Time', 'Monthly Present', 'Monthly Absent', 'Monthly Leave'],
        ...staffAttendance.map(staff => [
          staff.name || 'N/A',
          formatDate(selectedDate),
          staff.status || 'Not Marked',
          staff.attendance?.check_in_time || 'N/A',
          staff.attendance?.check_out_time || 'N/A',
          staff.monthlySummary?.present || 0,
          staff.monthlySummary?.absent || 0,
          staff.monthlySummary?.leave || 0,
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

  return (
    <div className="staff-attendance-page">
      {/* Header */}
      <header className="staff-attendance-header">
        <div className="header-left">
          <button className="menu-icon">
            <FaBars />
          </button>
          <h1 className="header-title">Staff Attendance</h1>
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

      <div className="staff-attendance-container">
        {/* Staff Attendance Card */}
        <div className="staff-attendance-card">
          {/* Top Section */}
          <div className="attendance-top-section">
            <h2 className="section-title">Staff Attendance</h2>
            <div className="top-actions">
              <div className="date-picker-wrapper">
                <label className="date-label">Date:</label>
                <div className="date-input-wrapper">
                  <input
                    type="date"
                    className="date-picker"
                    value={selectedDate}
                    onChange={(e) => setSelectedDate(e.target.value)}
                  />
                  <span className="date-display">{formatDate(selectedDate)}</span>
                  <span className="calendar-icon">
                    <FaCalendarAlt />
                  </span>
                </div>
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

          {/* Staff Attendance Table */}
          <div className="table-container">
            <table className="attendance-table">
              <thead>
                <tr>
                  <th>Staff Member</th>
                  <th>Status for {formatDateDisplay(selectedDate)}</th>
                  <th>Monthly Summary (December)</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan="4" className="empty-row">Loading...</td>
                  </tr>
                ) : staffAttendance.length === 0 ? (
                  <tr>
                    <td colSpan="4" className="empty-row">No staff found</td>
                  </tr>
                ) : (
                  staffAttendance.map((staff) => (
                    <tr key={staff.id}>
                      <td className="staff-name">{staff.name}</td>
                      <td>
                        <button className={`status-btn ${staff.status.toLowerCase().replace(' ', '-')}`}>
                          {staff.status}
                        </button>
                      </td>
                      <td>
                        <div className="monthly-summary">
                          <span className="summary-badge present">
                            P: {staff.monthlySummary.present}
                          </span>
                          <span className="summary-badge absent">
                            A: {staff.monthlySummary.absent}
                          </span>
                          <span className="summary-badge leave">
                            L: {staff.monthlySummary.leave}
                          </span>
                        </div>
                      </td>
                      <td>
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

export default StaffAttendance

