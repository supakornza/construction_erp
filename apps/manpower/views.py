import json
from datetime import date, timedelta
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils.dateparse import parse_date
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView, View
from apps.accounts.mixins import CurrentProjectMixin, ManagerRequiredMixin, OperationalViewMixin, OperationalUpdateMixin
from apps.projects.models import Project
from .models import DailyManpowerRecord, ManpowerCategory
from .forms import DailyManpowerRecordForm, BulkManpowerHeaderForm
from .services import get_default_manpower_period, get_manpower_dashboard_metrics


class ManpowerDashboardView(OperationalViewMixin, TemplateView):
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


class DailyManpowerRecordListView(CurrentProjectMixin, OperationalViewMixin, ListView):
    model = DailyManpowerRecord
    template_name = 'manpower/list.html'
    context_object_name = 'records'
    paginate_by = 50

    def get_queryset(self):
        qs = super().get_queryset().select_related('project', 'category')
        project_id = self.request.GET.get('project')
        date_str = self.request.GET.get('date')
        category_id = self.request.GET.get('category')
        if project_id:
            qs = qs.filter(project_id=project_id)
        if date_str:
            qs = qs.filter(report_date=date_str)
        if category_id:
            qs = qs.filter(category_id=category_id)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['projects'] = Project.objects.filter(status='Active')
        ctx['categories'] = ManpowerCategory.objects.all()

        # Category summary: totals across all records matching project/date filters (not category filter)
        summary_qs = DailyManpowerRecord.objects.all()
        if self.current_project:
            summary_qs = summary_qs.filter(project=self.current_project)
        project_id = self.request.GET.get('project')
        date_str = self.request.GET.get('date')
        if project_id:
            summary_qs = summary_qs.filter(project_id=project_id)
        if date_str:
            summary_qs = summary_qs.filter(report_date=date_str)

        totals_map = {
            row['category_id']: row['total']
            for row in summary_qs.values('category_id').annotate(total=Sum('quantity'))
        }
        grand_total = sum(totals_map.values())
        category_summary = []
        for cat in ManpowerCategory.objects.all():
            total = totals_map.get(cat.pk, 0)
            category_summary.append({
                'category': cat,
                'total': total,
                'pct': round(total / grand_total * 100) if grand_total else 0,
            })
        ctx['category_summary'] = category_summary
        ctx['summary_grand_total'] = grand_total
        return ctx


class BulkManpowerCreateView(CurrentProjectMixin, OperationalViewMixin, View):
    template_name = 'manpower/form.html'

    def _get_categories(self):
        return ManpowerCategory.objects.all()

    def _build_rows(self, categories, post_data=None):
        rows = []
        for cat in categories:
            qty_val = ''
            remarks_val = ''
            if post_data:
                qty_val = post_data.get(f'qty_{cat.pk}', '')
                remarks_val = post_data.get(f'remarks_{cat.pk}', '')
            rows.append({'category': cat, 'qty': qty_val, 'remarks': remarks_val})
        return rows

    def get(self, request):
        categories = self._get_categories()
        form = BulkManpowerHeaderForm()
        rows = self._build_rows(categories)
        return render(request, self.template_name, {
            'form': form,
            'rows': rows,
            'is_bulk': True,
        })

    def post(self, request):
        categories = self._get_categories()
        form = BulkManpowerHeaderForm(request.POST)
        rows = self._build_rows(categories, request.POST)

        if not form.is_valid():
            return render(request, self.template_name, {
                'form': form,
                'rows': rows,
                'is_bulk': True,
            })

        project = form.cleaned_data['project']
        report_date = form.cleaned_data['report_date']
        company = form.cleaned_data['company']

        created_count = 0
        for cat in categories:
            qty_str = request.POST.get(f'qty_{cat.pk}', '').strip()
            if not qty_str or qty_str == '0':
                continue
            try:
                qty = int(qty_str)
                if qty <= 0:
                    continue
            except ValueError:
                continue

            remarks = request.POST.get(f'remarks_{cat.pk}', '').strip()
            DailyManpowerRecord.objects.create(
                project=project,
                report_date=report_date,
                category=cat,
                company=company,
                quantity=qty,
                remarks=remarks,
            )
            created_count += 1

        if created_count:
            messages.success(request, f'บันทึก Manpower {created_count} รายการเรียบร้อย')
        else:
            messages.warning(request, 'ไม่มีข้อมูลที่บันทึก กรุณากรอกจำนวนอย่างน้อย 1 ประเภท')
            return render(request, self.template_name, {
                'form': form,
                'rows': rows,
                'is_bulk': True,
            })

        return redirect('manpower:list')


class DailyManpowerRecordUpdateView(CurrentProjectMixin, OperationalUpdateMixin, UpdateView):
    model = DailyManpowerRecord
    form_class = DailyManpowerRecordForm
    template_name = 'manpower/form.html'
    success_url = reverse_lazy('manpower:list')

    def form_valid(self, form):
        messages.success(self.request, 'Record updated.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['is_bulk'] = False
        return ctx


class DailyManpowerRecordDeleteView(CurrentProjectMixin, ManagerRequiredMixin, DeleteView):
    model = DailyManpowerRecord
    template_name = 'manpower/confirm_delete.html'
    success_url = reverse_lazy('manpower:list')


class ManpowerHistogramView(OperationalViewMixin, View):
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
