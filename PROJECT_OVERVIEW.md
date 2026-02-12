# Saloon Management System - Complete Project Overview

## 📋 Project Description

**Saloon Management System** is a comprehensive, multi-branch salon and spa business management application designed to handle all aspects of running a modern beauty salon business. The system provides end-to-end management from customer booking to billing, inventory tracking, staff management, and detailed analytics.

### Core Purpose
- **Point of Sale (POS)**: Quick billing and checkout system
- **Multi-Branch Management**: Support for multiple salon locations
- **Customer Relationship Management**: Track customers, leads, feedback, and loyalty programs
- **Inventory Management**: Real-time stock tracking for products
- **Staff Management**: Attendance, performance tracking, and commission calculations
- **Financial Management**: Bills, expenses, cash register, and comprehensive reporting
- **Appointment Scheduling**: Booking management system
- **Analytics & Reporting**: Business intelligence and performance metrics

---

## 🛠️ Technology Stack

### Frontend
- **Framework**: React 18.2.0
- **Build Tool**: Vite 5.0.8
- **UI Library**: Ant Design 6.1.2
- **State Management**: Zustand 5.0.9
- **Data Fetching**: TanStack React Query 5.90.14
- **Charts**: Recharts 3.6.0
- **Forms**: React Hook Form 7.69.0
- **Animations**: Framer Motion 12.23.26
- **Date Handling**: Day.js 1.11.19
- **Excel Export**: xlsx 0.18.5
- **Notifications**: React Hot Toast 2.6.0

### Backend
- **Framework**: Flask 3.0.0
- **Database**: MongoDB Atlas (Cloud)
- **ODM**: MongoEngine 0.27.0
- **Authentication**: PyJWT 2.8.0, bcrypt 4.1.2
- **CORS**: Flask-CORS 4.0.0
- **PDF Generation**: ReportLab 4.0.7
- **Caching**: Redis 5.0.1 (optional, with in-memory fallback)
- **HTTP Client**: Requests 2.31.0

### Deployment
- **Platform**: Google Cloud Run
- **Containerization**: Docker (multi-stage build)
- **Region**: europe-west2
- **Service URL**: https://saloon-management-system-895210689446.europe-west2.run.app

---

## 🏗️ Architecture

### System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (React)                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │  Vite    │  │   AntD    │  │ React   │             │
│  │  Build   │  │   UI      │  │ Query   │             │
│  └──────────┘  └──────────┘  └──────────┘             │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTP/REST API
                       │ (JWT Authentication)
