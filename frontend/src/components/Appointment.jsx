import React, { useState, useEffect } from 'react'
import { FaBars, FaCalendarAlt, FaPlus, FaTimes, FaEdit, FaShare, FaDownload } from 'react-icons/fa'
import './Appointment.css'
import { API_BASE_URL } from '../config'
import { useAuth } from '../contexts/AuthContext'
import { apiGet, apiPost, apiDelete } from '../utils/api'
import { showSuccess, showError, showWarning } from '../utils/toast.jsx'

const Appointment = ({ setActivePage }) => {
  const { currentBranch } = useAuth()
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0])
  const [viewMode, setViewMode] = useState('day')
  const [selectedStaff, setSelectedStaff] = useState('all')
  const [staffMembers, setStaffMembers] = useState([])
  const [appointments, setAppointments] = useState([])
  const [loading, setLoading] = useState(true)
  const [showBookingModal, setShowBookingModal] = useState(false)
  const [showCancelModal, setShowCancelModal] = useState(false)
  const [showDetailModal, setShowDetailModal] = useState(false)
  const [selectedAppointment, setSelectedAppointment] = useState(null)
  const [appointmentDetail, setAppointmentDetail] = useState(null)
  const [bookingForm, setBookingForm] = useState({
    customer_id: '',
    staff_id: '',
    service_id: '',
    appointment_date: new Date().toISOString().split('T')[0],
    start_time: '',
    notes: '',
  })
  const [customers, setCustomers] = useState([])
  const [services, setServices] = useState([])

  const formatDate = (dateString) => {
    const date = new Date(dateString)
    const day = String(date.getDate()).padStart(2, '0')
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const year = date.getFullYear()
    return `${day}-${month}-${year}`
  }

  const getCurrentDateDisplay = (dateString) => {
    const date = new Date(dateString)
    const days = [
      'Sunday',
      'Monday',
      'Tuesday',
      'Wednesday',
      'Thursday',
      'Friday',
      'Saturday',
    ]
    const months = [
      'Jan',
      'Feb',
      'Mar',
      'Apr',
      'May',
      'Jun',
      'Jul',
      'Aug',
      'Sep',
      'Oct',
      'Nov',
      'Dec',
    ]
    const dayName = days[date.getDay()]
    const monthName = months[date.getMonth()]
    const day = date.getDate()
    return `${dayName} ${monthName} ${day}`
  }

  const getCurrentTime = () => {
    const now = new Date()
    return now.getHours() + now.getMinutes() / 60
  }

  const isCurrentTime = (hour) => {
    // Show green line at 4:00 PM (16:00) as shown in screenshot
    return hour === 16
  }

  const timeSlots = []
  for (let hour = 6; hour <= 22; hour++) {
    const timeLabel =
      hour === 12
        ? '12:00 PM'
        : hour < 12
          ? `${hour}:00 AM`
          : `${hour - 12}:00 PM`
    timeSlots.push({ hour, label: timeLabel })
  }

  const handleToday = () => {
    setSelectedDate(new Date().toISOString().split('T')[0])
  }

  const handleBack = () => {
    const date = new Date(selectedDate)
    date.setDate(date.getDate() - 1)
    setSelectedDate(date.toISOString().split('T')[0])
  }

  const handleNext = () => {
    const date = new Date(selectedDate)
    date.setDate(date.getDate() + 1)
    setSelectedDate(date.toISOString().split('T')[0])
  }

  useEffect(() => {
    fetchStaff()
    fetchCustomers()
    fetchServices()
  }, [])

  useEffect(() => {
    fetchAppointments()
  }, [selectedDate, selectedStaff, viewMode, currentBranch])

  // Listen for branch changes
  useEffect(() => {
    const handleBranchChange = () => {
      fetchStaff()
      fetchCustomers()
      fetchServices()
      fetchAppointments()
    }
    
    window.addEventListener('branchChanged', handleBranchChange)
    return () => window.removeEventListener('branchChanged', handleBranchChange)
  }, [])

  const fetchStaff = async () => {
    try {
      const response = await apiGet('/api/staffs')
      const data = await response.json()
      setStaffMembers(data.staffs || [])
    } catch (error) {
      console.error('Error fetching staff:', error)
    }
  }

  const fetchCustomers = async () => {
    try {
      const response = await apiGet('/api/customers?per_page=100')
      const data = await response.json()
      setCustomers(data.customers || [])
    } catch (error) {
      console.error('Error fetching customers:', error)
    }
  }

  const fetchServices = async () => {
    try {
      const response = await apiGet('/api/services')
      const data = await response.json()
      setServices(data.services || [])
    } catch (error) {
      console.error('Error fetching services:', error)
    }
  }

  const fetchAppointments = async () => {
    try {
      setLoading(true)
      const params = new URLSearchParams({
        start_date: selectedDate,
        end_date: selectedDate,
      })
      if (selectedStaff !== 'all') {
        params.append('staff_id', selectedStaff)
      }
      const response = await apiGet(`/api/appointments?${params}`)
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const data = await response.json()
      console.log('Fetched appointments:', data) // Debug log
      
      // Ensure data is an array and map it correctly
      const appointmentsList = Array.isArray(data) ? data : []
      
      // Map appointments to ensure all fields are present
      const mappedAppointments = appointmentsList.map(apt => ({
        id: apt.id,
        customer_id: apt.customer_id,
        customer_name: apt.customer_name || 'Unknown Customer',
        staff_id: apt.staff_id,
        staff_name: apt.staff_name || 'Unknown Staff',
        service_id: apt.service_id,
        service_name: apt.service_name || 'Service',
        appointment_date: apt.appointment_date,
        start_time: apt.start_time,
        end_time: apt.end_time,
        status: apt.status || 'confirmed',
        notes: apt.notes,
      }))
      
      setAppointments(mappedAppointments)
    } catch (error) {
      console.error('Error fetching appointments:', error)
      setAppointments([])
    } finally {
      setLoading(false)
    }
  }

  const handleBookAppointment = async (e) => {
    e.preventDefault()
    
    // Validate required fields
    if (!bookingForm.customer_id || !bookingForm.staff_id || !bookingForm.appointment_date || !bookingForm.start_time) {
      showError('Please fill in all required fields')
      return
    }
    
    try {
      // Format time correctly (ensure HH:MM:SS format)
      let formattedTime = bookingForm.start_time
      if (formattedTime.length === 5) { // HH:MM format
        formattedTime = formattedTime + ':00'
      }
      
      const response = await apiPost('/api/appointments', {
        customer_id: bookingForm.customer_id,  // Send as string (MongoDB ObjectId)
        staff_id: bookingForm.staff_id,  // Send as string (MongoDB ObjectId)
        service_id: bookingForm.service_id || null,  // Send as string (MongoDB ObjectId) or null
        appointment_date: bookingForm.appointment_date,
        start_time: formattedTime,
        status: 'confirmed',
        notes: bookingForm.notes || '',
      })
      
      const responseData = await response.json()
      
      if (response.ok) {
        showSuccess('Appointment booked successfully!')
        setShowBookingModal(false)
        setBookingForm({
          customer_id: '',
          staff_id: '',
          service_id: '',
          appointment_date: selectedDate,
          start_time: '',
          notes: '',
        })
        // Refresh appointments immediately
        await fetchAppointments()
      } else {
        showError(responseData.error || 'Failed to book appointment')
      }
    } catch (error) {
      console.error('Error booking appointment:', error)
      showError('Error booking appointment: ' + error.message)
    }
  }

  const handleCancelAppointment = async () => {
    if (!selectedAppointment) return
    try {
      const response = await apiDelete(`/api/appointments/${selectedAppointment.id}`)
      if (response.ok) {
        showSuccess('Appointment cancelled successfully!')
        setShowCancelModal(false)
        setSelectedAppointment(null)
        fetchAppointments()
      } else {
        showError('Failed to cancel appointment')
      }
    } catch (error) {
      console.error('Error canceling appointment:', error)
      showError('Error canceling appointment')
    }
  }

  const getAppointmentsForSlot = (hour, staffId) => {
    return appointments.filter((apt) => {
      try {
        // Parse time - handle both HH:MM:SS and HH:MM formats
        let timeStr = apt.start_time
        if (!timeStr) return false
        
        // If time is in HH:MM:SS format, extract HH:MM
        if (timeStr.includes(':')) {
          const timeParts = timeStr.split(':')
          const aptHour = parseInt(timeParts[0], 10)
          const aptStaffId = apt.staff_id ? apt.staff_id.toString() : ''
          const staffIdStr = staffId ? staffId.toString() : ''
          
          return aptHour === hour && aptStaffId === staffIdStr && apt.status !== 'cancelled'
        }
        return false
      } catch (error) {
        console.error('Error parsing appointment time:', error, apt)
        return false
      }
    })
  }

  const openBookingModal = (staffId, hour) => {
    setBookingForm({
      ...bookingForm,
      staff_id: staffId,
      appointment_date: selectedDate,
      start_time: `${String(hour).padStart(2, '0')}:00`,
    })
    setShowBookingModal(true)
  }

  const openDetailModal = async (appointment) => {
    setSelectedAppointment(appointment)
    // Fetch full appointment details including service price
    try {
      const response = await apiGet(`/api/appointments/${appointment.id}`)
      if (response.ok) {
        const data = await response.json()
        setAppointmentDetail(data)
        setShowDetailModal(true)
      } else {
        // Fallback to basic appointment data
        setAppointmentDetail(appointment)
        setShowDetailModal(true)
      }
    } catch (error) {
      console.error('Error fetching appointment details:', error)
      // Fallback to basic appointment data
      setAppointmentDetail(appointment)
      setShowDetailModal(true)
    }
  }

  const openCancelModal = (appointment) => {
    setSelectedAppointment(appointment)
    setShowCancelModal(true)
  }

  const handleEditAppointment = (appointment) => {
    // Store appointment data in localStorage for QuickSale to pick up
    const appointmentData = {
      appointmentId: appointment.id || appointmentDetail?.id,
      customer_id: appointment.customer_id || appointmentDetail?.customer_id,
      customer_name: appointment.customer_name || appointmentDetail?.customer_name,
      customer_mobile: appointment.customer_mobile || appointmentDetail?.customer_mobile,
      staff_id: appointment.staff_id || appointmentDetail?.staff_id,
      staff_name: appointment.staff_name || appointmentDetail?.staff_name,
      service_id: appointment.service_id || appointmentDetail?.service_id,
      service_name: appointment.service_name || appointmentDetail?.service_name,
      service_price: appointment.service_price || appointmentDetail?.service_price,
      appointment_date: appointment.appointment_date || appointmentDetail?.appointment_date,
      start_time: appointment.start_time || appointmentDetail?.start_time,
      notes: appointment.notes || appointmentDetail?.notes,
      status: appointment.status || appointmentDetail?.status,
    }
    localStorage.setItem('edit_appointment_data', JSON.stringify(appointmentData))
    
    // Navigate to QuickSale
    if (setActivePage) {
      setActivePage('quick-sale')
    } else {
      window.dispatchEvent(new CustomEvent('navigateToPage', { detail: { page: 'quick-sale' } }))
    }
    setShowDetailModal(false)
  }

  return (
    <div className="appointment-page">
      {/* Header */}
      <header className="appointment-header">
        <div className="header-left">
          <button className="menu-icon"><FaBars /></button>
          <h1 className="header-title">Appointment</h1>
        </div>

        <div className="header-nav-bar">
          <div className="nav-controls-left">
            {/* Navigation Buttons Group */}
            <div className="nav-btn-group">
              <button className="nav-btn" onClick={handleToday}>
                Today
              </button>
              <button className="nav-btn" onClick={handleBack}>
                Back
              </button>
              <button className="nav-btn" onClick={handleNext}>
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
                  onChange={(e) => setSelectedDate(e.target.value)}
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
                onChange={(e) => setSelectedStaff(e.target.value)}
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

          <div className="current-date-display">
            {getCurrentDateDisplay(selectedDate)}
          </div>

          <div className="view-mode-buttons">
            <button
              className={`view-btn ${viewMode === 'month' ? 'active' : ''}`}
              onClick={() => setViewMode('month')}
            >
              Month
            </button>
            <button
              className={`view-btn ${viewMode === 'week' ? 'active' : ''}`}
              onClick={() => setViewMode('week')}
            >
              Week
            </button>
            <button
              className={`view-btn ${viewMode === 'day' ? 'active' : ''}`}
              onClick={() => setViewMode('day')}
            >
              Day
            </button>
            <button
              className={`view-btn ${viewMode === 'agenda' ? 'active' : ''}`}
              onClick={() => setViewMode('agenda')}
            >
              Agenda
            </button>
          </div>
        </div>
      </header>

      {/* Schedule Grid */}
      <div className="schedule-container">
        <div 
          className="schedule-grid"
          style={{
            gridTemplateColumns: `100px repeat(${staffMembers.length}, minmax(120px, 180px))`
          }}
        >
          {/* Time Column Header */}
          <div className="time-header"></div>

          {/* Staff Headers */}
          {staffMembers.map((staff) => (
            <div key={staff.id} className="staff-header" title={`${staff.firstName} ${staff.lastName || ''}`.trim()}>
              {`${staff.firstName} ${staff.lastName || ''}`.trim()}
            </div>
          ))}

          {/* Time Slots and Grid Cells */}
          {timeSlots.map((timeSlot) => {
            const showCurrentTime = isCurrentTime(timeSlot.hour)
            return (
              <React.Fragment key={timeSlot.hour}>
                {/* Time Label */}
                <div className="time-label">{timeSlot.label}</div>

                {/* Staff Columns */}
                {staffMembers.map((staff, staffIndex) => {
                  const slotAppointments = getAppointmentsForSlot(timeSlot.hour, staff.id)
                  return (
                    <div
                      key={`${timeSlot.hour}-${staff.id}`}
                      className="schedule-cell"
                      onClick={() => openBookingModal(staff.id, timeSlot.hour)}
                      style={{ cursor: 'pointer', position: 'relative' }}
                    >
                      {showCurrentTime && staffIndex === 0 && (
                        <div 
                          className="current-time-line-wrapper"
                          style={{
                            width: `calc(100% * ${staffMembers.length})`
                          }}
                        >
                          <div className="current-time-line">
                            <div className="current-time-marker"></div>
                          </div>
                        </div>
                      )}
                      {slotAppointments.map((apt) => (
                        <div
                          key={apt.id}
                          className={`appointment-block ${apt.status}`}
                          onClick={(e) => {
                            e.stopPropagation()
                            openDetailModal(apt)
                          }}
                          title={`${apt.customer_name} - ${apt.service_name || 'Service'}`}
                        >
                          <div className="appointment-customer">{apt.customer_name}</div>
                          <div className="appointment-service">{apt.service_name || 'Service'}</div>
                          <div className="appointment-time">
                            {new Date(`2000-01-01T${apt.start_time}`).toLocaleTimeString('en-US', {
                              hour: 'numeric',
                              minute: '2-digit',
                            })}
                          </div>
                        </div>
                      ))}
                    </div>
                  )
                })}
              </React.Fragment>
            )
          })}
        </div>
      </div>

      {/* Booking Modal */}
      {showBookingModal && (
        <div className="modal-overlay" onClick={() => setShowBookingModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Book Appointment</h2>
              <button className="close-btn" onClick={() => setShowBookingModal(false)}>
                <FaTimes />
              </button>
            </div>
            <form onSubmit={handleBookAppointment}>
              <div className="form-group">
                <label>Customer *</label>
                <select
                  required
                  value={bookingForm.customer_id}
                  onChange={(e) => setBookingForm({ ...bookingForm, customer_id: e.target.value })}
                >
                  <option value="">Select Customer</option>
                  {customers.map((customer) => (
                    <option key={customer.id} value={customer.id}>
                      {customer.firstName} {customer.lastName} - {customer.mobile}
                    </option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label>Service</label>
                <select
                  value={bookingForm.service_id}
                  onChange={(e) => setBookingForm({ ...bookingForm, service_id: e.target.value })}
                >
                  <option value="">Select Service</option>
                  {services.map((service) => (
                    <option key={service.id} value={service.id}>
                      {service.name} - ₹{service.price}
                    </option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label>Date *</label>
                <input
                  type="date"
                  required
                  value={bookingForm.appointment_date}
                  onChange={(e) => setBookingForm({ ...bookingForm, appointment_date: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label>Time *</label>
                <input
                  type="time"
                  required
                  value={bookingForm.start_time}
                  onChange={(e) => setBookingForm({ ...bookingForm, start_time: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label>Notes</label>
                <textarea
                  value={bookingForm.notes}
                  onChange={(e) => setBookingForm({ ...bookingForm, notes: e.target.value })}
                  rows="3"
                />
              </div>
              <div className="modal-actions">
                <button type="button" onClick={() => setShowBookingModal(false)}>
                  Cancel
                </button>
                <button type="submit">Book Appointment</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Appointment Detail Modal (Invoice Style) */}
      {showDetailModal && appointmentDetail && (
        <div className="modal-overlay" onClick={() => setShowDetailModal(false)}>
          <div className="appointment-invoice-modal" onClick={(e) => e.stopPropagation()}>
            <div className="invoice-header">
              <div className="invoice-customer-info">
                <h3>{appointmentDetail.customer_name || 'Customer'} - {appointmentDetail.customer_mobile ? `+91 ${appointmentDetail.customer_mobile}` : ''}</h3>
                <p className="invoice-date">Date: {appointmentDetail.appointment_date ? new Date(appointmentDetail.appointment_date).toISOString().split('T')[0] : 'N/A'}</p>
              </div>
              <button className="close-btn" onClick={() => setShowDetailModal(false)}>
                <FaTimes />
              </button>
            </div>
            
            <div className="invoice-table-container">
              <table className="invoice-table">
                <thead>
                  <tr>
                    <th>No.</th>
                    <th>Service</th>
                    <th>Staff</th>
                    <th>Price (₹)</th>
                    <th>Total (₹)</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td>1</td>
                    <td>{appointmentDetail.service_name || 'Service'}</td>
                    <td>{appointmentDetail.staff_name || 'N/A'}</td>
                    <td>{appointmentDetail.service_price ? appointmentDetail.service_price.toFixed(2) : '0.00'}</td>
                    <td>{(() => {
                      const price = appointmentDetail.service_price || 0
                      const tax = price * 0.18 // 18% GST
                      return (price + tax).toFixed(2)
                    })()}</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <div className="invoice-summary">
              <div className="summary-row">
                <span className="summary-label">Total:</span>
                <span className="summary-value">₹ {appointmentDetail.service_price ? appointmentDetail.service_price.toFixed(2) : '0.00'}</span>
              </div>
              <div className="summary-row">
                <span className="summary-label">Discount:</span>
                <span className="summary-value">₹ 0.00</span>
              </div>
              <div className="summary-row">
                <span className="summary-label">IGST / CGST:</span>
                <span className="summary-value">₹ {(() => {
                  const price = appointmentDetail.service_price || 0
                  return (price * 0.18).toFixed(2)
                })()}</span>
              </div>
              <div className="summary-row final">
                <span className="summary-label">Grand Total:</span>
                <span className="summary-value">₹ {(() => {
                  const price = appointmentDetail.service_price || 0
                  const tax = price * 0.18
                  return (price + tax).toFixed(2)
                })()}</span>
              </div>
            </div>

            <div className="invoice-actions">
              <button className="invoice-action-btn edit-btn" onClick={() => handleEditAppointment(appointmentDetail)}>
                <FaEdit /> Edit
              </button>
              <button className="invoice-action-btn share-btn">
                <FaShare /> Share Invoice
              </button>
              <button className="invoice-action-btn download-btn">
                <FaDownload /> Download Invoice
              </button>
              <button className="invoice-action-btn close-btn" onClick={() => setShowDetailModal(false)}>
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Cancel Modal */}
      {showCancelModal && selectedAppointment && (
        <div className="modal-overlay" onClick={() => setShowCancelModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Cancel Appointment</h2>
              <button className="close-btn" onClick={() => setShowCancelModal(false)}>
                <FaTimes />
              </button>
            </div>
            <div className="appointment-details">
              <p><strong>Customer:</strong> {selectedAppointment.customer_name}</p>
              <p><strong>Service:</strong> {selectedAppointment.service_name || 'N/A'}</p>
              <p><strong>Date:</strong> {selectedAppointment.appointment_date}</p>
              <p><strong>Time:</strong> {new Date(`2000-01-01T${selectedAppointment.start_time}`).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })}</p>
              <p><strong>Status:</strong> {selectedAppointment.status}</p>
            </div>
            <div className="modal-actions">
              <button type="button" onClick={() => setShowCancelModal(false)}>
                Close
              </button>
              <button type="button" className="cancel-btn" onClick={handleCancelAppointment}>
                Cancel Appointment
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default Appointment

