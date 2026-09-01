"""Application service coordinating catalog, persistence, and execution."""

from __future__ import annotations

import os
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import uuid4

from arena.application.engine import ArenaEngine
from arena.application.reporting import create_attestation, render_risk_report
from arena.application.risk_engine import RiskEngine
from arena.domain.models import AgentProfile, RunStatus
from arena.domain.risk import (
    AgentTarget,
    Assessment,
    AssessmentProfile,
    AssessmentStatus,
    RiskRunStatus,
    RiskTestRun,
)
from arena.domain.risk_evaluation import build_risk_report
from arena.infrastructure.config import Settings
from arena.infrastructure.registry import load_public_leaderboard
from arena.infrastructure.store import ArenaStore
from arena.infrastructure.telemetry import tracer
from arena.runtime.risk_scenarios import RiskCatalog, profile_defaults
from arena.runtime.scenarios import ScenarioCatalog
from arena.runtime.step_protocol import HTTPAgentClient, StepClient

RiskClientFactory = Callable[[AgentTarget, float], StepClient]


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
    risk_catalog: RiskCatalog
    risk_engine: RiskEngine
    risk_client_factory: RiskClientFactory

    @classmethod
    def create(cls, settings: Settings) -> ArenaService:
        store = ArenaStore(settings.database_url)
        store.upsert_agents(built_in_agents(settings))
        return cls(
            settings,
            store,
            ScenarioCatalog(settings.scenario_dir),
            ArenaEngine(settings.runtime_dir),
            RiskCatalog(settings.risk_pack_dir),
            RiskEngine(settings.runtime_dir),
            lambda target, timeout: HTTPAgentClient(target, timeout_seconds=timeout),
        )

    def register_agent_target(self, **values) -> AgentTarget:
        target = AgentTarget(
            id=f"target-{uuid4().hex[:12]}",
            **values,
        )
        return self.store.save_agent_target(target)

    def validate_agent_target(self, target_id: str) -> dict:
        target = self.store.agent_target(target_id)
        if target is None:
            raise KeyError(target_id)
        client = self.risk_client_factory(target, 5)
        check = getattr(client, "check_contract", None)
        if check is None:
            raise RuntimeError("risk client does not support contract validation")
        return check()

    def create_assessment(
        self,
        *,
        target_id: str,
        name: str,
        profile: AssessmentProfile,
        seed: int = 20260901,
        concurrency: int | None = None,
    ) -> Assessment:
        if self.store.agent_target(target_id) is None:
            raise KeyError(target_id)
        repetitions, default_concurrency, total = profile_defaults(profile)
        assessment = Assessment(
            id=f"assessment-{uuid4().hex[:12]}",
            target_id=target_id,
            name=name,
            profile=profile,
            seed=seed,
            repetitions=repetitions,
            concurrency=concurrency or default_concurrency,
            total_runs=total,
        )
        specs = self.risk_catalog.materialize(profile, seed=seed)
        runs = tuple(
            RiskTestRun(
                id=f"risk-run-{uuid4().hex[:12]}",
                assessment_id=assessment.id,
                target_id=target_id,
                case_id=spec.case.id,
                case_version=spec.case.version,
                variant_id=spec.variant_id,
                mutation=spec.mutation,
                seed=spec.seed,
                repetition=repetition,
            )
            for spec in specs
            for repetition in range(1, repetitions + 1)
        )
        self.store.create_assessment(assessment, runs)
        return assessment

    def execute_assessment(self, assessment_id: str) -> None:
        try:
            self._execute_assessment(assessment_id)
        except Exception:
            assessment = self.store.assessment(assessment_id)
            if assessment is not None:
                self.store.save_assessment(
                    assessment.model_copy(
                        update={
                            "status": AssessmentStatus.FAILED,
                            "completed_at": datetime.now(UTC),
                        }
                    )
                )
            raise

    def _execute_assessment(self, assessment_id: str) -> None:
        assessment = self.store.assessment(assessment_id)
        if assessment is None:
            raise KeyError(assessment_id)
        target = self.store.agent_target(assessment.target_id)
        if target is None:
            raise KeyError(assessment.target_id)
        assessment = self.store.save_assessment(
            assessment.model_copy(
                update={"status": AssessmentStatus.RUNNING, "started_at": datetime.now(UTC)}
            )
        )
        specs = {
            spec.variant_id: spec
            for spec in self.risk_catalog.materialize(assessment.profile, seed=assessment.seed)
        }
        runs = self.store.risk_test_runs(assessment.id)

        def cancelled() -> bool:
            current = self.store.assessment(assessment.id)
            return bool(current and current.cancel_requested)

        def execute_one(run: RiskTestRun):
            spec = specs[run.variant_id]
            client = self.risk_client_factory(target, spec.case.timeout_seconds)
            return self.risk_engine.execute(
                run=run,
                spec=spec,
                client=client,
                cancelled=cancelled,
            )

        with ThreadPoolExecutor(max_workers=assessment.concurrency) as executor:
            futures = [executor.submit(execute_one, run) for run in runs]
            for future in as_completed(futures):
                outcome = future.result()
                self.store.save_risk_outcome(outcome)
                current_runs = self.store.risk_test_runs(assessment.id)
                completed = sum(run.status != RiskRunStatus.QUEUED for run in current_runs)
                failed = sum(
                    run.status in {RiskRunStatus.FAILED, RiskRunStatus.TIMED_OUT}
                    for run in current_runs
                )
                assessment = self.store.save_assessment(
                    assessment.model_copy(
                        update={"completed_runs": completed, "failed_runs": failed}
                    )
                )

        refreshed = self.store.assessment(assessment.id) or assessment
        final_status = (
            AssessmentStatus.CANCELLED if refreshed.cancel_requested else AssessmentStatus.COMPLETED
        )
        assessment = self.store.save_assessment(
            refreshed.model_copy(
                update={"status": final_status, "completed_at": datetime.now(UTC)}
            )
        )
        if final_status == AssessmentStatus.COMPLETED:
            self._build_and_save_report(assessment, target)

    def _build_and_save_report(self, assessment: Assessment, target: AgentTarget) -> None:
        cases = {case.id: case for case in self.risk_catalog.load()}
        report = build_risk_report(
            assessment=assessment,
            target=target,
            runs=self.store.risk_test_runs(assessment.id),
            findings=self.store.risk_findings(assessment.id),
            cases=cases,
        )
        self.store.save_risk_report(report, render_risk_report(report))

    def create_public_attestation(self, assessment_id: str):
        report = self.store.risk_report(assessment_id)
        if report is None:
            raise KeyError(assessment_id)
        attestation = create_attestation(report)
        return self.store.save_attestation(assessment_id, attestation)

    def public_leaderboard(self) -> list[dict]:
        return load_public_leaderboard(self.settings.registry_dir)

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
