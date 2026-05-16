from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView

from apps.accounts.mixins import FinancialViewMixin, FinancialWriteMixin
from apps.projects.models import Project
from .forms import ActualCostForm, BudgetItemForm, CostCodeForm
from .models import ActualCost, BudgetItem, CostCode
from .services import (
    get_all_projects_cost_summary, get_budget_vs_actual_chart_data,
    get_cost_by_code, get_cost_by_source, get_cost_summary,
)


class CostDashboardView(FinancialViewMixin, TemplateView):
    template_name = 'cost_control/dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['projects'] = Project.objects.all().order_by('project_name')
        active_projects = list(Project.objects.filter(status='Active'))

        project_id = self.request.GET.get('project')
        if project_id:
            project = get_object_or_404(Project, pk=project_id)
            ctx['selected_project'] = project
            ctx['cost_summary'] = get_cost_summary(project)
            ctx['cost_by_code'] = get_cost_by_code(project)
            ctx['cost_by_source'] = get_cost_by_source(project)
        else:
            ctx['cost_summary'] = get_all_projects_cost_summary(active_projects)
            ctx['cost_by_code'] = []
            ctx['cost_by_source'] = []

        ctx['budget_vs_actual_json'] = get_budget_vs_actual_chart_data(active_projects)
        return ctx


# ── Cost Codes ─────────────────────────────────────────────

class CostCodeListView(FinancialViewMixin, ListView):
    model = CostCode
    template_name = 'cost_control/cost_code_list.html'
    context_object_name = 'cost_codes'

    def get_queryset(self):
        qs = CostCode.objects.select_related('project').order_by('project', 'code')
        project_id = self.request.GET.get('project')
        if project_id:
            qs = qs.filter(project_id=project_id)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['projects'] = Project.objects.all()
        return ctx


class CostCodeCreateView(FinancialWriteMixin, CreateView):
    model = CostCode
    form_class = CostCodeForm
    template_name = 'cost_control/cost_code_form.html'
    success_url = reverse_lazy('cost_control:cost_code_list')

    def form_valid(self, form):
        messages.success(self.request, 'Cost code created.')
        return super().form_valid(form)


class CostCodeUpdateView(FinancialWriteMixin, UpdateView):
    model = CostCode
    form_class = CostCodeForm
    template_name = 'cost_control/cost_code_form.html'
    success_url = reverse_lazy('cost_control:cost_code_list')

    def form_valid(self, form):
        messages.success(self.request, 'Cost code updated.')
        return super().form_valid(form)


class CostCodeDeleteView(FinancialWriteMixin, DeleteView):
    model = CostCode
    template_name = 'safety/confirm_delete.html'
    success_url = reverse_lazy('cost_control:cost_code_list')


# ── Budget Items ───────────────────────────────────────────

class BudgetItemListView(FinancialViewMixin, ListView):
    model = BudgetItem
    template_name = 'cost_control/budget_list.html'
    context_object_name = 'budget_items'

    def get_queryset(self):
        qs = (BudgetItem.objects
              .select_related('project', 'cost_code', 'boq_item')
              .order_by('project', 'cost_code__code'))
        project_id = self.request.GET.get('project')
        if project_id:
            qs = qs.filter(project_id=project_id)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['projects'] = Project.objects.all()
        return ctx


class BudgetItemCreateView(FinancialWriteMixin, CreateView):
    model = BudgetItem
    form_class = BudgetItemForm
    template_name = 'cost_control/budget_form.html'
    success_url = reverse_lazy('cost_control:budget_list')

    def form_valid(self, form):
        messages.success(self.request, 'Budget item created.')
        return super().form_valid(form)


class BudgetItemUpdateView(FinancialWriteMixin, UpdateView):
    model = BudgetItem
    form_class = BudgetItemForm
    template_name = 'cost_control/budget_form.html'
    success_url = reverse_lazy('cost_control:budget_list')

    def form_valid(self, form):
        messages.success(self.request, 'Budget item updated.')
        return super().form_valid(form)


class BudgetItemDeleteView(FinancialWriteMixin, DeleteView):
    model = BudgetItem
    template_name = 'safety/confirm_delete.html'
    success_url = reverse_lazy('cost_control:budget_list')


# ── Actual Costs ───────────────────────────────────────────

class ActualCostListView(FinancialViewMixin, ListView):
    model = ActualCost
    template_name = 'cost_control/actual_cost_list.html'
    context_object_name = 'costs'
    paginate_by = 50

    def get_queryset(self):
        qs = (ActualCost.objects
              .select_related('project', 'cost_code', 'created_by')
              .order_by('-cost_date'))
        project_id = self.request.GET.get('project')
        source = self.request.GET.get('source')
        if project_id:
            qs = qs.filter(project_id=project_id)
        if source:
            qs = qs.filter(source_type=source)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['projects'] = Project.objects.all()
        ctx['source_choices'] = ActualCost.SOURCE_CHOICES
        return ctx


class ActualCostCreateView(FinancialWriteMixin, CreateView):
    model = ActualCost
    form_class = ActualCostForm
    template_name = 'cost_control/actual_cost_form.html'
    success_url = reverse_lazy('cost_control:actual_cost_list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Actual cost recorded.')
        return super().form_valid(form)


class ActualCostUpdateView(FinancialWriteMixin, UpdateView):
    model = ActualCost
    form_class = ActualCostForm
    template_name = 'cost_control/actual_cost_form.html'
    success_url = reverse_lazy('cost_control:actual_cost_list')

    def form_valid(self, form):
        messages.success(self.request, 'Actual cost updated.')
        return super().form_valid(form)


class ActualCostDeleteView(FinancialWriteMixin, DeleteView):
    model = ActualCost
    template_name = 'safety/confirm_delete.html'
    success_url = reverse_lazy('cost_control:actual_cost_list')
