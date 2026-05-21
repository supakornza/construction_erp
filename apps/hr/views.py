from datetime import date, timedelta

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.views.generic import (
    ListView, CreateView, DetailView, UpdateView, DeleteView, View, TemplateView
)

from apps.accounts.mixins import HRViewMixin, HRWriteMixin, HRApproveMixin
from apps.notifications.utils import notify
from apps.projects.models import Project
from .models import Employee, AttendanceRecord, LeaveRequest, OvertimeRequest
from .forms import (
    EmployeeForm, AttendanceRecordForm, BulkAttendanceForm,
    LeaveRequestForm, OvertimeRequestForm, LeaveDecisionForm, OTActualHoursForm,
)


# ── Dashboard ─────────────────────────────────────────────────────────────────

class HRDashboardView(HRViewMixin, TemplateView):
    template_name = 'hr/dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        today = date.today()
        week_start = today - timedelta(days=today.weekday())

        ctx['total_employees']  = Employee.objects.filter(status='Active').count()
        ctx['present_today']    = AttendanceRecord.objects.filter(
            record_date=today, status='Present').count()
        ctx['absent_today']     = AttendanceRecord.objects.filter(
            record_date=today, status='Absent').count()
        ctx['pending_leaves']   = LeaveRequest.objects.filter(status='Submitted').count()
        ctx['pending_ot']       = OvertimeRequest.objects.filter(status='Draft').count()

        ctx['recent_attendance'] = AttendanceRecord.objects.filter(
            record_date__gte=week_start
        ).select_related('employee', 'project').order_by('-record_date')[:20]

        ctx['pending_leave_list'] = LeaveRequest.objects.filter(
            status='Submitted'
        ).select_related('employee')[:10]

        ctx['projects'] = Project.objects.filter(status='Active')
        return ctx


# ── Employee ──────────────────────────────────────────────────────────────────

class EmployeeListView(HRViewMixin, ListView):
    model = Employee
    template_name = 'hr/employee_list.html'
    context_object_name = 'employees'
    paginate_by = 25

    def get_queryset(self):
        qs = Employee.objects.select_related('project', 'category')
        project_id = self.request.GET.get('project')
        status     = self.request.GET.get('status', 'Active')
        search     = self.request.GET.get('q')
        if project_id:
            qs = qs.filter(project_id=project_id)
        if status:
            qs = qs.filter(status=status)
        if search:
            qs = qs.filter(
                Q(first_name__icontains=search) | Q(last_name__icontains=search) |
                Q(employee_no__icontains=search) | Q(company__icontains=search)
            )
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['projects']       = Project.objects.filter(status='Active')
        ctx['status_choices'] = Employee.STATUS_CHOICES
        return ctx


class EmployeeCreateView(HRWriteMixin, CreateView):
    model         = Employee
    form_class    = EmployeeForm
    template_name = 'hr/employee_form.html'

    def get_success_url(self):
        messages.success(self.request, f'Employee {self.object.employee_no} created.')
        return reverse('hr:employee_detail', kwargs={'pk': self.object.pk})


class EmployeeDetailView(HRViewMixin, DetailView):
    model               = Employee
    template_name       = 'hr/employee_detail.html'
    context_object_name = 'employee'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        today = date.today()
        month_start = today.replace(day=1)
        ctx['attendance_this_month'] = self.object.attendance_records.filter(
            record_date__gte=month_start
        ).order_by('-record_date')[:31]
        ctx['leave_history']  = self.object.leave_requests.order_by('-start_date')[:10]
        ctx['ot_history']     = self.object.overtime_requests.order_by('-ot_date')[:10]
        present = self.object.attendance_records.filter(
            record_date__gte=month_start, status__in=('Present', 'Late')
        ).count()
        ctx['days_present_month'] = present
        return ctx


class EmployeeUpdateView(HRWriteMixin, UpdateView):
    model         = Employee
    form_class    = EmployeeForm
    template_name = 'hr/employee_form.html'

    def get_success_url(self):
        messages.success(self.request, 'Employee updated.')
        return reverse('hr:employee_detail', kwargs={'pk': self.object.pk})


# ── Attendance ────────────────────────────────────────────────────────────────

