from django.conf import settings
from django.db import models
from django.db.models import Sum


class Subcontractor(models.Model):
    CATEGORY_CHOICES = [
        ('Civil', 'Civil Works'),
        ('MEP', 'MEP'),
        ('Steel', 'Steel Structure'),
        ('Concrete', 'Concrete Works'),
        ('Piling', 'Piling'),
        ('Marine', 'Marine Works'),
        ('Earthworks', 'Earthworks'),
        ('Survey', 'Survey'),
        ('Dredging', 'Dredging'),
        ('Other', 'Other'),
    ]
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
        ('Blacklisted', 'Blacklisted'),
    ]

    name            = models.CharField(max_length=300)
    registration_no = models.CharField(max_length=100, blank=True)
    category        = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='Other')
    status          = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Active')
    contact_person  = models.CharField(max_length=200, blank=True)
    phone           = models.CharField(max_length=50, blank=True)
    email           = models.EmailField(blank=True)
    address         = models.TextField(blank=True)
    tax_id          = models.CharField(max_length=50, blank=True)
    bank_account    = models.CharField(max_length=100, blank=True)
    notes           = models.TextField(blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def active_contracts_count(self):
        return self.contracts.filter(status='Active').count()

    @property
    def total_contract_value(self):
        return self.contracts.aggregate(t=Sum('contract_value'))['t'] or 0

    @property
    def total_paid(self):
        return (PaymentClaim.objects
                .filter(contract__subcontractor=self, status='Paid')
                .aggregate(t=Sum('net_payable'))['t'] or 0)


class SubcontractorContract(models.Model):
    CONTRACT_TYPE_CHOICES = [
        ('LumpSum', 'Lump Sum'),
        ('UnitRate', 'Unit Rate'),
        ('CostPlus', 'Cost Plus'),
        ('TimeAndMaterial', 'Time & Material'),
    ]
    STATUS_CHOICES = [
        ('Draft', 'Draft'),
        ('Active', 'Active'),
        ('Suspended', 'Suspended'),
        ('Completed', 'Completed'),
        ('Terminated', 'Terminated'),
    ]

    project        = models.ForeignKey('projects.Project', on_delete=models.CASCADE, related_name='subcontracts')
    subcontractor  = models.ForeignKey(Subcontractor, on_delete=models.PROTECT, related_name='contracts')
    contract_no    = models.CharField(max_length=30, blank=True)
    title          = models.CharField(max_length=300)
    contract_type  = models.CharField(max_length=20, choices=CONTRACT_TYPE_CHOICES, default='LumpSum')
    scope_of_work  = models.TextField(blank=True)
    contract_value = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    retention_pct  = models.DecimalField(max_digits=5, decimal_places=2, default=5)
    start_date     = models.DateField(null=True, blank=True)
    end_date       = models.DateField(null=True, blank=True)
    signed_date    = models.DateField(null=True, blank=True)
    status         = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Draft')
    created_by     = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                       null=True, related_name='subcontracts_created')
    created_at     = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.contract_no} – {self.title}"

    def save(self, *args, **kwargs):
        if not self.contract_no:
            count = SubcontractorContract.objects.filter(project=self.project).count()
            self.contract_no = f"SC-{count + 1:03d}"
        super().save(*args, **kwargs)

    @property
    def total_claimed(self):
        return (self.payment_claims.exclude(status='Rejected')
                .aggregate(t=Sum('claimed_amount'))['t'] or 0)

    @property
    def total_certified(self):
        return (self.payment_claims.filter(status__in=('Certified', 'Paid'))
                .aggregate(t=Sum('certified_amount'))['t'] or 0)

    @property
    def total_paid(self):
        return (self.payment_claims.filter(status='Paid')
                .aggregate(t=Sum('net_payable'))['t'] or 0)

    @property
    def balance(self):
        return self.contract_value - self.total_certified

    @property
    def progress_pct(self):
        if not self.contract_value:
            return 0
        return min(100, round(float(self.total_certified) / float(self.contract_value) * 100, 1))

    @property
    def status_color(self):
        return {
            'Draft': 'secondary', 'Active': 'success', 'Suspended': 'warning',
            'Completed': 'primary', 'Terminated': 'danger',
        }.get(self.status, 'secondary')


class SubcontractorWorkItem(models.Model):
    contract     = models.ForeignKey(SubcontractorContract, on_delete=models.CASCADE, related_name='work_items')
    description  = models.CharField(max_length=300)
    unit         = models.CharField(max_length=30, blank=True)
    contract_qty = models.DecimalField(max_digits=14, decimal_places=3, default=0)
    unit_rate    = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    completed_qty = models.DecimalField(max_digits=14, decimal_places=3, default=0)

    def __str__(self):
        return self.description

    @property
    def amount(self):
        return self.contract_qty * self.unit_rate

    @property
    def completed_amount(self):
        return self.completed_qty * self.unit_rate

    @property
    def progress_pct(self):
        if not self.contract_qty:
            return 0
        return min(100, round(float(self.completed_qty) / float(self.contract_qty) * 100, 1))


class PaymentClaim(models.Model):
    STATUS_CHOICES = [
        ('Draft', 'Draft'),
        ('Submitted', 'Submitted'),
        ('Certified', 'Certified'),
        ('Paid', 'Paid'),
        ('Rejected', 'Rejected'),
    ]

    contract            = models.ForeignKey(SubcontractorContract, on_delete=models.CASCADE,
                                            related_name='payment_claims')
    claim_no            = models.CharField(max_length=20, blank=True)
    claim_date          = models.DateField()
    period_from         = models.DateField(null=True, blank=True)
    period_to           = models.DateField(null=True, blank=True)
    claimed_amount      = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    certified_amount    = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    retention_deducted  = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    net_payable         = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    status              = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Draft')
    notes               = models.TextField(blank=True)
    certified_by        = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                            null=True, blank=True, related_name='certified_claims')
    certified_date      = models.DateField(null=True, blank=True)
    paid_date           = models.DateField(null=True, blank=True)
    created_by          = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                            null=True, related_name='created_claims')
    created_at          = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-claim_date']

    def __str__(self):
        return f"{self.claim_no} ({self.contract})"

    def save(self, *args, **kwargs):
        if not self.claim_no:
            count = PaymentClaim.objects.filter(contract=self.contract).count()
            self.claim_no = f"PC-{count + 1:03d}"
        super().save(*args, **kwargs)

    @property
    def status_color(self):
        return {
            'Draft': 'secondary', 'Submitted': 'info', 'Certified': 'warning',
            'Paid': 'success', 'Rejected': 'danger',
        }.get(self.status, 'secondary')
