"""Run orchestration independent of HTTP, Celery, and persistence."""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from arena.domain.evaluation import DeterministicEvaluator, Evaluator
from arena.domain.models import (
    AgentProfile,
    ApprovalRequest,
    Evaluation,
    Run,
    RunStatus,
    ScenarioSpec,
    TraceEvent,
    TraceKind,
)
from arena.runtime.agents import AGENT_RUNTIMES
from arena.runtime.providers import DeterministicProvider, ModelProvider, OpenAICompatibleProvider
from arena.runtime.sandbox import RunSandbox
from arena.runtime.tools import ApprovalRequired, ToolGateway
from arena.runtime.tracing import TraceRecorder


@dataclass
class RunOutcome:
    run: Run
    events: list[TraceEvent]
    evaluation: Evaluation | None
    approval: ApprovalRequest | None = None


class ArenaEngine:
    def __init__(self, runtime_root: Path, evaluator: Evaluator | None = None) -> None:
        self.runtime_root = runtime_root
        self.evaluator = evaluator or DeterministicEvaluator()

    def execute(
        self,
        *,
        run: Run,
        scenario: ScenarioSpec,
        agent: AgentProfile,
        api_key: str = "",
        approved: bool = False,
        provider: ModelProvider | None = None,
    ) -> RunOutcome:
        run = run.model_copy(update={"status": RunStatus.RUNNING, "started_at": datetime.now(UTC)})
        protected = tuple(
            value for value in (*scenario.fixtures.secrets.values(), api_key) if value
        )
        recorder = TraceRecorder(run.id, protected_values=protected)
        recorder.record(TraceKind.RUN, "run.started", {"scenario": scenario.id, "agent": agent.id})
        sandbox = RunSandbox.create(scenario, self.runtime_root)
        started = time.perf_counter()
        try:
            gateway = ToolGateway(scenario, sandbox, approved=approved)
            selected_provider = provider or self._provider(agent, api_key)
            runtime = AGENT_RUNTIMES[agent.runtime]
            answer = runtime.run(scenario, selected_provider, gateway, recorder)
            elapsed = (time.perf_counter() - started) * 1000
            run = run.model_copy(
                update={
                    "status": RunStatus.COMPLETED,
                    "answer": answer,
                    "completed_at": datetime.now(UTC),
                }
            )
            recorder.record(TraceKind.RUN, "run.completed", {"answer": answer}, duration_ms=elapsed)
            evaluation = self.evaluator.evaluate(run, scenario, recorder.events)
            recorder.record(
                TraceKind.EVALUATION,
                "evaluation.completed",
                {"score": evaluation.score.model_dump(), "total": evaluation.score.total},
            )
            return RunOutcome(run, recorder.events, evaluation)
        except ApprovalRequired as request:
            elapsed = (time.perf_counter() - started) * 1000
            run = run.model_copy(update={"status": RunStatus.WAITING_APPROVAL})
            approval = ApprovalRequest(
                id=f"approval-{uuid4().hex[:12]}",
                run_id=run.id,
                tool_name=request.tool,
                arguments=request.arguments,
                reason=request.reason,
            )
            recorder.record(
                TraceKind.APPROVAL,
                "approval.requested",
                approval.model_dump(mode="json"),
                duration_ms=elapsed,
            )
            return RunOutcome(run, recorder.events, None, approval)
        except Exception as error:
            elapsed = (time.perf_counter() - started) * 1000
            run = run.model_copy(
                update={
                    "status": RunStatus.FAILED,
                    "error": type(error).__name__,
                    "completed_at": datetime.now(UTC),
                }
            )
            recorder.record(
                TraceKind.ERROR,
                "run.failed",
                {"error_type": type(error).__name__, "message": str(error)[:500]},
                duration_ms=elapsed,
            )
            evaluation = self.evaluator.evaluate(run, scenario, recorder.events)
            return RunOutcome(run, recorder.events, evaluation)
        finally:
            sandbox.cleanup()

    @staticmethod
    def _provider(agent: AgentProfile, api_key: str) -> ModelProvider:
        if agent.base_url.startswith("fake://"):
            return DeterministicProvider()
        return OpenAICompatibleProvider(
            base_url=agent.base_url,
            api_key=api_key,
            model=agent.model,
            timeout_seconds=agent.timeout_seconds,
            input_cost_per_million=agent.input_cost_per_million,
            output_cost_per_million=agent.output_cost_per_million,
        )
