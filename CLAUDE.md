# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Saloon Management System - A multi-branch salon/spa business management application with billing, appointments, inventory, staff management, and reporting features.

## Tech Stack

- **Backend**: Flask 3.0, MongoEngine ODM, MongoDB Atlas
- **Frontend**: React 18, Vite, Ant Design 6, Zustand, React Query
- **Deployment**: Google Cloud Run via Docker (multi-stage build), and Vercel (SPA + Flask serverless function)

## Environment Setup

Config is a single root-level `.env` (copy from `.env.example`), loaded by `backend/utils/env_config.py::load_env()` (checks project root, then `backend/`) and by Vite for `VITE_*` vars. Required: `MONGODB_URI`, `JWT_SECRET`. `MONGODB_DB` defaults to `Saloon_prod`; set it to `Saloon` for a dev database. There is no more in-code toggle in `app.py` — do not edit `MONGODB_DB` there.

## Development Commands

The root is an npm workspace monorepo (`package.json` → `workspaces: ["frontend"]`).

### Backend
```bash
cd backend
python -m venv myenv && myenv\Scripts\activate  # Windows
pip install -r requirements.txt
python app.py  # Port 5000
```

### Frontend
```bash
npm install        # from repo root (installs frontend workspace)
npm run dev         # or: npm run dev:frontend — Vite on port 5173
npm run dev:backend # cd backend && python app.py, from root
npm run build       # frontend/npm run build directly, or `npm run build` at root for the Vercel bundle (see below)
```

### Docker (Cloud Run target)
```bash
docker-compose up  # Full stack locally: backend :5000, frontend :5173
cloud_run.bat      # Deploy to Cloud Run (Windows)
cloud_run.sh       # Deploy to Cloud Run (Linux/macOS)
```

