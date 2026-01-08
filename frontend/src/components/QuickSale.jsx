import React, { useState, useEffect, useRef } from 'react'
import { FaBars, FaBell, FaUser, FaCalendar, FaBoxes, FaTrash, FaChevronDown, FaClock, FaTimes, FaExclamationTriangle, FaClipboardList, FaTimesCircle, FaGift } from 'react-icons/fa'
import './QuickSale.css'
import { API_BASE_URL } from '../config'
import { useAuth } from '../contexts/AuthContext'
import { apiGet, apiPost, apiPut } from '../utils/api'
import { showSuccess, showError, showWarning, showInfo } from '../utils/toast.jsx'
import DatePicker from 'react-datepicker'
import 'react-datepicker/dist/react-datepicker.css'
import { celebrateBig } from '../utils/confetti'
import { formatLocalDate } from '../utils/dateUtils'
import { PageTransition } from './shared/PageTransition'
import { EmptyList } from './shared/EmptyStates'
import InvoicePreview from './InvoicePreview'

const QuickSale = () => {
  const { user, getMaxDiscountPercent, currentBranch } = useAuth()
  const [pendingApproval, setPendingApproval] = useState(null)
  const [showApprovalForm, setShowApprovalForm] = useState(false)
  const [approvalReason, setApprovalReason] = useState('')

  const [discountType, setDiscountType] = useState('fix')
  const [paymentMode, setPaymentMode] = useState('cash')
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedDate, setSelectedDate] = useState(new Date())
  const [selectedCustomer, setSelectedCustomer] = useState(null)
  const [customerDetails, setCustomerDetails] = useState(null)
  const [loadingCustomerDetails, setLoadingCustomerDetails] = useState(false)
  const [bookingStatus, setBookingStatus] = useState('confirmed')
  const [bookingNote, setBookingNote] = useState('')
  const [discountAmount, setDiscountAmount] = useState(0)
  const [membershipInfo, setMembershipInfo] = useState(null)
  const appointmentCreatedRef = useRef(false)

  // Helper function to get current time in HH:MM format
  const getCurrentTime = () => {
    const now = new Date()
    const hours = String(now.getHours()).padStart(2, '0')
    const minutes = String(now.getMinutes()).padStart(2, '0')
    return `${hours}:${minutes}`
  }

  // Data from backend
  const [customers, setCustomers] = useState([])
  const [staffMembers, setStaffMembers] = useState([])
  const [availableServices, setAvailableServices] = useState([])
  const [filteredCustomers, setFilteredCustomers] = useState([])
  const [showCustomerDropdown, setShowCustomerDropdown] = useState(false)

  // New customer form state
  const [showNewCustomerForm, setShowNewCustomerForm] = useState(false)
  const [creatingCustomer, setCreatingCustomer] = useState(false)
  const [newCustomerData, setNewCustomerData] = useState({
    mobile: '',
    name: '',
    gender: '',
    source: 'Walk-in',
    dobRange: ''
  })

  // Inventory modal state
  const [showInventoryModal, setShowInventoryModal] = useState(false)
  const [selectedServiceForInventory, setSelectedServiceForInventory] = useState(null)
  const [serviceRelatedProducts, setServiceRelatedProducts] = useState([])

  // Bill Activity modal state
  const [showBillActivityModal, setShowBillActivityModal] = useState(false)
  const [customerBills, setCustomerBills] = useState([])
  const [loadingBills, setLoadingBills] = useState(false)

  // Add Package/Product/Prepaid/Membership modal states
  const [showPackageModal, setShowPackageModal] = useState(false)
  const [showProductModal, setShowProductModal] = useState(false)
  const [showPrepaidModal, setShowPrepaidModal] = useState(false)
  const [showMembershipModal, setShowMembershipModal] = useState(false)
  const [selectedQuantity, setSelectedQuantity] = useState(1)

  const [services, setServices] = useState(() => {
    const currentTime = (() => {
      const now = new Date()
      const hours = String(now.getHours()).padStart(2, '0')
      const minutes = String(now.getMinutes()).padStart(2, '0')
      return `${hours}:${minutes}`
    })()
    return [
      {
        id: 1,
        service_id: '',
        staff_id: '',
        startTime: currentTime,
        price: 0,
        discount: 0,
        total: 0,
      },
    ]
  })
  const [packages, setPackages] = useState([])
  const [products, setProducts] = useState([])
  const [prepaidPackages, setPrepaidPackages] = useState([])
  const [memberships, setMemberships] = useState([])
  const [availablePackages, setAvailablePackages] = useState([])
  const [availableProducts, setAvailableProducts] = useState([])
  const [availablePrepaid, setAvailablePrepaid] = useState([])
  const [availableMemberships, setAvailableMemberships] = useState([])

  // State for editing appointment
  const [editingAppointmentId, setEditingAppointmentId] = useState(null)

  // State for invoice modal
  const [showInvoiceModal, setShowInvoiceModal] = useState(false)
  const [invoiceData, setInvoiceData] = useState(null)
  const [currentBillId, setCurrentBillId] = useState(null)
  const [loadingInvoice, setLoadingInvoice] = useState(false)

  // Fetch data on component mount
  useEffect(() => {
    fetchCustomers()
    fetchStaff()
    fetchServices()
    fetchPackages()
    fetchProducts()
    fetchPrepaidPackages()
    fetchMembershipPlans()
  }, [])

  // Pre-fill appointment data after data arrays are loaded
  useEffect(() => {
    // Only proceed if we have appointment data to pre-fill
    const editAppointmentData = localStorage.getItem('edit_appointment_data')
    if (!editAppointmentData) return
    
    // Wait for at least some data to be loaded (customers, services, or staff)
    // This ensures we don't try to pre-fill before any data is available
    const hasDataLoaded = customers.length > 0 || availableServices.length > 0 || staffMembers.length > 0
    if (!hasDataLoaded) {
      return // Data not loaded yet, wait for next render
    }

    try {
      const appointmentData = JSON.parse(editAppointmentData)
      setEditingAppointmentId(appointmentData.appointmentId)
      
      // Pre-fill the form with appointment data
      prefillAppointmentData(appointmentData)
      // Clear the data after reading
      localStorage.removeItem('edit_appointment_data')
    } catch (error) {
      console.error('Error parsing appointment data:', error)
      localStorage.removeItem('edit_appointment_data')
    }
  }, [customers, availableServices, staffMembers])

  // Fetch customer details and membership in background when customer is selected
  useEffect(() => {
    if (selectedCustomer?.id) {
      // Fetch in background without blocking UI
      fetchCustomerDetails(selectedCustomer.id)
      checkCustomerMembership(selectedCustomer.id)
    } else {
      // Clear customer details when no customer is selected
      setCustomerDetails(null)
      setMembershipInfo(null)
      setDiscountAmount(0)
      setDiscountType('fix')
    }
  }, [selectedCustomer])

  // Pre-fill form with appointment data
  const prefillAppointmentData = async (appointmentData) => {
    try {
      // Set customer
      if (appointmentData.customer_id) {
        // First try to find in loaded customers array
        let customer = customers.find(c => c.id === appointmentData.customer_id)
        
        if (!customer) {
          // If not found, fetch from API
          try {
            const response = await apiGet(`/api/customers/${appointmentData.customer_id}`)
            if (response.ok) {
              const customerData = await response.json()
              // Map to match expected format
              customer = {
                id: customerData.id,
                mobile: customerData.mobile || '',
                firstName: customerData.firstName || customerData.first_name || '',
                lastName: customerData.lastName || customerData.last_name || '',
                email: customerData.email || ''
              }
            }
          } catch (fetchError) {
            console.error('Error fetching customer:', fetchError)
          }
        }
        
        if (customer) {
          selectCustomer(customer)
          // Customer details will be fetched in background via useEffect
        }
      }

      // Set date
      if (appointmentData.appointment_date) {
        setSelectedDate(new Date(appointmentData.appointment_date))
      }

      // Set booking status
      if (appointmentData.status) {
        setBookingStatus(appointmentData.status === 'confirmed' ? 'confirmed' : 'service-completed')
      }

      // Set booking note
      if (appointmentData.notes) {
        setBookingNote(appointmentData.notes)
      }

      // Set service - try to find in loaded arrays first, then fetch if needed
      if (appointmentData.service_id && appointmentData.staff_id && appointmentData.start_time) {
        // Try to find service and staff in loaded arrays
        let service = availableServices.find(s => s.id === appointmentData.service_id)
        let staff = staffMembers.find(s => s.id === appointmentData.staff_id)
        
        // If not found, try fetching
        if (!service && appointmentData.service_id) {
          try {
            const response = await fetch(`${API_BASE_URL}/api/services`)
            const data = await response.json()
            service = (data.services || []).find(s => s.id === appointmentData.service_id)
          } catch (error) {
            console.error('Error fetching service:', error)
          }
        }
        
        if (!staff && appointmentData.staff_id) {
          try {
            const response = await apiGet('/api/staffs')
            const data = await response.json()
            staff = (data.staffs || []).find(s => s.id === appointmentData.staff_id)
          } catch (error) {
            console.error('Error fetching staff:', error)
          }
        }
        
        if (service && staff) {
          // Format time (remove seconds if present)
          let timeStr = appointmentData.start_time
          if (timeStr.includes(':')) {
            const parts = timeStr.split(':')
            timeStr = `${parts[0]}:${parts[1]}`
          }

          setServices([{
            id: 1,
            service_id: appointmentData.service_id,
            staff_id: appointmentData.staff_id,
            startTime: timeStr,
            price: appointmentData.service_price || service.price || 0,
            discount: 0,
            total: appointmentData.service_price || service.price || 0,
          }])
        } else {
          console.warn('Service or staff not found for appointment pre-fill', { 
            service_id: appointmentData.service_id, 
            staff_id: appointmentData.staff_id 
          })
        }
      }

      showInfo('Appointment data loaded. You can now edit and update the booking.')
    } catch (error) {
      console.error('Error pre-filling appointment data:', error)
      showError('Failed to load appointment data')
    }
  }

  // Listen for branch changes
  useEffect(() => {
    const handleBranchChange = () => {
      console.log('[QuickSale] Branch changed, refreshing data...')
      fetchCustomers()
      fetchStaff()
      fetchServices()
      fetchPackages()
      fetchProducts()
      fetchPrepaidPackages()
      fetchMembershipPlans()
    }
    
    window.addEventListener('branchChanged', handleBranchChange)
    return () => window.removeEventListener('branchChanged', handleBranchChange)
  }, [currentBranch])

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (showCustomerDropdown && !event.target.closest('.search-container')) {
        setShowCustomerDropdown(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [showCustomerDropdown])

  // Filter customers based on search query
  useEffect(() => {
    if (searchQuery.length > 0) {
      const query = searchQuery.toLowerCase()
      const filtered = customers.filter(customer =>
        customer.mobile.includes(searchQuery) ||
        (customer.firstName && customer.firstName.toLowerCase().includes(query)) ||
        (customer.lastName && customer.lastName.toLowerCase().includes(query)) ||
        `${customer.firstName || ''} ${customer.lastName || ''}`.toLowerCase().includes(query)
      )
      setFilteredCustomers(filtered)
      setShowCustomerDropdown(true)
    } else {
      // Show all customers when field is focused but empty
      setFilteredCustomers(customers.slice(0, 10)) // Limit to first 10 for performance
      setShowCustomerDropdown(false)
    }
  }, [searchQuery, customers])

  const fetchCustomers = async () => {
    try {
      const response = await apiGet(`/api/customers?per_page=200`)
      const data = await response.json()
      // Map the response to match the expected format (handle both camelCase and snake_case)
      const customersList = (data.customers || []).map(customer => ({
        id: customer.id,
        mobile: customer.mobile || '',
        firstName: customer.firstName || customer.first_name || '',
        lastName: customer.lastName || customer.last_name || '',
        email: customer.email || ''
      }))
      setCustomers(customersList)
    } catch (error) {
      console.error('Error fetching customers:', error)
      showError('Failed to load customers. Please refresh the page.')
    }
  }

  const fetchStaff = async () => {
    try {
      const response = await apiGet(`/api/staffs`)
      const data = await response.json()
      setStaffMembers(data.staffs || [])
    } catch (error) {
      console.error('Error fetching staff:', error)
    }
  }

  const fetchServices = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/services`)
      const data = await response.json()
      setAvailableServices(data.services || [])
    } catch (error) {
      console.error('Error fetching services:', error)
    }
  }

  const fetchPackages = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/packages`)
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      const data = await response.json()
      setAvailablePackages(Array.isArray(data) ? data : (data.packages || []))
    } catch (error) {
      console.error('Error fetching packages:', error)
      setAvailablePackages([])
    }
  }

  const fetchProducts = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/products`)
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      const data = await response.json()
      setAvailableProducts(Array.isArray(data) ? data : (data.products || []))
    } catch (error) {
      console.error('Error fetching products:', error)
      setAvailableProducts([])
    }
  }

  const fetchPrepaidPackages = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/prepaid/packages`)
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      const data = await response.json()
      setAvailablePrepaid(Array.isArray(data) ? data : (data.packages || []))
    } catch (error) {
      console.error('Error fetching prepaid packages:', error)
      setAvailablePrepaid([])
    }
  }

  const fetchMembershipPlans = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/membership-plans`)
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      const data = await response.json()
      setAvailableMemberships(Array.isArray(data) ? data : (data.plans || []))
    } catch (error) {
      console.error('Error fetching membership plans:', error)
      setAvailableMemberships([])
    }
  }

  const addService = () => {
    const currentTime = getCurrentTime()
    setServices([
      ...services,
      {
        id: Date.now(),
        service_id: '',
        staff_id: '',
        startTime: currentTime,
        price: 0,
        discount: 0,
        total: 0,
      },
    ])
  }

  const addPackage = () => {
    if (!selectedCustomer) {
      showWarning('Please select a customer first')
      return
    }
    setShowPackageModal(true)
  }

  const handleSelectPackage = (selectedPackage) => {
    setPackages([...packages, {
      id: Date.now(),
      package_id: selectedPackage.id,
      name: selectedPackage.name,
      price: selectedPackage.price,
      discount: 0,
      total: selectedPackage.price,
    }])
    setShowPackageModal(false)
    showSuccess(`${selectedPackage.name} added to bill`)
  }

  const addProduct = () => {
    if (!selectedCustomer) {
      showWarning('Please select a customer first')
      return
    }
    setSelectedQuantity(1)
    setShowProductModal(true)
  }

  const handleSelectProduct = async (selectedProduct, quantity) => {
    if (quantity <= 0) {
      showWarning('Quantity must be greater than 0')
      return
    }
    if (quantity > (selectedProduct.stock_quantity || 0)) {
      showWarning(`Only ${selectedProduct.stock_quantity} units available`)
      return
    }
    
    // Add to local state
    setProducts([...products, {
      id: Date.now(),
      product_id: selectedProduct.id,
      name: selectedProduct.name,
      price: selectedProduct.price,
      quantity: quantity,
      discount: 0,
      total: selectedProduct.price * quantity,
    }])
    
    // Update local stock count optimistically
    setAvailableProducts(prevProducts => 
      prevProducts.map(p => 
        p.id === selectedProduct.id 
          ? { ...p, stock_quantity: (p.stock_quantity || 0) - quantity }
          : p
      )
    )
    
    setShowProductModal(false)
    setSelectedQuantity(1)
    showSuccess(`${selectedProduct.name} (x${quantity}) added to bill`)
    
    // Refresh products to get actual stock from server
    setTimeout(() => fetchProducts(), 500)
  }

  const addPrepaid = async () => {
    if (!selectedCustomer) {
      showWarning('Please select a customer first')
      return
    }
    // Fetch all available prepaid packages (not filtered by customer)
    // These are packages available for purchase
    try {
      const response = await fetch(`${API_BASE_URL}/api/prepaid/packages`)
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      const data = await response.json()
      const availablePackages = Array.isArray(data) ? data : (data.packages || [])
      // Filter to show only packages without customers (available for purchase) or with active status
      const purchasablePackages = availablePackages.filter(p => !p.customer_id || p.status === 'active')
      setAvailablePrepaid(purchasablePackages)
      setShowPrepaidModal(true)
    } catch (error) {
      console.error('Error fetching prepaid packages:', error)
      showError('Failed to load prepaid packages')
      setAvailablePrepaid([])
    }
  }

  const handleSelectPrepaid = (selectedPrepaid) => {
    setPrepaidPackages([...prepaidPackages, {
      id: Date.now(),
      prepaid_id: selectedPrepaid.id,
      name: selectedPrepaid.name,
      balance: selectedPrepaid.remaining_balance || 0,
    }])
    setShowPrepaidModal(false)
    showSuccess(`${selectedPrepaid.name} added to bill`)
  }

  const addMembership = () => {
    if (!selectedCustomer) {
      showWarning('Please select a customer first')
      return
    }
    setShowMembershipModal(true)
  }

  const handleSelectMembership = (selectedMembership) => {
    setMemberships([...memberships, {
      id: Date.now(),
      membership_id: selectedMembership.id,
      name: selectedMembership.name,
      price: selectedMembership.price,
      validity: selectedMembership.validity_days,
    }])
    setShowMembershipModal(false)
    showSuccess(`${selectedMembership.name} added to bill`)
  }

  const removePackage = (id) => {
    setPackages(packages.filter(p => p.id !== id))
  }

  const removeProduct = (id) => {
    setProducts(products.filter(p => p.id !== id))
  }

  const removePrepaid = (id) => {
    setPrepaidPackages(prepaidPackages.filter(p => p.id !== id))
  }

  const removeMembership = (id) => {
    setMemberships(memberships.filter(m => m.id !== id))
  }

  const removeService = (id) => {
    if (services.length > 1) {
      setServices(services.filter((s) => s.id !== id))
    }
  }

  const updateService = (id, field, value) => {
    const updated = services.map((s) => {
      if (s.id === id) {
        const updatedService = { ...s, [field]: value }

        // Auto-fill price when service is selected
        if (field === 'service_id' && value) {
          const selectedService = availableServices.find(service => service.id === value)
          if (selectedService) {
            updatedService.price = selectedService.price
          }
        }

        // Ensure startTime is preserved as string
        if (field === 'startTime' && value) {
          updatedService.startTime = String(value).trim()
        }

        // Calculate total
        const price = parseFloat(updatedService.price) || 0
        const discount = parseFloat(updatedService.discount) || 0
        updatedService.total = price - (price * discount / 100)

        return updatedService
      }
      return s
    })
    setServices(updated)
  }

  const selectCustomer = (customer) => {
    setSelectedCustomer(customer)
    setSearchQuery(`${customer.firstName || ''} ${customer.lastName || ''} - ${customer.mobile}`.trim())
    setShowCustomerDropdown(false)
    // Customer details and membership will be fetched in background via useEffect
  }

  // Check customer's active membership
  const checkCustomerMembership = async (customerId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/customers/${customerId}/active-membership`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        }
      })
      
      if (!response.ok) {
        throw new Error('Failed to fetch membership')
      }
      
      const data = await response.json()
      
      if (data.active && data.membership && data.membership.plan) {
        // Customer has active membership
        // The backend returns: { active: true, membership: { id, name, plan: {...}, expiry_date, purchase_date, status } }
        setMembershipInfo(data.membership)
        // Auto-apply membership discount (will be calculated on checkout)
        // We set the discount type to 'membership' and let backend calculate
        setDiscountType('membership')
        setDiscountAmount(data.membership.plan.allocated_discount) // Store percentage for display
        showInfo(`Active Membership: ${data.membership.plan.name} - ${data.membership.plan.allocated_discount}% discount will be applied automatically`)
      } else {
        // No active membership
        setMembershipInfo(null)
        setDiscountAmount(0)
        setDiscountType('fix')
      }
    } catch (error) {
      console.error('Error checking membership:', error)
      setMembershipInfo(null)
      setDiscountAmount(0)
      setDiscountType('fix')
    }
  }

  // Create appointment when booking status is confirmed
  const handleCreateAppointment = async () => {
    try {
      // Validation
      if (!selectedCustomer) {
        showError('Please select a customer first')
        return false
      }

      // Get first service with staff and time
      const firstService = services.find(s => 
        s.service_id && 
        s.staff_id && 
        s.startTime && 
        s.startTime.trim() !== ''
      )
      if (!firstService) {
        // Provide more specific error message
        const hasService = services.some(s => s.service_id)
        const hasStaff = services.some(s => s.staff_id)
        const hasTime = services.some(s => s.startTime && s.startTime.trim() !== '')
        
        if (!hasService) {
          showError('Please add at least one service')
        } else if (!hasStaff) {
          showError('Please assign staff to at least one service')
        } else if (!hasTime) {
          showError('Please set start time for at least one service')
        } else {
          showError('Please add at least one service with staff and time assigned')
        }
        return false
      }

      // Format date for API (YYYY-MM-DD)
      const appointmentDate = formatLocalDate(selectedDate)
      
      // Format time (HH:MM:SS)
      let startTime = firstService.startTime.trim()
      if (!startTime || !startTime.includes(':')) {
        showError('Please provide a valid time for the service')
        return false
      }
      // Ensure time is in HH:MM:SS format
      if (startTime.split(':').length === 2) {
        startTime = `${startTime}:00`
      }

      // If editing an existing appointment, update it instead of creating new one
      if (editingAppointmentId) {
        const updateResponse = await apiPut(`/api/appointments/${editingAppointmentId}`, {
          customer_id: selectedCustomer.id,
          staff_id: firstService.staff_id,
          service_id: firstService.service_id,
          appointment_date: appointmentDate,
          start_time: startTime,
          status: 'confirmed',
          notes: bookingNote || undefined
        })

        if (!updateResponse.ok) {
          const errorData = await updateResponse.json().catch(() => ({ error: 'Failed to update appointment' }))
          showError(errorData.error || 'Failed to update appointment')
          return false
        }

        showSuccess('Booking updated! Appointment saved to Upcoming Appointments.')
        return true
      }

      // Create new appointment
      const response = await apiPost('/api/appointments', {
        customer_id: selectedCustomer.id,
        staff_id: firstService.staff_id,
        service_id: firstService.service_id,
        appointment_date: appointmentDate,
        start_time: startTime,
        status: 'confirmed',
        notes: bookingNote || undefined
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: 'Failed to create appointment' }))
        showError(errorData.error || 'Failed to create appointment')
        return false
      }

      const data = await response.json()
      showSuccess('Booking confirmed! Appointment saved to Upcoming Appointments.')
      return true
    } catch (error) {
      console.error('Error creating appointment:', error)
      showError(`Error creating appointment: ${error.message || 'Unknown error'}`)
      return false
    }
  }

  const fetchCustomerDetails = async (customerId) => {
    setLoadingCustomerDetails(true)
    try {
      const response = await apiGet(`/api/customers/${customerId}`)
      const data = await response.json()
      console.log('Customer details fetched:', data)
      console.log('Total visits:', data.total_visits)
      // Format membership data for display
      let membershipDisplay = 'No Membership'
      if (data.membership) {
        if (typeof data.membership === 'object' && data.membership.plan) {
          membershipDisplay = `${data.membership.plan.name || data.membership.name || 'Active Membership'} (${data.membership.plan.allocated_discount || 0}% discount)`
        } else if (typeof data.membership === 'string') {
          membershipDisplay = data.membership
        }
      }
      
      setCustomerDetails({
        membership: membershipDisplay,
        lastVisit: data.last_visit || null,
        totalVisits: data.total_visits || 0,
        totalRevenue: data.total_revenue || 0,
        notes: data.notes || 'N/A'
      })
    } catch (error) {
      console.error('Error fetching customer details:', error)
      setCustomerDetails(null)
    } finally {
      setLoadingCustomerDetails(false)
    }
  }

  const handleCustomerInputFocus = () => {
    // If a customer is selected, clear selection and allow searching again
    if (selectedCustomer) {
      setSelectedCustomer(null)
      setSearchQuery('')
      setFilteredCustomers(customers.slice(0, 10))
      setShowCustomerDropdown(true)
      return
    }
    
    // If no customer is selected, show dropdown
      if (searchQuery.length > 0) {
        // If there's a search query, filter customers
        const query = searchQuery.toLowerCase()
        const filtered = customers.filter(customer =>
          customer.mobile.includes(searchQuery) ||
          (customer.firstName && customer.firstName.toLowerCase().includes(query)) ||
          (customer.lastName && customer.lastName.toLowerCase().includes(query)) ||
          `${customer.firstName || ''} ${customer.lastName || ''}`.toLowerCase().includes(query)
        )
        setFilteredCustomers(filtered)
        setShowCustomerDropdown(true)
      } else {
        // Show first 10 customers when field is focused but empty
        setFilteredCustomers(customers.slice(0, 10))
        setShowCustomerDropdown(true)
    }
  }

  const handleCustomerInputChange = (e) => {
    const value = e.target.value
    setSearchQuery(value)
    // Clear selection if user is typing
    if (selectedCustomer && value !== `${selectedCustomer.firstName || ''} ${selectedCustomer.lastName || ''} - ${selectedCustomer.mobile}`.trim()) {
      setSelectedCustomer(null)
    }
  }

  const handleCreateNewCustomer = async () => {
    // Validate required fields
    if (!newCustomerData.mobile || !newCustomerData.name || !newCustomerData.gender) {
      showWarning('Please fill in all required fields: Mobile, Name, and Gender')
      return
    }

    // Validate mobile number
    const cleanMobile = newCustomerData.mobile.trim().replace(/\s+/g, '').replace(/^\+91/, '').replace(/^91/, '')
    if (cleanMobile.length !== 10 || !/^\d{10}$/.test(cleanMobile)) {
      showWarning('Please enter a valid 10-digit mobile number')
      return
    }

    // Split name into first and last name
    const nameParts = newCustomerData.name.trim().split(' ')
    const firstName = nameParts[0] || ''
    const lastName = nameParts.slice(1).join(' ') || ''

    setCreatingCustomer(true)
    try {
      const response = await apiPost('/api/customers', {
        mobile: cleanMobile,
        firstName: firstName,
        lastName: lastName,
        gender: newCustomerData.gender,
        source: newCustomerData.source,
        dobRange: newCustomerData.dobRange || ''
      })

      const data = await response.json()
      
      // Backend returns { id: "...", message: "..." }
      const newCustomer = {
        id: data.id,
        mobile: cleanMobile,
        firstName: firstName,
        lastName: lastName,
        email: ''
      }

      // Add to customers list
      setCustomers([newCustomer, ...customers])
      
      // Select the new customer
      selectCustomer(newCustomer)
      
      // Reset form
      setShowNewCustomerForm(false)
      setNewCustomerData({ mobile: '', name: '', gender: '', source: 'Walk-in', dobRange: '' })
      
      showSuccess(`Customer ${newCustomer.firstName} ${newCustomer.lastName} created successfully!`)
    } catch (error) {
      console.error('Error creating customer:', error)
      showError(`Failed to create customer: ${error.message}`)
    } finally {
      setCreatingCustomer(false)
    }
  }

  const handleShowInventory = (service) => {
    const selectedService = availableServices.find(s => s.id === service.service_id)
    
    if (!selectedService) {
      showWarning('Please select a service first')
      return
    }

    // Filter products related to this service
    // For hair coloring, show hair color products
    // For haircut, show styling products, etc.
    const serviceKeywords = selectedService.name.toLowerCase()
    const relatedProducts = availableProducts.filter(product => {
      const productName = product.name.toLowerCase()
      const productCategory = (product.category || '').toLowerCase()
      
      // Match by keywords in service name
      if (serviceKeywords.includes('color') || serviceKeywords.includes('dye')) {
        return productName.includes('color') || productName.includes('dye') || 
               productCategory.includes('color') || productCategory.includes('dye')
      }
      if (serviceKeywords.includes('hair') || serviceKeywords.includes('cut')) {
        return productName.includes('shampoo') || productName.includes('conditioner') ||
               productName.includes('serum') || productName.includes('oil') ||
               productCategory.includes('hair')
      }
      if (serviceKeywords.includes('facial') || serviceKeywords.includes('skin')) {
        return productName.includes('cream') || productName.includes('serum') ||
               productName.includes('mask') || productCategory.includes('skin')
      }
      if (serviceKeywords.includes('spa') || serviceKeywords.includes('massage')) {
        return productName.includes('oil') || productName.includes('lotion') ||
               productCategory.includes('spa') || productCategory.includes('massage')
      }
      
      // Default: show all products if no specific match
      return true
    })

    setSelectedServiceForInventory(selectedService)
    setServiceRelatedProducts(relatedProducts)
    setShowInventoryModal(true)
  }

  const calculateSubtotal = () => {
    const servicesTotal = services.reduce((sum, service) => sum + (parseFloat(service.total) || 0), 0)
    const packagesTotal = packages.reduce((sum, pkg) => sum + (parseFloat(pkg.total) || 0), 0)
    const productsTotal = products.reduce((sum, product) => sum + (parseFloat(product.total) || 0), 0)
    return servicesTotal + packagesTotal + productsTotal
  }

  const calculateDiscount = () => {
    const subtotal = calculateSubtotal()
    
    // Handle membership discount
    if (discountType === 'membership' && membershipInfo && membershipInfo.plan) {
      const discountPercent = membershipInfo.plan.allocated_discount || 0
      return subtotal * (discountPercent / 100)
    }
    
    if (discountType === 'fix') {
      return parseFloat(discountAmount) || 0
    } else if (discountType === '%') {
      return subtotal * (parseFloat(discountAmount) || 0) / 100
    }
    
    return 0
  }

  const calculateNet = () => {
    return calculateSubtotal() - calculateDiscount()
  }

  const calculateTax = () => {
    // Assuming 18% GST, you can make this configurable
    return calculateNet() * 0.18
  }

  const calculateFinalAmount = () => {
    return calculateNet() + calculateTax()
  }

  const handleShowBillActivity = async () => {
    if (!selectedCustomer) {
      showWarning('Please select a customer first')
      return
    }

    setShowBillActivityModal(true)
    setLoadingBills(true)

    try {
      // Fetch customer bills from backend
      const response = await apiGet(`/api/bills?customer_id=${selectedCustomer.id}`)
      const data = await response.json()
      
      console.log('Bills API response:', data)
      
      // The API returns an array directly, not wrapped in a 'bills' key
      const billsArray = Array.isArray(data) ? data : (data.bills || [])
      
      // Sort bills by date (newest first)
      const sortedBills = billsArray.sort((a, b) => 
        new Date(b.bill_date) - new Date(a.bill_date)
      )
      
      console.log(`Found ${sortedBills.length} bills for customer`)
      
      setCustomerBills(sortedBills)
    } catch (error) {
      console.error('Error fetching customer bills:', error)
      showError('Failed to load bill history')
      setCustomerBills([])
    } finally {
      setLoadingBills(false)
    }
  }

  const handleReset = () => {
    const currentTime = getCurrentTime()
    setServices([{
      id: 1,
      service_id: '',
      staff_id: '',
      startTime: currentTime,
      price: 0,
      discount: 0,
      total: 0,
    }])
    setPackages([])
    setProducts([])
    setPrepaidPackages([])
    setMemberships([])
    setSelectedCustomer(null)
    setSearchQuery('')
    setDiscountAmount(0)
    setDiscountType('fix')
    setMembershipInfo(null)
    setBookingNote('')
    setBookingStatus('confirmed')
    appointmentCreatedRef.current = false
    setEditingAppointmentId(null)
  }

  const handleCheckout = async () => {
    try {
      // Validation: Only allow checkout when status is 'service-completed'
      if (bookingStatus !== 'service-completed') {
        showWarning('Please change booking status to "Service Completed" before proceeding with checkout')
        return
      }

      // Validation
      if (!selectedCustomer) {
        showWarning('Please select a customer. Click on the customer search field and select a customer from the dropdown.')
        return
      }

      // Validate services
      const validServices = services.filter(s => s.service_id && s.price > 0)
      if (validServices.length === 0) {
        showWarning('Please add at least one service with a valid price')
        return
      }

      if (!paymentMode) {
        showWarning('Please select a payment mode')
        return
      }

      // Create bill with selected date
      // If editing appointment, include appointment_id to check for existing unchecked-out bill
      const billDate = formatLocalDate(selectedDate) // Format as YYYY-MM-DD
      const billPayload = {
        customer_id: selectedCustomer.id,
        bill_date: billDate, // Send selected date to backend
        booking_status: bookingStatus,
        booking_note: bookingNote,
      }
      
      // Include appointment_id if editing an appointment
      if (editingAppointmentId) {
        billPayload.appointment_id = editingAppointmentId
      }
      
      const billResponse = await apiPost('/api/bills', billPayload)

      if (!billResponse.ok) {
        let errorMessage = 'Failed to create bill'
        try {
          const error = await billResponse.json()
          errorMessage = error.error || errorMessage
        } catch (e) {
          errorMessage = `Server error: ${billResponse.status} ${billResponse.statusText}`
        }
        showError(errorMessage)
        return
      }

      const billData = await billResponse.json()
      const billId = billData.data.id

      // Add services to bill
      for (const service of validServices) {
        if (service.service_id && service.price > 0) {
          try {
            const itemResponse = await apiPost(`/api/bills/${billId}/items`, {
              item_type: 'service',
              service_id: service.service_id,  // MongoDB ObjectId as string
              staff_id: service.staff_id || null,  // MongoDB ObjectId as string
              start_time: service.startTime ? `${service.startTime}:00` : null,
              price: parseFloat(service.price) || 0,
              discount: parseFloat(service.discount) || 0,
              quantity: 1,
              total: parseFloat(service.total) || parseFloat(service.price) || 0,
            })

            if (!itemResponse.ok) {
              let errorMessage = 'Failed to add item to bill'
              try {
                const errorData = await itemResponse.json()
                errorMessage = errorData.error || errorMessage
              } catch (e) {
                errorMessage = `Server error: ${itemResponse.status} ${itemResponse.statusText}`
              }
              throw new Error(errorMessage)
            }
          } catch (itemError) {
            console.error('Failed to add item to bill:', itemError)
            throw itemError
          }
        }
      }

      // Add packages to bill
      for (const pkg of packages) {
        if (pkg.package_id) {
          try {
            const itemResponse = await apiPost(`/api/bills/${billId}/items`, {
              item_type: 'package',
              package_id: pkg.package_id,  // MongoDB ObjectId as string
              price: parseFloat(pkg.price) || 0,
              discount: parseFloat(pkg.discount) || 0,
              quantity: 1,
              total: parseFloat(pkg.total) || parseFloat(pkg.price) || 0,
            })

            if (!itemResponse.ok) {
              const errorData = await itemResponse.json()
              throw new Error(errorData.error || 'Failed to add package to bill')
            }
          } catch (itemError) {
            console.error('Failed to add package to bill:', itemError)
            throw itemError
          }
        }
      }

      // Add products to bill
      for (const product of products) {
        if (product.product_id) {
          try {
            const itemResponse = await apiPost(`/api/bills/${billId}/items`, {
              item_type: 'product',
              product_id: product.product_id,  // MongoDB ObjectId as string
              price: parseFloat(product.price) || 0,
              discount: parseFloat(product.discount) || 0,
              quantity: parseInt(product.quantity) || 1,  // Quantity is a number, keep parseInt
              total: parseFloat(product.total) || parseFloat(product.price) * (parseInt(product.quantity) || 1) || 0,
            })

            if (!itemResponse.ok) {
              const errorData = await itemResponse.json()
              throw new Error(errorData.error || 'Failed to add product to bill')
            }
          } catch (itemError) {
            console.error('Failed to add product to bill:', itemError)
            throw itemError
          }
        }
      }

      // Add memberships to bill
      for (const membership of memberships) {
        if (membership.membership_id) {
          try {
            const itemResponse = await apiPost(`/api/bills/${billId}/items`, {
              item_type: 'membership',
              membership_id: membership.membership_id,  // MongoDB ObjectId as string
              price: parseFloat(membership.price) || 0,
              discount: 0,
              quantity: 1,
              total: parseFloat(membership.price) || 0,
            })

            if (!itemResponse.ok) {
              const errorData = await itemResponse.json()
              throw new Error(errorData.error || 'Failed to add membership to bill')
            }
          } catch (itemError) {
            console.error('Failed to add membership to bill:', itemError)
            throw itemError
          }
        }
      }

      // Handle prepaid packages (if any selected)
      let prepaidPackageId = null
      if (prepaidPackages.length > 0) {
        prepaidPackageId = prepaidPackages[0].prepaid_id
      }

      // Phase 5: Check if approval is needed
      if (pendingApproval && pendingApproval.approval_status === 'pending') {
        showInfo('Discount approval is pending. Please wait for approval before checkout.')
        return
      }

      // Phase 5: Check discount limit
      if (discountType === '%' && user) {
        const maxDiscount = getMaxDiscountPercent()
        const discountPercent = parseFloat(discountAmount) || 0
        
        if (discountPercent > maxDiscount) {
          if (!approvalReason.trim()) {
            setShowApprovalForm(true)
            showWarning('Please provide a reason for the discount approval request')
            return
          }
        }
      }

      // Calculate discount amount for membership (if applicable)
      let finalDiscountAmount = discountAmount
      let finalDiscountType = discountType
      
      if (membershipInfo && membershipInfo.plan && discountType === 'membership') {
        // For membership, send percentage - backend will calculate
        finalDiscountAmount = membershipInfo.plan.allocated_discount
        finalDiscountType = 'membership'
      } else if (discountType === '%') {
        // For percentage discount, keep as is
        finalDiscountAmount = discountAmount
        finalDiscountType = 'percentage'
      } else {
        // For fix discount, keep as is
        finalDiscountAmount = discountAmount
        finalDiscountType = 'fix'
      }

      // Checkout with selected date
      const checkoutBillDate = formatLocalDate(selectedDate) // Format as YYYY-MM-DD
      const checkoutResponse = await apiPost(`/api/bills/${billId}/checkout`, {
        bill_date: checkoutBillDate, // Send selected date to update bill_date during checkout
        discount_amount: membershipInfo && membershipInfo.plan && discountType === 'membership' 
          ? membershipInfo.plan.allocated_discount 
          : parseFloat(discountAmount) || 0,
        discount_type: discountType === 'membership' ? 'membership' : (discountType === '%' ? 'percentage' : 'fix'),
        discount_reason: approvalReason || undefined, // Phase 5: Include reason
        tax_rate: 18.0, // GST rate - ensure it's a float
        payment_mode: paymentMode,
        booking_status: bookingStatus,
        prepaid_package_id: prepaidPackageId,
      })

      if (checkoutResponse.ok) {
        const checkoutData = await checkoutResponse.json()
        
        // Use the billId that was used in the checkout call (already available)
        // The checkout response doesn't include the bill ID, but we already have it
        
        // Update appointment if we're editing one
        if (editingAppointmentId) {
          try {
            const firstService = services.find(s => 
              s.service_id && 
              s.staff_id && 
              s.startTime && 
              s.startTime.trim() !== ''
            )
            if (firstService) {
              const appointmentDate = formatLocalDate(selectedDate)
              let startTime = firstService.startTime
              if (startTime.split(':').length === 2) {
                startTime = `${startTime}:00`
              }

              const updateResponse = await apiPut(`/api/appointments/${editingAppointmentId}`, {
                customer_id: selectedCustomer.id,
                staff_id: firstService.staff_id,
                service_id: firstService.service_id,
                appointment_date: appointmentDate,
                start_time: startTime,
                status: bookingStatus,
                notes: bookingNote || undefined
              })

              if (updateResponse.ok) {
                showSuccess(`Appointment updated and bill created successfully! Bill Number: ${checkoutData.bill_number} | Final Amount: ₹${checkoutData.final_amount.toFixed(2)}`)
              } else {
                showSuccess(`Bill created successfully! Bill Number: ${checkoutData.bill_number} | Final Amount: ₹${checkoutData.final_amount.toFixed(2)}`)
                showWarning('Appointment update failed, but bill was created')
              }
            } else {
              showSuccess(`Bill created successfully! Bill Number: ${checkoutData.bill_number} | Final Amount: ₹${checkoutData.final_amount.toFixed(2)}`)
            }
          } catch (error) {
            console.error('Error updating appointment:', error)
            showSuccess(`Bill created successfully! Bill Number: ${checkoutData.bill_number} | Final Amount: ₹${checkoutData.final_amount.toFixed(2)}`)
            showWarning('Appointment update failed, but bill was created')
          }
          setEditingAppointmentId(null)
        } else {
          showSuccess(`Bill created successfully! Bill Number: ${checkoutData.bill_number} | Final Amount: ₹${checkoutData.final_amount.toFixed(2)}`)
        }
        
        // Celebrate with confetti!
        celebrateBig()
        
        // Set bill ID and fetch invoice data, then show modal
        // billId is already available from the checkout call
        setCurrentBillId(billId)
        await fetchInvoiceData(billId)
        setShowInvoiceModal(true)
      } else {
        let errorMessage = 'Failed to complete checkout. Please try again.'
        try {
          const error = await checkoutResponse.json()
          errorMessage = error.error || errorMessage
          
          // Phase 5: Handle approval required
          if (error.requires_approval && error.approval_id) {
            setPendingApproval({ id: error.approval_id, approval_status: 'pending' })
            setShowApprovalForm(true)
            errorMessage = error.message || 'Discount approval required before checkout'
          }
        } catch (e) {
          errorMessage = `Server error: ${checkoutResponse.status} ${checkoutResponse.statusText}`
        }
        showError(errorMessage)
      }
    } catch (error) {
      console.error('Error during checkout:', error)
      if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
        showError('Cannot connect to the server. Please make sure the backend server is running.')
      } else {
        showError(`Error during checkout: ${error.message || 'Unknown error'}`)
      }
    }
  }

  const formatDate = (dateInput) => {
    // Handle both Date objects and date strings
    const date = dateInput instanceof Date ? dateInput : new Date(dateInput)
    if (isNaN(date.getTime())) {
      return ''
    }
    const day = String(date.getDate()).padStart(2, '0')
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const year = date.getFullYear()
    return `${day}-${month}-${year}`
  }

  const formatTime = (timeString) => {
    if (!timeString) return ''
    const [hours, minutes] = timeString.split(':')
    const hour12 = hours % 12 || 12
    const ampm = hours >= 12 ? 'PM' : 'AM'
    return `${hour12}:${minutes} ${ampm}`
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
    if (!currentBillId) {
      showError('No bill found')
      return
    }

    try {
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
      
      const response = await fetch(`${API_BASE_URL}/api/bills/${currentBillId}/invoice/pdf`, {
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
        a.download = `invoice_${invoiceData?.bill_number || invoiceData?.invoice_number || currentBillId}.pdf`
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

  const handleCloseInvoiceModal = () => {
    setShowInvoiceModal(false)
    setInvoiceData(null)
    setCurrentBillId(null)
    handleReset()
  }

  const handleReviewUs = () => {
    showWarning('Review functionality coming soon')
  }

  return (
    <PageTransition>
      <div className="quick-sale-page">
      <div className="quick-sale-container">
        <div className="quick-sale-card">
          <h1 className="card-title">New Booking</h1>
          <div className="title-separator"></div>

          {/* Top Row: Search, Date, Customer Info */}
          <div className="top-row">
            <div className="search-container" style={{ position: 'relative' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px', width: '100%' }}>
                <label 
                  className="field-label" 
                  style={{ color: selectedCustomer ? '#4CAF50' : '#374151', margin: 0, cursor: 'pointer' }}
                  onClick={() => {
                    // When label is clicked, clear selection if customer is selected and focus the input
                    if (selectedCustomer) {
                      setSelectedCustomer(null)
                      setSearchQuery('')
                      setFilteredCustomers(customers.slice(0, 10))
                      setShowCustomerDropdown(true)
                    }
                    // Focus the input to trigger the focus handler
                    const input = document.querySelector('.search-input')
                    if (input) {
                      input.focus()
                    }
                  }}
                >
                <span className="customer-label-text">Customer</span> {selectedCustomer && <span style={{ color: '#4CAF50', fontSize: '12px', marginLeft: '8px' }}>✓ Selected: {selectedCustomer.firstName || ''} {selectedCustomer.lastName || ''}</span>}
              </label>
                {!selectedCustomer && (
                        <button
                    className="add-new-customer-btn-header"
                          onClick={() => {
                            setShowNewCustomerForm(true)
                            setShowCustomerDropdown(false)
                            setNewCustomerData({ 
                              mobile: searchQuery.match(/^\d+$/) ? searchQuery : '', 
                              name: '', 
                              gender: '',
                              source: 'Walk-in',
                              dobRange: ''
                            })
                          }}
                          style={{
                      padding: '6px 14px',
                            background: '#0F766E',
                            color: 'white',
                            border: 'none',
                            borderRadius: '6px',
                      fontSize: '13px',
                            fontWeight: '600',
                      cursor: 'pointer',
                      whiteSpace: 'nowrap',
                      transition: 'all 0.2s ease',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px'
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.background = '#0d9488'
                      e.currentTarget.style.transform = 'translateY(-1px)'
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.background = '#0F766E'
                      e.currentTarget.style.transform = 'translateY(0)'
                          }}
                        >
                    <span>+</span> Add New Customer
                        </button>
                )}
              </div>
              <div style={{ position: 'relative', flex: 1 }}>
                <input
                  type="text"
                  className="search-input"
                  placeholder={selectedCustomer ? `${selectedCustomer.firstName || ''} ${selectedCustomer.lastName || ''} - ${selectedCustomer.mobile}` : "Search by Mobile Number or Name"}
                  value={selectedCustomer ? `${selectedCustomer.firstName || ''} ${selectedCustomer.lastName || ''} - ${selectedCustomer.mobile}` : searchQuery}
                  onChange={handleCustomerInputChange}
                  onFocus={handleCustomerInputFocus}
                  onClick={() => {
                    // When input is clicked with a selected customer, clear selection and reopen dropdown
                    if (selectedCustomer) {
                      setSelectedCustomer(null)
                      setSearchQuery('')
                      setFilteredCustomers(customers.slice(0, 10))
                      setShowCustomerDropdown(true)
                    }
                  }}
                  readOnly={selectedCustomer ? true : false}
                  style={{
                    borderColor: selectedCustomer ? '#4CAF50' : (showCustomerDropdown ? '#0F766E' : '#d1d5db'),
                    borderWidth: selectedCustomer ? '2px' : '1px',
                    backgroundColor: selectedCustomer ? '#f0fdf4' : 'white',
                    cursor: selectedCustomer ? 'pointer' : 'text'
                  }}
                />
                {showCustomerDropdown && (
                  <div className="customer-dropdown">
                    {filteredCustomers.length === 0 && searchQuery.length > 0 ? (
                      <div className="no-customer-section">
                        <div style={{ padding: '12px', color: '#6b7280', textAlign: 'center' }}>
                          No customers found for "{searchQuery}"
                        </div>
                      </div>
                    ) : filteredCustomers.length === 0 && searchQuery.length === 0 ? (
                      <div style={{ padding: '12px', color: '#6b7280', textAlign: 'center' }}>
                        Start typing to search for customers...
                      </div>
                    ) : (
                      <>
                        {filteredCustomers.map(customer => (
                          <div
                            key={customer.id}
                            className="customer-dropdown-item"
                            onClick={() => selectCustomer(customer)}
                          >
                            <div className="customer-dropdown-item-name">
                              {customer.firstName || ''} {customer.lastName || ''}
                            </div>
                            <div className="customer-dropdown-item-mobile">
                              {customer.mobile}
                            </div>
                          </div>
                        ))}
                        {filteredCustomers.length >= 10 && searchQuery.length === 0 && (
                          <div style={{ padding: '8px 16px', fontSize: '12px', color: '#6b7280', textAlign: 'center', borderTop: '1px solid #f0f0f0' }}>
                            Showing first 10 customers. Type to search more...
                          </div>
                        )}
                      </>
                    )}
                  </div>
                )}
              </div>
            </div>
            <div className="date-container">
              <label className="date-label">Date</label>
              <div 
                className="date-input-wrapper"
                onClick={(e) => {
                  // Find and click the DatePicker input
                  const input = e.currentTarget.querySelector('.react-datepicker__input-container input')
                  if (input) {
                    input.focus()
                    input.click()
                  }
                }}
              >
                <DatePicker
                  selected={selectedDate}
                  onChange={(date) => {
                    if (date) {
                      setSelectedDate(date)
                    }
                  }}
                  dateFormat="dd/MM/yyyy"
                  className="date-picker"
                  placeholderText="Select date"
                />
                <span className="date-display">{formatDate(selectedDate)}</span>
                <span className="calendar-icon"><FaCalendar /></span>
              </div>
            </div>
          </div>

          {/* Customer Details Card - Show when customer is selected */}
          {selectedCustomer && (
            <div className="customer-info-card">
              {loadingCustomerDetails ? (
                <div style={{ padding: '20px', textAlign: 'center', color: '#6b7280' }}>
                  Loading customer details...
                </div>
              ) : customerDetails ? (
                <>
              <div className="customer-info-table">
                <div className="customer-info-header">
                  <div className="customer-info-header-cell">Membership</div>
                  <div className="customer-info-header-cell">Last Visit</div>
                  <div className="customer-info-header-cell">Total Visits</div>
                  <div className="customer-info-header-cell">Total Revenue</div>
                </div>
                <div className="customer-info-row">
                  <div className="customer-info-cell">{customerDetails.membership}</div>
                  <div className="customer-info-cell">{customerDetails.lastVisit ? formatDate(customerDetails.lastVisit) : 'N/A'}</div>
                  <div className="customer-info-cell">{customerDetails.totalVisits}</div>
                  <div className="customer-info-cell">₹{customerDetails.totalRevenue.toFixed(2)}</div>
                </div>
                <div className="customer-note-row">
                  <span className="customer-note-label">Customer Note:</span>
                  <span className="customer-note-value">{customerDetails.notes}</span>
                </div>
              </div>
              <div className="customer-info-sidebar">
                <button className="bill-activity-btn" onClick={handleShowBillActivity}>
                  Bill Activity
                </button>
              </div>
                </>
              ) : (
                <div style={{ padding: '20px', textAlign: 'center', color: '#6b7280' }}>
                  No details available
                </div>
              )}
            </div>
          )}

          {/* Service Table */}
          <div className="service-table-container">
            <table className="service-table">
              <thead>
                <tr>
                  <th>Service</th>
                  <th>Staff</th>
                  <th>Start Time</th>
                  <th>Price</th>
                  <th>Discount</th>
                  <th>Total</th>
                  <th>Remove</th>
                </tr>
              </thead>
              <tbody>
                {services.length === 0 ? (
                  <tr>
                    <td colSpan="7" className="empty-table-message">
                      No services added. Click "Add Service" below to add services.
                    </td>
                  </tr>
                ) : (
                  services.map((service) => (
                    <tr key={service.id} className="service-table-row">
                      <td>
                        <select
                          className="table-select"
                          value={service.service_id}
                          onChange={(e) => updateService(service.id, 'service_id', e.target.value)}
                        >
                          <option value="">Choose service</option>
                          {availableServices.map(svc => (
                            <option key={svc.id} value={svc.id}>
                              {svc.name} - ₹{svc.price}
                            </option>
                          ))}
                        </select>
                      </td>
                      <td>
                        <select
                          className="table-select"
                          value={service.staff_id}
                          onChange={(e) => updateService(service.id, 'staff_id', e.target.value)}
                        >
                          <option value="">Choose staff</option>
                          {staffMembers.map(staff => (
                            <option key={staff.id} value={staff.id}>
                              {staff.firstName} {staff.lastName}
                            </option>
                          ))}
                        </select>
                      </td>
                      <td>
                        <input
                          type="time"
                          className="table-time-input"
                          value={service.startTime || ''}
                          onChange={(e) => {
                            const timeValue = e.target.value
                            if (timeValue) {
                              updateService(service.id, 'startTime', timeValue)
                            }
                          }}
                          onInput={(e) => {
                            const timeValue = e.target.value
                            if (timeValue) {
                              updateService(service.id, 'startTime', timeValue)
                            }
                          }}
                          onBlur={(e) => {
                            const timeValue = e.target.value
                            if (timeValue && timeValue !== service.startTime) {
                              updateService(service.id, 'startTime', timeValue)
                            }
                          }}
                        />
                      </td>
                      <td>
                        <input
                          type="number"
                          className="table-input"
                          placeholder="0"
                          value={service.price}
                          onChange={(e) => updateService(service.id, 'price', e.target.value)}
                        />
                      </td>
                      <td>
                        <div className="discount-input-wrapper">
                          <input
                            type="number"
                            className="table-input"
                            placeholder="0"
                            value={service.discount}
                            onChange={(e) => updateService(service.id, 'discount', e.target.value)}
                          />
                          <span className="discount-percent">%</span>
                        </div>
                      </td>
                      <td>
                        <input
                          type="number"
                          className="table-input"
                          placeholder="0"
                          value={service.total.toFixed(2)}
                          readOnly
                        />
                      </td>
                      <td>
                        <button
                          className="table-remove-btn"
                          onClick={() => removeService(service.id)}
                          title="Remove service"
                        >
                          <FaTrash />
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

        {/* Pill Buttons Row */}
        <div className="pill-buttons-row">
          <button className="pill-button" onClick={addService}>
            Add Service
          </button>
          <button className="pill-button" onClick={addPackage}>Add Package</button>
          <button className="pill-button" onClick={addProduct}>Add Product</button>
          <button className="pill-button" onClick={addPrepaid}>Add Prepaid</button>
          <button className="pill-button" onClick={addMembership}>Add Membership</button>
        </div>

        {/* Display Added Items in Grid Layout */}
        {(packages.length > 0 || products.length > 0 || prepaidPackages.length > 0 || memberships.length > 0) && (
          <div className="added-items-grid">
            {/* Display Added Packages */}
            {packages.length > 0 && (
              <div className="added-items-section">
                <h3>Added Packages:</h3>
                <div className="added-items-list">
                  {packages.map(pkg => (
                    <div key={pkg.id} className="added-item">
                      <span>{pkg.name} - ₹{pkg.price}</span>
                      <button onClick={() => removePackage(pkg.id)} className="remove-btn">Remove</button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Display Added Products */}
            {products.length > 0 && (
              <div className="added-items-section">
                <h3>Added Products:</h3>
                <div className="added-items-list">
                  {products.map(product => (
                    <div key={product.id} className="added-item">
                      <span>{product.name} - ₹{product.price} x {product.quantity} = ₹{product.total}</span>
                      <button onClick={() => removeProduct(product.id)} className="remove-btn">Remove</button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Display Added Prepaid */}
            {prepaidPackages.length > 0 && (
              <div className="added-items-section">
                <h3>Added Prepaid Packages:</h3>
                <div className="added-items-list">
                  {prepaidPackages.map(prepaid => (
                    <div key={prepaid.id} className="added-item">
                      <span>{prepaid.name} - Balance: ₹{prepaid.balance}</span>
                      <button onClick={() => removePrepaid(prepaid.id)} className="remove-btn">Remove</button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Display Added Memberships */}
            {memberships.length > 0 && (
              <div className="added-items-section">
                <h3>Added Memberships:</h3>
                <div className="added-items-list">
                  {memberships.map(membership => (
                    <div key={membership.id} className="added-item">
                      <span>{membership.name} - ₹{membership.price}</span>
                      <button onClick={() => removeMembership(membership.id)} className="remove-btn">Remove</button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

          {/* Bottom Section: Three Columns Layout */}
          <div className="bottom-section-grid">
            {/* Left Column: Booking Details */}
            <div className="bottom-column booking-column">
              <div className="booking-status-container">
                <label className="form-label">Booking Status</label>
                <select
                  className="form-select"
                  value={bookingStatus}
                  onChange={(e) => {
                    const newStatus = e.target.value
                    setBookingStatus(newStatus)
                    
                    // Reset appointment created flag when changing status
                    if (newStatus === 'service-completed') {
                      appointmentCreatedRef.current = false
                    } else if (newStatus === 'confirmed') {
                      appointmentCreatedRef.current = false
                    }
                  }}
                >
                  <option value="confirmed">Confirmed</option>
                  <option value="service-completed">Service Completed</option>
                </select>
              </div>
              
              {/* Mode of Payment */}
              <div className="payment-section">
                <label className="form-label">Payment Mode</label>
                <div className="payment-pills">
                  <button
                    className={`payment-pill ${paymentMode === 'cash' ? 'active' : ''}`}
                    onClick={() => setPaymentMode('cash')}
                  >
                    Cash
                  </button>
                  <button
                    className={`payment-pill ${paymentMode === 'upi' ? 'active' : ''}`}
                    onClick={() => setPaymentMode('upi')}
                  >
                    UPI
                  </button>
                  <button
                    className={`payment-pill ${paymentMode === 'card' ? 'active' : ''}`}
                    onClick={() => setPaymentMode('card')}
                  >
                    Card Payment
                  </button>
                </div>
              </div>
              
              <div className="booking-note-membership-wrapper">
                <div className="booking-note-container">
                  <h3 className="booking-note-title">Booking Note</h3>
                  <textarea
                    className="form-textarea"
                    placeholder="Add any notes here..."
                    rows="3"
                    value={bookingNote}
                    onChange={(e) => setBookingNote(e.target.value)}
                  />
                </div>
                
                {membershipInfo && membershipInfo.plan && (
                  <div className="membership-box-container">
                    <div className="membership-box">
                      <div style={{ 
                        padding: '12px', 
                        background: '#dbeafe', 
                        borderRadius: '8px',
                        border: '1px solid #3b82f6',
                        color: '#1e40af',
                        marginBottom: '12px'
                      }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                          <FaGift size={16} />
                          <strong>Active Membership: {membershipInfo.plan.name}</strong>
                        </div>
                        <div className="membership-info-text">
                          {membershipInfo.plan.allocated_discount}% discount will be applied automatically
                        </div>
                        {membershipInfo.expiry_date && (
                          <div className="membership-expiry-text">
                            Expires: {new Date(membershipInfo.expiry_date).toLocaleDateString()}
                          </div>
                        )}
                      </div>
                      <div className="membership-note-text">
                        Membership discount is automatic and cannot be modified
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Middle Column: Discount */}
            <div className="bottom-column discount-payment-column">
              {/* Discount Section */}
              {membershipInfo && membershipInfo.plan ? null : user && user.role === 'owner' ? (
                <div className="discount-section">
                  <label className="form-label">Discount</label>
                  <input
                    type="number"
                    className="form-input discount-input"
                    placeholder="Discount Amount (₹)"
                    value={discountAmount}
                    onChange={(e) => {
                      const value = parseFloat(e.target.value) || 0
                      setDiscountAmount(value)
                    }}
                  />
                  {discountType === '%' && (
                    <small className="discount-limit-info">
                      Owner: Unlimited discount
                    </small>
                  )}
                </div>
              ) : (
                <div className="discount-section" style={{ 
                  padding: '12px', 
                  background: '#fef3c7', 
                  borderRadius: '8px',
                  border: '1px solid #fbbf24',
                  color: '#92400e'
                }}>
                  <small>
                    <strong>Note:</strong> Only owners can apply discounts. Contact the owner for discount requests.
                  </small>
                </div>
              )}
            </div>

            {/* Right Column: Bill Summary */}
            <div className="bottom-column summary-column">
              <div className="summary-section">
                <h3 className="summary-title">Bill Summary</h3>
                <div className="summary-title-separator"></div>
                <div className="summary-values">
                  <div className="summary-row">
                    <span className="summary-label">Subtotal:</span>
                    <span className="summary-value">₹ {calculateSubtotal().toFixed(2)}</span>
                  </div>
                  {membershipInfo && membershipInfo.plan && discountType === 'membership' && calculateDiscount() > 0 && (
                    <div className="summary-row membership-discount-row">
                      <span className="summary-label" style={{ color: '#0F766E', display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <FaGift style={{ fontSize: '14px' }} />
                        Membership Discount ({membershipInfo.plan.allocated_discount}%):
                      </span>
                      <span className="summary-value" style={{ color: '#0F766E', fontWeight: '600' }}>
                        - ₹ {calculateDiscount().toFixed(2)}
                      </span>
                    </div>
                  )}
                  <div className="summary-row net-row">
                    <span className="summary-label">Net:</span>
                    <span className="summary-value net-value">₹ {calculateNet().toFixed(2)}</span>
                  </div>
                  <div className="summary-row">
                    <span className="summary-label">Tax:</span>
                    <span className="summary-value">₹ {calculateTax().toFixed(2)}</span>
                  </div>
                  <div className="summary-row final">
                    <span className="summary-label">Final Amount:</span>
                    <span className="summary-value final-value">₹ {calculateFinalAmount().toFixed(2)}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Bottom Buttons */}
          <div className="action-buttons">
            <button className="reset-button" onClick={handleReset}>Reset</button>
            {bookingStatus === 'confirmed' ? (
              <button
                className="checkout-button"
                onClick={async () => {
                  if (!appointmentCreatedRef.current) {
                    const success = await handleCreateAppointment()
                    if (success) {
                      appointmentCreatedRef.current = true
                    }
                  } else {
                    showInfo('Appointment already created for this booking')
                  }
                }}
                disabled={appointmentCreatedRef.current}
              >
                {appointmentCreatedRef.current ? '✓ Saved' : 'Confirm Booking'}
              </button>
            ) : (
              <button 
                className="checkout-button" 
                onClick={handleCheckout}
                disabled={
                  (pendingApproval && pendingApproval.approval_status === 'pending')
                }
              >
                {pendingApproval && pendingApproval.approval_status === 'pending' 
                  ? 'Approval Pending...' 
                  : 'Checkout'}
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Approval Request Form Modal */}
      {showApprovalForm && (
        <div className="modal-overlay" onClick={() => setShowApprovalForm(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2>Discount Approval Required</h2>
            <p>Your discount exceeds your role limit. Please provide a reason for approval.</p>
            <div className="form-group">
              <label>Reason for Discount *</label>
              <textarea
                value={approvalReason}
                onChange={(e) => setApprovalReason(e.target.value)}
                rows="4"
                placeholder="Explain why this discount is needed..."
                required
              />
            </div>
            <div className="modal-actions">
              <button type="button" onClick={() => {
                setShowApprovalForm(false)
                setApprovalReason('')
              }}>
                Cancel
              </button>
              <button 
                onClick={() => {
                  if (approvalReason.trim()) {
                    setShowApprovalForm(false)
                    // Approval request will be created during checkout
                  } else {
                    showWarning('Please provide a reason')
                  }
                }}
                className="btn-primary"
              >
                Submit for Approval
              </button>
            </div>
          </div>
        </div>
      )}

      {/* New Customer Modal */}
      {showNewCustomerForm && (
        <div className="new-customer-modal-overlay" onClick={() => {
          setShowNewCustomerForm(false)
          setNewCustomerData({ mobile: '', name: '', gender: '', source: 'Walk-in', dobRange: '' })
        }}>
          <div className="new-customer-modal" onClick={(e) => e.stopPropagation()}>
            <div className="new-customer-modal-header">
              <h2>Add New Customer</h2>
              <button 
                className="modal-close-btn"
                onClick={() => {
                  setShowNewCustomerForm(false)
                  setNewCustomerData({ mobile: '', name: '', gender: '', source: 'Walk-in', dobRange: '' })
                }}
                disabled={creatingCustomer}
              >
                <FaTimes />
              </button>
            </div>
            <div className="new-customer-modal-body">
              <div className="form-grid">
                <div className="form-field-modal">
                  <label className="modal-label">
                    Mobile Number <span className="required">*</span>
                  </label>
                  <input
                    type="text"
                    placeholder="Enter 10-digit mobile"
                    value={newCustomerData.mobile}
                    onChange={(e) => setNewCustomerData({ ...newCustomerData, mobile: e.target.value })}
                    className="modal-input"
                    maxLength={10}
                    disabled={creatingCustomer}
                  />
                </div>
                <div className="form-field-modal">
                  <label className="modal-label">
                    Name <span className="required">*</span>
                  </label>
                  <input
                    type="text"
                    placeholder="Enter full name"
                    value={newCustomerData.name}
                    onChange={(e) => setNewCustomerData({ ...newCustomerData, name: e.target.value })}
                    className="modal-input"
                    disabled={creatingCustomer}
                  />
                </div>
                <div className="form-field-modal">
                  <label className="modal-label">
                    Gender <span className="required">*</span>
                  </label>
                  <select
                    value={newCustomerData.gender}
                    onChange={(e) => setNewCustomerData({ ...newCustomerData, gender: e.target.value })}
                    className="modal-select"
                    disabled={creatingCustomer}
                  >
                    <option value="">Select gender</option>
                    <option value="Male">Male</option>
                    <option value="Female">Female</option>
                    <option value="Other">Other</option>
                  </select>
                </div>
                <div className="form-field-modal">
                  <label className="modal-label">
                    Source
                  </label>
                  <select
                    value={newCustomerData.source}
                    onChange={(e) => setNewCustomerData({ ...newCustomerData, source: e.target.value })}
                    className="modal-select"
                    disabled={creatingCustomer}
                  >
                    <option value="Walk-in">Walk-in</option>
                    <option value="Facebook">Facebook</option>
                    <option value="Instagram">Instagram</option>
                    <option value="Google">Google</option>
                    <option value="Referral">Referral</option>
                    <option value="Website">Website</option>
                    <option value="Other">Other</option>
                  </select>
                </div>
                <div className="form-field-modal">
                  <label className="modal-label">
                    Age Range
                  </label>
                  <select
                    value={newCustomerData.dobRange}
                    onChange={(e) => setNewCustomerData({ ...newCustomerData, dobRange: e.target.value })}
                    className="modal-select"
                    disabled={creatingCustomer}
                  >
                    <option value="">Select age range</option>
                    <option value="Young">Young (18-30)</option>
                    <option value="Adult">Adult (31-50)</option>
                    <option value="Senior">Senior (51+)</option>
                  </select>
                </div>
              </div>
            </div>
            <div className="new-customer-modal-footer">
              <button
                className="modal-btn-cancel"
                onClick={() => {
                  setShowNewCustomerForm(false)
                  setNewCustomerData({ mobile: '', name: '', gender: '', source: 'Walk-in', dobRange: '' })
                }}
                disabled={creatingCustomer}
              >
                Cancel
              </button>
              <button
                className="modal-btn-create"
                onClick={handleCreateNewCustomer}
                disabled={creatingCustomer}
              >
                {creatingCustomer ? 'Creating...' : 'Create & Select'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Inventory Modal */}
      {showInventoryModal && (
        <div className="inventory-modal-overlay" onClick={() => setShowInventoryModal(false)}>
          <div className="inventory-modal" onClick={(e) => e.stopPropagation()}>
            <div className="inventory-modal-header">
              <h2>
                <FaBoxes style={{ marginRight: '10px' }} />
                Related Inventory for: {selectedServiceForInventory?.name}
              </h2>
              <button 
                className="modal-close-btn"
                onClick={() => setShowInventoryModal(false)}
              >
                <FaTimes />
              </button>
            </div>
            <div className="inventory-modal-body">
              {serviceRelatedProducts.length > 0 ? (
                <div className="inventory-grid">
                  {serviceRelatedProducts.map(product => (
                    <div key={product.id} className="inventory-item">
                      <div className="inventory-item-header">
                        <h3>{product.name}</h3>
                        <span className="inventory-price">₹{product.price}</span>
                      </div>
                      <div className="inventory-item-details">
                        <div className="inventory-detail-row">
                          <span className="inventory-label">Category:</span>
                          <span className="inventory-value">{product.category || 'N/A'}</span>
                        </div>
                        <div className="inventory-detail-row">
                          <span className="inventory-label">Stock:</span>
                          <span className={`inventory-stock ${product.stock > 10 ? 'in-stock' : product.stock > 0 ? 'low-stock' : 'out-of-stock'}`}>
                            {product.stock > 0 ? `${product.stock} units` : 'Out of Stock'}
                          </span>
                        </div>
                        <div className="inventory-detail-row">
                          <span className="inventory-label">Brand:</span>
                          <span className="inventory-value">{product.brand || 'N/A'}</span>
                        </div>
                      </div>
                      <button 
                        className="add-inventory-btn"
                        onClick={() => {
                          // Add product to cart
                          const newProduct = {
                            id: Date.now(),
                            product_id: product.id,
                            name: product.name,
                            quantity: 1,
                            price: product.price,
                            total: product.price
                          }
                          setProducts([...products, newProduct])
                          showSuccess(`${product.name} added to bill`)
                          setShowInventoryModal(false)
                        }}
                        disabled={product.stock <= 0}
                      >
                        {product.stock > 0 ? 'Add to Bill' : 'Out of Stock'}
                      </button>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="inventory-empty">
                  <FaBoxes size={48} color="#cbd5e1" />
                  <p>No related inventory found for this service</p>
                  <p className="inventory-empty-hint">Products related to "{selectedServiceForInventory?.name}" will appear here</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Bill Activity Modal */}
      {showBillActivityModal && (
        <div className="bill-activity-modal-overlay" onClick={() => setShowBillActivityModal(false)}>
          <div className="bill-activity-modal" onClick={(e) => e.stopPropagation()}>
            <div className="bill-activity-modal-header">
              <h2>
                Bill Activity - {selectedCustomer?.firstName} {selectedCustomer?.lastName}
              </h2>
              <button 
                className="modal-close-btn"
                onClick={() => setShowBillActivityModal(false)}
              >
                <FaTimes />
              </button>
            </div>
            <div className="bill-activity-modal-body">
              {loadingBills ? (
                <div className="loading-container">
                  <div className="loading-spinner"></div>
                  <p>Loading bill history...</p>
                </div>
              ) : customerBills.length > 0 ? (
                <div className="bills-list">
                  {customerBills.map((bill, index) => (
                    <div key={bill.id || index} className="bill-card">
                      <div className="bill-card-header">
                        <div className="bill-info">
                          <h3 className="bill-number">#{bill.bill_number}</h3>
                          <span className="bill-date">
                            {bill.bill_date ? new Date(bill.bill_date).toLocaleDateString('en-IN', {
                              day: '2-digit',
                              month: 'short',
                              year: 'numeric'
                            }) : 'N/A'}
                          </span>
                        </div>
                        <div className="bill-amount">
                          <span className="amount-label">Total</span>
                          <span className="amount-value">₹{(bill.final_amount || 0).toFixed(2)}</span>
                        </div>
                      </div>
                      <div className="bill-card-body">
                        <div className="bill-detail-row">
                          <span className="detail-label">Subtotal:</span>
                          <span className="detail-value">₹{(bill.subtotal || 0).toFixed(2)}</span>
                        </div>
                        <div className="bill-detail-row">
                          <span className="detail-label">Discount:</span>
                          <span className="detail-value">
                            - ₹{(bill.discount_amount || 0).toFixed(2)}
                            {bill.discount_type === 'percentage' && bill.discount_amount > 0 && 
                              ` (${((bill.discount_amount / bill.subtotal) * 100).toFixed(0)}%)`
                            }
                          </span>
                        </div>
                        <div className="bill-detail-row">
                          <span className="detail-label">Tax:</span>
                          <span className="detail-value">+ ₹{(bill.tax_amount || 0).toFixed(2)}</span>
                        </div>
                        <div className="bill-detail-row">
                          <span className="detail-label">Payment Mode:</span>
                          <span className="detail-value payment-badge">
                            {bill.payment_mode ? bill.payment_mode.toUpperCase() : 'N/A'}
                          </span>
                        </div>
                        <div className="bill-detail-row">
                          <span className="detail-label">Status:</span>
                          <span className={`status-badge status-${bill.booking_status}`}>
                            {bill.booking_status || 'completed'}
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="empty-bills">
                  <div className="empty-icon"><FaClipboardList size={48} /></div>
                  <p>No bill history found</p>
                  <p className="empty-hint">This customer hasn't made any purchases yet</p>
                </div>
              )}
            </div>
            <div className="bill-activity-modal-footer">
              <div className="bills-summary">
                <div className="summary-item">
                  <span className="summary-label">Total Bills:</span>
                  <span className="summary-value">{customerBills.length}</span>
                </div>
                <div className="summary-item">
                  <span className="summary-label">Total Revenue:</span>
                  <span className="summary-value">
                    ₹{customerBills.reduce((sum, bill) => sum + (bill.final_amount || 0), 0).toFixed(2)}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Package Selection Modal */}
      {showPackageModal && (
        <div className="selection-modal-overlay" onClick={() => setShowPackageModal(false)}>
          <div className="selection-modal" onClick={(e) => e.stopPropagation()}>
            <div className="selection-modal-header">
              <h2>Select Package</h2>
              <button className="modal-close-btn" onClick={() => setShowPackageModal(false)}>
                <FaTimes />
              </button>
            </div>
            <div className="selection-modal-body">
              {availablePackages.length > 0 ? (
                <div className="selection-grid">
                  {availablePackages.map(pkg => (
                    <div key={pkg.id} className="selection-item package-item" onClick={() => handleSelectPackage(pkg)}>
                      <div className="selection-item-header">
                        <h3>{pkg.name}</h3>
                        <span className="selection-price">₹{pkg.price}</span>
                      </div>
                      <div className="selection-item-details">
                        <p className="package-description">{pkg.description || 'Package details'}</p>
                        {pkg.service_details && pkg.service_details.length > 0 && (
                          <div className="package-services-list">
                            <p className="services-label">Includes {pkg.service_details.length} Services:</p>
                            <ul className="services-list">
                              {pkg.service_details.map((service, idx) => (
                                <li key={idx} className="service-item">
                                  <span className="service-name">{service.name}</span>
                                  <span className="service-meta">
                                    ₹{service.price} • {service.duration}min
                                  </span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="selection-empty">
                  <p>No packages available</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Product Selection Modal */}
      {showProductModal && (
        <div className="selection-modal-overlay" onClick={() => setShowProductModal(false)}>
          <div className="selection-modal" onClick={(e) => e.stopPropagation()}>
            <div className="selection-modal-header">
              <h2>Select Product</h2>
              <button className="modal-close-btn" onClick={() => setShowProductModal(false)}>
                <FaTimes />
              </button>
            </div>
            <div className="selection-modal-body">
              {availableProducts.length > 0 ? (
                <div className="selection-grid">
                  {availableProducts.map(product => {
                    const stock = product.stock_quantity || 0
                    const isLowStock = stock > 0 && stock <= 5
                    const isOutOfStock = stock <= 0
                    
                    return (
                      <div 
                        key={product.id} 
                        className={`selection-item ${isOutOfStock ? 'out-of-stock' : ''} ${isLowStock ? 'low-stock' : ''}`}
                      >
                        <div className="selection-item-header">
                          <h3>{product.name}</h3>
                          <span className="selection-price">₹{product.price}</span>
                        </div>
                        <div className="selection-item-details">
                          <p className={`stock-info ${isOutOfStock ? 'stock-out' : isLowStock ? 'stock-low' : 'stock-ok'}`} style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                            Stock: {stock} units
                            {isLowStock && !isOutOfStock && (
                              <>
                                <FaExclamationTriangle size={14} /> Low Stock
                              </>
                            )}
                            {isOutOfStock && (
                              <>
                                <FaTimesCircle size={14} /> Out of Stock
                              </>
                            )}
                          </p>
                          <p>Brand: {product.brand || 'N/A'}</p>
                          {product.category && <p>Category: {product.category}</p>}
                          <div className="quantity-selector">
                            <label>Quantity:</label>
                            <input 
                              type="number" 
                              min="1" 
                              max={stock || 1}
                              value={selectedQuantity}
                              onChange={(e) => setSelectedQuantity(parseInt(e.target.value) || 1)}
                              onClick={(e) => e.stopPropagation()}
                              disabled={isOutOfStock}
                            />
                          </div>
                          <button 
                            className="select-btn"
                            onClick={(e) => {
                              e.stopPropagation()
                              handleSelectProduct(product, selectedQuantity)
                            }}
                            disabled={isOutOfStock}
                          >
                            {isOutOfStock ? 'Out of Stock' : 'Add to Bill'}
                          </button>
                        </div>
                      </div>
                    )
                  })}
                </div>
              ) : (
                <div className="selection-empty">
                  <p>No products available</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Prepaid Selection Modal */}
      {showPrepaidModal && (
        <div className="selection-modal-overlay" onClick={() => setShowPrepaidModal(false)}>
          <div className="selection-modal" onClick={(e) => e.stopPropagation()}>
            <div className="selection-modal-header">
              <h2>Select Prepaid Package</h2>
              <button className="modal-close-btn" onClick={() => setShowPrepaidModal(false)}>
                <FaTimes />
              </button>
            </div>
            <div className="selection-modal-body">
              {availablePrepaid.length > 0 ? (
                <div className="selection-grid">
                  {availablePrepaid.map(prepaid => (
                    <div key={prepaid.id} className="selection-item" onClick={() => handleSelectPrepaid(prepaid)}>
                      <div className="selection-item-header">
                        <h3>{prepaid.name}</h3>
                        <span className="selection-price">₹{prepaid.price || prepaid.remaining_balance || 0}</span>
                      </div>
                      <div className="selection-item-details">
                        {prepaid.group_name && <p>Group: {prepaid.group_name}</p>}
                        <p>Balance: ₹{prepaid.remaining_balance || prepaid.price || 0}</p>
                        {prepaid.expiry_date && (
                          <p>Expires: {new Date(prepaid.expiry_date).toLocaleDateString()}</p>
                        )}
                        <p className="prepaid-status">Status: {prepaid.status || 'active'}</p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="selection-empty">
                  <p>No prepaid packages available</p>
                  <p className="selection-empty-hint">No prepaid packages to purchase at the moment</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Membership Selection Modal */}
      {showMembershipModal && (
        <div className="selection-modal-overlay" onClick={() => setShowMembershipModal(false)}>
          <div className="selection-modal" onClick={(e) => e.stopPropagation()}>
            <div className="selection-modal-header">
              <h2>Select Membership Plan</h2>
              <button className="modal-close-btn" onClick={() => setShowMembershipModal(false)}>
                <FaTimes />
              </button>
            </div>
            <div className="selection-modal-body">
              {availableMemberships.length > 0 ? (
                <div className="selection-grid">
                  {availableMemberships.map(membership => (
                    <div key={membership.id} className="selection-item" onClick={() => handleSelectMembership(membership)}>
                      <div className="selection-item-header">
                        <h3>{membership.name}</h3>
                        <span className="selection-price">₹{membership.price}</span>
                      </div>
                      <div className="selection-item-details">
                        <p>Validity: {membership.validity_days} days</p>
                        <p>{membership.description || 'Membership benefits'}</p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="selection-empty">
                  <p>No membership plans available</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Invoice Modal */}
      {showInvoiceModal && (
        <div className="invoice-modal-overlay" onClick={handleCloseInvoiceModal}>
          <div className="invoice-modal-container" onClick={(e) => e.stopPropagation()}>
            <div className="invoice-modal-header">
              <h2>Invoice</h2>
              <button className="invoice-modal-close-btn" onClick={handleCloseInvoiceModal}>
                <FaTimes />
              </button>
            </div>
            
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
                <p>No invoice data available.</p>
                <button className="invoice-action-btn" onClick={handleCloseInvoiceModal}>
                  Close
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
    </PageTransition>
  )
}

export default QuickSale
