import subprocess
from pathlib import Path

import yaml
from tools.build_public_leaderboard import OUTPUT as LEADERBOARD_OUTPUT
from tools.build_public_leaderboard import rendered as rendered_leaderboard
from tools.check_change_note import is_material_change, missing_note_for_changes, validate_all_notes
from tools.check_docs import broken_links
from tools.check_project_map import load_project_map, validate_project_map
from tools.export_risk_schemas import OUTPUTS as RISK_SCHEMA_OUTPUTS
from tools.export_risk_schemas import rendered_schema as rendered_risk_schema
from tools.export_scenario_schema import OUTPUT, rendered_schema

from arena.domain.models import ScenarioSpec


def test_project_map_paths_and_commands_are_valid() -> None:
    assert validate_project_map(load_project_map()) == []


def test_markdown_links_and_navigation_files_are_valid() -> None:
    assert broken_links() == []


def test_scenario_json_schema_is_current() -> None:
    assert OUTPUT.read_text(encoding="utf-8") == rendered_schema()


def test_risk_contract_json_schemas_are_current() -> None:
    for output, model in RISK_SCHEMA_OUTPUTS.items():
        assert output.read_text(encoding="utf-8") == rendered_risk_schema(model)


def test_public_leaderboard_artifact_is_current() -> None:
    assert LEADERBOARD_OUTPUT.read_text(encoding="utf-8") == rendered_leaderboard()


def test_example_scenario_matches_the_public_type() -> None:
    root = Path(__file__).resolve().parents[3]
    payload = yaml.safe_load(
        (root / "packages" / "scenarios" / "example.yaml").read_text(encoding="utf-8")
    )
    assert ScenarioSpec.model_validate(payload).id == "example-safe-read"


def test_change_notes_are_valid_and_indexed() -> None:
    assert validate_all_notes() == []


def test_material_changes_require_an_added_change_note() -> None:
    assert is_material_change("apps/api/src/arena/application/engine.py")
    assert not is_material_change("docs/product/vision.md")
    assert missing_note_for_changes([("M", "apps/web/src/app/App.tsx")])
    assert not missing_note_for_changes([("M", "docs/product/vision.md")])
    assert not missing_note_for_changes(
        [
            ("M", "apps/web/src/app/App.tsx"),
            ("A", "docs/changes/2026/2026-08-31-example.md"),
        ]
    )


def test_required_repository_paths_do_not_use_legacy_layout() -> None:
    root = Path(__file__).resolve().parents[3]
    tracked = subprocess.run(
        ["git", "ls-files"], cwd=root, check=True, capture_output=True, text=True
    ).stdout.splitlines()
    legacy_prefixes = ("backend/", "frontend/", "scenarios/", "alembic/")
    assert not any(path.startswith(legacy_prefixes) for path in tracked)
