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
    """Admin, PM, CM and Engineer can approve records."""
    allowed_roles = ['admin', 'project_manager', 'construction_manager', 'engineer']


class ManagerRequiredMixin(RoleRequiredMixin):
    """Admin, PM and CM — full management including delete."""
    allowed_roles = ['admin', 'project_manager', 'construction_manager']


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
    allowed_roles = [
        'admin', 'project_manager', 'construction_manager', 'office_engineer',
        'engineer', 'inspector', 'owner', 'quantity_surveyor', 'safety_officer',
        'site_engineer', 'storekeeper', 'document_controller', 'project_coordinator',
        'legal_officer', 'environmental_specialist', 'senior_advisor', 'viewer',
    ]


class ProjectWriteMixin(RoleRequiredMixin):
    allowed_roles = ['admin', 'project_manager', 'construction_manager']


class DailyReportViewMixin(RoleRequiredMixin):
    allowed_roles = [
        'admin', 'project_manager', 'construction_manager', 'office_engineer',
        'engineer', 'inspector', 'owner', 'safety_officer', 'site_engineer',
        'document_controller', 'project_coordinator', 'environmental_specialist', 'senior_advisor',
    ]


class DailyReportCreateMixin(RoleRequiredMixin):
    allowed_roles = [
        'admin', 'project_manager', 'construction_manager', 'office_engineer',
        'engineer', 'inspector', 'contractor', 'site_engineer',
        'project_coordinator', 'environmental_specialist',
    ]


class DailyReportUpdateMixin(RoleRequiredMixin):
    allowed_roles = [
        'admin', 'project_manager', 'construction_manager', 'office_engineer',
        'engineer', 'inspector', 'site_engineer', 'project_coordinator', 'environmental_specialist',
    ]


class OperationalViewMixin(RoleRequiredMixin):
    """Manpower & Equipment list/create — contractor included."""
    allowed_roles = [
        'admin', 'project_manager', 'construction_manager', 'office_engineer',
        'engineer', 'inspector', 'contractor', 'site_engineer', 'project_coordinator',
    ]


class OperationalUpdateMixin(RoleRequiredMixin):
    """Manpower & Equipment update — contractor excluded."""
    allowed_roles = [
        'admin', 'project_manager', 'construction_manager', 'office_engineer',
        'engineer', 'inspector', 'site_engineer', 'project_coordinator',
    ]


class MaterialsViewMixin(RoleRequiredMixin):
    allowed_roles = [
        'admin', 'project_manager', 'construction_manager', 'office_engineer',
        'engineer', 'contractor', 'quantity_surveyor', 'storekeeper',
    ]


class MaterialsWriteMixin(RoleRequiredMixin):
    allowed_roles = [
        'admin', 'project_manager', 'construction_manager', 'office_engineer',
        'contractor', 'quantity_surveyor', 'storekeeper',
    ]


class MaterialsDeleteMixin(RoleRequiredMixin):
    allowed_roles = ['admin', 'project_manager', 'construction_manager', 'quantity_surveyor']


class SafetyViewMixin(RoleRequiredMixin):
    allowed_roles = [
        'admin', 'project_manager', 'construction_manager', 'office_engineer',
        'engineer', 'inspector', 'owner', 'safety_officer', 'site_engineer',
        'environmental_specialist', 'project_coordinator',
    ]


class SafetyWriteMixin(RoleRequiredMixin):
    allowed_roles = [
        'admin', 'project_manager', 'construction_manager', 'engineer', 'inspector',
        'safety_officer', 'site_engineer', 'environmental_specialist',
    ]


class SafetyDeleteMixin(RoleRequiredMixin):
    allowed_roles = ['admin', 'project_manager', 'construction_manager', 'safety_officer']


class QualityViewMixin(RoleRequiredMixin):
    allowed_roles = [
        'admin', 'project_manager', 'construction_manager', 'office_engineer',
        'engineer', 'inspector', 'owner',
    ]


class QualityInspectorMixin(RoleRequiredMixin):
    """Inspection requests, NCRs, punch lists — inspector CRU."""
    allowed_roles = [
        'admin', 'project_manager', 'construction_manager', 'office_engineer',
        'engineer', 'inspector',
    ]


class QualityEngineerMixin(RoleRequiredMixin):
    """Quality checkpoints & delete — no inspector."""
    allowed_roles = ['admin', 'project_manager', 'construction_manager', 'office_engineer', 'engineer']


class FinancialViewMixin(RoleRequiredMixin):
    """Cost Control view: Admin, PM, CM, OE, QS."""
    allowed_roles = ['admin', 'project_manager', 'construction_manager', 'office_engineer', 'quantity_surveyor']


class FinancialWriteMixin(RoleRequiredMixin):
    """Cost Control / Procurement / BOQ write + delete."""
    allowed_roles = ['admin', 'project_manager', 'construction_manager', 'office_engineer', 'quantity_surveyor']


class BOQViewMixin(RoleRequiredMixin):
    """BOQ view — wider than Cost Control (includes Inspector, PC, Advisor, Legal, Viewer)."""
    allowed_roles = [
        'admin', 'project_manager', 'construction_manager', 'office_engineer',
        'engineer', 'inspector', 'owner', 'quantity_surveyor',
        'project_coordinator', 'senior_advisor', 'legal_officer', 'viewer',
    ]


class DocumentsMixin(RoleRequiredMixin):
    """Documents read + write."""
    allowed_roles = [
        'admin', 'project_manager', 'construction_manager', 'office_engineer',
        'engineer', 'quantity_surveyor', 'document_controller',
        'legal_officer', 'project_coordinator',
    ]


class ProjectControlsViewMixin(RoleRequiredMixin):
    allowed_roles = [
        'admin', 'project_manager', 'construction_manager', 'office_engineer',
        'engineer', 'inspector', 'owner', 'quantity_surveyor',
        'site_engineer', 'project_coordinator', 'senior_advisor',
    ]


class ProjectControlsWriteMixin(RoleRequiredMixin):
    """Project Controls CRU: Admin, PM, CM, OE, Engineer, Site Engineer, PC."""
    allowed_roles = [
        'admin', 'project_manager', 'construction_manager', 'office_engineer',
        'engineer', 'site_engineer', 'project_coordinator',
    ]
