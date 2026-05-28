"""
PMC-compliant Daily Site Report PDF generator.

Sections:
  S1  Document Header Block
  S2  Manpower
  S3  Equipment
  S4  Daily Work Activities
  S5  Problems / Issues / Safety
  S6  Next Day Plan (Lookahead)
  S7  Document Control Footer

Entry point: generate_pmc_pdf(report) -> io.BytesIO
"""
import io
import os
from decimal import Decimal, InvalidOperation

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.platypus import (
    HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

# ── Colours ───────────────────────────────────────────────────────────────────

NAVY         = colors.HexColor('#1B2A4A')
NAVY_LIGHT   = colors.HexColor('#dce8f5')
WARN_YELLOW  = colors.HexColor('#FFF3CD')
ERROR_RED    = colors.HexColor('#F8D7DA')
OK_GREEN     = colors.HexColor('#D4EDDA')
GREY_LIGHT   = colors.HexColor('#f5f7fa')
BORDER_GREY  = colors.HexColor('#b0bec5')
GREY_TEXT    = colors.HexColor('#6c757d')
WHITE        = colors.white

# ── Font setup ────────────────────────────────────────────────────────────────

_FONTS_DIR    = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    'static', 'fonts',
)
_WIN_FONTS    = r'C:\Windows\Fonts'
_fonts_ready  = False


def _ensure_fonts():
    global _fonts_ready
    if _fonts_ready:
        return
    from apps.reports.pdf_generator import _register_fonts
    _register_fonts()
    _fonts_ready = True


def _font(thai=False, bold=False):
    _ensure_fonts()
    registered = pdfmetrics.getRegisteredFontNames()
    if thai:
        name = 'THSarabunNew-Bold' if bold else 'THSarabunNew'
        return name if name in registered else ('Helvetica-Bold' if bold else 'Helvetica')
    else:
        name = 'TimesNewRoman-Bold' if bold else 'TimesNewRoman'
        return name if name in registered else ('Helvetica-Bold' if bold else 'Helvetica')


# ── Paragraph helpers ─────────────────────────────────────────────────────────

def _ps(font_name, size, color=colors.black, align=TA_LEFT, leading=None, bold=False):
    return ParagraphStyle(
        font_name,
        fontName=font_name,
        fontSize=size,
        textColor=color,
        alignment=align,
        leading=leading or max(size + 3, 12),
    )


def _p(text, style):
    safe = str(text or '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    return Paragraph(safe, style)


def _styles():
    _ensure_fonts()
    EN   = _font(thai=False, bold=False)
    ENB  = _font(thai=False, bold=True)
    TH   = _font(thai=True,  bold=False)
    THB  = _font(thai=True,  bold=True)

    return {
        'title'   : _ps(ENB, 13, NAVY,       TA_CENTER),
        'section' : _ps(ENB, 10, WHITE,      TA_LEFT),
        'sub_hdr' : _ps(ENB, 9,  NAVY,       TA_LEFT),
        'tbl_hdr' : _ps(ENB, 8,  WHITE,      TA_CENTER),
        'label'   : _ps(ENB, 9,  colors.black),
        'en'      : _ps(EN,  9,  colors.black),
        'en_sm'   : _ps(EN,  8,  colors.black),
        'th'      : _ps(TH,  10, colors.black, leading=14),
        'th_sm'   : _ps(TH,  9,  colors.black, leading=13),
        'grey'    : _ps(EN,  8,  GREY_TEXT,  TA_LEFT),
        'grey_c'  : _ps(EN,  8,  GREY_TEXT,  TA_CENTER),
        'hdr_val' : _ps(TH,  10, NAVY),
        'sig_lbl' : _ps(ENB, 9,  colors.black, TA_CENTER),
        'sig_val' : _ps(TH,  10, colors.black, TA_CENTER),
        'sig_role': _ps(TH,  9,  GREY_TEXT,  TA_CENTER),
        'footer'  : _ps(EN,  7,  GREY_TEXT,  TA_CENTER),
    }


# ── Table style helpers ───────────────────────────────────────────────────────

def _base_tbl(extra=None):
    base = [
        ('BACKGROUND',    (0, 0), (-1, 0), NAVY),
        ('TEXTCOLOR',     (0, 0), (-1, 0), WHITE),
        ('FONTSIZE',      (0, 0), (-1, -1), 8),
        ('GRID',          (0, 0), (-1, -1), 0.3, BORDER_GREY),
        ('ROWBACKGROUNDS',(0, 1), (-1, -1), [WHITE, GREY_LIGHT]),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING',    (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING',   (0, 0), (-1, -1), 4),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 4),
    ]
    if extra:
        base.extend(extra)
    return TableStyle(base)


