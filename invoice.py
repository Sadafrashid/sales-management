from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def create_pdf(invoice_no, date, customer_name, items):
    file_name = f"invoice_{invoice_no}.pdf"
    doc = SimpleDocTemplate(file_name, pagesize=A4)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('TitleStyle', parent=styles['Title'], fontSize=24, spaceAfter=10)
    
    elements = []
    # Header Section
    elements.append(Paragraph("<b>FRESH MINI MARKET</b>", title_style))
    elements.append(Paragraph(f"Invoice No. {invoice_no}", styles["Normal"]))
    elements.append(Paragraph(f"{date}", styles["Normal"]))
    elements.append(Spacer(1, 15))
    elements.append(Paragraph(f"<b>Billed To:</b> {customer_name}", styles["Normal"]))
    elements.append(Spacer(1, 20))

    # Table Header
    data = [["Item Code", "Item", "Qty", "Unit Price", "Gross Price", "Total"]] 
    
    grand_total = 0
    for i in items:
        data.append([
            i[0], i[1], str(i[2]), 
            f"Rs.{i[3]:.2f}", f"Rs.{i[4]:.2f}", f"Rs.{i[5]:.2f}"
        ])
        grand_total += i[5]
    
    # Grand Total Row
    # We leave the first 4 columns empty and place "Grand Total" and the amount in the last two
    data.append(["", "", "", "", "Grand Total", f"Rs.{grand_total:.2f}"]) 

    # Table Column Widths
    t = Table(data, colWidths=[70, 180, 50, 80, 80, 80])
    
    # Updated Style for Alignment
    t.setStyle(TableStyle([
        # Header Style
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BACKGROUND', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        
        # Grid and padding for all items
        ('GRID', (0, 0), (-1, -2), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        
        # Alignment for Item Rows
        ('ALIGN', (2, 1), (-1, -2), 'RIGHT'), # Qty, Prices, and Totals right-aligned
        
        # SPECIFIC FIX FOR GRAND TOTAL ALIGNMENT
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('ALIGN', (-2, -1), (-1, -1), 'RIGHT'), # Align "Grand Total" and "Amount" to the right
        ('LINEABOVE', (-2, -1), (-1, -1), 1, colors.black), # Add a line above total for professional look
    ]))
    
    elements.append(t)
    elements.append(Spacer(1, 40))
    
    # Footer
    footer_text = "Thank you!<br/><br/>_________________<br/>Authorized sign<br/><br/>Customer care no. 3945"
    elements.append(Paragraph(footer_text, styles["Normal"]))

    doc.build(elements)
    return file_name
