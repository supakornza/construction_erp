from datetime import timedelta

from django.utils import timezone

from .models import Notification


def notify(recipient, notif_type, title, message='', url=''):
    """Create a single notification for one user."""
    Notification.objects.create(
        recipient=recipient,
        notif_type=notif_type,
        title=title,
        message=message,
        url=url,
    )


def notify_roles(roles, notif_type, title, message='', url=''):
    """Create notifications for all active users with the given role(s)."""
    from apps.accounts.models import User
    for user in User.objects.filter(role__in=roles, is_active=True):
        notify(user, notif_type, title, message, url)


def notify_approvers(notif_type, title, message='', url=''):
    """Notify admin, project_manager, and construction_manager."""
    notify_roles(['admin', 'project_manager', 'construction_manager'],
                 notif_type, title, message, url)


def notify_if_new(recipient, notif_type, title, message='', url='', cooldown_hours=23):
    """Create notification only if the same type hasn't been sent to this user recently."""
    cutoff = timezone.now() - timedelta(hours=cooldown_hours)
    already = Notification.objects.filter(
        recipient=recipient,
        notif_type=notif_type,
        created_at__gte=cutoff,
    ).exists()
    if not already:
        notify(recipient, notif_type, title, message, url)
        return True
    return False
