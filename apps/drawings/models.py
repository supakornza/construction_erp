from datetime import date

from django.conf import settings
from django.db import models


class Drawing(models.Model):
    DISCIPLINE_CHOICES = [
        ('Civil', 'Civil'),
        ('Structural', 'Structural'),
        ('Architectural', 'Architectural'),
        ('MEP', 'MEP'),
        ('Marine', 'Marine'),
        ('Geotechnical', 'Geotechnical'),
        ('Survey', 'Survey'),
        ('Landscape', 'Landscape'),
        ('Other', 'Other'),
    ]
    STATUS_CHOICES = [
        ('IFR', 'Issued for Review'),
        ('IFA', 'Issued for Approval'),
        ('IFC', 'Issued for Construction'),
        ('IFT', 'Issued for Tender'),
        ('AFC', 'Approved for Construction'),
        ('AsBuilt', 'As-Built'),
        ('Superseded', 'Superseded'),
        ('Cancelled', 'Cancelled'),
    ]

    project       = models.ForeignKey('projects.Project', on_delete=models.CASCADE, related_name='drawings')
    drawing_no    = models.CharField(max_length=100)
    title         = models.CharField(max_length=300)
    discipline    = models.CharField(max_length=30, choices=DISCIPLINE_CHOICES, default='Civil')
    revision      = models.CharField(max_length=10, default='A')
    status        = models.CharField(max_length=20, choices=STATUS_CHOICES, default='IFR')
    issue_date    = models.DateField(null=True, blank=True)
    prepared_by   = models.CharField(max_length=200, blank=True)
    description   = models.TextField(blank=True)
    file          = models.FileField(upload_to='drawings/', blank=True)
    superseded_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True,
                                      related_name='supersedes')
    created_by    = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                      null=True, related_name='drawings_created')
    created_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering        = ['drawing_no', 'revision']
        unique_together = [('project', 'drawing_no', 'revision')]

    def __str__(self):
        return f"{self.drawing_no} Rev.{self.revision} – {self.title}"

    @property
    def is_current(self):
        return self.status not in ('Superseded', 'Cancelled')

    @property
    def status_color(self):
        return {
            'IFR': 'warning', 'IFA': 'info', 'IFC': 'success', 'IFT': 'secondary',
            'AFC': 'primary', 'AsBuilt': 'dark', 'Superseded': 'secondary', 'Cancelled': 'danger',
        }.get(self.status, 'secondary')


class RFI(models.Model):
    PRIORITY_CHOICES = [
        ('Low', 'Low'),
        ('Normal', 'Normal'),
        ('High', 'High'),
        ('Critical', 'Critical'),
    ]
    STATUS_CHOICES = [
        ('Open', 'Open'),
        ('Submitted', 'Submitted'),
        ('UnderReview', 'Under Review'),
        ('Answered', 'Answered'),
        ('Closed', 'Closed'),
        ('Void', 'Void'),
    ]

    project                = models.ForeignKey('projects.Project', on_delete=models.CASCADE,
                                               related_name='rfis')
    rfi_no                 = models.CharField(max_length=20, blank=True)
    subject                = models.CharField(max_length=300)
    description            = models.TextField(blank=True)
    drawing                = models.ForeignKey(Drawing, on_delete=models.SET_NULL,
                                               null=True, blank=True, related_name='rfis')
    priority               = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='Normal')
    status                 = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Open')
    submitted_by           = models.CharField(max_length=200, blank=True)
    submitted_date         = models.DateField(null=True, blank=True)
    response_required_date = models.DateField(null=True, blank=True)
    answer                 = models.TextField(blank=True)
    answered_by            = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                               null=True, blank=True, related_name='rfis_answered')
    answered_date          = models.DateField(null=True, blank=True)
    attachment             = models.FileField(upload_to='rfi_attachments/', blank=True)
    created_by             = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                               null=True, related_name='rfis_created')
    created_at             = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering     = ['-created_at']
        verbose_name = 'RFI'

    def __str__(self):
        return f"{self.rfi_no} – {self.subject}"

    def save(self, *args, **kwargs):
        if not self.rfi_no:
            count      = RFI.objects.filter(project=self.project).count()
            self.rfi_no = f"RFI-{count + 1:03d}"
        super().save(*args, **kwargs)

    @property
    def is_overdue(self):
        return (self.response_required_date
                and self.status in ('Open', 'Submitted', 'UnderReview')
                and date.today() > self.response_required_date)

    @property
    def priority_color(self):
        return {'Low': 'secondary', 'Normal': 'info',
                'High': 'warning', 'Critical': 'danger'}.get(self.priority, 'secondary')

    @property
    def status_color(self):
        return {
            'Open': 'primary', 'Submitted': 'info', 'UnderReview': 'warning',
            'Answered': 'success', 'Closed': 'secondary', 'Void': 'dark',
        }.get(self.status, 'secondary')
