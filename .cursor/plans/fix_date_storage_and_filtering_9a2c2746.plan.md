---
name: Fix Date Storage and Filtering
overview: Fix timezone issues in bill date storage and filtering by using local date formatting instead of UTC conversion, ensuring bills are stored and filtered correctly based on the actual local date.
todos: []
---

# Fix Date Storage and Filtering for Bills

## Problem Analysis

The issue occurs because:

1. **Frontend date conversion**: Using `toISOString().split('T')[0]` converts local dates to UTC, which can shift the date (e.g., 2026-01-06 02:00 AM IST becomes 2026-01-05 20:30:00 UTC, resulting in "2026-01-05")
2. **Backend date storage**: When receiving a date string, the backend assumes it's a local date and converts it to UTC, but if the frontend already sent the wrong date, the stored date will be incorrect
3. **Date filtering**: The filter uses the same flawed `toISOString()` conversion, so it filters by the wrong date range

## Solution

Use local date formatting functions that preserve the local date without timezone conversion.

## Implementation Steps

### 1. Create Local Date Formatting Utility (Frontend)

**File**: `frontend/src/utils/dateUtils.js` (new file)

- Create `formatLocalDate(date)` function that formats a Date object as YYYY-MM-DD using local date components
- Create `getLocalDateString(date)` helper that ensures we get the local date, not UTC date
```javascript
export const formatLocalDate = (date) => {
  if (!date) return null
  const d = new Date(date)
  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

export const getLocalDateString = (date) => {
  return formatLocalDate(date)
}
```


### 2. Update QuickSale Component

**File**: `frontend/src/components/QuickSale.jsx`

- Import the new date utility
- Replace `selectedDate.toISOString().split('T')[0] `with `formatLocalDate(selectedDate)` in:
  - Bill creation (line ~1024)
  - Checkout (line ~1216)
  - Appointment creation (line ~666)

### 3. Update List of Bills Component

**File**: `frontend/src/components/ListOfBills.jsx`

- Import the new date utility
- Replace `today.toISOString().split('T')[0] `with `formatLocalDate(today)` in `getDateRange()` function
- Do the same for `yesterday`, `weekStart`, `monthStart`, `yearStart`

### 4. Verify Backend Date Handling

**Files**: `backend/routes/bill_routes.py`, `backend/routes/report_routes.py`

- Ensure the backend correctly interprets incoming date strings (YYYY-MM-DD) as local dates
- Verify the timezone conversion logic (IST = UTC+5:30) is correct
- The current logic should work correctly once the frontend sends the correct local date

### 5. Test Date Display

**File**: `frontend/src/components/ListOfBills.jsx`

- Verify `formatDate()` function correctly displays dates from UTC ISO strings
- The current implementation should work, but ensure it handles edge cases

## Expected Outcome

- Bills created today will be stored with today's date (local timezone)
- Filtering by "Today" will correctly show bills created today
- Date display will show the correct local date
- No more date shifts due to UTC conversion

## Testing Checklist

1. Create a bill with today's date selected → Verify it's stored correctly
2. Filter by "Today" → Verify it shows bills created today
3. Check date display → Verify dates match the actual creation date
4. Test edge cases (late night/early morning) → Verify dates don't shift