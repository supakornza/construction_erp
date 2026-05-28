from datetime import date, timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models

from apps.accounts.models import User
from apps.equipment.models import Equipment
from apps.projects.models import Project


# ── PM Schedule Definition ────────────────────────────────────────────────────

class MaintenanceSchedule(models.Model):
    INTERVAL_TYPE_CHOICES = [
        ('Hours',  'Every X Running Hours'),
        ('Days',   'Every X Days'),
        ('Weeks',  'Every X Weeks'),
        ('Months', 'Every X Months'),
    ]
    WORK_TYPE_CHOICES = [
        ('Preventive', 'Preventive Maintenance (PM)'),
        ('Inspection', 'Periodic Inspection'),
        ('Overhaul',   'Overhaul / Major Service'),
        ('Calibration','Calibration'),
        ('Other',      'Other'),
    ]

    equipment       = models.ForeignKey(Equipment, on_delete=models.CASCADE,
                                         related_name='maintenance_schedules')
    title           = models.CharField(max_length=300)
    work_type       = models.CharField(max_length=20, choices=WORK_TYPE_CHOICES, default='Preventive')
    description     = models.TextField(blank=True)

    interval_type   = models.CharField(max_length=10, choices=INTERVAL_TYPE_CHOICES, default='Hours')
    interval_value  = models.PositiveIntegerField(help_text='Repeat every N hours/days/weeks/months')

    # Tracking last service
    last_done_date  = models.DateField(null=True, blank=True)
    last_done_hours = models.DecimalField(max_digits=10, decimal_places=2,
                                           null=True, blank=True,
                                           help_text='Running hours at last service')

    # Next due (stored to allow manual override)
    next_due_date   = models.DateField(null=True, blank=True)
    next_due_hours  = models.DecimalField(max_digits=10, decimal_places=2,
                                           null=True, blank=True)

    is_active       = models.BooleanField(default=True)
    created_by      = models.ForeignKey(User, on_delete=models.SET_NULL,
                                         null=True, related_name='created_schedules')
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['equipment__name', 'title']

    def __str__(self):
        return f"{self.equipment} — {self.title}"

    def compute_next_due(self):
        """Recalculate next_due_date from last_done_date + interval."""
        if not self.last_done_date:
            return
        base = self.last_done_date
        iv   = self.interval_value or 1
        if self.interval_type == 'Hours':
            # For hour-based, compute a rough calendar date (250 hours/month approx)
            self.next_due_date = base + timedelta(days=max(1, int(iv / 10)))
            if self.last_done_hours is not None:
                self.next_due_hours = self.last_done_hours + Decimal(str(iv))
        elif self.interval_type == 'Days':
            self.next_due_date = base + timedelta(days=iv)
        elif self.interval_type == 'Weeks':
            self.next_due_date = base + timedelta(weeks=iv)
        elif self.interval_type == 'Months':
            month = base.month - 1 + iv
            year  = base.year + month // 12
            month = month % 12 + 1
            from calendar import monthrange
            day = min(base.day, monthrange(year, month)[1])
            self.next_due_date = date(year, month, day)

    @property
    def is_overdue(self):
        if self.next_due_date and self.next_due_date < date.today():
            return True
        return False

    @property
    def days_until_due(self):
        if self.next_due_date:
            return (self.next_due_date - date.today()).days
        return None

    @property
    def status_label(self):
        d = self.days_until_due
        if d is None:
            return 'Not Scheduled', 'secondary'
        if d < 0:
            return f'Overdue ({abs(d)}d)', 'danger'
        if d == 0:
            return 'Due Today', 'danger'
        if d <= 7:
            return f'Due in {d}d', 'warning'
        if d <= 30:
            return f'Due in {d}d', 'info'
        return f'Due in {d}d', 'success'


# ── Work Order ────────────────────────────────────────────────────────────────

