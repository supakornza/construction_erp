from decimal import Decimal
from django.db import models
from django.db.models import Sum
from apps.accounts.models import User
from apps.projects.models import Project


class BOQItem(models.Model):
    ITEM_TYPE_CHOICES = [
        ('header', 'Section Header'),
        ('item', 'Line Item'),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='boq_items')
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='children')
    item_no = models.CharField(max_length=20)
    item_type = models.CharField(max_length=10, choices=ITEM_TYPE_CHOICES, default='item')
    sort_key = models.CharField(max_length=100, editable=False, default='', db_index=True)
    description = models.CharField(max_length=500)
    unit = models.CharField(max_length=50, blank=True, default='')
    contract_quantity = models.DecimalField(max_digits=15, decimal_places=3, null=True, blank=True)
    unit_rate = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)

    class Meta:
        ordering = ['sort_key']
        unique_together = ('project', 'item_no')

    def __str__(self):
        return f"{self.project.contract_no} – {self.item_no} – {self.description[:50]}"

    def save(self, *args, **kwargs):
        parts = self.item_no.split('.')
        try:
            self.sort_key = '.'.join(str(int(p)).zfill(6) for p in parts)
        except (ValueError, AttributeError):
            self.sort_key = self.item_no
        super().save(*args, **kwargs)

    @classmethod
    def find_parent(cls, project, item_no, exclude_pk=None):
        parts = item_no.split('.')
        for depth in range(len(parts) - 1, 0, -1):
            candidate = '.'.join(parts[:depth])
            qs = cls.objects.filter(project=project, item_no=candidate)
            if exclude_pk:
                qs = qs.exclude(pk=exclude_pk)
            parent = qs.first()
            if parent:
                return parent
        return None

    @property
    def contract_amount(self):
        if self.contract_quantity is None or self.unit_rate is None:
            return Decimal('0')
        return self.contract_quantity * self.unit_rate

    @property
    def cumulative_quantity(self):
        result = self.progress_records.aggregate(total=Sum('daily_quantity'))['total']
        return result or 0

    @property
    def remaining_quantity(self):
        if self.contract_quantity is None:
            return Decimal('0')
        return self.contract_quantity - self.cumulative_quantity

    @property
    def percent_complete(self):
        if not self.contract_quantity:
            return 0
        return (self.cumulative_quantity / self.contract_quantity) * 100

    @property
    def earned_value(self):
        if self.unit_rate is None:
            return Decimal('0')
        return self.cumulative_quantity * self.unit_rate


class DailyProgressRecord(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='progress_records')
    boq_item = models.ForeignKey(BOQItem, on_delete=models.CASCADE, related_name='progress_records')
    record_date = models.DateField()
    daily_quantity = models.DecimalField(max_digits=15, decimal_places=3)
    remarks = models.CharField(max_length=300, blank=True)
    allow_overrun = models.BooleanField(default=False)

    class Meta:
        ordering = ['-record_date']

    def __str__(self):
        return f"{self.boq_item} – {self.record_date} – {self.daily_quantity}"

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.boq_item.contract_quantity is None:
            return
        if not self.allow_overrun:
            cumulative = self.boq_item.cumulative_quantity
            if self.pk:
                existing = DailyProgressRecord.objects.get(pk=self.pk)
                cumulative -= existing.daily_quantity
            if cumulative + (self.daily_quantity or 0) > self.boq_item.contract_quantity:
                raise ValidationError(
                    'Cumulative quantity would exceed contract quantity. '
                    'Check "Allow Overrun" to proceed.'
                )


class PaymentClaim(models.Model):
    STATUS_CHOICES = [
        ('Draft', 'Draft'),
        ('Submitted', 'Submitted'),
        ('Certified', 'Certified'),
        ('Paid', 'Paid'),
    ]
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='payment_claims')
    claim_no = models.CharField(max_length=30)
    claim_date = models.DateField()
    period_from = models.DateField()
    period_to = models.DateField()
    total_claimed_amount = models.DecimalField(max_digits=15, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Draft')

    class Meta:
        ordering = ['-claim_date']
        unique_together = ('project', 'claim_no')

    def __str__(self):
        return f"{self.project.contract_no} – {self.claim_no}"
