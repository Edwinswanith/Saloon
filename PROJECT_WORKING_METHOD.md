# Project Working Method

This document provides a step-by-step guide for using the Saloon Management System, focusing on the Owner login flow and mobile responsiveness verification.

---

## Table of Contents

1. [Owner Login Flow](#1-owner-login-flow)
2. [Owner Features After Login](#2-owner-features-after-login)
3. [Mobile Responsiveness Testing](#3-mobile-responsiveness-testing)

---

## 1. Owner Login Flow

Follow these steps to log in as an Owner with full system access.

### Step 1: Access the Application

Open your browser and navigate to:

| Environment | URL |
|-------------|-----|
| Development | `http://localhost:5173` |
| Production | `https://saloon-management-system-895210689446.europe-west2.run.app` |

### Step 2: Select User Type

On the login screen, locate the user type toggle buttons at the top of the form:

```
[ Staff ] [ Manager ] [ Owner ]
```

Click the **Owner** button to switch to owner login mode.

### Step 3: Select Branch

1. Click the **Select Branch** dropdown
2. Choose **T Nagar** from the list (displays as "T Nagar - Chennai")

> **Note:** Owners can select any branch. This sets your default working branch after login, but you can switch branches later using the header selector.

### Step 4: Enter Email

In the email input field, enter:

```
owner@salon.com
```

### Step 5: Enter Password

In the password input field, enter:

```
owner123
```

### Step 6: Click Sign In

Click the **Sign In** button to submit the form.

- Button text changes to "Signing in..."
- A loading spinner appears
- The form is disabled during submission

### Step 7: Verify Dashboard Access

After successful login, verify the following:

| Verification Item | Expected Result |
|-------------------|-----------------|
| Page redirect | Dashboard page loads |
| Sidebar | Full navigation menu visible |
| Header branch | Shows "T Nagar" |
| User badge | Displays owner name |
| Owner features | Discount Approvals, Approval Codes visible in sidebar |

---

## 2. Owner Features After Login

As an Owner, you have full access to all system features:

### Dashboard
- KPI stat cards (Revenue, Tax, Transactions, Expenses, etc.)
- Revenue breakdown charts
- Staff performance analytics
- Client funnel metrics

### Billing Section
- **Quick Sale** - Point of sale / billing interface
- **Cash Register** - Cash management
- **Appointment** - Booking management
- **Customers**
  - Customer List
  - Lead Management
  - Missed Enquiries
  - Feedback
  - Service Recovery
- **Inventory** - Stock management

### Owner-Exclusive Features
- **Discount Approvals** - Review and approve discount requests
- **Approval Codes** - Generate and manage approval codes

### Analytics
- **Reports & Analytics** - Comprehensive reporting suite
  - Service Sales Analysis
  - List of Bills / Deleted Bills
  - Sales by Service Group
  - Prepaid Package Clients
  - Membership Clients
  - Staff Incentive Report
  - Expense Report
  - Inventory Report
  - Business Growth Trend Analysis
  - Staff Performance Analysis
  - Period Performance Summary
  - Client Value & Loyalty Report
  - Service & Product Performance

### Master Settings
- **Saloon Settings**
  - Service configuration
  - Package configuration
  - Product configuration
  - Prepaid packages
  - General Settings
- **Staffs** - Staff management
- **Staff Attendance** - Attendance tracking
- **Staff Reassignment** - Temporary assignments
- **Asset Management** - Asset tracking
- **Expense** - Expense management
- **Membership** - Membership plans
- **Referral Program** - Referral settings
- **Tax** - Tax configuration
- **Manager** - Manager management

---

## 3. Mobile Responsiveness Testing

The application is fully responsive across all common screen sizes. Use this guide to verify mobile responsiveness.

### How to Test Using Chrome DevTools

1. Open the application in Google Chrome
2. Press **F12** (or right-click → Inspect) to open DevTools
3. Click the **Toggle Device Toolbar** icon (or press **Ctrl+Shift+M**)
4. Select a device preset from the dropdown, or enter custom dimensions

### Breakpoint Reference

| Breakpoint | Screen Width | UI Behavior |
|------------|--------------|-------------|
| **Desktop** | >1440px | Full sidebar (280px), 4-6 column grids, 32px padding |
| **Large Tablet** | 1025-1440px | Sidebar 260px, adjusted spacing |
| **Tablet** | 769-1024px | Sidebar 240px, 2-3 column grids, 24px padding |
| **Mobile** | ≤768px | Sidebar hidden (drawer), hamburger menu, single column, 16px padding |
| **Small Mobile** | ≤480px | Compact drawer (260px), smaller typography, 12px padding |

### Device Presets to Test

#### Desktop
| Device | Dimensions |
|--------|------------|
| Full HD | 1920 × 1080 |
| MacBook Pro | 1440 × 900 |

#### Tablet
| Device | Dimensions |
|--------|------------|
| iPad Pro | 1024 × 1366 |
| iPad | 768 × 1024 |

#### Mobile
| Device | Dimensions |
|--------|------------|
| iPhone 12 Pro | 390 × 844 |
| iPhone SE | 375 × 667 |
| Samsung Galaxy S20 | 360 × 800 |

#### Small Mobile
| Device | Dimensions |
|--------|------------|
| iPhone SE (old) | 320 × 568 |
| Galaxy Fold | 280 × 653 |

### Mobile Testing Checklist

Use this checklist to verify responsiveness at mobile breakpoints (≤768px):

#### Login Screen
- [ ] User type toggles stack vertically (≤640px)
- [ ] Form inputs are full width
- [ ] Sign In button is easily tappable
- [ ] No horizontal scrolling

#### Navigation
- [ ] Hamburger menu icon (☰) appears in header
- [ ] Tapping hamburger slides sidebar in from left
- [ ] Semi-transparent backdrop overlay appears
- [ ] Tapping backdrop closes the sidebar
- [ ] All menu items are accessible

#### Dashboard
- [ ] Stat cards stack in single column
- [ ] Charts resize proportionally
- [ ] Content scrolls smoothly
- [ ] No content is cut off

#### Forms & Tables
- [ ] Form fields stack vertically
- [ ] Tables have horizontal scroll
- [ ] Smooth momentum scrolling on tables
- [ ] All buttons are reachable

#### Touch & Accessibility
- [ ] Touch targets are minimum 44×44px
- [ ] Input fields don't auto-zoom on iOS (font-size ≥16px)
- [ ] Buttons have adequate spacing
- [ ] Text remains readable

### Common Mobile Issues to Check

| Issue | What to Look For | Solution |
|-------|------------------|----------|
| iOS Input Zoom | Screen zooms when focusing input | Verify font-size is 16px |
| Tap Targets Too Small | Difficult to tap buttons/links | Check 44×44px minimum |
| Content Overflow | Horizontal scrollbar on body | Check container widths |
| Sidebar Stuck | Sidebar doesn't close | Test backdrop tap and swipe |
| Slow Scroll | Janky scrolling in lists | Verify `-webkit-overflow-scrolling: touch` |

### Quick Responsive Test Steps

1. **Desktop (1920px)** → Verify full sidebar visible, multi-column layouts
2. **Tablet (1024px)** → Verify sidebar narrows, grids reduce columns
3. **Mobile (768px)** → Verify hamburger menu appears, sidebar hidden
4. **Small Mobile (375px)** → Verify all content accessible, no overflow
5. **Rotate device** → Verify landscape mode works correctly

---

## Quick Reference

### Owner Login Credentials

| Field | Value |
|-------|-------|
| User Type | Owner |
| Branch | T Nagar |
| Email | `owner@salon.com` |
| Password | `owner123` |

### Application URLs

| Environment | URL |
|-------------|-----|
| Frontend (Dev) | http://localhost:5173 |
| Backend (Dev) | http://127.0.0.1:5000 |
| Production | https://saloon-management-system-895210689446.europe-west2.run.app |