class AttendanceDashboardView(HRViewMixin, View):
    template_name = 'hr/attendance_dashboard.html'

    def get(self, request):
        record_date = request.GET.get('date')
        project_id  = request.GET.get('project')
        try:
            view_date = date.fromisoformat(record_date) if record_date else date.today()
        except ValueError:
            view_date = date.today()

        employees = Employee.objects.filter(status='Active').select_related('category', 'project')
        if project_id:
            employees = employees.filter(project_id=project_id)

        attendance_map = {
            a.employee_id: a
            for a in AttendanceRecord.objects.filter(
                record_date=view_date,
                employee__in=employees
            ).select_related('employee')
        }

        rows = []
        for emp in employees:
            rows.append({
                'employee':   emp,
                'attendance': attendance_map.get(emp.pk),
            })

        summary = {
            'present': sum(1 for r in rows if r['attendance'] and r['attendance'].status == 'Present'),
            'absent':  sum(1 for r in rows if r['attendance'] and r['attendance'].status == 'Absent'),
            'leave':   sum(1 for r in rows if r['attendance'] and r['attendance'].status == 'Leave'),
            'no_record': sum(1 for r in rows if not r['attendance']),
        }

        return render(request, self.template_name, {
            'rows':       rows,
            'view_date':  view_date,
            'summary':    summary,
            'projects':   Project.objects.filter(status='Active'),
            'project_id': project_id,
            'prev_date':  view_date - timedelta(days=1),
            'next_date':  view_date + timedelta(days=1),
            'status_choices': AttendanceRecord.STATUS_CHOICES,
        })


class AttendanceQuickSaveView(HRWriteMixin, View):
    """AJAX/form POST to set status for a single employee on a given date."""

    def post(self, request):
        employee_id = request.POST.get('employee_id')
        record_date = request.POST.get('record_date')
        status      = request.POST.get('status')
        time_in     = request.POST.get('time_in') or None
        time_out    = request.POST.get('time_out') or None
        ot_hours    = request.POST.get('overtime_hours') or 0

        employee = get_object_or_404(Employee, pk=employee_id)
        try:
            rec_date = date.fromisoformat(record_date)
        except (ValueError, TypeError):
            messages.error(request, 'Invalid date.')
            return redirect(request.META.get('HTTP_REFERER', 'hr:attendance_dashboard'))

        AttendanceRecord.objects.update_or_create(
            employee=employee, record_date=rec_date,
            defaults={
                'status':          status,
                'time_in':         time_in,
                'time_out':        time_out,
                'overtime_hours':  ot_hours,
                'project':         employee.project,
                'recorded_by':     request.user,
            }
        )
        redirect_url = reverse('hr:attendance_dashboard') + f'?date={record_date}'
        if request.POST.get('project'):
            redirect_url += f'&project={request.POST.get("project")}'
        return redirect(redirect_url)


