from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import ListView, View

from .models import Notification


class NotificationListView(LoginRequiredMixin, ListView):
    model               = Notification
    template_name       = 'notifications/list.html'
    context_object_name = 'notifications'
    paginate_by         = 30

    def get_queryset(self):
        qs = self.request.user.notifications.all()
        if self.request.GET.get('unread'):
            qs = qs.filter(is_read=False)
        return qs


class NotificationMarkReadView(LoginRequiredMixin, View):
    def post(self, request, pk):
        notif = get_object_or_404(Notification, pk=pk, recipient=request.user)
        notif.is_read = True
        notif.save(update_fields=['is_read'])
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'ok': True})
        next_url = notif.url or request.META.get('HTTP_REFERER', '/')
        return redirect(next_url)


class NotificationMarkAllReadView(LoginRequiredMixin, View):
    def post(self, request):
        request.user.notifications.filter(is_read=False).update(is_read=True)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'ok': True})
        return redirect(request.META.get('HTTP_REFERER', '/'))


class NotificationDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        Notification.objects.filter(pk=pk, recipient=request.user).delete()
        return redirect(request.META.get('HTTP_REFERER', '/'))


class NotificationDeleteAllView(LoginRequiredMixin, View):
    def post(self, request):
        request.user.notifications.filter(is_read=True).delete()
        return redirect('notifications:list')
