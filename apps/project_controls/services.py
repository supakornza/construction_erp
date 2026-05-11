import json
from decimal import Decimal
from django.db.models import Sum
from .models import (
    RockDailyRecord, SandDailyRecord, SandBargePlacement,
    RecoveryActionItem, RecoveryActionDailyProgress,
    RecoveryPlan,
    RevetmentStation, RevetmentActivity, RevetmentDailyRecord, RevetmentDailyItem,
)


def recalculate_rock_accumulatives(project):
    records = RockDailyRecord.objects.filter(project=project).order_by('record_date')
    tct_accum = placed_accum = outside_accum = Decimal('0')
    for rec in records:
        tct_accum += rec.tct_daily_ton
        placed_accum += rec.placed_daily_ton
        outside_accum += rec.core_outside_daily
        rec.tct_accum_ton = tct_accum
        rec.placed_accum_ton = placed_accum
        rec.core_outside_accum = outside_accum
        rec.save(update_fields=['tct_accum_ton', 'placed_accum_ton', 'core_outside_accum'])
    return records.count()


def recalculate_sand_accumulatives(project):
    records = SandDailyRecord.objects.filter(project=project).order_by('record_date')
    tct = mtp3 = oswald = total = offshore = onshore = inside = outside = Decimal('0')
    for rec in records:
        tct += rec.tct_daily_ton
        mtp3 += rec.mtp3_daily_ton
        oswald += rec.oswald_daily_ton
        total += rec.total_daily_ton
        offshore += rec.offshore_daily_ton
        onshore += rec.onshore_daily_ton
        inside += rec.inside_plot_daily
        outside += rec.outside_plot_daily
        rec.tct_accum_ton = tct
        rec.mtp3_accum_ton = mtp3
        rec.oswald_accum_ton = oswald
        rec.total_accum_ton = total
        rec.offshore_accum_ton = offshore
        rec.onshore_accum_ton = onshore
        rec.inside_plot_accum = inside
        rec.outside_plot_accum = outside
        rec.save(update_fields=[
            'tct_accum_ton', 'mtp3_accum_ton', 'oswald_accum_ton', 'total_accum_ton',
            'offshore_accum_ton', 'onshore_accum_ton', 'inside_plot_accum', 'outside_plot_accum',
        ])
    return records.count()


def recalculate_recovery_plan(plan):
    items = plan.daily_items.order_by('plan_date')
    planned_accum = actual_accum = Decimal('0')
    for item in items:
        planned_accum += item.planned_quantity
        actual_accum += item.actual_quantity or Decimal('0')
        item.accumulative_planned = planned_accum
        item.accumulative_actual = actual_accum
        item.save(update_fields=['accumulative_planned', 'accumulative_actual'])


def recalculate_action_item_progress(action_item):
    progress_list = action_item.daily_progress.order_by('progress_date')
    planned_accum = actual_accum = Decimal('0')
    for p in progress_list:
        planned_accum += p.planned_quantity
        actual_accum += p.actual_quantity
        p.accumulative_planned = planned_accum
        p.accumulative_actual = actual_accum
        p.status = p.compute_status()
        p.save(update_fields=['accumulative_planned', 'accumulative_actual', 'status'])


def get_rock_dashboard_data(project):
    from .models import RockBargePlacement
    records = RockDailyRecord.objects.filter(project=project).order_by('record_date')
    if not records.exists():
        return {}
    latest = records.last()
    records_list = list(records)
    chart_data = json.dumps({
        'labels': [str(r.record_date) for r in records_list],
        'daily_delivered': [float(r.tct_daily_ton) for r in records_list],
        'daily_placed': [float(r.placed_daily_ton) for r in records_list],
        'accum_delivered': [float(r.tct_accum_ton) for r in records_list],
        'accum_placed': [float(r.placed_accum_ton) for r in records_list],
    })
    barge_totals = (
        RockBargePlacement.objects
        .filter(record__project=project)
        .values('barge__name')
        .annotate(total_qty=Sum('quantity_ton'), total_trips=Sum('trips'))
        .order_by('barge__name')
    )
    return {
        'total_delivered': float(latest.tct_accum_ton),
        'total_placed': float(latest.placed_accum_ton),
        'stock_balance': float(latest.stock_balance),
        'core_outside_accum': float(latest.core_outside_accum),
        'core_inside_accum': float(latest.core_inside_accum),
        'total_records': records.count(),
        'latest_date': latest.record_date,
        'chart_data': chart_data,
        'barge_totals': barge_totals,
    }


