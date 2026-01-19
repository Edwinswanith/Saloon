import React, { useState, useEffect, Suspense, lazy } from 'react'
import { Toaster } from 'react-hot-toast'
import { ConfigProvider } from 'antd'
import { antdTheme } from './config/antd-theme'
import { AuthProvider, useAuth, RequireRole } from './contexts/AuthContext'
import { AnimatePresence } from 'framer-motion'

// Keep Login, Sidebar, GlobalHeader eager (needed immediately)
import Login from './components/Login'
import Sidebar from './components/Sidebar'
import GlobalHeader from './components/GlobalHeader'
import './App.css'

// PERFORMANCE OPTIMIZATION: Lazy load all page components
// These will be loaded on-demand when the user navigates to them
const Dashboard = lazy(() => import('./components/Dashboard'))
const QuickSale = lazy(() => import('./components/QuickSale'))
const CashRegister = lazy(() => import('./components/CashRegister'))
const Appointment = lazy(() => import('./components/Appointment'))
const CustomerList = lazy(() => import('./components/CustomerList'))
const LeadManagement = lazy(() => import('./components/LeadManagement'))
const MissedEnquiries = lazy(() => import('./components/MissedEnquiries'))
const CustomerLifecycleReport = lazy(() => import('./components/CustomerLifecycleReport'))
const Feedback = lazy(() => import('./components/Feedback'))
const ServiceRecovery = lazy(() => import('./components/ServiceRecovery'))
const DiscountApprovals = lazy(() => import('./components/DiscountApprovals'))
const ApprovalCodes = lazy(() => import('./components/ApprovalCodes'))
const Inventory = lazy(() => import('./components/Inventory'))
const ReportsAnalytics = lazy(() => import('./components/ReportsAnalytics'))
const Service = lazy(() => import('./components/Service'))
const Package = lazy(() => import('./components/Package'))
const Product = lazy(() => import('./components/Product'))
const Prepaid = lazy(() => import('./components/Prepaid'))
const Settings = lazy(() => import('./components/Settings'))
const Membership = lazy(() => import('./components/Membership'))
const ReferralProgram = lazy(() => import('./components/ReferralProgram'))
const Tax = lazy(() => import('./components/Tax'))
const Manager = lazy(() => import('./components/Manager'))
const OwnerSettings = lazy(() => import('./components/OwnerSettings'))
const Staffs = lazy(() => import('./components/Staffs'))
const StaffAttendance = lazy(() => import('./components/StaffAttendance'))
const StaffTempAssignment = lazy(() => import('./components/StaffTempAssignment'))
const AssetManagement = lazy(() => import('./components/AssetManagement'))
const Expense = lazy(() => import('./components/Expense'))
const ServiceSalesAnalysis = lazy(() => import('./components/ServiceSalesAnalysis'))
const ListOfBills = lazy(() => import('./components/ListOfBills'))
const ListOfDeletedBills = lazy(() => import('./components/ListOfDeletedBills'))
const SalesByServiceGroup = lazy(() => import('./components/SalesByServiceGroup'))
const PrepaidPackageClients = lazy(() => import('./components/PrepaidPackageClients'))
const MembershipClients = lazy(() => import('./components/MembershipClients'))
const StaffIncentiveReport = lazy(() => import('./components/StaffIncentiveReport'))
const ExpenseReport = lazy(() => import('./components/ExpenseReport'))
const InventoryReport = lazy(() => import('./components/InventoryReport'))
const StaffCombinedReport = lazy(() => import('./components/StaffCombinedReport'))
const BusinessGrowthTrendAnalysis = lazy(() => import('./components/BusinessGrowthTrendAnalysis'))
const StaffPerformanceAnalysis = lazy(() => import('./components/StaffPerformanceAnalysis'))
const PeriodPerformanceSummary = lazy(() => import('./components/PeriodPerformanceSummary'))
const ClientValueLoyaltyReport = lazy(() => import('./components/ClientValueLoyaltyReport'))
const ServiceProductPerformance = lazy(() => import('./components/ServiceProductPerformance'))

