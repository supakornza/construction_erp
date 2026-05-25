from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST

from .agents.daily_report import DailyReportAgent
from .models import AgentRun

AGENTS = {
    "daily_report": DailyReportAgent,
}


@login_required
@require_POST
def run_agent(request, agent_name: str):
    agent_cls = AGENTS.get(agent_name)
    if not agent_cls:
        return JsonResponse({"error": f"Unknown agent: {agent_name}"}, status=404)

    message = request.POST.get("message", "").strip()
    if not message:
        return JsonResponse({"error": "message is required"}, status=400)

    project_id = request.POST.get("project_id") or None
    project = None
    if project_id:
        from apps.projects.models import Project
        project = get_object_or_404(Project, pk=project_id)

    run = agent_cls().run(message, user=request.user, project=project)
    return JsonResponse({
        "run_id": run.id,
        "status": run.status,
        "output": run.output_payload,
        "tokens": {"in": run.input_tokens, "out": run.output_tokens,
                   "cache_read": run.cache_read_tokens},
        "cost_usd": str(run.cost_usd),
    })


@login_required
def run_detail(request, run_id: int):
    run = get_object_or_404(AgentRun, pk=run_id)
    return JsonResponse({
        "id": run.id, "agent": run.agent_name, "status": run.status,
        "output": run.output_payload, "error": run.error,
        "cost_usd": str(run.cost_usd),
        "messages": [
            {"step": m.step, "role": m.role, "content": m.content}
            for m in run.messages.all()
        ],
    })
