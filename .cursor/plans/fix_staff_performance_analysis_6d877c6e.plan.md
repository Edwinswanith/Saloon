---
name: Fix Staff Performance Analysis
overview: Remove branch filtering from Staff Performance Analysis to show all staff company-wide, matching the Analytics Dashboard's "top performer" behavior which already works company-wide.
todos:
  - id: remove-branch-filter
    content: Remove branch filtering from staff_performance_analysis endpoint in report_routes.py
    status: in_progress
  - id: test-both-staff
    content: Verify both Ajay Kumar and Rohan Mehta appear in Staff Performance Analysis
    status: pending
---

# Fix Staff Performance Analysis to Show All Staff (Company-Wide)

## Problem

Staff Performance Analysis currently filters by selected branch, so switching branches shows different staff. This is incorrect - the section should answer "Who are my top-performing staff?" across the entire company, not per-branch.

## Current Data

- Ajay Kumar: DLF branch, 15,875 revenue (actual top performer)
- Rohan Mehta: Main Road branch, 9,936 revenue

## Root Cause

The `/api/reports/staff-performance` endpoint applies branch filtering at line 675-684 in [`backend/routes/report_routes.py`](backend/routes/report_routes.py):

```python
branch = get_selected_branch(request, current_user)
if branch:
    match_stage["branch"] = ObjectId(str(branch.id))
```

This is inconsistent with the `/api/dashboard/top-performer` endpoint which is already company-wide.

## Solution

Remove branch filtering from the Staff Performance Analysis endpoint to make it company-wide.

### Files to Modify

**1. [`backend/routes/report_routes.py`](backend/routes/report_routes.py)** (lines 656-780)

In the `staff_performance_analysis()` function:

- Remove lines 674-684 (branch filtering logic)
- Remove the branch filter from `match_stage`
- Keep all other aggregation logic intact

Before:

```python
# Branch filtering
branch = get_selected_branch(request, current_user)

match_stage = {
    "is_deleted": False,
    "bill_date": {"$gte": start, "$lte": end},
    "items.staff": {"$ne": None}
}
if branch:
    match_stage["branch"] = ObjectId(str(branch.id))
```

After:

```python
# Company-wide analysis (no branch filtering)
match_stage = {
    "is_deleted": False,
    "bill_date": {"$gte": start, "$lte": end},
    "items.staff": {"$ne": None}
}
```

## Expected Result

After this change:

- Staff Performance Analysis will show ALL staff from ALL branches
- Ajay Kumar (15,875) will appear as #1
- Rohan Mehta (9,936) will appear as #2
- Rankings will be company-wide regardless of selected branch
- This matches the behavior of Analytics Dashboard's Top Performer section

## Why This is Correct

The question "Who are my top-performing staff?" is a company-wide business intelligence question. Branch filtering belongs in operational reports (Staff Incentive Report, etc.) but not in strategic performance analysis.