def _info_tbl():
    return TableStyle([
        ('BACKGROUND',    (0, 0), (0, -1), NAVY_LIGHT),
        ('BACKGROUND',    (2, 0), (2, -1), NAVY_LIGHT),
        ('FONTSIZE',      (0, 0), (-1, -1), 9),
        ('GRID',          (0, 0), (-1, -1), 0.3, BORDER_GREY),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING',    (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING',   (0, 0), (-1, -1), 4),
    ])


def _section_bar(title, S):
    row   = [_p(f'  {title}', S['section']), '', '', '']
    table = Table([row], colWidths=[18 * cm, 0, 0, 0])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), NAVY),
        ('SPAN',       (0, 0), (-1, -1)),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING',   (0, 0), (-1, -1), 6),
    ]))
    return table


# ── Computed helpers ──────────────────────────────────────────────────────────

_COMPLETED_UNITS = {'ton', 'tonnes', 't', 'm3', 'm³', 'cum', 'm2', 'm²', 'm', 'kg', 'lm', 'pcs', 'no'}


def _activity_status(act):
    unit = (act.unit or '').lower().strip()
    qty  = act.quantity
    pct  = act.percent_complete
    if qty is not None and qty > Decimal('0') and unit in _COMPLETED_UNITS:
        return 'Completed', OK_GREEN
    if pct is not None and pct > Decimal('0'):
        return 'In Progress', WARN_YELLOW
    return 'Not Started', WHITE


def _cumulative_qty(report, act):
    from django.db.models import Sum
    from apps.daily_reports.models import DailyWorkActivity
    result = DailyWorkActivity.objects.filter(
        report__project=report.project,
        report__report_date__lte=report.report_date,
        work_area=act.work_area,
        description=act.description,
    ).aggregate(total=Sum('quantity'))['total']
    return result or Decimal('0')


def _sig_name(user):
    if not user:
        return '________________________'
    return user.get_full_name() or user.username


def _sig_role(user):
    return getattr(user, 'role', '') or ''


def _fmt_qty(val):
    if val is None:
        return '—'
    try:
        d = Decimal(str(val))
        return f'{d:,f}'.rstrip('0').rstrip('.')
    except InvalidOperation:
        return str(val)


# ── Page header / footer callbacks ────────────────────────────────────────────

def _make_header_footer(report, report_no):
    EN  = _font(thai=False, bold=False)
    ENB = _font(thai=False, bold=True)

    def _draw(canvas, doc):
        canvas.saveState()
        w, h = A4
        margin = 1.5 * cm

        # Top border line
        canvas.setStrokeColor(NAVY)
        canvas.setLineWidth(1.2)
        canvas.line(margin, h - 1.2 * cm, w - margin, h - 1.2 * cm)

        # Header text
        canvas.setFillColor(NAVY)
        canvas.setFont(ENB, 8)
        canvas.drawString(margin, h - 1.0 * cm,
                          f"{report.project.project_name}  |  {report.project.contract_no}  |  {report.report_date}")
        canvas.setFont(EN, 8)
        canvas.drawRightString(w - margin, h - 1.0 * cm,
                               f"Page {doc.page} of <total>")

        # Footer
        canvas.setStrokeColor(BORDER_GREY)
        canvas.setLineWidth(0.5)
        canvas.line(margin, 1.4 * cm, w - margin, 1.4 * cm)
        canvas.setFillColor(GREY_TEXT)
        canvas.setFont(EN, 7)
        canvas.drawCentredString(w / 2, 1.0 * cm,
                                 f"CONFIDENTIAL  |  {report_no}  |  Rev 0")
        canvas.restoreState()

    return _draw


