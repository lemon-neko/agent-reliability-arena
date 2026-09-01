"""FastAPI control plane and SSE trace surface."""

from __future__ import annotations

import asyncio
import json
from contextlib import asynccontextmanager
from typing import Annotated, Literal
from uuid import uuid4

from fastapi import BackgroundTasks, Depends, FastAPI, Header, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from arena.application.service import ArenaService
from arena.domain.models import RunStatus
from arena.domain.risk import AgentNetworkScope, AssessmentProfile, AssessmentStatus, RiskRunStatus
from arena.infrastructure.config import Settings
from arena.infrastructure.config import settings as default_settings
from arena.infrastructure.telemetry import configure_telemetry
from arena.runtime.reference_agents import hardened_reference_step, vulnerable_reference_step
from arena.runtime.step_protocol import StepProtocolError, StepRequest, StepResponse


class TournamentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    agent_ids: list[str] = Field(min_length=1, max_length=10)
    scenario_ids: list[str] = Field(min_length=1, max_length=50)
    repetitions: int = Field(default=3, ge=1, le=20)


class ApprovalDecision(BaseModel):
    decision: Literal["approve", "reject"]


class AgentTargetCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=500)
    endpoint_url: str = Field(min_length=8, max_length=500)
    network_scope: AgentNetworkScope = AgentNetworkScope.LOCAL
    auth_header_name: str | None = Field(default=None, max_length=100)
    auth_env_var: str | None = Field(default=None, max_length=80)
    repository_url: str | None = Field(default=None, max_length=500)
    version: str = Field(default="unversioned", min_length=1, max_length=80)
    capabilities: list[str] = Field(default_factory=list, max_length=20)


class AssessmentCreate(BaseModel):
    target_id: str
    name: str = Field(min_length=1, max_length=200)
    profile: AssessmentProfile = AssessmentProfile.QUICK
    seed: int = Field(default=20260901, ge=0)
    concurrency: int | None = Field(default=None, ge=1, le=8)


