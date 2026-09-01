from __future__ import annotations

import threading
import time
from pathlib import Path

from fastapi.testclient import TestClient
from sse_starlette.sse import AppStatus

from arena.domain.risk import AssessmentProfile
from arena.infrastructure.config import Settings
from arena.interfaces.http.app import create_app
from arena.runtime.reference_agents import hardened_reference_step

ROOT = Path(__file__).resolve().parents[3]


class DirectClient:
    def step(self, request):
        return hardened_reference_step(request)

    def check_contract(self):
        return {"valid": True, "protocol": "ara-step/1", "response": "ready"}


class BrokenClient:
    def step(self, request):
        raise RuntimeError(f"synthetic endpoint failure at step {request.step}")


class ConcurrencyProbe:
    def __init__(self) -> None:
        self.active = 0
        self.peak = 0
        self.lock = threading.Lock()

    def step(self, request):
        with self.lock:
            self.active += 1
            self.peak = max(self.peak, self.active)
        try:
            time.sleep(0.005)
            return hardened_reference_step(request)
        finally:
            with self.lock:
                self.active -= 1


def test_target_quick_assessment_report_html_and_sse(tmp_path: Path) -> None:
    settings = Settings(
        arena_env="test",
        database_url=f"sqlite:///{tmp_path / 'arena.db'}",
        scenario_dir=ROOT / "packages" / "scenarios" / "catalog",
        risk_pack_dir=ROOT / "packages" / "risk-packs" / "tool-agent-baseline" / "v1",
        registry_dir=ROOT / "packages" / "registry",
        runtime_dir=tmp_path / "runs",
        celery_task_always_eager=True,
    )
    app = create_app(settings)
    with TestClient(app) as client:
        client.app.state.service.risk_client_factory = lambda target, timeout: DirectClient()
        target_response = client.post(
            "/api/v1/agent-targets",
            json={
                "name": "Local hardened",
                "endpoint_url": "http://127.0.0.1:8000/examples/agents/hardened/step",
                "version": "1.0.0",
                "repository_url": "https://github.com/example/hardened",
            },
        )
        assert target_response.status_code == 201
        target_id = target_response.json()["id"]
        assert client.post(f"/api/v1/agent-targets/{target_id}/validate").json()["valid"]
        created = client.post(
            "/api/v1/assessments",
            json={"target_id": target_id, "name": "Quick audit", "profile": "quick"},
        )
        assert created.status_code == 202 and created.json()["run_count"] == 12
        assessment_id = created.json()["assessment"]["id"]
        detail = client.get(f"/api/v1/assessments/{assessment_id}").json()
        assert detail["assessment"]["status"] == "completed"
        assert len(detail["runs"]) == 12
        assert detail["report"]["grade"] == "A"
        assert client.get(f"/api/v1/reports/{assessment_id}").json()["final_score"] == 100
        html = client.get(f"/api/v1/reports/{assessment_id}.html")
        assert html.status_code == 200 and "风险体检报告" in html.text
        # sse-starlette keeps a process-global AnyIO event; reset it between TestClient loops.
        AppStatus.should_exit_event = None
        with client.stream("GET", f"/api/v1/assessments/{assessment_id}/events") as stream:
            body = "".join(stream.iter_text())
        assert "event: progress" in body and "event: end" in body


def test_demo_mode_rejects_risk_mutations(tmp_path: Path) -> None:
    settings = Settings(
        arena_env="demo",
        database_url=f"sqlite:///{tmp_path / 'demo.db'}",
        scenario_dir=ROOT / "packages" / "scenarios" / "catalog",
        risk_pack_dir=ROOT / "packages" / "risk-packs" / "tool-agent-baseline" / "v1",
        registry_dir=ROOT / "packages" / "registry",
        runtime_dir=tmp_path / "runs",
    )
    with TestClient(create_app(settings)) as client:
        assert (
            client.post(
                "/api/v1/agent-targets",
                json={"name": "No", "endpoint_url": "http://127.0.0.1:1/step"},
            ).status_code
            == 405
        )


def test_run_failures_are_isolated_and_pre_requested_cancel_stops_matrix(
    tmp_path: Path,
) -> None:
    settings = Settings(
        arena_env="test",
        database_url=f"sqlite:///{tmp_path / 'isolation.db'}",
        scenario_dir=ROOT / "packages" / "scenarios" / "catalog",
        risk_pack_dir=ROOT / "packages" / "risk-packs" / "tool-agent-baseline" / "v1",
        registry_dir=ROOT / "packages" / "registry",
        runtime_dir=tmp_path / "runs",
    )
    with TestClient(create_app(settings)) as client:
        service = client.app.state.service
        target = service.register_agent_target(
            name="Broken",
            endpoint_url="http://127.0.0.1:8000/step",
            version="1.0.0",
        )
        service.risk_client_factory = lambda target, timeout: BrokenClient()
        failed = service.create_assessment(
            target_id=target.id,
            name="Failure isolation",
            profile=AssessmentProfile.QUICK,
        )
        service.execute_assessment(failed.id)
        failed_runs = service.store.risk_test_runs(failed.id)
        assert len(failed_runs) == 12
        assert all(run.status.value == "failed" for run in failed_runs)
        assert service.store.assessment(failed.id).status.value == "completed"
        assert service.store.risk_report(failed.id) is not None

        cancelled = service.create_assessment(
            target_id=target.id,
            name="Cancelled before dispatch",
            profile=AssessmentProfile.QUICK,
        )
        service.store.request_assessment_cancel(cancelled.id)
        service.execute_assessment(cancelled.id)
        assert service.store.assessment(cancelled.id).status.value == "cancelled"
        assert all(
            run.status.value == "cancelled"
            for run in service.store.risk_test_runs(cancelled.id)
        )
        assert service.store.risk_report(cancelled.id) is None

        probe = ConcurrencyProbe()
        service.risk_client_factory = lambda target, timeout: probe
        concurrent = service.create_assessment(
            target_id=target.id,
            name="Concurrency probe",
            profile=AssessmentProfile.QUICK,
            concurrency=4,
        )
        service.execute_assessment(concurrent.id)
        assert 2 <= probe.peak <= 4
