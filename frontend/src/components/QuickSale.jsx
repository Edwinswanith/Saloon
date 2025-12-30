import React, { useState, useEffect } from 'react'
import { FaBars, FaBell, FaUser, FaCalendar, FaHeart, FaTrash, FaChevronDown, FaClock } from 'react-icons/fa'
import './QuickSale.css'
import { API_BASE_URL } from '../config'
import { useAuth } from '../contexts/AuthContext'
import { apiGet } from '../utils/api'
import { showSuccess, showError, showWarning, showInfo } from '../utils/toast.jsx'
import DatePicker from 'react-datepicker'
import 'react-datepicker/dist/react-datepicker.css'
import { celebrateBig } from '../utils/confetti'
import { PageTransition } from './shared/PageTransition'
import { EmptyList } from './shared/EmptyStates'

const QuickSale = () => {
  const { user, getMaxDiscountPercent } = useAuth()
  const [pendingApproval, setPendingApproval] = useState(null)
  const [showApprovalForm, setShowApprovalForm] = useState(false)
  const [approvalReason, setApprovalReason] = useState('')

  const [discountType, setDiscountType] = useState('fix')
  const [paymentMode, setPaymentMode] = useState('cash')
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedDate, setSelectedDate] = useState(new Date())
  const [selectedCustomer, setSelectedCustomer] = useState(null)
  const [bookingStatus, setBookingStatus] = useState('pending')
  const [bookingNote, setBookingNote] = useState('')
  const [discountAmount, setDiscountAmount] = useState(0)

  // Data from backend
  const [customers, setCustomers] = useState([])
  const [staffMembers, setStaffMembers] = useState([])
  const [availableServices, setAvailableServices] = useState([])
  const [filteredCustomers, setFilteredCustomers] = useState([])
  const [showCustomerDropdown, setShowCustomerDropdown] = useState(false)

  const [services, setServices] = useState([
    {
      id: 1,
      service_id: '',
      staff_id: '',
      startTime: '',
      price: 0,
      discount: 0,
      total: 0,
    },
  ])
  const [packages, setPackages] = useState([])
  const [products, setProducts] = useState([])
  const [prepaidPackages, setPrepaidPackages] = useState([])
  const [memberships, setMemberships] = useState([])
  const [availablePackages, setAvailablePackages] = useState([])
  const [availableProducts, setAvailableProducts] = useState([])
  const [availablePrepaid, setAvailablePrepaid] = useState([])
  const [availableMemberships, setAvailableMemberships] = useState([])

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
        email: customer.email || '',
        wallet_balance: customer.wallet || customer.wallet_balance || 0,
        loyalty_points: customer.loyaltyPoints || customer.loyalty_points || 0
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
    setServices([
      ...services,
      {
        id: Date.now(),
        service_id: '',
        staff_id: '',
        startTime: '',
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
    const packageId = prompt('Enter Package ID or select from available packages:\n' + 
      availablePackages.map(p => `${p.id}: ${p.name} - ₹${p.price}`).join('\n'))
    if (packageId) {
      const selectedPackage = availablePackages.find(p => p.id === packageId)
      if (selectedPackage) {
        setPackages([...packages, {
          id: Date.now(),
          package_id: selectedPackage.id,
          name: selectedPackage.name,
          price: selectedPackage.price,
          discount: 0,
          total: selectedPackage.price,
        }])
      } else {
        showError('Package not found')
      }
    }
  }

  const addProduct = () => {
    if (!selectedCustomer) {
      showWarning('Please select a customer first')
      return
    }
    const productId = prompt('Enter Product ID or select from available products:\n' + 
      availableProducts.slice(0, 10).map(p => `${p.id}: ${p.name} - ₹${p.price} (Stock: ${p.stock_quantity || 0})`).join('\n'))
    if (productId) {
      const selectedProduct = availableProducts.find(p => p.id === productId)
      if (selectedProduct) {
        const quantity = prompt(`Enter quantity (Available: ${selectedProduct.stock_quantity || 0}):`, '1')
        if (quantity && parseInt(quantity) > 0) {
          setProducts([...products, {
            id: Date.now(),
            product_id: selectedProduct.id,
            name: selectedProduct.name,
            price: selectedProduct.price,
            quantity: parseInt(quantity),
            discount: 0,
            total: selectedProduct.price * parseInt(quantity),
          }])
        }
      } else {
        showError('Product not found')
      }
    }
  }

  const addPrepaid = () => {
    if (!selectedCustomer) {
      showWarning('Please select a customer first')
      return
    }
    // Fetch customer's prepaid packages
    fetch(`${API_BASE_URL}/api/prepaid/packages?customer_id=${selectedCustomer.id}`)
      .then(res => res.json())
      .then(data => {
        const customerPrepaid = data.packages || []
        if (customerPrepaid.length === 0) {
          showWarning('Customer has no active prepaid packages')
          return
        }
        const prepaidList = customerPrepaid.map(p => 
          `${p.id}: ${p.name} - Balance: ₹${p.remaining_balance || 0}`
        ).join('\n')
        const prepaidId = prompt('Select Prepaid Package:\n' + prepaidList)
        if (prepaidId) {
          const selectedPrepaid = customerPrepaid.find(p => p.id === prepaidId)
          if (selectedPrepaid) {
            setPrepaidPackages([...prepaidPackages, {
              id: Date.now(),
              prepaid_id: selectedPrepaid.id,
              name: selectedPrepaid.name,
              balance: selectedPrepaid.remaining_balance || 0,
            }])
          }
        }
      })
      .catch(error => {
        console.error('Error fetching prepaid packages:', error)
        showError('Error loading prepaid packages')
      })
  }

  const addMembership = () => {
    if (!selectedCustomer) {
      showWarning('Please select a customer first')
      return
    }
    const membershipId = prompt('Enter Membership Plan ID:\n' + 
      availableMemberships.map(m => `${m.id}: ${m.name} - ₹${m.price} (${m.validity_days} days)`).join('\n'))
    if (membershipId) {
      const selectedMembership = availableMemberships.find(m => m.id === membershipId)
      if (selectedMembership) {
        setMemberships([...memberships, {
          id: Date.now(),
          membership_id: selectedMembership.id,
          name: selectedMembership.name,
          price: selectedMembership.price,
        }])
      } else {
        showError('Membership plan not found')
      }
    }
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
  }

  const handleCustomerInputFocus = () => {
    if (!selectedCustomer) {
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
  }

  const handleCustomerInputChange = (e) => {
    const value = e.target.value
    setSearchQuery(value)
    // Clear selection if user is typing
    if (selectedCustomer && value !== `${selectedCustomer.firstName || ''} ${selectedCustomer.lastName || ''} - ${selectedCustomer.mobile}`.trim()) {
      setSelectedCustomer(null)
    }
  }

  const calculateSubtotal = () => {
    const servicesTotal = services.reduce((sum, service) => sum + (parseFloat(service.total) || 0), 0)
    const packagesTotal = packages.reduce((sum, pkg) => sum + (parseFloat(pkg.total) || 0), 0)
    const productsTotal = products.reduce((sum, product) => sum + (parseFloat(product.total) || 0), 0)
    return servicesTotal + packagesTotal + productsTotal
  }

  const calculateDiscount = () => {
    const subtotal = calculateSubtotal()
    if (discountType === 'fix') {
      return parseFloat(discountAmount) || 0
    } else {
      return subtotal * (parseFloat(discountAmount) || 0) / 100
    }
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

  const handleReset = () => {
    setServices([{
      id: 1,
      service_id: '',
      staff_id: '',
      startTime: '',
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
    setBookingNote('')
    setBookingStatus('pending')
  }

  const handleCheckout = async () => {
    try {
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

      // Create bill
      const billResponse = await fetch(`${API_BASE_URL}/api/bills`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          customer_id: selectedCustomer.id,
          booking_status: bookingStatus,
          booking_note: bookingNote,
        }),
      })

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
            const itemResponse = await fetch(`${API_BASE_URL}/api/bills/${billId}/items`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                item_type: 'service',
                service_id: service.service_id,  // MongoDB ObjectId as string
                staff_id: service.staff_id || null,  // MongoDB ObjectId as string
                start_time: service.startTime ? `${service.startTime}:00` : null,
                price: parseFloat(service.price) || 0,
                discount: parseFloat(service.discount) || 0,
                quantity: 1,
                total: parseFloat(service.total) || parseFloat(service.price) || 0,
              }),
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
            const itemResponse = await fetch(`${API_BASE_URL}/api/bills/${billId}/items`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                item_type: 'package',
                package_id: pkg.package_id,  // MongoDB ObjectId as string
                price: parseFloat(pkg.price) || 0,
                discount: parseFloat(pkg.discount) || 0,
                quantity: 1,
                total: parseFloat(pkg.total) || parseFloat(pkg.price) || 0,
              }),
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
            const itemResponse = await fetch(`${API_BASE_URL}/api/bills/${billId}/items`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                item_type: 'product',
                product_id: product.product_id,  // MongoDB ObjectId as string
                price: parseFloat(product.price) || 0,
                discount: parseFloat(product.discount) || 0,
                quantity: parseInt(product.quantity) || 1,  // Quantity is a number, keep parseInt
                total: parseFloat(product.total) || parseFloat(product.price) * (parseInt(product.quantity) || 1) || 0,
              }),
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
            const itemResponse = await fetch(`${API_BASE_URL}/api/bills/${billId}/items`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                item_type: 'membership',
                membership_id: membership.membership_id,  // MongoDB ObjectId as string
                price: parseFloat(membership.price) || 0,
                discount: 0,
                quantity: 1,
                total: parseFloat(membership.price) || 0,
              }),
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

      // Checkout
      const checkoutResponse = await fetch(`${API_BASE_URL}/api/bills/${billId}/checkout`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        },
        body: JSON.stringify({
          discount_amount: parseFloat(discountAmount) || 0,
          discount_type: discountType === 'fix' ? 'fix' : 'percentage',
          discount_reason: approvalReason || undefined, // Phase 5: Include reason
          tax_rate: 18.0, // GST rate - ensure it's a float
          payment_mode: paymentMode,
          booking_status: bookingStatus,
          prepaid_package_id: prepaidPackageId,
        }),
      })

      if (checkoutResponse.ok) {
        const checkoutData = await checkoutResponse.json()
        showSuccess(`Bill created successfully! Bill Number: ${checkoutData.bill_number} | Final Amount: ₹${checkoutData.final_amount.toFixed(2)}`)
        
        // Celebrate with confetti!
        celebrateBig()
        
        handleReset()
        setPendingApproval(null)
        setShowApprovalForm(false)
        setApprovalReason('')
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

  const formatDate = (dateString) => {
    const date = new Date(dateString)
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

  return (
    <PageTransition>
      <div className="quick-sale-page">
        {/* Top Header Bar */}
      <header className="quicksale-header">
        <div className="header-left">
          <button className="menu-icon"><FaBars /></button>
          <h1 className="header-title">Quicksale</h1>
        </div>
        <div className="header-right">
          <div className="logo-box">
            <span className="logo-text">HAIR STUDIO</span>
          </div>
          <button className="header-icon bell-icon"><FaBell /></button>
          <button className="header-icon user-icon"><FaUser /></button>
        </div>
      </header>

      <div className="quick-sale-container">
        <div className="quick-sale-card">
          <h1 className="card-title">New Booking</h1>

          {/* Top Row: Search, Date */}
          <div className="top-row">
            <div className="search-container" style={{ position: 'relative', flex: 1 }}>
              <label className="field-label" style={{ marginBottom: '5px', display: 'block', fontWeight: 'bold', color: selectedCustomer ? '#4CAF50' : '#374151' }}>
                Customer * {selectedCustomer && <span style={{ color: '#4CAF50', fontSize: '12px', marginLeft: '8px' }}>✓ Selected: {selectedCustomer.firstName || ''} {selectedCustomer.lastName || ''}</span>}
              </label>
              <input
                type="text"
                className="search-input"
                placeholder={selectedCustomer ? `${selectedCustomer.firstName || ''} ${selectedCustomer.lastName || ''} - ${selectedCustomer.mobile}` : "Search by Mobile Number or Name"}
                value={searchQuery}
                onChange={handleCustomerInputChange}
                onFocus={handleCustomerInputFocus}
                style={{
                  borderColor: selectedCustomer ? '#4CAF50' : (showCustomerDropdown ? '#7c3aed' : '#d1d5db'),
                  borderWidth: selectedCustomer ? '2px' : '1px',
                  backgroundColor: selectedCustomer ? '#f0fdf4' : 'white'
                }}
              />
              <span className="dropdown-arrow"><FaChevronDown /></span>
              {showCustomerDropdown && (
                <div className="customer-dropdown">
                  {filteredCustomers.length === 0 && searchQuery.length > 0 ? (
                    <div style={{ padding: '12px', color: '#6b7280', textAlign: 'center' }}>
                      No customers found. Try a different search term.
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
              {!selectedCustomer && (
                <div style={{ marginTop: '4px', fontSize: '12px', color: '#ef4444' }}>
                  ⚠ Please select a customer to proceed
                </div>
              )}
            </div>
            <div className="date-container">
              <label className="date-label">Date *</label>
              <div className="date-input-wrapper">
                <DatePicker
                  selected={selectedDate}
                  onChange={(date) => setSelectedDate(date)}
                  dateFormat="dd/MM/yyyy"
                  className="date-picker"
                  placeholderText="Select date"
                />
                <span className="date-display">{formatDate(selectedDate)}</span>
                <span className="calendar-icon"><FaCalendar /></span>
              </div>
            </div>
          </div>

          {/* Service Rows */}
          {services.map((service) => (
            <div key={service.id} className="service-row">
              <div className="form-field">
                <label className="field-label">Service</label>
                <select
                  className="form-select"
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
              </div>
              <div className="form-field">
                <label className="field-label">Staff</label>
                <select
                  className="form-select"
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
              </div>
              <div className="form-field">
                <label className="field-label">Start time</label>
                <div className="time-input-wrapper">
                  <input
                    type="time"
                    className="time-input"
                    value={service.startTime}
                    onChange={(e) => updateService(service.id, 'startTime', e.target.value)}
                  />
                  <span className="time-display">
                    {service.startTime ? formatTime(service.startTime) : ''}
                  </span>
                  <span className="clock-icon"><FaClock /></span>
                </div>
              </div>
              <div className="form-field">
                <label className="field-label">Price (₹)</label>
                <input
                  type="number"
                  className="form-input"
                  placeholder="0"
                  value={service.price}
                  onChange={(e) => updateService(service.id, 'price', e.target.value)}
                />
              </div>
              <div className="form-field">
                <label className="field-label">Discount (%)</label>
                <input
                  type="number"
                  className="form-input"
                  placeholder="0"
                  value={service.discount}
                  onChange={(e) => updateService(service.id, 'discount', e.target.value)}
                />
              </div>
              <div className="form-field">
                <label className="field-label">Total (₹)</label>
                <input
                  type="number"
                  className="form-input"
                  placeholder="0"
                  value={service.total.toFixed(2)}
                  readOnly
                />
              </div>
              <div className="service-actions">
                <button 
                  className="detail-button"
                  title="View Service Details"
                  onClick={() => {
                    const selectedService = availableServices.find(s => s.id === service.service_id)
                    if (selectedService) {
                      showInfo(`Service: ${selectedService.name} | Price: ₹${selectedService.price} | Duration: ${selectedService.duration || 'N/A'} mins`)
                    } else {
                      showWarning('Please select a service first')
                    }
                  }}
                >
                  <FaHeart />
                </button>
                <button
                  className="trash-button"
                  onClick={() => removeService(service.id)}
                >
                  <FaTrash />
                </button>
              </div>
            </div>
          ))}

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

        {/* Display Added Packages */}
        {packages.length > 0 && (
          <div className="added-items-section">
            <h3>Added Packages:</h3>
            {packages.map(pkg => (
              <div key={pkg.id} className="added-item">
                <span>{pkg.name} - ₹{pkg.price}</span>
                <button onClick={() => removePackage(pkg.id)} className="remove-btn">Remove</button>
              </div>
            ))}
          </div>
        )}

        {/* Display Added Products */}
        {products.length > 0 && (
          <div className="added-items-section">
            <h3>Added Products:</h3>
            {products.map(product => (
              <div key={product.id} className="added-item">
                <span>{product.name} - ₹{product.price} x {product.quantity} = ₹{product.total}</span>
                <button onClick={() => removeProduct(product.id)} className="remove-btn">Remove</button>
              </div>
            ))}
          </div>
        )}

        {/* Display Added Prepaid */}
        {prepaidPackages.length > 0 && (
          <div className="added-items-section">
            <h3>Added Prepaid Packages:</h3>
            {prepaidPackages.map(prepaid => (
              <div key={prepaid.id} className="added-item">
                <span>{prepaid.name} - Balance: ₹{prepaid.balance}</span>
                <button onClick={() => removePrepaid(prepaid.id)} className="remove-btn">Remove</button>
              </div>
            ))}
          </div>
        )}

        {/* Display Added Memberships */}
        {memberships.length > 0 && (
          <div className="added-items-section">
            <h3>Added Memberships:</h3>
            {memberships.map(membership => (
              <div key={membership.id} className="added-item">
                <span>{membership.name} - ₹{membership.price}</span>
                <button onClick={() => removeMembership(membership.id)} className="remove-btn">Remove</button>
              </div>
            ))}
          </div>
        )}

          {/* Booking Status and Note Row */}
          <div className="booking-row">
            <div className="booking-status-container">
              <label className="form-label">Booking Status</label>
              <select
                className="form-select"
                value={bookingStatus}
                onChange={(e) => setBookingStatus(e.target.value)}
              >
                <option value="pending">Pending</option>
                <option value="confirmed">Confirmed</option>
                <option value="service-completed">Service Completed</option>
                <option value="cancelled">Cancelled</option>
              </select>
            </div>
            <div className="booking-note-container">
              <label className="form-label">Booking Note</label>
              <textarea
                className="form-textarea"
                placeholder="Add any notes here..."
                rows="3"
                value={bookingNote}
                onChange={(e) => setBookingNote(e.target.value)}
              />
            </div>
          </div>

        {/* Discount Section */}
        <div className="discount-section">
          <label className="form-label">Discount</label>
          <div className="discount-toggle">
            <button
              className={`toggle-button ${discountType === 'fix' ? 'active' : ''}`}
              onClick={() => setDiscountType('fix')}
            >
              Fix
            </button>
            <button
              className={`toggle-button ${discountType === '%' ? 'active' : ''}`}
              onClick={() => setDiscountType('%')}
            >
              %
            </button>
          </div>
          <input
            type="number"
            className="form-input discount-input"
            placeholder={discountType === 'fix' ? 'Discount Amount (₹)' : 'Discount Percentage (%)'}
            value={discountAmount}
            onChange={(e) => {
              const value = parseFloat(e.target.value) || 0
              setDiscountAmount(value)
              
              // Phase 5: Check discount limit
              if (discountType === '%' && user) {
                const maxDiscount = getMaxDiscountPercent()
                const subtotal = calculateSubtotal()
                const discountPercent = value
                
                if (discountPercent > maxDiscount && subtotal > 0) {
                  // Will need approval
                  setShowApprovalForm(true)
                } else {
                  setShowApprovalForm(false)
                  setPendingApproval(null)
                }
              }
            }}
          />
          {user && discountType === '%' && (
            <small className="discount-limit-info">
              Max discount for {user.role}: {getMaxDiscountPercent()}%
            </small>
          )}
          {pendingApproval && (
            <div className="approval-pending-notice">
              ⚠️ Discount approval pending. Cannot checkout until approved.
            </div>
          )}
        </div>

          {/* Mode of Payment */}
          <div className="payment-section">
            <label className="form-label">Mode of payment *</label>
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
              <button
                className={`payment-pill ${paymentMode === 'wallet' ? 'active' : ''}`}
                onClick={() => setPaymentMode('wallet')}
              >
                Wallet
              </button>
            </div>
          </div>

          {/* Summary Section */}
          <div className="summary-section">
            <div className="summary-values">
              <div className="summary-row">
                <span className="summary-label">Wallet Amount:</span>
                <span className="summary-value">
                  ₹ {selectedCustomer ? (selectedCustomer.wallet_balance || 0).toFixed(2) : '0.00'}
                </span>
              </div>
              <div className="summary-row">
                <span className="summary-label">Subtotal:</span>
                <span className="summary-value">₹ {calculateSubtotal().toFixed(2)}</span>
              </div>
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
                <span className="summary-value final-value">₹ {calculateFinalAmount().toFixed(0)}</span>
              </div>
            </div>
          </div>

          {/* Bottom Buttons */}
          <div className="action-buttons">
            <button className="reset-button" onClick={handleReset}>Reset</button>
            <button 
              className="checkout-button" 
              onClick={handleCheckout}
              disabled={pendingApproval && pendingApproval.approval_status === 'pending'}
            >
              {pendingApproval && pendingApproval.approval_status === 'pending' 
                ? 'Approval Pending...' 
                : 'Checkout'}
            </button>
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
    </div>
    </PageTransition>
  )
}

export default QuickSale