┌──────────────────────┴──────────────────────────────────┐
│                 Backend (Flask)                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │  Flask   │  │MongoEngine│ │  Redis   │             │
│  │  Routes  │  │   ODM     │ │  Cache   │             │
│  └──────────┘  └──────────┘  └──────────┘             │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────┴──────────────────────────────────┐
│              MongoDB Atlas (Cloud)                       │
│  ┌──────────────────────────────────────────────┐      │
│  │  Database: Saloon_prod (Production)           │      │
│  │  Collections: 30+ collections                 │      │
│  │  Connection: mongodb+srv://...                │      │
│  └──────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────┘
```

### Application Flow

1. **User Authentication**: JWT-based authentication with role-based access (Owner, Manager, Staff)
2. **Branch Selection**: Multi-branch support with branch-specific data filtering
3. **Data Operations**: All CRUD operations through RESTful API endpoints
4. **Real-time Updates**: Optimistic UI updates with server-side validation
5. **Caching**: Redis caching for frequently accessed data (with fallback)

---

## 💾 Data Handling & Datasets

### Database: MongoDB Atlas

**Connection Details:**
- **Database Name**: `Saloon_prod` (Production) / `Saloon` (Development)
- **Connection String**: MongoDB Atlas Cloud Cluster
- **ODM**: MongoEngine for Python object-document mapping

### Data Collections (30+ Collections)

#### Core Business Entities

1. **`branches`** - Salon branch locations
   - Fields: name, address, city, phone, email, gstin, is_active
   - Multi-branch support with branch-specific data isolation

2. **`customers`** - Customer records
   - Fields: mobile, first_name, last_name, email, source, gender, dob, referral_code
   - Computed fields: last_visit_date, total_visits, total_spent
   - Branch association for multi-branch support
   - Customer merge functionality for duplicate handling

3. **`staffs`** - Staff members
   - Fields: mobile, first_name, last_name, email, salary, commission_rate, role, status
   - Branch assignment for multi-branch operations
   - Password hash for manager/owner roles

4. **`managers`** - Manager accounts
   - Separate collection for manager authentication
   - Branch assignment

5. **`owners`** - Owner accounts
   - Full system access
   - Multi-branch oversight

#### Service & Product Catalog

6. **`service_groups`** - Service categories
   - Fields: name, display_order
   - Examples: Hair Care, Skin Care, Nail Care, Spa, Bridal

7. **`services`** - Service offerings
   - Fields: name, group, price, duration, description, branch, status
   - Branch-specific services

8. **`product_categories`** - Product categories
   - Fields: name, display_order

9. **`products`** - Product inventory
   - Fields: name, category, price, cost, stock_quantity, min_stock_level, sku, description
   - **Real-time inventory tracking** with stock reduction on sale
   - Low stock alerts (≤5 units)

10. **`packages`** - Service packages
    - Fields: name, price, description, services (JSON), branch, status
    - Combo service offerings

#### Membership & Prepaid

11. **`membership_plans`** - Membership plan templates
    - Fields: name, validity_days, price, allocated_discount, status

12. **`memberships`** - Customer membership purchases
    - Fields: name, customer, plan, branch, price, purchase_date, expiry_date, benefits, status

13. **`prepaid_packages`** - Prepaid package purchases
    - Fields: customer, package_name, amount, balance, expiry_date, status
    - Customer-specific prepaid balance tracking

#### Transactions & Billing

14. **`bills`** - Invoice/bill records
    - Embedded documents: BillItemEmbedded (service, package, product, membership)
    - Fields: customer, branch, bill_date, items[], subtotal, tax, discount, total, payment_method, status
    - Comprehensive billing with multiple item types

15. **`bill_items`** - Individual bill line items (legacy support)
    - Reference to bills for detailed item tracking

16. **`cash_transactions`** - Cash register transactions
    - Fields: branch, transaction_type (cash_in, cash_out), amount, description, created_by

#### Appointments & Customer Engagement

17. **`appointments`** - Booking records
    - Fields: customer, branch, service, staff, appointment_date, appointment_time, status, notes

18. **`leads`** - Lead management
    - Fields: name, mobile, email, source, status, notes, branch

19. **`missed_enquiries`** - Missed customer enquiries
    - Fields: customer, enquiry_date, service, status, notes

20. **`feedbacks`** - Customer feedback
    - Fields: customer, branch, rating, comment, service, date

21. **`service_recovery`** - Service recovery records
    - Fields: customer, issue_description, resolution, status

#### Staff Management

22. **`staff_attendance`** - Attendance tracking
    - Fields: staff, branch, date, check_in, check_out, status, notes

23. **`leaves`** - Leave management
    - Fields: staff, branch, leave_type, start_date, end_date, status, reason

24. **`temp_assignments`** - Temporary staff assignments
    - Fields: staff, from_branch, to_branch, start_date, end_date, status

25. **`staff_performance`** - Performance metrics
    - Computed metrics: revenue, services_count, commission_earned
    - Indexed for fast dashboard queries

#### Financial & Operations

26. **`expenses`** - Expense records
    - Fields: branch, expense_type, amount, description, date, created_by

27. **`assets`** - Asset management
    - Fields: name, category, purchase_date, purchase_price, branch, status

28. **`tax_settings`** - Tax configuration
    - Fields: branch, tax_type, rate, is_active

29. **`tax_slabs`** - Tax rate slabs
    - Fields: min_amount, max_amount, rate

30. **`discount_approvals`** - Discount approval workflow
    - Fields: bill, requested_by, requested_discount, status, approved_by, approval_code

31. **`approval_codes`** - Approval code management
    - Fields: code, description, created_by, is_active

#### Referral & Loyalty

32. **`referral_program_settings`** - Referral program configuration
    - Fields: is_active, customer_reward, referrer_reward, min_purchase_amount

#### Analytics & Reporting

33. **`customer_lifecycle`** - Customer lifecycle tracking
    - Computed metrics for customer segmentation

34. **`client_value_loyalty`** - Client value analysis
    - Revenue, visits, loyalty metrics

### Data Relationships

```
Branch (1) ──→ (N) Customers
Branch (1) ──→ (N) Staff
Branch (1) ──→ (N) Services
Branch (1) ──→ (N) Products
Branch (1) ──→ (N) Bills
Branch (1) ──→ (N) Appointments

Customer (1) ──→ (N) Bills
Customer (1) ──→ (N) Appointments
Customer (1) ──→ (N) Memberships
Customer (1) ──→ (N) PrepaidPackages

Service (1) ──→ (N) BillItems
Product (1) ──→ (N) BillItems
Package (1) ──→ (N) BillItems

