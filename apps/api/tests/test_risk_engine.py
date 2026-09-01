from __future__ import annotations

from pathlib import Path

from arena.application.risk_engine import RiskEngine
from arena.domain.risk import (
    AgentTarget,
    Assessment,
    AssessmentProfile,
    RiskTestRun,
)
from arena.domain.risk_evaluation import build_risk_report
from arena.runtime.reference_agents import hardened_reference_step, vulnerable_reference_step
from arena.runtime.risk_scenarios import RiskCatalog

ROOT = Path(__file__).resolve().parents[3]
RISK_PACK = ROOT / "packages" / "risk-packs" / "tool-agent-baseline" / "v1"


class DirectClient:
    def __init__(self, handler):
        self.handler = handler

    def step(self, request):
        return self.handler(request)


def execute_pack(tmp_path: Path, handler):
    catalog = RiskCatalog(RISK_PACK)
    runs = []
    findings = []
    for index, spec in enumerate(catalog.materialize(AssessmentProfile.QUICK)):
        run = RiskTestRun(
            id=f"risk-{index}",
            assessment_id="assessment-1",
            target_id="target-1",
            case_id=spec.case.id,
            case_version=spec.case.version,
            variant_id=spec.variant_id,
            mutation=spec.mutation,
            seed=spec.seed,
            repetition=1,
        )
        outcome = RiskEngine(tmp_path).execute(
            run=run,
            spec=spec,
            client=DirectClient(handler),
        )
        runs.append(outcome.run)
        findings.extend(outcome.findings)
        assert [event.sequence for event in outcome.events] == list(
            range(1, len(outcome.events) + 1)
        )
    return catalog, runs, findings


def report_for(catalog, runs, findings, name):
    return build_risk_report(
        assessment=Assessment(
            id="assessment-1",
            target_id="target-1",
            name="Quick",
            profile=AssessmentProfile.QUICK,
            repetitions=1,
            total_runs=12,
        ),
        target=AgentTarget(
            id="target-1",
            name=name,
            endpoint_url="http://127.0.0.1:8000/step",
            version="1.0.0",
        ),
        runs=runs,
        findings=findings,
        cases={case.id: case for case in catalog.load()},
    )


def test_hardened_reference_agent_passes_without_high_or_critical_findings(tmp_path: Path) -> None:
    catalog, runs, findings = execute_pack(tmp_path, hardened_reference_step)
    report = report_for(catalog, runs, findings, "Hardened")
    assert report.grade == "A"
    assert report.final_score == 100
    assert report.verdict.value == "ready"
    assert report.finding_counts["high"] == report.finding_counts["critical"] == 0
    assert report.coverage["pass_rate_percent"] == 100
    assert report.coverage["volatility_percent"] == 0


def test_vulnerable_reference_agent_triggers_safety_gate_and_redacts_canaries(
    tmp_path: Path,
) -> None:
    catalog, runs, findings = execute_pack(tmp_path, vulnerable_reference_step)
    report = report_for(catalog, runs, findings, "Vulnerable")
    assert report.grade == "E"
    assert report.verdict.value == "not_recommended"
    assert report.finding_counts["critical"] > 0
    assert all("synthetic-deploy-canary" not in run.answer for run in runs)
    assert report.gate_reasons
