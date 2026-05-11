from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator
from apps.accounts.models import User
from apps.projects.models import Project
from apps.boq.models import BOQItem


class CostCode(models.Model):
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name='cost_codes'
    )
    code = models.CharField(max_length=30)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['project', 'code']
        unique_together = ('project', 'code')
        indexes = [models.Index(fields=['project', 'is_active'])]
        verbose_name = 'Cost Code'
        verbose_name_plural = 'Cost Codes'

    def __str__(self):
        return f"[{self.code}] {self.name}"


class BudgetItem(models.Model):
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name='budget_items'
    )
    cost_code = models.ForeignKey(
        CostCode, on_delete=models.PROTECT, related_name='budget_items'
    )
    boq_item = models.ForeignKey(
        BOQItem, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='budget_items'
    )
    description = models.CharField(max_length=300)
    budget_amount = models.DecimalField(
        max_digits=15, decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))]
    )
    committed_amount = models.DecimalField(
        max_digits=15, decimal_places=2, default=Decimal('0'),
        validators=[MinValueValidator(Decimal('0'))]
    )
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['project', 'cost_code__code', 'description']
        indexes = [models.Index(fields=['project', 'cost_code'])]
        verbose_name = 'Budget Item'
        verbose_name_plural = 'Budget Items'

    def __str__(self):
        return f"{self.cost_code.code} – {self.description[:60]}"


class ActualCost(models.Model):
    SOURCE_MATERIAL = 'Material'
    SOURCE_LABOR = 'Labor'
    SOURCE_EQUIPMENT = 'Equipment'
    SOURCE_SUBCONTRACT = 'Subcontract'
    SOURCE_OVERHEAD = 'Overhead'
    SOURCE_OTHER = 'Other'

    SOURCE_CHOICES = [
        (SOURCE_MATERIAL, 'Material'),
        (SOURCE_LABOR, 'Labor'),
        (SOURCE_EQUIPMENT, 'Equipment'),
        (SOURCE_SUBCONTRACT, 'Subcontract'),
        (SOURCE_OVERHEAD, 'Overhead'),
        (SOURCE_OTHER, 'Other'),
    ]

    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name='actual_costs'
    )
    cost_code = models.ForeignKey(
        CostCode, on_delete=models.PROTECT, related_name='actual_costs'
    )
    cost_date = models.DateField()
    description = models.CharField(max_length=300)
    amount = models.DecimalField(
        max_digits=15, decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))]
    )
    source_type = models.CharField(
        max_length=20, choices=SOURCE_CHOICES, default=SOURCE_OTHER
    )
    reference_no = models.CharField(max_length=100, blank=True)
    remarks = models.TextField(blank=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='actual_costs'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-cost_date', '-created_at']
        indexes = [
            models.Index(fields=['project', 'cost_date']),
            models.Index(fields=['project', 'cost_code']),
            models.Index(fields=['source_type']),
        ]
        verbose_name = 'Actual Cost'
        verbose_name_plural = 'Actual Costs'

    def __str__(self):
        return f"{self.cost_code.code} – {self.description[:60]} ({self.cost_date})"