Staff (1) ──→ (N) Bills (assigned_staff)
Staff (1) ──→ (N) Appointments
Staff (1) ──→ (N) Attendance
```

### Data Flow Examples

#### 1. Quick Sale (Billing) Flow
```
1. Customer Selection → Fetch customer from MongoDB
2. Add Service/Package/Product → Validate stock (products)
3. Add to Bill → Create bill item (optimistic UI update)
4. Complete Checkout → 
   - Create bill document in MongoDB
   - Reduce product stock_quantity
   - Update customer total_spent, total_visits
   - Create cash transaction record
```

#### 2. Inventory Management Flow
```
1. Product Sale → Stock reduction on bill creation
2. Low Stock Alert → Visual indicators (≤5 units)
3. Out of Stock → Disabled in UI, cannot add to bill
4. Stock Refresh → Real-time updates from MongoDB
```

#### 3. Multi-Branch Data Isolation
```
1. User selects branch → Branch ID stored in context
2. All queries filtered by branch → get_selected_branch()
3. Branch-specific data → Customers, Staff, Services, Products
4. Cross-branch reports → Owner/Manager can view all branches
```

---

## ✨ Key Features

### 1. Point of Sale (Quick Sale)
- **Multi-item billing**: Services, Packages, Products, Memberships, Prepaid
- **Real-time inventory**: Stock validation and automatic reduction
- **Discount management**: Approval workflow for discounts
- **Payment methods**: Cash, Card, UPI, Wallet
- **Invoice generation**: PDF invoice with GST details
- **Customer selection**: Quick customer lookup and creation

### 2. Customer Management
- **Customer database**: Complete customer profiles with history
- **Lead management**: Track and convert leads
- **Missed enquiries**: Follow-up on missed opportunities
- **Feedback system**: Collect and analyze customer feedback
- **Service recovery**: Handle customer complaints
- **Customer merge**: Combine duplicate customer records
- **Loyalty tracking**: Total visits, spending, last visit date

### 3. Appointment System
- **Booking management**: Schedule appointments with staff
- **Calendar view**: Visual appointment calendar
- **Status tracking**: Confirmed, Completed, Cancelled, No-show
- **Reminders**: Appointment notifications
- **Staff assignment**: Assign staff to appointments

### 4. Inventory Management
- **Product catalog**: Complete product database
- **Stock tracking**: Real-time stock quantity
- **Low stock alerts**: Visual indicators for low stock (≤5 units)
- **Stock reduction**: Automatic on sale
- **Category management**: Organize products by category
- **SKU tracking**: Product identification

### 5. Staff Management
- **Staff profiles**: Complete staff information
- **Attendance tracking**: Check-in/check-out system
- **Leave management**: Leave requests and approvals
- **Performance tracking**: Revenue, services, commission
- **Temporary assignments**: Cross-branch staff assignments
- **Commission calculation**: Automatic commission based on sales

### 6. Financial Management
- **Cash register**: Cash in/out transactions
- **Expense tracking**: Categorize and track expenses
- **Tax management**: Configurable tax rates and slabs
- **Payment tracking**: Multiple payment methods
- **Financial reports**: Revenue, expenses, profit analysis

### 7. Membership & Prepaid
- **Membership plans**: Create and manage membership templates
- **Customer memberships**: Track active memberships
- **Prepaid packages**: Customer-specific prepaid balances
- **Expiry tracking**: Automatic expiry date management
- **Balance tracking**: Real-time balance updates

### 8. Analytics & Reporting
- **Dashboard**: KPI cards, charts, metrics
- **Service Sales Analysis**: Revenue by service
- **Staff Performance**: Individual and team performance
- **Business Growth Trends**: Revenue trends over time
- **Customer Lifecycle**: Customer segmentation
- **Client Value & Loyalty**: High-value customer identification
- **Inventory Reports**: Stock levels, low stock alerts
- **Expense Reports**: Expense categorization and analysis
- **Period Performance**: Custom date range analysis

### 9. Multi-Branch Support
- **Branch management**: Multiple salon locations
- **Branch-specific data**: Isolated data per branch
- **Cross-branch reports**: Owner/Manager can view all branches
- **Branch switching**: Easy branch selection in header
- **Branch-specific settings**: Services, products, staff per branch

### 10. Role-Based Access Control
- **Owner**: Full system access, all branches
- **Manager**: Branch management, reports, staff management
- **Staff**: Limited access, billing, appointments

### 11. Discount & Approval System
- **Discount requests**: Staff can request discounts
- **Approval workflow**: Manager/Owner approval required
- **Approval codes**: Generate and manage approval codes
- **Discount tracking**: Track all discount approvals

### 12. Referral Program
- **Referral tracking**: Track customer referrals
- **Reward system**: Configure referral rewards
- **Referral codes**: Customer-specific referral codes

---

## 📁 Project Structure

```
Saloon/
├── backend/                    # Flask Backend
│   ├── app.py                  # Flask app initialization
│   ├── models.py               # MongoEngine models
│   ├── requirements.txt        # Python dependencies
│   ├── routes/                 # API route handlers
│   │   ├── auth_routes.py      # Authentication
│   │   ├── bill_routes.py      # Billing
│   │   ├── customer_routes.py  # Customer management
│   │   ├── dashboard_routes.py # Dashboard data
│   │   ├── inventory_routes.py # Inventory
│   │   ├── staff_routes.py     # Staff management
│   │   └── ... (30+ route files)
│   ├── services/               # Business logic services
│   │   └── invoice_pdf_service.py # PDF generation
│   ├── utils/                  # Utility functions
│   │   ├── auth.py             # JWT, decorators
│   │   ├── branch_filter.py    # Multi-branch filtering
│   │   └── redis_cache.py      # Caching
│   ├── migrations/             # Database migrations
│   └── templates/              # HTML templates
│       └── invoice/            # Invoice templates
│
├── frontend/                    # React Frontend
│   ├── src/
│   │   ├── App.jsx             # Main app router
│   │   ├── main.jsx            # Entry point
│   │   ├── config.js           # API configuration
│   │   ├── components/         # React components
│   │   │   ├── Dashboard.jsx   # Dashboard
│   │   │   ├── QuickSale.jsx   # POS system
│   │   │   ├── CustomerList.jsx # Customer management
│   │   │   ├── Appointment.jsx # Appointment booking
│   │   │   ├── Inventory.jsx   # Inventory management
│   │   │   ├── Staffs.jsx      # Staff management
│   │   │   └── ... (50+ components)
│   │   ├── contexts/           # React contexts
│   │   │   └── AuthContext.jsx # Authentication context
│   │   ├── utils/              # Utility functions
│   │   │   ├── api.js          # API client
│   │   │   └── dateUtils.js    # Date utilities
│   │   └── styles/             # Global styles
│   ├── package.json            # Node dependencies
│   └── vite.config.js          # Vite configuration
│
├── Dockerfile                  # Multi-stage Docker build
├── docker-compose.yml          # Local development setup
├── cloud_run.bat              # Cloud Run deployment script
├── .gitignore                 # Git ignore rules
└── PROJECT_OVERVIEW.md         # This file
```

---

## 🚀 Deployment

### Production Deployment

**Platform**: Google Cloud Run  
**Region**: europe-west2  
**Service URL**: https://saloon-management-system-895210689446.europe-west2.run.app

### Deployment Process

1. **Build Docker Image**: Multi-stage build (frontend + backend)
2. **Tag Image**: Tag with version (v20, v21, etc.)
3. **Push to Artifact Registry**: Google Artifact Registry
4. **Deploy to Cloud Run**: Deploy new revision

### Deployment Script

```batch
# cloud_run.bat
- Sets Google Cloud project
- Authenticates Docker
- Builds Docker image (--no-cache)
- Tags image for Artifact Registry
- Pushes to registry
- Deploys to Cloud Run
```

### Environment Configuration

**Backend** (`backend/app.py`):
- `MONGODB_URI`: MongoDB Atlas connection string
- `MONGODB_DB`: Database name (`Saloon_prod` for production)

**Frontend** (`frontend/src/config.js`):
- `API_BASE_URL`: Backend API URL
  - Development: `http://127.0.0.1:5000`
  - Production: `https://saloon-management-system-895210689446.europe-west2.run.app`