class AttendanceRecordCreateView(HRWriteMixin, CreateView):
    model         = AttendanceRecord
    form_class    = AttendanceRecordForm
    template_name = 'hr/attendance_form.html'

    def form_valid(self, form):
        form.instance.recorded_by = self.request.user
        messages.success(self.request, 'Attendance recorded.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('hr:attendance_dashboard') + f'?date={self.object.record_date}'


class AttendanceRecordUpdateView(HRWriteMixin, UpdateView):
    model         = AttendanceRecord
    form_class    = AttendanceRecordForm
    template_name = 'hr/attendance_form.html'

    def get_success_url(self):
        messages.success(self.request, 'Attendance updated.')
        return reverse('hr:attendance_dashboard') + f'?date={self.object.record_date}'


# ── Leave Requests ────────────────────────────────────────────────────────────

class LeaveListView(HRViewMixin, ListView):
    model               = LeaveRequest
    template_name       = 'hr/leave_list.html'
    context_object_name = 'leaves'
    paginate_by         = 20

    def get_queryset(self):
        qs = LeaveRequest.objects.select_related('employee', 'approved_by')
        status     = self.request.GET.get('status')
        project_id = self.request.GET.get('project')
        if status:
            qs = qs.filter(status=status)
        if project_id:
            qs = qs.filter(employee__project_id=project_id)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['status_choices'] = LeaveRequest.STATUS_CHOICES
        ctx['projects']       = Project.objects.filter(status='Active')
        return ctx


class LeaveRequestCreateView(HRWriteMixin, CreateView):
    model         = LeaveRequest
    form_class    = LeaveRequestForm
    template_name = 'hr/leave_form.html'
    success_url   = reverse_lazy('hr:leave_list')

    def form_valid(self, form):
        form.instance.created_by  = self.request.user
        form.instance.status      = 'Submitted'
        form.instance.submitted_at = timezone.now()
        messages.success(self.request, 'Leave request submitted.')
        return super().form_valid(form)


class LeaveRequestDetailView(HRViewMixin, DetailView):
    model               = LeaveRequest
    template_name       = 'hr/leave_detail.html'
    context_object_name = 'leave'


class LeaveApproveView(HRApproveMixin, View):
    def post(self, request, pk):
        leave = get_object_or_404(LeaveRequest, pk=pk)
        if leave.status != 'Submitted':
            messages.error(request, 'Only Submitted requests can be approved.')
        else:
            leave.status      = 'Approved'
            leave.approved_by = request.user
            leave.decided_at  = timezone.now()
            leave.save(update_fields=['status', 'approved_by', 'decided_at'])
            messages.success(request, f'Leave approved for {leave.employee.full_name}.')
            if leave.employee.user:
                notify(leave.employee.user, 'leave_approved',
                       f'Leave Request Approved',
                       f'Your {leave.get_leave_type_display()} leave ({leave.days} day(s)) has been approved.',
                       reverse('hr:leave_detail', kwargs={'pk': leave.pk}))
        return redirect('hr:leave_detail', pk=pk)


class LeaveRejectView(HRApproveMixin, View):
    def get(self, request, pk):
        leave = get_object_or_404(LeaveRequest, pk=pk)
        return render(request, 'hr/leave_reject.html', {'leave': leave, 'form': LeaveDecisionForm()})

    def post(self, request, pk):
        leave = get_object_or_404(LeaveRequest, pk=pk)
        form  = LeaveDecisionForm(request.POST)
        if not form.is_valid():
            return render(request, 'hr/leave_reject.html', {'leave': leave, 'form': form})
        if leave.status != 'Submitted':
            messages.error(request, 'Only Submitted requests can be rejected.')
        else:
            leave.status           = 'Rejected'
            leave.approved_by      = request.user
            leave.rejection_reason = form.cleaned_data.get('rejection_reason', '')
            leave.decided_at       = timezone.now()
            leave.save(update_fields=['status', 'approved_by', 'rejection_reason', 'decided_at'])
            messages.warning(request, f'Leave rejected for {leave.employee.full_name}.')
            if leave.employee.user:
                notify(leave.employee.user, 'leave_rejected',
                       f'Leave Request Rejected',
                       f'Your {leave.get_leave_type_display()} leave request has been rejected.',
                       reverse('hr:leave_detail', kwargs={'pk': leave.pk}))
        return redirect('hr:leave_detail', pk=pk)


# ── Overtime Requests ─────────────────────────────────────────────────────────

class OvertimeListView(HRViewMixin, ListView):
    model               = OvertimeRequest
    template_name       = 'hr/ot_list.html'
    context_object_name = 'ot_requests'
    paginate_by         = 20

    def get_queryset(self):
        qs = OvertimeRequest.objects.select_related('employee', 'project', 'approved_by')
        status     = self.request.GET.get('status')
        project_id = self.request.GET.get('project')
        if status:
            qs = qs.filter(status=status)
        if project_id:
            qs = qs.filter(project_id=project_id)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['status_choices'] = OvertimeRequest.STATUS_CHOICES
        ctx['projects']       = Project.objects.filter(status='Active')
        return ctx


class OvertimeRequestCreateView(HRWriteMixin, CreateView):
    model         = OvertimeRequest
    form_class    = OvertimeRequestForm
    template_name = 'hr/ot_form.html'
    success_url   = reverse_lazy('hr:ot_list')

    def form_valid(self, form):
        form.instance.requested_by = self.request.user
        messages.success(self.request, 'OT request submitted.')
        return super().form_valid(form)


class OvertimeApproveView(HRApproveMixin, View):
    def post(self, request, pk):
        ot = get_object_or_404(OvertimeRequest, pk=pk)
        if ot.status != 'Draft':
            messages.error(request, 'Only Draft OT requests can be approved.')
        else:
            ot.status      = 'Approved'
            ot.approved_by = request.user
            ot.save(update_fields=['status', 'approved_by'])
            messages.success(request, f'OT approved for {ot.employee.full_name}.')
        return redirect('hr:ot_list')


class OvertimeRejectView(HRApproveMixin, View):
    def post(self, request, pk):
        ot = get_object_or_404(OvertimeRequest, pk=pk)
        if ot.status != 'Draft':
            messages.error(request, 'Only Draft OT requests can be rejected.')
        else:
            ot.status           = 'Rejected'
            ot.approved_by      = request.user
            ot.rejection_reason = request.POST.get('rejection_reason', '')
            ot.save(update_fields=['status', 'approved_by', 'rejection_reason'])
            messages.warning(request, f'OT rejected for {ot.employee.full_name}.')
        return redirect('hr:ot_list')
