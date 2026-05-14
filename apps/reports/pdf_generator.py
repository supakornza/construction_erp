"""
PDF generator for Daily Site Reports.
Fonts:
  - TH Sarabun New  → all Thai text and mixed Thai/English body text
  - Times New Roman → section headings and label cells (English only)
"""
import io
import os

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable, Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

# ── Font registration ─────────────────────────────────────────────────────────

_FONTS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    'static', 'fonts',
)
_WINDOWS_FONTS = r'C:\Windows\Fonts'

_registered = False


def _register_fonts():
    global _registered
    if _registered:
        return

    # TH Sarabun New (bundled in static/fonts/ — supports Thai + Latin)
    th_regular = os.path.join(_FONTS_DIR, 'THSarabunNew.ttf')
    th_bold    = os.path.join(_FONTS_DIR, 'THSarabunNew-Bold.ttf')

    if os.path.exists(th_regular):
        pdfmetrics.registerFont(TTFont('THSarabunNew',      th_regular))
        pdfmetrics.registerFont(TTFont('THSarabunNew-Bold', th_bold if os.path.exists(th_bold) else th_regular))
    else:
        # Fallback to Angsana New which is pre-installed on Thai Windows
        angsana = os.path.join(_WINDOWS_FONTS, 'angsana.ttc')
        if os.path.exists(angsana):
            pdfmetrics.registerFont(TTFont('THSarabunNew',      angsana, subfontIndex=0))
            pdfmetrics.registerFont(TTFont('THSarabunNew-Bold', angsana, subfontIndex=1))
        else:
            import warnings
            warnings.warn("Thai font not found; Thai text may not render correctly.")

    # Times New Roman (system font — English section headings)
    times      = os.path.join(_WINDOWS_FONTS, 'times.ttf')
    times_bold = os.path.join(_WINDOWS_FONTS, 'timesbd.ttf')
    if os.path.exists(times):
        pdfmetrics.registerFont(TTFont('TimesNewRoman',      times))
        pdfmetrics.registerFont(TTFont('TimesNewRoman-Bold', times_bold if os.path.exists(times_bold) else times))
    else:
        import warnings
        warnings.warn("Times New Roman not found; falling back to Helvetica for headings.")

    _registered = True


# ── Style helpers ─────────────────────────────────────────────────────────────

def _styles():
    """Return a dict of ParagraphStyle objects after fonts are registered."""
    _register_fonts()

    has_times = 'TimesNewRoman-Bold' in pdfmetrics.getRegisteredFontNames()
    has_thai  = 'THSarabunNew' in pdfmetrics.getRegisteredFontNames()

    EN_BOLD   = 'TimesNewRoman-Bold'  if has_times else 'Helvetica-Bold'
    EN_NORMAL = 'TimesNewRoman'       if has_times else 'Helvetica'
    TH        = 'THSarabunNew'        if has_thai  else 'Helvetica'
    TH_BOLD   = 'THSarabunNew-Bold'   if has_thai  else 'Helvetica-Bold'

    NAVY = colors.HexColor('#1a3a5c')

    return {
        'title':   ParagraphStyle('title',   fontName=EN_BOLD,   fontSize=14, alignment=TA_CENTER,
                                  spaceAfter=4, textColor=NAVY),
        'heading': ParagraphStyle('heading', fontName=EN_BOLD,   fontSize=11, textColor=NAVY,
                                  spaceBefore=6, spaceAfter=3),
        'label':   ParagraphStyle('label',   fontName=EN_BOLD,   fontSize=9),
        'en':      ParagraphStyle('en',      fontName=EN_NORMAL, fontSize=9),
        'th':      ParagraphStyle('th',      fontName=TH,        fontSize=10, leading=14),
        'th_bold': ParagraphStyle('th_bold', fontName=TH_BOLD,   fontSize=10, leading=14),
        'th_sm':   ParagraphStyle('th_sm',   fontName=TH,        fontSize=9,  leading=13),
        'th_hdr':  ParagraphStyle('th_hdr',  fontName=TH_BOLD,   fontSize=9,  leading=13,
                                  textColor=colors.white),
        # table header (white text on navy)
        'tbl_hdr': ParagraphStyle('tbl_hdr', fontName=EN_BOLD,   fontSize=9,
                                  textColor=colors.white, alignment=TA_CENTER),
    }, EN_BOLD, EN_NORMAL, TH, TH_BOLD


