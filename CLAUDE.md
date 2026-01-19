# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Saloon Management System - A multi-branch salon/spa business management application with billing, appointments, inventory, staff management, and reporting features.

## Tech Stack

- **Backend**: Flask 3.0 with MongoEngine ODM, MongoDB Atlas
- **Frontend**: React 18, Vite, Ant Design 6, Zustand (state), React Query
- **Deployment**: Google Cloud Run via Docker (multi-stage build)

## Development Commands

### Backend
```bash
cd backend
python -m venv myenv
myenv\Scripts\activate  # Windows
pip install -r requirements.txt
python app.py  # Runs on port 5000
```

### Frontend
```bash
cd frontend
npm install
npm run dev   # Dev server on port 5173
npm run build # Production build to dist/
```

### Docker (local full stack)
```bash
docker-compose up
```

### Deploy to Cloud Run
```bash
# Windows
cloud_run.bat

# Linux/Mac
./cloud_run.sh
```

## Architecture

### Backend Structure

**Entry Point**: `backend/app.py` - Flask app with MongoDB connection, CORS setup, route registration

**Database**: MongoDB Atlas
- Production: `Saloon_prod`
- Development: `Saloon` (toggle in app.py MONGODB_DB constant)

**Models**: `backend/models.py` - MongoEngine document classes
- Key models: Branch, Customer, Staff, Service, Product, Package, Bill, Appointment, Expense, Inventory

**Routes**: `backend/routes/` - Flask Blueprints registered via `register_routes(app)`
- All API endpoints prefixed with `/api/`
- Branch filtering via `X-Branch-Id` header on most endpoints

### Frontend Structure

**Entry**: `frontend/src/main.jsx` → `App.jsx`

**API Configuration**: `frontend/src/config.js`
- Toggle `API_BASE_URL` between local (http://127.0.0.1:5000) and production Cloud Run URL

**Core Patterns**:
- Components in `src/components/` - each feature has `.jsx` + `.css` pair
- Auth via `src/contexts/AuthContext.jsx` - JWT tokens stored in localStorage
- API calls via `src/utils/api.js` - centralized fetch wrapper with auth headers and branch ID
- Main billing UI in `QuickSale.jsx` (largest component)

**Key Components**:
- `Sidebar.jsx` - Navigation
- `Dashboard.jsx` - Analytics overview
- `QuickSale.jsx` - Primary billing/POS interface
- `CustomerList.jsx`, `Staffs.jsx`, `Service.jsx`, `Product.jsx` - CRUD management

### Multi-Branch Architecture

The system supports multiple branches (locations):
- Users (staff/manager/owner) are associated with a branch
- Most data is branch-scoped via `branch` ReferenceField in models
- Frontend sends `X-Branch-Id` header with API requests
- Owners can switch between branches; managers/staff see only their branch

### Authentication Flow

1. Login via `/api/auth/login` returns JWT token
2. Token stored in `localStorage.auth_token`
3. `AuthContext` manages user state, token validation, branch selection
4. API utility automatically adds `Authorization` and `X-Branch-Id` headers

## Database Conventions

- All models use MongoEngine Document classes
- ObjectIds converted to string `id` field via `to_dict()` helper
- Timestamps: `created_at`, `updated_at` fields (DateTimeField)
- Soft deletes where applicable via `is_active` or `status` fields
