---
name: Frontend Project Structure Analysis
overview: Complete breakdown of the Saloon frontend project structure including sidebar navigation, modals, UI sections, component organization, and layout architecture.
todos: []
---

# Frontend Project Structure Analysis - Saloon Management System

## 1. Application Architecture

### Main Layout Structure

```
App.jsx (Root)
├── AuthProvider (Context)
├── ConfigProvider (Ant Design)
├── Toaster (Notifications)
└── AppContent
    ├── Sidebar (Navigation)
    ├── GlobalHeader (Top Bar)
    └── main-content (Page Container)
        └── Page Components (Conditional Rendering)
```

**Key Files:**

- `frontend/src/App.jsx` - Main application router and layout
- `frontend/src/main.jsx` - Entry point
- `frontend/src/App.css` - Main layout styles
- `frontend/src/components/GlobalHeader.jsx` - Top navigation bar
- `frontend/src/components/Sidebar.jsx` - Left navigation sidebar

---

## 2. Sidebar Navigation Structure

### Sidebar Component: `frontend/src/components/Sidebar.jsx`

**Logo Section:**

- Logo image: `/logo/priyanka logo.png`
- Collapsible toggle button

**Navigation Sections:**

#### **Dashboard** (Standalone)

- Dashboard

#### **BILLING Section**

1. Quick Sale
2. Cash Register
3. Appointment
4. Customers (Expandable Submenu)

   - Customer List
   - Lead Management
   - Missed Enquiries
   - Feedback
   - Service Recovery (Manager/Owner only)

5. Inventory
6. Discount Approvals (Owner only)
7. Approval Codes (Owner only)

#### **ANALYTICS Section**

1. Reports & Analytics (Manager/Owner only)

#### **MASTER Section**

1. Saloon Settings (Expandable Submenu)

   - Service
   - Package
   - Product
   - Prepaid
   - Settings (Manager/Owner only)

2. Staffs (Manager/Owner only)
3. Staff Attendance (Manager/Owner only)
4. Staff Reassignment (Manager/Owner only)
5. Asset Management (Manager/Owner only)
6. Expense (Manager/Owner only)

**Sidebar Features:**

- Collapsible (stored in localStorage)
- Mobile responsive with backdrop overlay
- Role-based visibility (`requiresRole` property)
- Expandable submenus for Customers and Saloon Settings
- Active page highlighting

---

## 3. Global Header Component

### GlobalHeader: `frontend/src/components/GlobalHeader.jsx`

**Left Section:**

- Mobile hamburger menu button (only on mobile)

**Center Section:**

- Banner text: "Priyanka Nature Cure"

**Right Section:**

1. BranchSelector component
2. Logout button (with confirmation modal)
3. Notifications bell icon
4. Profile icon/avatar (opens Profile modal)

**Modals in GlobalHeader:**

- Profile Modal (`Profile.jsx`)
- Logout Confirmation Modal (inline)

---

## 4. Modal/Popup Components

### Modal Patterns Found:

#### **1. Profile Modal** (`frontend/src/components/Profile.jsx`)

- **Trigger:** Profile icon in GlobalHeader
- **Features:**
  - User profile information display/edit
  - Header image upload
  - Personal information editing
  - Logout functionality
- **CSS Classes:** `profile-overlay`, `profile-modal`

#### **2. Customer Details Modal** (`frontend/src/components/Top10Customers.jsx`)

- **Trigger:** "View" button in Top 10 Customers table
- **Features:**
  - Customer information display
  - Top 10 customer statistics
  - Additional information (membership, last visit)
- **CSS Classes:** `customer-modal-overlay`, `customer-modal-content`

#### **3. Offering Clients Modal** (`frontend/src/components/Dashboard.jsx`)

- **Trigger:** "View Clients" button in Top Offerings
- **Features:**
  - List of clients for a specific offering
- **CSS Classes:** `customer-modal-overlay`, `customer-modal-content`

#### **4. Staff Details Modal** (`frontend/src/components/Dashboard.jsx`)

- **Trigger:** Staff performance chart click
- **Features:**
  - Staff performance details
- **CSS Classes:** Custom modal classes

#### **5. QuickSale Modals** (`frontend/src/components/QuickSale.jsx`)

Multiple modals for:

- Inventory selection (`showInventoryModal`)
- Bill activity (`showBillActivityModal`)
- Package selection (`showPackageModal`)
- Product selection (`showProductModal`)
- Prepaid selection (`showPrepaidModal`)
- Membership selection (`showMembershipModal`)
- Invoice preview (`showInvoiceModal`)
- Approval form (`showApprovalForm`)
- New customer form (`new-customer-modal`)

#### **6. Service/Product/Package Modals**

- **Add/Edit Service Modal** (`frontend/src/components/Service.jsx`)
- **Add/Edit Product Modal** (`frontend/src/components/Product.jsx`)
- **Add/Edit Package Modal** (`frontend/src/components/Package.jsx`)
- **CSS Classes:** `modal-overlay`, `modal-content`

#### **7. Logout Confirmation Modal** (`frontend/src/components/GlobalHeader.jsx`)

