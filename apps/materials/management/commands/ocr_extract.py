"""End-to-end OCR + template extraction on one image or a directory.

Usage:
  python manage.py ocr_extract ex/36285.jpg
  python manage.py ocr_extract ex/36285.jpg --json
  python manage.py ocr_extract ex/                    # whole dir, summary
  python manage.py ocr_extract ex/ --out /tmp/r.json  # full results to file
"""
from __future__ import annotations

import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from apps.materials.ocr.normalize import normalize
from apps.materials.ocr.service import run_ocr
from apps.materials.ocr.template_engine import extract


class Command(BaseCommand):
    help = 'Run OCR + template-based field extraction.'

    def add_arguments(self, parser):
        parser.add_argument('path', help='Image file or directory')
        parser.add_argument('--lang', default='tha+eng')
        parser.add_argument('--psm', type=int, default=6)
        parser.add_argument('--threshold', action='store_true')
        parser.add_argument('--out', help='Write full JSON results to this file')
        parser.add_argument('--json', action='store_true',
                            help='Print machine-readable JSON to stdout (one obj per file)')

    def handle(self, *args, **opts):
        path = Path(opts['path'])
        if not path.exists():
            raise CommandError(f'path not found: {path}')

        if path.is_dir():
            images = sorted([p for p in path.iterdir() if p.suffix.lower() in {'.jpg', '.jpeg', '.png'}])
        else:
            images = [path]

        results = []
        for img_path in images:
            try:
                ocr = run_ocr(img_path, lang=opts['lang'], psm=opts['psm'],
                              threshold=opts['threshold'])
                normalized = normalize(ocr.raw_text)
                ex = extract(ocr.words, normalized)
                row = {
                    'file': str(img_path),
                    'ocr': {
                        'duration_ms': ocr.duration_ms,
                        'avg_confidence': round(ocr.avg_confidence, 3),
                        'word_count': len(ocr.words),
                    },
                    **ex.as_dict(),
                }
                # date/time objects -> isoformat already done; ensure JSON-safe
                results.append(row)
                self._print_summary(img_path.name, ex, ocr.duration_ms,
                                    ocr.avg_confidence)
            except Exception as e:
                row = {'file': str(img_path), 'error': repr(e)}
                results.append(row)
                self.stdout.write(self.style.ERROR(f'  {img_path.name}: ERROR {e}'))

        if opts['out']:
            with Path(opts['out']).open('w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2, default=str)
            self.stdout.write(self.style.SUCCESS(f'\nWrote {opts["out"]}'))

        if opts['json']:
            print(json.dumps(results, ensure_ascii=False, default=str))

        # Aggregate summary
        ok = [r for r in results if 'error' not in r]
        if len(ok) > 1:
            template_counts: dict[str, int] = {}
            field_hits: dict[str, int] = {}
            for r in ok:
                template_counts[r['template']] = template_counts.get(r['template'], 0) + 1
                for k in (r.get('fields') or {}):
                    field_hits[k] = field_hits.get(k, 0) + 1
            self.stdout.write('\n=== SUMMARY ===')
            self.stdout.write(f'Files: {len(ok)} OK, {len(results) - len(ok)} errors')
            self.stdout.write('Templates: ' + ', '.join(f'{k}={v}' for k, v in template_counts.items()))
            self.stdout.write('Field hit rate:')
            for k, v in sorted(field_hits.items(), key=lambda x: -x[1]):
                self.stdout.write(f'  {k:20s} {v}/{len(ok)} ({v*100//len(ok)}%)')

    def _print_summary(self, fname, ex, dur, conf):
        flag = 'OK ' if ex.template_key != 'unknown' else 'NO '
        fields_short = '  '.join(
            f'{k}={"y" if v.value is not None else "n"}'
            for k, v in ex.fields.items()
        ) if ex.fields else '(no fields)'
        self.stdout.write(
            f'  {flag} {fname:30s} '
            f'tmpl={ex.template_key:8s} '
            f'score={ex.detect_score} '
            f'fields={len(ex.fields)} '
            f'conf={conf:.2f} '
            f'dur={dur}ms'
        )
