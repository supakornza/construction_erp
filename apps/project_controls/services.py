import json
from datetime import date, timedelta
from decimal import Decimal
from django.db.models import Count, Max, Q, Sum
from .models import (
    RockDailyRecord, RockBargePlacement, RockDashboardSettings, RockStationProgress,
    SandDailyRecord, SandBargePlacement, SandDashboardSettings, SandAreaProgress,
    RecoveryActionItem, RecoveryActionDailyProgress,
    RecoveryPlan,
    RevetmentStation, RevetmentActivity, RevetmentDailyRecord, RevetmentDailyItem,
)


def _fmt_short_date(value):
    return value.strftime('%d %b') if value else ''


def _safe_pct(numerator, denominator):
    if denominator and denominator > 0:
        return round(float(numerator) / float(denominator) * 100, 1)
    return None


def _forecast_completion_date(start_date, remaining_qty, average_daily):
    if not start_date or not remaining_qty or not average_daily or average_daily <= 0:
        return None
    days = int((Decimal(str(remaining_qty)) / Decimal(str(average_daily))).to_integral_value(rounding='ROUND_CEILING'))
    return start_date + timedelta(days=max(days, 0))


def _display_baseline_metrics(latest_date, completed_qty, delivered_qty, configured_target, average_daily):
    target_qty = configured_target
    target_note = 'Configured BOQ target'
    if target_qty is None or target_qty <= 0:
        target_qty = max(completed_qty or Decimal('0'), delivered_qty or Decimal('0'), Decimal('1'))
        target_note = 'Assumed from current production'

    completion_pct = _safe_pct(completed_qty, target_qty) or 0
    completion_pct = min(max(completion_pct, 0), 100)
    remaining_qty = max(target_qty - completed_qty, Decimal('0'))
    forecast_date = _forecast_completion_date(latest_date, remaining_qty, average_daily) or latest_date

    return {
        'display_completion_percent': completion_pct,
        'display_forecast_completion_date': forecast_date,
        'display_target_note': target_note,
        'display_average_daily': float(average_daily or Decimal('0')),
    }


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
    tct = mtp3 = chalothon = khlong_bang_phai = oswald = total = offshore = onshore = inside = outside = Decimal('0')
    for rec in records:
        tct += rec.tct_daily_ton
        mtp3 += rec.mtp3_daily_ton
        chalothon += rec.chalothon_daily_ton
        khlong_bang_phai += rec.khlong_bang_phai_daily_ton
        oswald += rec.oswald_daily_ton
        rec.total_daily_ton = rec.tct_daily_ton + rec.mtp3_daily_ton
        total += rec.total_daily_ton
        offshore += rec.offshore_daily_ton
        onshore += rec.onshore_daily_ton
        inside += rec.inside_plot_daily
        outside += rec.outside_plot_daily
        rec.tct_accum_ton = tct
        rec.mtp3_accum_ton = mtp3
        rec.chalothon_accum_ton = chalothon
        rec.khlong_bang_phai_accum_ton = khlong_bang_phai
        rec.oswald_accum_ton = oswald
        rec.total_accum_ton = total
        rec.offshore_accum_ton = offshore
        rec.onshore_accum_ton = onshore
        rec.inside_plot_accum = inside
        rec.outside_plot_accum = outside
        rec.save(update_fields=[
            'tct_accum_ton', 'mtp3_accum_ton', 'oswald_accum_ton', 'total_daily_ton', 'total_accum_ton',
            'chalothon_accum_ton', 'khlong_bang_phai_accum_ton',
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


def get_rock_dashboard_data(project, filters=None):
    filters = filters or {}
    records = RockDailyRecord.objects.filter(project=project).order_by('record_date')

    date_from = filters.get('date_from')
    date_to = filters.get('date_to')
    if date_from:
        records = records.filter(record_date__gte=date_from)
    if date_to:
        records = records.filter(record_date__lte=date_to)

    range_days = filters.get('range_days')
    if range_days and not date_from and not date_to:
        end = records.aggregate(last=Max('record_date'))['last'] or date.today()
        records = records.filter(record_date__gte=end - timedelta(days=range_days - 1))

    if filters.get('material_type'):
        records = records.filter(material_type=filters['material_type'])
    if filters.get('source_quarry'):
        records = records.filter(source_quarry__icontains=filters['source_quarry'])
    if filters.get('destination_area'):
        records = records.filter(destination_area__icontains=filters['destination_area'])
    if filters.get('station_range'):
        records = records.filter(station_of_core__icontains=filters['station_range'])
    if filters.get('barge_id'):
        records = records.filter(barge_placements__barge_id=filters['barge_id']).distinct()

    settings = RockDashboardSettings.objects.filter(project=project).first()
    if not records.exists():
        return {
            'chart_data': '{}',
            'barge_totals': [],
            'station_rows': [],
            'settings': settings,
            'has_data': False,
        }

    latest = records.last()
    agg = records.aggregate(
        production_days=Count('pk', filter=Q(placed_daily_ton__gt=0)),
        sum_placed_daily=Sum('placed_daily_ton'),
    )
    production_days = agg['production_days'] or 0
    records_list = list(records)
    total_delivered = latest.tct_accum_ton
    total_placed = latest.placed_accum_ton
    available_stock = total_delivered - total_placed
    average_daily_placement = (
        (agg['sum_placed_daily'] / production_days) if production_days else None
    )
    target_qty = settings.target_quantity_ton if settings else None
    daily_target = settings.daily_target_placement_ton if settings else None
    remaining_qty = (target_qty - total_placed) if target_qty is not None else None
    completion_pct = _safe_pct(total_placed, target_qty)
    stock_pct = _safe_pct(available_stock, total_delivered)
    placement_delivery_pct = _safe_pct(total_placed, total_delivered)
    placement_delivery_pct_capped = min(max(placement_delivery_pct or 0, 0), 100)
    forecast_date = _forecast_completion_date(latest.record_date, remaining_qty, average_daily_placement)
    display_metrics = _display_baseline_metrics(
        latest.record_date,
        total_placed,
        total_delivered,
        target_qty,
        average_daily_placement,
    )

    planned_accum = []
    target_line = []
    running_plan = Decimal('0')
    for rec in records_list:
        if daily_target:
            running_plan += daily_target
            planned_accum.append(float(running_plan))
        else:
            planned_accum.append(None)
        target_line.append(float(target_qty) if target_qty is not None else None)

    chart_data = json.dumps({
        'labels': [_fmt_short_date(r.record_date) for r in records_list],
        'full_dates': [str(r.record_date) for r in records_list],
        'daily_delivered': [float(r.tct_daily_ton) for r in records_list],
        'daily_placed': [float(r.placed_daily_ton) for r in records_list],
        'daily_target': [float(daily_target) if daily_target is not None else None for _ in records_list],
        'accum_delivered': [float(r.tct_accum_ton) for r in records_list],
        'accum_placed': [float(r.placed_accum_ton) for r in records_list],
        'planned_accum': planned_accum,
        'target_line': target_line,
        'variance': [
            float(r.placed_accum_ton - Decimal(str(planned_accum[idx]))) if planned_accum[idx] is not None else None
            for idx, r in enumerate(records_list)
        ],
    })

    barge_qs = RockBargePlacement.objects.filter(record__project=project)
    if filters.get('barge_id'):
        barge_qs = barge_qs.filter(barge_id=filters['barge_id'])
    if date_from:
        barge_qs = barge_qs.filter(record__record_date__gte=date_from)
    if date_to:
        barge_qs = barge_qs.filter(record__record_date__lte=date_to)
    barge_rows = []
    for row in (
        barge_qs.values('barge__name')
        .annotate(total_qty=Sum('quantity_ton'), total_trips=Sum('trips'), latest_trip_date=Max('record__record_date'))
        .order_by('-total_qty', 'barge__name')
    ):
        total_trips = row['total_trips']
        avg_tons = (row['total_qty'] / total_trips) if total_trips else None
        barge_rows.append({
            'barge__name': row['barge__name'],
            'total_qty': row['total_qty'] or Decimal('0'),
            'total_trips': total_trips,
            'average_tons_per_trip': avg_tons,
            'latest_trip_date': row['latest_trip_date'],
        })

    station_rows = []
    station_qs = RockStationProgress.objects.filter(project=project)
    if filters.get('material_type'):
        station_qs = station_qs.filter(material_type=filters['material_type'])
    if filters.get('station_range'):
        station_qs = station_qs.filter(station_range__icontains=filters['station_range'])
    for station in station_qs:
        station_rows.append({
            'station_range': station.station_range,
            'material_type': station.material_type,
            'delivered_quantity_ton': station.delivered_quantity_ton,
            'placed_quantity_ton': station.placed_quantity_ton,
            'completion_percent': station.completion_percent,
            'status': station.status,
        })

    return {
        'has_data': True,
        'settings': settings,
        'total_delivered': float(total_delivered),
        'total_placed': float(total_placed),
        'available_stock_balance': float(available_stock),
        'stock_balance': float(available_stock),
        'stock_percent': stock_pct,
        'placement_completion_percent': completion_pct,
        'placement_delivery_percent': placement_delivery_pct,
        'placement_delivery_percent_capped': placement_delivery_pct_capped,
        'remaining_quantity_to_boq': float(remaining_qty) if remaining_qty is not None else None,
        'average_daily_placement': float(average_daily_placement) if average_daily_placement is not None else None,
        'forecast_completion_date': forecast_date,
        **display_metrics,
        'latest_daily_delivered': float(latest.tct_daily_ton),
        'latest_daily_placed': float(latest.placed_daily_ton),
        'core_outside_accum': float(latest.core_outside_accum),
        'core_inside_accum': float(latest.core_inside_accum),
        'total_records': len(records_list),
        'record_count': len(records_list),
        'latest_date': latest.record_date,
        'chart_data': chart_data,
        'barge_totals': barge_rows,
        'station_rows': station_rows,
        'material_type_choices': RockDailyRecord.ROCK_MATERIAL_CHOICES,
    }


def get_sand_dashboard_data(project, filters=None):
    filters = filters or {}
    settings = SandDashboardSettings.objects.filter(project=project).first()
    records = SandDailyRecord.objects.filter(project=project).order_by('record_date')

    date_from = filters.get('date_from')
    date_to = filters.get('date_to')
    if date_from:
        records = records.filter(record_date__gte=date_from)
    if date_to:
        records = records.filter(record_date__lte=date_to)

    range_days = filters.get('range_days')
    if range_days and not date_from and not date_to:
        end = records.aggregate(last=Max('record_date'))['last'] or date.today()
        records = records.filter(record_date__gte=end - timedelta(days=range_days - 1))

    if filters.get('source') == 'chalothon':
        records = records.filter(chalothon_daily_ton__gt=0)
    elif filters.get('source') == 'khlong_bang_phai':
        records = records.filter(khlong_bang_phai_daily_ton__gt=0)
    if filters.get('destination') == 'tct':
        records = records.filter(tct_daily_ton__gt=0)
    elif filters.get('destination') == 'mtp3':
        records = records.filter(mtp3_daily_ton__gt=0)
    if filters.get('placement_type') == SandBargePlacement.PLACEMENT_OFFSHORE:
        records = records.filter(offshore_daily_ton__gt=0)
    elif filters.get('placement_type') == SandBargePlacement.PLACEMENT_ONSHORE:
        records = records.filter(onshore_daily_ton__gt=0)
    if filters.get('barge_id'):
        records = records.filter(barge_placements__barge_id=filters['barge_id']).distinct()
    if filters.get('area_zone'):
        records = records.filter(offshore_station__icontains=filters['area_zone'])

    if not records.exists():
        return {
            'chart_data': '{}',
            'barge_totals': [],
            'source_rows': [],
            'area_rows': [],
            'settings': settings,
            'has_data': False,
        }

    latest = records.last()
    agg = records.aggregate(
        delivery_days=Count('pk', filter=Q(total_daily_ton__gt=0)),
        placement_days=Count('pk', filter=Q(offshore_daily_ton__gt=0) | Q(onshore_daily_ton__gt=0)),
        period_delivered=Sum('total_daily_ton'),
        period_offshore=Sum('offshore_daily_ton'),
        period_onshore=Sum('onshore_daily_ton'),
    )
    delivery_days = agg['delivery_days'] or 0
    placement_days = agg['placement_days'] or 0
    period_delivered = agg['period_delivered'] or Decimal('0')
    period_placed = (agg['period_offshore'] or Decimal('0')) + (agg['period_onshore'] or Decimal('0'))
    records_list = list(records)
    total_delivered = latest.total_accum_ton
    total_placed = latest.total_placed
    # Prefer the recorded stock balance when entered; otherwise derive a safe balance
    # from delivered minus placed so imported/older rows still produce useful KPIs.
    recorded_stock_balance = latest.total_remaining  # remaining_tct + remaining_mtp3
    calculated_stock_balance = total_delivered - total_placed
    current_stock_balance = recorded_stock_balance if recorded_stock_balance > 0 else max(calculated_stock_balance, Decimal('0'))
    target_qty = settings.target_quantity_ton if settings else None
    daily_target_delivery = settings.daily_target_delivery_ton if settings else None
    daily_target_placement = settings.daily_target_placement_ton if settings else None
    remaining_qty = (target_qty - total_placed) if target_qty is not None else None
    if remaining_qty is not None and remaining_qty < 0:
        remaining_qty = Decimal('0')
    completion_pct = _safe_pct(total_placed, target_qty)
    remaining_pct = _safe_pct(remaining_qty, target_qty) if remaining_qty is not None else None
    stock_pct = _safe_pct(current_stock_balance, total_delivered)
    placement_delivery_pct = _safe_pct(total_placed, total_delivered)
    placement_delivery_pct_capped = min(max(placement_delivery_pct or 0, 0), 100)
    average_daily_delivery = (period_delivered / delivery_days) if delivery_days else None
    average_daily_placement = (period_placed / placement_days) if placement_days else None
    forecast_date = _forecast_completion_date(latest.record_date, remaining_qty, average_daily_placement)
    display_metrics = _display_baseline_metrics(
        latest.record_date,
        total_placed,
        total_delivered,
        target_qty,
        average_daily_placement,
    )

    planned_delivery = []
    planned_placement = []
    target_line = []
    delivery_plan = placement_plan = Decimal('0')
    placement_view = filters.get('placement_view') or 'daily'
    for rec in records_list:
        if daily_target_delivery:
            delivery_plan += daily_target_delivery
            planned_delivery.append(float(delivery_plan))
        else:
            planned_delivery.append(None)
        if daily_target_placement:
            placement_plan += daily_target_placement
            planned_placement.append(float(placement_plan))
        else:
            planned_placement.append(None)
        target_line.append(float(target_qty) if target_qty is not None else None)

    accum_placed = [float(rec.total_placed) for rec in records_list]
    chart_data = {
        'labels': [_fmt_short_date(rec.record_date) for rec in records_list],
        'full_dates': [str(rec.record_date) for rec in records_list],
        'tct_daily': [float(rec.tct_daily_ton) for rec in records_list],
        'mtp3_daily': [float(rec.mtp3_daily_ton) for rec in records_list],
        'daily_target_delivery': [float(daily_target_delivery) if daily_target_delivery is not None else None for _ in records_list],
        'chalothon_daily': [float(rec.chalothon_daily_ton) for rec in records_list],
        'khlong_bang_phai_daily': [float(rec.khlong_bang_phai_daily_ton) for rec in records_list],
        'other_daily': [float(rec.oswald_daily_ton) for rec in records_list],
        'actual_cumulative_delivery': [float(rec.total_accum_ton) for rec in records_list],
        'actual_cumulative_placement': accum_placed,
        'planned_cumulative_delivery': planned_delivery,
        'planned_cumulative_placement': planned_placement,
        'target_line': target_line,
        'variance': [
            float(Decimal(str(accum_placed[idx])) - Decimal(str(planned_placement[idx]))) if planned_placement[idx] is not None else None
            for idx in range(len(records_list))
        ],
        'offshore_placement': [
            float(rec.offshore_accum_ton if placement_view == 'cumulative' else rec.offshore_daily_ton)
            for rec in records_list
        ],
        'onshore_placement': [
            float(rec.onshore_accum_ton if placement_view == 'cumulative' else rec.onshore_daily_ton)
            for rec in records_list
        ],
    }

    source_rows = [
        {
            'name': 'Chalothon Sand Pit',
            'total_qty': latest.chalothon_accum_ton,
            'percent': _safe_pct(latest.chalothon_accum_ton, latest.total_source_accum_ton),
            'latest_date': records.filter(chalothon_daily_ton__gt=0).aggregate(last=Max('record_date'))['last'],
            'status': 'Active' if latest.chalothon_accum_ton > 0 else 'No Delivery',
        },
        {
            'name': 'Khlong Bang Phai (Oswald)',
            'total_qty': latest.khlong_bang_phai_accum_ton,
            'percent': _safe_pct(latest.khlong_bang_phai_accum_ton, latest.total_source_accum_ton),
            'latest_date': records.filter(khlong_bang_phai_daily_ton__gt=0).aggregate(last=Max('record_date'))['last'],
            'status': 'Active' if latest.khlong_bang_phai_accum_ton > 0 else 'No Delivery',
        },
    ]
    source_rows.sort(key=lambda row: row['total_qty'], reverse=True)

    barge_qs = SandBargePlacement.objects.filter(record__project=project)
    if date_from:
        barge_qs = barge_qs.filter(record__record_date__gte=date_from)
    if date_to:
        barge_qs = barge_qs.filter(record__record_date__lte=date_to)
    if filters.get('barge_id'):
        barge_qs = barge_qs.filter(barge_id=filters['barge_id'])
    if filters.get('source'):
        source_name = 'Chalothon Sand Pit' if filters['source'] == 'chalothon' else 'Khlong Bang Phai (Oswald)'
        barge_qs = barge_qs.filter(source__icontains=source_name)
    if filters.get('destination'):
        destination_name = 'TCT Pier' if filters['destination'] == 'tct' else 'Stockpile Sand MTP3'
        barge_qs = barge_qs.filter(destination__icontains=destination_name)
    if filters.get('placement_type'):
        barge_qs = barge_qs.filter(placement_type=filters['placement_type'])

    barge_rows = []
    for row in (
        barge_qs.values('barge__name', 'source', 'destination', 'placement_type', 'material_type', 'status')
        .annotate(total_qty=Sum('quantity_ton'), total_trips=Sum('trips'), latest_trip_date=Max('record__record_date'))
        .order_by('-total_qty', 'barge__name')
    ):
        total_trips = row['total_trips']
        avg_tons = (row['total_qty'] / total_trips) if total_trips else None
        barge_rows.append({
            'barge__name': row['barge__name'],
            'total_qty': row['total_qty'] or Decimal('0'),
            'total_trips': total_trips,
            'average_tons_per_trip': avg_tons,
            'latest_trip_date': row['latest_trip_date'],
            'source': row['source'] or 'Not specified',
            'destination': row['destination'] or 'Offshore Placement',
            'placement_type': row['placement_type'] or 'Not specified',
            'material_type': row['material_type'] or 'Sand',
            'status': SandBargePlacement.STATUS_MISSING_TRIPS if total_trips is None else row['status'],
        })

    area_qs = SandAreaProgress.objects.filter(project=project)
    if filters.get('area_zone'):
        area_qs = area_qs.filter(area_zone__icontains=filters['area_zone'])
    if filters.get('placement_type'):
        area_qs = area_qs.filter(placement_type=filters['placement_type'])
    area_rows = []
    for area in area_qs:
        area_rows.append({
            'area_zone': area.area_zone,
            'planned_quantity_ton': area.planned_quantity_ton,
            'delivered_quantity_ton': area.delivered_quantity_ton,
            'placed_quantity_ton': area.placed_quantity_ton,
            'remaining_quantity_ton': area.remaining_quantity_ton,
            'completion_percent': area.completion_percent,
            'placement_type': area.placement_type or 'All',
            'status': area.status,
        })

    return {
        'has_data': True,
        'settings': settings,
        'tct_accum': float(latest.tct_accum_ton),
        'mtp3_accum': float(latest.mtp3_accum_ton),
        'chalothon_accum': float(latest.chalothon_accum_ton),
        'khlong_bang_phai_accum': float(latest.khlong_bang_phai_accum_ton),
        'other_source_label': 'Khlong Bang Phai (Oswald)',
        'other_source_names': 'Khlong Bang Phai (Oswald)',
        'other_source_accum': float(latest.oswald_accum_ton),
        'total_source_accum': float(latest.total_source_accum_ton),
        'total_accum': float(latest.total_accum_ton),
        'offshore_accum': float(latest.offshore_accum_ton),
        'onshore_accum': float(latest.onshore_accum_ton),
        'barge_totals': barge_rows,
        'source_rows': source_rows,
        'area_rows': area_rows,
        'total_tct': float(latest.tct_accum_ton),
        'total_mtp3': float(latest.mtp3_accum_ton),
        'total_chalothon': float(latest.chalothon_accum_ton),
        'total_khlong_bang_phai': float(latest.khlong_bang_phai_accum_ton),
        'total_oswald': float(latest.oswald_accum_ton),
        'total_delivered': float(total_delivered),
        'total_placed': float(total_placed),
        'current_stock_balance': float(current_stock_balance),
        'total_offshore': float(latest.offshore_accum_ton),
        'total_onshore': float(latest.onshore_accum_ton),
        'inside_plot': float(latest.inside_plot_accum),
        'outside_plot': float(latest.outside_plot_accum),
        'remaining_tct': float(latest.remaining_tct),
        'remaining_mtp3': float(latest.remaining_mtp3),
        'total_remaining': float(current_stock_balance),
        'remaining_quantity': float(remaining_qty) if remaining_qty is not None else None,
        'remaining_percent': remaining_pct,
        'completion_percent': completion_pct,
        'stock_percent': stock_pct,
        'placement_delivery_percent': placement_delivery_pct,
        'placement_delivery_percent_capped': placement_delivery_pct_capped,
        'average_daily_delivery': float(average_daily_delivery) if average_daily_delivery is not None else None,
        'average_daily_placement': float(average_daily_placement) if average_daily_placement is not None else None,
        'forecast_completion_date': forecast_date,
        **display_metrics,
        'latest_daily_delivered': float(latest.total_daily_ton),
        'latest_daily_placed': float(latest.offshore_daily_ton + latest.onshore_daily_ton),
        'latest_date': latest.record_date,
        'record_count': len(records_list),
        'placement_chart_title': 'Cumulative Sand Placement: Offshore vs Onshore' if placement_view == 'cumulative' else 'Daily Sand Placement: Offshore vs Onshore',
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
