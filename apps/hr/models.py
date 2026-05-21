from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.accounts.models import User
from apps.projects.models import Project


# ── Employee Master ───────────────────────────────────────────────────────────

class Employee(models.Model):
    EMPLOYMENT_TYPE_CHOICES = [
        ('Staff',    'Staff (Monthly)'),
        ('Daily',    'Daily Worker'),
        ('Hourly',   'Hourly Worker'),
        ('Contract', 'Contract / Subcontract'),
    ]
    STATUS_CHOICES = [
        ('Active',     'Active'),
        ('Inactive',   'Inactive'),
        ('Terminated', 'Terminated'),
    ]
    NATIONALITY_CHOICES = [
        ('Thai',     'Thai'),
        ('Myanmar',  'Myanmar'),
        ('Lao',      'Lao'),
        ('Cambodian','Cambodian'),
        ('Other',    'Other'),
    ]

    employee_no     = models.CharField(max_length=20, unique=True, blank=True)
    user            = models.OneToOneField(User, on_delete=models.SET_NULL,
                                            null=True, blank=True, related_name='employee')
    first_name      = models.CharField(max_length=100)
    last_name       = models.CharField(max_length=100)
    nickname        = models.CharField(max_length=100, blank=True)
    id_card_no      = models.CharField(max_length=50, blank=True)
    nationality     = models.CharField(max_length=20, choices=NATIONALITY_CHOICES, default='Thai')
    date_of_birth   = models.DateField(null=True, blank=True)
    phone           = models.CharField(max_length=20, blank=True)
    email           = models.EmailField(blank=True)

    company         = models.CharField(max_length=200, help_text='Employer / subcontractor company')
    position        = models.CharField(max_length=200)
    category        = models.ForeignKey('manpower.ManpowerCategory', on_delete=models.SET_NULL,
                                         null=True, blank=True)
    employment_type = models.CharField(max_length=20, choices=EMPLOYMENT_TYPE_CHOICES, default='Daily')

    project         = models.ForeignKey(Project, on_delete=models.SET_NULL,
                                         null=True, blank=True, related_name='employees')
    start_date      = models.DateField()
    end_date        = models.DateField(null=True, blank=True)
    status          = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Active')

    photo           = models.ImageField(upload_to='hr/employees/%Y/', blank=True)
    remarks         = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f"{self.employee_no} – {self.full_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def save(self, *args, **kwargs):
        if not self.employee_no:
            last = Employee.objects.order_by('employee_no').last()
            seq = 1
            if last and last.employee_no.startswith('EMP-'):
                try:
                    seq = int(last.employee_no.split('-')[1]) + 1
                except (ValueError, IndexError):
                    seq = Employee.objects.count() + 1
            self.employee_no = f'EMP-{seq:04d}'
        super().save(*args, **kwargs)


# ── Attendance ────────────────────────────────────────────────────────────────

class AttendanceRecord(models.Model):
    STATUS_CHOICES = [
        ('Present',       'Present'),
        ('Absent',        'Absent'),
        ('Late',          'Late'),
        ('HalfDay',       'Half Day'),
        ('Leave',         'On Leave'),
        ('Holiday',       'Public Holiday'),
        ('OfficialLeave', 'Official Leave'),
    ]

    employee      = models.ForeignKey(Employee, on_delete=models.CASCADE,
                                       related_name='attendance_records')
    project       = models.ForeignKey(Project, on_delete=models.SET_NULL,
                                       null=True, blank=True, related_name='attendance_records')
    record_date   = models.DateField()
    status        = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Present')
    time_in       = models.TimeField(null=True, blank=True)
    time_out      = models.TimeField(null=True, blank=True)
    overtime_hours = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    remarks       = models.CharField(max_length=300, blank=True)
    recorded_by   = models.ForeignKey(User, on_delete=models.SET_NULL,
                                       null=True, related_name='recorded_attendance')
    created_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-record_date', 'employee__last_name']
        unique_together = ('employee', 'record_date')

    def __str__(self):
        return f"{self.employee} – {self.record_date} – {self.status}"

    @property
    def hours_worked(self):
        if self.time_in and self.time_out:
            from datetime import datetime, date
            dt_in  = datetime.combine(date.today(), self.time_in)
            dt_out = datetime.combine(date.today(), self.time_out)
            if dt_out <= dt_in:
                dt_out += timedelta(days=1)
            return round((dt_out - dt_in).seconds / 3600, 2)
        return None

    @property
    def status_color(self):
        return {
            'Present':       'success',
            'Absent':        'danger',
            'Late':          'warning',
            'HalfDay':       'info',
            'Leave':         'primary',
            'Holiday':       'secondary',
            'OfficialLeave': 'dark',
        }.get(self.status, 'secondary')