def get_sand_dashboard_data(project):
    records = SandDailyRecord.objects.filter(project=project).order_by('record_date')
    if not records.exists():
        return {}
    latest = records.last()
    chart_records = list(records.order_by('record_date'))
    other_sources = list(
        records.exclude(sand_source='')
        .values_list('sand_source', flat=True)
        .distinct()
        .order_by('sand_source')
    )
    other_source_label = latest.sand_source_display if len(other_sources) == 1 else 'Other sources'
    chart_data = {
        'labels': [str(rec.record_date) for rec in chart_records],
        'tct_daily': [float(rec.tct_daily_ton) for rec in chart_records],
        'mtp3_daily': [float(rec.mtp3_daily_ton) for rec in chart_records],
        'other_daily': [float(rec.oswald_daily_ton) for rec in chart_records],
        'tct_accum': [float(rec.tct_accum_ton) for rec in chart_records],
        'mtp3_accum': [float(rec.mtp3_accum_ton) for rec in chart_records],
        'total_accum': [float(rec.total_accum_ton) for rec in chart_records],
    }
    barge_totals = (
        SandBargePlacement.objects
        .filter(record__project=project)
        .values('barge__name')
        .annotate(total_qty=Sum('quantity_ton'), total_trips=Sum('trips'))
        .order_by('barge__name')
    )
    return {
        'tct_accum': float(latest.tct_accum_ton),
        'mtp3_accum': float(latest.mtp3_accum_ton),
        'other_source_label': other_source_label,
        'other_source_names': ', '.join(other_sources),
        'other_source_accum': float(latest.oswald_accum_ton),
        'total_accum': float(latest.total_accum_ton),
        'offshore_accum': float(latest.offshore_accum_ton),
        'onshore_accum': float(latest.onshore_accum_ton),
        'barge_totals': barge_totals,
        'total_tct': float(latest.tct_accum_ton),
        'total_mtp3': float(latest.mtp3_accum_ton),
        'total_oswald': float(latest.oswald_accum_ton),
        'total_delivered': float(latest.total_accum_ton),
        'total_offshore': float(latest.offshore_accum_ton),
        'total_onshore': float(latest.onshore_accum_ton),
        'inside_plot': float(latest.inside_plot_accum),
        'outside_plot': float(latest.outside_plot_accum),
        'remaining_tct': float(latest.remaining_tct),
        'remaining_mtp3': float(latest.remaining_mtp3),
        'total_remaining': float(latest.total_remaining),
        'latest_date': latest.record_date,
        'chart_data': json.dumps(chart_data),
    }


