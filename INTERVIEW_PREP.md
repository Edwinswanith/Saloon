# Interview Prep — AI Engineer (Salon CRM Project)

> Tip: Read these out loud. Keep answers under 60 seconds each. Be confident.

---

## PROJECT INTRO

**Q: Tell me about this project.**
> "I built a full-stack Salon Management CRM from scratch. It handles appointments, billing, inventory, staff management, and analytics — all with multi-branch support. The backend is Flask with MongoDB, the frontend is React with Ant Design, and it's deployed on Google Cloud Run. I used Claude AI as a co-pilot throughout the build."

**Q: Why did you build this?**
> "Small salon chains don't have affordable tools that handle multiple branches in one system. I wanted something that covers the full business loop — walk-ins, scheduling, invoices, and owner-level reports."

**Q: What was the hardest part?**
> "Three things — keeping data isolated per branch, handling duplicate customers across branches, and optimizing performance. I replaced Python loops with MongoDB aggregation pipelines which improved speed significantly."

---

## PACKAGES & TECH USED

**Q: What frontend packages did you use?**

| Package | Why |
|---|---|
| `React 18` | UI framework |
| `Ant Design 6` | Component library — tables, forms, modals |
| `Recharts` | Charts — line, bar, pie for dashboard analytics |
| `TanStack React Query` | Server state, caching, background refetch |
| `TanStack React Table` | Advanced table rendering with sorting/filtering |
| `Zustand` | Lightweight global state (auth, branch) |
| `Framer Motion` | UI animations |
| `React Hook Form` | Form state and validation |
| `React Hot Toast` | Notifications/alerts |
| `React Icons` | Icon set |
| `React Content Loader` | Skeleton loading screens |
| `Day.js` | Date formatting and manipulation |
| `React Datepicker` | Date picker UI |
| `XLSX` | Export tables to Excel |
| `NProgress` | Top loading bar for navigation |
| `Canvas Confetti` | Celebration animation on bill payment |
| `Vite + Terser` | Build tool; Terser strips console.log in production |

**Q: What backend packages did you use?**

| Package | Why |
|---|---|
| `Flask 3.0` | Web framework |
| `MongoEngine 0.27` | ODM — object-document mapping for MongoDB |
| `PyMongo 4.6` | Low-level MongoDB driver |
| `PyJWT 2.8` | JWT token creation and verification |
| `bcrypt 4.1` | Password hashing |
| `python-dateutil` | Date parsing and range calculations |
| `ReportLab` | PDF invoice/report generation |
| `Redis` | Optional caching layer (falls back to in-memory) |
| `Gunicorn 22` | Production WSGI server (2 workers, 4 threads) |
| `flask-compress` | Gzip compression on API responses |
| `Flask-CORS` | Cross-origin request handling |
| `requests` | HTTP calls to external APIs if needed |

---

## CHARTS & ANALYTICS

**Q: What chart library did you use and why?**
> "I used Recharts. It's built on D3 and integrates cleanly with React. It's composable — you build charts by combining components like `<LineChart>`, `<BarChart>`, `<PieChart>`, `<Tooltip>`, `<Legend>` — which made it easy to customize for the dashboard."

**Q: What kind of charts are in the dashboard?**
> - Line chart — daily/weekly revenue trends
> - Bar chart — staff performance and top performers
> - Pie chart — payment method distribution (cash, card, UPI)
> - Funnel — new vs returning client breakdown
> - KPI cards — total bills, revenue, tax collected

**Q: How did you make the dashboard fast?**
> "I run data fetches in parallel using `Promise.all` and `Promise.allSettled` on the frontend. On the backend, I use MongoDB aggregation pipelines instead of fetching all documents and grouping in Python. I also cache dashboard responses for 5 minutes using a decorator."

---

## API DESIGN

**Q: How are your APIs structured?**
> "All endpoints are prefixed with `/api/`. They're organized into Flask Blueprints — one file per feature: `staff_routes`, `billing_routes`, `appointment_routes`, etc. All registered in a central `routes/__init__.py`."

**Q: How does the frontend call APIs?**
> "I have a centralized `api.js` utility with `apiGet()`, `apiPost()`, `apiPut()`, `apiDelete()` functions. Every call automatically attaches the `Authorization: Bearer <token>` header and the `X-Branch-Id` header. No raw `fetch` calls scattered in components."

**Q: How does multi-branch filtering work?**
> "The frontend sends `X-Branch-Id` in every request header. The backend reads it via `get_selected_branch(request, user)`, validates the user has access to that branch, and all DB queries are scoped to that branch — like `Bill.objects(branch=branch)`."

