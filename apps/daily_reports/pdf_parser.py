"""
PDF parser for contractor daily reports (ITD/similar format).
Uses pdfplumber for text and table extraction.

PDF parsing is "best-effort" — the caller should show an editable
preview so the user can fix anything the parser missed.
"""
import re
from datetime import date, datetime as _datetime
from decimal import Decimal, InvalidOperation


# ── helpers ───────────────────────────────────────────────────────────────────

def _find_date(text):
    """Return the first parseable date found in text, or None."""
    # DD/MM/YYYY or D/M/YYYY (Thai contractor convention)
    for m in re.finditer(r'(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})', text):
        d, mon, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        try:
            return date(y, mon, d)
        except ValueError:
            pass
    # YYYY-MM-DD
    for m in re.finditer(r'(\d{4})[/\-](\d{2})[/\-](\d{2})', text):
        try:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            pass
    return None


def _clean_number(val):
    """Extract a Decimal from a cell that may contain commas, units, Thai text."""
    if val is None:
        return None
    s = str(val).strip()
    # Remove commas used as thousands separator
    s = s.replace(',', '')
    # Keep only leading numeric portion
    m = re.match(r'^-?[\d]+(?:\.[\d]+)?', s)
    if m:
        try:
            return Decimal(m.group())
        except InvalidOperation:
            pass
    return None


def _clean_int(val):
    digits = re.sub(r'\D', '', str(val or ''))
    return int(digits) if digits else None


def _strip(val):
    return str(val or '').strip()


# ── main entry point ──────────────────────────────────────────────────────────

