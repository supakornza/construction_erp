import json
import urllib.request
import urllib.error
from datetime import datetime, timezone

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.views.generic import TemplateView, View

THINGSPEAK_CHANNEL = 2656729
THINGSPEAK_BASE = f"https://api.thingspeak.com/channels/{THINGSPEAK_CHANNEL}/feeds.json"


def _fetch_thingspeak(minutes=1440):
    url = f"{THINGSPEAK_BASE}?minutes={minutes}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode())


def _parse_tide(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


class TideMonitorView(LoginRequiredMixin, TemplateView):
    template_name = 'tide_monitor/dashboard.html'


class TideDataAPIView(LoginRequiredMixin, View):
    """Proxy: fetches ThingSpeak data and returns computed stats + chart series."""

    def get(self, request):
        period = request.GET.get('period', '24h')
        minutes_map = {'1h': 60, '6h': 360, '24h': 1440, '7d': 10080}
        minutes = minutes_map.get(period, 1440)

        try:
            data = _fetch_thingspeak(minutes=minutes)
        except Exception as exc:
            return JsonResponse({'error': str(exc)}, status=502)

        feeds = data.get('feeds', [])
        channel = data.get('channel', {})

        readings = []
        for f in feeds:
            tide = _parse_tide(f.get('field4'))
            if tide is None:
                continue
            ts_str = f.get('created_at', '')
            try:
                ts = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
            except ValueError:
                continue
            readings.append({'ts': ts, 'tide': tide, 'ts_str': ts_str})

        if not readings:
            return JsonResponse({
                'current': None, 'max': None, 'min': None, 'avg': None,
                'chart_labels': [], 'chart_values': [],
                'channel_name': channel.get('name', 'Tide Station'),
                'period': period, 'count': 0,
            })

        tides = [r['tide'] for r in readings]
        latest = readings[-1]
        max_reading = max(readings, key=lambda r: r['tide'])
        min_reading = min(readings, key=lambda r: r['tide'])

        # Downsample chart to ≤288 points
        step = max(1, len(readings) // 288)
        sampled = readings[::step]

        def fmt_label(r):
            ts = r['ts'].astimezone(timezone.utc)
            if minutes <= 1440:
                return ts.strftime('%H:%M')
            return ts.strftime('%d/%m %H:%M')

        return JsonResponse({
            'current': latest['tide'],
            'current_time': latest['ts_str'],
            'max': max_reading['tide'],
            'max_time': max_reading['ts_str'],
            'min': min_reading['tide'],
            'min_time': min_reading['ts_str'],
            'avg': round(sum(tides) / len(tides), 3),
            'chart_labels': [fmt_label(r) for r in sampled],
            'chart_values': [r['tide'] for r in sampled],
            'channel_name': channel.get('name', 'Tide Station'),
            'channel_location': {
                'lat': channel.get('latitude'),
                'lng': channel.get('longitude'),
            },
            'period': period,
            'count': len(readings),
            'last_entry_id': channel.get('last_entry_id'),
        })