- **Trigger:** Logout button click
- **CSS Classes:** `logout-overlay`, `logout-modal`

#### **8. Import Modal** (`frontend/src/components/Service.jsx`)

- **Trigger:** Import button
- **Features:** Service import functionality

**Common Modal CSS Patterns:**

- Overlay: `modal-overlay`, `customer-modal-overlay`, `profile-overlay`
- Content: `modal-content`, `customer-modal-content`, `profile-modal`
- Header: `modal-header`, `customer-modal-header`
- Body: `modal-body`, `customer-modal-body`
- Close: `modal-close-btn`, `customer-modal-close`

---

## 5. Major UI Sections & Components

### **Dashboard** (`frontend/src/components/Dashboard.jsx`)

**Sections:**

1. **Header** - Title and filters (month/year selector)
2. **Tabs** - Sales / Staff
3. **Sales Tab Content:**

   - DashboardStatsCards (Revenue, Transactions, etc.)
   - SalesInsights (Tab-based: Top Moving Items, Top 10 Customers, Top 10 Offerings)
   - Revenue Breakdown (Pie Chart)
   - Payment Distribution
   - Right Sidebar:
     - Revenue & Payments
     - Client Funnel
     - Client Source
     - Alerts

4. **Staff Tab Content:**

   - Staff Performance Panel (Bar Chart)
   - Top Performer Card
   - Staff Leaderboard

### **QuickSale** (`frontend/src/components/QuickSale.jsx`)

**Sections:**

- Customer selection/search
- Service/Product/Package selection
- Bill summary
- Payment processing
- Multiple modals for item selection

### **Reports & Analytics** (`frontend/src/components/ReportsAnalytics.jsx`)

**Tabs:**

1. **Operational Reports:**

   - Service Sales Analysis
   - List of Bills
   - List of Deleted Bills
   - Sales by Service Group
   - Prepaid Package Clients
   - Membership Clients
   - Staff Incentive Report
   - Expense Report
   - Inventory Report
   - Staff Combined Report
   - (11 total reports)

2. **Analytics Dashboard:**

   - Business Growth & Trend Analysis
   - Staff Performance Analysis
   - Period Performance Summary
   - Client Value & Loyalty Report
   - Service & Product Performance
   - (9 total analytics)

### **Master Data Management:**

- **Service** (`frontend/src/components/Service.jsx`) - Service groups and services
- **Package** (`frontend/src/components/Package.jsx`) - Package management
- **Product** (`frontend/src/components/Product.jsx`) - Product/inventory management
- **Prepaid** (`frontend/src/components/Prepaid.jsx`) - Prepaid packages
- **Staffs** (`frontend/src/components/Staffs.jsx`) - Staff management
- **Settings** (`frontend/src/components/Settings.jsx`) - System settings

### **Customer Management:**

- **CustomerList** (`frontend/src/components/CustomerList.jsx`)
- **LeadManagement** (`frontend/src/components/LeadManagement.jsx`)
- **MissedEnquiries** (`frontend/src/components/MissedEnquiries.jsx`)
- **Feedback** (`frontend/src/components/Feedback.jsx`)

### **Financial Management:**

- **CashRegister** (`frontend/src/components/CashRegister.jsx`)
- **Expense** (`frontend/src/components/Expense.jsx`)
- **DiscountApprovals** (`frontend/src/components/DiscountApprovals.jsx`)

### **Staff Management:**

- **StaffAttendance** (`frontend/src/components/StaffAttendance.jsx`)
- **StaffTempAssignment** (`frontend/src/components/StaffTempAssignment.jsx`)

---

## 6. Component Organization

### **Directory Structure:**

```
frontend/src/
├── components/          (63 component files)
│   ├── shared/          (Shared utilities)
│   │   ├── EmptyStates.jsx
│   │   ├── PageTransition.jsx
│   │   └── SkeletonLoaders.jsx
│   ├── [Component].jsx  (Individual components)
│   └── [Component].css  (Component styles)
├── contexts/            (React contexts)
│   └── AuthContext.jsx
├── hooks/               (Custom hooks)
│   └── useProfile.js
├── utils/               (Utility functions)
│   ├── api.js
│   ├── confetti.js
│   ├── dateUtils.js
│   └── toast.jsx
├── styles/              (Global styles)
│   ├── components.css
│   ├── design-tokens.css
│   ├── nprogress.css
│   ├── page-layouts.css
│   ├── spacing.css
│   └── typography.css
├── config/              (Configuration)
│   ├── antd-theme.js
│   └── config.js
├── App.jsx              (Main router)
├── App.css              (App layout styles)
├── main.jsx             (Entry point)
└── index.css            (Global styles)
```

### **Component Categories:**

#### **Layout Components:**

- `Sidebar.jsx` - Navigation sidebar
- `GlobalHeader.jsx` - Top header bar
- `Header.jsx` - Page header (legacy, used in some pages)

#### **Feature Components:**