def get_revetment_dashboard_data(project):
    stations = list(RevetmentStation.objects.filter(project=project, is_active=True))
    activities = list(RevetmentActivity.objects.filter(project=project, is_active=True))
    records = RevetmentDailyRecord.objects.filter(project=project).order_by('record_date')
    items = (
        RevetmentDailyItem.objects
        .filter(record__project=project)
        .select_related('record', 'station', 'activity')
        .order_by('record__record_date', 'created_at', 'pk')
    )
    total_quantity = items.aggregate(t=Sum('quantity_done'))['t'] or Decimal('0')

    labels = []
    daily = []
    accum = []
    running = Decimal('0')
    daily_rows = (
        items.exclude(quantity_done__isnull=True)
        .values('record__record_date')
        .annotate(total=Sum('quantity_done'))
        .order_by('record__record_date')
    )
    for row in daily_rows:
        running += row['total'] or Decimal('0')
        labels.append(str(row['record__record_date']))
        daily.append(float(row['total'] or 0))
        accum.append(float(running))

    activity_rows = (
        items.exclude(quantity_done__isnull=True)
        .values('activity_id', 'activity__name', 'activity__unit', 'activity__sort_order')
        .annotate(total=Sum('quantity_done'))
        .order_by('activity__sort_order', 'activity__name')
    )
    activity_labels = []
    activity_totals = []
    for row in activity_rows:
        unit = f" ({row['activity__unit']})" if row['activity__unit'] else ''
        activity_labels.append(f"{row['activity__name']}{unit}")
        activity_totals.append(float(row['total'] or 0))

    quantity_map = {}
    for row in (
        items.exclude(quantity_done__isnull=True)
        .values('station_id', 'activity_id')
        .annotate(total=Sum('quantity_done'))
    ):
        quantity_map[(row['station_id'], row['activity_id'])] = row['total'] or Decimal('0')

    latest_map = {}
    for item in items:
        latest_map[(item.station_id, item.activity_id)] = item

    matrix_rows = []
    for station in stations:
        cells = []
        for activity in activities:
            latest = latest_map.get((station.pk, activity.pk))
            total = quantity_map.get((station.pk, activity.pk))
            if activity.is_inspection:
                if latest and latest.inspection_date:
                    value = latest.inspection_date
                    css = 'table-success'
                elif latest and latest.status:
                    value = latest.status
                    css = 'table-warning' if latest.status in ['Opening', 'Ongoing'] else 'table-success'
                else:
                    value = '-'
                    css = ''
            else:
                if total:
                    unit = f' {activity.unit}' if activity.unit else ''
                    value = f'{total:,.3f}{unit}'
                    css = 'table-success'
                elif latest and latest.status:
                    value = latest.status
                    css = 'table-warning' if latest.status in ['Opening', 'Ongoing'] else 'table-success'
                else:
                    value = '-'
                    css = ''
            cells.append({'activity': activity, 'value': value, 'css': css})
        matrix_rows.append({'station': station, 'cells': cells})

    return {
        'stations': stations,
        'activities': activities,
        'record_count': records.count(),
        'item_count': items.count(),
        'total_quantity': float(total_quantity),
        'latest_date': records.last().record_date if records.exists() else None,
        'recent_records': records.order_by('-record_date')[:8],
        'matrix_rows': matrix_rows,
        'chart_data': json.dumps({
            'labels': labels,
            'daily': daily,
            'accum': accum,
            'activity_labels': activity_labels,
            'activity_totals': activity_totals,
        }),
    }


def get_rap_dashboard_data(project):
    items = RecoveryActionItem.objects.filter(recovery_plan__project=project).select_related('recovery_plan')
    total_items = items.count()
    delayed = ahead = on_track = no_activity = 0
    total_planned = total_actual = Decimal('0')
    for item in items:
        latest = item.daily_progress.order_by('-progress_date').first()
        status = latest.status if latest else 'No Activity'
        if status == 'Delayed':
            delayed += 1
        elif status == 'Ahead':
            ahead += 1
        elif status == 'On Track':
            on_track += 1
        else:
            no_activity += 1
        total_planned += item.total_quantity
        total_actual += item.total_actual
    deviation = total_actual - total_planned
    pct = round(float(total_actual) / float(total_planned) * 100, 1) if total_planned > 0 else 0
    return {
        'total_items': total_items,
        'delayed_items': delayed,
        'ahead_items': ahead,
        'on_track_items': on_track,
        'no_activity_items': no_activity,
        'total_planned': float(total_planned),
        'total_actual': float(total_actual),
        'deviation': float(deviation),
        'overall_percent': pct,
    }
