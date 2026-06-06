"""
Cost Control service functions.
All financial calculations live here — templates and views stay thin.
"""
import json
from decimal import Decimal
from django.db.models import Sum


def calculate_cpi(earned_value, actual_cost):
    """Return CPI as Decimal or None if actual_cost is zero (safe division)."""
    try:
        ac = Decimal(str(actual_cost))
        ev = Decimal(str(earned_value))
        if ac == 0:
            return None
        return (ev / ac).quantize(Decimal('0.01'))
    except (TypeError, ValueError, ZeroDivisionError):
        return None


def calculate_cost_variance(earned_value, actual_cost):
    """EV – AC."""
    return Decimal(str(earned_value)) - Decimal(str(actual_cost))


def calculate_eac(total_budget, cpi):
    """BAC / CPI. Returns None if CPI is None or zero."""
    if cpi is None:
        return None
    try:
        c = Decimal(str(cpi))
        if c == 0:
            return None
        return (Decimal(str(total_budget)) / c).quantize(Decimal('0.01'))
    except (TypeError, ValueError, ZeroDivisionError):
        return None


def _cost_status(cpi):
    """Derive status label and CSS class from CPI value."""
    if cpi is None:
        return 'N/A', 'no-data'
    if cpi >= Decimal('1.00'):
        return 'Good', 'good'
    if cpi >= Decimal('0.90'):
        return 'Warning', 'warning'
    return 'Critical', 'critical'


def _boq_percent(project):
    """Return overall BOQ completion % (0–100 Decimal) for a project."""
    from apps.boq.models import BOQItem, DailyProgressRecord

    items = list(BOQItem.objects.filter(project=project, item_type='item'))
    if not items:
        return Decimal('0')
    total_contract = sum(i.contract_quantity * i.unit_rate for i in items)
    if total_contract == 0:
        return Decimal('0')
    total_earned = sum(
        (DailyProgressRecord.objects
         .filter(boq_item=item)
         .aggregate(q=Sum('daily_quantity'))['q'] or Decimal('0'))
        * item.unit_rate
        for item in items
    )
    return min(total_earned / total_contract * 100, Decimal('100'))


def get_cost_summary(project):
    """
    All cost metrics for one project.
    Always returns a dict — never raises even when there is no data.
    """
    from .models import BudgetItem, ActualCost

    total_budget = (
        BudgetItem.objects.filter(project=project)
        .aggregate(t=Sum('budget_amount'))['t'] or Decimal('0')
    )
    committed = (
        BudgetItem.objects.filter(project=project)
        .aggregate(t=Sum('committed_amount'))['t'] or Decimal('0')
    )
    actual_cost = (
        ActualCost.objects.filter(project=project)
        .aggregate(t=Sum('amount'))['t'] or Decimal('0')
    )

    boq_pct = _boq_percent(project)
    earned_value = (total_budget * boq_pct / Decimal('100')).quantize(Decimal('0.01'))

    cpi = calculate_cpi(earned_value, actual_cost)
    cost_variance = calculate_cost_variance(earned_value, actual_cost)
    eac = calculate_eac(total_budget, cpi)
    status, status_class = _cost_status(cpi)

    return dict(
        total_budget=float(total_budget),
        committed=float(committed),
        actual_cost=float(actual_cost),
        earned_value=float(earned_value),
        boq_pct=float(boq_pct),
        cost_variance=float(cost_variance),
        cpi=float(cpi) if cpi is not None else None,
        eac=float(eac) if eac is not None else None,
        cost_status=status,
        cost_status_class=status_class,
    )


def get_all_projects_cost_summary(projects):
    """Aggregate cost metrics across a list/queryset of projects."""
    from .models import BudgetItem, ActualCost

    projects = list(projects)

    total_budget = (
        BudgetItem.objects.filter(project__in=projects)
        .aggregate(t=Sum('budget_amount'))['t'] or Decimal('0')
    )
    committed = (
        BudgetItem.objects.filter(project__in=projects)
        .aggregate(t=Sum('committed_amount'))['t'] or Decimal('0')
    )
    actual_cost = (
        ActualCost.objects.filter(project__in=projects)
        .aggregate(t=Sum('amount'))['t'] or Decimal('0')
    )

    earned_value = Decimal('0')
    for p in projects:
        pct = _boq_percent(p)
        proj_budget = (
            BudgetItem.objects.filter(project=p)
            .aggregate(t=Sum('budget_amount'))['t'] or Decimal('0')
        )
        earned_value += proj_budget * pct / Decimal('100')
    earned_value = earned_value.quantize(Decimal('0.01'))

    cpi = calculate_cpi(earned_value, actual_cost)
    cost_variance = calculate_cost_variance(earned_value, actual_cost)
    eac = calculate_eac(total_budget, cpi)
    status, status_class = _cost_status(cpi)

    return dict(
        total_budget=float(total_budget),
        committed=float(committed),
        actual_cost=float(actual_cost),
        earned_value=float(earned_value),
        cost_variance=float(cost_variance),
        cpi=float(cpi) if cpi is not None else None,
        eac=float(eac) if eac is not None else None,
        cost_status=status,
        cost_status_class=status_class,
    )


