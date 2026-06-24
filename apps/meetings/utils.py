import uuid
import io
import qrcode
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from django.core.files.base import ContentFile


def log_action(user, action, model_name, object_id, details=None, ip=None):
    from apps.meetings.models import ActionLog
    ActionLog.objects.create(
        user=user,
        action=action,
        model_name=model_name,
        object_id=object_id,
        details=details or {},
        ip_address=ip,
    )


def generate_qr_code(data: str) -> bytes:
    qr = qrcode.QRCode(version=1, box_size=8, border=2)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return buf.getvalue()


def generate_pdf(meeting):
    from apps.meetings.models import Document

    qr_code_str = str(uuid.uuid4())[:12].upper()
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                             rightMargin=2*cm, leftMargin=2*cm,
                             topMargin=2*cm, bottomMargin=2*cm)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('title', parent=styles['Heading1'],
                                  fontSize=18, spaceAfter=6, alignment=1,
                                  textColor=colors.HexColor('#1a5276'))
    header_style = ParagraphStyle('header', parent=styles['Normal'],
                                   fontSize=10, textColor=colors.grey)
    normal = styles['Normal']
    normal.fontSize = 11

    elements = []

    # Header
    elements.append(Paragraph("YOUTHGUARD", title_style))
    elements.append(Paragraph("Yoshlar bilan uchrashuv dalolatnomasi", header_style))
    elements.append(Spacer(1, 0.5*cm))

    # QR code
    qr_bytes = generate_qr_code(qr_code_str)
    qr_img = RLImage(io.BytesIO(qr_bytes), width=3*cm, height=3*cm)

    # Info table
    data = [
        ['QR kod:', qr_code_str, '', qr_img],
        ['Rahbar:', meeting.rahbar.get_full_name() or meeting.rahbar.username, '', ''],
        ['Yosh:', meeting.youth.full_name, '', ''],
        ['Sana:', meeting.date.strftime('%d.%m.%Y %H:%M'), '', ''],
        ['Holat:', meeting.get_status_display(), '', ''],
        ['Manzil:', meeting.location_address or '—', '', ''],
        ['GPS:', f"{meeting.latitude:.6f}, {meeting.longitude:.6f}" if meeting.latitude else '—', '', ''],
    ]

    table = Table(data, colWidths=[4*cm, 9*cm, 0.5*cm, 3.5*cm])
    table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.HexColor('#f8f9fa'), colors.white]),
        ('GRID', (0, 0), (1, -1), 0.5, colors.HexColor('#dee2e6')),
        ('SPAN', (3, 0), (3, 3)),
        ('VALIGN', (3, 0), (3, 3), 'MIDDLE'),
        ('ALIGN', (3, 0), (3, 3), 'CENTER'),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 0.5*cm))

    if meeting.notes:
        elements.append(Paragraph(f"<b>Izoh:</b> {meeting.notes}", normal))
        elements.append(Spacer(1, 0.3*cm))

    if meeting.impossible_reason:
        elements.append(Paragraph(f"<b>Imkonsizlik sababi:</b> {meeting.impossible_reason}", normal))

    # Footer
    elements.append(Spacer(1, 1*cm))
    footer = Table(
        [['Rahbar imzosi: _____________', 'Yetakchi imzosi: _____________', 'Sana: ___________']],
        colWidths=[6*cm, 6*cm, 5*cm]
    )
    footer.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ]))
    elements.append(footer)

    doc.build(elements)
    pdf_bytes = buf.getvalue()

    document, _ = Document.objects.get_or_create(meeting=meeting, defaults={'qr_code': qr_code_str})
    document.file.save(f"meeting_{meeting.id}.pdf", ContentFile(pdf_bytes), save=True)
    document.qr_code = qr_code_str
    document.save()
    return document
