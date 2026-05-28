from datetime import date, timedelta

from django.db.models import Count, Sum

from .models import DailyManpowerRecord, ManpowerCategory


def get_default_manpower_period(today=None):
    end_date = today or date.today()
    return end_date - timedelta(days=29), end_date


def get_manpower_dashboard_metrics(projects, start_date=None, end_date=None):
    if start_date is None or end_date is None:
        start_date, end_date = get_default_manpower_period()

    records = DailyManpowerRecord.objects.filter(
        project__in=projects,
        report_date__range=[start_date, end_date],
    ).select_related('project', 'category')

    total_manpower = records.aggregate(total=Sum('quantity'))['total'] or 0
    active_days = records.values('report_date').distinct().count()
    average_daily = round(total_manpower / active_days, 1) if active_days else 0

    role_totals_raw = {
        row['category_id']: row
        for row in records.values('category_id').annotate(
            total=Sum('quantity'),
            days=Count('report_date', distinct=True),
        )
    }
    today_totals_raw = {
        row['category_id']: row['total'] or 0
        for row in DailyManpowerRecord.objects.filter(
            project__in=projects,
            report_date=end_date,
        ).values('category_id').annotate(total=Sum('quantity'))
    }

    role_rows = []
    for category in ManpowerCategory.objects.all().order_by('name'):
        aggregate = role_totals_raw.get(category.id, {})
        total = aggregate.get('total') or 0
        days = aggregate.get('days') or 0
        today_total = today_totals_raw.get(category.id, 0)
        role_rows.append({
            'category_id': category.id,
            'role': category.get_name_display(),
            'total': total,
            'today_total': today_total,
            'average_daily': round(total / days, 1) if days else 0,
            'share': round((total / total_manpower) * 100, 1) if total_manpower else 0,
        })

    role_rows.sort(key=lambda row: row['total'], reverse=True)
    peak_role = role_rows[0] if role_rows and role_rows[0]['total'] else None

    daily_raw = {
        row['report_date']: row['total'] or 0
        for row in records.values('report_date').annotate(total=Sum('quantity')).order_by('report_date')
    }
    day_count = (end_date - start_date).days + 1
    daily_trend = [
        {
            'date': (start_date + timedelta(days=i)).isoformat(),
            'total': daily_raw.get(start_date + timedelta(days=i), 0),
        }
        for i in range(day_count)
    ]

    company_rows = list(
        records.values('company')
        .annotate(total=Sum('quantity'))
        .order_by('-total', 'company')[:8]
    )

    return {
        'start_date': start_date,
        'end_date': end_date,
        'total_manpower': total_manpower,
        'active_days': active_days,
        'average_daily': average_daily,
        'active_roles': sum(1 for row in role_rows if row['total'] > 0),
        'peak_role': peak_role,
        'role_rows': role_rows,
        'daily_trend': daily_trend,
        'company_rows': company_rows,
    }
