"""Validate change notes and require one for each material change batch."""

from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
CHANGES = ROOT / "docs" / "changes"
NAME = re.compile(r"^\d{4}-\d{2}-\d{2}-[a-z0-9][a-z0-9-]+\.md$")
ALLOWED_TYPES = {
    "feature",
    "fix",
    "refactor",
    "dependency",
    "config",
    "migration",
    "ci",
    "docs",
    "security",
    "test",
}
MATERIAL_PREFIXES = ("apps/", "packages/", "tools/", ".github/workflows/")
MATERIAL_FILES = {"Makefile", "compose.yaml", ".env.example", "PROJECT_MAP.yaml"}
REQUIRED_SECTIONS = (
    "## 原因",
    "## 最终变化",
    "## 影响与兼容性",
    "## 验证",
    "## 回滚",
    "## 关联",
)


def parse_front_matter(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n") or "\n---\n" not in text[4:]:
        raise ValueError("missing YAML front matter")
    raw = text.split("\n---\n", 1)[0][4:]
    payload = yaml.safe_load(raw)
    if not isinstance(payload, dict):
        raise ValueError("front matter must be a mapping")
    return payload


def note_errors(path: Path) -> list[str]:
    errors: list[str] = []
    text = path.read_text(encoding="utf-8")
    if not NAME.match(path.name):
        errors.append(f"invalid change-note filename: {path.relative_to(ROOT)}")
    if path.parent.name != path.name[:4]:
        errors.append(f"change note is in the wrong year directory: {path.relative_to(ROOT)}")
    try:
        data = parse_front_matter(path)
    except (OSError, ValueError, yaml.YAMLError) as error:
        return [f"{path.relative_to(ROOT)}: {error}"]
    for field in ("date", "type", "status", "components", "compatibility"):
        if field not in data or data[field] in (None, "", []):
            errors.append(f"{path.relative_to(ROOT)}: missing {field}")
    if str(data.get("date")) != path.name[:10]:
        errors.append(f"{path.relative_to(ROOT)}: date does not match filename")
    if data.get("type") not in ALLOWED_TYPES:
        errors.append(f"{path.relative_to(ROOT)}: unsupported type {data.get('type')}")
    if data.get("status") != "completed":
        errors.append(f"{path.relative_to(ROOT)}: status must be completed")
    if not isinstance(data.get("components"), list):
        errors.append(f"{path.relative_to(ROOT)}: components must be a list")
    for section in REQUIRED_SECTIONS:
        if section not in text:
            errors.append(f"{path.relative_to(ROOT)}: missing section {section}")
    index = (CHANGES / "README.md").read_text(encoding="utf-8")
    expected_link = f"{path.parent.name}/{path.name}"
    if expected_link not in index:
        errors.append(f"{path.relative_to(ROOT)}: missing from docs/changes/README.md")
    return errors


def validate_all_notes() -> list[str]:
    return [
        error
        for path in sorted(CHANGES.glob("[0-9][0-9][0-9][0-9]/*.md"))
        for error in note_errors(path)
    ]


def is_material_change(relative: str) -> bool:
    return relative in MATERIAL_FILES or relative.startswith(MATERIAL_PREFIXES)


def changed_paths(base: str) -> list[tuple[str, str]]:
    result = subprocess.run(
        ["git", "diff", "--name-status", f"{base}...HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    changes: list[tuple[str, str]] = []
    for line in result.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) >= 2:
            changes.append((parts[0], parts[-1]))
    return changes


def missing_note_for_changes(changes: list[tuple[str, str]]) -> bool:
    material = any(is_material_change(path) for _status, path in changes)
    added_note = any(
        status.startswith("A") and re.match(r"docs/changes/\d{4}/\d{4}-\d{2}-\d{2}-.+\.md$", path)
        for status, path in changes
    )
    return material and not added_note


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", help="Git base revision for material-change enforcement")
    args = parser.parse_args()
    errors = validate_all_notes()
    if args.base and set(args.base) != {"0"}:
        try:
            changes = changed_paths(args.base)
        except subprocess.CalledProcessError as error:
            errors.append(f"cannot compare change-note base {args.base}: {error}")
        else:
            if missing_note_for_changes(changes):
                errors.append("material changes require a new docs/changes/YYYY change note")
    if errors:
        print("\n".join(errors))
        return 1
    print("change-note governance passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
