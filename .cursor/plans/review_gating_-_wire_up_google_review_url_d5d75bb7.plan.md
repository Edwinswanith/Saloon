---
name: Review Gating - Wire Up Google Review URL
overview: ""
todos:
  - id: env-var
    content: Add GOOGLE_REVIEW_URL to backend/.env (blank placeholder)
    status: pending
  - id: backend-url
    content: Read GOOGLE_REVIEW_URL from os.environ in feedback_routes.py and pass to render_template
    status: pending
  - id: frontend-config
    content: Export GOOGLE_REVIEW_URL from frontend/src/config.js
    status: pending
  - id: feedback-jsx
    content: Replace PLACEHOLDER_GOOGLE_REVIEW_LINK constant in Feedback.jsx with the imported config value
    status: pending
---

# Review Gating - Wire Up Google Review URL

The review gating system (public feedback page, service recovery cases, admin dashboard) is **already fully built**. The only task is replacing the two placeholder Google Review URL values with a real, configurable environment variable.

## What Already Exists (No Changes Needed)

- [`backend/templates/feedback/feedback.html`](backend/templates/feedback/feedback.html) - Public customer-facing review page with star rating, Google redirect step, and service recovery step
- [`backend/routes/feedback_routes.py`](backend/routes/feedback_routes.py) - Creates `ServiceRecoveryCase` automatically for rating <= 3, sets `google_review_eligible=True` for rating >= 4
- [`backend/routes/service_recovery_routes.py`](backend/routes/service_recovery_routes.py) - Assign, resolve, and list endpoints for internal cases
- [`frontend/src/components/ServiceRecovery.jsx`](frontend/src/components/ServiceRecovery.jsx) - Manager dashboard to manage open/resolved cases
- [`frontend/src/components/Feedback.jsx`](frontend/src/components/Feedback.jsx) - Admin modal already has Google review prompt and service recovery message

## Rating Thresholds (Already Correct)

| Rating | Action |
|--------|--------|
| 4 or 5 stars | Google Review prompt shown |
| 1, 2, or 3 stars | Service Recovery case created internally |

## Changes Required

### 1. Add env variable to `.env`

Add `GOOGLE_REVIEW_URL=` to `D:\Saloon\backend\.env` (value left blank for now, filled in when URL is ready).

### 2. Pass URL from `app.py` to template

Update [`backend/routes/feedback_routes.py`](backend/routes/feedback_routes.py): read `GOOGLE_REVIEW_URL` from `os.environ` and pass it to `render_template`.

### 3. Wire URL into admin `Feedback.jsx`

Update [`frontend/src/components/Feedback.jsx`](frontend/src/components/Feedback.jsx): replace the hardcoded placeholder constant with the URL fetched from a new `/api/config/google-review-url` endpoint (or simply as a one-line config in `frontend/src/config.js`).

The simplest approach: add `GOOGLE_REVIEW_URL` to `config.js` as an exported constant (empty string for now), and import it in `Feedback.jsx`.