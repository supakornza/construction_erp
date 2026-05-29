from django.db import models
from django.utils import timezone


class KanbanTask(models.Model):
    COLUMN_TODO = 'todo'
    COLUMN_IN_PROGRESS = 'in_progress'
    COLUMN_IN_REVIEW = 'in_review'
    COLUMN_DONE = 'done'
    COLUMN_CHOICES = [
        (COLUMN_TODO, 'To Do'),
        (COLUMN_IN_PROGRESS, 'In Progress'),
        (COLUMN_IN_REVIEW, 'In Review'),
        (COLUMN_DONE, 'Done'),
    ]

    PRIORITY_HIGH = 'high'
    PRIORITY_MEDIUM = 'medium'
    PRIORITY_LOW = 'low'
    PRIORITY_CHOICES = [
        (PRIORITY_HIGH, 'High'),
        (PRIORITY_MEDIUM, 'Medium'),
        (PRIORITY_LOW, 'Low'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    project = models.ForeignKey(
        'projects.Project', on_delete=models.CASCADE,
        null=True, blank=True, related_name='kanban_tasks',
    )
    column = models.CharField(max_length=20, choices=COLUMN_CHOICES, default=COLUMN_TODO)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default=PRIORITY_MEDIUM)
    assignee = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='assigned_kanban_tasks',
    )
    due_date = models.DateField(null=True, blank=True)
    order = models.PositiveIntegerField(default=0)
    created_by = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL,
        null=True, related_name='created_kanban_tasks',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', '-created_at']
        indexes = [
            models.Index(fields=['column', 'order'], name='kanban_col_order_idx'),
        ]

    def __str__(self):
        return self.title

    @property
    def is_overdue(self):
        return (
            self.due_date is not None
            and self.due_date < timezone.now().date()
            and self.column != self.COLUMN_DONE
        )

    @property
    def priority_color(self):
        return {'high': '#ef4444', 'medium': '#f59e0b', 'low': '#10b981'}.get(self.priority, '#64748b')
