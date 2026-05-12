import json
from datetime import date, timedelta
from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Sum, Avg
from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import (
    ListView, CreateView, DetailView, UpdateView, DeleteView, TemplateView, View, FormView
)
from apps.accounts.mixins import AdminRequiredMixin, ApproverRequiredMixin
from apps.projects.models import Project
from .models import (
    Barge, RockDailyRecord, RockBargePlacement,
    SandDailyRecord, SandBargePlacement, SandAllocation,
    RevetmentStation, RevetmentActivity, RevetmentDailyRecord,
    RecoveryPlan, RecoveryPlanDailyItem,
    RecoveryActionPlan, RecoveryActionItem, RecoveryActionDailyProgress,
    LogisticsScenario, ImportLog,
)
from .forms import (
    RockDailyRecordForm, RockBargePlacementFormSet,
    SandDailyRecordForm, SandBargePlacementFormSet,
    SandAllocationForm, RecoveryPlanForm, RecoveryPlanDailyItemFormSet,
    RevetmentStationForm, RevetmentActivityForm,
    RevetmentDailyRecordForm, RevetmentDailyItemFormSet,
    RecoveryActionPlanForm, RecoveryActionItemFormSet,
    RecoveryActionDailyProgressForm, LogisticsScenarioForm, ImportForm,
)
from .services import (
    recalculate_rock_accumulatives, recalculate_sand_accumulatives,
    recalculate_recovery_plan, recalculate_action_item_progress,
    get_rock_dashboard_data, get_sand_dashboard_data, get_revetment_dashboard_data,
    get_rap_dashboard_data,
)


# ── Project Controls Main Dashboard ──────────────────────────────────────────

class ProjectControlsDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'project_controls/dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        projects = Project.objects.filter(status='Active')
        project_id = self.request.GET.get('project')
        selected = None
        rock_data = sand_data = revetment_data = rap_data = {}
        if project_id:
            selected = get_object_or_404(Project, pk=project_id)
            rock_data = get_rock_dashboard_data(selected)
            sand_data = get_sand_dashboard_data(selected)
            revetment_data = get_revetment_dashboard_data(selected)
            rap_data = get_rap_dashboard_data(selected)
        elif projects.exists():
            selected = projects.first()
            rock_data = get_rock_dashboard_data(selected)
            sand_data = get_sand_dashboard_data(selected)
            revetment_data = get_revetment_dashboard_data(selected)
            rap_data = get_rap_dashboard_data(selected)
        ctx.update({
            'projects': projects,
            'selected_project': selected,
            'rock_data': rock_data,
            'sand_data': sand_data,
            'revetment_data': revetment_data,
            'rap_data': rap_data,
        })
        return ctx


# ── Rock Views ────────────────────────────────────────────────────────────────

class RockListView(LoginRequiredMixin, ListView):
    model = RockDailyRecord
    template_name = 'project_controls/rock/list.html'
    context_object_name = 'records'
    paginate_by = 30

    def get_queryset(self):
        qs = super().get_queryset().select_related('project')
        project_id = self.request.GET.get('project')
        if project_id:
            qs = qs.filter(project_id=project_id)
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        if date_from:
            qs = qs.filter(record_date__gte=date_from)
        if date_to:
            qs = qs.filter(record_date__lte=date_to)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['projects'] = Project.objects.filter(status='Active')
        return ctx


class RockCreateView(LoginRequiredMixin, CreateView):
    model = RockDailyRecord
    form_class = RockDailyRecordForm
    template_name = 'project_controls/rock/form.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.request.POST:
            ctx['barge_formset'] = RockBargePlacementFormSet(self.request.POST)
        else:
            ctx['barge_formset'] = RockBargePlacementFormSet()
        return ctx

    def form_valid(self, form):
        ctx = self.get_context_data()
        barge_fs = ctx['barge_formset']
        if barge_fs.is_valid():
            with transaction.atomic():
                form.instance.created_by = self.request.user
                self.object = form.save()
                barge_fs.instance = self.object
                barge_fs.save()
                # Auto-sum placed_daily_ton from barges
                total = sum(
                    bp.quantity_ton for bp in self.object.barge_placements.all()
                )
                self.object.placed_daily_ton = total
                self.object.save(update_fields=['placed_daily_ton'])
                recalculate_rock_accumulatives(self.object.project)
            messages.success(self.request, 'Rock daily record saved.')
            return redirect(self.get_success_url())
        return self.render_to_response(self.get_context_data(form=form))

    def get_success_url(self):
        return reverse_lazy('project_controls:rock_detail', kwargs={'pk': self.object.pk})


