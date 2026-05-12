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
    HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
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
