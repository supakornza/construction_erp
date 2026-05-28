import html
import json
import re
import threading
import urllib.parse
import urllib.request
import http.cookiejar
from html.parser import HTMLParser

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.views.generic import TemplateView, View

# ── DataQSC site constants ────────────────────────────────────────────────────
_LOGIN_URL   = "https://dataqsc.com/eqms/modules/index/check.php"
_TESTDATA_URL = "https://dataqsc.com/eqms/modules/index/testdata.php"
_TABLE_URL   = "https://dataqsc.com/eqms/index.php?names=viewdata&files=index&type={interval}&table=95"
_USERID      = "ttteia"
_PASS        = "ttt2025#"

# NTU status thresholds (Thai environmental guideline for construction runoff)
_THRESHOLDS = [
    (500, "CRITICAL",  "danger",  "danger"),
    (150, "HIGH",      "warning", "warning"),
    (75,  "MODERATE",  "info",    "info"),
    (25,  "LOW",       "success", "success"),
    (0,   "CLEAR",     "primary", "primary"),
]


# ── HTML table parser ─────────────────────────────────────────────────────────
class _ViewTableParser(HTMLParser):
    """Extracts rows from DataTables-rendered #viewtable."""

    def __init__(self):
        super().__init__()
        self._in_target = False
        self._in_tbody  = False
        self._in_row    = False
        self._in_td     = False
        self._cell      = ''
        self._row       = []
        self.rows       = []

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag == 'table' and d.get('id') == 'viewtable':
            self._in_target = True
        if not self._in_target:
            return
        if tag == 'tbody':
            self._in_tbody = True
        elif tag == 'tr' and self._in_tbody:
            self._in_row = True
            self._row = []
        elif tag == 'td' and self._in_row:
            self._in_td = True
            self._cell = ''

    def handle_endtag(self, tag):
        if tag == 'table' and self._in_target:
            self._in_target = False
        if tag == 'tbody':
            self._in_tbody = False
        elif tag == 'tr' and self._in_row:
            self._in_row = False
            if len(self._row) >= 2:
                self.rows.append(self._row[:])
        elif tag == 'td' and self._in_td:
            self._in_td = False
            self._row.append(self._cell.strip())

    def handle_data(self, data):
        if self._in_td:
            self._cell += data


# ── DataQSC session singleton ─────────────────────────────────────────────────
class _DataQSCSession:
    """Thread-safe session with auto re-login."""

    def __init__(self):
        self._lock   = threading.Lock()
        self._jar    = http.cookiejar.CookieJar()
        self._opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self._jar)
        )
        self._logged_in = False

    def _request(self, url, data=None, method='GET'):
        req = urllib.request.Request(url, data=data, method=method)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)')
        req.add_header('Referer', 'https://dataqsc.com/')
        with self._opener.open(req, timeout=15) as resp:
            body = resp.read()
            final_url = resp.geturl()
        return body.decode('utf-8', errors='replace'), final_url

    def _login(self):
        payload = urllib.parse.urlencode({'userid': _USERID, 'pass': _PASS}).encode()
        _, final_url = self._request(_LOGIN_URL, data=payload, method='POST')
        self._logged_in = 'login' not in final_url

    def _ensure_login(self):
        if not self._logged_in:
            self._login()

    def get_json(self, url):
        with self._lock:
            self._ensure_login()
            body, final_url = self._request(url)
            if 'login' in final_url:
                self._logged_in = False
                self._login()
                body, _ = self._request(url)
            return json.loads(body)

    def get_html(self, url):
        with self._lock:
            self._ensure_login()
            body, final_url = self._request(url)
            if 'login' in final_url:
                self._logged_in = False
                self._login()
                body, _ = self._request(url)
            return body


_session = _DataQSCSession()


# ── Helpers ───────────────────────────────────────────────────────────────────
def _parse_current(data: list) -> dict | None:
    """Parse testdata.php JSON → {value, datetime, unit, lat, lng}."""
    if not data:
        return None
    station = data[0]
    raw = html.unescape(station.get('lastval', ''))
    # Format: "Last date: 2026-05-15 19:00:00 <br>Data: [Turbidity:  1.8  NTU]"
    dt_val = None
    ntu_val = None
    for part in re.split(r'<br\s*/?>', raw, flags=re.IGNORECASE):
        part = part.strip()
        if part.lower().startswith('last date:'):
            dt_val = part.split(':', 1)[1].strip()
        elif 'turbidity' in part.lower():
            m = re.search(r'[\d]+\.?[\d]*', part)
            if m:
                try:
                    ntu_val = float(m.group())
                except ValueError:
                    pass
    return {
        'value': ntu_val,
        'datetime': dt_val,
        'unit': 'NTU',
        'lat': station.get('lat'),
        'lng': station.get('lng'),
        'station': station.get('title', 'TTT_Turbitdity'),
    }


