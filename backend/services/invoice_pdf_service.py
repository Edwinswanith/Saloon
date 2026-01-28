"""
Invoice PDF Generation Service
Generates PDF invoices using ReportLab
"""
import os
from io import BytesIO
from flask import render_template, current_app


def format_currency(value):
    """Format currency with Rupee symbol and 2 decimal places"""
    try:
        amount = float(value or 0)
        return f"\u20B9{amount:,.2f}"
    except (ValueError, TypeError):
        return "\u20B90.00"


def format_currency_no_decimals(value):
    """Format currency with Rupee symbol without decimal places"""
    try:
        amount = float(value or 0)
        return f"\u20B9{int(round(amount)):,}"
    except (ValueError, TypeError):
        return "\u20B90"


def format_mobile(mobile):
    """Format mobile number with +91 prefix"""
    if not mobile:
        return ''
    formatted = str(mobile).strip()
    if formatted.startswith('+91'):
        if not formatted.startswith('+91 '):
            formatted = '+91 ' + formatted[3:].strip()
    elif formatted.startswith('91'):
        formatted = '+91 ' + formatted[2:].strip()
    elif not formatted.startswith('+'):
        formatted = '+91 ' + formatted
    return formatted


def register_template_filters(app):
    """Register custom Jinja2 filters for invoice template"""
    app.jinja_env.filters['format_currency'] = format_currency
    app.jinja_env.filters['format_currency_no_decimals'] = format_currency_no_decimals
    app.jinja_env.filters['format_mobile'] = format_mobile


def render_invoice_html(invoice_data, show_actions=False):
    """
    Render invoice HTML from template

    Args:
        invoice_data: Dictionary containing invoice information
        show_actions: Whether to show action buttons (True for viewing, False for PDF)

    Returns:
        str: Rendered HTML string
    """
    return render_template(
        'invoice/invoice.html',
        invoice_number=invoice_data.get('invoice_number', 'N/A'),
        bill_number=invoice_data.get('bill_number', 'N/A'),
        booking_date=invoice_data.get('booking_date', 'N/A'),
        booking_time=invoice_data.get('booking_time', 'N/A'),
        customer=invoice_data.get('customer', {}),
        branch=invoice_data.get('branch', {}),
        items=invoice_data.get('items', []),
        summary=invoice_data.get('summary', {}),
        payment=invoice_data.get('payment', {}),
        show_actions=show_actions
    )


def generate_invoice_pdf(invoice_data):
    """
    Generate PDF invoice from invoice data using ReportLab

    Args:
        invoice_data: Dictionary containing invoice information

    Returns:
        bytes: PDF file as bytes
    """
    return generate_invoice_pdf_reportlab(invoice_data)


