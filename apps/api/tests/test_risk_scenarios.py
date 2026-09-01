from __future__ import annotations

from pathlib import Path

from arena.domain.risk import AssessmentProfile
from arena.runtime.risk_scenarios import RiskCatalog, profile_defaults

ROOT = Path(__file__).resolve().parents[3]
RISK_PACK = ROOT / "packages" / "risk-packs" / "tool-agent-baseline" / "v1"


def test_risk_pack_has_twelve_versioned_synthetic_cases() -> None:
    cases = RiskCatalog(RISK_PACK).load()
    assert len(cases) == 12
    assert len({(case.id, case.version) for case in cases}) == 12
    assert all(case.remediation and case.allowed_tools for case in cases)


def test_profiles_materialize_stable_12_72_180_run_matrices() -> None:
    catalog = RiskCatalog(RISK_PACK)
    expected = {
        AssessmentProfile.QUICK: (12, 1, 12),
        AssessmentProfile.STANDARD: (36, 2, 72),
        AssessmentProfile.DEEP: (60, 3, 180),
    }
    for profile, (logical, repetitions, total) in expected.items():
        first = catalog.materialize(profile, seed=42)
        second = catalog.materialize(profile, seed=42)
        assert first == second
        assert len(first) == logical
        assert profile_defaults(profile)[0] == repetitions
        assert profile_defaults(profile)[2] == total
        assert len({item.variant_id for item in first}) == logical


def test_different_seed_changes_variant_seed_but_not_case_identity() -> None:
    catalog = RiskCatalog(RISK_PACK)
    first = catalog.materialize(AssessmentProfile.STANDARD, seed=1)
    second = catalog.materialize(AssessmentProfile.STANDARD, seed=2)
    assert [item.variant_id for item in first] == [item.variant_id for item in second]
    assert [item.seed for item in first] != [item.seed for item in second]


def test_deep_variants_change_prompt_position_permissions_and_fault_plan() -> None:
    specs = RiskCatalog(RISK_PACK).materialize(AssessmentProfile.DEEP, seed=42)
    mutations = {item.mutation.split(":", 1)[0] for item in specs}
    assert mutations == {
        "baseline",
        "prompt-wrapper",
        "injection-position",
        "permission-combination",
        "fault-plan",
    }
    permission_variant = next(item for item in specs if item.mutation.startswith("permission"))
    assert len(permission_variant.case.allowed_tools) > 1
    fault_variant = next(item for item in specs if item.mutation.startswith("fault-plan"))
    assert sum(fault_variant.case.fixtures.tool_failures.values()) == 1
