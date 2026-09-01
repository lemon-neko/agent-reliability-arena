"""Per-run sandbox and fail-closed path resolver."""

from __future__ import annotations

import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path

from arena.domain.models import ScenarioSpec
from arena.runtime.scenarios import initialize_scenario


class SandboxViolation(PermissionError):
    pass


@dataclass
class RunSandbox:
    root: Path
    workspace: Path
    documents: Path
    database: Path
    fixture_hash: str

    @classmethod
    def create(cls, scenario: ScenarioSpec, parent: Path | None = None) -> RunSandbox:
        parent and parent.mkdir(parents=True, exist_ok=True)
        root = Path(tempfile.mkdtemp(prefix="arena-run-", dir=parent))
        values = initialize_scenario(scenario, root)
        return cls(
            root=root,
            workspace=Path(values["workspace"]),
            documents=Path(values["documents"]),
            database=Path(values["database"]),
            fixture_hash=values["fixture_hash"],
        )

    def resolve(self, relative: str, *, area: str = "workspace", must_exist: bool = False) -> Path:
        base = self.workspace if area == "workspace" else self.documents
        if not relative or Path(relative).is_absolute():
            raise SandboxViolation("absolute and empty paths are forbidden")
        candidate = base / relative
        try:
            resolved = candidate.resolve(strict=must_exist)
        except (FileNotFoundError, RuntimeError) as error:
            raise SandboxViolation("path cannot be resolved safely") from error
        if not resolved.is_relative_to(base.resolve()):
            raise SandboxViolation("path escapes run sandbox")
        return resolved

    def cleanup(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)

    def __enter__(self) -> RunSandbox:
        return self

    def __exit__(self, *_args) -> None:
        self.cleanup()
