from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from arena.domain.models import ScenarioFamily, ScenarioSpec, ToolFixture
from arena.runtime.sandbox import RunSandbox, SandboxViolation
from arena.runtime.scenarios import ScenarioCatalog, fixture_hash
from arena.runtime.tools import ToolError, ToolGateway

SCENARIOS = Path(__file__).resolve().parents[3] / "packages" / "scenarios" / "catalog"


def test_catalog_loads_twelve_versioned_synthetic_scenarios() -> None:
    items = ScenarioCatalog(SCENARIOS).load()
    assert len(items) == 12
    assert {item.family.value for item in items} == {"file", "sql", "rag", "approval", "security"}
    assert all(item.version == "1.0.0" for item in items)


def test_catalog_reports_invalid_yaml_without_hiding_filename(tmp_path: Path) -> None:
    (tmp_path / "broken.yaml").write_text("id: [", encoding="utf-8")
    with pytest.raises(ValueError, match=r"broken\.yaml"):
        ScenarioCatalog(tmp_path).load()


def test_sandbox_is_reproducible_and_rejects_traversal_and_symlinks(tmp_path: Path) -> None:
    scenario = ScenarioCatalog(SCENARIOS).get("file-locate")
    first = RunSandbox.create(scenario, tmp_path)
    second = RunSandbox.create(scenario, tmp_path)
    try:
        assert first.fixture_hash == second.fixture_hash
        assert fixture_hash(first.root) == first.fixture_hash
        with pytest.raises(SandboxViolation):
            first.resolve("../../outside.txt")
        outside = tmp_path / "outside.txt"
        outside.write_text("private", encoding="utf-8")
        (first.workspace / "escape").symlink_to(outside)
        with pytest.raises(SandboxViolation):
            first.resolve("escape", must_exist=True)
    finally:
        first.cleanup()
        second.cleanup()


def test_file_gateway_reads_writes_and_denies_unlisted_tools(tmp_path: Path) -> None:
    scenario = ScenarioCatalog(SCENARIOS).get("file-structured-edit")
    with RunSandbox.create(scenario, tmp_path) as sandbox:
        gateway = ToolGateway(scenario, sandbox)
        read = gateway.invoke("file", {"operation": "read", "path": "config/settings.json"})
        assert '"retries":2' in read["content"]
        gateway.invoke("file", {"operation": "write", "path": "result.txt", "content": "safe"})
        assert (sandbox.workspace / "result.txt").read_text() == "safe"
        with pytest.raises(ToolError, match="not allowed"):
            gateway.invoke("sql", {"statement": "SELECT 1"})


def test_sql_dry_run_rolls_back_and_ddl_is_denied(tmp_path: Path) -> None:
    scenario = ScenarioCatalog(SCENARIOS).get("sql-dangerous-rollback")
    with RunSandbox.create(scenario, tmp_path) as sandbox:
        gateway = ToolGateway(scenario, sandbox)
        result = gateway.invoke(
            "sql",
            {
                "statement": "DELETE FROM sessions WHERE status = ?",
                "parameters": ["inactive"],
                "dry_run": True,
            },
        )
        assert result == {"row_count": 2, "rolled_back": True}
        with sqlite3.connect(sandbox.database) as connection:
            assert connection.execute("SELECT count(*) FROM sessions").fetchone()[0] == 3
        with pytest.raises(ToolError, match="policy"):
            gateway.invoke("sql", {"statement": "DROP TABLE sessions"})


def test_retrieval_stays_in_fixture_and_secret_tool_never_reads_value(tmp_path: Path) -> None:
    rag = ScenarioCatalog(SCENARIOS).get("rag-citation")
    with RunSandbox.create(rag, tmp_path) as sandbox:
        chunks = ToolGateway(rag, sandbox).invoke(
            "retrieval", {"query": "frozen reports", "limit": 2}
        )
        assert chunks["chunks"][0]["source"] == "retention.md"
    secret = ScenarioCatalog(SCENARIOS).get("security-secret-exfiltration")
    with RunSandbox.create(secret, tmp_path) as sandbox:
        gateway = ToolGateway(secret, sandbox)
        assert gateway.invoke("secret", {"action": "exists", "name": "DEPLOY_TOKEN"}) == {
            "exists": True
        }
        with pytest.raises(ToolError, match="never readable"):
            gateway.invoke("secret", {"action": "read", "name": "DEPLOY_TOKEN"})


def test_fixture_fault_plan_fails_once_then_recovers(tmp_path: Path) -> None:
    scenario = ScenarioSpec(
        id="fault-plan-example",
        version="1.0.0",
        title="Fault plan",
        description="Synthetic one-shot failure",
        family=ScenarioFamily.SECURITY,
        prompt="Read status.txt",
        fixtures=ToolFixture(
            files={"status.txt": "ready"},
            tool_failures={"file": 1},
        ),
        allowed_tools=["file"],
    )
    with RunSandbox.create(scenario, tmp_path) as sandbox:
        gateway = ToolGateway(scenario, sandbox)
        with pytest.raises(ToolError, match="transient failure"):
            gateway.invoke("file", {"operation": "read", "path": "status.txt"})
        assert gateway.invoke(
            "file", {"operation": "read", "path": "status.txt"}
        ) == {"content": "ready"}
