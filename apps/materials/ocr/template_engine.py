"""Template-based field extractor for weight tickets.

Pipeline:
  1. load all *.yaml in templates/  (cached)
  2. detect template: count detect keyword matches against normalized
     OCR text, pick highest-scoring template above min_matches threshold
  3. for each field rule, locate the anchor word in the OCR words list
     (fuzzy match, score >= 0.7), then take the value from the direction
     (right / down) and run the configured extractor (regex / weight_kg
     / thai_date / time / truck_plate)
  4. return ExtractedFields with per-field confidence
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field as dc_field
from pathlib import Path
from typing import Any, Callable

import yaml
from rapidfuzz import fuzz

from .normalize import (
    join_thai_chars, parse_thai_date, parse_time, parse_truck_plate,
    parse_weight_kg, normalize,
)
from .service import Word

TEMPLATES_DIR = Path(__file__).resolve().parent / 'templates'

# anchor matching
FUZZY_THRESHOLD = 0.70
MAX_ANCHOR_DISTANCE_PX = 800   # don't look more than this far from anchor


@dataclass
class FieldValue:
    raw: str                     # the OCR-extracted string before normalization
    value: Any                   # parsed/typed result (str/date/time/float/None)
    confidence: float            # 0..1 (avg of anchor + value-word confidences)


@dataclass
class ExtractedFields:
    template_key: str
    template_supplier: str
    detect_score: int            # number of detect keywords matched
    fields: dict[str, FieldValue] = dc_field(default_factory=dict)
    warnings: list[str] = dc_field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            'template': self.template_key,
            'supplier': self.template_supplier,
            'detect_score': self.detect_score,
            'fields': {k: v.value for k, v in self.fields.items()},
            'raw_fields': {k: v.raw for k, v in self.fields.items()},
            'field_confidence': {k: v.confidence for k, v in self.fields.items()},
            'warnings': self.warnings,
        }


# ─── extractors registry ─────────────────────────────────────────────

def _ex_regex(text: str, rule: dict) -> Any:
    pat = rule.get('regex')
    if not pat:
        return text.strip()
    m = re.search(pat, text)
    return m.group(0) if m else None


def _ex_truck_plate(text: str, rule: dict) -> Any:
    return parse_truck_plate(text)


def _ex_weight_kg(text: str, rule: dict) -> Any:
    return parse_weight_kg(text)


def _ex_thai_date(text: str, rule: dict) -> Any:
    d = parse_thai_date(text)
    return d.isoformat() if d else None


def _ex_time(text: str, rule: dict) -> Any:
    t = parse_time(text)
    return t.strftime('%H:%M') if t else None


EXTRACTORS: dict[str, Callable[[str, dict], Any]] = {
    'regex': _ex_regex,
    'truck_plate': _ex_truck_plate,
    'weight_kg': _ex_weight_kg,
    'thai_date': _ex_thai_date,
    'time': _ex_time,
}

# Whole-doc extractors that operate on the full line list and don't need an anchor.
# Useful for pattern-based extraction where anchor labels are unreliable.
TABLE_ROW_PATTERN = re.compile(
    r'(\d{1,2}[/.\-]\d{1,2}[/.\-]\d{2,4}).{0,20}?(\d{1,2}:\d{2}(?::\d{2})?).{0,20}?([\d,.]+)'
)


def doc_extract_delivery_row(lines: list['Line'], rule: dict, want: str) -> 'FieldValue | None':
    """For weight-ticket tables that have ROWs like 'date time weight', pick the LAST
    such row (the รถออก / out-row) and return the requested component.

    want in {'date', 'time', 'weight'}
    """
    matches: list[tuple[int, re.Match[str]]] = []
    for i, ln in enumerate(lines):
        m = TABLE_ROW_PATTERN.search(ln.text)
        if m:
            matches.append((i, m))
    if not matches:
        return None
    idx, m = matches[-1]   # last row = out row
    line_conf = lines[idx].conf
    if want == 'date':
        d = parse_thai_date(m.group(1))
        return FieldValue(raw=m.group(0), value=d.isoformat() if d else None,
                          confidence=line_conf) if d else None
    if want == 'time':
        t = parse_time(m.group(2))
        return FieldValue(raw=m.group(0), value=t.strftime('%H:%M') if t else None,
                          confidence=line_conf) if t else None
    return None


# ─── template loading ────────────────────────────────────────────────

_cache: list[dict] | None = None


def load_templates(force: bool = False) -> list[dict]:
    global _cache
    if _cache is not None and not force:
        return _cache
    out = []
    for p in sorted(TEMPLATES_DIR.glob('*.yaml')):
        with p.open(encoding='utf-8') as f:
            t = yaml.safe_load(f)
        if not t or not t.get('key'):
            continue
        out.append(t)
    _cache = out
    return out


# ─── supplier detection ──────────────────────────────────────────────

DETECT_FUZZY_THRESHOLD = 80   # rapidfuzz partial_ratio 0..100


def _keyword_in_text(keyword: str, text_low: str) -> bool:
    """Substring match first (exact), then fuzzy partial_ratio fallback for
    Thai keywords where OCR fragments inject extra chars."""
    k = keyword.lower()
    if k in text_low:
        return True
    # fuzzy fallback: keyword present in text with up to ~20% noise
    score = fuzz.partial_ratio(k, text_low)
    return score >= DETECT_FUZZY_THRESHOLD


def detect_template(normalized_text: str, templates: list[dict] | None = None) -> tuple[dict | None, int]:
    """Return (template, detect_score) or (None, 0).

    Score = number of detect keywords found (exact OR fuzzy).
    """
    templates = templates or load_templates()
    text_low = normalized_text.lower()
    best = None
    best_score = -1
    for t in templates:
        det = t.get('detect', {})
        keywords = det.get('any_of', [])
        min_matches = det.get('min_matches', 1)
        score = sum(1 for k in keywords if _keyword_in_text(k, text_low))
        if score < min_matches:
            continue
        prio = t.get('priority', 0)
        if (score, prio) > (best_score, best.get('priority', 0) if best else -1):
            best = t
            best_score = score
    return best, best_score if best else 0


# ─── anchor + value extraction ───────────────────────────────────────

@dataclass
class Line:
    text: str          # joined-Thai text of all words on this line, separated by spaces
    y: int             # line top
    h: int             # line height
    conf: float        # average word conf
    word_count: int


def words_to_lines(words: list[Word]) -> list[Line]:
    """Cluster words into lines by y-overlap; join Thai char fragments within a line."""
    if not words:
        return []
    sorted_w = sorted(words, key=lambda w: (w.y, w.x))
    groups: list[list[Word]] = []
    for w in sorted_w:
        placed = False
        for g in groups:
            if abs(g[0].y - w.y) < max(g[0].h, w.h) * 0.7:
                g.append(w)
                placed = True
                break
        if not placed:
            groups.append([w])
    lines: list[Line] = []
    for g in groups:
        g.sort(key=lambda w: w.x)
        joined = join_thai_chars(' '.join(w.text for w in g))
        lines.append(Line(
            text=joined,
            y=min(w.y for w in g),
            h=max(w.h for w in g),
            conf=sum(w.conf for w in g) / len(g),
            word_count=len(g),
        ))
    return lines


def _anchor_matches(anchor: str, line_text: str) -> tuple[int, int] | None:
    """Return (match_start, match_end) char positions of anchor inside line_text.
    Uses substring first, fuzzy fallback. Returns None if below threshold."""
    a = anchor.lower()
    tl = line_text.lower()
    i = tl.find(a)
    if i >= 0:
        return i, i + len(a)
    # fuzzy: find best alignment
    score = fuzz.partial_ratio(a, tl)
    if score < int(FUZZY_THRESHOLD * 100):
        return None
    # rough position: use partial_ratio_alignment for char-level position
    al = fuzz.partial_ratio_alignment(a, tl)
    if al is None:
        return None
    return al.dest_start, al.dest_end


def _find_anchor_line(lines: list[Line], anchor: str, skip_first: bool = False
                      ) -> tuple[int, int, int] | None:
    """Return (line_index, anchor_end_pos, anchor_start_pos) for the first
    (or second, if skip_first) line that matches the anchor.
    """
    matches: list[tuple[int, int, int]] = []
    for idx, ln in enumerate(lines):
        m = _anchor_matches(anchor, ln.text)
        if m:
            matches.append((idx, m[1], m[0]))
    if not matches:
        return None
    if skip_first and len(matches) > 1:
        return matches[1]
    return matches[0]


def extract_field(lines: list[Line], rule: dict) -> FieldValue | None:
    if 'constant' in rule:
        return FieldValue(raw=rule['constant'], value=rule['constant'], confidence=1.0)

    anchors = [(rule.get('anchor'), rule.get('prefer_occurrence', 1))]
    if rule.get('fallback_anchor'):
        anchors.append((rule['fallback_anchor'], rule.get('fallback_occurrence', 1)))

    direction = rule.get('direction', 'right')

    located = None
    for anchor, occurrence in anchors:
        if not anchor:
            continue
        located = _find_anchor_line(lines, anchor, skip_first=(occurrence >= 2))
        if located:
            break
    if not located:
        return None

    line_idx, anchor_end, anchor_start = located
    anchor_line = lines[line_idx]

    if direction == 'right':
        raw = anchor_line.text[anchor_end:].lstrip(' :|.-')
        raw = raw[:120]  # limit
        conf_base = anchor_line.conf
    elif direction == 'down':
        # take the next non-empty line whose x-range plausibly overlaps
        if line_idx + 1 >= len(lines):
            return None
        nxt = lines[line_idx + 1]
        raw = nxt.text.strip()
        conf_base = (anchor_line.conf + nxt.conf) / 2
    elif direction == 'right_or_down':
        right_part = anchor_line.text[anchor_end:].lstrip(' :|.-').strip()
        if right_part:
            raw = right_part
            conf_base = anchor_line.conf
        elif line_idx + 1 < len(lines):
            raw = lines[line_idx + 1].text.strip()
            conf_base = (anchor_line.conf + lines[line_idx + 1].conf) / 2
        else:
            return None
    else:
        return None

    extractor_name = rule.get('extractor', 'regex')
    extractor = EXTRACTORS.get(extractor_name, _ex_regex)
    value = extractor(raw, rule)
    if value is None or value == '':
        return None

    # Max-words trimming (only when extractor is plain text/regex with max_words)
    if extractor_name == 'regex' and rule.get('max_words'):
        toks = str(value).split()
        value = ' '.join(toks[:rule['max_words']])

    return FieldValue(raw=raw.strip(), value=value, confidence=conf_base)


def extract(words: list[Word], normalized_text: str) -> ExtractedFields:
    templates = load_templates()
    template, score = detect_template(normalized_text, templates)
    if not template:
        return ExtractedFields(
            template_key='unknown', template_supplier='', detect_score=0,
            warnings=['no template matched'],
        )

    lines = words_to_lines(words)
    out = ExtractedFields(
        template_key=template['key'],
        template_supplier=template.get('supplier_name', ''),
        detect_score=score,
    )
    for field_name, rule in (template.get('fields') or {}).items():
        try:
            doc_kind = rule.get('doc_extractor')
            if doc_kind == 'delivery_row_date':
                fv = doc_extract_delivery_row(lines, rule, 'date')
            elif doc_kind == 'delivery_row_time':
                fv = doc_extract_delivery_row(lines, rule, 'time')
            else:
                fv = extract_field(lines, rule)
        except Exception as e:
            out.warnings.append(f'{field_name}: extractor error: {e}')
            continue
        if fv is None:
            out.warnings.append(f'{field_name}: not found')
            continue
        out.fields[field_name] = fv
    return out
