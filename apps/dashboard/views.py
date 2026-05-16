import json
from datetime import date, datetime, timedelta
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum, Count, F, ExpressionWrapper, DecimalField, Subquery, OuterRef, Q
from django.http import JsonResponse
from django.views.generic import TemplateView, View

from apps.projects.models import Project
from apps.daily_reports.models import DailyReport
from apps.manpower.models import DailyManpowerRecord
from apps.equipment.models import DailyEquipmentRecord
from apps.materials.models import MaterialDelivery
from apps.safety.models import SafetyInspection, IncidentReport, ToolboxMeeting
from apps.boq.models import BOQItem, DailyProgressRecord
from apps.quality.services import get_quality_dashboard_tables, get_quality_metrics
from apps.project_controls.models import ProjectActionPlan


# ─────────────────────────────────────────────────────────
#  Helpers (keep heavy math out of templates)
# ─────────────────────────────────────────────────────────

def _planned_pct(project, as_of):
    """Linear planned progress for a project on a given date."""
    total = max((project.finish_date - project.start_date).days, 1)
    elapsed = max((as_of - project.start_date).days, 0)
    return min(elapsed / total * 100, 100)


def _project_boq_stats(project):
    """Return contract_amount and earned_value for a project (avoids N+1)."""
    items = list(BOQItem.objects.filter(project=project))
    if not items:
        return 0.0, 0.0
    total_contract = sum(float(i.contract_amount) for i in items)
    total_earned = sum(float(i.earned_value) for i in items)
    return total_contract, total_earned


def _evm_metrics(today, boq_progress):
    """
    Weighted-average EVM metrics across all projects that have BOQ data.
    boq_progress is the list of dicts already built in DashboardView.
    """
    if not boq_progress:
        return dict(planned_pct=0, actual_pct=0, variance=0,
                    spi=0, status='No Data', status_class='no-data')

    total_w = sum(r['contract_amount'] for r in boq_progress)
    if total_w == 0:
        return dict(planned_pct=0, actual_pct=0, variance=0,
                    spi=0, status='No Data', status_class='no-data')

    w_planned = sum(_planned_pct(r['project'], today) * r['contract_amount']
                    for r in boq_progress)
    w_actual = sum(r['percent'] * r['contract_amount'] for r in boq_progress)

    planned = w_planned / total_w
    actual = w_actual / total_w
    variance = actual - planned
    spi = actual / planned if planned else 0

    if spi >= 0.95:
        status, cls = 'On Track', 'on-track'
    elif spi >= 0.80:
        status, cls = 'Slight Delay', 'warning'
    else:
        status, cls = 'Critical Delay', 'critical'

    return dict(planned_pct=round(planned, 1), actual_pct=round(actual, 1),
                variance=round(variance, 1), spi=round(spi, 2),
                status=status, status_class=cls)


def _safety_metrics(active_projects):
    """Aggregate safety KPIs across all active projects."""
    qs_filter = Q(project__in=active_projects)

    # Man-hours: total manpower-days × 10 h (construction shift)
    mp_days = (DailyManpowerRecord.objects
               .filter(project__in=active_projects)
               .aggregate(t=Sum('quantity'))['t'] or 0)
    man_hours = int(mp_days * 10)

    incidents = IncidentReport.objects.filter(qs_filter)
    lti = incidents.filter(type__in=['LostTime', 'Fatal']).count()
    near_miss = incidents.filter(type='NearMiss').count()
    incident_count = incidents.exclude(type='NearMiss').count()

    inspections = SafetyInspection.objects.filter(qs_filter)
    insp_open = inspections.filter(status='Open').count()
    insp_in_progress = inspections.filter(status='InProgress').count()
    insp_closed = inspections.filter(status='Closed').count()
    insp_total = inspections.count()

    toolbox_count = ToolboxMeeting.objects.filter(qs_filter).count()

    return dict(
        man_hours=man_hours,
        lti=lti,
        incidents=incident_count,
        near_miss=near_miss,
        open_issues=insp_open,
        insp_submitted=insp_total,
        insp_approved=insp_closed,
        insp_in_progress=insp_in_progress,
        toolbox_meetings=toolbox_count,
    )


