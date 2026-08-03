"""Versioned scenario catalog and reproducible fixture initialization."""

from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path

import yaml
from pydantic import ValidationError

from arena.domain import ScenarioSpec


class ScenarioCatalog:
    def __init__(self, root: Path) -> None:
        self.root = root

    def load(self) -> tuple[ScenarioSpec, ...]:
        scenarios: list[ScenarioSpec] = []
        seen: set[tuple[str, str]] = set()
        for path in sorted(self.root.glob("*.yaml")):
            try:
                payload = yaml.safe_load(path.read_text(encoding="utf-8"))
                scenario = ScenarioSpec.model_validate(payload)
            except (OSError, yaml.YAMLError, ValidationError) as error:
                raise ValueError(f"invalid scenario {path.name}: {error}") from error
            identity = (scenario.id, scenario.version)
            if identity in seen:
                raise ValueError(f"duplicate scenario: {scenario.id}@{scenario.version}")
            seen.add(identity)
            scenarios.append(scenario)
        return tuple(scenarios)

    def get(self, scenario_id: str) -> ScenarioSpec:
        matches = [scenario for scenario in self.load() if scenario.id == scenario_id]
        if not matches:
            raise KeyError(scenario_id)
        return max(matches, key=lambda scenario: tuple(map(int, scenario.version.split("."))))


def initialize_scenario(scenario: ScenarioSpec, run_root: Path) -> dict[str, str]:
    """Materialize only synthetic fixtures inside one isolated run directory."""

    workspace = run_root / "workspace"
    documents = run_root / "documents"
    workspace.mkdir(parents=True, exist_ok=False)
    documents.mkdir(parents=True, exist_ok=False)
    for relative, content in scenario.fixtures.files.items():
        path = _safe_fixture_path(workspace, relative)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    for relative, content in scenario.fixtures.documents.items():
        path = _safe_fixture_path(documents, relative)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    database = run_root / "scenario.sqlite3"
    with sqlite3.connect(database) as connection:
        for statement in scenario.fixtures.sql:
            connection.execute(statement)
    return {
        "workspace": str(workspace),
        "documents": str(documents),
        "database": str(database),
        "fixture_hash": fixture_hash(run_root),
    }


def fixture_hash(run_root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in run_root.rglob("*") if item.is_file()):
        digest.update(path.relative_to(run_root).as_posix().encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _safe_fixture_path(root: Path, relative: str) -> Path:
    if not relative or Path(relative).is_absolute():
        raise ValueError(f"unsafe fixture path: {relative!r}")
    candidate = (root / relative).resolve()
    if not candidate.is_relative_to(root.resolve()):
        raise ValueError(f"fixture escapes sandbox: {relative!r}")
    return candidate
