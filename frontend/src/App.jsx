import React, { useState, useEffect } from 'react'
import { Toaster } from 'react-hot-toast'
import { ConfigProvider } from 'antd'
import { antdTheme } from './config/antd-theme'
import { AuthProvider, useAuth, RequireRole } from './contexts/AuthContext'
import { AnimatePresence } from 'framer-motion'
import Login from './components/Login'
import Sidebar from './components/Sidebar'
import QuickSale from './components/QuickSale'
import Dashboard from './components/Dashboard'
import CashRegister from './components/CashRegister'
import Appointment from './components/Appointment'
import CustomerList from './components/CustomerList'
import LeadManagement from './components/LeadManagement'
import MissedEnquiries from './components/MissedEnquiries'
import CustomerLifecycleReport from './components/CustomerLifecycleReport'
import Feedback from './components/Feedback'
import ServiceRecovery from './components/ServiceRecovery'
import DiscountApprovals from './components/DiscountApprovals'
import ApprovalCodes from './components/ApprovalCodes'
import Inventory from './components/Inventory'
import ReportsAnalytics from './components/ReportsAnalytics'
import Service from './components/Service'
import Package from './components/Package'
import Product from './components/Product'
import Prepaid from './components/Prepaid'
import Settings from './components/Settings'
import Membership from './components/Membership'
import LoyaltyProgram from './components/LoyaltyProgram'
import ReferralProgram from './components/ReferralProgram'
import Tax from './components/Tax'
import Manager from './components/Manager'
import OwnerSettings from './components/OwnerSettings'
import Staffs from './components/Staffs'
import StaffAttendance from './components/StaffAttendance'
import StaffTempAssignment from './components/StaffTempAssignment'
import AssetManagement from './components/AssetManagement'
import Expense from './components/Expense'
import ServiceSalesAnalysis from './components/ServiceSalesAnalysis'
import ListOfBills from './components/ListOfBills'
import ListOfDeletedBills from './components/ListOfDeletedBills'
import SalesByServiceGroup from './components/SalesByServiceGroup'
import PrepaidPackageClients from './components/PrepaidPackageClients'
import MembershipClients from './components/MembershipClients'
import StaffIncentiveReport from './components/StaffIncentiveReport'
import ExpenseReport from './components/ExpenseReport'
import InventoryReport from './components/InventoryReport'
import StaffCombinedReport from './components/StaffCombinedReport'
import BusinessGrowthTrendAnalysis from './components/BusinessGrowthTrendAnalysis'
import StaffPerformanceAnalysis from './components/StaffPerformanceAnalysis'
import PeriodPerformanceSummary from './components/PeriodPerformanceSummary'
import ClientValueLoyaltyReport from './components/ClientValueLoyaltyReport'
import GlobalHeader from './components/GlobalHeader'
import './App.css'