---

## 📊 Data Statistics

### Current Database State (Sample)

- **Branches**: 7 locations
- **Customers**: 600+ customers
- **Staff**: 7+ staff members
- **Services**: 23+ services
- **Products**: 11+ products
- **Packages**: 4+ service packages
- **Bills**: 1000+ transaction records
- **Appointments**: 500+ appointments
- **Memberships**: Active membership plans
- **Prepaid Packages**: Customer prepaid balances

### Data Growth Patterns

- **Bills**: Daily transaction records
- **Appointments**: Ongoing booking system
- **Inventory**: Real-time stock updates
- **Customer Data**: Continuous customer acquisition
- **Staff Performance**: Daily performance metrics

---

## 🔐 Security Features

1. **JWT Authentication**: Secure token-based authentication
2. **Password Hashing**: bcrypt for password storage
3. **Role-Based Access**: Owner, Manager, Staff roles
4. **Branch Isolation**: Data filtered by branch
5. **CORS Configuration**: Secure cross-origin requests
6. **Input Validation**: Server-side validation for all inputs
7. **Stock Validation**: Prevents overselling with server-side checks

---

## 📱 Mobile Responsiveness

### Breakpoints

- **Desktop**: >1440px - Full sidebar, multi-column layouts
- **Large Tablet**: 1025-1440px - Narrowed sidebar
- **Tablet**: 769-1024px - 2-3 column grids
- **Mobile**: ≤768px - Hamburger menu, single column
- **Small Mobile**: ≤480px - Compact layout

