from django.db import models
from apps.accounts.models import User
from apps.projects.models import Project


class ToolboxMeeting(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='toolbox_meetings')
    meeting_date = models.DateField()
    topic = models.CharField(max_length=300)
    location = models.CharField(max_length=200)
    conducted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    attendee_count = models.PositiveIntegerField(default=0)
    attachment = models.FileField(upload_to='safety/toolbox/%Y/%m/', blank=True)
    remarks = models.TextField(blank=True)

    class Meta:
        ordering = ['-meeting_date']

    def __str__(self):
        return f"{self.project.contract_no} – {self.topic[:50]} – {self.meeting_date}"


class SafetyInspection(models.Model):
    STATUS_CHOICES = [
        ('Open', 'Open'),
        ('InProgress', 'In Progress'),
        ('Closed', 'Closed'),
    ]
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='safety_inspections')
    inspection_date = models.DateField()
    location = models.CharField(max_length=200)
    inspector = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    category = models.CharField(max_length=100)
    finding = models.TextField()
    action_required = models.TextField()
    responsible_person = models.CharField(max_length=200)
    due_date = models.DateField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='Open')
    close_date = models.DateField(null=True, blank=True)
    attachment = models.FileField(upload_to='safety/inspections/%Y/%m/', blank=True)

    class Meta:
        ordering = ['-inspection_date']

    def __str__(self):
        return f"{self.project.contract_no} – {self.category} – {self.inspection_date}"


class IncidentReport(models.Model):
    TYPE_CHOICES = [
        ('NearMiss', 'Near Miss'),
        ('FirstAid', 'First Aid'),
        ('MedicalTreatment', 'Medical Treatment'),
        ('LostTime', 'Lost Time'),
        ('Fatal', 'Fatal'),
    ]
    STATUS_CHOICES = [
        ('Draft', 'Draft'),
        ('Submitted', 'Submitted'),
        ('Closed', 'Closed'),
    ]
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='incident_reports')
    incident_date = models.DateField()
    incident_time = models.TimeField(null=True, blank=True)
    location = models.CharField(max_length=200)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    description = models.TextField()
    injured_person = models.CharField(max_length=200, blank=True)
    root_cause = models.TextField(blank=True)
    corrective_action = models.TextField(blank=True)
    reported_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='Draft')

    class Meta:
        ordering = ['-incident_date']

    def __str__(self):
        return f"{self.project.contract_no} – {self.get_type_display()} – {self.incident_date}"


class JSEARecord(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='jsea_records')
    work_activity = models.CharField(max_length=300)
    date = models.DateField()
    work_area = models.CharField(max_length=200)
    prepared_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='jsea_prepared')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='jsea_approved')
    attachment = models.FileField(upload_to='safety/jsea/%Y/%m/', blank=True)

    class Meta:
        ordering = ['-date']
        verbose_name = 'JSEA Record'

    def __str__(self):
        return f"{self.project.contract_no} – {self.work_activity[:50]} – {self.date}"