class RockDetailView(LoginRequiredMixin, DetailView):
    model = RockDailyRecord
    template_name = 'project_controls/rock/detail.html'
    context_object_name = 'record'


class RockUpdateView(LoginRequiredMixin, UpdateView):
    model = RockDailyRecord
    form_class = RockDailyRecordForm
    template_name = 'project_controls/rock/form.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.request.POST:
            ctx['barge_formset'] = RockBargePlacementFormSet(self.request.POST, instance=self.object)
        else:
            ctx['barge_formset'] = RockBargePlacementFormSet(instance=self.object)
        return ctx

    def form_valid(self, form):
        ctx = self.get_context_data()
        barge_fs = ctx['barge_formset']
        if barge_fs.is_valid():
            with transaction.atomic():
                self.object = form.save()
                barge_fs.instance = self.object
                barge_fs.save()
                total = sum(bp.quantity_ton for bp in self.object.barge_placements.all())
                self.object.placed_daily_ton = total
                self.object.save(update_fields=['placed_daily_ton'])
                recalculate_rock_accumulatives(self.object.project)
            messages.success(self.request, 'Rock record updated.')
            return redirect(self.get_success_url())
        return self.render_to_response(self.get_context_data(form=form))

    def get_success_url(self):
        return reverse_lazy('project_controls:rock_detail', kwargs={'pk': self.object.pk})


class RockDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'project_controls/rock/dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        projects = Project.objects.filter(status='Active')
        project_id = self.request.GET.get('project')
        selected = projects.filter(pk=project_id).first() if project_id else projects.first()
        rock_data = get_rock_dashboard_data(selected) if selected else {}
        rock_data.setdefault('chart_data', '{}')
        rock_data.setdefault('barge_totals', [])
        ctx.update({'projects': projects, 'selected_project': selected, 'data': rock_data})
        return ctx


class RockDeleteView(AdminRequiredMixin, View):
    def post(self, request, pk):
        record = get_object_or_404(RockDailyRecord, pk=pk)
        project = record.project
        record.delete()
        recalculate_rock_accumulatives(project)
        messages.success(request, 'Rock record deleted.')
        return redirect('project_controls:rock_list')


