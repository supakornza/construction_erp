from django.conf import settings
from django.db import models


class Notification(models.Model):
    TYPE_CHOICES = [
        # Maintenance
        ('maintenance_overdue',  'Maintenance WO Overdue'),
        ('maintenance_due_soon', 'PM Due Soon'),
        # RFI / Drawings
        ('rfi_overdue',   'RFI Overdue'),
        ('rfi_answered',  'RFI Answered'),
        # HR
        ('leave_pending',  'Leave Pending Approval'),
        ('leave_approved', 'Leave Approved'),
        ('leave_rejected', 'Leave Rejected'),
        ('ot_pending',     'OT Pending Approval'),
        # Finance
        ('claim_pending',  'Payment Claim Pending'),
        ('claim_certified','Payment Claim Certified'),
        ('claim_paid',     'Payment Claim Paid'),
        # Change Orders
        ('co_pending',     'Change Order Pending'),
        ('co_approved',    'Change Order Approved'),
        ('co_rejected',    'Change Order Rejected'),
        # General
        ('general', 'General'),
    ]

    ICON_MAP = {
        'maintenance_overdue':  'fas fa-tools',
        'maintenance_due_soon': 'fas fa-calendar-check',
        'rfi_overdue':          'fas fa-question-circle',
        'rfi_answered':         'fas fa-reply',
        'leave_pending':        'fas fa-user-clock',
        'leave_approved':       'fas fa-check-circle',
        'leave_rejected':       'fas fa-times-circle',
        'ot_pending':           'fas fa-clock',
        'claim_pending':        'fas fa-file-invoice-dollar',
        'claim_certified':      'fas fa-stamp',
        'claim_paid':           'fas fa-money-bill-wave',
        'co_pending':           'fas fa-exchange-alt',
        'co_approved':          'fas fa-check-double',
        'co_rejected':          'fas fa-ban',
        'general':              'fas fa-bell',
    }

    COLOR_MAP = {
        'maintenance_overdue':  'danger',
        'maintenance_due_soon': 'warning',
        'rfi_overdue':          'danger',
        'rfi_answered':         'success',
        'leave_pending':        'info',
        'leave_approved':       'success',
        'leave_rejected':       'danger',
        'ot_pending':           'info',
        'claim_pending':        'warning',
        'claim_certified':      'warning',
        'claim_paid':           'success',
        'co_pending':           'primary',
        'co_approved':          'success',
        'co_rejected':          'danger',
        'general':              'secondary',
    }

    recipient  = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                   related_name='notifications')
    notif_type = models.CharField(max_length=30, choices=TYPE_CHOICES, default='general')
    title      = models.CharField(max_length=200)
    message    = models.TextField(blank=True)
    url        = models.CharField(max_length=500, blank=True)
    is_read    = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.notif_type}] {self.title} → {self.recipient}"

    @property
    def icon(self):
        return self.ICON_MAP.get(self.notif_type, 'fas fa-bell')

    @property
    def color(self):
        return self.COLOR_MAP.get(self.notif_type, 'secondary')