### Mobile Features

- Responsive sidebar (drawer on mobile)
- Touch-friendly buttons (44×44px minimum)
- Horizontal scroll for tables
- Optimized forms for mobile input
- No auto-zoom on iOS (font-size ≥16px)

---

## 🎯 Use Cases

### For Salon Owners
- Monitor all branches from one dashboard
- View comprehensive business analytics
- Approve discounts and manage approval codes
- Track staff performance across branches
- Generate financial reports

### For Managers
- Manage branch operations
- Track staff attendance and performance
- Handle customer service recovery
- Generate branch-specific reports
- Manage inventory and stock levels

### For Staff
- Process quick sales and billing
- Book appointments
- Add customer feedback
- View assigned appointments
- Request discount approvals

---

## 🔄 Development Workflow

### Local Development

1. **Backend Setup**:
   ```bash
   cd backend
   python -m venv myenv
   myenv\Scripts\activate  # Windows
   pip install -r requirements.txt
   python app.py  # Runs on port 5000
   ```

2. **Frontend Setup**:
   ```bash
   cd frontend
   npm install
   npm run dev  # Runs on port 5173
   ```

3. **Database**: Connect to MongoDB Atlas (development database)

### Production Deployment

1. Update version in `cloud_run.bat`
2. Run deployment script: `cloud_run.bat`
3. Wait for build and deployment (5-10 minutes)
4. Verify deployment at Cloud Run URL

---

## 📝 Key Documentation Files

- `PROJECT_WORKING_METHOD.md` - User guide and login instructions
- `QUICKSALE_INVENTORY_MANAGEMENT_COMPLETE.md` - Inventory system details
- `MONGODB_VERIFICATION_REPORT.md` - Database verification
- `PROJECT_OVERVIEW.md` - This comprehensive overview

---

## 🎓 Learning Resources

### Technologies Used
- **React**: Component-based UI development
- **Flask**: Python web framework
- **MongoDB**: NoSQL document database
- **MongoEngine**: ODM for MongoDB
- **Docker**: Containerization
- **Google Cloud Run**: Serverless deployment

### Best Practices Implemented
- RESTful API design
- Component-based architecture
- Responsive design
- Role-based access control
- Real-time data validation
- Optimistic UI updates
- Error handling and user feedback

---

## 📈 Future Enhancements

### Potential Features
1. **Mobile App**: Native mobile application
2. **SMS/WhatsApp Integration**: Automated notifications
3. **Online Booking**: Customer self-booking portal
4. **Loyalty Program**: Points and rewards system
5. **Advanced Analytics**: Machine learning insights
6. **Barcode Scanning**: Product scanning for inventory
7. **Multi-language Support**: Internationalization
8. **Payment Gateway Integration**: Online payments

---

## 📞 Support & Maintenance

### Database Management
- MongoDB Atlas cloud database
- Automatic backups
- Index optimization for performance
- Connection pooling

### Monitoring
- Cloud Run metrics
- Error logging
- Performance monitoring
- Usage analytics

---

## ✅ Project Status

**Current Version**: v20  
**Status**: Production Ready  
**Last Updated**: February 2026

### Completed Features
- ✅ Multi-branch support
- ✅ Complete billing system
- ✅ Inventory management
- ✅ Staff management
- ✅ Customer management
- ✅ Appointment system
- ✅ Analytics and reporting
- ✅ Mobile responsive design
- ✅ Role-based access control
- ✅ Real-time stock tracking

---

## 📄 License & Credits

**Project**: Saloon Management System  
**Database**: MongoDB Atlas  
**Deployment**: Google Cloud Run  
**Version Control**: Git

---

*This document provides a comprehensive overview of the Saloon Management System. For specific implementation details, refer to the individual component documentation files.*