Production image runs gunicorn with `gthread` workers (2 workers × 4 threads, 120s timeout) - see [Dockerfile](Dockerfile#L70). `python app.py` is dev-only.

### Vercel (alternate deployment target)

The repo also deploys as a single Vercel project: SPA + Flask served same-origin. `api/index.py` is the actual Vercel Python entrypoint — a thin shim that adds `backend/` to `sys.path` and imports the Flask `app` object from `backend/app.py` (Vercel's Python builder requires the function file to live under `api/`; it auto-installs `backend/requirements.txt` itself, so `installCommand` in `vercel.json` must not also run `pip install` — that fails on Vercel's `uv`-managed Python image with `externally-managed-environment`). `vercel.json` rewrites `/api/*`, `/i/*`, `/invoice/*`, `/feedback*` to `/api/index` and everything else to the SPA. `npm run vercel-build` (→ [scripts/vercel-build.mjs](scripts/vercel-build.mjs)) builds the frontend with empty `VITE_API_BASE_URL`/`VITE_PUBLIC_BASE_URL` so production web calls same-origin `/api/...`, then copies `frontend/dist` and `backend/static/css` into `public/`. When adding a new public (non-`/api`) route prefix, update both the Flask skip-list (see Static/Public Route Precedence below) *and* the `rewrites` array in `vercel.json`, or Vercel will serve `index.html` instead of routing to Flask.

## Architecture

### Backend Structure

**Entry Point**: `backend/app.py` - Flask app initialization, MongoDB connection, route registration

**Database Toggle**: set `MONGODB_DB` in `.env` (see Environment Setup above) — not a code edit

**Models**: `backend/models.py` - MongoEngine documents with `to_dict()` helper for JSON serialization

**Routes**: `backend/routes/` - Flask Blueprints registered in `routes/__init__.py`
- Most endpoints prefixed with `/api/`
- Public (no-auth, no `/api` prefix) routes registered directly in `app.py`: `/i/<share_code>` (short invoice links), `/invoice/view/<token>`, `/invoice/pdf/<token>`, `/feedback`, `/feedback/lookup`, `/feedback/submit`
- Add new blueprints in `__init__.py` via `register_routes()`

**Startup migrations**: `app.py` drops legacy indexes on boot (`customers.mobile_1`, `customers.referral_code_1`, duplicate appointment index). Safe to add more one-time migrations in this block.

**`backend/` root clutter**: dozens of one-off scripts (`migrate_*.py`, `create_*.py`, `fix_*.py`, `verify_*.py`) and status docs (`MIGRATION_COMPLETE.md`, `CONVERSION_STATUS.md`, etc.) live at the `backend/` root from the original SQLite→MongoDB migration (Dec 2025) and later data fixes. They are historical/ad-hoc, not part of the running app and not maintained — don't treat them as current documentation or examples of house style. The only migration mechanism that actually runs is the startup block in `app.py`; `backend/migrations/` holds separate one-off index-creation scripts, also run manually, not on boot.

**Backend Utilities** (`backend/utils/`):
- `auth.py` - JWT handling, decorators: `@require_auth`, `@require_role('manager', 'owner')`, `@optional_auth`
- `branch_filter.py` - Multi-branch filtering: `get_selected_branch()`, `filter_by_branch()`
- `redis_cache.py` - Caching layer (optional, falls back to in-memory)

### Frontend Structure

**API Configuration**: `frontend/src/config.js` - `API_BASE_URL` resolves from `VITE_API_BASE_URL` if set, else `window.location.origin` in prod builds (same-origin, used by the Vercel target), else `http://127.0.0.1:5000` in dev

**API Utility**: `frontend/src/utils/api.js` - Centralized fetch with auth headers
- Use `apiGet()`, `apiPost()`, `apiPut()`, `apiDelete()` for all API calls
- Automatically adds `Authorization` and `X-Branch-Id` headers

**State**:
- Auth: `src/contexts/AuthContext.jsx` - JWT token in `sessionStorage.auth_token`, user in `sessionStorage.auth_user`
- Branch: Stored in `sessionStorage.current_branch` (JSON), sent via `X-Branch-Id` header on every request
- "All Branches" mode: when an owner selects `{isAll: true}` as the current branch, [api.js](frontend/src/utils/api.js) intentionally **omits** the `X-Branch-Id` header so the backend aggregates across branches. Do not fall back to the user's home branch in that path — it would silently re-scope every endpoint.

### Multi-Branch Architecture

- Users have roles: `staff`, `manager`, `owner`
- Data is branch-scoped via `branch` ReferenceField in models
- `X-Branch-Id` header determines data scope; absence of the header (owner-only) means "no scope" → aggregate across branches
- Owners can switch branches; staff/managers locked to their branch
- Use `get_selected_branch(request, user)` in routes to get current branch (returns `None` for owner aggregate mode — code paths must handle that)

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
- Soft deletes: `is_active` or `status='inactive'` (do NOT physically delete)
- Customer uniqueness is a compound `(mobile, branch)` index, not global - same customer can exist across branches
- For embedded documents with ReferenceFields, use `_get_raw_ref_id(item, 'field')` (defined in [bill_routes.py](backend/routes/bill_routes.py)) to read the ObjectId without triggering a lazy dereference (avoids N+1). It reads `item._data[field]` to bypass MongoEngine's auto-deref

### Performance Conventions

- Dashboard endpoints use `@cache_response(ttl=300)` + `@log_performance` from `utils/redis_cache.py`
- Prefer MongoDB aggregation pipelines over Python loops for list endpoints that reduce/group (see `dashboard_routes.py` for examples)
- Batch-fetch referenced docs in bulk rather than relying on lazy dereference inside a loop
- Frontend: run independent fetches via `Promise.all` / `Promise.allSettled`, not sequentially
- Production builds strip `console.log` via terser ([vite.config.js](frontend/vite.config.js))
- `flask-compress` (gzip) is enabled in [app.py](backend/app.py) for JSON, JS, CSS, and PDFs ≥ 500 bytes — keep responses JSON-serializable rather than streaming where possible

### Static / Public Route Precedence

- Single Flask app serves both API (`/api/*`) and the built React SPA from `backend/static/`
- The catch-all `serve(path)` in [app.py](backend/app.py) explicitly skips paths starting with `i/`, `invoice/`, or `feedback` so dedicated public routes win — when adding a new public (non-`/api`) prefix, update that skip list, otherwise the SPA's `index.html` will be served instead

## Testing & Linting

There is no test suite, lint config, or type checker in this repo. `frontend/package.json` exposes only `dev`, `build`, `preview`; `backend` has no test runner configured. Verify changes by running the app (`python app.py` + `npm run dev`) and exercising the affected flow.
