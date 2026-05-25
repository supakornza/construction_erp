from django.urls import path

from . import views

app_name = "ai_agent"

urlpatterns = [
    path("run/<str:agent_name>/", views.run_agent, name="run"),
    path("runs/<int:run_id>/", views.run_detail, name="run_detail"),
]
