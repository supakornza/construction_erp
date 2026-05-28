from django.contrib import admin

from .models import AgentMessage, AgentRun


class AgentMessageInline(admin.TabularInline):
    model = AgentMessage
    extra = 0
    readonly_fields = ("step", "role", "content", "created_at")
    can_delete = False


@admin.register(AgentRun)
class AgentRunAdmin(admin.ModelAdmin):
    list_display = ("id", "agent_name", "status", "user", "project", "model",
                    "input_tokens", "output_tokens", "cost_usd", "created_at")
    list_filter = ("agent_name", "status", "model")
    search_fields = ("agent_name", "error")
    readonly_fields = tuple(f.name for f in AgentRun._meta.fields)
    inlines = [AgentMessageInline]
