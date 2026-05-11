import io
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


def generate_daily_report_pdf(report):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('title', parent=styles['Heading1'], alignment=TA_CENTER, fontSize=14)
    heading_style = ParagraphStyle('heading', parent=styles['Heading2'], fontSize=11,
                                   textColor=colors.HexColor('#1a5276'))
    normal = styles['Normal']
    small = ParagraphStyle('small', parent=normal, fontSize=8)

    story = []

    story.append(Paragraph('DAILY SITE REPORT', title_style))
    story.append(Spacer(1, 0.3 * cm))

    header_data = [
        ['Project:', report.project.project_name, 'Contract No:', report.project.contract_no],
        ['Date:', str(report.report_date), 'Status:', report.status],
        ['Weather AM:', report.weather_morning, 'Weather PM:', report.weather_afternoon],
        ['Contractor:', report.project.contractor, 'Owner:', report.project.owner],
    ]
    header_table = Table(header_data, colWidths=[3.5 * cm, 7 * cm, 3.5 * cm, 4 * cm])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#d6eaf8')),
        ('BACKGROUND', (2, 0), (2, -1), colors.HexColor('#d6eaf8')),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('PADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 0.4 * cm))

    manpower_records = report.manpower_records.select_related('category').all()
    if manpower_records.exists():
        story.append(Paragraph('1. MANPOWER', heading_style))
        mp_data = [['Category', 'Company', 'Quantity', 'Remarks']]
        for rec in manpower_records:
            mp_data.append([
                rec.category.get_name_display(),
                rec.company,
                str(rec.quantity),
                rec.remarks,
            ])
        mp_data.append(['TOTAL', '', str(sum(r.quantity for r in manpower_records)), ''])
        mp_table = Table(mp_data, colWidths=[5 * cm, 6 * cm, 3 * cm, 4 * cm])
        mp_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a5276')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#d6eaf8')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#f2f3f4')]),
        ]))
        story.append(mp_table)
        story.append(Spacer(1, 0.3 * cm))

    equipment_records = report.equipment_records.select_related('equipment').all()
    if equipment_records.exists():
        story.append(Paragraph('2. EQUIPMENT', heading_style))
        eq_data = [['Equipment', 'Status', 'Working Hours', 'Remarks']]
        for rec in equipment_records:
            eq_data.append([
                rec.equipment.name,
                rec.status,
                str(rec.working_hours),
                rec.remarks,
            ])
        eq_table = Table(eq_data, colWidths=[6 * cm, 3.5 * cm, 3.5 * cm, 5 * cm])
        eq_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a5276')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f2f3f4')]),
        ]))
        story.append(eq_table)
        story.append(Spacer(1, 0.3 * cm))

    activities = report.activities.all()
    if activities.exists():
        story.append(Paragraph('3. WORK ACTIVITIES', heading_style))
        act_data = [['Work Area', 'Description', 'Quantity', 'Unit', '% Complete']]
        for act in activities:
            act_data.append([
                str(act.work_area) if act.work_area else '-',
                act.description,
                str(act.quantity) if act.quantity else '-',
                act.unit,
                f"{act.percent_complete}%" if act.percent_complete else '-',
            ])
        act_table = Table(act_data, colWidths=[3.5 * cm, 7 * cm, 2.5 * cm, 2 * cm, 3 * cm])
        act_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a5276')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f2f3f4')]),
        ]))
        story.append(act_table)
        story.append(Spacer(1, 0.3 * cm))

    problems = report.problems.all()
    if problems.exists():
        story.append(Paragraph('4. PROBLEMS / REMARKS', heading_style))
        prob_data = [['Category', 'Description', 'Impact', 'Action', 'Status']]
        for p in problems:
            prob_data.append([p.category, p.description[:80], p.impact[:60], p.corrective_action[:60], p.status])
        prob_table = Table(prob_data, colWidths=[3 * cm, 5 * cm, 3.5 * cm, 3.5 * cm, 2.5 * cm])
        prob_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a5276')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f2f3f4')]),
        ]))
        story.append(prob_table)
        story.append(Spacer(1, 0.3 * cm))

    if report.remarks:
        story.append(Paragraph('5. GENERAL REMARKS', heading_style))
        story.append(Paragraph(report.remarks, normal))
        story.append(Spacer(1, 0.3 * cm))

    story.append(HRFlowable(width='100%', thickness=1, color=colors.grey))
    story.append(Spacer(1, 0.3 * cm))
    sig_data = [
        ['Prepared By', 'Checked By', 'Approved By'],
        [
            report.prepared_by.get_full_name() if report.prepared_by else '_______________',
            report.checked_by.get_full_name() if report.checked_by else '_______________',
            report.approved_by.get_full_name() if report.approved_by else '_______________',
        ],
        [
            report.prepared_by.role if report.prepared_by else '',
            report.checked_by.role if report.checked_by else '',
            report.approved_by.role if report.approved_by else '',
        ],
    ]
    sig_table = Table(sig_data, colWidths=[6 * cm, 6 * cm, 6 * cm])
    sig_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('LINEABOVE', (0, 1), (-1, 1), 1, colors.black),
        ('TOPPADDING', (0, 0), (-1, 0), 20),
    ]))
    story.append(sig_table)

    doc.build(story)
    return buffer
