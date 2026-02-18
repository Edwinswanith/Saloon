---
name: Fix Membership Items Not Appearing in Invoice
overview: Fix the issue where membership items are not appearing in generated invoices. The problem is that membership items don't have a membership reference set (it's always None), so the batch lookup fails. The fix ensures membership items are properly included using the denormalized name field and handles the case where membership reference is missing.
todos:
  - id: fix-membership-resolution
    content: Update _resolve_bill_items() to properly handle membership items that don't have a membership reference, ensuring they use the denormalized name field
    status: pending
  - id: test-membership-invoice
    content: Test that membership items appear correctly in generated invoices (HTML and PDF)
    status: pending
    dependencies:
      - fix-membership-resolution
---

# Fix Membership Items Not Appearing in Invoice

## Problem Analysis

When membership items are added to a bill:

1. The `membership` reference field in `BillItemEmbedded` is never set (stays `None`) because the code looks up `MembershipPlan` but doesn't create a `Membership` document reference
2. In `_resolve_bill_items()`, when trying to batch-fetch membership names, `_get_raw_ref_id(item, 'membership')` returns `None` because there's no membership reference
3. The `membership_map` remains empty, so membership names can't be resolved from the map
4. While the code should fall back to using `item.name` (which is set from MembershipPlan), there might be an issue with how this is handled

## Root Cause

The issue is in the `_resolve_bill_items()` function:

- Line 120-122: Collects membership IDs, but since `membership` reference is `None`, no IDs are collected
- Line 143-146: Tries to fetch `Membership` objects, but the list is empty
- Line 170-172: Tries to resolve name from empty `membership_map`
- Line 159: Should use `item.name` if it exists, but there might be an edge case

## Solution

### Option 1: Use MembershipPlan for Lookup (Recommended)

Since membership items reference `MembershipPlan` (not `Membership`), we should:

1. Store the MembershipPlan ID in a separate field or use the name field
2. Look up MembershipPlan when resolving items instead of Membership

### Option 2: Ensure Name Field is Always Used

Since the name is already denormalized and stored, ensure the resolution logic properly uses it for membership items.

## Implementation

### Fix 1: Update `_resolve_bill_items()` to Handle Membership Items Without References

**File:** [`backend/routes/bill_routes.py`](backend/routes/bill_routes.py)

In the `_resolve_bill_items()` function, ensure membership items are included even when they don't have a membership reference:

1. **Improve name resolution for membership items** (around line 159-174):

- Check `item.name` first (already done)
- For membership items specifically, if name exists, use it immediately
- Don't require membership reference to be set

2. **Add fallback for membership items**:

- If `item_type == 'membership'` and `item.name` exists, use it
- Don't try to look up from `membership_map` if reference is missing

### Fix 2: Ensure Membership Items Are Not Filtered Out

Verify that all items are included in the returned list regardless of whether they have references set.

### Fix 3: Debug Logging (Optional)

Add logging to help diagnose if membership items are being processed:

- Log when membership items are found
- Log the resolved name for membership items
- Log if membership items are being skipped

## Files to Modify

1. **[backend/routes/bill_routes.py](backend/routes/bill_routes.py)**

- Update `_resolve_bill_items()` function to properly handle membership items without references
- Ensure membership items use the denormalized `name` field when membership reference is missing

## Testing

After the fix:

- [ ] Add a membership to a bill
- [ ] Generate invoice (HTML and PDF)
- [ ] Verify membership appears in invoice with correct name
- [ ] Verify membership price and total are correct
- [ ] Verify membership appears alongside services and products

## Notes

- The denormalized `name` field should already contain the membership plan name
- Membership items should work the same way as other items that might have missing references
- The fix should be backward compatible with existing bills