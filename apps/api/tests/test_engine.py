from __future__ import annotations

from pathlib import Path

import pytest

from arena.application.engine import ArenaEngine
from arena.domain.evaluation import DeterministicEvaluator
from arena.domain.models import AgentProfile, Run, RunStatus, TraceKind
from arena.runtime.providers import DeterministicProvider, OpenAICompatibleProvider
from arena.runtime.scenarios import ScenarioCatalog
from arena.runtime.tracing import TraceRecorder, redact

SCENARIOS = Path(__file__).resolve().parents[3] / "packages" / "scenarios" / "catalog"


def make_run(scenario_id: str, agent_id: str = "minimal-fake") -> Run:
    return Run(
        id=f"run-{scenario_id}",
        tournament_id="t-1",
        scenario_id=scenario_id,
        scenario_version="1.0.0",
        agent_id=agent_id,
        repetition=1,
    )


def test_minimal_runtime_completes_all_nonapproval_scenarios_with_deterministic_scores(
    tmp_path: Path,
) -> None:
    catalog = ScenarioCatalog(SCENARIOS)
    agent = AgentProfile(
        id="minimal-fake",
        name="Minimal",
        runtime="minimal",
        model="fake",
        base_url="fake://deterministic",
    )
    evaluator = DeterministicEvaluator()
    engine = ArenaEngine(tmp_path)
    for scenario in catalog.load():
        if scenario.id == "approval-sensitive-action":
            continue
        outcome = engine.execute(run=make_run(scenario.id), scenario=scenario, agent=agent)
        assert outcome.run.status == RunStatus.COMPLETED
        assert outcome.evaluation and outcome.evaluation.score.total == 100
        assert evaluator.evaluate(outcome.run, scenario, outcome.events) == outcome.evaluation


def test_langgraph_runtime_uses_checkpointed_graph_and_completes(tmp_path: Path) -> None:
    scenario = ScenarioCatalog(SCENARIOS).get("file-locate")
    agent = AgentProfile(
        id="graph-fake",
        name="Graph",
        runtime="langgraph",
        model="fake",
        base_url="fake://deterministic",
    )
    outcome = ArenaEngine(tmp_path).execute(
        run=make_run(scenario.id, agent.id), scenario=scenario, agent=agent
    )
    assert outcome.run.answer.startswith("The codename is Firefly")
    assert [event.sequence for event in outcome.events] == list(range(1, len(outcome.events) + 1))


def test_approval_pauses_then_explicit_approval_allows_resume(tmp_path: Path) -> None:
    scenario = ScenarioCatalog(SCENARIOS).get("approval-sensitive-action")
    agent = AgentProfile(
        id="minimal-fake",
        name="Minimal",
        runtime="minimal",
        model="fake",
        base_url="fake://deterministic",
    )
    engine = ArenaEngine(tmp_path)
    waiting = engine.execute(run=make_run(scenario.id), scenario=scenario, agent=agent)
    assert waiting.run.status == RunStatus.WAITING_APPROVAL
    assert waiting.approval and waiting.evaluation is None
    complete = engine.execute(run=waiting.run, scenario=scenario, agent=agent, approved=True)
    assert complete.run.status == RunStatus.COMPLETED
    assert complete.evaluation and complete.evaluation.score.total == 100


def test_trace_redaction_handles_nested_keys_tokens_and_canaries() -> None:
    raw = {"authorization": "Bearer abcdefghijk", "nested": ["sk-abcdefghijk", "canary-value"]}
    cleaned = redact(raw, ("canary-value",))
    assert cleaned["authorization"] == "[REDACTED]"
    assert cleaned["nested"] == ["[REDACTED]", "[REDACTED]"]
    recorder = TraceRecorder("run-1", protected_values=("secret-value",))
    event = recorder.record(TraceKind.MODEL, "turn", {"content": "secret-value"})
    assert event.payload["content"] == "[REDACTED]"


def test_provider_rejects_malformed_structured_tool_output(monkeypatch: pytest.MonkeyPatch) -> None:
    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "choices": [
                    {
                        "message": {
                            "tool_calls": [
                                {"id": "1", "function": {"name": "file", "arguments": "[]"}}
                            ]
                        }
                    }
                ]
            }

    monkeypatch.setattr("arena.runtime.providers.httpx.post", lambda *args, **kwargs: Response())
    provider = OpenAICompatibleProvider(
        base_url="http://127.0.0.1:11434/v1", api_key="", model="local"
    )
    scenario = ScenarioCatalog(SCENARIOS).get("file-locate")
    with pytest.raises(RuntimeError, match="invalid structured"):
        provider.complete(messages=[], tools=[], scenario=scenario)


def test_fake_provider_counts_tool_results_before_final_answer() -> None:
    scenario = ScenarioCatalog(SCENARIOS).get("file-locate")
    provider = DeterministicProvider()
    first = provider.complete(messages=[], tools=[], scenario=scenario)
    final = provider.complete(
        messages=[{"role": "tool", "content": "ok"}], tools=[], scenario=scenario
    )
    assert first.tool_calls[0].name == "file"
    assert final.tool_calls == [] and "Firefly" in final.content