# ── Leave Request ─────────────────────────────────────────────────────────────

class LeaveRequest(models.Model):
    LEAVE_TYPE_CHOICES = [
        ('Annual',    'Annual Leave'),
        ('Sick',      'Sick Leave'),
        ('Personal',  'Personal Leave'),
        ('Maternity', 'Maternity Leave'),
        ('Other',     'Other'),
    ]
    STATUS_CHOICES = [
        ('Draft',     'Draft'),
        ('Submitted', 'Submitted'),
        ('Approved',  'Approved'),
        ('Rejected',  'Rejected'),
        ('Cancelled', 'Cancelled'),
    ]

    employee     = models.ForeignKey(Employee, on_delete=models.CASCADE,
                                      related_name='leave_requests')
    leave_type   = models.CharField(max_length=20, choices=LEAVE_TYPE_CHOICES)
    start_date   = models.DateField()
    end_date     = models.DateField()
    reason       = models.TextField()
    status       = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Draft')
    approved_by  = models.ForeignKey(User, on_delete=models.SET_NULL,
                                      null=True, blank=True, related_name='approved_leaves')
    rejection_reason = models.TextField(blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    decided_at   = models.DateTimeField(null=True, blank=True)
    created_by   = models.ForeignKey(User, on_delete=models.SET_NULL,
                                      null=True, related_name='created_leaves')
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.employee} – {self.get_leave_type_display()} – {self.start_date}"

    def clean(self):
        if self.end_date and self.start_date and self.end_date < self.start_date:
            raise ValidationError('End date cannot be before start date.')

    @property
    def days(self):
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days + 1
        return 0

    @property
    def status_color(self):
        return {
            'Draft':     'secondary',
            'Submitted': 'info',
            'Approved':  'success',
            'Rejected':  'danger',
            'Cancelled': 'dark',
        }.get(self.status, 'secondary')


# ── Overtime Request ──────────────────────────────────────────────────────────

class OvertimeRequest(models.Model):
    STATUS_CHOICES = [
        ('Draft',    'Draft'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]

    employee      = models.ForeignKey(Employee, on_delete=models.CASCADE,
                                       related_name='overtime_requests')
    project       = models.ForeignKey(Project, on_delete=models.SET_NULL,
                                       null=True, blank=True, related_name='overtime_requests')
    ot_date       = models.DateField()
    planned_hours = models.DecimalField(max_digits=4, decimal_places=2)
    actual_hours  = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    reason        = models.TextField()
    status        = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Draft')
    approved_by   = models.ForeignKey(User, on_delete=models.SET_NULL,
                                       null=True, blank=True, related_name='approved_overtime')
    rejection_reason = models.TextField(blank=True)
    requested_by  = models.ForeignKey(User, on_delete=models.SET_NULL,
                                       null=True, related_name='requested_overtime')
    created_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-ot_date']

    def __str__(self):
        return f"{self.employee} – OT {self.ot_date} – {self.planned_hours}h"

    @property
    def status_color(self):
        return {'Draft': 'secondary', 'Approved': 'success', 'Rejected': 'danger'}.get(self.status, 'secondary')
