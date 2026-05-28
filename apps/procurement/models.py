from django.db import models
from django.core.exceptions import ValidationError
from apps.accounts.models import User
from apps.projects.models import Project
from apps.materials.models import Material


class Supplier(models.Model):
    name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=200, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    tax_id = models.CharField(max_length=50, blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class PurchaseRequest(models.Model):
    STATUS_CHOICES = [
        ('Draft', 'Draft'),
        ('Submitted', 'Submitted'),
        ('Reviewed', 'Reviewed'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='purchase_requests')
    pr_no = models.CharField(max_length=20, unique=True, blank=True)
    requested_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='purchase_requests')
    request_date = models.DateField()
    required_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Draft')
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.pr_no

    def save(self, *args, **kwargs):
        if not self.pr_no:
            from django.utils import timezone
            year = timezone.now().year
            count = PurchaseRequest.objects.filter(pr_no__startswith=f'PR-{year}-').count() + 1
            self.pr_no = f'PR-{year}-{count:04d}'
        super().save(*args, **kwargs)


class PurchaseRequestItem(models.Model):
    pr = models.ForeignKey(PurchaseRequest, on_delete=models.CASCADE, related_name='items')
    material = models.ForeignKey(Material, on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=15, decimal_places=3)
    unit = models.CharField(max_length=50)
    estimated_price = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    remarks = models.CharField(max_length=300, blank=True)

    def __str__(self):
        return f"{self.pr.pr_no} – {self.material.name}"


class PurchaseOrder(models.Model):
    STATUS_CHOICES = [
        ('Ordered', 'Ordered'),
        ('PartialDelivered', 'Partial Delivered'),
        ('Delivered', 'Delivered'),
        ('Closed', 'Closed'),
    ]
    pr = models.ForeignKey(PurchaseRequest, on_delete=models.PROTECT, related_name='purchase_orders')
    po_no = models.CharField(max_length=20, unique=True, blank=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT)
    order_date = models.DateField()
    delivery_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Ordered')
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.po_no

    def save(self, *args, **kwargs):
        if not self.po_no:
            from django.utils import timezone
            year = timezone.now().year
            count = PurchaseOrder.objects.filter(po_no__startswith=f'PO-{year}-').count() + 1
            self.po_no = f'PO-{year}-{count:04d}'
        super().save(*args, **kwargs)


class PurchaseOrderItem(models.Model):
    po = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='items')
    material = models.ForeignKey(Material, on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=15, decimal_places=3)
    unit_price = models.DecimalField(max_digits=15, decimal_places=2)
    total_price = models.DecimalField(max_digits=15, decimal_places=2)
    delivered_quantity = models.DecimalField(max_digits=15, decimal_places=3, default=0)

    def clean(self):
        if self.delivered_quantity > self.quantity:
            raise ValidationError('Delivered quantity cannot exceed ordered quantity.')

    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.po.po_no} – {self.material.name}"