**Q: How did you handle auth?**
> "JWT tokens. Login returns a token, stored in `localStorage`. Every API call sends it in the `Authorization` header. Backend decorators `@require_auth` and `@require_role('manager', 'owner')` protect routes. Passwords are hashed with bcrypt before storing."

**Q: What HTTP status codes do you use and why?**
> - `200` — success, existing resource reused
> - `201` — new resource created
> - `400` — bad request / validation error
> - `401` — not authenticated
> - `403` — authenticated but not authorized
> - `404` — resource not found
> - `500` — server error

---

## MONGODB / DATABASE

**Q: Why MongoDB over SQL?**
> "Salon data is flexible — services, packages, and appointments have varying fields. MongoDB's document model fits that better. Also MongoEngine's ODM made rapid development fast."

**Q: What is an aggregation pipeline?**
> "It's MongoDB's way of processing data in stages — like a SQL GROUP BY but more powerful. For example: filter bills by branch and date → group by staff → sum revenue → sort. All inside the database, much faster than loading everything into Python."

**Q: How did you handle duplicate customers?**
> "Same mobile number is a duplicate within a branch but allowed across branches. I dropped the global `unique=True` on mobile and replaced it with a compound `(mobile, branch)` index. Creation logic: same branch + same mobile → reuse existing customer. Different branch → create new."

**Q: What indexes did you add?**
> "Compound indexes on the most queried field combinations — for example `(branch, created_at)` on Bills, `(branch, status)` on Appointments. This makes date-range queries and status filters fast even at scale."

---

## AI CONCEPTS

**Q: How did you use AI in this project?**
> "I used Claude as an engineering co-pilot. I'd describe a problem with context — existing code, constraints — and it would draft code. I'd review it, catch issues, correct via follow-up prompts, and iterate. It accelerated the boilerplate and pattern work significantly."

**Q: What is prompt engineering?**
> "Structuring your input to an LLM to get reliable, high-quality output. Techniques I used: injecting existing code as context before asking for changes, stating constraints first ('don't use global indexes'), and iterative refinement — treating the first output as a draft."

**Q: Did AI ever get things wrong?**
> "Yes — it suggested global unique indexes when I needed compound ones, generated Python loops where aggregation pipelines were better, and sometimes used MongoEngine methods that don't exist. I caught these by reading every output carefully, testing, and correcting."

**Q: What is RAG?**
> "Retrieval-Augmented Generation. You retrieve relevant documents from a vector store and inject them into the LLM's context before generating a response. It grounds the model in real data without retraining. Useful for building a chatbot that answers questions about your own data."

**Q: What is fine-tuning vs prompting?**
> "Prompting steers the model at inference time — no weights change, cheap and fast. Fine-tuning updates model weights on your own dataset — deeper behavioral change but expensive. For most product features, prompting is enough."

**Q: What is hallucination?**
> "When an LLM generates confident but wrong output. You mitigate it by grounding responses in retrieved facts (RAG), asking the model to cite sources, verifying programmatically, and using lower temperature for factual tasks."

**Q: What is temperature?**
> "A parameter from 0 to 1 that controls randomness. Low temperature (0–0.2) = deterministic output, good for code and facts. High temperature (0.8–1) = creative, varied output. I used low temperature for code generation."

**Q: What is an AI Agent?**
> "An LLM that takes actions in a loop — calling tools, reading files, writing code, running commands — until a goal is achieved. Instead of one response, it plans and executes steps autonomously."

---

## DEPLOYMENT

**Q: How is this deployed?**
> "Multi-stage Docker build. Backend runs Gunicorn. Frontend is a Vite production build served as static files. Deployed to Google Cloud Run with min-instances=1 to avoid cold starts, 512MB memory, concurrency of 80."

**Q: Why Cloud Run instead of a traditional server?**
> "It's serverless — scales to zero when idle, scales up automatically under load. No server maintenance. Pay per request. For an MVP or small business app, it's cost-effective and simple to deploy."

---

## BEHAVIORAL

**Q: What's your biggest learning from this project?**
> "AI accelerates the 60% that's boilerplate and patterns. The other 40% — architecture decisions, debugging subtle bugs, performance tradeoffs — still needs real engineering judgment. The skill is knowing which is which."

**Q: What would you add next?**
> "A RAG-based chatbot so owners can ask their business data questions in plain English. Also real-time appointment notifications via WebSockets, and anomaly detection on daily revenue."

**Q: How do you verify AI-generated code?**
> "I read it line by line like a code review. Check for edge cases the AI missed — nulls, auth gaps, wrong DB calls. Run it against real data. Treat the first output as a draft, not production code."

---

*Last updated: 2026-03-19*