def _p(text, style):
    """Wrap text in a Paragraph, escaping & and <."""
    safe = str(text or '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    return Paragraph(safe, style)


def _tbl_style(extra=None):
    base = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a3a5c')),
        ('TEXTCOLOR',  (0, 0), (-1, 0), colors.white),
        ('FONTSIZE',   (0, 0), (-1, -1), 9),
        ('GRID',       (0, 0), (-1, -1), 0.4, colors.HexColor('#b0bec5')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1),
         [colors.white, colors.HexColor('#f5f7fa')]),
        ('VALIGN',     (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]
    if extra:
        base.extend(extra)
    return TableStyle(base)


# ── Main generator ────────────────────────────────────────────────────────────

def generate_daily_report_pdf(report):
    _register_fonts()
    S, EN_BOLD, EN_NORMAL, TH, TH_BOLD = _styles()

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    story = []

    # ── Title ─────────────────────────────────────────────────────────────────
    story.append(_p('DAILY SITE REPORT', S['title']))
    story.append(Spacer(1, 0.3 * cm))

    # ── Header table ──────────────────────────────────────────────────────────
    L = S['label']
    T = S['th']
    header_data = [
        [_p('Project:', L),      _p(report.project.project_name, T),
         _p('Contract No:', L),  _p(report.project.contract_no, T)],
        [_p('Date:', L),         _p(str(report.report_date), S['en']),
         _p('Status:', L),       _p(report.status, S['en'])],
        [_p('Weather AM:', L),   _p(report.weather_morning, S['en']),
         _p('Weather PM:', L),   _p(report.weather_afternoon, S['en'])],
        [_p('Contractor:', L),   _p(report.project.contractor, T),
         _p('Owner:', L),        _p(report.project.owner, T)],
    ]
    header_table = Table(header_data, colWidths=[3 * cm, 7.5 * cm, 3 * cm, 4.5 * cm])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#dce8f5')),
        ('BACKGROUND', (2, 0), (2, -1), colors.HexColor('#dce8f5')),
        ('GRID',       (0, 0), (-1, -1), 0.4, colors.HexColor('#b0bec5')),
        ('VALIGN',     (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 0.4 * cm))

    # ── 1. Manpower ───────────────────────────────────────────────────────────
    manpower_records = report.manpower_records.select_related('category').all()
    if manpower_records.exists():
        story.append(_p('1.  MANPOWER', S['heading']))
        mp_data = [[
            _p('Category',  S['tbl_hdr']),
            _p('Company',   S['tbl_hdr']),
            _p('Quantity',  S['tbl_hdr']),
            _p('Remarks',   S['tbl_hdr']),
        ]]
        total = 0
        for rec in manpower_records:
            total += rec.quantity
            mp_data.append([
                _p(rec.category.get_name_display(), T),
                _p(rec.company, T),
                _p(str(rec.quantity), S['en']),
                _p(rec.remarks, T),
            ])
        mp_data.append([
            _p('TOTAL', S['label']), _p('', S['en']),
            _p(str(total), S['label']), _p('', S['en']),
        ])
        mp_table = Table(mp_data, colWidths=[4.5 * cm, 6 * cm, 2.5 * cm, 5 * cm])
        mp_table.setStyle(_tbl_style([
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#dce8f5')),
        ]))
        story.append(mp_table)
        story.append(Spacer(1, 0.3 * cm))

    # ── 2. Equipment ──────────────────────────────────────────────────────────
    equipment_records = report.equipment_records.select_related('equipment').all()
    if equipment_records.exists():
        story.append(_p('2.  EQUIPMENT', S['heading']))
        eq_data = [[
            _p('Equipment',     S['tbl_hdr']),
            _p('Status',        S['tbl_hdr']),
            _p('Working Hrs',   S['tbl_hdr']),
            _p('Remarks',       S['tbl_hdr']),
        ]]
        for rec in equipment_records:
            eq_data.append([
                _p(rec.equipment.name, T),
                _p(rec.status, S['en']),
                _p(str(rec.working_hours), S['en']),
                _p(rec.remarks, T),
            ])
        eq_table = Table(eq_data, colWidths=[6 * cm, 3 * cm, 3 * cm, 6 * cm])
        eq_table.setStyle(_tbl_style())
        story.append(eq_table)
        story.append(Spacer(1, 0.3 * cm))

    # ── 3. Work Activities ────────────────────────────────────────────────────
    activities = report.activities.all()
    if activities.exists():
        story.append(_p('3.  WORK ACTIVITIES', S['heading']))
        act_data = [[
            _p('Work Area',    S['tbl_hdr']),
            _p('Description',  S['tbl_hdr']),
            _p('Quantity',     S['tbl_hdr']),
            _p('Unit',         S['tbl_hdr']),
            _p('% Complete',   S['tbl_hdr']),
        ]]
        for act in activities:
            act_data.append([
                _p(str(act.work_area) if act.work_area else '-', T),
                _p(act.description, T),
                _p(str(act.quantity) if act.quantity else '-', S['en']),
                _p(act.unit, T),
                _p(f"{act.percent_complete}%" if act.percent_complete else '-', S['en']),
            ])
        act_table = Table(act_data, colWidths=[3 * cm, 8 * cm, 2.5 * cm, 1.8 * cm, 2.7 * cm])
        act_table.setStyle(_tbl_style())
        story.append(act_table)
        story.append(Spacer(1, 0.3 * cm))

    # ── 4. Lookahead ──────────────────────────────────────────────────────────
    lookaheads = report.lookaheads.all()
    if lookaheads.exists():
        story.append(_p('4.  DAILY LOOKAHEAD', S['heading']))
        la_data = [[
            _p('Planned Activity',    S['tbl_hdr']),
            _p('Planned Date',        S['tbl_hdr']),
            _p('Responsible Person',  S['tbl_hdr']),
        ]]
        for la in lookaheads:
            la_data.append([
                _p(la.planned_activity, T),
                _p(str(la.planned_date), S['en']),
                _p(la.responsible_person, T),
            ])
        la_table = Table(la_data, colWidths=[9 * cm, 3 * cm, 6 * cm])
        la_table.setStyle(_tbl_style())
        story.append(la_table)
        story.append(Spacer(1, 0.3 * cm))

    # ── 5. Problems / Remarks ─────────────────────────────────────────────────
    problems = report.problems.all()
    if problems.exists():
        story.append(_p('5.  PROBLEMS / REMARKS', S['heading']))
        prob_data = [[
            _p('Category',    S['tbl_hdr']),
            _p('Description', S['tbl_hdr']),
            _p('Impact',      S['tbl_hdr']),
            _p('Action',      S['tbl_hdr']),
            _p('Status',      S['tbl_hdr']),
        ]]
        for p in problems:
            prob_data.append([
                _p(p.category, S['en']),
                _p(p.description, T),
                _p(p.impact, T),
                _p(p.corrective_action, T),
                _p(p.status, S['en']),
            ])
        prob_table = Table(prob_data, colWidths=[2.5 * cm, 5 * cm, 3.5 * cm, 3.5 * cm, 2.5 * cm])
        prob_table.setStyle(_tbl_style())
        story.append(prob_table)
        story.append(Spacer(1, 0.3 * cm))

    # ── 6. General Remarks ────────────────────────────────────────────────────
    if report.remarks:
        story.append(_p('6.  GENERAL REMARKS', S['heading']))
        story.append(_p(report.remarks, S['th']))
        story.append(Spacer(1, 0.3 * cm))

    # ── Signature block ───────────────────────────────────────────────────────
    story.append(HRFlowable(width='100%', thickness=0.5, color=colors.HexColor('#90a4ae')))
    story.append(Spacer(1, 0.3 * cm))

    def _sig_name(user):
        if not user:
            return '________________________'
        return user.get_full_name() or user.username

    def _sig_role(user):
        return getattr(user, 'role', '') or ''

    sig_data = [
        [_p('Prepared By', S['label']),  _p('Checked By', S['label']),  _p('Approved By', S['label'])],
        [_p(_sig_name(report.prepared_by), T),
         _p(_sig_name(report.checked_by),  T),
         _p(_sig_name(report.approved_by), T)],
        [_p(_sig_role(report.prepared_by), S['th_sm']),
         _p(_sig_role(report.checked_by),  S['th_sm']),
         _p(_sig_role(report.approved_by), S['th_sm'])],
    ]
    sig_table = Table(sig_data, colWidths=[6 * cm, 6 * cm, 6 * cm])
    sig_table.setStyle(TableStyle([
        ('ALIGN',      (0, 0), (-1, -1), 'CENTER'),
        ('FONTSIZE',   (0, 0), (-1, -1), 9),
        ('LINEABOVE',  (0, 1), (-1, 1), 0.8, colors.black),
        ('TOPPADDING', (0, 0), (-1, 0), 22),
        ('TOPPADDING', (0, 1), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(sig_table)

    doc.build(story)
    return buffer


# ── Photo Report PDF (A4, 6 photos per page, 2 columns × 3 rows) ─────────────

# Layout constants (in points; A4 = 595 × 842 pt)
_PAGE_W, _PAGE_H = A4
_MARGIN_L = _MARGIN_R = 1.5 * cm
_MARGIN_T = 2.0 * cm
_MARGIN_B = 1.5 * cm
_CONTENT_W = _PAGE_W - _MARGIN_L - _MARGIN_R   # ≈ 510 pt

# 6 photos per page: 2 columns, 3 rows
_COLS = 2
_ROWS = 3
_PHOTOS_PER_PAGE = _COLS * _ROWS

_COL_GAP = 0.5 * cm
_ROW_GAP = 0.4 * cm

# Header band per page (project info)
_HEADER_H = 1.8 * cm

# Photo cell dimensions
_CELL_W = (_CONTENT_W - (_COLS - 1) * _COL_GAP) / _COLS   # ≈ 247 pt
_CAPTION_ROWS_H = 1.0 * cm                                   # space for caption + location text
_CONTENT_PHOTO_H = (_PAGE_H - _MARGIN_T - _MARGIN_B
                    - _HEADER_H - 0.3 * cm
                    - (_ROWS - 1) * _ROW_GAP)
_CELL_H = _CONTENT_PHOTO_H / _ROWS                           # ≈ 222 pt
_IMG_H  = _CELL_H - _CAPTION_ROWS_H - 0.1 * cm              # ≈ 212 pt


def _photo_cell(photo_obj, seq_no, S):
    """Return a Table (single cell) containing the photo + caption + location."""
    img_path = photo_obj.photo.path

    try:
        img = Image(img_path, width=_CELL_W, height=_IMG_H)
        img.hAlign = 'CENTER'
    except Exception:
        img = Paragraph(f"[Image not found: {img_path}]", S['th_sm'])

    lines = []
    # Number + caption
    caption_text = f"<b>{seq_no}.</b>  {photo_obj.caption or ''}"
    safe_caption = caption_text.replace('&', '&amp;').replace('<b>', '<b>').replace('</b>', '</b>')
    # Escape only the caption part, not the <b> tags already added
    safe_cap_raw = (photo_obj.caption or '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    lines.append(Paragraph(f"<b>{seq_no}.</b>  {safe_cap_raw}", S['th_sm']))

    if photo_obj.location:
        safe_loc = photo_obj.location.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        lines.append(Paragraph(f"<font size='8' color='#607d8b'>📍 {safe_loc}</font>", S['th_sm']))

    cell_content = [img] + lines

    t = Table([[cell_content]], colWidths=[_CELL_W])
    t.setStyle(TableStyle([
        ('BOX',        (0, 0), (-1, -1), 0.6, colors.HexColor('#b0bec5')),
        ('BACKGROUND', (0, 0), (-1, -1), colors.white),
        ('VALIGN',     (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING',  (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    return t


def _page_header_table(report, page_no, total_pages, S):
    """Thin header band shown at the top of every page."""
    NAVY = colors.HexColor('#1a3a5c')
    L = S['label']
    T = S['th_sm']

    left = Paragraph(
        f"<b>DAILY PHOTO REPORT</b>  –  {report.project.contract_no}  |  {report.report_date}",
        ParagraphStyle('hdr_left', parent=L, textColor=NAVY, fontSize=9),
    )
    right = Paragraph(
        f"Page {page_no} / {total_pages}",
        ParagraphStyle('hdr_right', parent=L, fontSize=9, alignment=TA_RIGHT),
    )
    t = Table([[left, right]], colWidths=[_CONTENT_W * 0.75, _CONTENT_W * 0.25])
    t.setStyle(TableStyle([
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        ('LINEBELOW',     (0, 0), (-1, -1), 0.8, NAVY),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING',    (0, 0), (-1, -1), 2),
    ]))
    return t


def generate_photo_report_pdf(report):
    """Generate an A4 photo report with 6 photos per page (2 cols × 3 rows)."""
    _register_fonts()
    S, EN_BOLD, EN_NORMAL, TH, TH_BOLD = _styles()

    photos = list(report.photos.order_by('sort_order', 'id'))
    if not photos:
        # Return a simple "no photos" PDF
        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4,
                                leftMargin=_MARGIN_L, rightMargin=_MARGIN_R,
                                topMargin=_MARGIN_T, bottomMargin=_MARGIN_B)
        doc.build([Paragraph("No photos attached to this report.", S['th'])])
        return buf

    total_pages = (len(photos) + _PHOTOS_PER_PAGE - 1) // _PHOTOS_PER_PAGE

    story = []

    for page_idx in range(total_pages):
        page_photos = photos[page_idx * _PHOTOS_PER_PAGE:(page_idx + 1) * _PHOTOS_PER_PAGE]

        # Page header
        story.append(_page_header_table(report, page_idx + 1, total_pages, S))
        story.append(Spacer(1, 0.3 * cm))

        # Build rows: each row is a list of 2 cell Tables
        for row_i in range(_ROWS):
            left_i  = row_i * _COLS
            right_i = left_i + 1
            seq_left  = page_idx * _PHOTOS_PER_PAGE + left_i + 1
            seq_right = seq_left + 1

            left_cell  = (
                _photo_cell(page_photos[left_i], seq_left, S)
                if left_i < len(page_photos)
                else ''
            )
            right_cell = (
                _photo_cell(page_photos[right_i], seq_right, S)
                if right_i < len(page_photos)
                else ''
            )

            row_table = Table(
                [[left_cell, right_cell]],
                colWidths=[_CELL_W, _CELL_W],
                rowHeights=[_CELL_H],
            )
            gap = int(_COL_GAP / 2)
            row_table.setStyle(TableStyle([
                ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING',   (0, 0), (0, -1), 0),
                ('RIGHTPADDING',  (0, 0), (0, -1), gap),
                ('LEFTPADDING',   (1, 0), (1, -1), gap),
                ('RIGHTPADDING',  (1, 0), (1, -1), 0),
                ('TOPPADDING',    (0, 0), (-1, -1), 0),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ]))
            story.append(row_table)

            if row_i < _ROWS - 1:
                story.append(Spacer(1, _ROW_GAP))

        if page_idx < total_pages - 1:
            story.append(PageBreak())

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=_MARGIN_L,
        rightMargin=_MARGIN_R,
        topMargin=_MARGIN_T,
        bottomMargin=_MARGIN_B,
    )
    doc.build(story)
    return buffer
