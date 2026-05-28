"""Text normalizers + numeric/date heuristics.

Tesseract Thai LSTM under psm=6 fragments Thai words into per-character
tokens separated by spaces ('บริษัท' -> 'บ ร ิ ษั ท'). It also sometimes
reads thousand-separator ',' as decimal '.', so '36,140' becomes '36.140'.
These helpers fix those before the parser sees the text.
"""
from __future__ import annotations

import re
import unicodedata
from datetime import date, time

THAI_RANGE = '฀-๿'
_THAI_JOIN_RE = re.compile(rf'(?<=[{THAI_RANGE}])\s+(?=[{THAI_RANGE}])')
_NUM_THOUSAND_AS_DECIMAL_RE = re.compile(r'(\d{1,3})\.(\d{3})(?!\d)')
_TIME_RE = re.compile(r'\b(\d{1,2}):(\d{2})(?::(\d{2}))?\b')
_DATE_RE = re.compile(r'\b(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{2,4})\b')
_TRUCK_RE = re.compile(rf'\b(?:[{THAI_RANGE}]{{1,3}}\s?)?(\d{{1,2}})[\s\-]?(\d{{3,4}})(?:[\s\-]?(\d{{3,4}}))?\b')


def join_thai_chars(s: str) -> str:
    """Collapse single-space separators between consecutive Thai chars.

    >>> join_thai_chars('บ ร ิ ษั ท')
    'บริษัท'
    >>> join_thai_chars('hello โล ก world')
    'hello โลก world'
    """
    # repeat until stable (handles 'อ ิ ' where i is combining mark)
    prev = None
    cur = s
    while prev != cur:
        prev = cur
        cur = _THAI_JOIN_RE.sub('', cur)
    return cur


def fix_thousand_separator(num_str: str, *, expect_int: bool = True) -> str:
    """Tesseract sometimes reads ',' as '.'. If a number looks like
    `dd.ddd` (1-3 digits, period, exactly 3 digits, nothing else) and we
    expect an integer-grade thousand-separated number (weight in kg),
    treat the '.' as a thousand separator.

    >>> fix_thousand_separator('36.140')
    '36140'
    >>> fix_thousand_separator('36.140', expect_int=False)
    '36.140'
    >>> fix_thousand_separator('36,140')
    '36140'
    >>> fix_thousand_separator('1.234.567')
    '1234567'
    """
    s = num_str.strip().replace(',', '')
    if expect_int:
        # one period followed by exactly 3 digits and nothing else
        if re.fullmatch(r'\d{1,3}\.\d{3}', s):
            return s.replace('.', '')
    # otherwise treat as a normal decimal: only fix repeated thousands like 1.234.567
    parts = s.split('.')
    if len(parts) > 2 and all(len(p) == 3 for p in parts[1:]):
        return ''.join(parts)
    return s


def parse_thai_date(s: str) -> date | None:
    """Parse d/m/y where year may be Buddhist (>=2500) or AD (<=2099).

    >>> parse_thai_date('23/05/2569')
    datetime.date(2026, 5, 23)
    >>> parse_thai_date('21/05/2026')
    datetime.date(2026, 5, 21)
    >>> parse_thai_date('1/5/69')   # 2-digit Thai short year: 69 -> 2569 -> 2026
    datetime.date(2026, 5, 1)
    """
    m = _DATE_RE.search(s)
    if not m:
        return None
    d, mo, y = (int(g) for g in m.groups())
    if y < 100:
        # 2-digit year: 00-50 -> 2000+y (AD), 51-99 -> 2500+y (BE) -> AD
        y = 2000 + y if y < 50 else 2500 + y
    if y >= 2500:
        y -= 543
    try:
        return date(y, mo, d)
    except ValueError:
        return None


def parse_time(s: str) -> time | None:
    """Extract first HH:MM or HH:MM:SS in string."""
    m = _TIME_RE.search(s)
    if not m:
        return None
    h, mi, sec = m.group(1), m.group(2), m.group(3) or '0'
    try:
        return time(int(h), int(mi), int(sec))
    except ValueError:
        return None


def parse_weight_kg(s: str) -> float | None:
    """Extract weight in kg from OCR text. Handles ',' and '.' confusion.

    >>> parse_weight_kg('36,140 กก.')
    36140.0
    >>> parse_weight_kg('36.140 ก ก .')
    36140.0
    >>> parse_weight_kg('28,960.00 กก')
    28960.0
    >>> parse_weight_kg('1,234.56')
    1234.56
    """
    m = re.search(r'[\d,.]+', s.replace(' ', ''))
    if not m:
        return None
    raw = m.group(0).rstrip('.,')
    fixed = fix_thousand_separator(raw, expect_int=True)
    try:
        return float(fixed)
    except ValueError:
        return None


def kg_to_unit(kg: float, target_unit: str) -> float:
    """Convert kg to target unit (ton or kg)."""
    u = (target_unit or '').lower().strip()
    if u in ('ton', 'ตัน', 't'):
        return round(kg / 1000.0, 3)
    return kg


def parse_truck_plate(s: str) -> str | None:
    """Normalize Thai truck plate. Returns 'NN-NNNN' or 'NN-NNNN-NNNN' form.

    >>> parse_truck_plate('82-3290')
    '82-3290'
    >>> parse_truck_plate('72 4820')
    '72-4820'
    >>> parse_truck_plate('72-7760-7770')
    '72-7760-7770'
    >>> parse_truck_plate('ทะเบียนรถ : 82-3290 PO')
    '82-3290'
    """
    m = _TRUCK_RE.search(s)
    if not m:
        return None
    head, mid, tail = m.group(1), m.group(2), m.group(3)
    out = f'{head}-{mid}'
    if tail:
        out += f'-{tail}'
    return out


def normalize(text: str) -> str:
    """Run all text-level normalizers in sequence."""
    text = unicodedata.normalize('NFC', text)
    text = join_thai_chars(text)
    return text