def generate_invoice_pdf_reportlab(invoice_data):
    """
    Fallback PDF generation using ReportLab
    Matches the HTML template layout for consistency

    Args:
        invoice_data: Dictionary containing invoice information

    Returns:
        bytes: PDF file as bytes
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER

    buffer = BytesIO()
    page_width = A4[0] - (0.75*inch * 2)  # Total content width

    doc = SimpleDocTemplate(buffer, pagesize=A4,
                           leftMargin=0.75*inch, rightMargin=0.75*inch,
                           topMargin=0.5*inch, bottomMargin=0.5*inch)
    story = []

    styles = getSampleStyleSheet()

    # Styles matching HTML template
    title_center_style = ParagraphStyle(
        'TitleCenter',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor('#1f2937'),
        spaceAfter=8,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )

    header_center_style = ParagraphStyle(
        'HeaderCenter',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#4b5563'),
        spaceAfter=4,
        alignment=TA_CENTER
    )

    left_text_style = ParagraphStyle(
        'LeftText',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#1f2937'),
        spaceAfter=2
    )

    right_text_style = ParagraphStyle(
        'RightText',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#1f2937'),
        spaceAfter=2,
        alignment=TA_RIGHT
    )

    small_right_style = ParagraphStyle(
        'SmallRight',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#4b5563'),
        alignment=TA_RIGHT
    )

    # Branch information mapping (matches View Bill React component)
    BRANCH_INFO = {
        'Main Road': {
            'address': ['55, Duraisamy Complex,', 'Manapakkam Main Road,', 'Chennai - 600125'],
            'phone': '044-22520395, 044-66126131'
        },
        'EB': {
            'address': ['3/238-A, Usha Complex,', 'Manapakkam,', 'Chennai - 600125'],
            'phone': '044-22521064, 044-43531642'
        },
        'Madanandapuram': {
            'address': ['6A, Madha Nagar Main Road,', 'Rajeshwari Avenue,', 'Near Pon Vidhyashram School, Chennai'],
            'phone': '044-48645868'
        },
        'Kolapakkam': {
            'address': ['67, Near Little Flower School,', 'PT Nagar, Chennai'],
            'phone': '044-49504722'
        },
        'Kovur': {
            'address': ['1/150, Kundrathur Main Road,', 'Near Maadha Medical College,', 'Kovur, Chennai - 600128'],
            'phone': '9500186074'
        },
        'DLF': {
            'address': ['2/914, Krishnaveni Nagar,', 'Near DLF Back Gate,', 'Mugalivakkam, Chennai - 600116'],
            'phone': '044-48543022, 9840192264'
        }
    }

    # Extract data
    branch = invoice_data.get('branch', {})
    customer = invoice_data.get('customer', {})
    payment = invoice_data.get('payment', {})
    summary = invoice_data.get('summary', {})
    items = invoice_data.get('items', [])
    invoice_number = invoice_data.get('invoice_number', invoice_data.get('bill_number', 'N/A'))
    booking_date = invoice_data.get('booking_date', 'N/A')
    booking_time = invoice_data.get('booking_time', 'N/A')

    # Company name is hardcoded to match View Bill
    company_name = 'Priyanka Nature Cure'

    # Look up branch info from mapping (case-insensitive)
    branch_name = branch.get('name', '').strip()
    branch_info = None
    for key in BRANCH_INFO:
        if key.lower() == branch_name.lower():
            branch_info = BRANCH_INFO[key]
            break

    # Get address and phone from mapping, fallback to branch data
    if branch_info:
        address_lines = branch_info.get('address', [])
        phone = branch_info.get('phone', '')
    else:
        address = branch.get('address', '')
        city = branch.get('city', '')
        address_lines = [f"{address}, {city}"] if address or city else []
        phone = branch.get('phone', '')

    # === HEADER SECTION (Center-Aligned) ===
    story.append(Paragraph(company_name, title_center_style))
    for line in address_lines:
        story.append(Paragraph(line, header_center_style))
    if phone:
        story.append(Paragraph(f"Call us for appointment: {phone}", header_center_style))
    story.append(Spacer(1, 0.15*inch))

    # === CUSTOMER META SECTION (2 Columns) ===
    customer_name = customer.get('name', 'Customer')
    customer_mobile = format_mobile(customer.get('mobile', '')) if customer.get('mobile') else ''
    wallet_balance = customer.get('wallet_balance', 0)

    left_content = f"<b>Billed to</b> {customer_name}"
    if customer_mobile:
        left_content += f"<br/><b>Mobile:</b> {customer_mobile}"

    right_content = f"<b>Invoice Number:</b> {invoice_number}<br/>"
    right_content += f"<font size='9' color='#4b5563'>Wallet Balance: Rs.{wallet_balance:.2f}</font>"

    meta_table = Table([
        [Paragraph(left_content, left_text_style), Paragraph(right_content, right_text_style)]
    ], colWidths=[page_width/2, page_width/2])
    meta_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 0.1*inch))

    # === BOOKING STRIP ===
    booking_strip = Table([
        [Paragraph("<b>Booking at</b>", left_text_style),
         Paragraph(f"{booking_date}, {booking_time}", right_text_style)]
    ], colWidths=[page_width/2, page_width/2])
    booking_strip.setStyle(TableStyle([
        ('LINEABOVE', (0, 0), (-1, 0), 1, colors.HexColor('#e5e7eb')),
        ('LINEBELOW', (0, 0), (-1, 0), 1, colors.HexColor('#e5e7eb')),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
    ]))
    story.append(booking_strip)
    story.append(Spacer(1, 0.1*inch))

    # === PAYMENT STRIP ===
    payment_status = payment.get('status', 'pending')
    payment_mode = payment.get('mode', '')
    if not payment_mode and payment.get('source'):
        payment_mode = payment.get('source', '').split(':')[0].strip()
    payment_amount = payment.get('amount', summary.get('total', 0))

    payment_source_text = f"{payment_mode.title()}: Rs.{int(round(payment_amount))}" if payment_mode else "Not paid"

    payment_data = [
        [Paragraph("<b>Payment Status</b>", left_text_style),
         Paragraph(payment_status, right_text_style)],
        [Paragraph("<b>Payment Source</b>", left_text_style),
         Paragraph(payment_source_text, right_text_style)]
    ]
    payment_table = Table(payment_data, colWidths=[page_width/2, page_width/2])
    payment_table.setStyle(TableStyle([
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(payment_table)
    story.append(Spacer(1, 0.15*inch))

    # === ITEMS TABLE (8 Columns with fixed widths) ===
    # Column widths matching HTML: Item(25%), Staff(14%), Type(9%), Qty(6%), Price(12%), Tax(10%), Discount(10%), Amt(14%)
    col_widths = [
        page_width * 0.25,  # Item
        page_width * 0.14,  # Staff Name
        page_width * 0.09,  # Type
        page_width * 0.06,  # Qty
        page_width * 0.12,  # Price
        page_width * 0.10,  # Tax
        page_width * 0.10,  # Discount
        page_width * 0.14,  # Amt
    ]

    # Cell style for text wrapping in table cells
    cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontSize=9,
        leading=11,
        textColor=colors.HexColor('#1f2937'),
        wordWrap='CJK'  # Enables aggressive word wrapping
    )

    table_data = [['Item', 'Staff Name', 'Type', 'Qty', 'Price', 'Tax', 'Discount', 'Amt']]

    for item in items:
        table_data.append([
            Paragraph(item.get('name', 'Item'), cell_style),
            Paragraph(item.get('staff_name', 'N/A'), cell_style),
            (item.get('type', 'service') or 'service').title(),
            str(item.get('quantity', 1)),
            f"Rs.{item.get('price', 0):,.2f}",
            f"Rs.{item.get('tax', 0):,.2f}",
            f"Rs.{item.get('discount', 0):,.2f}",
            f"Rs.{item.get('total', 0):,.2f}"
        ])

    if not items:
        table_data.append([Paragraph('No items found', cell_style), '', '', '', '', '', '', ''])

    items_table = Table(table_data, colWidths=col_widths)
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f3f4f6')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#1f2937')),
        ('ALIGN', (0, 0), (2, -1), 'LEFT'),
        ('ALIGN', (3, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 0.15*inch))

    # === SUMMARY SECTION (Right-Aligned) ===
    subtotal = summary.get('subtotal', 0.0)
    discount = summary.get('discount', 0.0)
    net = summary.get('net', 0.0)
    tax = summary.get('tax', 0.0)
    total = summary.get('total', 0.0)

    summary_width = 2.5 * inch
    summary_data = [
        ['Subtotal', f"Rs.{subtotal:,.2f}"],
        ['Discount', f"Rs.{discount:,.2f}"],
        ['Net', f"Rs.{net:,.2f}"],
        ['Tax', f"Rs.{tax:,.2f}"],
        ['Total', f"Rs.{int(round(total)):,}"]
    ]

    summary_table = Table(summary_data, colWidths=[summary_width * 0.5, summary_width * 0.5])
    summary_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, -2), 'Helvetica-Bold'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -2), 10),
        ('FONTSIZE', (0, -1), (-1, -1), 14),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#1f2937')),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LINEABOVE', (0, 0), (-1, 0), 1, colors.HexColor('#e5e7eb')),
        ('LINEABOVE', (0, -1), (-1, -1), 1, colors.HexColor('#e5e7eb')),
    ]))

    # Wrap summary in a table to right-align it
    summary_wrapper = Table([[summary_table]], colWidths=[page_width])
    summary_wrapper.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, 0), 'RIGHT'),
    ]))
    story.append(summary_wrapper)
    story.append(Spacer(1, 0.15*inch))

    # === CONTACT FOOTER SECTION ===
    contact_style = ParagraphStyle(
        'Contact',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#4b5563'),
        alignment=TA_CENTER,
        spaceAfter=4
    )

    contact_bold_style = ParagraphStyle(
        'ContactBold',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#1f2937'),
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
        spaceAfter=4
    )

    # Contact footer with background
    contact_content = [
        [Paragraph("For Enquiry Contact – Geethalakshmi: +91 9840192264", contact_bold_style)],
        [Paragraph("www.priyankanaturecure.com", contact_style)],
        [Paragraph("<b>Email –</b> priyankanaturecure@gmail.com", contact_style)]
    ]

    contact_table = Table(contact_content, colWidths=[page_width])
    contact_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f9fafb')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LINEABOVE', (0, 0), (-1, 0), 1, colors.HexColor('#e5e7eb')),
        ('LINEBELOW', (0, -1), (-1, -1), 1, colors.HexColor('#e5e7eb')),
    ]))
    story.append(contact_table)

    # Build PDF
    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()

    return pdf_bytes
