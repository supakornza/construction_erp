from django.conf import settings
from django.db import models

from apps.boq.models import BOQItem
from apps.projects.models import Project


class InspectionRequest(models.Model):
    STATUS_DRAFT = 'Draft'
    STATUS_SUBMITTED = 'Submitted'
    STATUS_APPROVED = 'Approved'
    STATUS_REJECTED = 'Rejected'
    STATUS_CLOSED = 'Closed'
    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_SUBMITTED, 'Submitted'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
        (STATUS_CLOSED, 'Closed'),
    ]

    RESULT_PENDING = 'Pending'
    RESULT_PASS = 'Pass'
    RESULT_FAIL = 'Fail'
    RESULT_CONDITIONAL = 'Conditional'
    RESULT_CHOICES = [
        (RESULT_PENDING, 'Pending'),
        (RESULT_PASS, 'Pass'),
        (RESULT_FAIL, 'Fail'),
        (RESULT_CONDITIONAL, 'Conditional'),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='quality_inspections')
    boq_item = models.ForeignKey(
        BOQItem, on_delete=models.SET_NULL, null=True, blank=True, related_name='quality_inspections'
    )
    work_package = models.CharField(max_length=200, blank=True)
    inspection_date = models.DateField()
    location = models.CharField(max_length=200)
    station_or_chainage = models.CharField(max_length=100, blank=True)
    inspection_type = models.CharField(max_length=100)
    description = models.TextField()
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='requested_quality_inspections',
    )
    inspected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='inspected_quality_inspections',
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    result = models.CharField(max_length=20, choices=RESULT_CHOICES, default=RESULT_PENDING)
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-inspection_date', '-created_at']
        indexes = [
            models.Index(fields=['project'], name='quality_ir_project_idx'),
            models.Index(fields=['status'], name='quality_ir_status_idx'),
            models.Index(fields=['inspection_date'], name='quality_ir_date_idx'),
            models.Index(fields=['project', 'status'], name='quality_ir_proj_status_idx'),
        ]

    def __str__(self):
        return f'{self.project.contract_no} - {self.inspection_type} - {self.inspection_date}'


class QualityCheckpoint(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='quality_checkpoints')
    boq_item = models.ForeignKey(
        BOQItem, on_delete=models.SET_NULL, null=True, blank=True, related_name='quality_checkpoints'
    )
    checkpoint_name = models.CharField(max_length=200)
    specification_ref = models.CharField(max_length=200, blank=True)
    acceptance_criteria = models.TextField()
    frequency = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['project__contract_no', 'checkpoint_name']
        indexes = [
            models.Index(fields=['project'], name='quality_cp_project_idx'),
            models.Index(fields=['is_active'], name='quality_cp_active_idx'),
        ]

    def __str__(self):
        return f'{self.project.contract_no} - {self.checkpoint_name}'


class NonConformance(models.Model):
    STATUS_OPEN = 'Open'
    STATUS_IN_PROGRESS = 'In Progress'
    STATUS_CLOSED = 'Closed'
    STATUS_CANCELLED = 'Cancelled'
    STATUS_CHOICES = [
        (STATUS_OPEN, 'Open'),
        (STATUS_IN_PROGRESS, 'In Progress'),
        (STATUS_CLOSED, 'Closed'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    SEVERITY_LOW = 'Low'
    SEVERITY_MEDIUM = 'Medium'
    SEVERITY_HIGH = 'High'
    SEVERITY_CRITICAL = 'Critical'
    SEVERITY_CHOICES = [
        (SEVERITY_LOW, 'Low'),
        (SEVERITY_MEDIUM, 'Medium'),
        (SEVERITY_HIGH, 'High'),
        (SEVERITY_CRITICAL, 'Critical'),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='non_conformances')
    inspection_request = models.ForeignKey(
        InspectionRequest,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='non_conformances',
    )
    boq_item = models.ForeignKey(
        BOQItem, on_delete=models.SET_NULL, null=True, blank=True, related_name='non_conformances'
    )
    ncr_no = models.CharField(max_length=50)
    description = models.TextField()
    root_cause = models.TextField(blank=True)
    corrective_action = models.TextField(blank=True)
    preventive_action = models.TextField(blank=True)
    responsible_person = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='responsible_non_conformances',
    )
    issued_date = models.DateField()
    due_date = models.DateField()
    closed_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_OPEN)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default=SEVERITY_MEDIUM)
    attachment = models.FileField(upload_to='quality/ncr/%Y/%m/', blank=True)

    class Meta:
        ordering = ['-issued_date', '-id']
        unique_together = ('project', 'ncr_no')
        indexes = [
            models.Index(fields=['project'], name='quality_ncr_project_idx'),
            models.Index(fields=['status'], name='quality_ncr_status_idx'),
            models.Index(fields=['due_date'], name='quality_ncr_due_idx'),
            models.Index(fields=['project', 'status'], name='quality_ncr_proj_status_idx'),
        ]

    def __str__(self):
        return f'{self.project.contract_no} - {self.ncr_no}'


class PunchList(models.Model):
    STATUS_OPEN = 'Open'
    STATUS_IN_PROGRESS = 'In Progress'
    STATUS_CLOSED = 'Closed'
    STATUS_CHOICES = [
        (STATUS_OPEN, 'Open'),
        (STATUS_IN_PROGRESS, 'In Progress'),
        (STATUS_CLOSED, 'Closed'),
    ]

    PRIORITY_LOW = 'Low'
    PRIORITY_MEDIUM = 'Medium'
    PRIORITY_HIGH = 'High'
    PRIORITY_CRITICAL = 'Critical'
    PRIORITY_CHOICES = [
        (PRIORITY_LOW, 'Low'),
        (PRIORITY_MEDIUM, 'Medium'),
        (PRIORITY_HIGH, 'High'),
        (PRIORITY_CRITICAL, 'Critical'),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='punch_list_items')
    description = models.TextField()
    location = models.CharField(max_length=200)
    responsible_person = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='responsible_punch_list_items',
    )
    target_date = models.DateField()
    closed_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_OPEN)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default=PRIORITY_MEDIUM)
    attachment = models.FileField(upload_to='quality/punch-list/%Y/%m/', blank=True)

    class Meta:
        ordering = ['target_date', '-id']
        indexes = [
            models.Index(fields=['project'], name='quality_pl_project_idx'),
            models.Index(fields=['status'], name='quality_pl_status_idx'),
            models.Index(fields=['target_date'], name='quality_pl_target_idx'),
            models.Index(fields=['project', 'status'], name='quality_pl_proj_status_idx'),
        ]

    def __str__(self):
        return f'{self.project.contract_no} - {self.description[:60]}'
