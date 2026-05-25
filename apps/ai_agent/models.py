from django.conf import settings
from django.db import models


class AgentRun(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        RUNNING = "running", "Running"
        SUCCESS = "success", "Success"
        FAILED = "failed", "Failed"
        AWAITING_APPROVAL = "awaiting_approval", "Awaiting Approval"

    agent_name = models.CharField(max_length=64, db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="agent_runs",
    )
    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="agent_runs",
    )
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.PENDING)
    model = models.CharField(max_length=64, blank=True)

    input_payload = models.JSONField(default=dict, blank=True)
    output_payload = models.JSONField(default=dict, blank=True)
    error = models.TextField(blank=True)

    input_tokens = models.IntegerField(default=0)
    output_tokens = models.IntegerField(default=0)
    cache_read_tokens = models.IntegerField(default=0)
    cache_creation_tokens = models.IntegerField(default=0)
    cost_usd = models.DecimalField(max_digits=10, decimal_places=6, default=0)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.agent_name} [{self.status}] @ {self.created_at:%Y-%m-%d %H:%M}"


class AgentMessage(models.Model):
    """Per-step log inside an AgentRun (assistant turn, tool call, tool result)."""

    class Role(models.TextChoices):
        USER = "user", "User"
        ASSISTANT = "assistant", "Assistant"
        TOOL_USE = "tool_use", "Tool use"
        TOOL_RESULT = "tool_result", "Tool result"

    run = models.ForeignKey(AgentRun, on_delete=models.CASCADE, related_name="messages")
    step = models.PositiveIntegerField()
    role = models.CharField(max_length=16, choices=Role.choices)
    content = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("step",)
        unique_together = ("run", "step")
