import csv
import io
from decimal import Decimal, InvalidOperation

from django.db import transaction

from .models import BOQItem


def _to_decimal(value):
    text = (value or '').replace(',', '').strip()
    if not text:
        return None
    try:
        return Decimal(text)
    except InvalidOperation:
        return None


def import_boq_csv(project, uploaded_file, duplicate_action='skip'):
    """Bulk-create BOQItem rows from an uploaded CSV.

    Expected columns (Thai BOQ template): รหัส, รายการ, หน่วย, ปริมาณ, ราคาต่อหน่วย.
    Parent/child relationships are derived from the dotted item codes using a
    stack keyed by depth (number of dots), assuming the file is in document
    order (parents appear before their children) — true depth-first pre-order,
    which is how these documents are written.

    Returns {'created': [BOQItem, ...], 'skipped': [{'row', 'item_no', 'description', 'reason'}, ...]}.
    """
    text_stream = io.TextIOWrapper(uploaded_file.file, encoding='utf-8-sig', errors='replace')
    reader = csv.DictReader(text_stream)

    existing = set(
        BOQItem.objects.filter(project=project).values_list('item_no', flat=True)
    )
    seen = set()
    created = []
    skipped = []
    stack = []  # list of (level, BOQItem)

    with transaction.atomic():
        for row_num, row in enumerate(reader, start=2):
            item_no = (row.get('รหัส') or '').strip()
            description = (row.get('รายการ') or '').strip()
            unit = (row.get('หน่วย') or '').strip()
            contract_quantity = _to_decimal(row.get('ปริมาณ'))
            unit_rate = _to_decimal(row.get('ราคาต่อหน่วย'))

            if not item_no:
                skipped.append({'row': row_num, 'item_no': '', 'description': description,
                                'reason': 'Missing item code (รหัส)'})
                continue
            if not description:
                skipped.append({'row': row_num, 'item_no': item_no, 'description': '',
                                'reason': 'Missing description (รายการ)'})
                continue
            if item_no in seen:
                skipped.append({'row': row_num, 'item_no': item_no, 'description': description,
                                'reason': 'Duplicate item code within this file'})
                continue
            if item_no in existing and duplicate_action == 'skip':
                seen.add(item_no)
                skipped.append({'row': row_num, 'item_no': item_no, 'description': description,
                                'reason': 'Item code already exists in this project'})
                continue

            item_type = 'item' if (unit or contract_quantity is not None or unit_rate is not None) else 'header'
            level = item_no.count('.')
            while stack and stack[-1][0] >= level:
                stack.pop()
            parent = stack[-1][1] if stack else None

            defaults = {
                'description': description,
                'item_type': item_type,
                'unit': unit,
                'contract_quantity': contract_quantity,
                'unit_rate': unit_rate,
                'parent': parent,
            }

            if item_no in existing and duplicate_action == 'update':
                item = BOQItem.objects.get(project=project, item_no=item_no)
                for field, value in defaults.items():
                    setattr(item, field, value)
                item.save()
            else:
                item = BOQItem.objects.create(project=project, item_no=item_no, **defaults)
                existing.add(item_no)

            seen.add(item_no)
            created.append(item)
            stack.append((level, item))

    return {'created': created, 'skipped': skipped}
