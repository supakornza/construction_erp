from datetime import date, timedelta

from django.contrib import messages
from django.db import transaction
from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.views.generic import (
    ListView, CreateView, DetailView, UpdateView, TemplateView, View
)

from apps.accounts.mixins import MaintenanceViewMixin, MaintenanceWriteMixin
from apps.equipment.models import Equipment
from apps.projects.models import Project
from .models import MaintenanceSchedule, MaintenanceWorkOrder, MaintenancePart
from .forms import (
    MaintenanceScheduleForm, MaintenanceWorkOrderForm,
    WorkOrderCompleteForm, MaintenancePartFormSet,
)


# ── Dashboard ─────────────────────────────────────────────────────────────────

class MaintenanceDashboardView(MaintenanceViewMixin, TemplateView):
    template_name = 'maintenance/dashboard.html'

    def get_context_data(self, **kwargs):
        ctx  = super().get_context_data(**kwargs)
        today = date.today()

        ctx['open_wo']      = MaintenanceWorkOrder.objects.filter(
            status__in=('Open', 'InProgress')).count()
        ctx['overdue_wo']   = MaintenanceWorkOrder.objects.filter(
            status__in=('Open', 'InProgress'), planned_date__lt=today).count()
        ctx['due_this_week'] = MaintenanceSchedule.objects.filter(
            is_active=True,
            next_due_date__range=(today, today + timedelta(days=7))).count()
        ctx['completed_this_month'] = MaintenanceWorkOrder.objects.filter(
            status='Completed',
            actual_end__year=today.year,
            actual_end__month=today.month).count()

        ctx['overdue_schedules'] = MaintenanceSchedule.objects.filter(
            is_active=True, next_due_date__lt=today
        ).select_related('equipment').order_by('next_due_date')[:10]

        ctx['upcoming_schedules'] = MaintenanceSchedule.objects.filter(
            is_active=True,
            next_due_date__range=(today, today + timedelta(days=30))
        ).select_related('equipment').order_by('next_due_date')[:10]

        ctx['open_work_orders'] = MaintenanceWorkOrder.objects.filter(
            status__in=('Open', 'InProgress')
        ).select_related('equipment', 'project').order_by('planned_date')[:10]

        ctx['projects'] = Project.objects.filter(status='Active')
        return ctx


# ── PM Schedule ───────────────────────────────────────────────────────────────

class ScheduleListView(MaintenanceViewMixin, ListView):
    model               = MaintenanceSchedule
    template_name       = 'maintenance/schedule_list.html'
    context_object_name = 'schedules'
    paginate_by         = 25

    def get_queryset(self):
        qs = MaintenanceSchedule.objects.select_related('equipment__category', 'equipment__project')
        equipment_id = self.request.GET.get('equipment')
        work_type    = self.request.GET.get('work_type')
        overdue_only = self.request.GET.get('overdue')
        if equipment_id:
            qs = qs.filter(equipment_id=equipment_id)
        if work_type:
            qs = qs.filter(work_type=work_type)
        if overdue_only:
            qs = qs.filter(next_due_date__lt=date.today(), is_active=True)
        return qs.filter(is_active=True)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['equipment_list'] = Equipment.objects.filter(status='Active').order_by('name')
        ctx['work_type_choices'] = MaintenanceSchedule.WORK_TYPE_CHOICES
        ctx['today'] = date.today()
        return ctx


class ScheduleCreateView(MaintenanceWriteMixin, CreateView):
    model         = MaintenanceSchedule
    form_class    = MaintenanceScheduleForm
    template_name = 'maintenance/schedule_form.html'

    def get_initial(self):
        initial = super().get_initial()
        eq_id = self.request.GET.get('equipment')
        if eq_id:
            initial['equipment'] = eq_id
        return initial

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        obj = form.save(commit=False)
        obj.compute_next_due()
        obj.save()
        messages.success(self.request, f'PM schedule created: {obj.title}')
        return redirect(reverse('maintenance:schedule_list'))


class ScheduleUpdateView(MaintenanceWriteMixin, UpdateView):
    model         = MaintenanceSchedule
    form_class    = MaintenanceScheduleForm
    template_name = 'maintenance/schedule_form.html'

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.compute_next_due()
        obj.save()
        messages.success(self.request, 'Schedule updated.')
        return redirect(reverse('maintenance:schedule_list'))


# ── Work Orders ───────────────────────────────────────────────────────────────

class WorkOrderListView(MaintenanceViewMixin, ListView):
    model               = MaintenanceWorkOrder
    template_name       = 'maintenance/wo_list.html'
    context_object_name = 'work_orders'
    paginate_by         = 20

    def get_queryset(self):
        qs = MaintenanceWorkOrder.objects.select_related(
            'equipment', 'project', 'created_by', 'completed_by'
        )
        status      = self.request.GET.get('status')
        work_type   = self.request.GET.get('work_type')
        priority    = self.request.GET.get('priority')
        project_id  = self.request.GET.get('project')
        equipment_id = self.request.GET.get('equipment')
        if status:
            qs = qs.filter(status=status)
        if work_type:
            qs = qs.filter(work_type=work_type)
        if priority:
            qs = qs.filter(priority=priority)
        if project_id:
            qs = qs.filter(project_id=project_id)
        if equipment_id:
            qs = qs.filter(equipment_id=equipment_id)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['status_choices']    = MaintenanceWorkOrder.STATUS_CHOICES
        ctx['work_type_choices'] = MaintenanceWorkOrder.WORK_TYPE_CHOICES
        ctx['priority_choices']  = MaintenanceWorkOrder.PRIORITY_CHOICES
        ctx['projects']          = Project.objects.filter(status='Active')
        ctx['equipment_list']    = Equipment.objects.filter(status='Active').order_by('name')
        ctx['today']             = date.today()
        return ctx


