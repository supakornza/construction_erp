from django.db import models
from apps.accounts.models import User
from apps.projects.models import Project


class OwnerDecisionItem(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Decided', 'Decided'),
        ('Escalated', 'Escalated'),
    ]
    PRIORITY_CHOICES = [
        ('Critical', 'Critical'),
        ('High', 'High'),
        ('Medium', 'Medium'),
    ]

    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name='owner_decisions'
    )
    issue = models.CharField(max_length=300, help_text='Brief description of the critical issue')
    impact = models.TextField(help_text='Impact on schedule, cost, or safety if unresolved')
    decision_required = models.TextField(help_text='Specific decision or action needed from owner')
    responsible_party = models.CharField(max_length=200, help_text='Person or team responsible')
    due_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='High')
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='created_decisions'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = [
            models.Case(
                models.When(priority='Critical', then=0),
                models.When(priority='High', then=1),
                models.When(priority='Medium', then=2),
                default=3,
                output_field=models.IntegerField(),
            ),
            'due_date',
        ]
        verbose_name = 'Owner Decision Item'
        verbose_name_plural = 'Owner Decision Items'

    def __str__(self):
        return f"{self.project.contract_no} – {self.issue[:60]} [{self.status}]"

    @property
    def is_overdue(self):
        from datetime import date
        return self.status == 'Pending' and self.due_date < date.today()