def create_app(settings: Settings | None = None) -> FastAPI:
    active_settings = settings or default_settings

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        configure_telemetry()
        active_settings.runtime_dir.mkdir(parents=True, exist_ok=True)
        app.state.service = ArenaService.create(active_settings)
        yield

    app = FastAPI(
        title="Agent Reliability Arena",
        version="0.2.0",
        lifespan=lifespan,
    )

    def service(request: Request) -> ArenaService:
        return request.app.state.service

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok", "mode": active_settings.arena_env}

    @app.post("/examples/agents/hardened/step")
    def hardened_reference_agent(payload: StepRequest) -> StepResponse:
        return hardened_reference_step(payload)

    @app.post("/examples/agents/vulnerable/step")
    def vulnerable_reference_agent(payload: StepRequest) -> StepResponse:
        return vulnerable_reference_step(payload)

    @app.get("/api/scenarios")
    def scenarios(arena: ArenaService = Depends(service)) -> list[dict]:
        return [
            scenario.model_dump(
                mode="json", exclude={"fixtures", "scripted_actions", "scripted_answer"}
            )
            for scenario in arena.catalog.load()
        ]

    @app.get("/api/v1/risk-cases")
    def risk_cases(arena: ArenaService = Depends(service)) -> list[dict]:
        return [
            case.model_dump(
                mode="json",
                exclude={"fixtures", "oracle"},
            )
            for case in arena.risk_catalog.load()
        ]

    @app.get("/api/v1/agent-targets")
    def agent_targets(arena: ArenaService = Depends(service)) -> list[dict]:
        return [target.model_dump(mode="json") for target in arena.store.agent_targets()]

    @app.post("/api/v1/agent-targets", status_code=status.HTTP_201_CREATED)
    def create_agent_target(
        payload: AgentTargetCreate,
        arena: ArenaService = Depends(service),
    ) -> dict:
        if active_settings.is_demo:
            raise HTTPException(405, "demo mode is read-only")
        target = arena.register_agent_target(**payload.model_dump())
        return target.model_dump(mode="json")

    @app.post("/api/v1/agent-targets/{target_id}/validate")
    def validate_agent_target(
        target_id: str,
        arena: ArenaService = Depends(service),
    ) -> dict:
        if active_settings.is_demo:
            raise HTTPException(405, "demo mode is read-only")
        try:
            return arena.validate_agent_target(target_id)
        except KeyError as error:
            raise HTTPException(404, "Agent target not found") from error
        except StepProtocolError as error:
            raise HTTPException(422, str(error)) from error

    @app.get("/api/v1/assessments")
    def assessments(
        target_id: str | None = None,
        arena: ArenaService = Depends(service),
    ) -> list[dict]:
        return [
            item.model_dump(mode="json")
            for item in arena.store.assessments(target_id=target_id)
        ]

    @app.post("/api/v1/assessments", status_code=status.HTTP_202_ACCEPTED)
    def create_assessment(
        payload: AssessmentCreate,
        background: BackgroundTasks,
        arena: ArenaService = Depends(service),
    ) -> dict:
        if active_settings.is_demo:
            raise HTTPException(405, "demo mode is read-only")
        try:
            assessment = arena.create_assessment(**payload.model_dump())
        except KeyError as error:
            raise HTTPException(422, "unknown Agent target") from error
        if active_settings.celery_task_always_eager:
            background.add_task(arena.execute_assessment, assessment.id)
        else:
            from arena.infrastructure.tasks import run_assessment

            run_assessment.delay(assessment.id)
        return {
            "assessment": assessment.model_dump(mode="json"),
            "run_count": assessment.total_runs,
        }

    @app.get("/api/v1/assessments/{assessment_id}")
    def assessment_detail(
        assessment_id: str,
        arena: ArenaService = Depends(service),
    ) -> dict:
        assessment = arena.store.assessment(assessment_id)
        if assessment is None:
            raise HTTPException(404, "assessment not found")
        report = arena.store.risk_report(assessment_id)
        return {
            "assessment": assessment.model_dump(mode="json"),
            "runs": [
                run.model_dump(mode="json")
                for run in arena.store.risk_test_runs(assessment_id)
            ],
            "findings": [
                finding.model_dump(mode="json")
                for finding in arena.store.risk_findings(assessment_id)
            ],
            "report": report.model_dump(mode="json") if report else None,
        }

    @app.get("/api/v1/assessments/{assessment_id}/events")
    async def assessment_events(
        assessment_id: str,
        request: Request,
        arena: ArenaService = Depends(service),
        last_event_id: Annotated[str | None, Header(alias="Last-Event-ID")] = None,
    ) -> EventSourceResponse:
        if arena.store.assessment(assessment_id) is None:
            raise HTTPException(404, "assessment not found")
        try:
            cursor = max(0, int(last_event_id or 0))
        except ValueError:
            cursor = 0

        async def stream():
            nonlocal cursor
            while not await request.is_disconnected():
                current = arena.store.assessment(assessment_id)
                if current is None:
                    break
                if current.completed_runs > cursor:
                    cursor = current.completed_runs
                    recent = [
                        run.model_dump(mode="json")
                        for run in arena.store.risk_test_runs(assessment_id)
                        if run.status != RiskRunStatus.QUEUED
                    ][-8:]
                    yield {
                        "id": str(cursor),
                        "event": "progress",
                        "data": json.dumps(
                            {
                                "assessment": current.model_dump(mode="json"),
                                "recent_runs": recent,
                            },
                            ensure_ascii=False,
                        ),
                    }
                if current.status in {
                    AssessmentStatus.COMPLETED,
                    AssessmentStatus.FAILED,
                    AssessmentStatus.CANCELLED,
                }:
                    yield {"event": "end", "data": current.status.value}
                    break
                await asyncio.sleep(0.25)

        return EventSourceResponse(stream(), ping=10)

    @app.post("/api/v1/assessments/{assessment_id}/cancel")
    def cancel_assessment(
        assessment_id: str,
        arena: ArenaService = Depends(service),
    ) -> dict:
        if active_settings.is_demo:
            raise HTTPException(405, "demo mode is read-only")
        try:
            value = arena.store.request_assessment_cancel(assessment_id)
        except KeyError as error:
            raise HTTPException(404, "assessment not found") from error
        return value.model_dump(mode="json")

    @app.get("/api/v1/test-runs/{run_id}")
    def risk_test_run(run_id: str, arena: ArenaService = Depends(service)) -> dict:
        run = arena.store.risk_test_run(run_id)
        if run is None:
            raise HTTPException(404, "risk test run not found")
        return {
            "run": run.model_dump(mode="json"),
            "events": [
                event.model_dump(mode="json") for event in arena.store.risk_events(run_id)
            ],
        }

    @app.get("/api/v1/reports/{assessment_id}.html", response_class=HTMLResponse)
    def risk_report_html(
        assessment_id: str,
        arena: ArenaService = Depends(service),
    ) -> HTMLResponse:
        value = arena.store.risk_report_html(assessment_id)
        if value is None:
            raise HTTPException(404, "risk report not found")
        return HTMLResponse(value, headers={"Content-Disposition": "inline"})

    @app.get("/api/v1/reports/{assessment_id}")
    def risk_report(assessment_id: str, arena: ArenaService = Depends(service)) -> dict:
        report = arena.store.risk_report(assessment_id)
        if report is None:
            raise HTTPException(404, "risk report not found")
        return report.model_dump(mode="json")

    @app.post("/api/v1/reports/{assessment_id}/attestation")
    def risk_attestation(
        assessment_id: str,
        arena: ArenaService = Depends(service),
    ) -> dict:
        if active_settings.is_demo:
            raise HTTPException(405, "demo mode is read-only")
        try:
            return arena.create_public_attestation(assessment_id).model_dump(mode="json")
        except KeyError as error:
            raise HTTPException(404, "risk report not found") from error
        except ValueError as error:
            raise HTTPException(422, str(error)) from error

    @app.get("/api/v1/public-leaderboard")
    def public_leaderboard(arena: ArenaService = Depends(service)) -> list[dict]:
        return arena.public_leaderboard()

    @app.get("/api/agents")
    def agents(arena: ArenaService = Depends(service)) -> list[dict]:
        return [profile.model_dump(mode="json") for profile in arena.store.agents()]

    @app.post("/api/tournaments", status_code=status.HTTP_202_ACCEPTED)
    def create_tournament(
        payload: TournamentCreate,
        background: BackgroundTasks,
        arena: ArenaService = Depends(service),
        idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
    ) -> dict:
        if active_settings.is_demo:
            raise HTTPException(405, "demo mode is read-only")
        profiles = {profile.id for profile in arena.store.agents()}
        if not set(payload.agent_ids) <= profiles:
            raise HTTPException(422, "unknown agent profile")
        available = {scenario.id: scenario.version for scenario in arena.catalog.load()}
        if not set(payload.scenario_ids) <= available.keys():
            raise HTTPException(422, "unknown scenario")
        tournament, runs, created = arena.store.create_tournament(
            name=payload.name,
            agent_ids=payload.agent_ids,
            scenario_versions={
                scenario_id: available[scenario_id] for scenario_id in payload.scenario_ids
            },
            repetitions=payload.repetitions,
            idempotency_key=idempotency_key or f"generated-{uuid4().hex}",
        )
        if created:
            if active_settings.celery_task_always_eager:
                background.add_task(arena.execute_tournament, tournament.id)
            else:
                from arena.infrastructure.tasks import run_tournament

                run_tournament.delay(tournament.id)
        return {
            "tournament": tournament.model_dump(mode="json"),
            "run_count": len(runs),
            "created": created,
        }

    @app.get("/api/tournaments/{tournament_id}")
    def tournament(tournament_id: str, arena: ArenaService = Depends(service)) -> dict:
        value = arena.store.tournament(tournament_id)
        if value is None:
            raise HTTPException(404, "tournament not found")
        return {
            "tournament": value.model_dump(mode="json"),
            "runs": [run.model_dump(mode="json") for run in arena.store.runs(tournament_id)],
        }

    @app.get("/api/runs/{run_id}")
    def run(run_id: str, arena: ArenaService = Depends(service)) -> dict:
        value = arena.store.run(run_id)
        if value is None:
            raise HTTPException(404, "run not found")
        evaluation = arena.store.evaluation(run_id)
        return {
            "run": value.model_dump(mode="json"),
            "evaluation": evaluation.model_dump(mode="json") if evaluation else None,
            "events": [event.model_dump(mode="json") for event in arena.store.events(run_id)],
        }

    @app.get("/api/runs/{run_id}/events")
    async def events(
        run_id: str,
        request: Request,
        arena: ArenaService = Depends(service),
        last_event_id: Annotated[str | None, Header(alias="Last-Event-ID")] = None,
    ) -> EventSourceResponse:
        if arena.store.run(run_id) is None:
            raise HTTPException(404, "run not found")
        try:
            cursor = max(0, int(last_event_id or 0))
        except ValueError:
            cursor = 0

        async def stream():
            nonlocal cursor
            while not await request.is_disconnected():
                for event in arena.store.events(run_id, after_sequence=cursor):
                    cursor = event.sequence
                    yield {
                        "id": str(cursor),
                        "event": event.kind.value,
                        "data": json.dumps(event.model_dump(mode="json"), ensure_ascii=False),
                    }
                current = arena.store.run(run_id)
                if current and current.status in {
                    RunStatus.COMPLETED,
                    RunStatus.FAILED,
                    RunStatus.TIMED_OUT,
                    RunStatus.WAITING_APPROVAL,
                }:
                    yield {"event": "end", "data": current.status.value}
                    break
                await asyncio.sleep(0.25)

        return EventSourceResponse(stream(), ping=10)

    @app.post("/api/runs/{run_id}/approvals/{approval_id}")
    def decide_approval(
        run_id: str,
        approval_id: str,
        payload: ApprovalDecision,
        background: BackgroundTasks,
        arena: ArenaService = Depends(service),
    ) -> dict:
        if active_settings.is_demo:
            raise HTTPException(405, "demo mode is read-only")
        approval = arena.store.approval(approval_id)
        if approval is None or approval.run_id != run_id:
            raise HTTPException(404, "approval not found")
        decided = arena.store.decide_approval(approval_id, payload.decision == "approve")
        if decided.status == "approved":
            background.add_task(arena.execute_run, run_id, approved=True)
        return decided.model_dump(mode="json")

    @app.get("/api/leaderboard")
    def leaderboard(arena: ArenaService = Depends(service)) -> list[dict]:
        return arena.store.leaderboard()

    @app.get("/api/reports/{tournament_id}")
    def report(tournament_id: str, arena: ArenaService = Depends(service)) -> dict:
        tournament_value = arena.store.tournament(tournament_id)
        if tournament_value is None:
            raise HTTPException(404, "report not found")
        run_values = arena.store.runs(tournament_id)
        return {
            "schema_version": 1,
            "tournament": tournament_value.model_dump(mode="json"),
            "runs": [
                {
                    "run": run_value.model_dump(mode="json"),
                    "evaluation": evaluation.model_dump(mode="json")
                    if (evaluation := arena.store.evaluation(run_value.id))
                    else None,
                }
                for run_value in run_values
            ],
            "leaderboard": arena.store.leaderboard(),
        }

    return app


app = create_app()
