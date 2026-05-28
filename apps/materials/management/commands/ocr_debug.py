"""Debug Tesseract OCR on a sample ticket image.

Usage:
  python manage.py ocr_debug ex/36285.jpg
  python manage.py ocr_debug ex/36285.jpg --psm 4 --threshold
  python manage.py ocr_debug ex/36285.jpg --by-line
"""
from __future__ import annotations

from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from apps.materials.ocr.service import run_ocr


class Command(BaseCommand):
    help = 'Run Tesseract OCR on an image and print raw text + confidence.'

    def add_arguments(self, parser):
        parser.add_argument('image', help='Path to image (relative to project root or absolute)')
        parser.add_argument('--lang', default='tha+eng')
        parser.add_argument('--psm', type=int, default=6,
                            help='Page segmentation mode (default 6 = uniform block)')
        parser.add_argument('--threshold', action='store_true',
                            help='Apply adaptive threshold before OCR')
        parser.add_argument('--by-line', action='store_true',
                            help='Reconstruct text grouped by line position')
        parser.add_argument('--show-words', action='store_true',
                            help='Print every word with position and confidence')
        parser.add_argument('--min-conf', type=float, default=0.0,
                            help='Hide words below this confidence (0..1)')
        parser.add_argument('--out', default=None,
                            help='Write full output (text + words) to file as UTF-8 (Windows console cannot print Thai)')

    def handle(self, *args, **opts):
        path = Path(opts['image'])
        if not path.exists():
            raise CommandError(f'image not found: {path}')

        self.stdout.write(self.style.HTTP_INFO(f'\nOCR: {path.name}'))
        self.stdout.write(f'  lang={opts["lang"]}  psm={opts["psm"]}  threshold={opts["threshold"]}')

        r = run_ocr(path, lang=opts['lang'], psm=opts['psm'], threshold=opts['threshold'])

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'  duration:    {r.duration_ms} ms'
        ))
        self.stdout.write(self.style.SUCCESS(
            f'  avg conf:    {r.avg_confidence:.2f}  ({len(r.words)} words)'
        ))

        out = r.text_by_line if opts['by_line'] else r.raw_text

        if opts['out']:
            out_path = Path(opts['out'])
            with out_path.open('w', encoding='utf-8') as f:
                f.write(f'# OCR debug for {path}\n')
                f.write(f'# lang={opts["lang"]}  psm={opts["psm"]}  threshold={opts["threshold"]}\n')
                f.write(f'# duration={r.duration_ms} ms  avg_conf={r.avg_confidence:.3f}  words={len(r.words)}\n\n')
                if opts['show_words']:
                    f.write('## WORDS\n')
                    for w in r.words:
                        if w.conf < opts['min_conf']:
                            continue
                        f.write(f'[{w.conf:.2f}] x={w.x:>4} y={w.y:>4} w={w.w:>4} h={w.h:>3}  {w.text}\n')
                    f.write('\n')
                f.write('## RAW TEXT\n')
                f.write(out)
                f.write('\n')
            self.stdout.write(self.style.SUCCESS(f'  wrote {out_path}'))
        else:
            self.stdout.write(self.style.WARNING(
                '  (no --out given; Thai text cannot be printed to Windows console — '
                'rerun with --out result.txt to read the result)'
            ))