def _production_forecast(today, boq_progress, active_projects):
    """Compute average daily production, required rate, gap, forecast date."""
    if not boq_progress or not active_projects:
        return None

    total_contract = sum(r['contract_amount'] for r in boq_progress)
    total_earned = sum(r['earned_value'] for r in boq_progress)
    total_remaining = total_contract - total_earned

    # Count distinct working days with any progress
    working_days = (DailyProgressRecord.objects
                    .filter(project__in=active_projects)
                    .values('record_date').distinct().count())

    # Average daily EV progress (% per working day)
    if working_days > 0 and total_contract > 0:
        avg_daily_pct = (total_earned / total_contract * 100) / working_days
    else:
        avg_daily_pct = 0.0

    # Latest finish date across active projects
    finish_dates = [p.finish_date for p in active_projects]
    latest_finish = max(finish_dates) if finish_dates else today
    days_remaining = (latest_finish - today).days
    remaining_pct = (total_remaining / total_contract * 100) if total_contract else 0
    # If already overdue, required rate is undefined — use 0 to avoid division by ≤0
    required_daily_pct = remaining_pct / days_remaining if days_remaining > 0 else 0

    gap = required_daily_pct - avg_daily_pct

    if avg_daily_pct > 0 and total_contract > 0:
        days_needed = remaining_pct / avg_daily_pct
        forecast_date = today + timedelta(days=int(days_needed))
    else:
        forecast_date = None

    is_overdue = days_remaining <= 0

    return dict(
        avg_daily_pct=round(avg_daily_pct, 3),
        required_daily_pct=round(required_daily_pct, 3),
        gap=round(gap, 3),
        forecast_date=forecast_date,
        working_days=working_days,
        is_on_track=gap <= 0 and not is_overdue,
        is_overdue=is_overdue,
        days_overdue=abs(days_remaining) if is_overdue else 0,
        days_remaining=days_remaining,
        latest_finish=latest_finish,
    )


def _quantity_balance(active_projects):
    """
    Return a list of dicts with completed/remaining quantities per BOQ item.
    Uses a subquery to avoid N+1.
    """
    cum_subquery = (DailyProgressRecord.objects
                    .filter(boq_item=OuterRef('pk'))
                    .values('boq_item')
                    .annotate(total=Sum('daily_quantity'))
                    .values('total'))

    items = (BOQItem.objects
             .filter(project__in=active_projects)
             .select_related('project')
             .annotate(completed_qty=Subquery(cum_subquery, output_field=DecimalField()))
             .order_by('project__project_name', 'item_no'))

    result = []
    for item in items:
        completed = float(item.completed_qty or 0)
        contract = float(item.contract_quantity)
        remaining = max(contract - completed, 0)
        pct = round(completed / contract * 100, 1) if contract else 0.0
        result.append(dict(
            project_name=item.project.project_name,
            item_no=item.item_no,
            description=item.description,
            unit=item.unit,
            contract_qty=contract,
            completed_qty=completed,
            remaining_qty=remaining,
            percent=pct,
        ))
    return result


# ─────────────────────────────────────────────────────────
#  Main Dashboard View
# ─────────────────────────────────────────────────────────

def _safe_float(value):
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _percent(numerator, denominator):
    numerator = _safe_float(numerator)
    denominator = _safe_float(denominator)
    return round((numerator / denominator * 100), 1) if denominator else 0.0


def _latest_date(*dates):
    valid_dates = [value for value in dates if value]
    return max(valid_dates) if valid_dates else None


