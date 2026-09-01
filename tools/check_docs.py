"""Check local Markdown links and required human/agent navigation files."""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
LINK = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
REQUIRED = (
    "AGENTS.md",
    "README.md",
    "docs/README.md",
    "apps/api/AGENTS.md",
    "apps/api/README.md",
    "apps/web/AGENTS.md",
    "apps/web/README.md",
    "packages/scenarios/AGENTS.md",
    "packages/scenarios/README.md",
    "packages/risk-packs/AGENTS.md",
    "packages/risk-packs/README.md",
    "packages/registry/README.md",
)


def markdown_files() -> tuple[Path, ...]:
    ignored = {".git", ".venv", "node_modules", "dist", "runtime"}
    return tuple(
        path
        for path in ROOT.rglob("*.md")
        if not any(part in ignored for part in path.relative_to(ROOT).parts)
    )


def broken_links(files: tuple[Path, ...] | None = None) -> list[str]:
    errors: list[str] = []
    for path in files or markdown_files():
        text = path.read_text(encoding="utf-8")
        for raw in LINK.findall(text):
            target = raw.strip().split()[0].strip("<>")
            if not target or target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            relative = unquote(target.split("#", 1)[0])
            if relative and not (path.parent / relative).resolve().exists():
                errors.append(f"{path.relative_to(ROOT)} -> {target}")
    for relative in REQUIRED:
        if not (ROOT / relative).is_file():
            errors.append(f"required navigation file is missing: {relative}")
    return errors


def main() -> int:
    errors = broken_links()
    if errors:
        print("broken or missing documentation paths:\n" + "\n".join(errors))
        return 1
    print("documentation links passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
