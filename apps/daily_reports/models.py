from django.db import models
from django.core.exceptions import ValidationError
from apps.accounts.models import User
from apps.projects.models import Project, WorkArea


class DailyReport(models.Model):
    STATUS_CHOICES = [
        ('Draft', 'Draft'),
        ('Submitted', 'Submitted'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]
    WEATHER_CHOICES = [
        ('Sunny', 'Sunny'),
        ('Partly Cloudy', 'Partly Cloudy'),
        ('Cloudy', 'Cloudy'),
        ('Rainy', 'Rainy'),
        ('Heavy Rain', 'Heavy Rain'),
        ('Stormy', 'Stormy'),
    ]
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='daily_reports')
    report_date = models.DateField()
    weather_morning = models.CharField(max_length=30, choices=WEATHER_CHOICES, default='Sunny')
    weather_afternoon = models.CharField(max_length=30, choices=WEATHER_CHOICES, default='Sunny')
    prepared_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='prepared_reports')
    checked_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='checked_reports')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_reports')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Draft')
    remarks = models.TextField(blank=True)
    rejection_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('project', 'report_date')
        ordering = ['-report_date']

    def __str__(self):
        return f"{self.project.contract_no} – {self.report_date}"

    def clean(self):
        if self.pk is None:
            if DailyReport.objects.filter(project=self.project, report_date=self.report_date).exists():
                raise ValidationError(f'A daily report for {self.report_date} already exists for this project.')


class DailyWorkActivity(models.Model):
    report = models.ForeignKey(DailyReport, on_delete=models.CASCADE, related_name='activities')
    work_area = models.ForeignKey(WorkArea, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.CharField(max_length=500)
    quantity = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    unit = models.CharField(max_length=50, blank=True)
    percent_complete = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    remarks = models.CharField(max_length=300, blank=True)

    def __str__(self):
        return f"{self.report} – {self.description[:50]}"


class DailyLookahead(models.Model):
    report = models.ForeignKey(DailyReport, on_delete=models.CASCADE, related_name='lookaheads')
    planned_activity = models.CharField(max_length=500)
    planned_date = models.DateField()
    responsible_person = models.CharField(max_length=200)

    def __str__(self):
        return f"{self.planned_activity[:50]} – {self.planned_date}"


class DailyProblemRemark(models.Model):
    CATEGORY_CHOICES = [
        ('Weather', 'Weather'),
        ('Labour', 'Labour'),
        ('Equipment', 'Equipment'),
        ('Material', 'Material'),
        ('Design', 'Design'),
        ('Safety', 'Safety'),
        ('Other', 'Other'),
    ]
    STATUS_CHOICES = [
        ('Open', 'Open'),
        ('Closed', 'Closed'),
    ]
    report = models.ForeignKey(DailyReport, on_delete=models.CASCADE, related_name='problems')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    description = models.TextField()
    impact = models.TextField(blank=True)
    corrective_action = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Open')

    def __str__(self):
        return f"{self.category} – {self.description[:50]}"


class DailyPhoto(models.Model):
    report = models.ForeignKey(DailyReport, on_delete=models.CASCADE, related_name='photos')
    caption = models.CharField(max_length=300)
    photo = models.ImageField(upload_to='daily_reports/%Y/%m/%d/')
    location = models.CharField(max_length=200, blank=True)
    taken_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.report} – {self.caption[:50]}"


# ── Contractor Import ─────────────────────────────────────────────────────────

class ContractorImport(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending Review'),
        ('Imported', 'Imported to Daily Report'),
        ('Rejected', 'Rejected'),
    ]
    WEATHER_CHOICES = [
        ('Clear', 'Clear'),
        ('Cloudy', 'Cloudy'),
        ('Windy', 'Windy'),
        ('Raining', 'Raining'),
        ('High Wave', 'High Wave'),
        ('Other', 'Other'),
    ]
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='contractor_imports')
    report_date = models.DateField()
    contractor_name = models.CharField(max_length=200)
    weather_day = models.CharField(max_length=20, choices=WEATHER_CHOICES, default='Clear')
    weather_night = models.CharField(max_length=20, choices=WEATHER_CHOICES, default='Clear')
    wind_speed = models.CharField(max_length=50, blank=True)
    total_manpower = models.PositiveIntegerField(default=0)
    prepared_by_name = models.CharField(max_length=200, blank=True)
    checked_by_name = models.CharField(max_length=200, blank=True)
    remarks = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    source_file = models.FileField(upload_to='contractor_imports/%Y/%m/', blank=True, null=True)
    daily_report = models.ForeignKey(
        DailyReport, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='contractor_imports',
    )
    uploaded_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='contractor_imports',
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-report_date', '-uploaded_at']

    def __str__(self):
        return f"{self.contractor_name} – {self.report_date}"


class ContractorImportEquipment(models.Model):
    contractor_import = models.ForeignKey(
        ContractorImport, on_delete=models.CASCADE, related_name='equipment_items',
    )
    equipment_name = models.CharField(max_length=200)
    quantity = models.PositiveIntegerField(default=1)
    remarks = models.CharField(max_length=300, blank=True)

    class Meta:
        ordering = ['equipment_name']

    def __str__(self):
        return f"{self.equipment_name} × {self.quantity}"


class ContractorImportManpower(models.Model):
    contractor_import = models.ForeignKey(
        ContractorImport, on_delete=models.CASCADE, related_name='manpower_items',
    )
    role = models.CharField(max_length=200)
    quantity = models.PositiveIntegerField(default=0)
    company = models.CharField(max_length=200, blank=True)
    remarks = models.CharField(max_length=300, blank=True)

    class Meta:
        ordering = ['role']

    def __str__(self):
        return f"{self.role}: {self.quantity}"


class ContractorImportActivity(models.Model):
    contractor_import = models.ForeignKey(
        ContractorImport, on_delete=models.CASCADE, related_name='activities',
    )
    item_no = models.PositiveSmallIntegerField(default=1)
    description = models.CharField(max_length=500)
    location = models.CharField(max_length=200, blank=True)
    quantity = models.DecimalField(max_digits=14, decimal_places=3, null=True, blank=True)
    unit = models.CharField(max_length=50, blank=True)
    problem = models.CharField(max_length=300, blank=True)
    remarks = models.CharField(max_length=300, blank=True)

    class Meta:
        ordering = ['item_no']

    def __str__(self):
        return f"[{self.item_no}] {self.description[:60]}"


class ContractorImportLookahead(models.Model):
    contractor_import = models.ForeignKey(
        ContractorImport, on_delete=models.CASCADE, related_name='lookaheads',
    )
    item_no = models.PositiveSmallIntegerField(default=1)
    description = models.CharField(max_length=500)
    location = models.CharField(max_length=200, blank=True)
    quantity = models.DecimalField(max_digits=14, decimal_places=3, null=True, blank=True)
    unit = models.CharField(max_length=50, blank=True)
    remarks = models.CharField(max_length=300, blank=True)

    class Meta:
        ordering = ['item_no']

    def __str__(self):
        return f"[{self.item_no}] {self.description[:60]}"
