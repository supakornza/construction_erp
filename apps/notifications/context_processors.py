def notifications(request):
    if not request.user.is_authenticated:
        return {}
    unread = request.user.notifications.filter(is_read=False)
    return {
        'notif_unread_count': unread.count(),
        'notif_recent':       unread.order_by('-created_at')[:6],
    }
