---
name: Fix Branch Selector Dropdown Z-Index in Tablet View
overview: The branch selector dropdown is being hidden behind page content in tablet view due to stacking context and overflow clipping issues. The dropdown needs to be rendered using React Portal to escape the GlobalHeader's overflow constraints and ensure proper z-index layering.
todos:
  - id: portal-implementation
    content: Update BranchSelector.jsx to use React Portal (createPortal) for rendering dropdown and overlay to document.body
    status: completed
  - id: css-verification
    content: Verify and update BranchSelector.css z-index values and add tablet-specific media queries if needed
    status: completed
    dependencies:
      - portal-implementation
  - id: test-tablet-view
    content: Test dropdown visibility and functionality in tablet view (768px-1024px)
    status: completed
    dependencies:
      - portal-implementation
      - css-verification
---

# Fix Branch Selector Dropdown Z-Index in Tablet View

## Problem Analysis

The branch selector dropdown is hidden behind page content in tablet view (768px-1024px) because:

1. **Overflow Clipping**: `GlobalHeader` has `overflow: hidden` by default, which clips the dropdown even though it's `position: fixed`
2. **Stacking Context**: The dropdown is rendered inside `GlobalHeader` which creates a stacking context that can interfere with z-index
3. **Tablet Breakpoint Gap**: At 768px and below, `overflow: visible` is set, but between 768px-1024px (tablet landscape), `overflow: hidden` remains active

## Solution

Use React Portal to render the dropdown and overlay at the document body level, ensuring they escape all parent overflow and stacking context constraints.

## Implementation Steps

### 1. Update BranchSelector Component

- Import `createPortal` from `react-dom`
- Render the dropdown and overlay using Portal to `document.body`
- Keep the button in its original position (no portal needed)

### 2. Update BranchSelector CSS

- Ensure z-index values remain high (already 99999/100000)
- Add tablet-specific media query if needed to ensure visibility
- Verify dropdown positioning works correctly with portal

### 3. Test Responsive Behavior

- Verify dropdown displays correctly in tablet view (768px-1024px)
- Ensure mobile and desktop views still work correctly
- Check that dropdown positioning calculations still work with portal

## Files to Modify

1. `frontend/src/components/BranchSelector.jsx` - Add React Portal for dropdown rendering
2. `frontend/src/components/BranchSelector.css` - Verify z-index and add tablet-specific rules if needed

## Technical Details

The dropdown is currently rendered inline within the `GlobalHeader` component. By using `createPortal`, we'll render it directly to `document.body`, which:

- Escapes the `overflow: hidden` constraint of `GlobalHeader`
- Avoids stacking context issues
- Maintains the same visual positioning (since it's already `position: fixed`)
- Works consistently across all viewport sizes