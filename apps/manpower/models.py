from django.db import models
from apps.projects.models import Project


class ManpowerCategory(models.Model):
    NAME_CHOICES = [
        ('Engineer', 'Engineer'),
        ('Foreman', 'Foreman'),
        ('Surveyor', 'Surveyor'),
        ('SafetyOfficer', 'Safety Officer'),
        ('Operator', 'Operator'),
        ('Driver', 'Driver'),
        ('GeneralWorker', 'General Worker'),
        ('Other', 'Other'),
    ]
    name = models.CharField(max_length=50, choices=NAME_CHOICES, unique=True)
    description = models.CharField(max_length=200, blank=True)

    class Meta:
        verbose_name_plural = 'Manpower Categories'
        ordering = ['name']

    def __str__(self):
        return self.get_name_display()


class DailyManpowerRecord(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='manpower_records')
    report = models.ForeignKey('daily_reports.DailyReport', on_delete=models.SET_NULL,
                               null=True, blank=True, related_name='manpower_records')
    report_date = models.DateField()
    category = models.ForeignKey(ManpowerCategory, on_delete=models.PROTECT)
    company = models.CharField(max_length=200)
    quantity = models.PositiveIntegerField()
    remarks = models.CharField(max_length=300, blank=True)

    class Meta:
        ordering = ['-report_date', 'category']

    def __str__(self):
        return f"{self.project.contract_no} – {self.category} – {self.report_date} – {self.quantity}"
