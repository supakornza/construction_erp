from django.db import transaction

from .models import SandBargePlacement
from .services import (
    recalculate_recovery_plan,
    recalculate_rock_accumulatives,
    recalculate_sand_accumulatives,
)
from .utils import english_day_abbreviation


def save_rock_record(form, barge_formset, user=None, set_created_by=False):
    with transaction.atomic():
        if set_created_by:
            form.instance.created_by = user
        form.instance.day_name = english_day_abbreviation(form.cleaned_data.get('record_date'))
        record = form.save()
        barge_formset.instance = record
        barge_formset.save()
        record.placed_daily_ton = sum(bp.quantity_ton for bp in record.barge_placements.all())
        record.save(update_fields=['placed_daily_ton'])
        recalculate_rock_accumulatives(record.project)
    return record


def save_sand_record(form, barge_formset, user=None, set_created_by=False):
    with transaction.atomic():
        if set_created_by:
            form.instance.created_by = user
        form.instance.day_name = english_day_abbreviation(form.cleaned_data.get('record_date'))
        tct = form.cleaned_data.get('tct_daily_ton') or 0
        mtp3 = form.cleaned_data.get('mtp3_daily_ton') or 0
        form.instance.total_daily_ton = tct + mtp3
        record = form.save()
        barge_formset.instance = record
        barge_formset.save()
        record.offshore_daily_ton = sum(
            bp.quantity_ton
            for bp in record.barge_placements.filter(
                placement_type=SandBargePlacement.PLACEMENT_OFFSHORE
            )
        )
        record.save(update_fields=['offshore_daily_ton'])
        recalculate_sand_accumulatives(record.project)
    return record


def save_revetment_record(form, item_formset, user=None, set_created_by=False):
    with transaction.atomic():
        if set_created_by:
            form.instance.created_by = user
        form.instance.day_name = english_day_abbreviation(form.cleaned_data.get('record_date'))
        record = form.save()
        item_formset.instance = record
        item_formset.save()
    return record


def save_recovery_plan_daily_items(formset):
    changed_items = formset.save(commit=False)
    for deleted in formset.deleted_objects:
        deleted.delete()
    for item in changed_items:
        item.day_name = english_day_abbreviation(item.plan_date)
        item.save()
    for form in formset.forms:
        if form in formset.deleted_forms or not form.cleaned_data:
            continue
        item = form.instance
        if item.pk and item.plan_date:
            expected_day_name = english_day_abbreviation(item.plan_date)
            if item.day_name != expected_day_name:
                item.day_name = expected_day_name
                item.save(update_fields=['day_name'])
    formset.save_m2m()


def save_recovery_plan(form, item_formset, user=None, set_prepared_by=False):
    with transaction.atomic():
        if set_prepared_by:
            form.instance.prepared_by = user
        plan = form.save()
        item_formset.instance = plan
        save_recovery_plan_daily_items(item_formset)
        recalculate_recovery_plan(plan)
    return plan
