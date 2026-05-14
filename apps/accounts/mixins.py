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
    """Admin, Project Manager, and Engineer can approve records."""
    allowed_roles = ['admin', 'project_manager', 'engineer']


class ManagerRequiredMixin(RoleRequiredMixin):
    """Admin and Project Manager only."""
    allowed_roles = ['admin', 'project_manager']


class OperationalMixin(LoginRequiredMixin):
    """Allow all roles that can create/edit records; deny owner, viewer, contractor."""
    def dispatch(self, request, *args, **kwargs):
        result = super().dispatch(request, *args, **kwargs)
        if not request.user.is_authenticated:
            return result
        if request.user.is_superuser:
            return result
        if not request.user.can_create_records():
            raise PermissionDenied
        return result


class FinancialAccessMixin(LoginRequiredMixin):
    """Restrict access to financial/cost data to authorized roles."""
    def dispatch(self, request, *args, **kwargs):
        result = super().dispatch(request, *args, **kwargs)
        if not request.user.is_authenticated:
            return result
        if request.user.is_superuser:
            return result
        if not request.user.can_access_financial():
            raise PermissionDenied
        return result


class ContractorBlockedMixin(LoginRequiredMixin):
    """Block contractor and viewer from write operations (they are read-only for this view)."""
    BLOCKED_ROLES = {'contractor', 'viewer', 'owner'}

    def dispatch(self, request, *args, **kwargs):
        result = super().dispatch(request, *args, **kwargs)
        if not request.user.is_authenticated:
            return result
        if request.user.is_superuser:
            return result
        if request.user.role in self.BLOCKED_ROLES:
            raise PermissionDenied
        return result
