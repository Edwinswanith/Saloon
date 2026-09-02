# Saloon Management System

A full-stack, multi-branch salon and spa business management application. Handles point-of-sale billing, appointments, inventory, staff management, customer relationships, and analytics -- all from a single dashboard.

**Live URL:** deployed on Vercel (see Deployment section below)

---

## Tech Stack

| Layer      | Technology                                                    |
|------------|---------------------------------------------------------------|
| Frontend   | React 18, Vite 5, Ant Design 6, Zustand, React Query, Recharts |
| Backend    | Flask 3, MongoEngine, PyJWT, bcrypt, ReportLab               |
| Database   | MongoDB Atlas (cloud)                                        |
| Cache      | Redis (optional, in-memory fallback)                         |
| Deployment | Vercel (SPA + Flask serverless function, same-origin)         |

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- MongoDB Atlas connection string (or a local MongoDB instance)

### Backend

```bash
cd backend
python -m venv myenv
myenv\Scripts\activate        # Windows
# source myenv/bin/activate   # macOS / Linux
pip install -r requirements.txt
python app.py                 # Runs on http://127.0.0.1:5000
```

### Frontend

```bash
cd frontend
npm install
npm run dev                   # Runs on http://localhost:5173
```

---

## Project Structure

```
Saloon/
|-- backend/
|   |-- app.py                # Flask entry point, DB connection
|   |-- models.py             # MongoEngine document models
|   |-- routes/               # Flask Blueprints (30+ route files)
|   |-- services/             # Business logic (PDF generation, etc.)
|   |-- utils/                # auth.py, branch_filter.py, redis_cache.py
|   |-- templates/            # HTML / invoice templates
|   |-- migrations/           # DB migration scripts
|   +-- requirements.txt
|
|-- frontend/
|   |-- src/
|   |   |-- App.jsx           # Root router
|   |   |-- main.jsx          # Entry point
|   |   |-- config.js         # API base URL toggle
|   |   |-- components/       # 50+ React components
|   |   |-- contexts/         # AuthContext (JWT + localStorage)
|   |   |-- hooks/            # Custom hooks
|   |   |-- utils/            # api.js, dateUtils.js, confetti.js
|   |   +-- styles/           # Design tokens, global CSS
|   |-- package.json
|   +-- vite.config.js
|
|-- api/
|   +-- index.py              # Vercel Python entrypoint (imports backend/app.py)
+-- vercel.json                # Rewrites + build config for the Vercel deployment
```

---

## Key Features

1. **Point of Sale (Quick Sale)** -- Multi-item billing for services, packages, products, memberships, and prepaid. Supports cash, card, UPI. PDF invoice generation with GST.
2. **Multi-Branch Support** -- Branch-level data isolation. Owners see all branches; managers and staff are scoped to their own.
3. **Customer Management** -- Profiles, visit history, lead tracking, missed enquiries, feedback, service recovery, customer merge, referral program.
4. **Appointment System** -- Calendar-based booking with staff assignment and status tracking.
5. **Inventory Management** -- Real-time stock tracking, automatic reduction on sale, low-stock alerts.
6. **Staff Management** -- Attendance, leave requests, performance metrics, commission calculation, temporary cross-branch assignments.
7. **Financial Management** -- Cash register (in/out), expense tracking, configurable tax slabs, discount approval workflow.
8. **Memberships & Prepaid** -- Plan templates, customer-specific balances, expiry tracking.
9. **Analytics & Reporting** -- Dashboard KPIs, service sales breakdown, staff performance, business growth trends, customer lifecycle, client value analysis.
10. **Role-Based Access** -- Owner (full access), Manager (branch-level), Staff (limited).

---

## Environment Configuration

### Backend (`backend/app.py`)

| Variable      | Description                              |
|---------------|------------------------------------------|
| `MONGODB_URI` | MongoDB Atlas connection string          |
| `MONGODB_DB`  | `Saloon_prod` (production) / `Saloon` (dev) |

### Frontend (`frontend/src/config.js`)

| Variable       | Description                                  |
|----------------|----------------------------------------------|
| `API_BASE_URL` | `http://127.0.0.1:5000` (dev) or same-origin (prod, via Vercel) |

---

## Deployment

Production runs on **Vercel** — a single project serving the built SPA and the Flask API from the same origin. Deploys automatically on every push to `main`. See the "Vercel (the only deployment target)" section in `CLAUDE.md` for how the Python entrypoint (`api/index.py`) and `vercel.json` rewrites are wired up.

Cloud Run was previously used for production and has been retired — do not reintroduce Docker/Cloud Run deployment tooling.

---

## Database

MongoDB Atlas with 30+ collections covering branches, customers, staff, services, products, packages, bills, appointments, memberships, prepaid packages, expenses, assets, tax settings, referral settings, and more. See `PROJECT_OVERVIEW.md` for the full schema breakdown and data relationships.

---

## Mobile Responsiveness

Fully responsive across desktop (1440px+), tablet (768-1024px), and mobile (<=768px) with touch-friendly UI, collapsible sidebar, and horizontally scrollable tables.

---

## License

Private project.