// Loading fallback component for lazy-loaded pages
const PageLoader = () => (
  <div className="page-loading" style={{
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    height: '100%',
    minHeight: '400px'
  }}>
    <div className="loading-spinner-large"></div>
  </div>
)

// Main application content (protected - requires authentication)
function AppContent() {
  const [activePage, setActivePage] = useState('dashboard')
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(() => {
    // Load from localStorage
    const saved = localStorage.getItem('sidebarCollapsed')
    return saved ? JSON.parse(saved) : false
  })
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false)
  const { isAuthenticated, loading, user } = useAuth()

  // Save sidebar state to localStorage
  useEffect(() => {
    localStorage.setItem('sidebarCollapsed', JSON.stringify(isSidebarCollapsed))
  }, [isSidebarCollapsed])

  // Close mobile sidebar when page changes
  useEffect(() => {
    setIsMobileSidebarOpen(false)
  }, [activePage])

  // Handle body scroll lock when mobile sidebar is open
  useEffect(() => {
    if (isMobileSidebarOpen) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = ''
    }
    return () => {
      document.body.style.overflow = ''
    }
  }, [isMobileSidebarOpen])

  const toggleSidebar = () => {
    setIsSidebarCollapsed((prev) => !prev)
  }

  const toggleMobileSidebar = () => {
    setIsMobileSidebarOpen((prev) => !prev)
  }

  const closeMobileSidebar = () => {
    setIsMobileSidebarOpen(false)
  }

  // Listen for navigation events - must be called before any conditional returns
  useEffect(() => {
    const handleNavigate = (event) => {
      if (event.detail && event.detail.page) {
        setActivePage(event.detail.page)
      }
    }
    window.addEventListener('navigateToPage', handleNavigate)
    return () => window.removeEventListener('navigateToPage', handleNavigate)
  }, [])

  // Show loading spinner while checking authentication
  if (loading) {
    return (
      <div className="app-loading">
        <div className="loading-container">
          <div className="loading-spinner-large"></div>
          <p className="loading-text">Loading Saloon Management System...</p>
        </div>
      </div>
    )
  }

  // Show login screen if not authenticated
  if (!isAuthenticated) {
    return <Login onLoginSuccess={() => setActivePage('dashboard')} />
  }

  // Render authenticated app
  return (
    <div className={`app ${isSidebarCollapsed ? 'sidebar-collapsed' : ''} ${isMobileSidebarOpen ? 'mobile-sidebar-open' : ''}`}>
      <Sidebar
        activePage={activePage}
        setActivePage={setActivePage}
        onToggle={toggleSidebar}
        isCollapsed={isSidebarCollapsed}
        isMobileOpen={isMobileSidebarOpen}
        onMobileClose={closeMobileSidebar}
      />
      <GlobalHeader onMobileMenuToggle={toggleMobileSidebar} />
      <main className="main-content">
        {/* PERFORMANCE: Suspense wrapper for lazy-loaded components */}
        <Suspense fallback={<PageLoader />}>
          <AnimatePresence mode="wait">
            {activePage === 'dashboard' && <Dashboard key="dashboard" />}
            {activePage === 'quick-sale' && <QuickSale key="quick-sale" />}
            {activePage === 'cash-register' && <CashRegister key="cash-register" />}
            {activePage === 'appointment' && <Appointment key="appointment" setActivePage={setActivePage} />}
            {activePage === 'customer-list' && <CustomerList key="customer-list" />}
            {activePage === 'lead-management' && <LeadManagement key="lead-management" />}
            {activePage === 'missed-enquiries' && <MissedEnquiries key="missed-enquiries" />}
            {activePage === 'customer-lifecycle' && (
              <RequireRole roles={['manager', 'owner']}>
                <CustomerLifecycleReport key="customer-lifecycle" />
              </RequireRole>
            )}
            {activePage === 'feedback' && <Feedback key="feedback" />}
            {activePage === 'service-recovery' && (
              <RequireRole roles={['manager', 'owner']}>
                <ServiceRecovery key="service-recovery" />
              </RequireRole>
            )}
            {activePage === 'discount-approvals' && (
              <RequireRole roles={['owner']}>
                <DiscountApprovals key="discount-approvals" />
              </RequireRole>
            )}
            {activePage === 'approval-codes' && (
              <RequireRole roles={['owner']}>
                <ApprovalCodes key="approval-codes" />
              </RequireRole>
            )}
            {activePage === 'inventory' && <Inventory key="inventory" />}
            {activePage === 'reports' && (
              <RequireRole roles={['manager', 'owner']}>
                <ReportsAnalytics key="reports" setActivePage={setActivePage} />
              </RequireRole>
            )}
            {activePage === 'reports-analytics' && (
              <RequireRole roles={['manager', 'owner']}>
                <ReportsAnalytics key="reports-analytics" setActivePage={setActivePage} initialTab="analytics" />
              </RequireRole>
            )}
            {activePage === 'analytics' && (
              <RequireRole roles={['manager', 'owner']}>
                <ReportsAnalytics key="analytics" setActivePage={setActivePage} initialTab="analytics" />
              </RequireRole>
            )}
            {activePage === 'service-sales-analysis' && (
              <RequireRole roles={['manager', 'owner']}>
                <ServiceSalesAnalysis key="service-sales-analysis" setActivePage={setActivePage} />
              </RequireRole>
            )}
            {activePage === 'list-of-bills' && (
              <RequireRole roles={['manager', 'owner']}>
                <ListOfBills key="list-of-bills" setActivePage={setActivePage} />
              </RequireRole>
            )}
            {activePage === 'list-of-deleted-bills' && (
              <RequireRole roles={['manager', 'owner']}>
                <ListOfDeletedBills key="list-of-deleted-bills" setActivePage={setActivePage} />
              </RequireRole>
            )}
            {activePage === 'sales-by-service-group' && (
              <RequireRole roles={['manager', 'owner']}>
                <SalesByServiceGroup key="sales-by-service-group" setActivePage={setActivePage} />
              </RequireRole>
            )}
            {activePage === 'prepaid-package-clients' && (
              <RequireRole roles={['manager', 'owner']}>
                <PrepaidPackageClients key="prepaid-package-clients" setActivePage={setActivePage} />
              </RequireRole>
            )}
            {activePage === 'membership-clients' && (
              <RequireRole roles={['manager', 'owner']}>
                <MembershipClients key="membership-clients" setActivePage={setActivePage} />
              </RequireRole>
            )}
            {activePage === 'staff-incentive-report' && (
              <RequireRole roles={['manager', 'owner']}>
                <StaffIncentiveReport key="staff-incentive-report" setActivePage={setActivePage} />
              </RequireRole>
            )}
            {activePage === 'expense-report' && (
              <RequireRole roles={['manager', 'owner']}>
                <ExpenseReport key="expense-report" setActivePage={setActivePage} />
              </RequireRole>
            )}
            {activePage === 'inventory-report' && (
              <RequireRole roles={['manager', 'owner']}>
                <InventoryReport key="inventory-report" setActivePage={setActivePage} />
              </RequireRole>
            )}
            {activePage === 'staff-combined-report' && (
              <RequireRole roles={['manager', 'owner']}>
                <StaffCombinedReport key="staff-combined-report" setActivePage={setActivePage} />
              </RequireRole>
            )}
            {activePage === 'business-growth-trend-analysis' && (
              <RequireRole roles={['manager', 'owner']}>
                <BusinessGrowthTrendAnalysis key="business-growth-trend-analysis" setActivePage={setActivePage} />
              </RequireRole>
            )}
            {activePage === 'staff-performance-analysis' && (
              <RequireRole roles={['manager', 'owner']}>
                <StaffPerformanceAnalysis key="staff-performance-analysis" setActivePage={setActivePage} />
              </RequireRole>
            )}
            {activePage === 'period-performance-summary' && (
              <RequireRole roles={['manager', 'owner']}>
                <PeriodPerformanceSummary key="period-performance-summary" setActivePage={setActivePage} />
              </RequireRole>
            )}
            {activePage === 'client-value-loyalty-report' && (
              <RequireRole roles={['manager', 'owner']}>
                <ClientValueLoyaltyReport key="client-value-loyalty-report" setActivePage={setActivePage} />
              </RequireRole>
            )}
            {activePage === 'service-product-performance' && (
              <RequireRole roles={['manager', 'owner']}>
                <ServiceProductPerformance key="service-product-performance" setActivePage={setActivePage} />
              </RequireRole>
            )}
            {activePage === 'service' && <Service key="service" />}
            {activePage === 'package' && <Package key="package" />}
            {activePage === 'product' && <Product key="product" />}
            {activePage === 'prepaid' && <Prepaid key="prepaid" />}
            {activePage === 'settings' && (
              <RequireRole roles={['manager', 'owner']}>
                <Settings key="settings" setActivePage={setActivePage} />
              </RequireRole>
            )}
            {activePage === 'membership' && (
              <RequireRole roles={['owner']}>
                <Membership key="membership" />
              </RequireRole>
            )}
            {activePage === 'referral-program' && (
              <RequireRole roles={['owner']}>
                <ReferralProgram key="referral-program" />
              </RequireRole>
            )}
            {activePage === 'tax' && (
              <RequireRole roles={['owner']}>
                <Tax key="tax" />
              </RequireRole>
            )}
            {activePage === 'manager' && (
              <RequireRole roles={['owner']}>
                <Manager key="manager" />
              </RequireRole>
            )}
            {activePage === 'owner-settings' && (
              <RequireRole roles={['owner']}>
                <OwnerSettings key="owner-settings" />
              </RequireRole>
            )}
            {activePage === 'staffs' && (
              <RequireRole roles={['manager', 'owner']}>
                <Staffs key="staffs" />
              </RequireRole>
            )}
            {activePage === 'staff-attendance' && (
              <RequireRole roles={['manager', 'owner']}>
                <StaffAttendance key="staff-attendance" />
              </RequireRole>
            )}
            {activePage === 'staff-temp-assignment' && (
              <RequireRole roles={['manager', 'owner']}>
                <StaffTempAssignment key="staff-temp-assignment" />
              </RequireRole>
            )}
            {activePage === 'asset-management' && (
              <RequireRole roles={['manager', 'owner']}>
                <AssetManagement key="asset-management" />
              </RequireRole>
            )}
            {activePage === 'expense' && (
              <RequireRole roles={['manager', 'owner']}>
                <Expense key="expense" />
              </RequireRole>
            )}
          </AnimatePresence>
        </Suspense>
      </main>
    </div>
  )
}

// Root App component wrapped with AuthProvider and Ant Design ConfigProvider
function App() {
  return (
    <ConfigProvider theme={antdTheme}>
      <AuthProvider>
        <Toaster
          position="top-right"
          toastOptions={{
            // Default options
            duration: 3000,
            style: {
              background: '#fff',
              color: '#363636',
              padding: '16px',
              borderRadius: '8px',
              boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
            },
            // Success toast
            success: {
              duration: 3000,
              iconTheme: {
                primary: '#10b981',
                secondary: '#fff',
              },
            },
            // Error toast
            error: {
              duration: 4000,
              iconTheme: {
                primary: '#ef4444',
                secondary: '#fff',
              },
            },
          }}
        />
        <AppContent />
      </AuthProvider>
    </ConfigProvider>
  )
}

export default App
