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


# ── Module-level permission mixins (enforce Role Permissions Reference) ──────

class ProjectViewMixin(RoleRequiredMixin):
    allowed_roles = ['admin', 'project_manager', 'engineer', 'inspector',
                     'owner', 'quantity_surveyor', 'safety_officer',
                     'site_engineer', 'storekeeper', 'viewer']


class ProjectWriteMixin(RoleRequiredMixin):
    allowed_roles = ['admin', 'project_manager']


class DailyReportViewMixin(RoleRequiredMixin):
    allowed_roles = ['admin', 'project_manager', 'engineer', 'inspector',
                     'owner', 'safety_officer', 'site_engineer']


class DailyReportCreateMixin(RoleRequiredMixin):
    allowed_roles = ['admin', 'project_manager', 'engineer', 'inspector',
                     'contractor', 'site_engineer']


class DailyReportUpdateMixin(RoleRequiredMixin):
    allowed_roles = ['admin', 'project_manager', 'engineer', 'inspector', 'site_engineer']


class OperationalViewMixin(RoleRequiredMixin):
    """Manpower & Equipment list/create — contractor included."""
    allowed_roles = ['admin', 'project_manager', 'engineer', 'inspector',
                     'contractor', 'site_engineer']


class OperationalUpdateMixin(RoleRequiredMixin):
    """Manpower & Equipment update — contractor excluded."""
    allowed_roles = ['admin', 'project_manager', 'engineer', 'inspector', 'site_engineer']


class MaterialsViewMixin(RoleRequiredMixin):
    allowed_roles = ['admin', 'project_manager', 'engineer', 'contractor',
                     'quantity_surveyor', 'storekeeper']


class MaterialsWriteMixin(RoleRequiredMixin):
    allowed_roles = ['admin', 'project_manager', 'contractor',
                     'quantity_surveyor', 'storekeeper']


class MaterialsDeleteMixin(RoleRequiredMixin):
    allowed_roles = ['admin', 'project_manager', 'quantity_surveyor']


class SafetyViewMixin(RoleRequiredMixin):
    allowed_roles = ['admin', 'project_manager', 'engineer', 'inspector',
                     'owner', 'safety_officer', 'site_engineer']


class SafetyWriteMixin(RoleRequiredMixin):
    allowed_roles = ['admin', 'project_manager', 'engineer', 'inspector',
                     'safety_officer', 'site_engineer']


class SafetyDeleteMixin(RoleRequiredMixin):
    allowed_roles = ['admin', 'project_manager', 'safety_officer']


class QualityViewMixin(RoleRequiredMixin):
    allowed_roles = ['admin', 'project_manager', 'engineer', 'inspector', 'owner']


class QualityInspectorMixin(RoleRequiredMixin):
    """Inspection requests, NCRs, punch lists — inspector CRU."""
    allowed_roles = ['admin', 'project_manager', 'engineer', 'inspector']


class QualityEngineerMixin(RoleRequiredMixin):
    """Quality checkpoints & delete — engineer Full, no inspector."""
    allowed_roles = ['admin', 'project_manager', 'engineer']


class FinancialViewMixin(RoleRequiredMixin):
    """Cost Control view: Admin, PM, Engineer, Owner, QS."""
    allowed_roles = ['admin', 'project_manager', 'engineer', 'owner', 'quantity_surveyor']


class FinancialWriteMixin(RoleRequiredMixin):
    """Cost Control / Procurement / BOQ write + delete: Admin, PM, QS."""
    allowed_roles = ['admin', 'project_manager', 'quantity_surveyor']


class BOQViewMixin(RoleRequiredMixin):
    """BOQ view — wider than Cost Control (includes Inspector and Viewer)."""
    allowed_roles = ['admin', 'project_manager', 'engineer', 'inspector',
                     'owner', 'quantity_surveyor', 'viewer']


class DocumentsMixin(RoleRequiredMixin):
    """Documents read + write: Admin, PM, Engineer, QS."""
    allowed_roles = ['admin', 'project_manager', 'engineer', 'quantity_surveyor']


class ProjectControlsViewMixin(RoleRequiredMixin):
    allowed_roles = ['admin', 'project_manager', 'engineer', 'inspector',
                     'owner', 'quantity_surveyor', 'site_engineer']


class ProjectControlsWriteMixin(RoleRequiredMixin):
    """Project Controls CRU: Admin, PM, Engineer, Site Engineer."""
    allowed_roles = ['admin', 'project_manager', 'engineer', 'site_engineer']
