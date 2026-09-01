from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from arena.infrastructure.config import Settings
from arena.interfaces.http.app import create_app

SCENARIOS = Path(__file__).resolve().parents[3] / "packages" / "scenarios" / "catalog"


def client_for(tmp_path: Path, *, demo: bool = False) -> TestClient:
    settings = Settings(
        arena_env="demo" if demo else "test",
        database_url=f"sqlite:///{tmp_path / 'arena.db'}",
        scenario_dir=SCENARIOS,
        runtime_dir=tmp_path / "runs",
        celery_task_always_eager=True,
    )
    return TestClient(create_app(settings))


def test_catalog_agents_tournament_idempotency_run_report_and_leaderboard(tmp_path: Path) -> None:
    with client_for(tmp_path) as client:
        assert client.get("/health").json()["status"] == "ok"
        assert len(client.get("/api/scenarios").json()) == 12
        assert len(client.get("/api/agents").json()) == 2
        payload = {
            "name": "Smoke",
            "agent_ids": ["minimal-fake"],
            "scenario_ids": ["file-locate"],
            "repetitions": 2,
        }
        first = client.post(
            "/api/tournaments", json=payload, headers={"Idempotency-Key": "same-request"}
        )
        second = client.post(
            "/api/tournaments", json=payload, headers={"Idempotency-Key": "same-request"}
        )
        assert first.status_code == 202 and second.status_code == 202
        assert first.json()["tournament"]["id"] == second.json()["tournament"]["id"]
        assert first.json()["created"] is True and second.json()["created"] is False
        tournament_id = first.json()["tournament"]["id"]
        tournament = client.get(f"/api/tournaments/{tournament_id}").json()
        assert {run["status"] for run in tournament["runs"]} == {"completed"}
        run_id = tournament["runs"][0]["id"]
        assert client.get(f"/api/runs/{run_id}").json()["evaluation"]["score"]["correctness"] == 50
        assert client.get("/api/leaderboard").json()[0]["runs"] == 2
        assert client.get(f"/api/reports/{tournament_id}").json()["schema_version"] == 1
        assert client.get("/api/tournaments/missing").status_code == 404
        with client.stream(
            "GET",
            f"/api/runs/{run_id}/events",
            headers={"Last-Event-ID": "2"},
        ) as stream:
            body = "".join(stream.iter_text())
        assert stream.status_code == 200
        assert "event: tool" in body or "event: model" in body
        assert "event: end" in body


def test_approval_endpoint_requires_matching_request_and_resumes_run(tmp_path: Path) -> None:
    with client_for(tmp_path) as client:
        created = client.post(
            "/api/tournaments",
            json={
                "name": "Gate",
                "agent_ids": ["minimal-fake"],
                "scenario_ids": ["approval-sensitive-action"],
                "repetitions": 1,
            },
        )
        tournament_id = created.json()["tournament"]["id"]
        run = client.get(f"/api/tournaments/{tournament_id}").json()["runs"][0]
        detail = client.get(f"/api/runs/{run['id']}").json()
        approval_event = next(
            event for event in detail["events"] if event["name"] == "approval.requested"
        )
        approval_id = approval_event["payload"]["id"]
        assert run["status"] == "waiting_approval"
        assert (
            client.post(
                f"/api/runs/{run['id']}/approvals/missing", json={"decision": "approve"}
            ).status_code
            == 404
        )
        approved = client.post(
            f"/api/runs/{run['id']}/approvals/{approval_id}", json={"decision": "approve"}
        )
        assert approved.status_code == 200
        assert client.get(f"/api/runs/{run['id']}").json()["run"]["status"] == "completed"


def test_demo_mode_rejects_all_mutations(tmp_path: Path) -> None:
    with client_for(tmp_path, demo=True) as client:
        response = client.post(
            "/api/tournaments",
            json={"name": "No", "agent_ids": ["minimal-fake"], "scenario_ids": ["file-locate"]},
        )
        assert response.status_code == 405
