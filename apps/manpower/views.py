import json
from datetime import date, timedelta
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.utils.dateparse import parse_date
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView, View
from apps.accounts.mixins import AdminRequiredMixin
from apps.projects.models import Project
from .models import DailyManpowerRecord, ManpowerCategory
from .forms import DailyManpowerRecordForm
from .services import get_default_manpower_period, get_manpower_dashboard_metrics


class ManpowerDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'manpower/dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        projects = Project.objects.filter(status='Active').order_by('contract_no')
        selected_project_id = self.request.GET.get('project')
        if selected_project_id:
            projects_for_metrics = projects.filter(pk=selected_project_id)
        else:
            projects_for_metrics = projects

        default_start, default_end = get_default_manpower_period()
        start_date = parse_date(self.request.GET.get('start', '')) or default_start
        end_date = parse_date(self.request.GET.get('end', '')) or default_end
        if start_date > end_date:
            start_date, end_date = end_date, start_date

        metrics = get_manpower_dashboard_metrics(projects_for_metrics, start_date, end_date)
        ctx.update({
            'projects': projects,
            'selected_project_id': selected_project_id,
            'metrics': metrics,
            'role_chart_labels': json.dumps([row['role'] for row in metrics['role_rows']]),
            'role_chart_values': json.dumps([row['total'] for row in metrics['role_rows']]),
            'trend_chart_labels': json.dumps([row['date'] for row in metrics['daily_trend']]),
            'trend_chart_values': json.dumps([row['total'] for row in metrics['daily_trend']]),
        })
        return ctx


class DailyManpowerRecordListView(LoginRequiredMixin, ListView):
    model = DailyManpowerRecord
    template_name = 'manpower/list.html'
    context_object_name = 'records'
    paginate_by = 30

    def get_queryset(self):
        qs = super().get_queryset().select_related('project', 'category')
        project_id = self.request.GET.get('project')
        date_str = self.request.GET.get('date')
        if project_id:
            qs = qs.filter(project_id=project_id)
        if date_str:
            qs = qs.filter(report_date=date_str)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['projects'] = Project.objects.filter(status='Active')
        return ctx


class DailyManpowerRecordCreateView(LoginRequiredMixin, CreateView):
    model = DailyManpowerRecord
    form_class = DailyManpowerRecordForm
    template_name = 'manpower/form.html'
    success_url = reverse_lazy('manpower:list')

    def form_valid(self, form):
        messages.success(self.request, 'Manpower record added.')
        return super().form_valid(form)


class DailyManpowerRecordUpdateView(LoginRequiredMixin, UpdateView):
    model = DailyManpowerRecord
    form_class = DailyManpowerRecordForm
    template_name = 'manpower/form.html'
    success_url = reverse_lazy('manpower:list')

    def form_valid(self, form):
        messages.success(self.request, 'Record updated.')
        return super().form_valid(form)


class DailyManpowerRecordDeleteView(AdminRequiredMixin, DeleteView):
    model = DailyManpowerRecord
    template_name = 'manpower/confirm_delete.html'
    success_url = reverse_lazy('manpower:list')


class ManpowerHistogramView(LoginRequiredMixin, View):
    def get(self, request):
        project_id = request.GET.get('project_id')
        end = date.today()
        start = end - timedelta(days=29)
        qs = DailyManpowerRecord.objects.filter(report_date__range=[start, end])
        if project_id:
            qs = qs.filter(project_id=project_id)
        data = (qs.values('report_date')
                   .annotate(total=Sum('quantity'))
                   .order_by('report_date'))
        labels = [(start + timedelta(days=i)).isoformat() for i in range(30)]
        totals_map = {str(r['report_date']): r['total'] for r in data}
        totals = [totals_map.get(d, 0) for d in labels]
        return JsonResponse({'labels': labels, 'data': totals})
