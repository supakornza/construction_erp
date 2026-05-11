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
