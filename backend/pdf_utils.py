"""Server-side PDF generation for receipts and reports using reportlab."""
from io import BytesIO
from datetime import datetime
from typing import List, Dict, Any
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, PageBreak
)
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT


def _num_to_words_inr(n: float) -> str:
    """Convert number to Indian rupee words (basic)."""
    n = int(round(n))
    if n == 0:
        return 'Zero Rupees Only'
    ones = ['', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine',
            'Ten', 'Eleven', 'Twelve', 'Thirteen', 'Fourteen', 'Fifteen', 'Sixteen',
            'Seventeen', 'Eighteen', 'Nineteen']
    tens = ['', '', 'Twenty', 'Thirty', 'Forty', 'Fifty', 'Sixty', 'Seventy', 'Eighty', 'Ninety']

    def two_digit(x):
        if x < 20:
            return ones[x]
        return tens[x // 10] + (' ' + ones[x % 10] if x % 10 else '')

    def three_digit(x):
        s = ''
        if x >= 100:
            s += ones[x // 100] + ' Hundred'
            x %= 100
            if x:
                s += ' '
        if x:
            s += two_digit(x)
        return s

    parts = []
    crore = n // 10000000
    n %= 10000000
    lakh = n // 100000
    n %= 100000
    thousand = n // 1000
    n %= 1000
    if crore:
        parts.append(three_digit(crore) + ' Crore')
    if lakh:
        parts.append(three_digit(lakh) + ' Lakh')
    if thousand:
        parts.append(three_digit(thousand) + ' Thousand')
    if n:
        parts.append(three_digit(n))
    return ' '.join(parts) + ' Rupees Only'


def generate_receipt_pdf(payment: Dict[str, Any], school: Dict[str, Any], student: Dict[str, Any]) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=15 * mm, bottomMargin=15 * mm,
        title=f"Fee Receipt - {payment.get('receipt_number', '')}"
    )
    styles = getSampleStyleSheet()
    story = []

    # Header
    header_style = ParagraphStyle('h', parent=styles['Title'], fontSize=20,
                                  textColor=colors.HexColor('#0B2F4A'),
                                  alignment=TA_CENTER, spaceAfter=2)
    sub_style = ParagraphStyle('s', parent=styles['Normal'], fontSize=10,
                               textColor=colors.HexColor('#475569'),
                               alignment=TA_CENTER, spaceAfter=6)
    story.append(Paragraph(school.get('name', 'STANVARD SCHOOL').upper(), header_style))
    tag = f"{school.get('city', '')} · {school.get('address', '')}".strip(' ·')
    story.append(Paragraph(tag or 'Excellence in Education', sub_style))
    story.append(HRFlowable(width='100%', thickness=1.2,
                            color=colors.HexColor('#0B2F4A'), spaceBefore=4, spaceAfter=10))

    title_style = ParagraphStyle('t', parent=styles['Heading2'], fontSize=13,
                                 textColor=colors.HexColor('#1E40AF'),
                                 alignment=TA_CENTER, spaceAfter=8)
    story.append(Paragraph('FEE PAYMENT RECEIPT', title_style))

    # Meta table
    paid_at = payment.get('paid_at', '')
    if paid_at:
        try:
            paid_at_display = datetime.fromisoformat(paid_at.replace('Z', '+00:00')).strftime('%d %b %Y, %H:%M')
        except Exception:
            paid_at_display = paid_at
    else:
        paid_at_display = ''
    meta = [
        ['Receipt No:', payment.get('receipt_number', ''), 'Date:', paid_at_display],
        ['Payment Mode:', str(payment.get('payment_mode', '')).replace('_', ' ').title(),
         'Txn Ref:', payment.get('txn_ref') or payment.get('razorpay_payment_id') or '-'],
    ]
    meta_tbl = Table(meta, colWidths=[30 * mm, 55 * mm, 22 * mm, 60 * mm])
    meta_tbl.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, -1), 'Helvetica', 9),
        ('FONT', (0, 0), (0, -1), 'Helvetica-Bold', 9),
        ('FONT', (2, 0), (2, -1), 'Helvetica-Bold', 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(meta_tbl)
    story.append(Spacer(1, 8))

    # Student details
    student_rows = [
        ['Student Name:', student.get('full_name', ''),
         'Admission No:', student.get('admission_number', '')],
        ['Class:', f"{student.get('class_name', '') or ''} - {student.get('section', '') or ''}",
         'Roll No:', student.get('roll_number', '') or '-'],
        ['Father:', student.get('father_name', '') or '-',
         'Contact:', student.get('phone', '') or '-'],
    ]
    stu_tbl = Table(student_rows, colWidths=[30 * mm, 60 * mm, 25 * mm, 52 * mm])
    stu_tbl.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, -1), 'Helvetica', 9),
        ('FONT', (0, 0), (0, -1), 'Helvetica-Bold', 9),
        ('FONT', (2, 0), (2, -1), 'Helvetica-Bold', 9),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F1F5F9')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.HexColor('#E2E8F0')),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(stu_tbl)
    story.append(Spacer(1, 12))

    # Fee items
    fee_rows = [['#', 'Fee Head', 'Period', 'Amount (Rs.)']]
    for i, it in enumerate(payment.get('items', []), start=1):
        fee_rows.append([str(i), it.get('fee_head_name', ''), it.get('period', ''),
                         f"{it.get('amount', 0):,.2f}"])
    subtotal = payment.get('subtotal', 0.0)
    discount = payment.get('discount', 0.0)
    late_fee = payment.get('late_fee', 0.0)
    total = payment.get('total_paid', 0.0)
    fee_rows.append(['', '', 'Sub-Total', f"{subtotal:,.2f}"])
    if late_fee:
        fee_rows.append(['', '', 'Late Fee', f"{late_fee:,.2f}"])
    if discount:
        fee_rows.append(['', '', 'Discount', f"-{discount:,.2f}"])
    fee_rows.append(['', '', 'TOTAL PAID', f"{total:,.2f}"])

    fee_tbl = Table(fee_rows, colWidths=[12 * mm, 78 * mm, 40 * mm, 40 * mm])
    style_cmds = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0B2F4A')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold', 9),
        ('FONT', (0, 1), (-1, -1), 'Helvetica', 9),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('ALIGN', (3, 0), (3, -1), 'RIGHT'),
        ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#94A3B8')),
        ('LINEABOVE', (0, len(fee_rows) - (2 + (1 if late_fee else 0) + (1 if discount else 0))),
         (-1, len(fee_rows) - (2 + (1 if late_fee else 0) + (1 if discount else 0))),
         0.5, colors.HexColor('#94A3B8')),
        ('FONT', (2, -1), (-1, -1), 'Helvetica-Bold', 10),
        ('BACKGROUND', (2, -1), (-1, -1), colors.HexColor('#DBEAFE')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]
    fee_tbl.setStyle(TableStyle(style_cmds))
    story.append(fee_tbl)
    story.append(Spacer(1, 14))

    story.append(Paragraph(
        f"<b>Amount in Words:</b> {_num_to_words_inr(total)}",
        ParagraphStyle('aw', parent=styles['Normal'], fontSize=9,
                       textColor=colors.HexColor('#0F172A'))
    ))
    if payment.get('remarks'):
        story.append(Spacer(1, 6))
        story.append(Paragraph(f"<b>Remarks:</b> {payment['remarks']}",
                               ParagraphStyle('rm', parent=styles['Normal'], fontSize=9,
                                              textColor=colors.HexColor('#475569'))))
    story.append(Spacer(1, 18))
    story.append(HRFlowable(width='100%', thickness=0.5,
                            color=colors.HexColor('#CBD5E1'), spaceAfter=6))
    footer = Table([
        ['This is a computer-generated receipt and does not require a signature.',
         'Authorised Signatory']
    ], colWidths=[110 * mm, 60 * mm])
    footer.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, -1), 'Helvetica-Oblique', 8),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#64748B')),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
    ]))
    story.append(footer)

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


