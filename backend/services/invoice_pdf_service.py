"""
Invoice PDF Generation Service
Generates professional PDF invoices matching the reference design
"""
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER
from reportlab.pdfgen import canvas
from reportlab.platypus.flowables import Flowable
from datetime import datetime


def generate_invoice_pdf(invoice_data):
    """
    Generate PDF invoice from invoice data
    
    Args:
        invoice_data: Dictionary containing invoice information
        
    Returns:
        bytes: PDF file as bytes
    """
    buffer = BytesIO()
    
    # Custom flowable for footer with brand color
    class GradientFooter(Flowable):
        def __init__(self, width, height, text):
            Flowable.__init__(self)
            self.width = width
            self.height = height
            self.text = text
        
        def draw(self):
            canvas = self.canv
            # Draw footer with brand color
            canvas.setFillColor(colors.HexColor('#0F766E'))
            canvas.rect(0, 0, self.width, self.height, fill=1, stroke=0)
            # Draw text
            canvas.setFillColor(colors.white)
            canvas.setFont('Helvetica-Bold', 12)
            text_width = canvas.stringWidth(self.text, 'Helvetica-Bold', 12)
            canvas.drawString((self.width - text_width) / 2, self.height / 2 - 4, self.text)
    
    doc = SimpleDocTemplate(buffer, pagesize=A4, 
                           leftMargin=0.75*inch, rightMargin=0.75*inch,
                           topMargin=0.5*inch, bottomMargin=0.5*inch)
    story = []
    
    # Get styles
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1f2937'),
        spaceAfter=12,
        alignment=TA_LEFT
    )
    
    header_style = ParagraphStyle(
        'CustomHeader',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#4b5563'),
        spaceAfter=4,
        alignment=TA_LEFT
    )
    
    invoice_num_style = ParagraphStyle(
        'InvoiceNumber',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor('#1f2937'),
        spaceAfter=8,
        alignment=TA_RIGHT,
        fontName='Helvetica-Bold'
    )
    
    section_title_style = ParagraphStyle(
        'SectionTitle',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#1f2937'),
        spaceAfter=6,
        fontName='Helvetica-Bold'
    )
    
    normal_style = ParagraphStyle(
        'NormalText',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#1f2937'),
        spaceAfter=4
    )
    
    # Company Header
    branch = invoice_data.get('branch', {})
    company_name = branch.get('name', 'SaloonBoost Demo Account')
    address = branch.get('address', '')
    city = branch.get('city', '')
    full_address = f"{address}, {city}" if address and city else (address or city or '')
    phone = branch.get('phone', '')
    gstin = branch.get('gstin', '')
    
    story.append(Paragraph(company_name, title_style))
    if full_address:
        story.append(Paragraph(full_address, header_style))
    if gstin:
        story.append(Paragraph(f"GST: GSTIN {gstin}", header_style))
    if phone:
        story.append(Paragraph(f"Call us for appointment: {phone}", header_style))
    
    story.append(Spacer(1, 0.3*inch))
    
    # Invoice Number and Balances (Right aligned)
    invoice_number = invoice_data.get('invoice_number', invoice_data.get('bill_number', 'N/A'))
    customer = invoice_data.get('customer', {})
    invoice_info_data = [
        [Paragraph(f"Invoice Number: {invoice_number}", invoice_num_style)]
    ]
    invoice_info_table = Table(invoice_info_data, colWidths=[3*inch])
    invoice_info_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(invoice_info_table)
    story.append(Spacer(1, 0.2*inch))
    
    # Customer Information
    customer_name = customer.get('name', 'Customer')
    customer_mobile = customer.get('mobile', '')
    # Ensure mobile is in +91 [number] format with space
    if customer_mobile:
        customer_mobile = customer_mobile.strip()
        if customer_mobile.startswith('+91'):
            if not customer_mobile.startswith('+91 '):
                customer_mobile = '+91 ' + customer_mobile[3:].strip()
        elif customer_mobile.startswith('91'):
            customer_mobile = '+91 ' + customer_mobile[2:].strip()
        elif not customer_mobile.startswith('+'):
            customer_mobile = '+91 ' + customer_mobile
    story.append(Paragraph(f"<b>Billed to {customer_name}</b>", section_title_style))
    if customer_mobile:
        story.append(Paragraph(f"Mobile: {customer_mobile}", normal_style))
    
    # Booking Date and Time (already formatted by backend as "Day, DD Mon, YYYY" and "HH:MM am/pm")
    booking_date = invoice_data.get('booking_date', 'N/A')
    booking_time = invoice_data.get('booking_time', 'N/A')
    if booking_date != 'N/A' and booking_time != 'N/A':
        story.append(Paragraph(f"Booking at {booking_date}, {booking_time}", normal_style))
    else:
        story.append(Paragraph(f"Booking at {booking_date}, {booking_time}", normal_style))
    story.append(Spacer(1, 0.15*inch))
    
    # Payment Status and Source (on same line if possible)
    payment = invoice_data.get('payment', {})
    payment_status = payment.get('status', 'pending')
    payment_source = payment.get('source', '')
    payment_text = f"<b>Payment Status:</b> {payment_status}"
    if payment_source:
        payment_text += f" | <b>Payment Source:</b> {payment_source}"
    story.append(Paragraph(payment_text, normal_style))
    
    story.append(Spacer(1, 0.2*inch))
    
    # Items Table
    items = invoice_data.get('items', [])
    if items:
        # Table headers
        table_data = [['Item', 'Staff Name', 'Type', 'Qty', 'Price', 'Tax', 'Discount', 'Amt']]
        
        # Table rows
        for item in items:
            table_data.append([
                item.get('name', 'Item'),
                item.get('staff_name', 'N/A'),
                item.get('type', 'service').title(),
                str(item.get('quantity', 1)),
                f"₹{item.get('price', 0):.2f}",
                f"₹{item.get('tax', 0):.2f}",
                f"₹{item.get('discount', 0):.2f}",
                f"₹{item.get('total', 0):.2f}"
            ])
        
        items_table = Table(table_data, colWidths=[1.5*inch, 1*inch, 0.6*inch, 0.4*inch, 0.7*inch, 0.6*inch, 0.7*inch, 0.7*inch])
        items_table.setStyle(TableStyle([
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f3f4f6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1f2937')),
            ('ALIGN', (0, 0), (2, -1), 'LEFT'),  # Item, Staff Name, Type left-aligned
            ('ALIGN', (3, 0), (-1, -1), 'RIGHT'),  # Qty, Price, Tax, Discount, Amt right-aligned
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            # Data rows
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ]))
        story.append(items_table)
    
    story.append(Spacer(1, 0.2*inch))
    
    # Bill Summary
    summary = invoice_data.get('summary', {})
    subtotal = summary.get('subtotal', 0.0)
    discount = summary.get('discount', 0.0)
    net = summary.get('net', 0.0)
    tax = summary.get('tax', 0.0)
    total = summary.get('total', 0.0)
    
    summary_data = [
        [Paragraph('<b>Subtotal:</b>', normal_style), Paragraph(f"₹{subtotal:.2f}", normal_style)],
        [Paragraph('<b>Discount:</b>', normal_style), Paragraph(f"₹{discount:.2f}", normal_style)],
        [Paragraph('<b>Net:</b>', normal_style), Paragraph(f"₹{net:.2f}", normal_style)],
        [Paragraph('<b>Tax:</b>', normal_style), Paragraph(f"₹{tax:.2f}", normal_style)],
        [Paragraph('<b>Total:</b>', section_title_style), Paragraph(f"₹{int(round(total))}", section_title_style)]
    ]
    
    summary_table = Table(summary_data, colWidths=[3*inch, 1.5*inch])
    summary_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTSIZE', (0, 0), (-1, -2), 10),
        ('FONTSIZE', (0, -1), (-1, -1), 11),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LINEABOVE', (0, 3), (-1, 3), 1, colors.HexColor('#e5e7eb')),  # Line above Net
    ]))
    story.append(summary_table)
    
    story.append(Spacer(1, 0.3*inch))
    
    # Footer with gradient (using custom flowable)
    page_width = A4[0] - (0.75*inch * 2)  # Width minus margins
    footer = GradientFooter(page_width, 0.4*inch, company_name)
    story.append(footer)
    
    # Build PDF
    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    return pdf_bytes

