import React, { useState } from 'react'
import Sidebar from './components/Sidebar'
import QuickSale from './components/QuickSale'
import Dashboard from './components/Dashboard'
import CashRegister from './components/CashRegister'
import Appointment from './components/Appointment'
import CustomerList from './components/CustomerList'
import LeadManagement from './components/LeadManagement'
import Feedback from './components/Feedback'
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
import Staffs from './components/Staffs'
import StaffAttendance from './components/StaffAttendance'
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
import './App.css'

function App() {
  const [activePage, setActivePage] = useState('dashboard')

  return (
    <div className="app">
      <Sidebar activePage={activePage} setActivePage={setActivePage} />
      <main className="main-content">
        {activePage === 'dashboard' && <Dashboard />}
        {activePage === 'quick-sale' && <QuickSale />}
        {activePage === 'cash-register' && <CashRegister />}
        {activePage === 'appointment' && <Appointment />}
        {activePage === 'customer-list' && <CustomerList />}
        {activePage === 'lead-management' && <LeadManagement />}
        {activePage === 'feedback' && <Feedback />}
        {activePage === 'inventory' && <Inventory />}
        {activePage === 'reports' && <ReportsAnalytics setActivePage={setActivePage} />}
        {activePage === 'reports-analytics' && <ReportsAnalytics setActivePage={setActivePage} />}
        {activePage === 'analytics' && <ReportsAnalytics setActivePage={setActivePage} />}
        {activePage === 'service-sales-analysis' && <ServiceSalesAnalysis setActivePage={setActivePage} />}
        {activePage === 'list-of-bills' && <ListOfBills setActivePage={setActivePage} />}
        {activePage === 'list-of-deleted-bills' && <ListOfDeletedBills setActivePage={setActivePage} />}
        {activePage === 'sales-by-service-group' && <SalesByServiceGroup setActivePage={setActivePage} />}
        {activePage === 'prepaid-package-clients' && <PrepaidPackageClients setActivePage={setActivePage} />}
        {activePage === 'membership-clients' && <MembershipClients setActivePage={setActivePage} />}
        {activePage === 'staff-incentive-report' && <StaffIncentiveReport setActivePage={setActivePage} />}
        {activePage === 'expense-report' && <ExpenseReport setActivePage={setActivePage} />}
        {activePage === 'inventory-report' && <InventoryReport setActivePage={setActivePage} />}
        {activePage === 'staff-combined-report' && <StaffCombinedReport setActivePage={setActivePage} />}
        {activePage === 'business-growth-trend-analysis' && <BusinessGrowthTrendAnalysis setActivePage={setActivePage} />}
        {activePage === 'staff-performance-analysis' && <StaffPerformanceAnalysis setActivePage={setActivePage} />}
        {activePage === 'period-performance-summary' && <PeriodPerformanceSummary setActivePage={setActivePage} />}
        {activePage === 'client-value-loyalty-report' && <ClientValueLoyaltyReport setActivePage={setActivePage} />}
        {activePage === 'service' && <Service />}
        {activePage === 'package' && <Package />}
        {activePage === 'product' && <Product />}
        {activePage === 'prepaid' && <Prepaid />}
        {activePage === 'settings' && <Settings setActivePage={setActivePage} />}
        {activePage === 'membership' && <Membership />}
        {activePage === 'loyalty-program' && <LoyaltyProgram />}
        {activePage === 'referral-program' && <ReferralProgram />}
        {activePage === 'tax' && <Tax />}
        {activePage === 'manager' && <Manager />}
        {activePage === 'staffs' && <Staffs />}
        {activePage === 'staff-attendance' && <StaffAttendance />}
        {activePage === 'asset-management' && <AssetManagement />}
        {activePage === 'expense' && <Expense />}
      </main>
    </div>
  )
}

export default App