# ── Main generator ────────────────────────────────────────────────────────────

def generate_pmc_pdf(report):
    """Return io.BytesIO containing the PMC-compliant daily report PDF."""
    _ensure_fonts()
    S = _styles()

    proj       = report.project
    report_no  = f"{proj.contract_no}-DR-{report.report_date:%Y%m%d}"
    start_date = getattr(proj, 'start_date', None)
    day_count  = ((report.report_date - start_date).days + 1) if start_date else '—'
    status_lbl = 'FINAL' if report.status == 'Approved' else 'DRAFT'

    buffer  = io.BytesIO()
    draw_cb = _make_header_footer(report, report_no)
    doc     = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=1.8 * cm,
        bottomMargin=1.8 * cm,
    )

    story = []
    TW = 18 * cm  # usable table width

    # ── Title ─────────────────────────────────────────────────────────────────
    story.append(_p('DAILY SITE REPORT', S['title']))
    story.append(_p('PMC DAILY PROGRESS REPORT', S['grey_c']))
    story.append(Spacer(1, 0.3 * cm))

    # ── S1: Document Header Block ─────────────────────────────────────────────
    story.append(_section_bar('1.  DOCUMENT HEADER', S))
    story.append(Spacer(1, 0.15 * cm))

    LB = S['label']
    HV = S['hdr_val']
    EN = S['en']
    hdr_data = [
        [_p('Project:', LB),      _p(proj.project_name, HV),
         _p('Contract No:', LB),  _p(proj.contract_no, EN)],
        [_p('Report No:', LB),    _p(report_no, EN),
         _p('Report Date:', LB),  _p(str(report.report_date), EN)],
        [_p('Day Count:', LB),    _p(f'Day {day_count}' if start_date else '—', EN),
         _p('Status:', LB),       _p(status_lbl, S['label'])],
        [_p('Weather AM:', LB),   _p(report.weather_morning, EN),
         _p('Weather PM:', LB),   _p(report.weather_afternoon, EN)],
        [_p('Sea Condition:', LB),_p('N/A', S['grey']),
         _p('Distribution:', LB), _p('PMC / Owner / Contractor', EN)],
        [_p('Contractor:', LB),   _p(proj.contractor, HV),
         _p('Owner:', LB),        _p(proj.owner, HV)],
    ]
    hdr_table = Table(hdr_data, colWidths=[3 * cm, 7.5 * cm, 3 * cm, 4.5 * cm])
    hdr_table.setStyle(_info_tbl())
    story.append(hdr_table)
    story.append(Spacer(1, 0.4 * cm))

    # ── S2: Manpower ──────────────────────────────────────────────────────────
    story.append(_section_bar('2.  MANPOWER', S))
    story.append(Spacer(1, 0.15 * cm))

    mp_records = report.manpower_records.select_related('category').all()
    TH = S['th']
    TH_SM = S['th_sm']
    mp_data = [[
        _p('Category',  S['tbl_hdr']),
        _p('Company',   S['tbl_hdr']),
        _p('Planned',   S['tbl_hdr']),
        _p('Actual',    S['tbl_hdr']),
        _p('Remarks',   S['tbl_hdr']),
    ]]
    total_actual = 0
    for rec in mp_records:
        total_actual += rec.quantity
        mp_data.append([
            _p(rec.category.get_name_display(), TH_SM),
            _p(rec.company, TH_SM),
            _p('—', S['grey_c']),
            _p(str(rec.quantity), S['en_sm']),
            _p(rec.remarks, TH_SM),
        ])
    if not mp_records:
        mp_data.append([_p('No manpower records.', S['grey']), '', '', '', ''])
    mp_data.append([
        _p('TOTAL', S['label']), _p('', EN),
        _p('—', S['grey_c']),
        _p(str(total_actual), S['label']), _p('', EN),
    ])
    mp_tbl = Table(mp_data, colWidths=[4.5 * cm, 5.5 * cm, 2.5 * cm, 2.5 * cm, 3 * cm])
    mp_tbl.setStyle(_base_tbl([
        ('BACKGROUND', (0, -1), (-1, -1), NAVY_LIGHT),
        ('FONTSIZE',   (0, -1), (-1, -1), 9),
    ]))
    story.append(mp_tbl)
    story.append(Spacer(1, 0.4 * cm))

    # ── S3: Equipment ─────────────────────────────────────────────────────────
    story.append(_section_bar('3.  EQUIPMENT', S))
    story.append(Spacer(1, 0.15 * cm))

    eq_records = report.equipment_records.select_related('equipment').all()
    eq_data = [[
        _p('Equipment',     S['tbl_hdr']),
        _p('Status',        S['tbl_hdr']),
        _p('Working Hrs',   S['tbl_hdr']),
        _p('Idle Hrs',      S['tbl_hdr']),
        _p('Utilization %', S['tbl_hdr']),
        _p('Remarks',       S['tbl_hdr']),
    ]]
    eq_row_styles = []
    for i, rec in enumerate(eq_records, 1):
        wh   = rec.working_hours or Decimal('0')
        idle = max(Decimal('0'), Decimal('10') - wh)
        util = round(float(wh) / 10.0 * 100, 1)
        bg   = WARN_YELLOW if rec.status in ('Standby', 'Breakdown') else None
        if bg:
            eq_row_styles.append(('BACKGROUND', (0, i), (-1, i), bg))
        eq_data.append([
            _p(rec.equipment.name, TH_SM),
            _p(rec.status, S['en_sm']),
            _p(str(wh), S['en_sm']),
            _p(str(idle), S['en_sm']),
            _p(f'{util}%', S['en_sm']),
            _p(rec.remarks, TH_SM),
        ])
    if not eq_records:
        eq_data.append([_p('No equipment records.', S['grey']), '', '', '', '', ''])
    eq_tbl = Table(eq_data, colWidths=[5 * cm, 2.5 * cm, 2.2 * cm, 2.2 * cm, 2.3 * cm, 3.8 * cm])
    eq_tbl.setStyle(_base_tbl(eq_row_styles))
    story.append(eq_tbl)
    story.append(Spacer(1, 0.4 * cm))

    # ── S4: Daily Work Activities ─────────────────────────────────────────────
    story.append(_section_bar('4.  DAILY WORK ACTIVITIES', S))
    story.append(Spacer(1, 0.15 * cm))

    activities = report.activities.select_related('work_area').all()
    act_data = [[
        _p('No',           S['tbl_hdr']),
        _p('Activity',     S['tbl_hdr']),
        _p('Location',     S['tbl_hdr']),
        _p('Unit',         S['tbl_hdr']),
        _p('Today Qty',    S['tbl_hdr']),
        _p('Cumul. Qty',   S['tbl_hdr']),
        _p('% Complete',   S['tbl_hdr']),
        _p('Status',       S['tbl_hdr']),
        _p('Remarks',      S['tbl_hdr']),
    ]]
    act_row_styles = []
    if not activities:
        act_data.append([
            _p('—', S['grey_c']),
            _p('No activities recorded.', S['grey']),
            '', '', '', '', '', '', '',
        ])
        act_row_styles.append(('BACKGROUND', (0, 1), (-1, 1), ERROR_RED))
    else:
        for i, act in enumerate(activities, 1):
            cumul   = _cumulative_qty(report, act)
            status, bg = _activity_status(act)
            location_str = str(act.work_area) if act.work_area else '—'
            act_data.append([
                _p(str(i), S['en_sm']),
                _p(act.description, TH_SM),
                _p(location_str, TH_SM),
                _p(act.unit or '—', S['en_sm']),
                _p(_fmt_qty(act.quantity), S['en_sm']),
                _p(_fmt_qty(cumul), S['en_sm']),
                _p(f"{act.percent_complete}%" if act.percent_complete else '—', S['en_sm']),
                _p(status, S['en_sm']),
                _p(act.remarks, TH_SM),
            ])
            if bg != WHITE:
                act_row_styles.append(('BACKGROUND', (7, i), (7, i), bg))
    act_tbl = Table(
        act_data,
        colWidths=[0.8 * cm, 5.0 * cm, 2.5 * cm, 1.5 * cm,
                   1.8 * cm, 1.8 * cm, 1.7 * cm, 2.1 * cm, 2.8 * cm],
    )
    act_tbl.setStyle(_base_tbl(act_row_styles))
    story.append(act_tbl)
    story.append(Spacer(1, 0.4 * cm))

    # ── S5: Problems / Issues / Safety ────────────────────────────────────────
    story.append(_section_bar('5.  PROBLEMS / ISSUES / SAFETY', S))
    story.append(Spacer(1, 0.15 * cm))

    all_problems  = list(report.problems.all())
    tech_problems = [p for p in all_problems if p.category != 'Safety']
    safety_probs  = [p for p in all_problems if p.category == 'Safety']

    prob_cols = [2 * cm, 5.5 * cm, 3 * cm, 3.5 * cm, 2.5 * cm, 1.5 * cm]

    # Technical Issues
    story.append(_p('  Technical Issues', S['sub_hdr']))
    prob_hdr = [[
        _p('Category',   S['tbl_hdr']),
        _p('Description',S['tbl_hdr']),
        _p('Impact',     S['tbl_hdr']),
        _p('Action',     S['tbl_hdr']),
        _p('Status',     S['tbl_hdr']),
        _p('',           S['tbl_hdr']),
    ]]
    if tech_problems:
        rows = prob_hdr[:]
        for p in tech_problems:
            rows.append([
                _p(p.category, S['en_sm']),
                _p(p.description, TH_SM),
                _p(p.impact, TH_SM),
                _p(p.corrective_action, TH_SM),
                _p(p.status, S['en_sm']),
                _p('', S['en_sm']),
            ])
        tech_tbl = Table(rows, colWidths=prob_cols)
        tech_tbl.setStyle(_base_tbl())
        story.append(tech_tbl)
    else:
        nil_row = Table(
            [prob_hdr[0],
             [_p('NIL — No issues reported', S['grey']), '', '', '', '', '']],
            colWidths=prob_cols,
        )
        nil_row.setStyle(_base_tbl([('SPAN', (0, 1), (-1, 1))]))
        story.append(nil_row)

    story.append(Spacer(1, 0.2 * cm))

    # Safety
    story.append(_p('  Safety', S['sub_hdr']))
    if safety_probs:
        s_rows = prob_hdr[:]
        for p in safety_probs:
            s_rows.append([
                _p('Safety', S['en_sm']),
                _p(p.description, TH_SM),
                _p(p.impact, TH_SM),
                _p(p.corrective_action, TH_SM),
                _p(p.status, S['en_sm']),
                _p('', S['en_sm']),
            ])
        story.append(Table(s_rows, colWidths=prob_cols))
    else:
        nil_s = Table(
            [prob_hdr[0],
             [_p('NIL — No safety issues reported', S['grey']), '', '', '', '', '']],
            colWidths=prob_cols,
        )
        nil_s.setStyle(_base_tbl([('SPAN', (0, 1), (-1, 1))]))
        story.append(nil_s)

    # Safety indicators (always shown, values "—" since model lacks these fields)
    ind_data = [
        [_p('Near Miss Count', S['label']), _p('—', S['grey_c']),
         _p('Toolbox Talk', S['label']),    _p('—', S['grey_c']),
         _p('PTW Active',   S['label']),    _p('—', S['grey_c'])],
    ]
    ind_tbl = Table(ind_data, colWidths=[3.5 * cm, 2.5 * cm, 3 * cm, 2.5 * cm, 3 * cm, 3.5 * cm])
    ind_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), NAVY_LIGHT),
        ('BACKGROUND', (2, 0), (2, 0), NAVY_LIGHT),
        ('BACKGROUND', (4, 0), (4, 0), NAVY_LIGHT),
        ('GRID',       (0, 0), (-1, -1), 0.3, BORDER_GREY),
        ('FONTSIZE',   (0, 0), (-1, -1), 9),
        ('VALIGN',     (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING',   (0, 0), (-1, -1), 4),
    ]))
    story.append(Spacer(1, 0.15 * cm))
    story.append(ind_tbl)
    story.append(Spacer(1, 0.4 * cm))

    # ── S6: Next Day Plan ─────────────────────────────────────────────────────
    story.append(_section_bar('6.  NEXT DAY PLAN (LOOKAHEAD)', S))
    story.append(Spacer(1, 0.15 * cm))

    lookaheads = report.lookaheads.all()
    la_data = [[
        _p('Activity',           S['tbl_hdr']),
        _p('Location',           S['tbl_hdr']),
        _p('Planned Qty',        S['tbl_hdr']),
        _p('Equipment Required', S['tbl_hdr']),
        _p('Responsible',        S['tbl_hdr']),
        _p('Remarks',            S['tbl_hdr']),
    ]]
    if not lookaheads:
        la_data.append([_p('No next-day plan recorded.', S['grey']), '', '', '', '', ''])
        la_tbl = Table(la_data, colWidths=[5 * cm, 2.5 * cm, 2 * cm, 3 * cm, 3 * cm, 2.5 * cm])
        la_tbl.setStyle(_base_tbl([('SPAN', (0, 1), (-1, 1))]))
    else:
        for la in lookaheads:
            la_data.append([
                _p(la.planned_activity, TH_SM),
                _p('—', S['grey_c']),
                _p('—', S['grey_c']),
                _p('—', S['grey_c']),
                _p(la.responsible_person, TH_SM),
                _p(str(la.planned_date), S['en_sm']),
            ])
        la_tbl = Table(la_data, colWidths=[5 * cm, 2.5 * cm, 2 * cm, 3 * cm, 3 * cm, 2.5 * cm])
        la_tbl.setStyle(_base_tbl())
    story.append(la_tbl)
    story.append(Spacer(1, 0.4 * cm))

    # ── General Remarks ───────────────────────────────────────────────────────
    if report.remarks:
        story.append(_section_bar('7.  GENERAL REMARKS', S))
        story.append(Spacer(1, 0.15 * cm))
        story.append(_p(report.remarks, S['th']))
        story.append(Spacer(1, 0.3 * cm))

    # ── S7: Document Control Footer ───────────────────────────────────────────
    story.append(HRFlowable(width='100%', thickness=0.5, color=BORDER_GREY))
    story.append(Spacer(1, 0.3 * cm))

    sig_data = [
        [_p('Prepared By', S['sig_lbl']),  _p('Checked By', S['sig_lbl']),  _p('Approved By', S['sig_lbl'])],
        [_p(_sig_name(report.prepared_by), S['sig_val']),
         _p(_sig_name(report.checked_by),  S['sig_val']),
         _p(_sig_name(report.approved_by), S['sig_val'])],
        [_p(_sig_role(report.prepared_by), S['sig_role']),
         _p(_sig_role(report.checked_by),  S['sig_role']),
         _p(_sig_role(report.approved_by), S['sig_role'])],
    ]
    sig_tbl = Table(sig_data, colWidths=[6 * cm, 6 * cm, 6 * cm])
    sig_tbl.setStyle(TableStyle([
        ('ALIGN',         (0, 0), (-1, -1), 'CENTER'),
        ('FONTSIZE',      (0, 0), (-1, -1), 9),
        ('LINEABOVE',     (0, 1), (-1, 1), 0.8, colors.black),
        ('TOPPADDING',    (0, 0), (-1, 0), 22),
        ('TOPPADDING',    (0, 1), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(sig_tbl)
    story.append(Spacer(1, 0.3 * cm))

    # Document info row
    doc_info = [[
        _p(f'Issue Date: {report.report_date}', S['en_sm']),
        _p('Revision: Rev 0', S['en_sm']),
        _p(f'File: {proj.contract_no}-DR-{report.report_date:%Y%m%d}-Rev0.pdf', S['en_sm']),
    ]]
    doc_tbl = Table(doc_info, colWidths=[4.5 * cm, 4.5 * cm, 9 * cm])
    doc_tbl.setStyle(TableStyle([
        ('FONTSIZE',  (0, 0), (-1, -1), 8),
        ('TEXTCOLOR', (0, 0), (-1, -1), GREY_TEXT),
        ('TOPPADDING',    (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    story.append(doc_tbl)

    doc.build(story, onFirstPage=draw_cb, onLaterPages=draw_cb)
    buffer.seek(0)
    return buffer
