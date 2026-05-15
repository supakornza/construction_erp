from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.dashboard.urls', namespace='dashboard')),
    path('accounts/', include('apps.accounts.urls', namespace='accounts')),
    path('projects/', include('apps.projects.urls', namespace='projects')),
    path('daily-reports/', include('apps.daily_reports.urls', namespace='daily_reports')),
    path('manpower/', include('apps.manpower.urls', namespace='manpower')),
    path('equipment/', include('apps.equipment.urls', namespace='equipment')),
    path('materials/', include('apps.materials.urls', namespace='materials')),
    path('procurement/', include('apps.procurement.urls', namespace='procurement')),
    path('boq/', include('apps.boq.urls', namespace='boq')),
    path('safety/', include('apps.safety.urls', namespace='safety')),
    path('quality/', include('apps.quality.urls', namespace='quality')),
    path('documents/', include('apps.documents.urls', namespace='documents')),
    path('reports/', include('apps.reports.urls', namespace='reports')),
    path('api/v1/', include('apps.api.urls')),
    path('project-controls/', include('apps.project_controls.urls', namespace='project_controls')),
    path('cost-control/', include('apps.cost_control.urls', namespace='cost_control')),
    path('tide-monitor/', include('apps.tide_monitor.urls', namespace='tide_monitor')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
