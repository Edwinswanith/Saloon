# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Saloon Management System - A multi-branch salon/spa business management application with billing, appointments, inventory, staff management, and reporting features.

## Tech Stack

- **Backend**: Flask 3.0, MongoEngine ODM, MongoDB Atlas
- **Frontend**: React 18, Vite, Ant Design 6, Zustand, React Query
- **Deployment**: Google Cloud Run via Docker (multi-stage build)

## Development Commands

### Backend
```bash
cd backend
python -m venv myenv && myenv\Scripts\activate  # Windows
pip install -r requirements.txt
python app.py  # Port 5000
```

### Frontend
```bash
cd frontend
npm install
npm run dev   # Port 5173
npm run build # Production build
```

### Docker
```bash
docker-compose up  # Full stack locally
cloud_run.bat      # Deploy to Cloud Run (Windows)
```

## Architecture

### Backend Structure

**Entry Point**: `backend/app.py` - Flask app initialization, MongoDB connection, route registration

**Database Toggle**: In `app.py`, switch `MONGODB_DB` between `'Saloon_prod'` (production) and `'Saloon'` (development)

**Models**: `backend/models.py` - MongoEngine documents with `to_dict()` helper for JSON serialization

**Routes**: `backend/routes/` - Flask Blueprints registered in `routes/__init__.py`
- All endpoints prefixed with `/api/`
- Add new blueprints in `__init__.py` via `register_routes()`

**Backend Utilities** (`backend/utils/`):
- `auth.py` - JWT handling, decorators: `@require_auth`, `@require_role('manager', 'owner')`, `@optional_auth`
- `branch_filter.py` - Multi-branch filtering: `get_selected_branch()`, `filter_by_branch()`
- `redis_cache.py` - Caching layer (optional, falls back to in-memory)

### Frontend Structure

**API Configuration**: `frontend/src/config.js` - Toggle `API_BASE_URL` between local and Cloud Run URL

**API Utility**: `frontend/src/utils/api.js` - Centralized fetch with auth headers
- Use `apiGet()`, `apiPost()`, `apiPut()`, `apiDelete()` for all API calls
- Automatically adds `Authorization` and `X-Branch-Id` headers

**State**:
- Auth: `src/contexts/AuthContext.jsx` - JWT tokens in localStorage
- Branch: Stored in `localStorage.current_branch`, sent via `X-Branch-Id` header

### Multi-Branch Architecture

- Users have roles: `staff`, `manager`, `owner`
- Data is branch-scoped via `branch` ReferenceField in models
- `X-Branch-Id` header determines data scope
- Owners can switch branches; staff/managers locked to their branch
- Use `get_selected_branch(request, user)` in routes to get current branch

### Adding a New API Endpoint

1. Create route file in `backend/routes/` with Blueprint
2. Use auth decorators: `@require_auth` or `@require_role('manager', 'owner')`
3. Get branch via: `branch = get_selected_branch(request, current_user)`
4. Filter queries: `Model.objects(branch=branch)` or `filter_by_branch(query, branch)`
5. Register blueprint in `routes/__init__.py`

### Database Conventions

- Models use MongoEngine Document classes
- Convert to JSON via `to_dict(doc)` - converts ObjectId to string `id`
- Timestamps: `created_at`, `updated_at` (DateTimeField)
- Soft deletes: `is_active` or `status` fields
