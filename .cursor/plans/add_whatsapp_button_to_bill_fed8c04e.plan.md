---
name: Add WhatsApp Button to Bill
overview: Add a WhatsApp button to the invoice preview modal that opens WhatsApp with a pre-filled message containing the bill details. The button will be added to the InvoicePreview component's action buttons section.
todos:
  - id: add-whatsapp-handler
    content: Add handleSendWhatsApp function to InvoicePreview component that formats mobile number and creates WhatsApp URL with pre-filled message
    status: pending
  - id: add-whatsapp-button
    content: Add WhatsApp button to invoice actions section, only visible when customer mobile exists
    status: pending
    dependencies:
      - add-whatsapp-handler
  - id: style-whatsapp-button
    content: Add CSS styling for WhatsApp button with brand color (#25D366) matching existing button styles
    status: pending
    dependencies:
      - add-whatsapp-button
---

# Add WhatsApp Button to Bill

## Overview
Add a WhatsApp button to the invoice preview that appears after checkout. The button will open WhatsApp with a pre-filled message containing bill details.

## Implementation Details

### Files to Modify

1. **[frontend/src/components/InvoicePreview.jsx](frontend/src/components/InvoicePreview.jsx)**
   - Add a `handleSendWhatsApp` function that:
     - Formats the customer mobile number (removes +91, spaces, etc. to get just digits)
     - Creates a formatted bill message template with:
       - Bill number
       - Date and time
       - List of items (name, quantity, price)
       - Summary (subtotal, discount, tax, total)
       - Payment mode
     - Constructs WhatsApp URL: `https://wa.me/{phone}?text={encoded_message}`
     - Opens the URL in a new window/tab
   - Add WhatsApp button in the action buttons section (lines 179-191)
   - Only show button if `customer?.mobile` exists
   - Use WhatsApp icon (can use react-icons FaWhatsapp if available, or text)

2. **[frontend/src/components/InvoicePreview.css](frontend/src/components/InvoicePreview.css)**
   - Add styling for `.whatsapp-btn` class
   - Use WhatsApp brand color (#25D366) for the button
   - Match existing button styles from `.download-btn` and `.review-btn`

### Message Template Format
The WhatsApp message should be formatted as:
```
*Bill Details*

Bill Number: {bill_number}
Date: {booking_date}, {booking_time}

*Items:*
{item_name} - Qty: {quantity} - ₹{total}
...

*Summary:*
Subtotal: ₹{subtotal}
Discount: ₹{discount}
Tax: ₹{tax}
*Total: ₹{total}*

Payment Mode: {payment_mode}

Thank you for your visit!
{branch_name}
```

### Technical Notes
- Use `encodeURIComponent()` to encode the message for the URL
- Handle mobile number formatting: remove +91 prefix, spaces, and non-digits
- WhatsApp web URL format: `https://wa.me/{country_code}{number}` (e.g., `https://wa.me/919876543210`)
- The button should be disabled or hidden if customer mobile is not available
- Ensure the message is concise and readable on mobile devices

## Testing Considerations
- Test with valid mobile numbers (with/without +91 prefix)
- Test with missing customer mobile (button should not appear)
- Verify message formatting and encoding
- Test on both desktop and mobile browsers