def _get_status(ntu):
    if ntu is None:
        return {'label': 'N/A', 'color': 'secondary', 'badge': 'secondary'}
    for threshold, label, color, badge in _THRESHOLDS:
        if ntu > threshold:
            return {'label': label, 'color': color, 'badge': badge}
    return {'label': 'CLEAR', 'color': 'primary', 'badge': 'primary'}


def _parse_table(html: str) -> list[dict]:
    """Parse HTML table → list of {dt, value}."""
    parser = _ViewTableParser()
    parser.feed(html)
    readings = []
    for row in parser.rows:
        try:
            val = float(row[1])
        except (ValueError, IndexError):
            continue
        readings.append({'dt': row[0], 'value': val})
    return readings


def _compute_stats(readings):
    if not readings:
        return None, None, None, None
    vals = [r['value'] for r in readings]
    max_r = max(readings, key=lambda r: r['value'])
    min_r = min(readings, key=lambda r: r['value'])
    return max_r, min_r, round(sum(vals) / len(vals), 2), vals


# Interval names for UI
_INTERVAL_LABELS = {
    'T10':   '10-minute',
    'T60':   'Hourly',
    'T1440': 'Daily',
}

_PERIOD_INTERVALS = {
    '24h': 'T10',
    '7d':  'T60',
    '30d': 'T60',
    '60d': 'T1440',
}


# ── Views ─────────────────────────────────────────────────────────────────────
class TurbidityMonitorView(LoginRequiredMixin, TemplateView):
    template_name = 'turbidity_monitor/dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['thresholds'] = [
            {'max': 500, 'label': 'CRITICAL (>500)',  'color': 'danger'},
            {'max': 150, 'label': 'HIGH (151–500)',    'color': 'warning'},
            {'max': 75,  'label': 'MODERATE (76–150)', 'color': 'info'},
            {'max': 25,  'label': 'LOW (26–75)',        'color': 'success'},
            {'max': 0,   'label': 'CLEAR (0–25)',       'color': 'primary'},
        ]
        return ctx


class TurbidityDataAPIView(LoginRequiredMixin, View):
    """Proxy: returns current reading + historical chart data as JSON."""

    def get(self, request):
        period = request.GET.get('period', '24h')
        interval = _PERIOD_INTERVALS.get(period, 'T60')

        # Fetch current reading
        try:
            raw_current = _session.get_json(_TESTDATA_URL)
            current_info = _parse_current(raw_current)
        except Exception as exc:
            return JsonResponse({'error': f'Current read failed: {exc}'}, status=502)

        # Fetch historical table
        try:
            html = _session.get_html(_TABLE_URL.format(interval=interval))
            readings = _parse_table(html)
        except Exception as exc:
            return JsonResponse({'error': f'History read failed: {exc}'}, status=502)

        # Limit data to requested period
        limit_map = {'24h': 144, '7d': 168, '30d': 720, '60d': 60}
        limit = limit_map.get(period, 144)
        readings_period = readings[:limit]  # newest first

        max_r, min_r, avg_val, vals = _compute_stats(readings_period)
        current_val = current_info['value'] if current_info else None
        status = _get_status(current_val)

        # Chart: reverse to chronological order
        chart_data = list(reversed(readings_period))
        step = max(1, len(chart_data) // 200)
        chart_sampled = chart_data[::step]

        return JsonResponse({
            'current': current_val,
            'current_dt': current_info['datetime'] if current_info else None,
            'station': current_info['station'] if current_info else 'TTT_Turbitdity',
            'lat': current_info['lat'] if current_info else None,
            'lng': current_info['lng'] if current_info else None,
            'unit': 'NTU',
            'status': status,
            'max': max_r['value'] if max_r else None,
            'max_dt': max_r['dt'] if max_r else None,
            'min': min_r['value'] if min_r else None,
            'min_dt': min_r['dt'] if min_r else None,
            'avg': avg_val,
            'count': len(readings_period),
            'interval': _INTERVAL_LABELS.get(interval, interval),
            'period': period,
            'chart_labels': [r['dt'][5:16] for r in chart_sampled],  # MM-DD HH:MM
            'chart_values': [r['value'] for r in chart_sampled],
            'thresholds': {
                'critical': 500,
                'high': 150,
                'moderate': 75,
                'low': 25,
            },
        })