def parse_pdf_report(file_obj):
    """
    Parse a contractor daily report PDF.

    Returns the same dict structure as importer.parse_import_file():
        report_date, contractor_name, weather_day, weather_night, wind_speed,
        total_manpower, prepared_by_name, checked_by_name, remarks,
        equipment_items, manpower_items, activities, lookaheads

    Raises ValueError with a human-readable message if the file cannot be parsed.
    """
    try:
        import pdfplumber
    except ImportError:
        raise ValueError(
            "PDF parsing requires pdfplumber. "
            "Run: pip install pdfplumber"
        )

    result = {
        'report_date': None,
        'contractor_name': '',
        'weather_day': 'Clear',
        'weather_night': 'Clear',
        'wind_speed': '',
        'total_manpower': 0,
        'prepared_by_name': '',
        'checked_by_name': '',
        'remarks': '',
        'equipment_items': [],
        'manpower_items': [],
        'activities': [],
        'lookaheads': [],
    }

    with pdfplumber.open(file_obj) as pdf:
        pages_text = [p.extract_text() or '' for p in pdf.pages]
        full_text = '\n'.join(pages_text)

        # ── Date ──────────────────────────────────────────────────────────────
        # Priority: "As of Date : DD/M/YYYY", then first date in document
        date_match = re.search(
            r'[Aa]s\s+of\s+[Dd]ate\s*:?\s*(\d{1,2}[/\-]\d{1,2}[/\-]\d{4})',
            full_text,
        )
        if date_match:
            result['report_date'] = _find_date(date_match.group(1))
        if not result['report_date']:
            result['report_date'] = _find_date(full_text)

        # ── Contractor name ───────────────────────────────────────────────────
        m = re.search(r'[Aa]ttention\s*:\s*([^\n]+)', full_text)
        if m:
            # "TTT/ITD Doc. No. …" → take the part before "Doc."
            raw = m.group(1).strip()
            result['contractor_name'] = re.split(r'\s+Doc\.', raw)[0].strip()

        # ── Total manpower ────────────────────────────────────────────────────
        m = re.search(r'Total\s+Manpower\s+(\d+)', full_text, re.IGNORECASE)
        if m:
            result['total_manpower'] = int(m.group(1))

        # ── Weather (day) ─────────────────────────────────────────────────────
        # The report uses checkboxes; pdfplumber may render the checked box
        # as a special Unicode character (✓ ✔ ☑ √ /) or just put the text first.
        WEATHER_ORDER = ['CLEAR', 'CLOUDY', 'WINDY', 'RAINING', 'HIGH WAVE']
        WEATHER_VAL   = {w: w.title().replace('High Wave', 'High Wave') for w in WEATHER_ORDER}
        WEATHER_VAL['CLEAR'] = 'Clear'
        WEATHER_VAL['CLOUDY'] = 'Cloudy'
        WEATHER_VAL['WINDY'] = 'Windy'
        WEATHER_VAL['RAINING'] = 'Raining'
        WEATHER_VAL['HIGH WAVE'] = 'High Wave'

        tick_re = r'[✓✔☑√/✓✔☐☑]'
        weather_section = re.search(
            r'Weather\s+Report(.{0,600})',
            full_text,
            re.DOTALL | re.IGNORECASE,
        )
        if weather_section:
            wsec = weather_section.group(1)
            # Look for a tick immediately before/after each weather word
            found = None
            for wkey in WEATHER_ORDER:
                pat = tick_re + r'.{0,6}' + re.escape(wkey)
                if re.search(pat, wsec, re.IGNORECASE):
                    found = WEATHER_VAL[wkey]
                    break
            # Second pass: keyword right after tick on the same line
            if not found:
                for wkey in WEATHER_ORDER:
                    pat = re.escape(wkey) + r'.{0,6}' + tick_re
                    if re.search(pat, wsec, re.IGNORECASE):
                        found = WEATHER_VAL[wkey]
                        break
            # Fallback: first weather keyword that appears in the section
            if not found:
                for wkey in WEATHER_ORDER:
                    if wkey in wsec.upper():
                        found = WEATHER_VAL[wkey]
                        break
            if found:
                result['weather_day'] = found
                result['weather_night'] = found  # same unless night section detected

        # ── Wind speed ────────────────────────────────────────────────────────
        m = re.search(r'[Ww]ind\s+speed\s*=\s*([\d.]+)\s*km', full_text)
        if m:
            result['wind_speed'] = m.group(1) + ' km/hr'

        # ── Prepared / Checked by ─────────────────────────────────────────────
        # "By Name:" and "Check Name:" can appear on the same line in some PDFs
        m = re.search(
            r'[Bb]y\s+[Nn]ame\s*:?\s*(.+?)(?=\s{3,}|[Cc]heck\s+[Nn]ame|\n|$)',
            full_text,
        )
        if m:
            result['prepared_by_name'] = m.group(1).strip()
        m = re.search(r'[Cc]heck\s+[Nn]ame\s*:?\s*(.+?)(?=\s{3,}|\n|$)', full_text)
        if m:
            result['checked_by_name'] = m.group(1).strip()

        # ── Table extraction ──────────────────────────────────────────────────
        in_lookahead = False
        for page_idx, page in enumerate(pdf.pages):
            # Use both line-based and text-based strategies for better coverage
            for strategy in (
                {'vertical_strategy': 'lines', 'horizontal_strategy': 'lines'},
                {'vertical_strategy': 'text',  'horizontal_strategy': 'lines'},
            ):
                tables = page.extract_tables(strategy) or []
                for table in tables:
                    if not table or len(table) < 2:
                        continue
                    _dispatch_table(table, result, page_idx, in_lookahead)

            # After page 1, any work-activity-like table is a lookahead
            if page_idx == 0:
                in_lookahead = _page_has_lookahead(pages_text[0])

    # ── Validate ──────────────────────────────────────────────────────────────
    if not result['report_date']:
        raise ValueError(
            "Could not find a report date in the PDF. "
            "Please ensure the file uses the standard contractor daily report format "
            "(the date should appear near 'As of Date' or in the document header)."
        )

    return result


# ── table dispatching ─────────────────────────────────────────────────────────

def _header_text(table):
    """Concatenate the first non-empty row of a table into a lower-case string."""
    for row in table[:3]:
        if row:
            line = ' '.join(_strip(c) for c in row if c)
            if line.strip():
                return line.lower()
    return ''


def _page_has_lookahead(text):
    return bool(re.search(r'daily\s+lookahead', text, re.IGNORECASE))


def _dispatch_table(table, result, page_idx, in_lookahead):
    hdr = _header_text(table)

    if any(k in hdr for k in ['today work', 'work activit', 'item']):
        if in_lookahead or _is_lookahead_table(table):
            _parse_lookahead_table(table, result)
        else:
            _parse_activities_table(table, result)
    elif any(k in hdr for k in ['equipment of machine', 'equipment name', 'machine']):
        _parse_equipment_manpower_table(table, result)
    elif 'lookahead' in hdr:
        _parse_lookahead_table(table, result)
    elif any(k in hdr for k in ['manpower', 'quantity']):
        _parse_equipment_manpower_table(table, result)


def _is_lookahead_table(table):
    """Heuristic: lookahead tables appear after 'DAILY LOOKAHEAD' heading."""
    combined = ' '.join(_strip(c) for row in table[:5] for c in (row or []) if c)
    return 'lookahead' in combined.lower()


# ── individual table parsers ──────────────────────────────────────────────────

