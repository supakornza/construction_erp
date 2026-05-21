from decimal import Decimal
from django.db import models
from django.db.models import Sum
from apps.accounts.models import User
from apps.projects.models import Project


class ChangeOrder(models.Model):
    TYPE_CHOICES = [
        ('Addition',     'Addition — New Scope'),
        ('Omission',     'Omission — Scope Removed'),
        ('Substitution', 'Substitution — Scope Replaced'),
        ('Extension',    'Extension — Time Extension'),
        ('Acceleration', 'Acceleration — Time Reduction'),
        ('Other',        'Other'),
    ]
    STATUS_CHOICES = [
        ('Draft',       'Draft'),
        ('Submitted',   'Submitted'),
        ('UnderReview', 'Under Review'),
        ('Approved',    'Approved'),
        ('Rejected',    'Rejected'),
        ('Cancelled',   'Cancelled'),
    ]
    INITIATED_BY_CHOICES = [
        ('Owner',      'Owner'),
        ('Contractor', 'Contractor'),
        ('PMC',        'PMC / Consultant'),
        ('Engineer',   'Engineer'),
    ]

    project        = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='change_orders')
    co_no          = models.CharField(max_length=30)
    title          = models.CharField(max_length=300)
    description    = models.TextField()
    type           = models.CharField(max_length=20, choices=TYPE_CHOICES)
    initiated_by   = models.CharField(max_length=20, choices=INITIATED_BY_CHOICES)
    status         = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Draft')

    contract_value_impact = models.DecimalField(max_digits=15, decimal_places=2, default=0,
                                                 help_text='Positive = increase, Negative = decrease (THB)')
    time_impact_days      = models.IntegerField(default=0,
                                                 help_text='Positive = extension, Negative = acceleration (days)')

    initiated_date  = models.DateField()
    submitted_date  = models.DateField(null=True, blank=True)
    approved_date   = models.DateField(null=True, blank=True)

    prepared_by  = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                      related_name='prepared_change_orders')
    reviewed_by  = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                      related_name='reviewed_change_orders')
    approved_by  = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                      related_name='approved_change_orders')

    rejection_reason = models.TextField(blank=True)
    attachment       = models.FileField(upload_to='change_orders/%Y/%m/', blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-initiated_date', 'co_no']
        unique_together = ('project', 'co_no')

    def __str__(self):
        return f"{self.project.contract_no} – {self.co_no} – {self.title[:50]}"

    @property
    def items_total(self):
        result = self.items.aggregate(total=Sum('_amount_cache'))['total']
        # Compute dynamically since amount is a property
        return sum(item.amount for item in self.items.all())

    @property
    def is_editable(self):
        return self.status in ('Draft', 'Rejected')

    @property
    def status_color(self):
        return {
            'Draft':       'secondary',
            'Submitted':   'info',
            'UnderReview': 'warning',
            'Approved':    'success',
            'Rejected':    'danger',
            'Cancelled':   'dark',
        }.get(self.status, 'secondary')

    @classmethod
    def generate_co_no(cls, project):
        last = cls.objects.filter(project=project).order_by('co_no').last()
        if last:
            try:
                seq = int(last.co_no.split('-')[-1]) + 1
            except (ValueError, IndexError):
                seq = cls.objects.filter(project=project).count() + 1
        else:
            seq = 1
        return f"CO-{seq:03d}"


class ChangeOrderItem(models.Model):
    CHANGE_TYPE_CHOICES = [
        ('Add',    'Add New Item'),
        ('Modify', 'Modify Quantity'),
        ('Delete', 'Delete Item'),
    ]

    change_order      = models.ForeignKey(ChangeOrder, on_delete=models.CASCADE, related_name='items')
    boq_item          = models.ForeignKey('boq.BOQItem', on_delete=models.SET_NULL,
                                           null=True, blank=True, related_name='co_items')
    description       = models.CharField(max_length=500)
    unit              = models.CharField(max_length=50)
    change_type       = models.CharField(max_length=10, choices=CHANGE_TYPE_CHOICES, default='Modify')
    original_quantity = models.DecimalField(max_digits=15, decimal_places=3, default=0)
    revised_quantity  = models.DecimalField(max_digits=15, decimal_places=3, default=0)
    unit_rate         = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    remarks           = models.CharField(max_length=300, blank=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.change_order.co_no} – {self.description[:50]}"

    @property
    def quantity_change(self):
        return self.revised_quantity - self.original_quantity

    @property
    def amount(self):
        return self.quantity_change * self.unit_rate