// Main application content (protected - requires authentication)
function AppContent() {
  const [activePage, setActivePage] = useState('dashboard')
  const { isAuthenticated, loading, user } = useAuth()

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
          <p className="loading-text">Loading Salon Management System...</p>
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
    <div className="app">
      <Sidebar
        activePage={activePage}
        setActivePage={setActivePage}
        user={user}
      />
      <GlobalHeader />
      <main className="main-content">
        <AnimatePresence mode="wait">
          {activePage === 'dashboard' && <Dashboard key="dashboard" />}
          {activePage === 'quick-sale' && <QuickSale key="quick-sale" />}
        {activePage === 'cash-register' && <CashRegister />}
        {activePage === 'appointment' && <Appointment setActivePage={setActivePage} />}
        {activePage === 'customer-list' && <CustomerList />}
        {activePage === 'lead-management' && <LeadManagement />}
        {activePage === 'missed-enquiries' && <MissedEnquiries />}
        {activePage === 'customer-lifecycle' && (
          <RequireRole roles={['manager', 'owner']}>
            <CustomerLifecycleReport />
          </RequireRole>
        )}
        {activePage === 'feedback' && <Feedback />}
        {activePage === 'service-recovery' && (
          <RequireRole roles={['manager', 'owner']}>
            <ServiceRecovery />
          </RequireRole>
        )}
        {activePage === 'discount-approvals' && (
          <RequireRole roles={['owner']}>
            <DiscountApprovals />
          </RequireRole>
        )}
        {activePage === 'approval-codes' && (
          <RequireRole roles={['owner']}>
            <ApprovalCodes />
          </RequireRole>
        )}
        {activePage === 'inventory' && <Inventory />}
        {activePage === 'reports' && (
          <RequireRole roles={['manager', 'owner']}>
            <ReportsAnalytics setActivePage={setActivePage} />
          </RequireRole>
        )}
        {activePage === 'reports-analytics' && (
          <RequireRole roles={['manager', 'owner']}>
            <ReportsAnalytics setActivePage={setActivePage} />
          </RequireRole>
        )}
        {activePage === 'analytics' && (
          <RequireRole roles={['manager', 'owner']}>
            <ReportsAnalytics setActivePage={setActivePage} />
          </RequireRole>
        )}
        {activePage === 'service-sales-analysis' && (
          <RequireRole roles={['manager', 'owner']}>
            <ServiceSalesAnalysis setActivePage={setActivePage} />
          </RequireRole>
        )}
        {activePage === 'list-of-bills' && (
          <RequireRole roles={['manager', 'owner']}>
            <ListOfBills setActivePage={setActivePage} />
          </RequireRole>
        )}
        {activePage === 'list-of-deleted-bills' && (
          <RequireRole roles={['manager', 'owner']}>
            <ListOfDeletedBills setActivePage={setActivePage} />
          </RequireRole>
        )}
        {activePage === 'sales-by-service-group' && (
          <RequireRole roles={['manager', 'owner']}>
            <SalesByServiceGroup setActivePage={setActivePage} />
          </RequireRole>
        )}
        {activePage === 'prepaid-package-clients' && (
          <RequireRole roles={['manager', 'owner']}>
            <PrepaidPackageClients setActivePage={setActivePage} />
          </RequireRole>
        )}
        {activePage === 'membership-clients' && (
          <RequireRole roles={['manager', 'owner']}>
            <MembershipClients setActivePage={setActivePage} />
          </RequireRole>
        )}
        {activePage === 'staff-incentive-report' && (
          <RequireRole roles={['manager', 'owner']}>
            <StaffIncentiveReport setActivePage={setActivePage} />
          </RequireRole>
        )}
        {activePage === 'expense-report' && (
          <RequireRole roles={['manager', 'owner']}>
            <ExpenseReport setActivePage={setActivePage} />
          </RequireRole>
        )}
        {activePage === 'inventory-report' && (
          <RequireRole roles={['manager', 'owner']}>
            <InventoryReport setActivePage={setActivePage} />
          </RequireRole>
        )}
        {activePage === 'staff-combined-report' && (
          <RequireRole roles={['manager', 'owner']}>
            <StaffCombinedReport setActivePage={setActivePage} />
          </RequireRole>
        )}
        {activePage === 'business-growth-trend-analysis' && (
          <RequireRole roles={['manager', 'owner']}>
            <BusinessGrowthTrendAnalysis setActivePage={setActivePage} />
          </RequireRole>
        )}
        {activePage === 'staff-performance-analysis' && (
          <RequireRole roles={['manager', 'owner']}>
            <StaffPerformanceAnalysis setActivePage={setActivePage} />
          </RequireRole>
        )}
        {activePage === 'period-performance-summary' && (
          <RequireRole roles={['manager', 'owner']}>
            <PeriodPerformanceSummary setActivePage={setActivePage} />
          </RequireRole>
        )}
        {activePage === 'client-value-loyalty-report' && (
          <RequireRole roles={['manager', 'owner']}>
            <ClientValueLoyaltyReport setActivePage={setActivePage} />
          </RequireRole>
        )}
        {activePage === 'service' && <Service />}
        {activePage === 'package' && <Package />}
        {activePage === 'product' && <Product />}
        {activePage === 'prepaid' && <Prepaid />}
        {activePage === 'settings' && (
          <RequireRole roles={['manager', 'owner']}>
            <Settings setActivePage={setActivePage} />
          </RequireRole>
        )}
        {activePage === 'membership' && (
          <RequireRole roles={['owner']}>
            <Membership />
          </RequireRole>
        )}
        {activePage === 'loyalty-program' && (
          <RequireRole roles={['owner']}>
            <LoyaltyProgram />
          </RequireRole>
        )}
        {activePage === 'referral-program' && (
          <RequireRole roles={['owner']}>
            <ReferralProgram />
          </RequireRole>
        )}
        {activePage === 'tax' && (
          <RequireRole roles={['owner']}>
            <Tax />
          </RequireRole>
        )}
        {activePage === 'manager' && (
          <RequireRole roles={['owner']}>
            <Manager />
          </RequireRole>
        )}
        {activePage === 'owner-settings' && (
          <RequireRole roles={['owner']}>
            <OwnerSettings />
          </RequireRole>
        )}
        {activePage === 'staffs' && (
          <RequireRole roles={['manager', 'owner']}>
            <Staffs />
          </RequireRole>
        )}
        {activePage === 'staff-attendance' && (
          <RequireRole roles={['manager', 'owner']}>
            <StaffAttendance />
          </RequireRole>
        )}
        {activePage === 'staff-temp-assignment' && (
          <RequireRole roles={['manager', 'owner']}>
            <StaffTempAssignment />
          </RequireRole>
        )}
        {activePage === 'asset-management' && (
          <RequireRole roles={['manager', 'owner']}>
            <AssetManagement />
          </RequireRole>
        )}
        {activePage === 'expense' && (
          <RequireRole roles={['manager', 'owner']}>
            <Expense />
          </RequireRole>
        )}
        </AnimatePresence>
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

