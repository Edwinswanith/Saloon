import React, { useState, useEffect } from 'react'
import { FaTimes, FaEdit, FaShare, FaDownload, FaArrowLeft } from 'react-icons/fa'
import './Appointment.css'
import { API_BASE_URL } from '../config'
import { useAuth } from '../contexts/AuthContext'
import { apiGet, apiPost, apiDelete } from '../utils/api'
import { showSuccess, showError, showWarning } from '../utils/toast.jsx'
import InvoicePreview from './InvoicePreview'
import CalendarHeader from './calendar/CalendarHeader'
import { useCalendarView } from './calendar/CalendarView'
import { getWeekDates, getMonthGridDates } from './calendar/calendarUtils'

const Appointment = ({ setActivePage }) => {
  const { currentBranch } = useAuth()
  const [selectedStaff, setSelectedStaff] = useState('all')
  const [activeNavButton, setActiveNavButton] = useState('today')
  
  // Use calendar view hook for state management
  const calendarView = useCalendarView('day', null, (range) => {
    // Date range change callback - will trigger fetchAppointments via useEffect
  })
  
  const { activeView, selectedDate, fromDate, toDate, setActiveView, setSelectedDate, navigate } = calendarView
  const [staffMembers, setStaffMembers] = useState([])
  const [appointments, setAppointments] = useState([])
  const [loading, setLoading] = useState(true)
  const [showBookingModal, setShowBookingModal] = useState(false)
  const [showCancelModal, setShowCancelModal] = useState(false)
  const [showDetailModal, setShowDetailModal] = useState(false)
  const [selectedAppointment, setSelectedAppointment] = useState(null)
  const [appointmentDetail, setAppointmentDetail] = useState(null)
  const [invoiceData, setInvoiceData] = useState(null)
  const [loadingInvoice, setLoadingInvoice] = useState(false)
  const [billId, setBillId] = useState(null)
  const [showInvoiceView, setShowInvoiceView] = useState(false) // Track whether to show invoice or appointment details
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
    navigate('today')
    setActiveNavButton('today')
  }

  const handleBack = () => {
    navigate('prev')
    setActiveNavButton('back')
  }

  const handleNext = () => {
    navigate('next')
    setActiveNavButton('next')
  }

  const handleViewChange = (view) => {
    setActiveView(view)
    setActiveNavButton('today')
  }

  const handleDateChange = (date) => {
    setSelectedDate(date)
    setActiveNavButton('today')
  }

  const handleNavigate = (direction) => {
    navigate(direction)
    if (direction === 'today') {
      setActiveNavButton('today')
    } else if (direction === 'prev') {
      setActiveNavButton('back')
    } else if (direction === 'next') {
      setActiveNavButton('next')
    }
  }

  useEffect(() => {
    fetchStaff()
    fetchCustomers()
    fetchServices()
  }, [])

  useEffect(() => {
    if (fromDate && toDate) {
      fetchAppointments()
    }
  }, [fromDate, toDate, selectedStaff, currentBranch, activeView])

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
    if (!fromDate || !toDate) return

    try {
      setLoading(true)
      const params = new URLSearchParams({
        start_date: fromDate,
        end_date: toDate,
        // Request more items for month view to ensure all appointments are fetched
        per_page: activeView === 'month' ? '200' : '100',
      })
      if (selectedStaff !== 'all') {
        params.append('staff_id', selectedStaff)
      }
      const response = await apiGet(`/api/appointments?${params}`)
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const responseData = await response.json()
      console.log('Fetched appointments:', responseData) // Debug log
      
      // Backend returns {data: [...], pagination: {...}}, so extract the data array
      const appointmentsList = responseData.data || (Array.isArray(responseData) ? responseData : [])
      console.log('Extracted appointments list:', appointmentsList, 'Count:', appointmentsList.length)
      
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

  const getAppointmentsForSlot = (hour, staffId, date = null) => {
    return appointments.filter((apt) => {
      try {
        // Filter by date if provided (for week/month views)
        if (date) {
          const aptDate = apt.appointment_date ? new Date(apt.appointment_date).toISOString().split('T')[0] : null
          if (aptDate !== date) return false
        }
        
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

  const getAppointmentsForDate = (date, staffId = null) => {
    return appointments.filter((apt) => {
      try {
        const aptDate = apt.appointment_date ? new Date(apt.appointment_date).toISOString().split('T')[0] : null
        if (aptDate !== date) return false
        
        if (staffId) {
          const aptStaffId = apt.staff_id ? apt.staff_id.toString() : ''
          const staffIdStr = staffId.toString()
          if (aptStaffId !== staffIdStr) return false
        }
        
        return apt.status !== 'cancelled'
      } catch (error) {
        console.error('Error filtering appointments by date:', error, apt)
        return false
      }
    })
  }

  const openBookingModal = (staffId, hour, date = null) => {
    setBookingForm({
      ...bookingForm,
      staff_id: staffId,
      appointment_date: date || selectedDate,
      start_time: hour ? `${String(hour).padStart(2, '0')}:00` : '',
    })
    setShowBookingModal(true)
  }

  const openDetailModal = async (appointment) => {
    setSelectedAppointment(appointment)
    setShowInvoiceView(false) // Start with appointment details view
    setInvoiceData(null)
    setBillId(null)
    setLoadingInvoice(false)
    
    // Fetch full appointment details including service price
    try {
      const response = await apiGet(`/api/appointments/${appointment.id}`)
      if (response.ok) {
        const data = await response.json()
        setAppointmentDetail(data)
        setShowDetailModal(true)
        
        // Check if bill exists (but don't fetch invoice data yet)
        try {
          const billResponse = await apiGet(`/api/appointments/${appointment.id}/bill`)
          if (billResponse.ok) {
            const billData = await billResponse.json()
            if (billData.bill_id) {
              setBillId(billData.bill_id)
            }
          }
        } catch (billError) {
          console.error('Error checking bill for appointment:', billError)
        }
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

  const handleViewBill = async () => {
    if (!billId) {
      showError('No bill found for this appointment')
      return
    }
    
    setLoadingInvoice(true)
    setShowInvoiceView(true)
    
    try {
      await fetchInvoiceData(billId)
    } catch (error) {
      console.error('Error fetching invoice data:', error)
      showError('Failed to load invoice data')
      setLoadingInvoice(false)
    }
  }

  const handleBackToAppointment = () => {
    setShowInvoiceView(false)
    setInvoiceData(null)
  }

  const fetchInvoiceData = async (billId) => {
    try {
      setLoadingInvoice(true)
      const response = await apiGet(`/api/bills/${billId}/invoice`)
      if (response.ok) {
        const data = await response.json()
        setInvoiceData(data)
      } else {
        showError('Failed to load invoice data')
      }
    } catch (error) {
      console.error('Error fetching invoice data:', error)
      showError('Error loading invoice data')
    } finally {
      setLoadingInvoice(false)
    }
  }

  const handleDownloadInvoice = async () => {
    if (!billId) {
      showError('No bill found for this appointment')
      return
    }

    try {
      // Use the correct token key (auth_token) and branch ID
      const token = localStorage.getItem('auth_token') || localStorage.getItem('token')
      let branchId = currentBranch?.id
      if (!branchId) {
        const storedBranch = localStorage.getItem('current_branch')
        if (storedBranch) {
          try {
            const branch = JSON.parse(storedBranch)
            branchId = branch?.id
          } catch (e) {
            console.error('Error parsing stored branch:', e)
          }
        }
      }
      
      if (!token) {
        showError('Authentication token not found. Please log in again.')
        return
      }
      
      const response = await fetch(`${API_BASE_URL}/api/bills/${billId}/invoice/pdf`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'X-Branch-Id': branchId || ''
        }
      })

      if (response.ok) {
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `invoice_${invoiceData?.bill_number || invoiceData?.invoice_number || billId}.pdf`
        document.body.appendChild(a)
        a.click()
        window.URL.revokeObjectURL(url)
        document.body.removeChild(a)
        showSuccess('Invoice downloaded successfully')
      } else {
        const errorText = await response.text().catch(() => 'Failed to download invoice')
        console.error('Failed to download invoice:', response.status, errorText)
        if (response.status === 401) {
          showError('Unauthorized. Please log in again.')
        } else {
          showError(`Failed to download invoice: ${errorText}`)
        }
      }
    } catch (error) {
      console.error('Error downloading invoice:', error)
      showError('Error downloading invoice')
    }
  }

  const handleReviewUs = () => {
    // Placeholder for review functionality
    showWarning('Review functionality coming soon')
  }

  const openCancelModal = (appointment) => {
    setSelectedAppointment(appointment)
    setShowCancelModal(true)
  }

  const handleEditAppointment = async (appointment) => {
    const appointmentId = appointment.id || appointmentDetail?.id

    // Store appointment data in localStorage for QuickSale to pick up
    const appointmentData = {
      appointmentId: appointmentId,
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

    // Try to fetch the associated bill to get all items and payment_mode
    try {
      console.log('[APPOINTMENT EDIT] Fetching bill for appointment_id:', appointmentId)
      const billResponse = await apiGet(`/api/bills?appointment_id=${appointmentId}`)
      console.log('[APPOINTMENT EDIT] Bill response status:', billResponse.status, billResponse.ok)
      
      if (billResponse.ok) {
        const billData = await billResponse.json()
        console.log('[APPOINTMENT EDIT] Bill response data:', billData)
        
        // Handle both 'data' and 'bills' response formats
        const billsArray = billData.data || billData.bills || []
        console.log('[APPOINTMENT EDIT] Bills array:', billsArray)
        
        if (billsArray && billsArray.length > 0) {
          const bill = billsArray[0]
          console.log('[APPOINTMENT EDIT] Found associated bill:', bill)
          console.log('[APPOINTMENT EDIT] Bill has items?', !!bill.items)
          console.log('[APPOINTMENT EDIT] Bill items count:', bill.items ? bill.items.length : 0)
          console.log('[APPOINTMENT EDIT] Bill items:', bill.items)

          // Add bill data to appointment data
          appointmentData.bill_id = bill.id
          appointmentData.payment_mode = bill.payment_mode
          appointmentData.booking_note = bill.booking_note
          appointmentData.booking_status = bill.booking_status // Use booking_status from bill
          appointmentData.discount_amount = bill.discount_amount
          appointmentData.discount_type = bill.discount_type

          // Add bill items
          if (bill.items && bill.items.length > 0) {
            appointmentData.bill_items = bill.items
            console.log('[APPOINTMENT EDIT] Bill items added to appointment data:', bill.items)
            console.log('[APPOINTMENT EDIT] appointmentData.bill_items after assignment:', appointmentData.bill_items)
          } else {
            console.log('[APPOINTMENT EDIT] Bill has no items or items array is empty')
          }
        } else {
          console.log('[APPOINTMENT EDIT] No bill found in response data')
        }
      } else {
        console.log('[APPOINTMENT EDIT] Bill response not OK:', billResponse.status)
      }
    } catch (error) {
      console.error('[APPOINTMENT EDIT] Error fetching associated bill:', error)
      // Continue without bill data
    }
    
    console.log('[APPOINTMENT EDIT] Final appointmentData before localStorage:', appointmentData)
    console.log('[APPOINTMENT EDIT] Final appointmentData.bill_items:', appointmentData.bill_items)

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
      <CalendarHeader
        activeView={activeView}
        selectedDate={selectedDate}
        fromDate={fromDate}
        toDate={toDate}
        onViewChange={handleViewChange}
        onDateChange={handleDateChange}
        onNavigate={handleNavigate}
        staffMembers={staffMembers}
        selectedStaff={selectedStaff}
        onStaffChange={setSelectedStaff}
        activeNavButton={activeNavButton}
      />

      {/* Schedule Grid */}
      <div className="schedule-container">
        {activeView === 'day' && (
          <div 
            className="schedule-grid schedule-grid-day"
            style={{
              gridTemplateColumns: `100px repeat(${staffMembers.length}, minmax(120px, 180px))`
            }}
          >
            {/* Time Column Header */}
            <div className="time-header">Time</div>

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
                    const slotAppointments = getAppointmentsForSlot(timeSlot.hour, staff.id, selectedDate)
                    return (
                      <div
                        key={`${timeSlot.hour}-${staff.id}`}
                        className="schedule-cell"
                        onClick={() => openBookingModal(staff.id, timeSlot.hour, selectedDate)}
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
        )}

        {activeView === 'week' && (
          <div 
            className="schedule-grid schedule-grid-week"
            style={{
              gridTemplateColumns: `100px repeat(7, minmax(150px, 1fr))`
            }}
          >
            {/* Time Column Header */}
            <div className="time-header">Time</div>

            {/* Day Headers */}
            {getWeekDates(selectedDate).map((date) => {
              const d = new Date(date)
              const dayName = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'][d.getDay()]
              const dayNum = d.getDate()
              const isToday = date === new Date().toISOString().split('T')[0]
              return (
                <div key={date} className={`day-header ${isToday ? 'today' : ''}`}>
                  <div className="day-name">{dayName}</div>
                  <div className="day-number">{dayNum}</div>
                </div>
              )
            })}

            {/* Time Slots and Grid Cells */}
            {timeSlots.map((timeSlot) => {
              const showCurrentTime = isCurrentTime(timeSlot.hour)
              return (
                <React.Fragment key={timeSlot.hour}>
                  {/* Time Label */}
                  <div className="time-label">{timeSlot.label}</div>

                  {/* Day Columns */}
                  {getWeekDates(selectedDate).map((date) => {
                    const dayAppointments = getAppointmentsForDate(date, selectedStaff !== 'all' ? selectedStaff : null).filter(apt => {
                      if (!apt.start_time) return false
                      const timeParts = apt.start_time.split(':')
                      const aptHour = parseInt(timeParts[0], 10)
                      return aptHour === timeSlot.hour
                    })
                    
                    return (
                      <div
                        key={`${timeSlot.hour}-${date}`}
                        className="schedule-cell"
                        onClick={() => openBookingModal(selectedStaff !== 'all' ? selectedStaff : null, timeSlot.hour, date)}
                        style={{ cursor: 'pointer', position: 'relative' }}
                      >
                        {showCurrentTime && date === getWeekDates(selectedDate)[0] && (
                          <div className="current-time-line-wrapper">
                            <div className="current-time-line">
                              <div className="current-time-marker"></div>
                            </div>
                          </div>
                        )}
                        {dayAppointments.map((apt) => (
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
        )}

        {activeView === 'month' && (
          <div className="schedule-grid schedule-grid-month">
            {/* Day Name Headers */}
            {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map((dayName) => (
              <div key={dayName} className="month-day-header">
                {dayName}
              </div>
            ))}

            {/* Month Grid Cells */}
            {getMonthGridDates(selectedDate).map((date) => {
              const d = new Date(date)
              const dayNum = d.getDate()
              const isCurrentMonth = d.getMonth() === new Date(selectedDate).getMonth()
              const isToday = date === new Date().toISOString().split('T')[0]
              const dayAppointments = getAppointmentsForDate(date, selectedStaff !== 'all' ? selectedStaff : null)
              
              return (
                <div
                  key={date}
                  className={`month-cell ${!isCurrentMonth ? 'other-month' : ''} ${isToday ? 'today' : ''}`}
                  onClick={() => {
                    // Switch to day view for the clicked date
                    setSelectedDate(date)
                    setActiveView('day')
                  }}
                >
                  <div className="month-cell-date">{dayNum}</div>
                  <div className="month-cell-appointments">
                    {dayAppointments.slice(0, 3).map((apt) => (
                      <div
                        key={apt.id}
                        className={`month-appointment ${apt.status}`}
                        onClick={(e) => {
                          e.stopPropagation()
                          openDetailModal(apt)
                        }}
                        title={`${apt.customer_name} - ${apt.service_name || 'Service'}`}
                      >
                        <span className="month-appointment-time">
                          {new Date(`2000-01-01T${apt.start_time}`).toLocaleTimeString('en-US', {
                            hour: 'numeric',
                            minute: '2-digit',
                          })}
                        </span>
                        <span className="month-appointment-customer">{apt.customer_name}</span>
                        <span className="month-appointment-service">{apt.service_name || 'Service'}</span>
                      </div>
                    ))}
                    {dayAppointments.length > 3 && (
                      <div className="month-more-appointments">
                        +{dayAppointments.length - 3} more
                      </div>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        )}
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

      {/* Appointment Detail Modal */}
      {showDetailModal && appointmentDetail && (
        <div className="modal-overlay" onClick={() => setShowDetailModal(false)}>
          <div className="appointment-detail-modal" onClick={(e) => e.stopPropagation()}>
            {showInvoiceView ? (
              // Invoice View
              <>
                <h2>Invoice</h2>
                
                {loadingInvoice ? (
                  <div className="invoice-loading-state">
                    <p>Loading invoice data...</p>
                  </div>
                ) : invoiceData ? (
                  <div className="invoice-preview-wrapper">
                    <InvoicePreview 
                      invoiceData={invoiceData}
                      onDownload={handleDownloadInvoice}
                      onReview={handleReviewUs}
                    />
                  </div>
                ) : (
                  <div className="invoice-no-data">
                    <p>No invoice data available for this appointment.</p>
                    <p className="invoice-no-data-subtitle">A bill may not have been created yet.</p>
                    <div className="invoice-fallback-actions">
                      <button className="invoice-action-btn back-btn" onClick={handleBackToAppointment}>
                        <FaArrowLeft /> Back to Appointment
                      </button>
                    </div>
                  </div>
                )}
              </>
            ) : (
              // Appointment Details View
              <>
                <div className="appointment-modal-header">
                  <h2>Appointment Details</h2>
                  <button className="close-btn" onClick={() => setShowDetailModal(false)}>
                    <FaTimes />
                  </button>
                </div>
                
                <div className="appointment-details-content">
                  <div className="appointment-info-section">
                    <div className="info-row">
                      <span className="info-label">Customer:</span>
                      <span className="info-value">{appointmentDetail.customer_name || 'N/A'}</span>
                    </div>
                    <div className="info-row">
                      <span className="info-label">Mobile:</span>
                      <span className="info-value">{appointmentDetail.customer_mobile || 'N/A'}</span>
                    </div>
                    <div className="info-row">
                      <span className="info-label">Service:</span>
                      <span className="info-value">{appointmentDetail.service_name || 'N/A'}</span>
                    </div>
                    <div className="info-row">
                      <span className="info-label">Staff:</span>
                      <span className="info-value">{appointmentDetail.staff_name || 'N/A'}</span>
                    </div>
                    <div className="info-row">
                      <span className="info-label">Date:</span>
                      <span className="info-value">
                        {appointmentDetail.appointment_date 
                          ? new Date(appointmentDetail.appointment_date).toLocaleDateString('en-IN', {
                              day: '2-digit',
                              month: 'short',
                              year: 'numeric'
                            })
                          : 'N/A'}
                      </span>
                    </div>
                    <div className="info-row">
                      <span className="info-label">Time:</span>
                      <span className="info-value">
                        {appointmentDetail.start_time 
                          ? new Date(`2000-01-01T${appointmentDetail.start_time}`).toLocaleTimeString('en-US', {
                              hour: 'numeric',
                              minute: '2-digit',
                              hour12: true
                            })
                          : 'N/A'}
                      </span>
                    </div>
                    <div className="info-row">
                      <span className="info-label">Status:</span>
                      <span className={`info-value status-${appointmentDetail.status || 'confirmed'}`}>
                        {appointmentDetail.status || 'confirmed'}
                      </span>
                    </div>
                    {appointmentDetail.notes && (
                      <div className="info-row">
                        <span className="info-label">Notes:</span>
                        <span className="info-value">{appointmentDetail.notes}</span>
                      </div>
                    )}
                  </div>
                  
                  <div className="appointment-actions-section">
                    <button 
                      className="appointment-action-btn edit-btn" 
                      onClick={() => handleEditAppointment(appointmentDetail)}
                    >
                      <FaEdit /> Edit Appointment
                    </button>
                    {billId && (
                      <button 
                        className="appointment-action-btn view-bill-btn" 
                        onClick={handleViewBill}
                      >
                        <FaDownload /> View Bill
                      </button>
                    )}
                    <button 
                      className="appointment-action-btn share-btn" 
                      onClick={() => showWarning('Share functionality coming soon')}
                    >
                      <FaShare /> Share
                    </button>
                  </div>
                </div>
              </>
            )}
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

