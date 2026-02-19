---
name: Fix Cash Register Display
overview: ""
todos:
  - id: add-require-auth-checkout
    content: Add @require_auth decorator to checkout_bill route in bill_routes.py
    status: pending
  - id: auth-error-cash-register
    content: Handle 401 responses in CashRegister.jsx with user-visible error instead of silent empty state
    status: pending
  - id: cash-txn-save-warning
    content: Include cash transaction save failure in checkout JSON response so frontend can warn the user
    status: pending
---

# Fix Cash Register Card/UPI Payment Display

## What is confirmed working

- Card transaction **IS saved correctly** in MongoDB: `payment_method: "card"`, `amount: 9799`, `branch: DLF`, `transaction_date: 2026-02-19`
- Backend save logic in [`bill_routes.py`](backend/routes/bill_routes.py) (lines 1303-1322) is correct
- Frontend summary mapping in [`CashRegister.jsx`](frontend/src/components/CashRegister.jsx) is correct

## Root Cause

The `checkout_bill` route has **no `@require_auth` decorator**, which creates an auth inconsistency between saving and reading:

```python
# bill_routes.py line 938 -- MISSING @require_auth
@bill_bp.route('/bills/<id>/checkout', methods=['POST'])
def checkout_bill(id):
    ...
    cash_txn = CashTransaction(...)
    cash_txn.save()  # Saves correctly ✓
```

The Cash Register GET routes **do** require auth. If the user's JWT token is expired or references a deleted account, `@require_auth` returns 401, and the frontend silently catches it and shows empty data -- the user sees nothing with no error message.

Also, the `CashTransaction` save failure is **silently swallowed**:

```python
except Exception as e:
    print(f"[CHECKOUT] Warning: Failed to record cash transaction: {e}")
    # No re-raise, no user-facing error
```

## Data Flow

```mermaid
flowchart TD
    A[QuickSale: Select Card payment] --> B["apiPost /api/bills/id/checkout"]
    B --> C["checkout_bill route (NO @require_auth)"]
    C --> D["CashTransaction saved to MongoDB\npayment_method=card, branch=DLF"]
    D --> E[User navigates to Cash Register]
    E --> F["apiGet /api/cash/transactions?date=2026-02-19"]
    F --> G["@require_auth checks JWT"]
    G -->|JWT valid| H["get_selected_branch → filter by DLF"]
    G -->|JWT expired/invalid| I["Returns 401 → frontend shows empty"]
    H --> J["Query matches card transaction ✓"]
    J --> K["Card total shows in UI ✓"]
    I --> L["User sees empty Cash Register ✗"]
```

## Fixes

### 1. Add `@require_auth` to `checkout_bill`

In [`backend/routes/bill_routes.py`](backend/routes/bill_routes.py) line 938-939, add the decorator so the auth context is consistent with all other routes.

### 2. Show auth error in Cash Register instead of silent empty state

In [`frontend/src/components/CashRegister.jsx`](frontend/src/components/CashRegister.jsx), catch 401 responses and show a "Session expired, please log in again" message instead of silently showing empty data.

### 3. Make cash transaction save failure visible in checkout response

In [`backend/routes/bill_routes.py`](backend/routes/bill_routes.py) lines 1321-1322, include a warning in the checkout response JSON if the cash transaction failed to save, so the frontend can alert the user.