def _project_controls_summary(active_projects):
    """Aggregate project-control operational data for the executive page."""
    try:
        from apps.project_controls.services import (
            get_rap_dashboard_data,
            get_revetment_dashboard_data,
            get_rock_dashboard_data,
            get_sand_dashboard_data,
        )
    except Exception:
        return {'available': False, 'rows': [], 'latest_date': None}

    summary = {
        'available': True,
        'project_count': len(active_projects),
        'rock_delivered': 0.0,
        'rock_placed': 0.0,
        'rock_stock': 0.0,
        'rock_avg_daily': 0.0,
        'rock_forecast_date': None,
        'sand_delivered': 0.0,
        'sand_placed': 0.0,
        'sand_remaining': 0.0,
        'sand_avg_daily': 0.0,
        'sand_forecast_date': None,
        'revetment_quantity': 0.0,
        'revetment_records': 0,
        'rap_total_items': 0,
        'rap_delayed_items': 0,
        'rap_planned': 0.0,
        'rap_actual': 0.0,
        'stock_alerts': 0,
        'latest_date': None,
        'rows': [],
    }

    for project in active_projects:
        rock = get_rock_dashboard_data(project)
        sand = get_sand_dashboard_data(project)
        revetment = get_revetment_dashboard_data(project)
        rap = get_rap_dashboard_data(project)

        rock_delivered = _safe_float(rock.get('total_delivered'))
        rock_placed = _safe_float(rock.get('total_placed'))
        sand_delivered = _safe_float(sand.get('total_delivered'))
        sand_placed = _safe_float(sand.get('total_placed'))

        summary['rock_delivered'] += rock_delivered
        summary['rock_placed'] += rock_placed
        summary['rock_stock'] += _safe_float(rock.get('stock_balance'))
        summary['rock_avg_daily'] += _safe_float(rock.get('average_daily_placement'))
        summary['sand_delivered'] += sand_delivered
        summary['sand_placed'] += sand_placed
        summary['sand_remaining'] += _safe_float(sand.get('total_remaining'))
        summary['sand_avg_daily'] += _safe_float(sand.get('average_daily_placement'))
        summary['revetment_quantity'] += _safe_float(revetment.get('total_quantity'))
        summary['revetment_records'] += int(revetment.get('record_count') or 0)
        summary['rap_total_items'] += int(rap.get('total_items') or 0)
        summary['rap_delayed_items'] += int(rap.get('delayed_items') or 0)
        summary['rap_planned'] += _safe_float(rap.get('total_planned'))
        summary['rap_actual'] += _safe_float(rap.get('total_actual'))
        summary['latest_date'] = _latest_date(
            summary['latest_date'],
            rock.get('latest_date'),
            sand.get('latest_date'),
            revetment.get('latest_date'),
        )
        summary['rock_forecast_date'] = _latest_date(
            summary['rock_forecast_date'],
            rock.get('forecast_completion_date'),
        )
        summary['sand_forecast_date'] = _latest_date(
            summary['sand_forecast_date'],
            sand.get('forecast_completion_date'),
        )

        if _safe_float(rock.get('stock_balance')) < 0 or _safe_float(sand.get('total_remaining')) < 0:
            summary['stock_alerts'] += 1

        summary['rows'].append({
            'project': project,
            'rock_pct': _percent(rock_placed, rock_delivered),
            'sand_pct': _percent(sand_placed, sand_delivered),
            'rap_delayed': int(rap.get('delayed_items') or 0),
            'rap_total': int(rap.get('total_items') or 0),
            'stock_alert': _safe_float(rock.get('stock_balance')) < 0 or _safe_float(sand.get('total_remaining')) < 0,
        })

    summary['rock_pct'] = _percent(summary['rock_placed'], summary['rock_delivered'])
    summary['rock_pct_capped'] = min(summary['rock_pct'], 100)
    summary['sand_pct'] = _percent(summary['sand_placed'], summary['sand_delivered'])
    summary['sand_pct_capped'] = min(summary['sand_pct'], 100)
    summary['rap_pct'] = _percent(summary['rap_actual'], summary['rap_planned'])
    summary['rap_pct_capped'] = min(summary['rap_pct'], 100)
    summary['rows'] = summary['rows'][:6]
    return summary


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/index.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        today = date.today()

        # ── Projects ──────────────────────────────────────
        ctx['projects'] = Project.objects.all().order_by('project_name')
        ctx['active_projects'] = list(Project.objects.filter(status='Active'))
        ctx['active_projects_count'] = len(ctx['active_projects'])

        # ── Today's site snapshot ─────────────────────────
        ctx['today_manpower'] = (DailyManpowerRecord.objects
                                 .filter(report_date=today)
                                 .aggregate(total=Sum('quantity'))['total'] or 0)

        ctx['today_equipment'] = (DailyEquipmentRecord.objects
                                  .filter(report_date=today, status='Working').count())

        ctx['pending_reports'] = DailyReport.objects.filter(status='Submitted').count()
        ctx['open_safety_issues'] = SafetyInspection.objects.filter(status='Open').count()

        ctx['latest_reports'] = (DailyReport.objects
                                 .select_related('project', 'prepared_by')
                                 .order_by('-report_date')[:8])

        # ── Material deliveries (last 7 days) ─────────────
        week_ago = today - timedelta(days=7)
        ctx['recent_deliveries'] = (MaterialDelivery.objects
                                    .select_related('project', 'material')
                                    .filter(delivery_date__gte=week_ago)
                                    .order_by('-delivery_date')[:10])

        stone_qs = MaterialDelivery.objects.filter(
            delivery_date__gte=week_ago, material__category__name='Rock')
        sand_qs = MaterialDelivery.objects.filter(
            delivery_date__gte=week_ago, material__category__name='Aggregate')

        ctx['stone_by_source'] = (stone_qs
                                  .values('source', 'material__name', 'material__unit')
                                  .annotate(total=Sum('quantity'))
                                  .order_by('source', 'material__name'))
        ctx['sand_by_source'] = (sand_qs
                                 .values('source', 'material__name', 'material__unit')
                                 .annotate(total=Sum('quantity'))
                                 .order_by('source', 'material__name'))
        ctx['stone_total_week'] = stone_qs.aggregate(t=Sum('quantity'))['t'] or 0
        ctx['sand_total_week'] = sand_qs.aggregate(t=Sum('quantity'))['t'] or 0

        # ── BOQ progress per project ──────────────────────
        project_overview = []
        boq_progress = []
        donut_data = []

        for project in ctx['projects']:
            total_contract, total_earned = _project_boq_stats(project)
            pct = (total_earned / total_contract * 100) if total_contract else 0.0

            days_total = max((project.finish_date - project.start_date).days, 1)
            days_elapsed = max((today - project.start_date).days, 0)
            days_remaining = (project.finish_date - today).days
            schedule_pct = min(days_elapsed / days_total * 100, 100)

            if days_remaining < 0:
                sched_status = 'overdue'
            elif days_remaining < 30:
                sched_status = 'critical'
            elif days_remaining < 90:
                sched_status = 'warning'
            else:
                sched_status = 'on-track'

            row = dict(
                project=project,
                percent=round(float(pct), 1),
                earned_value=float(total_earned),
                contract_amount=float(total_contract),
                days_remaining=days_remaining,
                days_overdue=abs(days_remaining) if days_remaining < 0 else 0,
                schedule_pct=round(float(schedule_pct), 1),
                schedule_status=sched_status,
            )
            if total_contract:
                boq_progress.append(row)
                donut_data.append(dict(
                    name=project.project_name,
                    contract_no=project.contract_no,
                    percent=round(float(pct), 1),
                    status=project.status,
                ))
            project_overview.append({
                **row,
                'report_count': DailyReport.objects.filter(project=project).count(),
                'delivery_count': MaterialDelivery.objects.filter(project=project).count(),
                'latest_report': DailyReport.objects.filter(project=project).order_by('-report_date').first(),
            })

        ctx['boq_progress'] = boq_progress
        ctx['project_overview'] = project_overview
        ctx['donut_data_json'] = json.dumps(donut_data)
        ctx['boq_projects'] = [r['project'] for r in boq_progress]
        ctx['default_scurve_project_id'] = boq_progress[0]['project'].pk if boq_progress else ''

        # ── Executive summary totals ──────────────────────
        total_contract_value = float(
            Project.objects.filter(status='Active').aggregate(t=Sum('contract_value'))['t'] or 0
        )
        total_earned_value = sum(r['earned_value'] for r in boq_progress)
        overall_progress_pct = round(
            (total_earned_value / total_contract_value * 100) if total_contract_value else 0, 1
        )
        ctx['total_contract_value'] = total_contract_value
        ctx['total_earned_value'] = total_earned_value
        ctx['total_remaining_value'] = max(total_contract_value - total_earned_value, 0)
        ctx['overall_progress_pct'] = overall_progress_pct
        ctx['owner_attention_count'] = ctx['pending_reports'] + ctx['open_safety_issues']
        ctx['today'] = today

        # ── EVM metrics (Planned vs Actual) ───────────────
        ctx['evm'] = _evm_metrics(today, boq_progress)

        # ── Safety & quality scorecard ────────────────────
        ctx['quality_metrics'] = get_quality_metrics(ctx['active_projects'])
        ctx['quality_tables'] = get_quality_dashboard_tables(ctx['active_projects'], today=today)
        ctx['safety_metrics'] = _safety_metrics(ctx['active_projects'])

        # ── Production forecast ───────────────────────────
        ctx['forecast'] = _production_forecast(today, boq_progress, ctx['active_projects'])

        # ── Quantity balance table ────────────────────────
        ctx['quantity_balance'] = _quantity_balance(ctx['active_projects'])
        ctx['project_controls_summary'] = _project_controls_summary(ctx['active_projects'])

        # ── Owner decisions (from Project Action Plans) ───
        ctx['owner_decisions'] = (ProjectActionPlan.objects
                                  .select_related('project')
                                  .filter(
                                      project__in=ctx['active_projects'],
                                      status__in=[
                                          ProjectActionPlan.STATUS_OPEN,
                                          ProjectActionPlan.STATUS_IN_PROGRESS,
                                          ProjectActionPlan.STATUS_PENDING,
                                      ],
                                  )
                                  .order_by('due_date'))

        return ctx


