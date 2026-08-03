"""Application service coordinating catalog, persistence, and execution."""

from __future__ import annotations

import os
from dataclasses import dataclass

from arena.config import Settings
from arena.domain import AgentProfile, RunStatus
from arena.engine import ArenaEngine
from arena.scenarios import ScenarioCatalog
from arena.store import ArenaStore
from arena.telemetry import tracer


def built_in_agents(settings: Settings) -> tuple[AgentProfile, ...]:
    profiles = [
        AgentProfile(
            id="minimal-fake",
            name="最小工具 Agent · 确定性假模型",
            runtime="minimal",
            model="fake-deterministic",
            base_url="fake://deterministic",
        ),
        AgentProfile(
            id="langgraph-fake",
            name="LangGraph Agent · 确定性假模型",
            runtime="langgraph",
            model="fake-deterministic",
            base_url="fake://deterministic",
        ),
    ]
    if settings.model_base_url and not settings.model_base_url.startswith("fake://"):
        profiles.extend(
            [
                AgentProfile(
                    id="minimal-configured",
                    name=f"最小工具 Agent · {settings.model_name}",
                    runtime="minimal",
                    model=settings.model_name,
                    base_url=settings.model_base_url,
                ),
                AgentProfile(
                    id="langgraph-configured",
                    name=f"LangGraph Agent · {settings.model_name}",
                    runtime="langgraph",
                    model=settings.model_name,
                    base_url=settings.model_base_url,
                ),
            ]
        )
    return tuple(profiles)


@dataclass
class ArenaService:
    settings: Settings
    store: ArenaStore
    catalog: ScenarioCatalog
    engine: ArenaEngine

    @classmethod
    def create(cls, settings: Settings) -> ArenaService:
        store = ArenaStore(settings.database_url)
        store.upsert_agents(built_in_agents(settings))
        return cls(
            settings,
            store,
            ScenarioCatalog(settings.scenario_dir),
            ArenaEngine(settings.runtime_dir),
        )

    def execute_run(self, run_id: str, *, approved: bool = False) -> None:
        run = self.store.run(run_id)
        if run is None:
            raise KeyError(run_id)
        scenario = self.catalog.get(run.scenario_id)
        agent = self.store.agent(run.agent_id)
        if agent is None:
            raise KeyError(run.agent_id)
        if not agent.base_url.startswith("fake://") and not self.settings.allow_external_models:
            raise PermissionError("external model calls are disabled")
        with tracer.start_as_current_span("arena.run") as span:
            span.set_attribute("arena.run_id", run.id)
            span.set_attribute("arena.scenario_id", scenario.id)
            span.set_attribute("arena.agent_runtime", agent.runtime)
            outcome = self.engine.execute(
                run=run,
                scenario=scenario,
                agent=agent,
                api_key=os.getenv("MODEL_API_KEY", ""),
                approved=approved,
            )
        self.store.save_outcome(outcome)

    def execute_tournament(self, tournament_id: str) -> None:
        if self.store.tournament(tournament_id) is None:
            raise KeyError(tournament_id)
        for run in self.store.runs(tournament_id):
            if run.status in {RunStatus.QUEUED, RunStatus.RUNNING}:
                self.execute_run(run.id)
