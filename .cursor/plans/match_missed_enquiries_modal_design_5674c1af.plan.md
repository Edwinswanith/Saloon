# Match Missed Enquiries Modal Design to Customer List Modal

## Analysis

The Customer List edit modal has a clean, consistent design that needs to be replicated in the Missed Enquiries modal. Key differences identified:

### Customer List Modal Structure:
- Simple structure: `modal-overlay` > `modal-content` (direct content, no nested header/body)
- Modal content: `padding: 24px`, `border-radius: 12px`, `max-width: 500px`
- Form spacing: `margin-bottom: 16px` for form groups
- Label styling: `margin-bottom: 6px`, `font-weight: 500`, `color: var(--text-secondary)`
- Input styling: `padding: 10px 14px`, `border: 1px solid var(--border-medium)`, `border-radius: 6px`
- Modal actions: `margin-top: 24px`, `padding-top: 20px`, `border-top: 1px solid var(--border-light)`, no background color
- Button styling: Cancel uses `border: 1px solid var(--border-medium)`, `border-radius: 6px`

### Missed Enquiries Modal Current Structure:
- Complex structure: `modal-overlay` > `modal-content` with flex layout (though header/body not used in JSX)
- Modal content: `padding: 0`, `border-radius: 16px`, `max-width: 600px`
- Form spacing: `margin-bottom: 20px` for form groups
- Label styling: `margin-bottom: 8px`, `font-weight: 600`, `color: #374151`
- Input styling: `padding: 12px 14px`, `border: 2px solid #e5e7eb`, `border-radius: 10px`
- Modal actions: `padding: 20px 24px`, `background: #f9fafb`, `border-top: 1px solid #e5e7eb`
- Button styling: Cancel uses `border: 2px solid #e5e7eb`, `border-radius: 8px`

## Changes Required

### 1. Update [frontend/src/components/MissedEnquiries.css](frontend/src/components/MissedEnquiries.css)

Update the modal styles to match Customer List exactly:

**Modal Content:**
- Change `padding: 0` to `padding: 24px`
- Change `border-radius: 16px` to `border-radius: 12px`
- Change `max-width: 600px` to `max-width: 500px`
- Remove `display: flex` and `flex-direction: column`
- Remove `overflow: hidden`

**H2 Title:**
- Ensure `margin: 0 0 20px 0`
- Ensure `font-size: 20px`
- Ensure `font-weight: 600`
- Ensure `color: var(--text-primary)`

**Form Group:**
- Change `margin-bottom: 20px` to `margin-bottom: 16px`

**Form Group Label:**
- Change `margin-bottom: 8px` to `margin-bottom: 6px`
- Change `font-weight: 600` to `font-weight: 500`
- Change `color: #374151` to `color: var(--text-secondary)`

**Form Inputs/Selects/Textareas:**
- Change `padding: 12px 14px` to `padding: 10px 14px`
- Change `border: 2px solid #e5e7eb` to `border: 1px solid var(--border-medium)`
- Change `border-radius: 10px` to `border-radius: 6px`
- Remove explicit `background: white` (inherit from modal)

**Modal Actions:**
- Change `padding: 20px 24px` to `margin-top: 24px` and `padding-top: 20px`
- Change `border-top: 1px solid #e5e7eb` to `border-top: 1px solid var(--border-light)`
- Remove `background: #f9fafb`
- Keep `justify-content: flex-end` and `gap: 12px`

**Cancel Button:**
- Change `border: 2px solid #e5e7eb` to `border: 1px solid var(--border-medium)`
- Change `border-radius: 8px` to `border-radius: 6px`
- Ensure `background: white` and `color: var(--text-secondary)`

**Save Button:**
- Keep existing gradient and styling (already matches)
- Ensure `border-radius: 8px` (already correct)

### 2. No JSX Changes Required

The JSX structure in MissedEnquiries.jsx is already compatible - it uses the same basic structure (modal-overlay > modal-content with direct h2 and form). The form wrapper doesn't affect the styling.

## Implementation Details

The modal will have:
- Same padding and spacing as Customer List
- Same border radius (12px instead of 16px)
- Same max-width (500px instead of 600px)
- Same form field styling (thinner borders, smaller padding, smaller border radius)
- Same label styling (lighter weight, smaller margin)
- Same modal actions styling (no background color, proper spacing)
- Same button styling (thinner borders, smaller border radius for cancel)