# ─────────────────────────────────────────────────────────
#  Chart data (manpower + material – existing logic)
# ─────────────────────────────────────────────────────────

class DashboardChartDataView(LoginRequiredMixin, View):
    def get(self, request):
        project_id = request.GET.get('project_id')
        today = date.today()
        range_key = request.GET.get('range', '30')
        date_from = request.GET.get('date_from')
        date_to = request.GET.get('date_to')

        if range_key == 'custom' and date_from and date_to:
            try:
                start = datetime.strptime(date_from, '%Y-%m-%d').date()
                end = datetime.strptime(date_to, '%Y-%m-%d').date()
            except ValueError:
                start = today - timedelta(days=29)
                end = today
        else:
            days = 7 if range_key == '7' else 30
            start = today - timedelta(days=days - 1)
            end = today

        if start > end:
            start, end = end, start
        if (end - start).days > 365:
            start = end - timedelta(days=365)

        labels = [(start + timedelta(days=i)).isoformat()
                  for i in range((end - start).days + 1)]

        mp_qs = DailyManpowerRecord.objects.filter(report_date__range=[start, end])
        if project_id:
            mp_qs = mp_qs.filter(project_id=project_id)
        mp_map = {str(r['report_date']): r['total']
                  for r in mp_qs.values('report_date').annotate(total=Sum('quantity'))}
        manpower = [mp_map.get(d, 0) for d in labels]

        stone_qs = MaterialDelivery.objects.filter(
            delivery_date__range=[start, end], material__category__name='Rock')
        sand_qs = MaterialDelivery.objects.filter(
            delivery_date__range=[start, end], material__category__name='Aggregate')
        if project_id:
            stone_qs = stone_qs.filter(project_id=project_id)
            sand_qs = sand_qs.filter(project_id=project_id)

        stone_map = {str(r['delivery_date']): float(r['total'])
                     for r in stone_qs.values('delivery_date').annotate(total=Sum('quantity'))}
        sand_map = {str(r['delivery_date']): float(r['total'])
                    for r in sand_qs.values('delivery_date').annotate(total=Sum('quantity'))}
        stone_data = [stone_map.get(d, 0) for d in labels]
        sand_data = [sand_map.get(d, 0) for d in labels]

        return JsonResponse({
            'labels': labels,
            'manpower_histogram': manpower,
            'stone_delivery_chart': stone_data,
            'sand_delivery_chart': sand_data,
            'date_from': start.isoformat(),
            'date_to': end.isoformat(),
            'days': len(labels),
        })


