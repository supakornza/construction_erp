from django.db import models
from apps.projects.models import Project


class EquipmentCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.CharField(max_length=200, blank=True)

    class Meta:
        verbose_name_plural = 'Equipment Categories'
        ordering = ['name']

    def __str__(self):
        return self.name


class Equipment(models.Model):
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
        ('Transferred', 'Transferred'),
    ]
    name = models.CharField(max_length=200)
    category = models.ForeignKey(EquipmentCategory, on_delete=models.PROTECT)
    capacity = models.CharField(max_length=100, blank=True)
    unit = models.CharField(max_length=50, blank=True)
    registration_no = models.CharField(max_length=50, blank=True)
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True, related_name='equipment')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Active')

    class Meta:
        verbose_name_plural = 'Equipment'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.registration_no})" if self.registration_no else self.name


class EquipmentPhoto(models.Model):
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField(upload_to='equipment/photos/')
    caption = models.CharField(max_length=200, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['uploaded_at']

    def __str__(self):
        return f"Photo of {self.equipment} – {self.uploaded_at.date()}"


class DailyEquipmentRecord(models.Model):
    STATUS_CHOICES = [
        ('Working', 'Working'),
        ('Standby', 'Standby'),
        ('Breakdown', 'Breakdown'),
        ('Offsite', 'Offsite'),
    ]
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='equipment_records')
    report = models.ForeignKey('daily_reports.DailyReport', on_delete=models.SET_NULL,
                               null=True, blank=True, related_name='equipment_records')
    report_date = models.DateField()
    equipment = models.ForeignKey(Equipment, on_delete=models.PROTECT)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Working')
    working_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    remarks = models.CharField(max_length=300, blank=True)

    class Meta:
        ordering = ['-report_date', 'equipment']

    def __str__(self):
        return f"{self.equipment} – {self.report_date} – {self.status}"
