from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from arena.application.reporting import (
    canonical_report_json,
    create_attestation,
    render_risk_report,
)
from arena.domain.risk import (
    AssessmentProfile,
    Finding,
    FindingSeverity,
    RiskCategory,
    RiskDimension,
    RiskDimensionScores,
    RiskReport,
    Verdict,
    VerificationLevel,
)
from arena.infrastructure.registry import load_public_leaderboard


def report(*, profile: AssessmentProfile = AssessmentProfile.STANDARD) -> RiskReport:
    finding = Finding(
        id="finding-1",
        assessment_id="assessment-1",
        test_run_id="run-1",
        case_id="case-1",
        category=RiskCategory.DATA_EXPOSURE,
        dimension=RiskDimension.SECURITY_PRIVACY,
        severity=FindingSeverity.HIGH,
        title="Synthetic finding",
        summary="A safe synthetic summary.",
        expected="No disclosure",
        observed="A canary marker was detected and removed.",
        evidence_event_ids=["event-1"],
        reproduction="arena assess replay assessment-1 --run run-1",
        remediation="Keep secrets behind the gateway.",
    )
    return RiskReport(
        assessment_id="assessment-1",
        target_id="target-1",
        target_name="Harbor Guard",
        target_version="1.2.3",
        repository_url="https://github.com/example/harbor",
        suite_version="tool-agent-baseline/1.0.0",
        profile=profile,
        generated_at=datetime(2026, 9, 1, tzinfo=UTC),
        raw_score=88,
        final_score=64,
        grade="D",
        verdict=Verdict.NOT_RECOMMENDED,
        gate_reasons=["High gate"],
        dimension_scores=RiskDimensionScores(
            security_privacy=18,
            authorization_control=18,
            side_effect_safety=12,
            correctness_grounding=12,
            resilience_idempotency=12,
            efficiency_resources=8,
        ),
        coverage={
            "total_runs": 72,
            "completed_runs": 72,
            "pass_rate_percent": 80.5,
            "volatility_percent": 4.2,
        },
        finding_counts={"critical": 0, "high": 1, "medium": 0, "low": 0, "info": 0},
        findings=[finding],
        limitations=["Synthetic scope only."],
    )


def test_html_and_attestation_are_sanitized_and_canonical() -> None:
    value = report()
    first = canonical_report_json(value)
    second = canonical_report_json(value)
    assert first == second
    html = render_risk_report(value)
    assert "Harbor Guard" in html and "Synthetic finding" in html
    attestation = create_attestation(value)
    assert len(attestation.report_sha256) == 64
    assert attestation.volatility_percent == 4.2
    serialized = attestation.model_dump_json()
    assert "endpoint" not in serialized and "evidence_event_ids" not in serialized
    assert "credential" not in serialized


def test_attestation_requires_standard_profile_and_repository() -> None:
    with pytest.raises(ValueError, match="Standard"):
        create_attestation(report(profile=AssessmentProfile.QUICK))
    value = report().model_copy(update={"repository_url": None})
    with pytest.raises(ValueError, match="repository_url"):
        create_attestation(value)


def test_public_leaderboard_excludes_self_reports_and_sorts_verified_entries(
    tmp_path: Path,
) -> None:
    entries = tmp_path / "entries"
    entries.mkdir()
    base = create_attestation(report())
    values = [
        base.model_copy(
            update={
                "id": "self",
                "agent_name": "Self",
                "score": 99,
                "verification": VerificationLevel.SELF_REPORTED,
            }
        ),
        base.model_copy(
            update={
                "id": "verified-low",
                "agent_name": "Verified Low",
                "score": 81,
                "verification": VerificationLevel.VERIFIED,
            }
        ),
        base.model_copy(
            update={
                "id": "repro-high",
                "agent_name": "Repro High",
                "score": 91,
                "verification": VerificationLevel.REPRODUCIBLE,
            }
        ),
        base.model_copy(
            update={
                "id": "repro-high-volatile",
                "agent_name": "Repro High Volatile",
                "score": 91,
                "volatility_percent": 12,
                "verification": VerificationLevel.REPRODUCIBLE,
            }
        ),
    ]
    for value in values:
        (entries / f"{value.id}.json").write_text(
            json.dumps(value.model_dump(mode="json")), encoding="utf-8"
        )
    board = load_public_leaderboard(tmp_path)
    assert [row["id"] for row in board] == [
        "repro-high",
        "repro-high-volatile",
        "verified-low",
    ]
    assert [row["rank"] for row in board] == [1, 2, 3]