# ─────────────────────────────────────────────────────────
#  S-Curve data (new endpoint)
# ─────────────────────────────────────────────────────────

class SCurveDataView(LoginRequiredMixin, View):
    """
    Returns weekly Planned / Actual / Forecast progress series for a project.
    GET params: project_id (required)
    """
    def get(self, request):
        project_id = request.GET.get('project_id')
        today = date.today()

        if project_id:
            project = Project.objects.filter(pk=project_id).first()
        else:
            project = Project.objects.filter(status='Active').order_by('project_name').first()

        if not project:
            return JsonResponse({'labels': [], 'planned': [], 'actual': [], 'forecast': [],
                                 'project_name': ''})

        start = project.start_date
        contract_end = project.finish_date

        # Build weekly tick dates from project start to max(today, contract_end)
        timeline_end = max(contract_end, today)
        ticks = []
        d = start
        while d <= timeline_end:
            ticks.append(d)
            d += timedelta(days=7)
        if not ticks or ticks[-1] < timeline_end:
            ticks.append(timeline_end)

        # Contract value (BAC)
        items = list(BOQItem.objects.filter(project=project))
        bac = sum(float(i.contract_amount) for i in items)
        if not bac:
            return JsonResponse({'labels': [t.isoformat() for t in ticks],
                                 'planned': [], 'actual': [], 'forecast': [],
                                 'project_name': project.project_name})

        # Build daily EV map from progress records (single query)
        daily_ev_rows = (DailyProgressRecord.objects
                         .filter(project=project)
                         .values('record_date', 'boq_item__unit_rate', 'daily_quantity'))
        daily_ev: dict[str, float] = {}
        for r in daily_ev_rows:
            key = r['record_date'].isoformat()
            daily_ev[key] = daily_ev.get(key, 0) + float(r['daily_quantity']) * float(r['boq_item__unit_rate'])

        sorted_dates = sorted(daily_ev)
        total_days = max((contract_end - start).days, 1)

        # Cumulative EV at each tick (walk through sorted dates once)
        cum_ev = 0.0
        date_idx = 0
        cum_at_tick: dict[str, float] = {}
        for tick in ticks:
            tick_str = tick.isoformat()
            while date_idx < len(sorted_dates) and sorted_dates[date_idx] <= tick_str:
                cum_ev += daily_ev[sorted_dates[date_idx]]
                date_idx += 1
            cum_at_tick[tick_str] = cum_ev

        # Today's actual % and daily rate for forecast
        today_actual_pct = min((cum_at_tick.get(
            max((t for t in cum_at_tick if t <= today.isoformat()), default=start.isoformat()),
            0) / bac * 100), 100)
        today_planned_pct = _planned_pct(project, today)
        elapsed_days = max((today - start).days, 1)
        daily_rate = today_actual_pct / elapsed_days  # % per calendar day

        labels, planned, actual, forecast = [], [], [], []
        for tick in ticks:
            tick_str = tick.isoformat()
            labels.append(tick_str)

            # Planned (linear)
            elapsed = (tick - start).days
            planned.append(round(min(elapsed / total_days * 100, 100), 1))

            if tick <= today:
                ev = cum_at_tick.get(tick_str, 0)
                actual.append(round(min(ev / bac * 100, 100), 1))
                forecast.append(None)
            else:
                actual.append(None)
                days_ahead = (tick - today).days
                fc = min(today_actual_pct + daily_rate * days_ahead, 100)
                forecast.append(round(fc, 1))

        return JsonResponse({
            'labels': labels,
            'planned': planned,
            'actual': actual,
            'forecast': forecast,
            'project_name': project.project_name,
            'contract_no': project.contract_no,
            'planned_today': round(today_planned_pct, 1),
            'actual_today': round(today_actual_pct, 1),
            'spi': round(today_actual_pct / today_planned_pct, 2) if today_planned_pct else 0,
        })
