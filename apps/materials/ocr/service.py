"""Tesseract wrapper. Returns raw text + per-word data + avg confidence."""
from __future__ import annotations

import os
import shutil
import time
from dataclasses import dataclass, field
from pathlib import Path

import pytesseract
from PIL import Image

from . import preprocess

# Common Tesseract binary locations on supported deployments.
DEFAULT_TESSERACT_CMD = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
DEFAULT_TESSERACT_CANDIDATES = [
    '/usr/bin/tesseract',
    '/usr/local/bin/tesseract',
    '/snap/bin/tesseract',
    DEFAULT_TESSERACT_CMD,
]
PROJECT_TESSDATA = Path(__file__).resolve().parents[3] / 'tessdata'


def _is_executable(cmd: str) -> bool:
    return os.path.isfile(cmd) and os.access(cmd, os.X_OK)


def _candidate_commands() -> list[str]:
    candidates = [
        os.environ.get('TESSERACT_CMD'),
        shutil.which('tesseract'),
        *DEFAULT_TESSERACT_CANDIDATES,
    ]
    return [cmd for cmd in candidates if cmd]


def _configure():
    for cmd in _candidate_commands():
        if _is_executable(cmd):
            pytesseract.pytesseract.tesseract_cmd = cmd
            break
    # tha.traineddata lives in project-local tessdata (winget install lacks Thai)
    if PROJECT_TESSDATA.exists():
        os.environ['TESSDATA_PREFIX'] = str(PROJECT_TESSDATA)


@dataclass
class Word:
    text: str
    x: int
    y: int
    w: int
    h: int
    conf: float  # 0..1


@dataclass
class OcrResult:
    raw_text: str
    words: list[Word]
    avg_confidence: float  # 0..1, only over words with conf > 0
    duration_ms: int
    lang: str = 'tha+eng'
    psm: int = 6

    @property
    def text_by_line(self) -> str:
        """Reconstruct text grouped by line (sorted top-to-bottom, left-to-right)."""
        if not self.words:
            return ''
        # bucket words into lines by y position (height-tolerant)
        lines: list[list[Word]] = []
        for w in sorted(self.words, key=lambda x: (x.y, x.x)):
            placed = False
            for line in lines:
                if abs(line[0].y - w.y) < line[0].h * 0.7:
                    line.append(w)
                    placed = True
                    break
            if not placed:
                lines.append([w])
        return '\n'.join(
            ' '.join(w.text for w in sorted(line, key=lambda x: x.x))
            for line in lines
        )


def run_ocr(path: str | Path, *, lang: str = 'tha+eng', psm: int = 6,
            threshold: bool = False) -> OcrResult:
    _configure()
    img = preprocess.prepare(path, threshold=threshold)
    t0 = time.time()
    config = f'--psm {psm}'
    try:
        data = pytesseract.image_to_data(
            img, lang=lang, config=config, output_type=pytesseract.Output.DICT,
        )
    except pytesseract.pytesseract.TesseractNotFoundError as exc:
        configured_cmd = pytesseract.pytesseract.tesseract_cmd
        tried = ', '.join(repr(cmd) for cmd in _candidate_commands())
        raise RuntimeError(
            'Tesseract executable was not found. Install Tesseract OCR or set '
            f'TESSERACT_CMD to its full path. Active command: {configured_cmd!r}. '
            f'Checked: {tried}. On Ubuntu/Debian VPS run: '
            'sudo apt-get update && sudo apt-get install -y tesseract-ocr tesseract-ocr-tha'
        ) from exc
    duration_ms = int((time.time() - t0) * 1000)

    words: list[Word] = []
    confs: list[float] = []
    n = len(data['text'])
    for i in range(n):
        text = (data['text'][i] or '').strip()
        conf_raw = data['conf'][i]
        try:
            conf = float(conf_raw)
        except (TypeError, ValueError):
            conf = -1
        if not text or conf < 0:
            continue
        words.append(Word(
            text=text,
            x=int(data['left'][i]),
            y=int(data['top'][i]),
            w=int(data['width'][i]),
            h=int(data['height'][i]),
            conf=conf / 100.0,
        ))
        if conf > 0:
            confs.append(conf / 100.0)

    raw_text = '\n'.join(w.text for w in words)
    avg_conf = sum(confs) / len(confs) if confs else 0.0
    return OcrResult(
        raw_text=raw_text, words=words, avg_confidence=avg_conf,
        duration_ms=duration_ms, lang=lang, psm=psm,
    )