- Dashboard, QuickSale, CashRegister, Appointment
- CustomerList, LeadManagement, MissedEnquiries, Feedback
- Service, Package, Product, Prepaid, Inventory
- Staffs, StaffAttendance, StaffTempAssignment
- Expense, DiscountApprovals, ApprovalCodes
- ReportsAnalytics and all report components

#### **Shared/Utility Components:**

- `SalesInsights.jsx` - Tab-based lazy loading component
- `TopMovingItems.jsx` - Top moving items display
- `Top10Customers.jsx` - Top customers table
- `DashboardStatsCards.jsx` - Statistics cards
- `BranchSelector.jsx` - Branch selection dropdown
- `Profile.jsx` - User profile modal

#### **Shared Utilities:**

- `EmptyStates.jsx` - Empty state components
- `SkeletonLoaders.jsx` - Loading skeletons
- `PageTransition.jsx` - Page transition animations

---

## 7. Routing & Navigation

### Navigation System:

- **State-based routing** (no React Router)
- Uses `activePage` state in `App.jsx`
- Navigation via `setActivePage()` function
- Custom events: `navigateToPage` event for cross-component navigation

### Page IDs (from App.jsx):

1. `dashboard`
2. `quick-sale`
3. `cash-register`
4. `appointment`
5. `customer-list`
6. `lead-management`
7. `missed-enquiries`
8. `customer-lifecycle`
9. `feedback`
10. `service-recovery`
11. `discount-approvals`
12. `approval-codes`
13. `inventory`
14. `reports` / `reports-analytics` / `analytics`
15. `service-sales-analysis`
16. `list-of-bills`
17. `list-of-deleted-bills`
18. `sales-by-service-group`
19. `prepaid-package-clients`
20. `membership-clients`
21. `staff-incentive-report`
22. `expense-report`
23. `inventory-report`
24. `staff-combined-report`
25. `business-growth-trend-analysis`
26. `staff-performance-analysis`
27. `period-performance-summary`
28. `client-value-loyalty-report`
29. `service-product-performance`
30. `service`
31. `package`
32. `product`
33. `prepaid`
34. `settings`
35. `membership`
36. `referral-program`
37. `tax`
38. `manager`
39. `owner-settings`
40. `staffs`
41. `staff-attendance`
42. `staff-temp-assignment`
43. `asset-management`
44. `expense`

---

## 8. Styling Architecture

### **Design System:**

- **Design Tokens:** `styles/design-tokens.css` (CSS variables)
- **Typography:** `styles/typography.css`
- **Spacing:** `styles/spacing.css`
- **Components:** `styles/components.css`
- **Page Layouts:** `styles/page-layouts.css`

### **Component Styling:**

- Each component has its own CSS file
- Uses CSS variables from design tokens
- Consistent color scheme: Teal (#0F766E) as primary
- Responsive design with mobile breakpoints

### **Common CSS Patterns:**

- Modal overlays with backdrop blur
- Card-based layouts with rounded corners
- Table components with hover effects
- Form inputs with focus states
- Button variants (primary, secondary, danger)

---

## 9. State Management

### **Context API:**

- `AuthContext.jsx` - Authentication, user data, branch selection

### **Local State:**

- Most components use `useState` for local state
- Modal visibility states (`showModal`, `setShowModal`)
- Form data states
- Loading states

### **Persistence:**

- Sidebar collapse state in `localStorage`
- User authentication in `localStorage`
- Branch selection in context

---

## 10. Key Features

### **Authentication:**

- Login component with role-based access
- Protected routes via `RequireRole` component
- Role-based sidebar visibility

### **Multi-Branch Support:**

- BranchSelector in GlobalHeader
- Branch filtering in API calls
- Branch-specific data display

### **Responsive Design:**

- Mobile sidebar with backdrop
- Collapsible sidebar (desktop)
- Responsive tables and cards
- Mobile-friendly modals

### **Performance Optimizations:**

- Lazy loading in SalesInsights (tab-based)
- Caching in Dashboard component
- Skeleton loaders for better UX
- Page transitions with Framer Motion

---

## 11. Component Count Summary

**Total Components:** ~63 JSX files

**Total CSS Files:** ~63 CSS files

**Shared Components:** 3 (EmptyStates, SkeletonLoaders, PageTransition)

**Layout Components:** 3 (Sidebar, GlobalHeader, Header)

**Modal Components:** 8+ different modal patterns

**Report Components:** 20+ report/analytics components

---

## 12. Notable Patterns

### **Modal Pattern:**

```jsx
{showModal && (
  <div className="modal-overlay" onClick={closeModal}>
    <div className="modal-content" onClick={(e) => e.stopPropagation()}>
      {/* Modal content */}
    </div>
  </div>
)}
```

### **Page Structure Pattern:**

```jsx
<div className="page-container">
  <Header title="Page Title" />
  {/* Page content */}
</div>
```

### **Table Pattern:**

- Consistent table styling across components
- Hover effects
- Empty states
- Loading states

### **Form Pattern:**

- Consistent form group styling
- Label/input structure
- Validation display
- Submit/cancel buttons

---

This analysis provides a complete overview of the frontend structure, navigation, modals, and component organization of the Saloon Management System.