def current_project(request):
    from apps.projects.models import Project
    pid = request.session.get('current_project_id')
    project = Project.objects.filter(pk=pid).first() if pid else None
    return {'current_project': project}
