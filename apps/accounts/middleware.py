from django.shortcuts import redirect
from django.urls import reverse

EXEMPT_PREFIXES = (
    '/accounts/login/',
    '/accounts/logout/',
    '/accounts/select-project/',
    '/accounts/password-reset',
    '/admin/',
    '/api/',
    '/static/',
    '/media/',
    '/i18n/',
)


class ProjectSelectionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.current_project = None
        if request.user.is_authenticated:
            pid = request.session.get('current_project_id')
            if pid:
                from apps.projects.models import Project
                request.current_project = Project.objects.filter(pk=pid).first()
            else:
                path = request.path
                if not any(path.startswith(p) for p in EXEMPT_PREFIXES):
                    select_url = reverse('accounts:select_project')
                    if path != select_url:
                        return redirect(select_url)
        return self.get_response(request)