def generate_report_pdf(title: str, subtitle: str, columns: List[str],
                       rows: List[List[Any]], school_name: str = 'Stanvard School',
                       summary: Dict[str, Any] = None) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=landscape(A4),
        leftMargin=15 * mm, rightMargin=15 * mm,
        topMargin=15 * mm, bottomMargin=15 * mm,
        title=title
    )
    styles = getSampleStyleSheet()
    story = []
    story.append(Paragraph(school_name.upper(),
                           ParagraphStyle('h', parent=styles['Title'], fontSize=16,
                                          textColor=colors.HexColor('#0B2F4A'),
                                          alignment=TA_CENTER)))
    story.append(Paragraph(title,
                           ParagraphStyle('t', parent=styles['Heading2'], fontSize=12,
                                          textColor=colors.HexColor('#1E40AF'),
                                          alignment=TA_CENTER)))
    if subtitle:
        story.append(Paragraph(subtitle,
                               ParagraphStyle('sub', parent=styles['Normal'], fontSize=9,
                                              textColor=colors.HexColor('#64748B'),
                                              alignment=TA_CENTER)))
    story.append(Spacer(1, 10))

    data = [columns] + rows
    n_cols = len(columns)
    col_widths = [270 * mm / n_cols] * n_cols
    tbl = Table(data, colWidths=col_widths, repeatRows=1)
    tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0B2F4A')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold', 9),
        ('FONT', (0, 1), (-1, -1), 'Helvetica', 8),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#94A3B8')),
        ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1),
         [colors.white, colors.HexColor('#F8FAFC')]),
    ]))
    story.append(tbl)
    if summary:
        story.append(Spacer(1, 10))
        summ_lines = ' &nbsp;&nbsp;·&nbsp;&nbsp; '.join(
            [f"<b>{k}:</b> {v}" for k, v in summary.items()]
        )
        story.append(Paragraph(summ_lines,
                               ParagraphStyle('sm', parent=styles['Normal'], fontSize=10,
                                              textColor=colors.HexColor('#0F172A'))))
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