def _parse_activities_table(table, result):
    seen = {a['description'] for a in result['activities']}
    item_counter = len(result['activities'])

    for row in table[1:]:
        if not row:
            continue
        cells = [_strip(c) for c in row]
        if len(cells) < 2:
            continue

        # column layout: No. | Description | Location | Quantity | Unit | Problem | Remarks
        item_no_raw, desc = cells[0], cells[1]
        if not desc:
            desc = cells[0]
            item_no_raw = ''

        # Skip cumulative rows, empty rows, headers repeated mid-table
        if not desc:
            continue
        desc_upper = desc.upper()
        if desc_upper.startswith('**') or 'สะสม' in desc or 'TOTAL' in desc_upper:
            continue
        if desc_upper in ('ITEM', 'NO.', 'TODAY WORK ACTIVITIES', 'DESCRIPTION'):
            continue

        item_counter += 1
        item_no = _clean_int(item_no_raw) or item_counter
        location = cells[2] if len(cells) > 2 else ''
        qty      = _clean_number(cells[3] if len(cells) > 3 else None)
        unit     = _clean_unit(cells[4] if len(cells) > 4 else '')
        problem  = cells[5] if len(cells) > 5 else ''
        remarks  = cells[6] if len(cells) > 6 else ''

        if desc not in seen:
            seen.add(desc)
            result['activities'].append({
                'item_no': item_no,
                'description': desc,
                'location': location,
                'quantity': qty,
                'unit': unit,
                'problem': problem,
                'remarks': remarks,
            })


def _parse_lookahead_table(table, result):
    seen = {la['description'] for la in result['lookaheads']}
    item_counter = len(result['lookaheads'])

    # Find the data start row (skip header rows)
    start = 0
    for i, row in enumerate(table[:4]):
        if row and any(
            kw in _strip(c).upper()
            for c in row if c
            for kw in ('WORK ACTIVIT', 'LOOKAHEAD', 'ITEM', 'NO.')
        ):
            start = i + 1
            break

    for row in table[start:]:
        if not row:
            continue
        cells = [_strip(c) for c in row]
        if len(cells) < 2:
            continue

        item_no_raw, desc = cells[0], cells[1]
        if not desc:
            desc, item_no_raw = cells[0], ''
        if not desc:
            continue
        if desc.upper() in ('ITEM', 'NO.', 'WORK ACTIVITY', 'WORK ACTIVITIES'):
            continue

        item_counter += 1
        item_no  = _clean_int(item_no_raw) or item_counter
        location = cells[2] if len(cells) > 2 else ''
        qty      = _clean_number(cells[3] if len(cells) > 3 else None)
        unit     = _clean_unit(cells[4] if len(cells) > 4 else '')
        remarks  = cells[5] if len(cells) > 5 else ''

        if desc not in seen:
            seen.add(desc)
            result['lookaheads'].append({
                'item_no': item_no,
                'description': desc,
                'location': location,
                'quantity': qty,
                'unit': unit,
                'remarks': remarks,
            })


def _parse_equipment_manpower_table(table, result):
    """
    The contractor report has a side-by-side layout:
    left columns = Equipment Name | Qty
    right columns = Manpower Role | Qty
    """
    eq_seen = {e['equipment_name'] for e in result['equipment_items']}
    mp_seen = {m['role'] for m in result['manpower_items']}

    for row in table[1:]:
        if not row:
            continue
        cells = [_strip(c) for c in row]
        while len(cells) < 4:
            cells.append('')

        eq_name, eq_qty_raw, mp_role, mp_qty_raw = (
            cells[0], cells[1], cells[2], cells[3]
        )

        # Equipment side
        if eq_name and eq_name not in eq_seen:
            qty = _clean_int(eq_qty_raw)
            if qty and qty > 0:
                eq_seen.add(eq_name)
                result['equipment_items'].append({
                    'equipment_name': eq_name,
                    'quantity': qty,
                    'remarks': '',
                })

        # Manpower side
        if mp_role and mp_role not in mp_seen:
            skip_roles = {'total manpower', 'manpower', 'quantity', 'role'}
            if mp_role.lower() in skip_roles:
                continue
            qty = _clean_int(mp_qty_raw)
            if qty is not None and qty > 0:
                mp_seen.add(mp_role)
                result['manpower_items'].append({
                    'role': mp_role,
                    'quantity': qty,
                    'company': '',
                    'remarks': '',
                })


def _clean_unit(val):
    """Remove non-ASCII noise but keep common unit strings."""
    s = _strip(val)
    # Keep only ASCII + common Thai unit chars
    s = re.sub(r'[^\w\s/.-]', '', s, flags=re.UNICODE).strip()
    return s
