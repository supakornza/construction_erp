from django.db import models
from apps.accounts.models import User


class Project(models.Model):
    STATUS_CHOICES = [
        ('Planning', 'Planning'),
        ('Active', 'Active'),
        ('Suspended', 'Suspended'),
        ('Completed', 'Completed'),
        ('Closed', 'Closed'),
    ]
    project_name = models.CharField(max_length=200)
    contract_no = models.CharField(max_length=100, unique=True)
    owner = models.CharField(max_length=200)
    contractor = models.CharField(max_length=200)
    consultant = models.CharField(max_length=200, blank=True)
    location = models.CharField(max_length=300, blank=True)
    start_date = models.DateField()
    finish_date = models.DateField()
    contract_value = models.DecimalField(max_digits=15, decimal_places=2)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Planning')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_projects')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.contract_no} – {self.project_name}"

    def duration_days(self):
        return (self.finish_date - self.start_date).days


class Stakeholder(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='stakeholders')
    name = models.CharField(max_length=200)
    company = models.CharField(max_length=200)
    role = models.CharField(max_length=100)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    is_primary = models.BooleanField(default=False)

    class Meta:
        ordering = ['-is_primary', 'name']

    def __str__(self):
        return f"{self.name} ({self.role})"


class WorkArea(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='work_areas')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    area_sqm = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.project.contract_no} – {self.name}"