class MaintenanceWorkOrder(models.Model):
    WORK_TYPE_CHOICES = [
        ('Preventive',  'Preventive (Scheduled)'),
        ('Corrective',  'Corrective (Breakdown)'),
        ('Emergency',   'Emergency'),
        ('Inspection',  'Periodic Inspection'),
        ('Overhaul',    'Overhaul'),
    ]
    PRIORITY_CHOICES = [
        ('Low',      'Low'),
        ('Medium',   'Medium'),
        ('High',     'High'),
        ('Critical', 'Critical'),
    ]
    STATUS_CHOICES = [
        ('Open',        'Open'),
        ('InProgress',  'In Progress'),
        ('OnHold',      'On Hold'),
        ('Completed',   'Completed'),
        ('Cancelled',   'Cancelled'),
    ]

    wo_no        = models.CharField(max_length=20, unique=True, blank=True)
    equipment    = models.ForeignKey(Equipment, on_delete=models.CASCADE,
                                      related_name='work_orders')
    schedule     = models.ForeignKey(MaintenanceSchedule, on_delete=models.SET_NULL,
                                      null=True, blank=True, related_name='work_orders')
    project      = models.ForeignKey(Project, on_delete=models.SET_NULL,
                                      null=True, blank=True, related_name='maintenance_work_orders')

    title        = models.CharField(max_length=300)
    work_type    = models.CharField(max_length=20, choices=WORK_TYPE_CHOICES)
    priority     = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='Medium')
    status       = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Open')

    description  = models.TextField(blank=True)
    planned_date = models.DateField()

    actual_start     = models.DateTimeField(null=True, blank=True)
    actual_end       = models.DateTimeField(null=True, blank=True)
    running_hours_at_service = models.DecimalField(max_digits=10, decimal_places=2,
                                                    null=True, blank=True,
                                                    help_text='Equipment running hours when service was done')

    assigned_to  = models.CharField(max_length=200, blank=True,
                                     help_text='Technician / workshop name')
    findings     = models.TextField(blank=True, help_text='What was found during inspection/repair')
    actions_taken = models.TextField(blank=True)
    cost         = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    next_service_due_date  = models.DateField(null=True, blank=True)
    next_service_due_hours = models.DecimalField(max_digits=10, decimal_places=2,
                                                  null=True, blank=True)

    completed_by = models.ForeignKey(User, on_delete=models.SET_NULL,
                                      null=True, blank=True, related_name='completed_wo')
    created_by   = models.ForeignKey(User, on_delete=models.SET_NULL,
                                      null=True, related_name='created_wo')
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-planned_date', 'priority']

    def __str__(self):
        return f"{self.wo_no} — {self.equipment} — {self.title}"

    def save(self, *args, **kwargs):
        if not self.wo_no:
            last = MaintenanceWorkOrder.objects.order_by('wo_no').last()
            seq  = 1
            if last and last.wo_no.startswith('WO-'):
                try:
                    seq = int(last.wo_no.split('-')[1]) + 1
                except (ValueError, IndexError):
                    seq = MaintenanceWorkOrder.objects.count() + 1
            self.wo_no = f'WO-{seq:04d}'
        super().save(*args, **kwargs)

    @property
    def is_overdue(self):
        return self.status not in ('Completed', 'Cancelled') and self.planned_date < date.today()

    @property
    def duration_hours(self):
        if self.actual_start and self.actual_end:
            delta = self.actual_end - self.actual_start
            return round(delta.total_seconds() / 3600, 2)
        return None

    @property
    def priority_color(self):
        return {'Low': 'secondary', 'Medium': 'info',
                'High': 'warning', 'Critical': 'danger'}.get(self.priority, 'secondary')

    @property
    def status_color(self):
        return {'Open': 'primary', 'InProgress': 'warning', 'OnHold': 'secondary',
                'Completed': 'success', 'Cancelled': 'dark'}.get(self.status, 'secondary')


# ── Parts Used ────────────────────────────────────────────────────────────────

class MaintenancePart(models.Model):
    work_order  = models.ForeignKey(MaintenanceWorkOrder, on_delete=models.CASCADE,
                                     related_name='parts')
    part_name   = models.CharField(max_length=200)
    part_no     = models.CharField(max_length=100, blank=True)
    quantity    = models.DecimalField(max_digits=8, decimal_places=2, default=1)
    unit        = models.CharField(max_length=50, blank=True)
    unit_cost   = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        ordering = ['part_name']

    def __str__(self):
        return f"{self.part_name} × {self.quantity}"

    @property
    def total_cost(self):
        return self.quantity * self.unit_cost
