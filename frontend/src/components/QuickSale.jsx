import React, { useState, useEffect, useRef } from 'react'
import { createPortal } from 'react-dom'
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
import CompactSelect from './shared/CompactSelect'
import ClassicTimePicker from './shared/ClassicTimePicker'

const ServiceSearchSelect = ({ value, services, onChange, disabled, loadingServices }) => {
  const [isOpen, setIsOpen] = useState(false)
  const [searchText, setSearchText] = useState('')
  const [highlightedIndex, setHighlightedIndex] = useState(-1)
  const [dropdownPos, setDropdownPos] = useState({ top: 0, left: 0, width: 0 })
  const wrapperRef = useRef(null)
  const inputRef = useRef(null)
  const dropdownRef = useRef(null)

  const selectedService = services.find(s => s.id === value)
  const selectedLabel = selectedService ? `${selectedService.name} - ₹${selectedService.price}` : ''
  const displayValue = isOpen ? searchText : selectedLabel

  const filteredServices = searchText.trim()
    ? services.filter(s => (s.name || '').toLowerCase().includes(searchText.trim().toLowerCase()))
    : services

  const updateDropdownPosition = () => {
    if (!inputRef.current) return
    const rect = inputRef.current.getBoundingClientRect()
    // Give the dropdown a minimum readable width so service names don't truncate
    // on narrow columns (tablet portrait, cramped Service column, etc.).
    const MIN_WIDTH = 280
    const viewportW = window.innerWidth
    const width = Math.max(rect.width, Math.min(MIN_WIDTH, viewportW - 16))
    // Keep the dropdown on-screen — shift left if the min-width would overflow the viewport.
    let left = rect.left
    if (left + width > viewportW - 8) {
      left = Math.max(8, viewportW - width - 8)
    }
    setDropdownPos({
      top: rect.bottom + 2,
      left,
      width,
    })
  }

  useEffect(() => {
    const handler = (e) => {
      if (
        wrapperRef.current && !wrapperRef.current.contains(e.target) &&
        dropdownRef.current && !dropdownRef.current.contains(e.target)
      ) {
        setIsOpen(false)
        setSearchText('')
        setHighlightedIndex(-1)
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  useEffect(() => {
    if (!isOpen) return
    updateDropdownPosition()
    const onScrollOrResize = () => updateDropdownPosition()
    window.addEventListener('scroll', onScrollOrResize, true)
    window.addEventListener('resize', onScrollOrResize)
    return () => {
      window.removeEventListener('scroll', onScrollOrResize, true)
      window.removeEventListener('resize', onScrollOrResize)
    }
  }, [isOpen])

  const openDropdown = () => {
    if (disabled) return
    setIsOpen(true)
    setHighlightedIndex(-1)
    updateDropdownPosition()
  }

  const handleSelect = (svc) => {
    onChange(svc.id)
    setIsOpen(false)
    setSearchText('')
    setHighlightedIndex(-1)
  }

  const handleInputChange = (e) => {
    setSearchText(e.target.value)
    if (!isOpen) setIsOpen(true)
    setHighlightedIndex(0)
  }

  const handleKeyDown = (e) => {
    if (!isOpen && (e.key === 'ArrowDown' || e.key === 'Enter')) {
      e.preventDefault()
      openDropdown()
      return
    }
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setHighlightedIndex(i => Math.min(i + 1, filteredServices.length - 1))
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setHighlightedIndex(i => Math.max(i - 1, 0))
    } else if (e.key === 'Enter') {
      e.preventDefault()
      if (highlightedIndex >= 0 && filteredServices[highlightedIndex]) {
        handleSelect(filteredServices[highlightedIndex])
      } else if (filteredServices.length === 1) {
        handleSelect(filteredServices[0])
      }
    } else if (e.key === 'Escape') {
      setIsOpen(false)
      setSearchText('')
      setHighlightedIndex(-1)
      inputRef.current?.blur()
    }
  }

  const placeholder = loadingServices
    ? 'Loading services...'
    : services.length === 0
      ? 'No services available'
      : 'Select or search a service'

  return (
    <div className="service-search-select" ref={wrapperRef}>
      <div className="service-search-input-wrapper">
        <input
          ref={inputRef}
          type="text"
          className="table-select service-search-input"
          value={displayValue}
          onChange={handleInputChange}
          onFocus={openDropdown}
          onClick={openDropdown}
          onKeyDown={handleKeyDown}
          placeholder={selectedService && !isOpen ? '' : placeholder}
          disabled={disabled}
          autoComplete="off"
        />
        <FaChevronDown
          className={`service-search-chevron ${isOpen ? 'open' : ''}`}
          onClick={(e) => {
            e.stopPropagation()
            if (isOpen) {
              setIsOpen(false)
              setSearchText('')
            } else {
              openDropdown()
              inputRef.current?.focus()
            }
          }}
        />
      </div>
      {isOpen && createPortal(
        <ul
          ref={dropdownRef}
          className="service-search-dropdown"
          style={{
            position: 'fixed',
            top: `${dropdownPos.top}px`,
            left: `${dropdownPos.left}px`,
            width: `${dropdownPos.width}px`,
          }}
        >
          {filteredServices.length === 0 ? (
            <li className="service-search-option no-match">
              {services.length === 0 ? 'No services available' : `No services match "${searchText}"`}
            </li>
          ) : (
            filteredServices.map((svc, idx) => (
              <li
                key={svc.id}
                className={`service-search-option ${svc.id === value ? 'selected' : ''} ${idx === highlightedIndex ? 'highlighted' : ''}`}
                onMouseDown={(e) => { e.preventDefault(); handleSelect(svc) }}
                onMouseEnter={() => setHighlightedIndex(idx)}
              >
                <span className="service-search-option-name">{svc.name}</span>
                <span className="service-search-option-price">₹{svc.price}</span>
              </li>
            ))
          )}
        </ul>,
        document.body
      )}
    </div>
  )
}

const QuickSale = () => {
  const { user, currentBranch } = useAuth()
  const [pendingApproval, setPendingApproval] = useState(null)
  const [showApprovalForm, setShowApprovalForm] = useState(false)
  const [approvalReason, setApprovalReason] = useState('')
  const [approvalCode, setApprovalCode] = useState('')

  const [discountType, setDiscountType] = useState('fix')
  const [paymentMode, setPaymentMode] = useState('cash')
  const [cardBank, setCardBank] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedDate, setSelectedDate] = useState(new Date())
  const [selectedCustomer, setSelectedCustomer] = useState(null)
  const [customerDetails, setCustomerDetails] = useState(null)
  const [loadingCustomerDetails, setLoadingCustomerDetails] = useState(false)
  const [bookingStatus, setBookingStatus] = useState('service-completed')
  const [bookingNote, setBookingNote] = useState('')
  const [customerDob, setCustomerDob] = useState(null)
  const [discountAmount, setDiscountAmount] = useState(0)
  const [membershipInfo, setMembershipInfo] = useState(null)
  // Offer Management integration
  const [availableOffers, setAvailableOffers] = useState([])
  const [appliedOffer, setAppliedOffer] = useState(null)
  const [showOfferModal, setShowOfferModal] = useState(false)
  // Prevents duplicate bills from rapid Checkout clicks
  const [isCheckingOut, setIsCheckingOut] = useState(false)
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
  const [loadingServices, setLoadingServices] = useState(false)
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
    dobRange: '',
    dob: '',
    referralCode: ''
  })
  const [referralInfo, setReferralInfo] = useState(null) // { enabled, rewardType, referrerReward, refereeReward }
  const [referralValidation, setReferralValidation] = useState(null) // { valid, referrerName } or null

  // Inventory modal state
  const [showInventoryModal, setShowInventoryModal] = useState(false)
  const [selectedServiceForInventory, setSelectedServiceForInventory] = useState(null)
  const [serviceRelatedProducts, setServiceRelatedProducts] = useState([])

  // Bill Activity modal state
  const [showBillActivityModal, setShowBillActivityModal] = useState(false)
  const [customerBills, setCustomerBills] = useState([])
  const [loadingBills, setLoadingBills] = useState(false)

  // Add Package/Product/Membership modal states
  const [showPackageModal, setShowPackageModal] = useState(false)
  const [showProductModal, setShowProductModal] = useState(false)
  const [showMembershipModal, setShowMembershipModal] = useState(false)
  const [productQuantities, setProductQuantities] = useState({}) // Map product ID to quantity

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
  const [memberships, setMemberships] = useState([])
  // Tax configuration from Tax Settings
  const [taxSettings, setTaxSettings] = useState({
    gstNumber: '',
    servicePricingType: 'inclusive',
    productPricingType: 'exclusive'
  })
  const [serviceTaxRate, setServiceTaxRate] = useState(0)
  const [productTaxRate, setProductTaxRate] = useState(0)
  const [availablePackages, setAvailablePackages] = useState([])
  const [availableProducts, setAvailableProducts] = useState([])
  const [availableMemberships, setAvailableMemberships] = useState([])

  // State for editing appointment
  const [editingAppointmentId, setEditingAppointmentId] = useState(null)

  // State for invoice modal
  const [showInvoiceModal, setShowInvoiceModal] = useState(false)
  const [invoiceData, setInvoiceData] = useState(null)
  const [currentBillId, setCurrentBillId] = useState(null)
  const [loadingInvoice, setLoadingInvoice] = useState(false)

  // Fetch essential data on component mount
  // Packages, products, and memberships are fetched on-demand when needed
  useEffect(() => {
    fetchCustomers()
    fetchStaff()
    fetchServices()
    fetchTaxConfig()
    fetchReferralSettings()
    fetchActiveOffers()
  }, [currentBranch])

  // Fetch currently-valid offers for the selected branch
  const fetchActiveOffers = async () => {
    try {
      const response = await apiGet('/api/offers/active')
      if (response.ok) {
        const data = await response.json()
        setAvailableOffers(data.offers || [])
      } else {
        setAvailableOffers([])
      }
    } catch (error) {
      console.error('Error fetching active offers:', error)
      setAvailableOffers([])
    }
  }

  // Auto-select logged-in staff when staff members are loaded
  useEffect(() => {
    if (staffMembers.length > 0 && user && user.id) {
      // Check if user is a staff member (not manager/owner accessing the system)
      const loggedInStaff = staffMembers.find(s => s.id === user.id)
      if (loggedInStaff) {
        // Auto-select this staff for existing services that don't have staff selected
        setServices(prevServices =>
          prevServices.map(service => ({
            ...service,
            staff_id: service.staff_id || user.id
          }))
        )
      }
    }
  }, [staffMembers, user])

  // Pre-fill appointment data immediately from localStorage (no waiting for data arrays)
  useEffect(() => {
    // Only proceed if we have appointment data to pre-fill
    const editAppointmentData = localStorage.getItem('edit_appointment_data')
    if (!editAppointmentData) return

    try {
      const appointmentData = JSON.parse(editAppointmentData)
      console.log('[APPOINTMENT EDIT] Loading appointment data immediately:', appointmentData)
      
      // Set editing appointment ID immediately
      setEditingAppointmentId(appointmentData.appointmentId)
      
      // Pre-fill the form with appointment data immediately
      prefillAppointmentData(appointmentData)
      
      // Clear the data after reading
      localStorage.removeItem('edit_appointment_data')
    } catch (error) {
      console.error('Error parsing appointment data:', error)
      localStorage.removeItem('edit_appointment_data')
    }
  }, []) // Run only once on mount, no dependencies

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

  // Reset card bank when payment mode changes away from card
  useEffect(() => {
    if (paymentMode !== 'card') {
      setCardBank('')
    }
  }, [paymentMode])

  // Pre-fill form with appointment data - immediate population with parallel API calls
  const prefillAppointmentData = async (appointmentData) => {
    try {
      console.log('[APPOINTMENT EDIT] Pre-filling appointment data:', appointmentData)
      
      // IMMEDIATE STATE UPDATES - No waiting for API calls
      // Set date immediately
      if (appointmentData.appointment_date) {
        setSelectedDate(new Date(appointmentData.appointment_date))
      }

      // Set booking status immediately
      if (appointmentData.status) {
        setBookingStatus(appointmentData.status === 'confirmed' ? 'confirmed' : 'service-completed')
      }

      // Set booking note immediately (from appointment or bill)
      if (appointmentData.booking_note) {
        setBookingNote(appointmentData.booking_note || '')
      } else if (appointmentData.notes) {
        setBookingNote(appointmentData.notes || '')
      }

      // Set payment mode from bill data
      if (appointmentData.payment_mode) {
        setPaymentMode(appointmentData.payment_mode)
        console.log('[APPOINTMENT EDIT] Payment mode set:', appointmentData.payment_mode)
      }

      // Set discount from bill data
      if (appointmentData.discount_amount !== undefined) {
        setDiscountAmount(appointmentData.discount_amount || 0)
      }
      if (appointmentData.discount_type) {
        setDiscountType(appointmentData.discount_type)
      }

      // Create and set customer object immediately from appointment data
      if (appointmentData.customer_id) {
        // Parse customer name to extract first and last name
        const customerNameParts = (appointmentData.customer_name || '').trim().split(' ')
        const firstName = customerNameParts[0] || ''
        const lastName = customerNameParts.slice(1).join(' ') || ''
        
        const customer = {
          id: appointmentData.customer_id,
          mobile: appointmentData.customer_mobile || '',
          firstName: firstName,
          lastName: lastName,
          email: ''
        }
        
        // Set customer immediately
        setSelectedCustomer(customer)
        setSearchQuery(`${firstName} ${lastName} - ${customer.mobile}`.trim())
        setShowCustomerDropdown(false)
        console.log('[APPOINTMENT EDIT] Customer set immediately:', customer)
      }

      // Process bill items if available (preferred over single service from appointment)
      if (appointmentData.bill_items && appointmentData.bill_items.length > 0) {
        console.log('[APPOINTMENT EDIT] Processing bill items:', appointmentData.bill_items)

        // Process services from bill items
        const serviceItems = appointmentData.bill_items.filter(item => item.item_type === 'service')
        if (serviceItems.length > 0) {
          const servicesFromBill = serviceItems.map((item, index) => {
            let timeStr = item.start_time || appointmentData.start_time || ''
            if (timeStr && timeStr.includes(':')) {
              const parts = timeStr.split(':')
              timeStr = `${parts[0]}:${parts[1]}`
            }
            return {
              id: index + 1,
              service_id: item.service_id,
              staff_id: item.staff_id,
              startTime: timeStr,
              price: item.price || 0,
              discount: item.discount || 0,
              total: item.total || item.price || 0,
            }
          })
          setServices(servicesFromBill)
          console.log('[APPOINTMENT EDIT] Services from bill:', servicesFromBill)
        }

        // Process packages from bill items
        const packageItems = appointmentData.bill_items.filter(item => item.item_type === 'package')
        if (packageItems.length > 0) {
          const packagesFromBill = packageItems.map((item, index) => ({
            id: index + 1,
            package_id: item.package_id,
            name: item.name || '',
            price: item.price || 0,
            discount: item.discount || 0,
            total: item.total || item.price || 0,
          }))
          setPackages(packagesFromBill)
          console.log('[APPOINTMENT EDIT] Packages from bill:', packagesFromBill)
        }

        // Process products from bill items
        const productItems = appointmentData.bill_items.filter(item => item.item_type === 'product')
        if (productItems.length > 0) {
          const productsFromBill = productItems.map((item, index) => ({
            id: index + 1,
            product_id: item.product_id,
            name: item.name || '',
            price: item.price || 0,
            discount: item.discount || 0,
            quantity: item.quantity || 1,
            total: item.total || item.price || 0,
          }))
          setProducts(productsFromBill)
          console.log('[APPOINTMENT EDIT] Products from bill:', productsFromBill)
        }

        // Process memberships from bill items
        const membershipItems = appointmentData.bill_items.filter(item => item.item_type === 'membership')
        if (membershipItems.length > 0) {
          const membershipsFromBill = membershipItems.map((item, index) => ({
            id: index + 1,
            membership_id: item.membership_id,
            name: item.name || '',
            price: item.price || 0,
          }))
          setMemberships(membershipsFromBill)
          console.log('[APPOINTMENT EDIT] Memberships from bill:', membershipsFromBill)
        }
      } else if (appointmentData.service_id && appointmentData.staff_id && appointmentData.start_time) {
        // Fallback: Create and set service entry from basic appointment data
        // Format time (remove seconds if present, keep HH:MM format)
        let timeStr = appointmentData.start_time
        if (timeStr && timeStr.includes(':')) {
          const parts = timeStr.split(':')
          timeStr = `${parts[0]}:${parts[1]}`
        }

        // Set service immediately with data from appointment
        setServices([{
          id: 1,
          service_id: appointmentData.service_id,
          staff_id: appointmentData.staff_id,
          startTime: timeStr,
          price: appointmentData.service_price || 0,
          discount: 0,
          total: appointmentData.service_price || 0,
        }])
        console.log('[APPOINTMENT EDIT] Service set from appointment (no bill):', {
          service_id: appointmentData.service_id,
          staff_id: appointmentData.staff_id,
          startTime: timeStr,
          price: appointmentData.service_price || 0
        })
      }

      // PARALLEL API CALLS - Fetch missing details in background (non-blocking)
      const apiPromises = []
      
      // Fetch customer details if not in loaded array
      if (appointmentData.customer_id) {
        const customerInArray = customers.find(c => c.id === appointmentData.customer_id)
        if (!customerInArray) {
          apiPromises.push(
            apiGet(`/api/customers/${appointmentData.customer_id}`)
              .then(response => {
                if (response.ok) {
                  return response.json().then(customerData => {
                    // Update customer if needed (customer details will be fetched via useEffect)
                    console.log('[APPOINTMENT EDIT] Customer details fetched:', customerData)
                  })
                }
              })
              .catch(error => console.error('[APPOINTMENT EDIT] Error fetching customer:', error))
          )
        }
      }

      // Fetch service details if not in loaded array
      if (appointmentData.service_id) {
        const serviceInArray = availableServices.find(s => s.id === appointmentData.service_id)
        if (!serviceInArray) {
          apiPromises.push(
            apiGet('/api/services')
              .then(response => {
                if (response.ok) {
                  return response.json().then(data => {
                    const service = (data.services || []).find(s => s.id === appointmentData.service_id)
                    if (service) {
                      // Update service price if available
                      setServices(prev => prev.map(s => 
                        s.service_id === appointmentData.service_id
                          ? { ...s, price: service.price || s.price, total: service.price || s.total }
                          : s
                      ))
                      console.log('[APPOINTMENT EDIT] Service details fetched:', service)
                    }
                  })
                }
              })
              .catch(error => console.error('[APPOINTMENT EDIT] Error fetching service:', error))
          )
        }
      }

      // Fetch staff details if not in loaded array (optional, for validation)
      if (appointmentData.staff_id) {
        const staffInArray = staffMembers.find(s => s.id === appointmentData.staff_id)
        if (!staffInArray) {
          apiPromises.push(
            apiGet('/api/staffs')
              .then(response => {
                if (response.ok) {
                  return response.json().then(data => {
                    const staff = (data.staffs || []).find(s => s.id === appointmentData.staff_id)
                    if (staff) {
                      console.log('[APPOINTMENT EDIT] Staff details fetched:', staff)
                    }
                  })
                }
              })
              .catch(error => console.error('[APPOINTMENT EDIT] Error fetching staff:', error))
          )
        }
      }

      // Wait for all API calls to complete, then show success message
      Promise.all(apiPromises)
        .then(() => {
          // Show success message after UI updates are visible
          setTimeout(() => {
            showInfo('Appointment data loaded. You can now edit and update the booking.')
            console.log('[APPOINTMENT EDIT] All data loaded successfully')
          }, 100)
        })
        .catch(error => {
          console.error('[APPOINTMENT EDIT] Error in parallel API calls:', error)
          // Still show success since form is already populated
          setTimeout(() => {
            showInfo('Appointment data loaded. You can now edit and update the booking.')
          }, 100)
        })

      // If no API calls needed, show success immediately
      if (apiPromises.length === 0) {
        setTimeout(() => {
          showInfo('Appointment data loaded. You can now edit and update the booking.')
          console.log('[APPOINTMENT EDIT] Data loaded immediately (no API calls needed)')
        }, 100)
      }

    } catch (error) {
      console.error('[APPOINTMENT EDIT] Error pre-filling appointment data:', error)
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
      fetchTaxConfig()
      // Reset deferred data so it re-fetches on next use
      setAvailablePackages([])
      setAvailableProducts([])
      setAvailableMemberships([])
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

  // Fetch initial customers for dropdown (when search is empty)
  const fetchCustomersForDropdown = async () => {
    try {
      const response = await apiGet(`/api/customers?per_page=10`)
      const data = await response.json()
      const customersList = (data.customers || []).map(customer => ({
        id: customer.id,
        mobile: customer.mobile || '',
        firstName: customer.firstName || customer.first_name || '',
        lastName: customer.lastName || customer.last_name || '',
        email: customer.email || ''
      }))
      setFilteredCustomers(customersList)
    } catch (error) {
      console.error('Error fetching customers for dropdown:', error)
      setFilteredCustomers([])
    }
  }

  // Search customers using server-side API (with debouncing)
  useEffect(() => {
    let searchTimeout
    const searchCustomers = async () => {
      try {
        const params = new URLSearchParams({
          per_page: '50', // Limit results for dropdown
        })
        if (searchQuery && searchQuery.trim().length > 0) {
          params.append('search', searchQuery.trim())
        }
        
        const response = await apiGet(`/api/customers?${params}`)
        const data = await response.json()
        
        // Map the response to match the expected format (handle both camelCase and snake_case)
        const customersList = (data.customers || []).map(customer => ({
          id: customer.id,
          mobile: customer.mobile || '',
          firstName: customer.firstName || customer.first_name || '',
          lastName: customer.lastName || customer.last_name || '',
          email: customer.email || ''
        }))
        
        setFilteredCustomers(customersList)
        setShowCustomerDropdown(true)
      } catch (error) {
        console.error('Error searching customers:', error)
        setFilteredCustomers([])
      }
    }

    if (searchQuery && searchQuery.trim().length > 0) {
      // Debounce search: wait 300ms after user stops typing
      searchTimeout = setTimeout(() => {
        searchCustomers()
      }, 300)
    } else {
      // When search is empty, show first 10 customers
      fetchCustomersForDropdown()
    }

    return () => {
      if (searchTimeout) {
        clearTimeout(searchTimeout)
      }
    }
  }, [searchQuery])

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
      // Request the largest page size the backend allows (max=100) so the full
      // staff roster lands in one call — otherwise pagination can silently hide
      // staff from the dropdown.
      const response = await apiGet(`/api/staffs?per_page=100`)
      const data = await response.json()
      const list = data.staffs || []
      if (!list.length) {
        console.warn('[QuickSale] fetchStaff returned 0 staff — check branch filter or data')
      }
      setStaffMembers(list)
    } catch (error) {
      console.error('Error fetching staff:', error)
    }
  }

  const fetchTaxConfig = async () => {
    try {
      const [settingsRes, slabsRes] = await Promise.all([
        apiGet('/api/tax/settings'),
        apiGet('/api/tax/slabs?status=active')
      ])

      if (settingsRes.ok) {
        const settings = await settingsRes.json()
        setTaxSettings({
          gstNumber: settings.gstNumber || '',
          servicePricingType: settings.servicePricingType || 'inclusive',
          productPricingType: settings.productPricingType || 'exclusive'
        })
      }

      if (slabsRes.ok) {
        const data = await slabsRes.json()
        const slabs = data.slabs || []
        setServiceTaxRate(slabs.reduce((sum, s) => s.applyToServices ? sum + (s.rate || 0) : sum, 0))
        setProductTaxRate(slabs.reduce((sum, s) => s.applyToProducts ? sum + (s.rate || 0) : sum, 0))
      }
    } catch (error) {
      console.error('Error fetching tax config:', error)
    }
  }

  const fetchReferralSettings = async () => {
    try {
      const response = await apiGet('/api/referral-program/settings')
      if (response.ok) {
        const data = await response.json()
        setReferralInfo({
          enabled: data.enabled || false,
          rewardType: data.rewardType || 'percentage',
          referrerReward: data.referrerRewardPercentage || 0,
          refereeReward: data.refereeRewardPercentage || 0
        })
      }
    } catch (error) {
      console.error('Error fetching referral settings:', error)
    }
  }

  const validateReferralCode = async (code) => {
    if (!code || !code.trim()) {
      setReferralValidation(null)
      return
    }
    try {
      const response = await apiGet(`/api/referral-program/validate-code?code=${encodeURIComponent(code.trim())}`)
      const data = await response.json()
      if (response.ok && data.valid) {
        setReferralValidation({ valid: true, referrerName: data.referrerName })
      } else {
        setReferralValidation({ valid: false, error: data.error || 'Invalid code' })
      }
    } catch (error) {
      setReferralValidation({ valid: false, error: 'Could not validate code' })
    }
  }

  const fetchServices = async (retryCount = 0) => {
    setLoadingServices(true)
    try {
      // Request all services by using a high per_page limit
      const response = await apiGet('/api/services?per_page=1000')
      if (!response.ok) {
        // Handle specific error codes
        if (response.status === 401) {
          throw new Error('Authentication failed. Please log in again.')
        } else if (response.status === 403) {
          throw new Error('You do not have permission to view services.')
        } else if (response.status >= 500) {
          throw new Error('Server error. Please try again later.')
        } else {
          throw new Error(`Failed to load services (${response.status}). Please try again.`)
        }
      }
      const data = await response.json()
      
      // Handle both response formats: backend returns 'data' array, legacy format uses 'services'
      let services = []
      if (data.data && Array.isArray(data.data)) {
        // Backend format: { data: [...], pagination: {...} }
        services = data.data
      } else if (data.services && Array.isArray(data.services)) {
        // Legacy format: { services: [...] }
        services = data.services
      } else if (Array.isArray(data)) {
        // Direct array format
        services = data
      }
      
      setAvailableServices(services)
      console.log('[QuickSale] Services loaded:', services.length)
      
      if (services.length === 0) {
        console.warn('[QuickSale] No services found. Check if services exist in the database.')
        showInfo('No services available. Please add services in the Service management section.')
      }
    } catch (error) {
      console.error('Error fetching services:', error)
      
      // Retry logic for network errors (max 2 retries)
      if (retryCount < 2 && (error.message.includes('Failed to fetch') || error.message.includes('Network'))) {
        console.log(`[QuickSale] Retrying service fetch (attempt ${retryCount + 1}/2)...`)
        setTimeout(() => {
          fetchServices(retryCount + 1)
        }, 1000 * (retryCount + 1)) // Exponential backoff: 1s, 2s
        return
      }
      
      setAvailableServices([])
      const errorMessage = error.message || 'Failed to load services. Please refresh the page or check your connection.'
      showError(errorMessage)
    } finally {
      setLoadingServices(false)
    }
  }

  const fetchPackages = async () => {
    try {
      console.log('[QuickSale] Fetching packages...')
      const response = await apiGet('/api/packages')
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      const responseData = await response.json()
      console.log('[QuickSale] Packages API response:', responseData)
      
      // Backend returns {data: [...], pagination: {...}}
      const packagesList = responseData.data || (Array.isArray(responseData) ? responseData : (responseData.packages || []))
      setAvailablePackages(packagesList)
      console.log('[QuickSale] Packages loaded:', packagesList.length, 'Branch:', currentBranch?.name || 'Not set')
      
      if (packagesList.length === 0) {
        console.warn('[QuickSale] No packages found. Check:')
        console.warn('  - Branch filtering (current branch:', currentBranch?.id || 'Not set', ')')
        console.warn('  - Package status (should be "active")')
        console.warn('  - X-Branch-Id header in request')
      }
    } catch (error) {
      console.error('[QuickSale] Error fetching packages:', error)
      setAvailablePackages([])
    }
  }

  const fetchProducts = async () => {
    try {
      console.log('[QuickSale] Fetching products...')
      const response = await apiGet('/api/products')
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      const responseData = await response.json()
      console.log('[QuickSale] Products API response:', responseData)
      
      // Backend returns {data: [...], pagination: {...}}
      const productsList = responseData.data || (Array.isArray(responseData) ? responseData : (responseData.products || []))
      setAvailableProducts(productsList)
      console.log('[QuickSale] Products loaded:', productsList.length, 'Branch:', currentBranch?.name || 'Not set')

      if (productsList.length === 0) {
        console.warn('[QuickSale] No products found. Check:')
        console.warn('  - Branch filtering (current branch:', currentBranch?.id || 'Not set', ')')
        console.warn('  - Product status (should be "active")')
        console.warn('  - X-Branch-Id header in request')
      }
      return productsList
    } catch (error) {
      console.error('[QuickSale] Error fetching products:', error)
      setAvailableProducts([])
      return []
    }
  }

  const fetchMembershipPlans = async () => {
    try {
      const response = await apiGet('/api/membership-plans?status=active')
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
    // Auto-select logged-in staff if they are in the staff list
    const loggedInStaffId = (user && staffMembers.find(s => s.id === user.id)) ? user.id : ''
    setServices([
      ...services,
      {
        id: Date.now(),
        service_id: '',
        staff_id: loggedInStaffId,
        startTime: currentTime,
        price: 0,
        discount: 0,
        total: 0,
      },
    ])
  }

  const addPackage = async () => {
    if (!selectedCustomer) {
      showWarning('Please select a customer first')
      return
    }
    if (availablePackages.length === 0) {
      await fetchPackages()
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

  const addProduct = async () => {
    if (!selectedCustomer) {
      showWarning('Please select a customer first')
      return
    }
    let products = availableProducts
    if (products.length === 0) {
      products = await fetchProducts()
    }
    // Initialize quantities for all products to 1 when opening modal
    const initialQuantities = {}
    products.forEach(product => {
      initialQuantities[product.id] = 1
    })
    setProductQuantities(initialQuantities)
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
    
    // Add to local state (stock will only be decremented during checkout)
    setProducts([...products, {
      id: Date.now(),
      product_id: selectedProduct.id,
      name: selectedProduct.name,
      price: selectedProduct.price,
      quantity: quantity,
      discount: 0,
      total: selectedProduct.price * quantity,
    }])
    
    setShowProductModal(false)
    // Reset quantity for this product after adding
    setProductQuantities(prev => ({
      ...prev,
      [selectedProduct.id]: 1
    }))
    showSuccess(`${selectedProduct.name} (x${quantity}) added to bill`)
    
    // Note: Stock will be updated by backend during checkout, not here
  }

  const addMembership = async () => {
    if (!selectedCustomer) {
      showWarning('Please select a customer first')
      return
    }
    if (memberships.length > 0) {
      showWarning('Only one membership plan can be added per bill. Remove the existing one first.')
      return
    }
    // If the customer already has an active plan, confirm upgrade/replacement.
    // Backend will expire the old membership when the new one is checked out.
    if (membershipInfo && membershipInfo.plan) {
      const ok = window.confirm(
        `${membershipInfo.plan.name} (${membershipInfo.plan.allocated_discount}%) is already active for this customer.\n\n` +
        `Their discount is being applied automatically — you do NOT need to add a plan here to redeem benefits.\n\n` +
        `Selecting a new plan will REPLACE ${membershipInfo.plan.name} at checkout.\n\n` +
        `Continue only if you want to upgrade or renew. Otherwise click Cancel.`
      )
      if (!ok) return
    }
    await fetchMembershipPlans()
    setShowMembershipModal(true)
  }

  const handleSelectMembership = (selectedMembership) => {
    if (memberships.length > 0) {
      showWarning('Only one membership plan can be added per bill.')
      setShowMembershipModal(false)
      return
    }
    const planDiscount = parseFloat(
      selectedMembership.allocated_discount ?? selectedMembership.allocatedDiscount ?? 0
    ) || 0
    // Capture the plan's whitelist of services it covers. Without this the cart
    // entry's `applicable_service_ids` is undefined, which `getMembershipCoverageForService`
    // treats as "covers all" — making the per-service discount logic apply to
    // every line, even ones the plan doesn't actually cover.
    const applicableServices = Array.isArray(selectedMembership.applicable_services)
      ? selectedMembership.applicable_services
      : []
    const applicableServiceIds = applicableServices
      .map(s => (s && (s.id || s)) || null)
      .filter(Boolean)
    setMemberships([{
      id: Date.now(),
      membership_id: selectedMembership.id,
      name: selectedMembership.name,
      price: selectedMembership.price,
      validity: selectedMembership.validity_days,
      allocated_discount: planDiscount,
      applicable_service_ids: applicableServiceIds,
    }])
    setShowMembershipModal(false)
    // Auto-enable the membership discount toggle so the discount applies
    // immediately on this bill. Staff can untick it from Bill Summary if
    // they want to opt out for this transaction.
    if (planDiscount > 0 && discountType !== 'membership') {
      setDiscountType('membership')
      setDiscountAmount(0)
    }
    if (planDiscount > 0) {
      showSuccess(`${selectedMembership.name} added — ${planDiscount}% discount applied to covered services`)
    } else {
      showSuccess(`${selectedMembership.name} added to bill`)
    }
  }

  const removePackage = (id) => {
    setPackages(packages.filter(p => p.id !== id))
  }

  const removeProduct = (id) => {
    setProducts(products.filter(p => p.id !== id))
  }

  const removeMembership = (id) => {
    setMemberships(memberships.filter(m => m.id !== id))
    // Cart memberships no longer drive the discount, so removing one never
    // toggles discountType. The discount path is governed solely by whether
    // the customer has an existing active membership (set in checkCustomerMembership).
  }

  const removeService = (id) => {
    if (services.length > 1) {
      setServices(services.filter((s) => s.id !== id))
    }
  }

  // Add minutes to a "HH:MM" time string, wrapping at midnight
  const addMinutesToTime = (timeStr, minutes) => {
    const parts = (timeStr || '00:00').split(':').map(Number)
    const totalMins = parts[0] * 60 + (parts[1] || 0) + minutes
    const h = Math.floor(totalMins / 60) % 24
    const m = totalMins % 60
    return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`
  }

  const updateService = (id, field, value) => {
    // When the FIRST service's start time changes, cascade to all subsequent services
    if (field === 'startTime' && services.length > 1 && services[0]?.id === id) {
      let cursor = String(value).trim()
      const updated = services.map((s) => {
        const updatedS = { ...s }
        updatedS.startTime = cursor
        const price = parseFloat(updatedS.price) || 0
        const discount = parseFloat(updatedS.discount) || 0
        updatedS.total = price - (price * discount / 100)
        // Advance cursor by this service's duration for the next service
        cursor = addMinutesToTime(cursor, parseInt(s.duration) || 30)
        return updatedS
      })
      setServices(updated)
      return
    }

    const updated = services.map((s) => {
      if (s.id === id) {
        const updatedService = { ...s, [field]: value }

        // Auto-fill price and duration when service is selected
        if (field === 'service_id' && value) {
          const selectedService = availableServices.find(service => service.id === value)
          if (selectedService) {
            updatedService.price = selectedService.price
            updatedService.duration = parseInt(selectedService.duration) || 30
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
    // Reset previously selected offer — eligibility may differ for the new customer
    setAppliedOffer(null)
    // Customer details and membership will be fetched in background via useEffect
  }

  // Check customer's active membership
  const checkCustomerMembership = async (customerId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/customers/${customerId}/active-membership`, {
        headers: {
          'Authorization': `Bearer ${sessionStorage.getItem('auth_token')}`
        }
      })
      
      if (!response.ok) {
        throw new Error('Failed to fetch membership')
      }
      
      const data = await response.json()
      
      if (data.active && data.membership && data.membership.plan) {
        // Customer has an active membership — auto-tick the membership discount
        // toggle so the discount applies immediately on this bill. Staff can
        // untick it from Bill Summary if they need to opt out for a particular
        // transaction. This removes the "staff forgot to tick the box → invoice
        // shows ₹0 discount" failure mode.
        setMembershipInfo(data.membership)
        const planPct = parseFloat(data.membership.plan.allocated_discount) || 0
        if (planPct > 0) {
          setDiscountType('membership')
          setDiscountAmount(0)
        }
        showInfo(
          `${data.membership.plan.name} member — ${data.membership.plan.allocated_discount}% discount auto-applied to covered services`
        )
      } else {
        // No active membership
        setMembershipInfo(null)
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
        console.log('[APPOINTMENT UPDATE] Sending request:', {
          appointment_id: editingAppointmentId,
          customer_id: selectedCustomer.id,
          staff_id: firstService.staff_id,
          service_id: firstService.service_id,
          appointment_date: appointmentDate,
          start_time: startTime,
          status: 'confirmed',
          notes: bookingNote || undefined
        })

        const updateResponse = await apiPut(`/api/appointments/${editingAppointmentId}`, {
          customer_id: selectedCustomer.id,
          staff_id: firstService.staff_id,
          service_id: firstService.service_id,
          appointment_date: appointmentDate,
          start_time: startTime,
          status: 'confirmed',
          notes: bookingNote || undefined
        })

        console.log('[APPOINTMENT UPDATE] Response status:', updateResponse.status, updateResponse.ok)

        if (!updateResponse.ok) {
          const errorData = await updateResponse.json().catch(() => ({ error: 'Failed to update appointment' }))
          console.error('[APPOINTMENT UPDATE] Error response:', errorData)
          showError(errorData.error || 'Failed to update appointment')
          return false
        }

        const updateData = await updateResponse.json().catch(() => ({}))
        console.log('[APPOINTMENT UPDATE] Response data:', updateData)
        console.log('[APPOINTMENT UPDATE] Success: Appointment updated with ID', editingAppointmentId)

        // Update or create the Bill linked to this appointment
        await updateBillForAppointment(editingAppointmentId, appointmentDate)

        showSuccess('Booking updated! Appointment saved to Upcoming Appointments.')
        return true
      }

      // Create new appointment
      console.log('[APPOINTMENT CREATE] Sending request:', {
        customer_id: selectedCustomer.id,
        staff_id: firstService.staff_id,
        service_id: firstService.service_id,
        appointment_date: appointmentDate,
        start_time: startTime,
        status: 'confirmed',
        notes: bookingNote || undefined
      })

      const response = await apiPost('/api/appointments', {
        customer_id: selectedCustomer.id,
        staff_id: firstService.staff_id,
        service_id: firstService.service_id,
        appointment_date: appointmentDate,
        start_time: startTime,
        status: 'confirmed',
        notes: bookingNote || undefined
      })

      console.log('[APPOINTMENT CREATE] Response status:', response.status, response.ok)

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: 'Failed to create appointment' }))
        console.error('[APPOINTMENT CREATE] Error response:', errorData)
        showError(errorData.error || 'Failed to create appointment')
        return false
      }

      // Verify response status is 201 (Created)
      if (response.status !== 201) {
        console.warn('[APPOINTMENT CREATE] Unexpected status code:', response.status)
      }

      const data = await response.json()
      console.log('[APPOINTMENT CREATE] Response data:', data)

      // Verify response data contains appointment ID before showing success
      if (!data || !data.id) {
        console.error('[APPOINTMENT CREATE] Failed: No appointment ID in response', data)
        showError('Failed to create appointment: Invalid response from server')
        return false
      }

      // Create a Bill linked to this appointment to store all items and payment_mode
      const appointmentId = data.id
      await createBillForAppointment(appointmentId, appointmentDate)

      // Only show success if we have a valid appointment ID
      showSuccess('Booking confirmed! Appointment saved to Upcoming Appointments.')
      console.log('[APPOINTMENT CREATE] Success: Appointment created with ID', data.id)
      return true
    } catch (error) {
      console.error('Error creating appointment:', error)
      showError(`Error creating appointment: ${error.message || 'Unknown error'}`)
      return false
    }
  }

  // Helper function to create a Bill linked to an appointment with all items
  const createBillForAppointment = async (appointmentId, billDate) => {
    try {
      console.log('[BILL CREATE FOR APPOINTMENT] Creating bill for appointment:', appointmentId)

      // Create bill with confirmed status linked to appointment
      const billPayload = {
        customer_id: selectedCustomer.id,
        bill_date: billDate,
        booking_status: 'confirmed',
        booking_note: bookingNote,
        appointment_id: appointmentId,
        payment_mode: paymentMode,
      }

      const billResponse = await apiPost('/api/bills', billPayload)

      if (!billResponse.ok) {
        console.error('[BILL CREATE FOR APPOINTMENT] Failed to create bill')
        return // Don't fail the whole operation, appointment was already created
      }

      const billData = await billResponse.json()
      const billId = billData.data.id
      console.log('[BILL CREATE FOR APPOINTMENT] Bill created with ID:', billId)

      // Add all items to bill
      const validServices = services.filter(s => s.service_id && s.price > 0)

      // Add services
      for (const service of validServices) {
        await apiPost(`/api/bills/${billId}/items`, {
          item_type: 'service',
          service_id: service.service_id,
          staff_id: service.staff_id || null,
          start_time: service.startTime ? `${service.startTime}:00` : null,
          price: parseFloat(service.price) || 0,
          discount: parseFloat(service.discount) || 0,
          quantity: 1,
          total: parseFloat(service.total) || parseFloat(service.price) || 0,
        })
      }

      // Add packages
      for (const pkg of packages) {
        if (pkg.package_id) {
          await apiPost(`/api/bills/${billId}/items`, {
            item_type: 'package',
            package_id: pkg.package_id,
            price: parseFloat(pkg.price) || 0,
            discount: parseFloat(pkg.discount) || 0,
            quantity: 1,
            total: parseFloat(pkg.total) || parseFloat(pkg.price) || 0,
          })
        }
      }

      // Add products
      for (const product of products) {
        if (product.product_id) {
          await apiPost(`/api/bills/${billId}/items`, {
            item_type: 'product',
            product_id: product.product_id,
            price: parseFloat(product.price) || 0,
            discount: parseFloat(product.discount) || 0,
            quantity: parseInt(product.quantity) || 1,
            total: parseFloat(product.total) || parseFloat(product.price) * (parseInt(product.quantity) || 1) || 0,
          })
        }
      }

      // Add memberships
      for (const membership of memberships) {
        if (membership.membership_id) {
          await apiPost(`/api/bills/${billId}/items`, {
            item_type: 'membership',
            membership_id: membership.membership_id,
            name: membership.name || '',
            price: parseFloat(membership.price) || 0,
            discount: 0,
            quantity: 1,
            total: parseFloat(membership.price) || 0,
          })
        }
      }

      // Finalize bill
      await apiPut(`/api/bills/${billId}`, {
        payment_mode: paymentMode,
        discount_amount: discountAmount,
        discount_type: discountType,
      })

      console.log('[BILL CREATE FOR APPOINTMENT] Bill finalized with all items')
    } catch (error) {
      console.error('[BILL CREATE FOR APPOINTMENT] Error creating bill:', error)
      // Don't fail the whole operation, appointment was already created
    }
  }

  // Helper function to update or create Bill for an existing appointment
  const updateBillForAppointment = async (appointmentId, billDate) => {
    try {
      console.log('[BILL UPDATE FOR APPOINTMENT] Updating bill for appointment:', appointmentId)

      // First, try to find existing bill for this appointment
      const searchResponse = await apiGet(`/api/bills?appointment_id=${appointmentId}`)
      let billId = null

      if (searchResponse.ok) {
        const searchData = await searchResponse.json()
        if (searchData.data && searchData.data.length > 0) {
          billId = searchData.data[0].id
          console.log('[BILL UPDATE FOR APPOINTMENT] Found existing bill:', billId)

          // Delete existing items from the bill before adding new ones
          // We'll update the bill with new items
        }
      }

      if (!billId) {
        // No existing bill found, create a new one
        console.log('[BILL UPDATE FOR APPOINTMENT] No existing bill found, creating new one')
        await createBillForAppointment(appointmentId, billDate)
        return
      }

      // Update existing bill - first clear items, then add new ones
      const validServices = services.filter(s => s.service_id && s.price > 0)

      // Add services
      for (const service of validServices) {
        await apiPost(`/api/bills/${billId}/items`, {
          item_type: 'service',
          service_id: service.service_id,
          staff_id: service.staff_id || null,
          start_time: service.startTime ? `${service.startTime}:00` : null,
          price: parseFloat(service.price) || 0,
          discount: parseFloat(service.discount) || 0,
          quantity: 1,
          total: parseFloat(service.total) || parseFloat(service.price) || 0,
        })
      }

      // Add packages
      for (const pkg of packages) {
        if (pkg.package_id) {
          await apiPost(`/api/bills/${billId}/items`, {
            item_type: 'package',
            package_id: pkg.package_id,
            price: parseFloat(pkg.price) || 0,
            discount: parseFloat(pkg.discount) || 0,
            quantity: 1,
            total: parseFloat(pkg.total) || parseFloat(pkg.price) || 0,
          })
        }
      }

      // Add products
      for (const product of products) {
        if (product.product_id) {
          await apiPost(`/api/bills/${billId}/items`, {
            item_type: 'product',
            product_id: product.product_id,
            price: parseFloat(product.price) || 0,
            discount: parseFloat(product.discount) || 0,
            quantity: parseInt(product.quantity) || 1,
            total: parseFloat(product.total) || parseFloat(product.price) * (parseInt(product.quantity) || 1) || 0,
          })
        }
      }

      // Add memberships
      for (const membership of memberships) {
        if (membership.membership_id) {
          await apiPost(`/api/bills/${billId}/items`, {
            item_type: 'membership',
            membership_id: membership.membership_id,
            name: membership.name || '',
            price: parseFloat(membership.price) || 0,
            discount: 0,
            quantity: 1,
            total: parseFloat(membership.price) || 0,
          })
        }
      }

      // Update bill with payment_mode and discount
      await apiPut(`/api/bills/${billId}`, {
        payment_mode: paymentMode,
        discount_amount: discountAmount,
        discount_type: discountType,
        booking_note: bookingNote,
      })

      console.log('[BILL UPDATE FOR APPOINTMENT] Bill updated with all items')
    } catch (error) {
      console.error('[BILL UPDATE FOR APPOINTMENT] Error updating bill:', error)
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
        lastService: data.last_service || 'N/A',
        dob: data.dob || null,
        notes: data.notes || 'N/A',
        referredBy: data.referredBy || null,
        referralRewardUsed: data.referralRewardUsed || false
      })
      setCustomerDob(data.dob ? new Date(data.dob) : null)
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
      fetchCustomersForDropdown()
      setShowCustomerDropdown(true)
      return
    }
    
    // If no customer is selected, show dropdown
    if (searchQuery && searchQuery.trim().length > 0) {
      // If there's a search query, it will be handled by the useEffect
      setShowCustomerDropdown(true)
    } else {
      // Show first 10 customers when field is focused but empty
      fetchCustomersForDropdown()
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

    // Normalize mobile: strip spaces and a leading "+", then strip a leading
    // "91" only when the total length is exactly 12 (the country-code form).
    // This preserves real 10-digit numbers that happen to start with 91.
    let cleanMobile = newCustomerData.mobile.trim().replace(/\s+/g, '').replace(/^\+/, '')
    if (cleanMobile.length === 12 && cleanMobile.startsWith('91')) {
      cleanMobile = cleanMobile.slice(2)
    }
    if (!/^\d{10}$/.test(cleanMobile)) {
      showWarning('Please enter a valid 10-digit mobile number')
      return
    }

    // Split name into first and last name
    const nameParts = newCustomerData.name.trim().split(' ')
    const firstName = nameParts[0] || ''
    const lastName = nameParts.slice(1).join(' ') || ''

    setCreatingCustomer(true)
    try {
      const customerPayload = {
        mobile: cleanMobile,
        firstName: firstName,
        lastName: lastName,
        gender: newCustomerData.gender,
        source: newCustomerData.source,
        dobRange: newCustomerData.dobRange || '',
        dob: newCustomerData.dob || ''
      }
      // Include referral code if provided and validated
      if (newCustomerData.referralCode && referralValidation?.valid) {
        customerPayload.referralCode = newCustomerData.referralCode.trim()
      }
      const response = await apiPost('/api/customers', customerPayload)

      const data = await response.json()

      if (!response.ok) {
        showError(data.error || 'Failed to create customer')
        return
      }

      // Build customer object from response
      const newCustomer = {
        id: data.id,
        mobile: cleanMobile,
        firstName: data.reason === 'existing_same_branch' && data.customerName ? data.customerName.split(' ')[0] : firstName,
        lastName: data.reason === 'existing_same_branch' && data.customerName ? data.customerName.split(' ').slice(1).join(' ') : lastName,
        email: ''
      }

      // Add to customers list and select
      setCustomers([newCustomer, ...customers])
      selectCustomer(newCustomer)

      // Reset form
      setShowNewCustomerForm(false)
      setNewCustomerData({ mobile: '', name: '', gender: '', source: 'Walk-in', dobRange: '', dob: '', referralCode: '' }); setReferralValidation(null)

      // Show appropriate message based on backend response
      if (data.created) {
        showSuccess(`Customer ${firstName} ${lastName} created successfully!`)
      } else if (data.reason === 'existing_same_branch') {
        showWarning(`Customer already exists in this branch — ${data.customerName || 'selected'}. Using existing record.`)
      }
    } catch (error) {
      console.error('Error creating customer:', error)
      showError(`Failed to create customer: ${error.message}`)
    } finally {
      setCreatingCustomer(false)
    }
  }

  const handleShowInventory = async (service) => {
    const selectedService = availableServices.find(s => s.id === service.service_id)

    if (!selectedService) {
      showWarning('Please select a service first')
      return
    }

    if (availableProducts.length === 0) {
      await fetchProducts()
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

  // Subtotal helpers split by category
  // These use gross price (before item-level discount) so the summary shows the right breakdown
  const getServiceSubtotal = () => {
    const servicesTotal = services.reduce((sum, s) => sum + (parseFloat(s.price) || 0), 0)
    const packagesTotal = packages.reduce((sum, pkg) => sum + (parseFloat(pkg.price) || 0), 0)
    const membershipsTotal = memberships.reduce((sum, m) => sum + (parseFloat(m.price) || 0), 0)
    return servicesTotal + packagesTotal + membershipsTotal
  }

  const getProductSubtotal = () => {
    return products.reduce((sum, product) => {
      const qty = parseFloat(product.quantity) || 1
      return sum + (parseFloat(product.price) || 0) * qty
    }, 0)
  }

  // Per-category subtotals for the Bill Summary breakdown.
  // Each is a plain sum of price × quantity for that category, before any
  // item-level discount, offer, or membership discount is applied.
  const getServicesOnlySubtotal = () =>
    services.reduce((sum, s) => sum + (parseFloat(s.price) || 0), 0)
  const getPackagesOnlySubtotal = () =>
    packages.reduce((sum, pkg) => sum + (parseFloat(pkg.price) || 0), 0)

  const calculateSubtotal = () => {
    return getServiceSubtotal() + getProductSubtotal()
  }

  // Sum of item-level discounts (entered as % per item)
  const calculateItemLevelDiscount = () => {
    const servicesDisc = services.reduce((sum, s) => {
      const price = parseFloat(s.price) || 0
      const disc = parseFloat(s.discount) || 0
      return sum + price * disc / 100
    }, 0)
    const packagesDisc = packages.reduce((sum, pkg) => {
      const price = parseFloat(pkg.price) || 0
      const disc = parseFloat(pkg.discount) || 0
      return sum + price * disc / 100
    }, 0)
    const productsDisc = products.reduce((sum, p) => {
      const price = parseFloat(p.price) || 0
      const qty = parseFloat(p.quantity) || 1
      const disc = parseFloat(p.discount) || 0
      return sum + price * qty * disc / 100
    }, 0)
    return servicesDisc + packagesDisc + productsDisc
  }

  // Helper: total of membership plan purchases in the cart (excluded from membership discount base)
  const getMembershipsTotal = () => {
    return memberships.reduce((sum, m) => sum + (parseFloat(m.price) || 0), 0)
  }

  // Helper: highest membership discount % available for THIS bill — considering
  // both the customer's active membership AND any plan being purchased now
  // (in-cart). Drives the toggle label and the visibility check.
  const getEffectiveMembershipPercent = () => {
    const active = (membershipInfo && membershipInfo.plan)
      ? parseFloat(membershipInfo.plan.allocated_discount) || 0
      : 0
    const inCart = memberships.reduce(
      (max, m) => Math.max(max, parseFloat(m.allocated_discount) || 0),
      0
    )
    return Math.max(active, inCart)
  }

  // Returns the matching membership coverage info for a given service id, or null.
  // Considers BOTH the customer's EXISTING active membership AND any plan being
  // purchased on this same bill (in-cart). When both cover the service, the
  // higher discount % wins.
  // STRICT MAPPING: a plan with empty `applicable_service_ids` covers nothing —
  // it applies no discount until the owner ticks specific services for it in
  // the Membership editor. Previously this defaulted to "covers all" which
  // surprised staff when adding a generic plan to a bill.
  const getMembershipCoverageForService = (serviceId) => {
    if (!serviceId) return null
    let best = null
    const consider = (plan, source) => {
      if (!plan) return
      const pct = parseFloat(plan.allocated_discount) || 0
      if (pct <= 0) return
      const ids = plan.applicable_service_ids
      // Strict: empty list = no coverage. The owner must explicitly tick services.
      if (!ids || ids.length === 0) return
      if (!ids.includes(serviceId)) return
      if (!best || pct > best.percent) {
        best = { name: plan.name || 'Membership', percent: pct, source }
      }
    }
    if (membershipInfo && membershipInfo.plan) {
      consider(membershipInfo.plan, 'active')
    }
    for (const m of memberships) {
      consider(m, 'in-cart')
    }
    return best
  }

  // (Removed getLegacyCoverageMembershipPercent — strict mapping means
  // packages and products are never discounted by membership. Membership
  // coverage is services-only, ticked explicitly in the Membership editor.)

  const calculateDiscount = () => {
    const subtotal = calculateSubtotal()

    // Offer takes precedence (single-offer rule: only one offer per bill)
    if (appliedOffer) {
      const pct = parseFloat(appliedOffer.discount_percentage) || 0
      const eligibleBase = subtotal - getMembershipsTotal()
      return Math.max(0, eligibleBase) * (pct / 100)
    }

    // Membership: walk per service line, apply each plan only to services it
    // actually covers (via getMembershipCoverageForService). Strict mapping —
    // packages and products are NOT discounted by membership; only services
    // explicitly ticked in the plan's coverage list get the discount.
    // Mirrors the backend's candidate_plans loop in bill_routes.py.
    if (discountType === 'membership') {
      let total = 0
      for (const s of services) {
        const lineTotal = parseFloat(s.total) || 0
        if (lineTotal <= 0) continue
        const coverage = getMembershipCoverageForService(s.service_id)
        if (coverage && coverage.percent > 0) {
          total += lineTotal * coverage.percent / 100
        }
      }
      return total
    }

    if (discountType === 'fix') {
      return parseFloat(discountAmount) || 0
    } else if (discountType === '%') {
      return subtotal * (parseFloat(discountAmount) || 0) / 100
    }

    return 0
  }

  // Calculate referral discount for referee's first bill
  const calculateReferralDiscount = () => {
    if (!referralInfo?.enabled || !customerDetails?.referredBy || customerDetails?.referralRewardUsed) return 0
    const subtotal = calculateSubtotal()
    if (subtotal <= 0) return 0
    if (referralInfo.rewardType === 'percentage') {
      return subtotal * (referralInfo.refereeReward / 100)
    }
    // Fixed amount — cap at subtotal
    return Math.min(referralInfo.refereeReward, subtotal)
  }

  const calculateNet = () => {
    return calculateSubtotal() - calculateItemLevelDiscount() - calculateDiscount() - calculateReferralDiscount()
  }

  // Tax calculation respecting inclusive/exclusive pricing per category
  const calculateTaxBreakdown = () => {
    const net = calculateNet()
    const totalSubtotal = calculateSubtotal()
    if (totalSubtotal === 0 || net <= 0) return { displayTax: 0, additionalTax: 0 }

    // Split net proportionally between services and products
    const servicePortion = net * (getServiceSubtotal() / totalSubtotal)
    const productPortion = net * (getProductSubtotal() / totalSubtotal)

    let displayTax = 0    // Tax amount to show in summary
    let additionalTax = 0 // Tax to add on top of net (only for exclusive)

    // Service tax
    if (serviceTaxRate > 0 && servicePortion > 0) {
      if (taxSettings.servicePricingType === 'inclusive') {
        // Tax is already in the price — extract for display only
        displayTax += servicePortion - (servicePortion / (1 + serviceTaxRate / 100))
      } else {
        const tax = servicePortion * (serviceTaxRate / 100)
        displayTax += tax
        additionalTax += tax
      }
    }

    // Product tax
    if (productTaxRate > 0 && productPortion > 0) {
      if (taxSettings.productPricingType === 'inclusive') {
        displayTax += productPortion - (productPortion / (1 + productTaxRate / 100))
      } else {
        const tax = productPortion * (productTaxRate / 100)
        displayTax += tax
        additionalTax += tax
      }
    }

    return { displayTax, additionalTax }
  }

  const calculateTax = () => {
    return calculateTaxBreakdown().displayTax
  }

  const calculateFinalAmount = () => {
    // Only exclusive tax adds to the total; inclusive tax is already in the price
    return calculateNet() + calculateTaxBreakdown().additionalTax
  }

  // Combined effective tax rate for display
  const getDisplayTaxRate = () => {
    const sRate = serviceTaxRate
    const pRate = productTaxRate
    if (sRate === pRate) return sRate
    // Mixed rates — show whichever is non-zero, or both
    const totalSubtotal = calculateSubtotal()
    if (totalSubtotal === 0) return sRate || pRate
    // Weighted average for display
    const sWeight = getServiceSubtotal() / totalSubtotal
    const pWeight = getProductSubtotal() / totalSubtotal
    return (sRate * sWeight + pRate * pWeight)
  }

  // Check if any portion uses inclusive pricing
  const hasInclusiveTax = () => {
    return (serviceTaxRate > 0 && taxSettings.servicePricingType === 'inclusive' && getServiceSubtotal() > 0) ||
           (productTaxRate > 0 && taxSettings.productPricingType === 'inclusive' && getProductSubtotal() > 0)
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
    setMemberships([])
    setSelectedCustomer(null)
    setSearchQuery('')
    setDiscountAmount(0)
    setDiscountType('fix')
    setMembershipInfo(null)
    setCustomerDetails(null)
    setCustomerDob(null)
    setBookingNote('')
    setBookingStatus('confirmed')
    setAppliedOffer(null)
    appointmentCreatedRef.current = false
    setEditingAppointmentId(null)
    setPendingApproval(null)
    setApprovalReason('')
    setApprovalCode('')
    setShowApprovalForm(false)
  }

  const handleCheckout = async () => {
    // Re-entrancy guard — prevents duplicate bills when user clicks Checkout repeatedly
    if (isCheckingOut) return
    setIsCheckingOut(true)
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

      // Phase 5: Non-owner applying ANY discount → needs approval reason BEFORE bill creation
      const hasBillDiscount = discountType !== 'membership' && parseFloat(discountAmount) > 0
      const hasItemDiscount = services.some(s => parseFloat(s.discount) > 0) ||
                              packages.some(p => parseFloat(p.discount) > 0) ||
                              products.some(p => parseFloat(p.discount) > 0)
      const hasManualDiscount = hasBillDiscount || hasItemDiscount
      if (hasManualDiscount && user && user.role !== 'owner') {
        if (!approvalReason.trim()) {
          setShowApprovalForm(true)
          showWarning('Please provide a reason for the discount approval request')
          return
        }
      }

      // If retrying after approval was granted, reuse the existing bill
      if (pendingApproval && pendingApproval.billId) {
        const billId = pendingApproval.billId
        // Go straight to checkout with the existing bill
        const checkoutBillDate = formatLocalDate(selectedDate)
        const checkoutResponse = await apiPost(`/api/bills/${billId}/checkout`, {
          bill_date: checkoutBillDate,
          discount_amount: appliedOffer
            ? 0
            : (membershipInfo && membershipInfo.plan && discountType === 'membership'
              ? membershipInfo.plan.allocated_discount
              : parseFloat(discountAmount) || 0),
          discount_type: appliedOffer
            ? 'offer'
            : (discountType === 'membership' ? 'membership' : (discountType === '%' ? 'percentage' : 'fix')),
          applied_offer_id: appliedOffer ? appliedOffer.id : undefined,
          discount_reason: approvalReason || undefined,
          approval_code: approvalCode.trim() || undefined,
          referral_discount: calculateReferralDiscount(),
          tax_rate: getDisplayTaxRate(),
          tax_amount: calculateTax(),
          final_amount: calculateFinalAmount(),
          payment_mode: paymentMode,
          card_bank: paymentMode === 'card' ? cardBank : undefined,
          booking_status: bookingStatus,
        })

        if (checkoutResponse.ok) {
          setPendingApproval(null)
          setApprovalReason('')
          setApprovalCode('')
          celebrateBig()
          showSuccess('Checkout successful!')
          handleReset()
          fetchProducts()
          setCurrentBillId(billId)
          setShowInvoiceModal(true)
          fetchInvoiceData(billId) // parallel, not awaited
          return
        } else {
          let errorMessage = 'Failed to complete checkout. Please try again.'
          try {
            const error = await checkoutResponse.json()
            errorMessage = error.error || errorMessage
            if (error.code_invalid) {
              showError(error.error || 'Invalid approval code')
              setApprovalCode('')
              return
            }
            if (error.requires_approval) {
              showWarning(error.message || 'Discount still pending owner approval')
              return
            }
          } catch (e) {
            errorMessage = `Server error: ${checkoutResponse.status} ${checkoutResponse.statusText}`
          }
          showError(errorMessage)
          return
        }
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

      // Build the items list up front so we can send them alongside the bill creation
      // (saves one HTTP round-trip). When editing an existing appointment bill, the
      // backend clears and re-adds items, so skip inline-items in that path and use bulk.
      const allItems = []
      validServices.forEach(service => {
        if (service.service_id && service.price > 0) {
          allItems.push({
            item_type: 'service',
            service_id: service.service_id,
            staff_id: service.staff_id || null,
            start_time: service.startTime ? `${service.startTime}:00` : null,
            price: parseFloat(service.price) || 0,
            discount: parseFloat(service.discount) || 0,
            quantity: 1,
            total: parseFloat(service.total) || parseFloat(service.price) || 0,
          })
        }
      })
      packages.forEach(pkg => {
        if (pkg.package_id) {
          allItems.push({
            item_type: 'package',
            package_id: pkg.package_id,
            price: parseFloat(pkg.price) || 0,
            discount: parseFloat(pkg.discount) || 0,
            quantity: 1,
            total: parseFloat(pkg.total) || parseFloat(pkg.price) || 0,
          })
        }
      })
      products.forEach(product => {
        if (product.product_id) {
          allItems.push({
            item_type: 'product',
            product_id: product.product_id,
            price: parseFloat(product.price) || 0,
            discount: parseFloat(product.discount) || 0,
            quantity: parseInt(product.quantity) || 1,
            total: parseFloat(product.total) || parseFloat(product.price) * (parseInt(product.quantity) || 1) || 0,
          })
        }
      })
      memberships.forEach(membership => {
        if (membership.membership_id || membership.name) {
          allItems.push({
            item_type: 'membership',
            membership_id: membership.membership_id,
            name: membership.name || '',
            price: parseFloat(membership.price) || 0,
            discount: 0,
            quantity: 1,
            total: parseFloat(membership.price) || 0,
          })
        }
      })

      // Only inline items when creating a fresh bill. Editing an appointment reuses
      // an existing bill on the backend which clears items — use bulk-add after instead.
      if (!editingAppointmentId && allItems.length > 0) {
        billPayload.items = allItems
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

      // Items flow:
      //  - Fresh bill with `items` inlined in POST /bills → already persisted server-side.
      //  - Otherwise (editing an appointment, or older backend) → fall back to bulk-add,
      //    then to per-item add if the bulk endpoint isn't available.
      const itemsAlreadyPersisted = !editingAppointmentId && (billData.data.items_count || 0) > 0
      if (!itemsAlreadyPersisted && allItems.length > 0) {
        const bulkResp = await apiPost(`/api/bills/${billId}/items/bulk`, { items: allItems })
        if (bulkResp.ok) {
          // Bulk path succeeded
        } else if (bulkResp.status === 404 || bulkResp.status === 405) {
          console.warn('[CHECKOUT] Bulk items endpoint not available, falling back to per-item add')
          for (const itemData of allItems) {
            const r = await apiPost(`/api/bills/${billId}/items`, itemData)
            if (!r.ok) {
              const errorData = await r.json().catch(() => ({}))
              throw new Error(errorData.error || `Failed to add ${itemData.item_type} to bill`)
            }
          }
        } else {
          const errorData = await bulkResp.json().catch(() => ({}))
          throw new Error(errorData.error || 'Failed to add items to bill')
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
        discount_amount: appliedOffer
          ? 0
          : (membershipInfo && membershipInfo.plan && discountType === 'membership'
            ? membershipInfo.plan.allocated_discount
            : parseFloat(discountAmount) || 0),
        discount_type: appliedOffer
          ? 'offer'
          : (discountType === 'membership' ? 'membership' : (discountType === '%' ? 'percentage' : 'fix')),
        applied_offer_id: appliedOffer ? appliedOffer.id : undefined,
        discount_reason: approvalReason || undefined,
        approval_code: approvalCode.trim() || undefined,
        referral_discount: calculateReferralDiscount(),
        tax_rate: getDisplayTaxRate(),
        tax_amount: calculateTax(),
        final_amount: calculateFinalAmount(),
        payment_mode: paymentMode,
        card_bank: paymentMode === 'card' ? cardBank : undefined,
        booking_status: bookingStatus,
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

        // Save customer DOB if entered/updated
        if (customerDob && selectedCustomer) {
          apiPut(`/api/customers/${selectedCustomer.id}`, {
            dob: customerDob.toISOString().split('T')[0]
          }).catch(err => console.error('Error saving customer DOB:', err))
        }

        // Celebrate with confetti!
        celebrateBig()

        // Refresh products to show updated stock after checkout
        fetchProducts()
        
        // Show the invoice modal immediately. If the checkout response already bundled
        // the invoice data (new backend), use it directly — skips the GET /invoice round-trip
        // entirely. Otherwise fall back to the background fetch.
        setCurrentBillId(billId)
        setShowInvoiceModal(true)
        if (checkoutData && checkoutData.invoice) {
          setInvoiceData(checkoutData.invoice)
          setLoadingInvoice(false)
        } else {
          fetchInvoiceData(billId) // not awaited — runs in parallel
        }
      } else {
        let errorMessage = 'Failed to complete checkout. Please try again.'
        try {
          const error = await checkoutResponse.json()
          errorMessage = error.error || errorMessage

          // Handle invalid approval code
          if (error.code_invalid) {
            showError(error.error || 'Invalid approval code')
            setApprovalCode('')
            setPendingApproval({ id: error.approval_id || null, approval_status: 'pending', billId })
            return
          }

          // Handle approval required - store billId for retry
          if (error.requires_approval && error.approval_id) {
            setPendingApproval({ id: error.approval_id, approval_status: 'pending', billId })
            showInfo(error.message || 'Discount approval request submitted. Ask the owner to approve, then retry.')
            return
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
    } finally {
      // Always release the guard so the user can retry on validation/server errors
      setIsCheckingOut(false)
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

  const handleDownloadInvoice = async (billIdArg) => {
    const billId = billIdArg || currentBillId
    if (!billId) {
      showError('No bill found')
      return
    }

    try {
      const token = sessionStorage.getItem('auth_token') || sessionStorage.getItem('token')
      let branchId = currentBranch?.id
      if (!branchId) {
        const storedBranch = sessionStorage.getItem('current_branch')
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
                      fetchCustomersForDropdown()
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
                      fetchCustomersForDropdown()
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
                    {filteredCustomers.length === 0 && searchQuery.length > 0 && !selectedCustomer ? (
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
                  // Only open calendar if clicking on wrapper/display/icon, not on the datepicker itself
                  const target = e.target
                  if (target.classList.contains('date-display') || 
                      target.classList.contains('calendar-icon') || 
                      target.closest('.date-display') || 
                      target.closest('.calendar-icon')) {
                    const input = e.currentTarget.querySelector('.react-datepicker__input-container input')
                    if (input) {
                      input.focus()
                      input.click()
                    }
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
                  shouldCloseOnSelect={true}
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
                  <div className="customer-info-header-cell">Last Service</div>
                  <div className="customer-info-header-cell">Date of Birth</div>
                </div>
                <div className="customer-info-row">
                  <div className="customer-info-cell" data-label="Membership">{customerDetails.membership}</div>
                  <div className="customer-info-cell" data-label="Last Visit">{customerDetails.lastVisit ? formatDate(customerDetails.lastVisit) : 'N/A'}</div>
                  <div className="customer-info-cell" data-label="Total Visits">{customerDetails.totalVisits}</div>
                  <div className="customer-info-cell" data-label="Total Revenue">₹{customerDetails.totalRevenue.toFixed(2)}</div>
                  <div className="customer-info-cell" data-label="Last Service">{customerDetails.lastService}</div>
                  <div className="customer-info-cell" data-label="Date of Birth">
                    {customerDetails.dob
                      ? (() => {
                          const d = new Date(customerDetails.dob)
                          const today = new Date()
                          const isBirthMonth = d.getMonth() === today.getMonth()
                          return (
                            <span style={isBirthMonth ? { color: '#be185d', fontWeight: '700' } : {}}>
                              {d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })}
                              {isBirthMonth && ' 🎂'}
                            </span>
                          )
                        })()
                      : 'N/A'}
                  </div>
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
                  services.map((service) => {
                    const coverage = getMembershipCoverageForService(service.service_id)
                    return (
                    <tr key={service.id} className="service-table-row">
                      <td>
                        <ServiceSearchSelect
                          value={service.service_id}
                          services={availableServices}
                          onChange={(id) => updateService(service.id, 'service_id', id)}
                          disabled={loadingServices}
                          loadingServices={loadingServices}
                        />
                        {coverage && (
                          <div
                            title={`${coverage.name}: ${coverage.percent}% off applies when membership discount is enabled`}
                            style={{
                              marginTop: 4,
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: 4,
                              padding: '2px 8px',
                              borderRadius: 10,
                              background: '#dcfce7',
                              color: '#15803d',
                              fontSize: 11,
                              fontWeight: 600,
                            }}
                          >
                            <FaGift size={10} />
                            Membership {coverage.percent}%
                          </div>
                        )}
                      </td>
                      <td>
                        <CompactSelect
                          className="table-select"
                          value={service.staff_id}
                          onChange={(val) => updateService(service.id, 'staff_id', val)}
                          placeholder="Select staff"
                          options={staffMembers.map(staff => ({
                            value: staff.id,
                            label: `${staff.firstName} ${staff.lastName || ''}`.trim()
                          }))}
                        />
                      </td>
                      <td>
                        <ClassicTimePicker
                          value={service.startTime || ''}
                          onChange={(v) => updateService(service.id, 'startTime', v)}
                          placeholder="HH:MM"
                          minuteStep={5}
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
                        {coverage && coverage.percent > 0 && (parseFloat(service.total) || 0) > 0 ? (
                          <div className="row-total-with-discount">
                            <span className="row-total-strike">₹{Number(service.total || 0).toFixed(2)}</span>
                            <span className="row-total-net">
                              ₹{(Number(service.total || 0) * (1 - coverage.percent / 100)).toFixed(2)}
                            </span>
                          </div>
                        ) : (
                          <input
                            type="number"
                            className="table-input"
                            placeholder="0"
                            value={service.total.toFixed(2)}
                            readOnly
                          />
                        )}
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
                    )
                  })
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
          <button
            className="pill-button"
            onClick={addMembership}
            disabled={memberships.length > 0}
            title={
              memberships.length > 0
                ? 'Only one membership plan per bill'
                : (membershipInfo && membershipInfo.plan
                    ? `Use this only to upgrade or renew ${membershipInfo.plan.name}. The customer's existing discount applies automatically — you don't need to add it here.`
                    : undefined)
            }
          >
            {membershipInfo && membershipInfo.plan ? 'Upgrade / Renew Membership' : 'Add Membership'}
          </button>
          <button
            className="pill-button"
            onClick={() => setShowOfferModal(true)}
            title={appliedOffer ? `Currently applied: ${appliedOffer.name}` : 'Pick an active offer for this bill'}
          >
            {appliedOffer ? `Change Offer (${appliedOffer.discount_percentage}%)` : 'Add Offer'}
          </button>
        </div>

        {/* Display Added Items in Grid Layout */}
        {(packages.length > 0 || products.length > 0 || memberships.length > 0) && (
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
                <CompactSelect
                  className="form-select"
                  value={bookingStatus}
                  onChange={(newStatus) => {
                    setBookingStatus(newStatus)
                    // Reset appointment created flag when changing status
                    if (newStatus === 'service-completed' || newStatus === 'confirmed') {
                      appointmentCreatedRef.current = false
                    }
                  }}
                  options={[
                    { value: 'confirmed', label: 'Appointment' },
                    { value: 'service-completed', label: 'Service Completed' },
                  ]}
                />
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
                {paymentMode === 'card' && (
                  <div className="bank-dropdown-container" style={{ marginTop: '12px' }}>
                    <label className="form-label" style={{ marginBottom: '8px', display: 'block' }}>Card Bank</label>
                    <select
                      className="form-select"
                      value={cardBank}
                      onChange={(e) => setCardBank(e.target.value)}
                      required
                    >
                      <option value="">Select Bank</option>
                      <option value="HDFC">HDFC</option>
                      <option value="ICICI">ICICI</option>
                      <option value="SBI">SBI</option>
                      <option value="Axis">Axis</option>
                      <option value="Kotak">Kotak</option>
                      <option value="Yes Bank">Yes Bank</option>
                      <option value="IndusInd">IndusInd</option>
                      <option value="PNB">PNB</option>
                      <option value="BOB">BOB</option>
                      <option value="Canara">Canara</option>
                      <option value="Other">Other</option>
                    </select>
                  </div>
                )}
              </div>
              
              {/* Date of Birth Collection */}
              {selectedCustomer && (
                <div className="dob-collection-container" style={{ marginBottom: '16px' }}>
                  <label className="form-label">Date of Birth</label>
                  <DatePicker
                    selected={customerDob}
                    onChange={(date) => setCustomerDob(date)}
                    dateFormat="dd-MM-yyyy"
                    maxDate={new Date()}
                    placeholderText="Select date of birth"
                    className="form-input"
                    showYearDropdown
                    showMonthDropdown
                    dropdownMode="select"
                    isClearable
                  />
                </div>
              )}

              <div className="booking-note-membership-wrapper">
                <div className="booking-note-container">
                  <h3 className="booking-note-title">Booking Note</h3>
                  <textarea
                    className="form-textarea"
                    placeholder="Add booking notes (optional)"
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
                        marginBottom: '8px'
                      }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                          <FaGift size={16} />
                          <strong>Active Membership: {membershipInfo.plan.name}</strong>
                        </div>
                        <div className="membership-info-text">
                          {membershipInfo.plan.allocated_discount}% discount available on services
                        </div>
                        {membershipInfo.expiry_date && (
                          <div className="membership-expiry-text">
                            Expires: {new Date(membershipInfo.expiry_date).toLocaleDateString()}
                          </div>
                        )}
                        <div style={{ display: 'flex', gap: '8px', marginTop: '10px', flexWrap: 'wrap' }}>
                          {discountType === 'membership' ? (
                            <button
                              type="button"
                              onClick={() => {
                                setDiscountType('fix')
                                setDiscountAmount(0)
                              }}
                              style={{
                                padding: '6px 14px',
                                background: '#fff',
                                border: '1px solid #3b82f6',
                                color: '#1e40af',
                                borderRadius: '6px',
                                cursor: 'pointer',
                                fontSize: '13px',
                                fontWeight: 600
                              }}
                            >
                              Remove Membership Discount
                            </button>
                          ) : (
                            <button
                              type="button"
                              onClick={() => {
                                setDiscountType('membership')
                                setDiscountAmount(0)
                              }}
                              style={{
                                padding: '6px 14px',
                                background: '#3b82f6',
                                border: '1px solid #3b82f6',
                                color: '#fff',
                                borderRadius: '6px',
                                cursor: 'pointer',
                                fontSize: '13px',
                                fontWeight: 600
                              }}
                            >
                              Apply {membershipInfo.plan.allocated_discount}% Discount
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Right Column: Bill Summary */}
            <div className="bottom-column summary-column">
              <div className="summary-section">
                <h3 className="summary-title">Bill Summary</h3>
                <div className="summary-title-separator"></div>
                <div className="summary-values">
                  {/* Per-category breakdown — only rows with > 0 are shown so the
                      summary stays compact on simple bills. */}
                  <div className="summary-group">
                    {getServicesOnlySubtotal() > 0 && (
                      <div className="summary-row">
                        <span className="summary-label">Services</span>
                        <span className="summary-value">₹ {getServicesOnlySubtotal().toFixed(2)}</span>
                      </div>
                    )}
                    {getPackagesOnlySubtotal() > 0 && (
                      <div className="summary-row">
                        <span className="summary-label">Packages</span>
                        <span className="summary-value">₹ {getPackagesOnlySubtotal().toFixed(2)}</span>
                      </div>
                    )}
                    {getMembershipsTotal() > 0 && (
                      <div className="summary-row">
                        <span className="summary-label">
                          Membership{memberships[0]?.name ? ` (${memberships[0].name})` : ''}
                        </span>
                        <span className="summary-value">₹ {getMembershipsTotal().toFixed(2)}</span>
                      </div>
                    )}
                    {getProductSubtotal() > 0 && (
                      <div className="summary-row">
                        <span className="summary-label">Products</span>
                        <span className="summary-value">₹ {getProductSubtotal().toFixed(2)}</span>
                      </div>
                    )}
                    <div className="summary-row" style={{ fontWeight: 600 }}>
                      <span className="summary-label">Subtotal</span>
                      <span className="summary-value">₹ {calculateSubtotal().toFixed(2)}</span>
                    </div>
                  </div>

                  {/* Membership Discount Toggle — visible in the summary so staff
                      can opt-in next to the totals. Shows only when the customer has
                      an active plan OR a plan is being purchased in this bill. */}
                  {(membershipInfo && membershipInfo.plan && parseFloat(membershipInfo.plan.allocated_discount) > 0) ||
                   (memberships.some(m => parseFloat(m.allocated_discount) > 0)) ? (
                    <>
                      <div className="summary-divider"></div>
                      <div className="summary-group">
                        <div
                          className="summary-row"
                          style={{
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'space-between',
                            gap: '8px',
                            flexWrap: 'wrap'
                          }}
                        >
                          <label style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '8px',
                            cursor: 'pointer',
                            fontSize: '14px',
                            color: '#1e40af',
                            fontWeight: 500
                          }}>
                            <input
                              type="checkbox"
                              checked={discountType === 'membership'}
                              onChange={(e) => {
                                if (e.target.checked) {
                                  setDiscountType('membership')
                                  setDiscountAmount(0)
                                } else {
                                  setDiscountType('fix')
                                  setDiscountAmount(0)
                                }
                              }}
                              style={{ width: '16px', height: '16px', cursor: 'pointer' }}
                            />
                            <FaGift style={{ fontSize: '14px' }} />
                            Apply Membership Discount ({getEffectiveMembershipPercent()}%)
                          </label>
                        </div>
                      </div>
                    </>
                  ) : null}

                  {/* Discounts Group */}
                  {(calculateItemLevelDiscount() > 0) ||
                   (appliedOffer && calculateDiscount() > 0) ||
                   (!appliedOffer && discountType === 'membership' && calculateDiscount() > 0) ||
                   (!appliedOffer && discountType !== 'membership' && discountAmount > 0) ? (
                    <>
                      <div className="summary-divider"></div>
                      <div className="summary-group">
                        {calculateItemLevelDiscount() > 0 && (
                          <div className="summary-row manual-discount-row">
                            <span className="summary-label discount-label">
                              Item Discount
                            </span>
                            <span className="summary-value discount-value">
                              − ₹ {calculateItemLevelDiscount().toFixed(2)}
                            </span>
                          </div>
                        )}
                        {appliedOffer && calculateDiscount() > 0 && (
                          <div className="summary-row membership-discount-row">
                            <span className="summary-label discount-label">
                              <FaGift style={{ fontSize: '14px', marginRight: '6px' }} />
                              Offer ({appliedOffer.name} – {appliedOffer.discount_percentage}%)
                            </span>
                            <span className="summary-value discount-value">
                              − ₹ {calculateDiscount().toFixed(2)}
                            </span>
                          </div>
                        )}
                        {!appliedOffer && discountType === 'membership' && calculateDiscount() > 0 && (
                          <div className="summary-row membership-discount-row">
                            <span className="summary-label discount-label">
                              <FaGift style={{ fontSize: '14px', marginRight: '6px' }} />
                              {(() => {
                                const planName = (membershipInfo && membershipInfo.plan && membershipInfo.plan.name)
                                  || (memberships[0] && memberships[0].name)
                                  || null
                                return planName
                                  ? `Membership (${planName} – ${getEffectiveMembershipPercent()}%)`
                                  : `Membership (${getEffectiveMembershipPercent()}%)`
                              })()}
                            </span>
                            <span className="summary-value discount-value">
                              − ₹ {calculateDiscount().toFixed(2)}
                            </span>
                          </div>
                        )}
                        {!appliedOffer && discountType !== 'membership' && discountAmount > 0 && (
                          <div className="summary-row manual-discount-row">
                            <span className="summary-label discount-label">
                              Discount{discountType === '%' ? ` (${discountAmount}%)` : ''}
                            </span>
                            <span className="summary-value discount-value">
                              − ₹ {calculateDiscount().toFixed(2)}
                            </span>
                          </div>
                        )}
                      </div>
                    </>
                  ) : null}

                  {/* Referral Discount */}
                  {calculateReferralDiscount() > 0 && (
                    <>
                      <div className="summary-divider"></div>
                      <div className="summary-group">
                        <div className="summary-row referral-discount-row">
                          <span className="summary-label discount-label">
                            <FaGift style={{ fontSize: '14px', marginRight: '6px' }} />
                            Referral Discount ({referralInfo.rewardType === 'percentage' ? `${referralInfo.refereeReward}%` : `₹${referralInfo.refereeReward}`})
                          </span>
                          <span className="summary-value discount-value">
                            − ₹ {calculateReferralDiscount().toFixed(2)}
                          </span>
                        </div>
                      </div>
                    </>
                  )}

                  {/* Net Amount */}
                  <div className="summary-divider"></div>
                  <div className="summary-group">
                    <div className="summary-row net-row">
                      <span className="summary-label">Net Amount</span>
                      <span className="summary-value net-value">₹ {calculateNet().toFixed(2)}</span>
                    </div>
                  </div>

                  {/* Tax Group */}
                  <div className="summary-divider"></div>
                  <div className="summary-group">
                    <div className="summary-row">
                      <span className="summary-label">Tax ({getDisplayTaxRate().toFixed(1)}%{hasInclusiveTax() ? ' Incl.' : ''})</span>
                      <span className="summary-value">₹ {calculateTax().toFixed(2)}</span>
                    </div>
                  </div>

                  {/* Final Amount */}
                  <div className="summary-divider summary-divider-final"></div>
                  <div className="summary-group summary-group-final">
                    <div className="summary-row final">
                      <span className="summary-label">Total</span>
                      <span className="summary-value final-value">₹ {calculateFinalAmount().toFixed(2)}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Bottom Buttons */}
          <div className="action-buttons">
            <button className="reset-button" onClick={handleReset} disabled={isCheckingOut}>Reset</button>
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
              <>
                {pendingApproval && pendingApproval.approval_status === 'pending' && (
                  <div className="approval-code-inline">
                    <input
                      type="text"
                      className="approval-code-input-inline"
                      value={approvalCode}
                      onChange={(e) => setApprovalCode(e.target.value.toUpperCase())}
                      placeholder="Enter approval code from owner"
                      maxLength={12}
                    />
                  </div>
                )}
                <button
                  className="checkout-button"
                  onClick={handleCheckout}
                  disabled={isCheckingOut}
                  style={isCheckingOut ? { opacity: 0.6, cursor: 'not-allowed' } : undefined}
                >
                  {isCheckingOut
                    ? 'Processing...'
                    : (pendingApproval && pendingApproval.approval_status === 'pending'
                        ? (approvalCode.trim() ? 'Approve & Checkout' : 'Retry Checkout (Pending Approval)')
                        : 'Checkout')}
                </button>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Approval Request Form Modal */}
      {showApprovalForm && (
        <div className="modal-overlay" onClick={() => setShowApprovalForm(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="std-modal-header">
              <h2>Discount Approval Required</h2>
              <button
                type="button"
                className="modal-close-btn"
                onClick={() => {
                  setShowApprovalForm(false)
                  setApprovalReason('')
                  setApprovalCode('')
                }}
                aria-label="Close"
              >
                <FaTimes />
              </button>
            </div>
            <p>Discounts (including per-item discounts) require owner approval. Provide a reason, and enter an approval code if you have one.</p>
            <div className="form-group">
              <label>Reason for Discount *</label>
              <textarea
                value={approvalReason}
                onChange={(e) => setApprovalReason(e.target.value)}
                rows="3"
                placeholder="Enter reason for discount approval request"
                required
              />
            </div>
            <div className="form-group">
              <label>Approval Code (optional)</label>
              <input
                type="text"
                className="approval-code-input"
                value={approvalCode}
                onChange={(e) => setApprovalCode(e.target.value.toUpperCase())}
                placeholder="e.g. KX7H3NP2"
                maxLength={12}
              />
              <span style={{ fontSize: '12px', color: '#6b7280', marginTop: '4px', display: 'block' }}>
                Enter the code from your owner to approve instantly
              </span>
            </div>
            <div className="modal-actions">
              <button type="button" onClick={() => {
                setShowApprovalForm(false)
                setApprovalReason('')
                setApprovalCode('')
              }}>
                Cancel
              </button>
              <button
                onClick={() => {
                  if (approvalReason.trim()) {
                    setShowApprovalForm(false)
                    handleCheckout()
                  } else {
                    showWarning('Please provide a reason')
                  }
                }}
                className="btn-primary"
                disabled={isCheckingOut}
              >
                {isCheckingOut
                  ? 'Processing...'
                  : (approvalCode.trim() ? 'Approve & Checkout' : 'Submit for Approval')}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* New Customer Modal */}
      {showNewCustomerForm && createPortal(
        <div className="new-customer-modal-overlay" onClick={() => {
          setShowNewCustomerForm(false)
          setNewCustomerData({ mobile: '', name: '', gender: '', source: 'Walk-in', dobRange: '', dob: '', referralCode: '' }); setReferralValidation(null)
        }}>
          <div className="new-customer-modal" onClick={(e) => e.stopPropagation()}>
            <div className="new-customer-modal-header">
              <h2>Add New Customer</h2>
              <button 
                className="modal-close-btn"
                onClick={() => {
                  setShowNewCustomerForm(false)
                  setNewCustomerData({ mobile: '', name: '', gender: '', source: 'Walk-in', dobRange: '', dob: '', referralCode: '' }); setReferralValidation(null)
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
                    placeholder="10-digit mobile or with +91 prefix"
                    value={newCustomerData.mobile}
                    onChange={(e) => setNewCustomerData({ ...newCustomerData, mobile: e.target.value })}
                    className="modal-input"
                    maxLength={15}
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
                <div className="form-field-modal">
                  <label className="modal-label">
                    Date of Birth (Optional)
                  </label>
                  <DatePicker
                    selected={newCustomerData.dob ? new Date(newCustomerData.dob) : null}
                    onChange={(date) => setNewCustomerData({ ...newCustomerData, dob: date ? date.toISOString().split('T')[0] : '' })}
                    dateFormat="yyyy-MM-dd"
                    maxDate={new Date()}
                    placeholderText="Select date of birth"
                    className="modal-input"
                    disabled={creatingCustomer}
                    showYearDropdown
                    showMonthDropdown
                    dropdownMode="select"
                  />
                </div>
                {referralInfo?.enabled && (
                  <div className="form-field-modal">
                    <label className="modal-label">
                      Referral Code
                    </label>
                    <input
                      type="text"
                      placeholder="Enter referral code (optional)"
                      value={newCustomerData.referralCode}
                      onChange={(e) => {
                        const val = e.target.value.toUpperCase()
                        setNewCustomerData({ ...newCustomerData, referralCode: val })
                        setReferralValidation(null)
                      }}
                      onBlur={(e) => validateReferralCode(e.target.value)}
                      className="modal-input"
                      disabled={creatingCustomer}
                    />
                    {referralValidation && (
                      <span className={`referral-validation ${referralValidation.valid ? 'valid' : 'invalid'}`}>
                        {referralValidation.valid
                          ? `Referred by: ${referralValidation.referrerName}`
                          : referralValidation.error}
                      </span>
                    )}
                  </div>
                )}
              </div>
            </div>
            <div className="new-customer-modal-footer">
              <button
                className="modal-btn-cancel"
                onClick={() => {
                  setShowNewCustomerForm(false)
                  setNewCustomerData({ mobile: '', name: '', gender: '', source: 'Walk-in', dobRange: '', dob: '', referralCode: '' }); setReferralValidation(null)
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
        </div>,
        document.body
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
              <h2>Bill Activity - {selectedCustomer?.firstName} {selectedCustomer?.lastName}</h2>
              <button
                type="button"
                className="modal-close-btn"
                onClick={() => setShowBillActivityModal(false)}
                aria-label="Close"
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
                              value={productQuantities[product.id] || 1}
                              onChange={(e) => {
                                const newQuantity = parseInt(e.target.value) || 1
                                setProductQuantities(prev => ({
                                  ...prev,
                                  [product.id]: newQuantity
                                }))
                              }}
                              onClick={(e) => e.stopPropagation()}
                              disabled={isOutOfStock}
                            />
                          </div>
                          <button 
                            className="select-btn"
                            onClick={(e) => {
                              e.stopPropagation()
                              const quantity = productQuantities[product.id] || 1
                              handleSelectProduct(product, quantity)
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

      {/* Offer Selection Modal — single offer per bill (single-offer rule) */}
      {showOfferModal && (
        <div className="selection-modal-overlay" onClick={() => setShowOfferModal(false)}>
          <div className="selection-modal" onClick={(e) => e.stopPropagation()}>
            <div className="selection-modal-header">
              <h2>Select Offer</h2>
              <button className="modal-close-btn" onClick={() => setShowOfferModal(false)}>
                <FaTimes />
              </button>
            </div>
            <div className="selection-modal-body">
              {(() => {
                const eligible = availableOffers.filter(o =>
                  o.offer_type === 'general' || (membershipInfo && membershipInfo.plan)
                )
                if (eligible.length === 0) {
                  return (
                    <div className="selection-empty">
                      <p>No active offers. Create one in <strong>Offer Management</strong>.</p>
                    </div>
                  )
                }
                return (
                  <div className="selection-grid">
                    {appliedOffer && (
                      <div
                        className="selection-item"
                        onClick={() => {
                          setAppliedOffer(null)
                          setShowOfferModal(false)
                          showInfo('Offer removed')
                        }}
                        style={{ borderStyle: 'dashed' }}
                      >
                        <div className="selection-item-header">
                          <h3>Remove Offer</h3>
                          <span className="selection-price">—</span>
                        </div>
                        <div className="selection-item-details">
                          <p>Clear "{appliedOffer.name}" from this bill</p>
                        </div>
                      </div>
                    )}
                    {eligible.map(offer => (
                      <div
                        key={offer.id}
                        className={`selection-item ${appliedOffer && appliedOffer.id === offer.id ? 'selected' : ''}`}
                        onClick={() => {
                          if (offer.offer_type === 'membership' && !(membershipInfo && membershipInfo.plan)) {
                            showWarning(`"${offer.name}" applies only to membership customers`)
                            return
                          }
                          setAppliedOffer(offer)
                          setShowOfferModal(false)
                          showInfo(`Offer applied: ${offer.name} (${offer.discount_percentage}% off)`)
                        }}
                      >
                        <div className="selection-item-header">
                          <h3>{offer.name}</h3>
                          <span className="selection-price">{offer.discount_percentage}%</span>
                        </div>
                        <div className="selection-item-details">
                          <p>Type: {offer.offer_type === 'membership' ? 'Membership customers only' : 'All customers'}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                )
              })()}
            </div>
          </div>
        </div>
      )}

      {/* Invoice Modal */}
      {showInvoiceModal && (
        <div className="invoice-modal-overlay" onClick={handleCloseInvoiceModal}>
          <div className="invoice-modal-container" onClick={(e) => e.stopPropagation()}>
            <div className="invoice-modal-header">
              <button className="invoice-back-btn" onClick={handleCloseInvoiceModal}>
                ← Back
              </button>
              <h2>Invoice</h2>
            </div>

            {loadingInvoice ? (
              <div className="invoice-loading-state">
                <p>Loading invoice data...</p>
              </div>
            ) : invoiceData ? (
              <div className="invoice-preview-wrapper">
                <InvoicePreview
                  invoiceData={invoiceData}
                  billId={currentBillId}
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