def get_all_projects_cost_summaries(projects):
    """Return per-project cost summary dicts using bulk queries (avoids N+1 on BudgetItem/ActualCost)."""
    from .models import BudgetItem, ActualCost

    projects = list(projects)
    pks = [p.pk for p in projects]

    budget_by_project = {
        row['project_id']: row
        for row in BudgetItem.objects.filter(project_id__in=pks)
            .values('project_id')
            .annotate(total=Sum('budget_amount'), committed=Sum('committed_amount'))
    }
    actual_by_project = {
        row['project_id']: row['total']
        for row in ActualCost.objects.filter(project_id__in=pks)
            .values('project_id')
            .annotate(total=Sum('amount'))
    }

    result = []
    for p in projects:
        b = budget_by_project.get(p.pk, {})
        total_budget = Decimal(str(b.get('total') or 0))
        committed = Decimal(str(b.get('committed') or 0))
        actual_cost = Decimal(str(actual_by_project.get(p.pk) or 0))

        boq_pct = _boq_percent(p)
        earned_value = (total_budget * boq_pct / Decimal('100')).quantize(Decimal('0.01'))

        cpi = calculate_cpi(earned_value, actual_cost)
        cost_variance = calculate_cost_variance(earned_value, actual_cost)
        eac = calculate_eac(total_budget, cpi)
        status, status_class = _cost_status(cpi)

        result.append(dict(
            total_budget=float(total_budget),
            committed=float(committed),
            actual_cost=float(actual_cost),
            earned_value=float(earned_value),
            boq_pct=float(boq_pct),
            cost_variance=float(cost_variance),
            cpi=float(cpi) if cpi is not None else None,
            eac=float(eac) if eac is not None else None,
            cost_status=status,
            cost_status_class=status_class,
        ))
    return result


def get_cost_by_code(project):
    """Cost breakdown by cost code for one project. Returns list of dicts."""
    from .models import BudgetItem, ActualCost

    codes = {}
    for item in BudgetItem.objects.filter(project=project).select_related('cost_code'):
        k = item.cost_code.code
        codes.setdefault(k, {'code': k, 'name': item.cost_code.name,
                              'budget': Decimal('0'), 'actual': Decimal('0')})
        codes[k]['budget'] += item.budget_amount

    for ac in ActualCost.objects.filter(project=project).select_related('cost_code'):
        k = ac.cost_code.code
        codes.setdefault(k, {'code': k, 'name': ac.cost_code.name,
                              'budget': Decimal('0'), 'actual': Decimal('0')})
        codes[k]['actual'] += ac.amount

    result = []
    for v in sorted(codes.values(), key=lambda x: x['code']):
        variance = v['budget'] - v['actual']
        pct = round(float(variance / v['budget'] * 100), 1) if v['budget'] else None
        result.append({
            'code': v['code'],
            'name': v['name'],
            'budget': float(v['budget']),
            'actual': float(v['actual']),
            'variance': float(variance),
            'variance_pct': pct,
        })
    return result


def get_cost_by_source(project):
    """Cost breakdown by source type for chart data."""
    from .models import ActualCost

    rows = (ActualCost.objects
            .filter(project=project)
            .values('source_type')
            .annotate(total=Sum('amount'))
            .order_by('source_type'))
    return [{'source': r['source_type'], 'total': float(r['total'])} for r in rows]


def get_budget_vs_actual_chart_data(projects):
    """Budget vs Actual by project — JSON string for Chart.js."""
    from .models import BudgetItem, ActualCost

    labels, budget_data, actual_data = [], [], []
    for p in projects:
        budget = float(
            BudgetItem.objects.filter(project=p)
            .aggregate(t=Sum('budget_amount'))['t'] or 0
        )
        actual = float(
            ActualCost.objects.filter(project=p)
            .aggregate(t=Sum('amount'))['t'] or 0
        )
        if budget or actual:
            labels.append(p.project_name)
            budget_data.append(budget)
            actual_data.append(actual)

    return json.dumps({'labels': labels, 'budget': budget_data, 'actual': actual_data})