class RockExportExcelView(LoginRequiredMixin, View):
    def get(self, request, project_id):
        from .exports import export_rock_excel
        project = get_object_or_404(Project, pk=project_id)
        buffer = export_rock_excel(project)
        filename = f"Rock_Summary_{project.contract_no}.xlsx"
        response = HttpResponse(
            buffer.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response


class RockExportPDFView(LoginRequiredMixin, View):
    def get(self, request, pk):
        from .exports import export_rock_pdf
        record = get_object_or_404(RockDailyRecord, pk=pk)
        buffer = export_rock_pdf(record)
        filename = f"Rock_{record.project.contract_no}_{record.record_date}.pdf"
        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response


# ── Sand Views ────────────────────────────────────────────────────────────────

class SandListView(LoginRequiredMixin, ListView):
    model = SandDailyRecord
    template_name = 'project_controls/sand/list.html'
    context_object_name = 'records'
    paginate_by = 30

    def get_queryset(self):
        qs = super().get_queryset().select_related('project')
        project_id = self.request.GET.get('project')
        if project_id:
            qs = qs.filter(project_id=project_id)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['projects'] = Project.objects.filter(status='Active')
        return ctx


class SandCreateView(LoginRequiredMixin, CreateView):
    model = SandDailyRecord
    form_class = SandDailyRecordForm
    template_name = 'project_controls/sand/form.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.request.POST:
            ctx['barge_formset'] = SandBargePlacementFormSet(self.request.POST)
        else:
            ctx['barge_formset'] = SandBargePlacementFormSet()
        return ctx

    def form_valid(self, form):
        ctx = self.get_context_data()
        barge_fs = ctx['barge_formset']
        if barge_fs.is_valid():
            with transaction.atomic():
                form.instance.created_by = self.request.user
                # Auto-compute total_daily_ton
                tct = form.cleaned_data.get('tct_daily_ton', Decimal('0')) or Decimal('0')
                mtp3 = form.cleaned_data.get('mtp3_daily_ton', Decimal('0')) or Decimal('0')
                oswald = form.cleaned_data.get('oswald_daily_ton', Decimal('0')) or Decimal('0')
                form.instance.total_daily_ton = tct + mtp3 + oswald
                self.object = form.save()
                barge_fs.instance = self.object
                barge_fs.save()
                # Auto-sum offshore from barges
                offshore_total = sum(bp.quantity_ton for bp in self.object.barge_placements.all())
                self.object.offshore_daily_ton = offshore_total
                self.object.save(update_fields=['offshore_daily_ton'])
                recalculate_sand_accumulatives(self.object.project)
            messages.success(self.request, 'Sand daily record saved.')
            return redirect(self.get_success_url())
        return self.render_to_response(self.get_context_data(form=form))

    def get_success_url(self):
        return reverse_lazy('project_controls:sand_detail', kwargs={'pk': self.object.pk})


class SandDetailView(LoginRequiredMixin, DetailView):
    model = SandDailyRecord
    template_name = 'project_controls/sand/detail.html'
    context_object_name = 'record'


class SandUpdateView(LoginRequiredMixin, UpdateView):
    model = SandDailyRecord
    form_class = SandDailyRecordForm
    template_name = 'project_controls/sand/form.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.request.POST:
            ctx['barge_formset'] = SandBargePlacementFormSet(self.request.POST, instance=self.object)
        else:
            ctx['barge_formset'] = SandBargePlacementFormSet(instance=self.object)
        return ctx

    def form_valid(self, form):
        ctx = self.get_context_data()
        barge_fs = ctx['barge_formset']
        if barge_fs.is_valid():
            with transaction.atomic():
                tct = form.cleaned_data.get('tct_daily_ton', Decimal('0')) or Decimal('0')
                mtp3 = form.cleaned_data.get('mtp3_daily_ton', Decimal('0')) or Decimal('0')
                oswald = form.cleaned_data.get('oswald_daily_ton', Decimal('0')) or Decimal('0')
                form.instance.total_daily_ton = tct + mtp3 + oswald
                self.object = form.save()
                barge_fs.instance = self.object
                barge_fs.save()
                offshore_total = sum(bp.quantity_ton for bp in self.object.barge_placements.all())
                self.object.offshore_daily_ton = offshore_total
                self.object.save(update_fields=['offshore_daily_ton'])
                recalculate_sand_accumulatives(self.object.project)
            messages.success(self.request, 'Sand record updated.')
            return redirect(self.get_success_url())
        return self.render_to_response(self.get_context_data(form=form))

    def get_success_url(self):
        return reverse_lazy('project_controls:sand_detail', kwargs={'pk': self.object.pk})


class SandDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'project_controls/sand/dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        projects = Project.objects.filter(status='Active')
        project_id = self.request.GET.get('project')
        selected = projects.filter(pk=project_id).first() if project_id else projects.first()
        sand_data = get_sand_dashboard_data(selected) if selected else {}
        sand_data.setdefault('chart_data', '{}')
        sand_data.setdefault('barge_totals', [])
        sand_data.setdefault('other_source_label', 'Other sources')
        ctx.update({'projects': projects, 'selected_project': selected, 'sand_data': sand_data, 'data': sand_data})
        return ctx


class SandDeleteView(AdminRequiredMixin, View):
    def post(self, request, pk):
        record = get_object_or_404(SandDailyRecord, pk=pk)
        project = record.project
        record.delete()
        recalculate_sand_accumulatives(project)
        messages.success(request, 'Sand record deleted.')
        return redirect('project_controls:sand_list')


class SandExportExcelView(LoginRequiredMixin, View):
    def get(self, request, project_id):
        from .exports import export_sand_excel
        project = get_object_or_404(Project, pk=project_id)
        buffer = export_sand_excel(project)
        filename = f"Sand_Summary_{project.contract_no}.xlsx"
        response = HttpResponse(
            buffer.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response


# ── Sand Allocation Views ─────────────────────────────────────────────────────

def _resolve_revetment_project(request, obj=None):
    project_id = request.POST.get('project') or request.GET.get('project')
    if project_id:
        return Project.objects.filter(pk=project_id).first()
    if obj and getattr(obj, 'project_id', None):
        return obj.project
    return Project.objects.filter(status='Active').first()


class RevetmentDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'project_controls/revetment/dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        projects = Project.objects.filter(status='Active')
        project_id = self.request.GET.get('project')
        selected = projects.filter(pk=project_id).first() if project_id else projects.first()
        data = get_revetment_dashboard_data(selected) if selected else {}
        ctx.update({'projects': projects, 'selected_project': selected, 'data': data})
        return ctx


class RevetmentRecordListView(LoginRequiredMixin, ListView):
    model = RevetmentDailyRecord
    template_name = 'project_controls/revetment/list.html'
    context_object_name = 'records'
    paginate_by = 30

    def get_queryset(self):
        qs = super().get_queryset().select_related('project', 'created_by').prefetch_related('items')
        project_id = self.request.GET.get('project')
        if project_id:
            qs = qs.filter(project_id=project_id)
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        if date_from:
            qs = qs.filter(record_date__gte=date_from)
        if date_to:
            qs = qs.filter(record_date__lte=date_to)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['projects'] = Project.objects.filter(status='Active')
        return ctx


class RevetmentRecordCreateView(LoginRequiredMixin, CreateView):
    model = RevetmentDailyRecord
    form_class = RevetmentDailyRecordForm
    template_name = 'project_controls/revetment/form.html'

    def get_initial(self):
        initial = super().get_initial()
        project = _resolve_revetment_project(self.request)
        if project:
            initial['project'] = project
        return initial

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        project = _resolve_revetment_project(self.request, getattr(self, 'object', None))
        if self.request.POST:
            ctx['item_formset'] = RevetmentDailyItemFormSet(
                self.request.POST,
                form_kwargs={'project': project},
            )
        else:
            ctx['item_formset'] = RevetmentDailyItemFormSet(
                form_kwargs={'project': project},
            )
        ctx['selected_project'] = project
        return ctx

    def form_valid(self, form):
        project = form.cleaned_data.get('project')
        item_formset = RevetmentDailyItemFormSet(
            self.request.POST,
            form_kwargs={'project': project},
        )
        if item_formset.is_valid():
            with transaction.atomic():
                form.instance.created_by = self.request.user
                self.object = form.save()
                item_formset.instance = self.object
                item_formset.save()
            messages.success(self.request, 'Revetment daily record saved.')
            return redirect(self.get_success_url())
        return self.render_to_response(self.get_context_data(form=form, item_formset=item_formset))

    def get_success_url(self):
        return reverse_lazy('project_controls:revetment_detail', kwargs={'pk': self.object.pk})


class RevetmentRecordDetailView(LoginRequiredMixin, DetailView):
    model = RevetmentDailyRecord
    template_name = 'project_controls/revetment/detail.html'
    context_object_name = 'record'

    def get_queryset(self):
        return super().get_queryset().select_related('project', 'created_by').prefetch_related(
            'items__station', 'items__activity'
        )


class RevetmentRecordUpdateView(LoginRequiredMixin, UpdateView):
    model = RevetmentDailyRecord
    form_class = RevetmentDailyRecordForm
    template_name = 'project_controls/revetment/form.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        project = _resolve_revetment_project(self.request, self.object)
        if self.request.POST:
            ctx['item_formset'] = RevetmentDailyItemFormSet(
                self.request.POST,
                instance=self.object,
                form_kwargs={'project': project},
            )
        else:
            ctx['item_formset'] = RevetmentDailyItemFormSet(
                instance=self.object,
                form_kwargs={'project': project},
            )
        ctx['selected_project'] = project
        return ctx

    def form_valid(self, form):
        project = form.cleaned_data.get('project')
        item_formset = RevetmentDailyItemFormSet(
            self.request.POST,
            instance=self.object,
            form_kwargs={'project': project},
        )
        if item_formset.is_valid():
            with transaction.atomic():
                self.object = form.save()
                item_formset.instance = self.object
                item_formset.save()
            messages.success(self.request, 'Revetment record updated.')
            return redirect(self.get_success_url())
        return self.render_to_response(self.get_context_data(form=form, item_formset=item_formset))

    def get_success_url(self):
        return reverse_lazy('project_controls:revetment_detail', kwargs={'pk': self.object.pk})


class RevetmentSetupView(LoginRequiredMixin, TemplateView):
    template_name = 'project_controls/revetment/setup.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        projects = Project.objects.filter(status='Active')
        project_id = self.request.GET.get('project')
        selected = projects.filter(pk=project_id).first() if project_id else projects.first()
        ctx.update({
            'projects': projects,
            'selected_project': selected,
            'stations': RevetmentStation.objects.filter(project=selected) if selected else [],
            'activities': RevetmentActivity.objects.filter(project=selected) if selected else [],
        })
        return ctx


class RevetmentStationCreateView(LoginRequiredMixin, CreateView):
    model = RevetmentStation
    form_class = RevetmentStationForm
    template_name = 'project_controls/revetment/station_form.html'

    def get_initial(self):
        initial = super().get_initial()
        project = _resolve_revetment_project(self.request)
        if project:
            initial['project'] = project
        return initial

    def get_success_url(self):
        return f"{reverse_lazy('project_controls:revetment_setup')}?project={self.object.project_id}"


class RevetmentStationUpdateView(LoginRequiredMixin, UpdateView):
    model = RevetmentStation
    form_class = RevetmentStationForm
    template_name = 'project_controls/revetment/station_form.html'

    def get_success_url(self):
        return f"{reverse_lazy('project_controls:revetment_setup')}?project={self.object.project_id}"


class RevetmentActivityCreateView(LoginRequiredMixin, CreateView):
    model = RevetmentActivity
    form_class = RevetmentActivityForm
    template_name = 'project_controls/revetment/activity_form.html'

    def get_initial(self):
        initial = super().get_initial()
        project = _resolve_revetment_project(self.request)
        if project:
            initial['project'] = project
        return initial

    def get_success_url(self):
        return f"{reverse_lazy('project_controls:revetment_setup')}?project={self.object.project_id}"


class RevetmentActivityUpdateView(LoginRequiredMixin, UpdateView):
    model = RevetmentActivity
    form_class = RevetmentActivityForm
    template_name = 'project_controls/revetment/activity_form.html'

    def get_success_url(self):
        return f"{reverse_lazy('project_controls:revetment_setup')}?project={self.object.project_id}"


class RevetmentExportExcelView(LoginRequiredMixin, View):
    def get(self, request, project_id):
        from .exports import export_revetment_excel
        project = get_object_or_404(Project, pk=project_id)
        buffer = export_revetment_excel(project)
        filename = f"Revetment_Progress_{project.contract_no}.xlsx"
        response = HttpResponse(
            buffer.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response


class SandAllocationListView(LoginRequiredMixin, ListView):
    model = SandAllocation
    template_name = 'project_controls/sand/allocation_list.html'
    context_object_name = 'allocations'
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset().select_related('project')
        project_id = self.request.GET.get('project')
        if project_id:
            qs = qs.filter(project_id=project_id)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['projects'] = Project.objects.filter(status='Active')
        return ctx


class SandAllocationCreateView(LoginRequiredMixin, CreateView):
    model = SandAllocation
    form_class = SandAllocationForm
    template_name = 'project_controls/sand/allocation_form.html'
    success_url = reverse_lazy('project_controls:sand_allocation_list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, 'Sand allocation calculated.')
        return response


class SandAllocationDetailView(LoginRequiredMixin, DetailView):
    model = SandAllocation
    template_name = 'project_controls/sand/allocation_detail.html'
    context_object_name = 'allocation'


# ── Recovery Plan Views ───────────────────────────────────────────────────────

class RecoveryPlanListView(LoginRequiredMixin, ListView):
    model = RecoveryPlan
    template_name = 'project_controls/recovery/plan_list.html'
    context_object_name = 'plans'
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset().select_related('project')
        project_id = self.request.GET.get('project')
        if project_id:
            qs = qs.filter(project_id=project_id)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['projects'] = Project.objects.filter(status='Active')
        return ctx


class RecoveryPlanCreateView(LoginRequiredMixin, CreateView):
    model = RecoveryPlan
    form_class = RecoveryPlanForm
    template_name = 'project_controls/recovery/plan_form.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.request.POST:
            ctx['item_formset'] = RecoveryPlanDailyItemFormSet(self.request.POST, prefix='daily_items')
        else:
            ctx['item_formset'] = RecoveryPlanDailyItemFormSet(prefix='daily_items')
        return ctx

    def form_valid(self, form):
        ctx = self.get_context_data()
        item_fs = ctx['item_formset']
        if item_fs.is_valid():
            with transaction.atomic():
                form.instance.prepared_by = self.request.user
                self.object = form.save()
                item_fs.instance = self.object
                item_fs.save()
                recalculate_recovery_plan(self.object)
            messages.success(self.request, 'Recovery plan created.')
            return redirect(self.get_success_url())
        return self.render_to_response(self.get_context_data(form=form))

    def get_success_url(self):
        return reverse_lazy('project_controls:recovery_plan_detail', kwargs={'pk': self.object.pk})


class RecoveryPlanDetailView(LoginRequiredMixin, DetailView):
    model = RecoveryPlan
    template_name = 'project_controls/recovery/plan_detail.html'
    context_object_name = 'plan'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        items = self.object.daily_items.order_by('plan_date')
        labels = [str(i.plan_date) for i in items]
        planned = [float(i.planned_quantity) for i in items]
        actual = [float(i.actual_quantity or 0) for i in items]
        accum_planned = [float(i.accumulative_planned) for i in items]
        accum_actual = [float(i.accumulative_actual) for i in items]
        ctx['chart_json'] = json.dumps({
            'labels': labels, 'planned': planned, 'actual': actual,
            'accum_planned': accum_planned, 'accum_actual': accum_actual,
        })
        ctx['items'] = items
        return ctx


class RecoveryPlanUpdateView(LoginRequiredMixin, UpdateView):
    model = RecoveryPlan
    form_class = RecoveryPlanForm
    template_name = 'project_controls/recovery/plan_form.html'

    def get_success_url(self):
        return reverse_lazy('project_controls:recovery_plan_detail', kwargs={'pk': self.object.pk})


class RecoveryPlanDailyUpdateView(LoginRequiredMixin, View):
    """Bulk update daily items for a recovery plan."""
    template_name = 'project_controls/recovery/plan_daily_update.html'

    def get(self, request, pk):
        plan = get_object_or_404(RecoveryPlan, pk=pk)
        items = plan.daily_items.order_by('plan_date')
        from django.template.response import TemplateResponse
        return TemplateResponse(request, self.template_name, {'plan': plan, 'items': items})

    def post(self, request, pk):
        plan = get_object_or_404(RecoveryPlan, pk=pk)
        items = plan.daily_items.order_by('plan_date')
        for item in items:
            key = f'actual_{item.pk}'
            val = request.POST.get(key)
            if val is not None:
                try:
                    item.actual_quantity = Decimal(val)
                    item.save(update_fields=['actual_quantity'])
                except Exception:
                    pass
        recalculate_recovery_plan(plan)
        messages.success(request, 'Daily actuals updated.')
        return redirect('project_controls:recovery_plan_detail', pk=pk)


# ── Recovery Action Plan Views ────────────────────────────────────────────────

class RecoveryActionPlanListView(LoginRequiredMixin, ListView):
    model = RecoveryActionPlan
    template_name = 'project_controls/recovery/rap_list.html'
    context_object_name = 'plans'
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset().select_related('project', 'prepared_by')
        project_id = self.request.GET.get('project')
        status = self.request.GET.get('status')
        if project_id:
            qs = qs.filter(project_id=project_id)
        if status:
            qs = qs.filter(status=status)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['projects'] = Project.objects.filter(status='Active')
        ctx['status_choices'] = RecoveryActionPlan.STATUS_CHOICES
        return ctx


class RecoveryActionPlanCreateView(LoginRequiredMixin, CreateView):
    model = RecoveryActionPlan
    form_class = RecoveryActionPlanForm
    template_name = 'project_controls/recovery/rap_form.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.request.POST:
            ctx['item_formset'] = RecoveryActionItemFormSet(self.request.POST)
        else:
            ctx['item_formset'] = RecoveryActionItemFormSet()
        return ctx

    def form_valid(self, form):
        ctx = self.get_context_data()
        item_fs = ctx['item_formset']
        if item_fs.is_valid():
            with transaction.atomic():
                form.instance.prepared_by = self.request.user
                self.object = form.save()
                item_fs.instance = self.object
                item_fs.save()
            messages.success(self.request, 'Recovery Action Plan created.')
            return redirect(self.get_success_url())
        return self.render_to_response(self.get_context_data(form=form))

    def get_success_url(self):
        return reverse_lazy('project_controls:rap_detail', kwargs={'pk': self.object.pk})


class RecoveryActionPlanDetailView(LoginRequiredMixin, DetailView):
    model = RecoveryActionPlan
    template_name = 'project_controls/recovery/rap_detail.html'
    context_object_name = 'plan'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        items = self.object.items.prefetch_related('daily_progress').all()
        rap_data = get_rap_dashboard_data(self.object.project)
        ctx.update({'items': items, 'rap_data': rap_data})
        return ctx


class RecoveryActionPlanUpdateView(LoginRequiredMixin, UpdateView):
    model = RecoveryActionPlan
    form_class = RecoveryActionPlanForm
    template_name = 'project_controls/recovery/rap_form.html'

    def get_queryset(self):
        return RecoveryActionPlan.objects.filter(status__in=['Draft', 'Rejected'])

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.request.POST:
            ctx['item_formset'] = RecoveryActionItemFormSet(self.request.POST, instance=self.object)
        else:
            ctx['item_formset'] = RecoveryActionItemFormSet(instance=self.object)
        return ctx

    def form_valid(self, form):
        ctx = self.get_context_data()
        item_fs = ctx['item_formset']
        if item_fs.is_valid():
            with transaction.atomic():
                self.object = form.save()
                item_fs.instance = self.object
                item_fs.save()
            messages.success(self.request, 'Recovery Action Plan updated.')
            return redirect(self.get_success_url())
        return self.render_to_response(self.get_context_data(form=form))

    def get_success_url(self):
        return reverse_lazy('project_controls:rap_detail', kwargs={'pk': self.object.pk})


class RAPSubmitView(LoginRequiredMixin, View):
    def post(self, request, pk):
        plan = get_object_or_404(RecoveryActionPlan, pk=pk, status='Draft')
        plan.status = 'Submitted'
        plan.save()
        messages.success(request, 'Plan submitted for review.')
        return redirect('project_controls:rap_detail', pk=pk)


class RAPApproveView(ApproverRequiredMixin, View):
    def post(self, request, pk):
        plan = get_object_or_404(RecoveryActionPlan, pk=pk, status__in=['Submitted', 'Reviewed'])
        plan.status = 'Approved'
        plan.approved_by = request.user
        plan.save()
        messages.success(request, 'Plan approved.')
        return redirect('project_controls:rap_detail', pk=pk)


class RAPRejectView(ApproverRequiredMixin, View):
    def post(self, request, pk):
        plan = get_object_or_404(RecoveryActionPlan, pk=pk, status__in=['Submitted', 'Reviewed'])
        reason = request.POST.get('rejection_reason', '')
        plan.status = 'Rejected'
        plan.rejection_reason = reason
        plan.save()
        messages.warning(request, 'Plan rejected.')
        return redirect('project_controls:rap_detail', pk=pk)


class RecoveryActionDailyProgressCreateView(LoginRequiredMixin, CreateView):
    model = RecoveryActionDailyProgress
    form_class = RecoveryActionDailyProgressForm
    template_name = 'project_controls/recovery/progress_form.html'

    def get_action_item(self):
        return get_object_or_404(RecoveryActionItem, pk=self.kwargs['item_pk'])

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['action_item'] = self.get_action_item()
        return ctx

    def form_valid(self, form):
        action_item = self.get_action_item()
        form.instance.action_item = action_item
        self.object = form.save()
        recalculate_action_item_progress(action_item)
        messages.success(self.request, 'Progress recorded.')
        return redirect('project_controls:rap_detail', pk=action_item.recovery_plan.pk)


class RecoveryDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'project_controls/recovery/dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        projects = Project.objects.filter(status='Active')
        project_id = self.request.GET.get('project')
        selected = projects.filter(pk=project_id).first() if project_id else projects.first()
        rap_data = get_rap_dashboard_data(selected) if selected else {}
        items = RecoveryActionItem.objects.filter(
            recovery_plan__project=selected
        ).prefetch_related('daily_progress') if selected else []
        ctx.update({
            'projects': projects, 'selected_project': selected,
            'rap_data': rap_data, 'items': items,
        })
        return ctx


class RAPExportExcelView(LoginRequiredMixin, View):
    def get(self, request, pk):
        from .exports import export_rap_excel
        plan = get_object_or_404(RecoveryActionPlan, pk=pk)
        buffer = export_rap_excel(plan)
        filename = f"RAP_{plan.project.contract_no}_{plan.pk}.xlsx"
        response = HttpResponse(
            buffer.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response


class RAPExportPDFView(LoginRequiredMixin, View):
    def get(self, request, pk):
        from .exports import export_rap_pdf
        plan = get_object_or_404(RecoveryActionPlan, pk=pk)
        buffer = export_rap_pdf(plan)
        filename = f"RAP_{plan.project.contract_no}_{plan.pk}.pdf"
        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response


# ── Logistics Views ───────────────────────────────────────────────────────────

class LogisticsScenarioListView(LoginRequiredMixin, ListView):
    model = LogisticsScenario
    template_name = 'project_controls/logistics/list.html'
    context_object_name = 'scenarios'
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset().select_related('project')
        project_id = self.request.GET.get('project')
        if project_id:
            qs = qs.filter(project_id=project_id)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['projects'] = Project.objects.filter(status='Active')
        return ctx


class LogisticsScenarioCreateView(LoginRequiredMixin, CreateView):
    model = LogisticsScenario
    form_class = LogisticsScenarioForm
    template_name = 'project_controls/logistics/form.html'
    success_url = reverse_lazy('project_controls:logistics_list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Logistics scenario created.')
        return super().form_valid(form)


class LogisticsScenarioDetailView(LoginRequiredMixin, DetailView):
    model = LogisticsScenario
    template_name = 'project_controls/logistics/detail.html'
    context_object_name = 'scenario'


class LogisticsScenarioUpdateView(LoginRequiredMixin, UpdateView):
    model = LogisticsScenario
    form_class = LogisticsScenarioForm
    template_name = 'project_controls/logistics/form.html'

    def get_success_url(self):
        return reverse_lazy('project_controls:logistics_detail', kwargs={'pk': self.object.pk})


class LogisticsScenarioDeleteView(AdminRequiredMixin, View):
    def post(self, request, pk):
        get_object_or_404(LogisticsScenario, pk=pk).delete()
        messages.success(request, 'Logistics scenario deleted.')
        return redirect('project_controls:logistics_list')


class LogisticsComparisonView(LoginRequiredMixin, TemplateView):
    template_name = 'project_controls/logistics/comparison.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        projects = Project.objects.filter(status='Active')
        project_id = self.request.GET.get('project')
        selected = projects.filter(pk=project_id).first() if project_id else projects.first()
        scenarios = LogisticsScenario.objects.filter(project=selected) if selected else []
        ctx.update({'projects': projects, 'selected_project': selected, 'scenarios': scenarios})
        return ctx


# ── Import Views ──────────────────────────────────────────────────────────────

class ImportView(LoginRequiredMixin, FormView):
    template_name = 'project_controls/import.html'
    form_class = ImportForm

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['projects'] = Project.objects.filter(status='Active')
        ctx['recent_logs'] = ImportLog.objects.select_related('project', 'imported_by')[:10]
        return ctx

    def form_valid(self, form):
        from .importers import run_import
        project = form.cleaned_data['project']
        import_type = form.cleaned_data['import_type']
        excel_file = form.cleaned_data['excel_file']
        duplicate_action = form.cleaned_data['duplicate_action']
        log = run_import(
            project=project,
            import_type=import_type,
            excel_file=excel_file,
            user=self.request.user,
            duplicate_action=duplicate_action,
        )
        if log.status == 'success':
            messages.success(self.request, f'Import complete: {log.success_rows} rows imported.')
        elif log.status == 'partial':
            messages.warning(self.request, f'Partial import: {log.success_rows} ok, {log.failed_rows} failed.')
        else:
            messages.error(self.request, f'Import failed: {log.error_message[:200]}')
        return redirect('project_controls:import_log_detail', pk=log.pk)


class ImportLogListView(LoginRequiredMixin, ListView):
    model = ImportLog
    template_name = 'project_controls/import_log_list.html'
    context_object_name = 'logs'
    paginate_by = 20


class ImportLogDetailView(LoginRequiredMixin, DetailView):
    model = ImportLog
    template_name = 'project_controls/import_log_detail.html'
    context_object_name = 'log'


# ── Chart Data API ────────────────────────────────────────────────────────────

class RockChartDataView(LoginRequiredMixin, View):
    def get(self, request):
        project_id = request.GET.get('project_id')
        project = get_object_or_404(Project, pk=project_id) if project_id else None
        if not project:
            return JsonResponse({'error': 'project required'}, status=400)
        records = RockDailyRecord.objects.filter(project=project).order_by('record_date')
        labels = [str(r.record_date) for r in records]
        daily_delivered = [float(r.tct_daily_ton) for r in records]
        daily_placed = [float(r.placed_daily_ton) for r in records]
        accum_delivered = [float(r.tct_accum_ton) for r in records]
        accum_placed = [float(r.placed_accum_ton) for r in records]
        barge_totals = {}
        for rec in records:
            for bp in rec.barge_placements.select_related('barge').all():
                k = bp.barge.name
                barge_totals[k] = barge_totals.get(k, 0) + float(bp.quantity_ton)
        return JsonResponse({
            'labels': labels,
            'daily_delivered': daily_delivered,
            'daily_placed': daily_placed,
            'accum_delivered': accum_delivered,
            'accum_placed': accum_placed,
            'barge_totals': barge_totals,
        })


class SandChartDataView(LoginRequiredMixin, View):
    def get(self, request):
        project_id = request.GET.get('project_id')
        project = get_object_or_404(Project, pk=project_id) if project_id else None
        if not project:
            return JsonResponse({'error': 'project required'}, status=400)
        records = SandDailyRecord.objects.filter(project=project).order_by('record_date')
        labels = [str(r.record_date) for r in records]
        return JsonResponse({
            'labels': labels,
            'tct_daily': [float(r.tct_daily_ton) for r in records],
            'mtp3_daily': [float(r.mtp3_daily_ton) for r in records],
            'other_daily': [float(r.oswald_daily_ton) for r in records],
            'other_source_labels': [r.sand_source_display for r in records],
            'total_accum': [float(r.total_accum_ton) for r in records],
            'offshore_daily': [float(r.offshore_daily_ton) for r in records],
            'onshore_daily': [float(r.onshore_daily_ton) for r in records],
            'remaining_tct': [float(r.remaining_tct) for r in records],
            'remaining_mtp3': [float(r.remaining_mtp3) for r in records],
        })
