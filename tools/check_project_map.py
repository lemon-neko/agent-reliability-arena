"""Validate that PROJECT_MAP.yaml points to real, documented repository surfaces."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
MAP_PATH = ROOT / "PROJECT_MAP.yaml"


def load_project_map() -> dict[str, Any]:
    payload = yaml.safe_load(MAP_PATH.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("PROJECT_MAP.yaml must contain a mapping")
    return payload


def validate_project_map(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if payload.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    project = payload.get("project")
    if not isinstance(project, dict) or not project.get("id") or not project.get("purpose"):
        errors.append("project.id and project.purpose are required")
    entrypoints = payload.get("entrypoints")
    if not isinstance(entrypoints, dict):
        errors.append("entrypoints must be a mapping")
    else:
        for name, relative in entrypoints.items():
            if not isinstance(relative, str) or not (ROOT / relative).exists():
                errors.append(f"entrypoint does not exist: {name}={relative}")
    areas = payload.get("areas")
    if not isinstance(areas, list) or not areas:
        errors.append("areas must be a non-empty list")
    else:
        for area in areas:
            if not isinstance(area, dict):
                errors.append("area entries must be mappings")
                continue
            for field in ("path", "purpose", "read_first", "verification"):
                if not area.get(field):
                    errors.append(f"area is missing {field}: {area}")
            for field in ("path", "read_first", "rules"):
                relative = area.get(field)
                if relative and not (ROOT / str(relative)).exists():
                    errors.append(f"area {field} does not exist: {relative}")
    modules = payload.get("modules")
    if not isinstance(modules, list) or not modules:
        errors.append("modules must be a non-empty list")
    else:
        for module in modules:
            if not isinstance(module, dict):
                errors.append("module entries must be mappings")
                continue
            for field in ("path", "responsibility", "authoritative_doc", "tests"):
                if not module.get(field):
                    errors.append(f"module is missing {field}: {module}")
            for field in ("path", "authoritative_doc"):
                relative = module.get(field)
                if relative and not (ROOT / str(relative)).exists():
                    errors.append(f"module {field} does not exist: {relative}")
            tests = module.get("tests")
            if tests and not isinstance(tests, list):
                errors.append(f"module tests must be a list: {module.get('path')}")
            elif isinstance(tests, list):
                for relative in tests:
                    if not (ROOT / str(relative)).is_file():
                        errors.append(f"module test entry does not exist: {relative}")
    docs = payload.get("authoritative_docs")
    if not isinstance(docs, dict) or not docs:
        errors.append("authoritative_docs must be a non-empty mapping")
    else:
        for name, relative in docs.items():
            if not (ROOT / str(relative)).is_file():
                errors.append(f"authoritative document does not exist: {name}={relative}")
    commands = payload.get("commands")
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    if not isinstance(commands, dict):
        errors.append("commands must be a mapping")
    else:
        for name, command in commands.items():
            if not isinstance(command, str) or not command.strip():
                errors.append(f"command is empty: {name}")
            elif command.startswith("make "):
                target = command.split()[1]
                if f"{target}:" not in makefile:
                    errors.append(f"Make target does not exist: {target}")
    for field in ("generated_files", "private_paths", "forbidden_commit_paths"):
        paths = payload.get(field)
        if not isinstance(paths, list) or not paths:
            errors.append(f"{field} must be a non-empty list")
    for relative in payload.get("generated_files", []):
        if not (ROOT / str(relative)).is_file():
            errors.append(f"generated file does not exist: {relative}")
    return errors


def main() -> int:
    errors = validate_project_map(load_project_map())
    if errors:
        print("\n".join(errors))
        return 1
    print("project map passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
