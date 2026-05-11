from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied


class RoleRequiredMixin(LoginRequiredMixin):
    allowed_roles = []

    def dispatch(self, request, *args, **kwargs):
        result = super().dispatch(request, *args, **kwargs)
        if not request.user.is_authenticated:
            return result
        if request.user.is_superuser:
            return result
        if self.allowed_roles and request.user.role not in self.allowed_roles:
            raise PermissionDenied
        return result


class AdminRequiredMixin(RoleRequiredMixin):
    allowed_roles = ['admin']

    def dispatch(self, request, *args, **kwargs):
        result = super(RoleRequiredMixin, self).dispatch(request, *args, **kwargs)
        if not request.user.is_authenticated:
            return result
        if not (request.user.is_superuser or request.user.role == 'admin'):
            raise PermissionDenied
        return result


class ApproverRequiredMixin(RoleRequiredMixin):
    allowed_roles = ['admin', 'project_manager']
