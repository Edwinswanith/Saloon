# Saloon Management System

A full-stack, multi-branch salon and spa business management application. Handles point-of-sale billing, appointments, inventory, staff management, customer relationships, and analytics -- all from a single dashboard.

**Live URL:** https://saloon-management-system-895210689446.europe-west2.run.app

---

## Tech Stack

| Layer      | Technology                                                    |
|------------|---------------------------------------------------------------|
| Frontend   | React 18, Vite 5, Ant Design 6, Zustand, React Query, Recharts |
| Backend    | Flask 3, MongoEngine, PyJWT, bcrypt, ReportLab               |
| Database   | MongoDB Atlas (cloud)                                        |
| Cache      | Redis (optional, in-memory fallback)                         |
| Deployment | Docker (multi-stage) on Google Cloud Run                     |

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- MongoDB Atlas connection string (or a local MongoDB instance)
- (Optional) Docker & Docker Compose

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

### Docker (full stack)

```bash
docker-compose up             # Backend :5000, Frontend :5173
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
|-- Dockerfile                # Multi-stage (Node build -> Python serve)
|-- docker-compose.yml        # Local dev orchestration
|-- cloud_run.bat             # One-click deploy to Google Cloud Run
+-- cloud_run.sh
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
| `API_BASE_URL` | `http://127.0.0.1:5000` (dev) or Cloud Run URL (prod) |

---

## Deployment

Production runs on **Google Cloud Run** (region: `europe-west2`).

```bash
# Windows
cloud_run.bat

# Linux / macOS
./cloud_run.sh
```

The script builds a Docker image, pushes it to Google Artifact Registry, and deploys a new Cloud Run revision.

---

## Database

MongoDB Atlas with 30+ collections covering branches, customers, staff, services, products, packages, bills, appointments, memberships, prepaid packages, expenses, assets, tax settings, referral settings, and more. See `PROJECT_OVERVIEW.md` for the full schema breakdown and data relationships.

---

## Mobile Responsiveness

Fully responsive across desktop (1440px+), tablet (768-1024px), and mobile (<=768px) with touch-friendly UI, collapsible sidebar, and horizontally scrollable tables.

---

## License

Private project.

