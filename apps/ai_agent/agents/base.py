"""Base agent: agentic loop with tool use, logging, and cost accounting."""
from __future__ import annotations

from dataclasses import dataclass, field
from django.utils import timezone

from ..models import AgentMessage, AgentRun
from ..services.client import DEFAULT_MODEL, estimate_cost, get_client
from ..services.tools import get_definitions, run_tool


@dataclass
class BaseAgent:
    name: str = "base"
    model: str = DEFAULT_MODEL
    system_prompt: str = "You are a helpful assistant."
    tool_names: list[str] = field(default_factory=list)
    max_steps: int = 10
    max_tokens: int = 4096
    # Set True to cache the (long, stable) system prompt + tools block.
    cache_system: bool = True

    def run(self, user_message: str, *, user=None, project=None, extra_input: dict | None = None) -> AgentRun:
        agent_run = AgentRun.objects.create(
            agent_name=self.name,
            user=user,
            project=project,
            model=self.model,
            status=AgentRun.Status.RUNNING,
            input_payload={"message": user_message, **(extra_input or {})},
        )
        try:
            self._loop(agent_run, user_message)
            agent_run.status = AgentRun.Status.SUCCESS
        except Exception as e:
            agent_run.status = AgentRun.Status.FAILED
            agent_run.error = f"{type(e).__name__}: {e}"
        finally:
            agent_run.finished_at = timezone.now()
            agent_run.save()
        return agent_run

    # --- internals -----------------------------------------------------------

    def _system_block(self):
        block = {"type": "text", "text": self.system_prompt}
        if self.cache_system:
            block["cache_control"] = {"type": "ephemeral"}
        return [block]

    def _loop(self, run: AgentRun, user_message: str):
        client = get_client()
        tools = get_definitions(self.tool_names) if self.tool_names else None
        messages = [{"role": "user", "content": user_message}]
        ctx = {"run": run, "user": run.user, "project": run.project}

        step = 0
        AgentMessage.objects.create(run=run, step=step, role=AgentMessage.Role.USER,
                                    content={"text": user_message})

        for _ in range(self.max_steps):
            step += 1
            kwargs = dict(
                model=self.model,
                max_tokens=self.max_tokens,
                system=self._system_block(),
                messages=messages,
            )
            if tools:
                kwargs["tools"] = tools

            resp = client.messages.create(**kwargs)
            self._account_usage(run, resp)

            assistant_content = [block.model_dump() for block in resp.content]
            messages.append({"role": "assistant", "content": assistant_content})
            AgentMessage.objects.create(run=run, step=step, role=AgentMessage.Role.ASSISTANT,
                                        content={"blocks": assistant_content,
                                                 "stop_reason": resp.stop_reason})

            if resp.stop_reason != "tool_use":
                # Final assistant message.
                text = "".join(b.get("text", "") for b in assistant_content if b.get("type") == "text")
                run.output_payload = {"text": text, "stop_reason": resp.stop_reason}
                return

            # Execute every tool_use block in this assistant turn.
            tool_results = []
            for block in assistant_content:
                if block.get("type") != "tool_use":
                    continue
                step += 1
                try:
                    result = run_tool(block["name"], block.get("input", {}), ctx)
                    is_error = False
                except Exception as e:
                    result = f"{type(e).__name__}: {e}"
                    is_error = True
                AgentMessage.objects.create(
                    run=run, step=step, role=AgentMessage.Role.TOOL_RESULT,
                    content={"tool_use_id": block["id"], "name": block["name"],
                             "result": result, "is_error": is_error},
                )
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block["id"],
                    "content": str(result)[:50_000],
                    "is_error": is_error,
                })
            messages.append({"role": "user", "content": tool_results})

        raise RuntimeError(f"Exceeded max_steps ({self.max_steps}) without final answer.")

    def _account_usage(self, run: AgentRun, resp):
        u = resp.usage
        run.input_tokens += getattr(u, "input_tokens", 0) or 0
        run.output_tokens += getattr(u, "output_tokens", 0) or 0
        run.cache_read_tokens += getattr(u, "cache_read_input_tokens", 0) or 0
        run.cache_creation_tokens += getattr(u, "cache_creation_input_tokens", 0) or 0
        run.cost_usd = (run.cost_usd or 0) + estimate_cost(self.model, {
            "input_tokens": getattr(u, "input_tokens", 0) or 0,
            "output_tokens": getattr(u, "output_tokens", 0) or 0,
            "cache_read_input_tokens": getattr(u, "cache_read_input_tokens", 0) or 0,
            "cache_creation_input_tokens": getattr(u, "cache_creation_input_tokens", 0) or 0,
        })
        run.save(update_fields=["input_tokens", "output_tokens", "cache_read_tokens",
                                "cache_creation_tokens", "cost_usd"])