class WorkOrderCreateView(MaintenanceWriteMixin, CreateView):
    model         = MaintenanceWorkOrder
    form_class    = MaintenanceWorkOrderForm
    template_name = 'maintenance/wo_form.html'

    def get_initial(self):
        initial = super().get_initial()
        eq_id      = self.request.GET.get('equipment')
        sched_id   = self.request.GET.get('schedule')
        if eq_id:
            initial['equipment'] = eq_id
        if sched_id:
            sched = MaintenanceSchedule.objects.filter(pk=sched_id).first()
            if sched:
                initial['schedule']    = sched_id
                initial['equipment']   = sched.equipment_id
                initial['title']       = sched.title
                initial['work_type']   = sched.work_type
                initial['planned_date'] = sched.next_due_date or date.today()
        initial.setdefault('planned_date', date.today())
        return initial

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        self.object = form.save()
        messages.success(self.request, f'Work Order {self.object.wo_no} created.')
        return redirect(reverse('maintenance:wo_detail', kwargs={'pk': self.object.pk}))


class WorkOrderDetailView(MaintenanceViewMixin, DetailView):
    model               = MaintenanceWorkOrder
    template_name       = 'maintenance/wo_detail.html'
    context_object_name = 'wo'

    def get_queryset(self):
        return MaintenanceWorkOrder.objects.select_related(
            'equipment', 'schedule', 'project',
            'completed_by', 'created_by',
        ).prefetch_related('parts')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['parts_total'] = sum(p.total_cost for p in self.object.parts.all())
        return ctx


class WorkOrderUpdateView(MaintenanceWriteMixin, UpdateView):
    model         = MaintenanceWorkOrder
    form_class    = MaintenanceWorkOrderForm
    template_name = 'maintenance/wo_form.html'

    def dispatch(self, request, *args, **kwargs):
        obj = get_object_or_404(MaintenanceWorkOrder, pk=kwargs['pk'])
        if obj.status == 'Completed':
            messages.error(request, 'Completed work orders cannot be edited.')
            return redirect('maintenance:wo_detail', pk=obj.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        messages.success(self.request, 'Work order updated.')
        return reverse('maintenance:wo_detail', kwargs={'pk': self.object.pk})


class WorkOrderStartView(MaintenanceWriteMixin, View):
    def post(self, request, pk):
        wo = get_object_or_404(MaintenanceWorkOrder, pk=pk)
        if wo.status == 'Open':
            from django.utils import timezone
            wo.status       = 'InProgress'
            wo.actual_start = timezone.now()
            wo.save(update_fields=['status', 'actual_start'])
            messages.success(request, f'{wo.wo_no} started.')
        return redirect('maintenance:wo_detail', pk=pk)


class WorkOrderCompleteView(MaintenanceWriteMixin, View):
    template_name = 'maintenance/wo_complete.html'

    def get(self, request, pk):
        wo   = get_object_or_404(MaintenanceWorkOrder, pk=pk)
        form = WorkOrderCompleteForm(instance=wo)
        fs   = MaintenancePartFormSet(instance=wo)
        return self._render(request, wo, form, fs)

    def post(self, request, pk):
        wo   = get_object_or_404(MaintenanceWorkOrder, pk=pk)
        form = WorkOrderCompleteForm(request.POST, instance=wo)
        fs   = MaintenancePartFormSet(request.POST, instance=wo)

        if form.is_valid() and fs.is_valid():
            with transaction.atomic():
                wo_obj = form.save(commit=False)
                wo_obj.status       = 'Completed'
                wo_obj.completed_by = request.user
                if not wo_obj.actual_end:
                    from django.utils import timezone
                    wo_obj.actual_end = timezone.now()
                wo_obj.save()
                fs.save()

                # Update linked PM schedule
                if wo_obj.schedule:
                    sched = wo_obj.schedule
                    sched.last_done_date  = wo_obj.actual_end.date() if wo_obj.actual_end else date.today()
                    sched.last_done_hours = wo_obj.running_hours_at_service
                    if wo_obj.next_service_due_date:
                        sched.next_due_date  = wo_obj.next_service_due_date
                        sched.next_due_hours = wo_obj.next_service_due_hours
                    else:
                        sched.compute_next_due()
                    sched.save()

                # Update cost = parts total + labour
                parts_total = sum(p.total_cost for p in wo_obj.parts.all())
                if parts_total > 0 and wo_obj.cost == 0:
                    wo_obj.cost = parts_total
                    wo_obj.save(update_fields=['cost'])

            messages.success(request, f'{wo_obj.wo_no} completed.')
            return redirect('maintenance:wo_detail', pk=pk)

        return self._render(request, wo, form, fs)

    def _render(self, request, wo, form, fs):
        from django.shortcuts import render
        return render(request, self.template_name, {'wo': wo, 'form': form, 'part_formset': fs})


class WorkOrderCancelView(MaintenanceWriteMixin, View):
    def post(self, request, pk):
        wo = get_object_or_404(MaintenanceWorkOrder, pk=pk)
        if wo.status not in ('Completed', 'Cancelled'):
            wo.status = 'Cancelled'
            wo.save(update_fields=['status'])
            messages.warning(request, f'{wo.wo_no} cancelled.')
        return redirect('maintenance:wo_detail', pk=pk)
