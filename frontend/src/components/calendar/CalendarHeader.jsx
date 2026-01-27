import React from 'react'
import { FaCalendarAlt } from 'react-icons/fa'
import './CalendarHeader.css'

const CalendarHeader = ({
  activeView,
  selectedDate,
  fromDate,
  toDate,
  onViewChange,
  onDateChange,
  onNavigate,
  staffMembers = [],
  selectedStaff,
  onStaffChange,
  activeNavButton,
}) => {

  const formatDate = (dateString) => {
    const date = new Date(dateString)
    const day = String(date.getDate()).padStart(2, '0')
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const year = date.getFullYear()
    return `${day}-${month}-${year}`
  }

  const handleToday = () => {
    onNavigate('today')
  }

  const handleBack = () => {
    onNavigate('prev')
  }

  const handleNext = () => {
    onNavigate('next')
  }

  return (
    <header className="appointment-header">
      <div className="header-left">
        <h1 className="header-title">Appointment</h1>
      </div>

      <div className="header-nav-bar">
        <div className="nav-controls-left">
          {/* Navigation Buttons Group */}
          <div className="nav-btn-group">
            <button 
              className={`nav-btn ${activeNavButton === 'today' ? 'active' : ''}`} 
              onClick={handleToday}
            >
              Today
            </button>
            <button 
              className={`nav-btn ${activeNavButton === 'back' ? 'active' : ''}`} 
              onClick={handleBack}
            >
              Previous
            </button>
            <button 
              className={`nav-btn ${activeNavButton === 'next' ? 'active' : ''}`} 
              onClick={handleNext}
            >
              Next
            </button>
          </div>

          {/* Date Input Group */}
          <div className="date-input-group">
            <div className="date-input-wrapper">
              <input
                type="date"
                className="date-picker"
                value={selectedDate}
                onChange={(e) => onDateChange(e.target.value)}
              />
              <span className="date-display">{formatDate(selectedDate)}</span>
              <span className="calendar-icon"><FaCalendarAlt /></span>
            </div>
          </div>

          {/* Staff Select Group */}
          <div className="staff-select-group">
            <select
              className="staff-select"
              value={selectedStaff}
              onChange={(e) => onStaffChange(e.target.value)}
            >
              <option value="all">All Staff</option>
              {staffMembers.map((staff) => (
                <option key={staff.id} value={staff.id}>
                  {staff.firstName} {staff.lastName}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="view-mode-buttons">
          <button
            className={`view-btn ${activeView === 'month' ? 'active' : ''}`}
            onClick={() => onViewChange('month')}
          >
            Month
          </button>
          <button
            className={`view-btn ${activeView === 'week' ? 'active' : ''}`}
            onClick={() => onViewChange('week')}
          >
            Week
          </button>
          <button
            className={`view-btn ${activeView === 'day' ? 'active' : ''}`}
            onClick={() => onViewChange('day')}
          >
            Day
          </button>
        </div>
      </div>
    </header>
  )
}

export default CalendarHeader

