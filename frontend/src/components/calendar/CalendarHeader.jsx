import React from 'react'
import CompactSelect from '../shared/CompactSelect'
import ClassicDatePicker from '../shared/ClassicDatePicker'
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

  const handleToday = () => onNavigate('today')
  const handleBack = () => onNavigate('prev')
  const handleNext = () => onNavigate('next')

  const staffOptions = [
    { value: 'all', label: 'All Staff' },
    ...staffMembers.map(s => ({
      value: s.id,
      label: `${s.firstName || ''} ${s.lastName || ''}`.trim() || 'Staff',
    })),
  ]

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

          {/* Date Picker — classic compact date picker matching the rest of the app */}
          <div className="date-input-group" style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            <label className="date-label" style={{ fontSize: 14, fontWeight: 600, color: '#374151' }}>Date:</label>
            <ClassicDatePicker
              value={selectedDate}
              onChange={(v) => v && onDateChange(v)}
              placeholder="Select date"
              allowEmpty={false}
            />
          </div>

          {/* Staff Select — compact custom dropdown */}
          <div className="staff-select-group" style={{ width: 160, flexShrink: 0 }}>
            <CompactSelect
              className="cal-staff-select"
              value={selectedStaff || 'all'}
              onChange={(v) => onStaffChange(v)}
              options={staffOptions}
              placeholder="All Staff"
            />
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
