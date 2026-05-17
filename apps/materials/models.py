from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Sum
from apps.projects.models import Project, WorkArea


class MaterialCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name_plural = 'Material Categories'
        ordering = ['name']

    def __str__(self):
        return self.name


class DeliverySource(models.Model):
    name = models.CharField(max_length=200, unique=True, verbose_name='ชื่อแหล่งวัสดุ')
    description = models.CharField(max_length=300, blank=True, verbose_name='รายละเอียด')

    class Meta:
        ordering = ['name']
        verbose_name = 'แหล่งวัสดุ'
        verbose_name_plural = 'แหล่งวัสดุ'

    def __str__(self):
        return self.name


class Material(models.Model):
    name = models.CharField(max_length=200)
    category = models.ForeignKey(MaterialCategory, on_delete=models.PROTECT)
    unit = models.CharField(max_length=50)
    unit_weight = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.unit})"


class MaterialDelivery(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='material_deliveries')
    delivery_date = models.DateField(verbose_name='วันที่รับวัสดุ')
    delivery_time = models.TimeField(null=True, blank=True, verbose_name='เวลารับ')
    material = models.ForeignKey(Material, on_delete=models.PROTECT, verbose_name='วัสดุ')
    destination = models.ForeignKey(WorkArea, on_delete=models.SET_NULL, null=True, blank=True, related_name='material_deliveries', verbose_name='ปลายทาง (กอง/พื้นที่)')
    source = models.CharField(max_length=200, blank=True, verbose_name='แหล่งวัสดุ')
    truck_no = models.CharField(max_length=50, blank=True, verbose_name='ทะเบียนรถ')
    delivery_note_no = models.CharField(max_length=100, blank=True, verbose_name='เลขที่ใบส่งของ')
    quantity = models.DecimalField(max_digits=15, decimal_places=3, verbose_name='ปริมาณ')
    unit_price = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, verbose_name='ราคาต่อหน่วย')
    remarks = models.CharField(max_length=300, blank=True, verbose_name='หมายเหตุ')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-delivery_date']
        verbose_name_plural = 'Material Deliveries'

    def __str__(self):
        return f"{self.material} – {self.quantity} – {self.delivery_date}"

    def clean(self):
        if self.quantity is not None and self.quantity <= 0:
            raise ValidationError('Delivery quantity must be greater than zero.')

    @property
    def total_amount(self):
        if self.unit_price:
            return self.quantity * self.unit_price
        return None


class MaterialUsage(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='material_usages')
    usage_date = models.DateField()
    material = models.ForeignKey(Material, on_delete=models.PROTECT)
    work_area = models.ForeignKey(WorkArea, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.DecimalField(max_digits=15, decimal_places=3)
    remarks = models.CharField(max_length=300, blank=True)

    class Meta:
        ordering = ['-usage_date']

    def __str__(self):
        return f"{self.material} – {self.quantity} used – {self.usage_date}"


def get_stock_balance(project, material):
    delivered = (MaterialDelivery.objects
                 .filter(project=project, material=material)
                 .aggregate(total=Sum('quantity'))['total'] or 0)
    used = (MaterialUsage.objects
            .filter(project=project, material=material)
            .aggregate(total=Sum('quantity'))['total'] or 0)
    return {'delivered': delivered, 'used': used, 'balance': delivered - used}
