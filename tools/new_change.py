"""Create an indexed change note from the repository template."""

from __future__ import annotations

import argparse
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHANGES = ROOT / "docs" / "changes"
SLUG = re.compile(r"^[a-z0-9][a-z0-9-]+$")
TYPES = (
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
)
MARKER = "<!-- new-change -->"


def create_change(slug: str, change_type: str) -> Path:
    if not SLUG.match(slug):
        raise ValueError("SLUG must use lowercase letters, digits, and hyphens")
    stamp = date.today().isoformat()
    year = stamp[:4]
    target = CHANGES / year / f"{stamp}-{slug}.md"
    if target.exists():
        raise FileExistsError(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    title = slug.replace("-", " ").title()
    content = f"""---
date: {stamp}
type: {change_type}
status: completed
components:
  - component-name
compatibility: compatible
---

# {title}

## 原因

待填写。

## 最终变化

- 待填写。

## 影响与兼容性

待填写。

## 验证

- `make check`

## 回滚

待填写。

## 关联

- Commit: 待提交后补充
- Issue/PR: 无
"""
    target.write_text(content, encoding="utf-8")
    index_path = CHANGES / "README.md"
    index = index_path.read_text(encoding="utf-8")
    if MARKER not in index:
        raise ValueError(f"{MARKER} is missing from docs/changes/README.md")
    row = f"| {stamp} | {change_type} | [{title}]({year}/{target.name}) | 待填写 |\n"
    index_path.write_text(index.replace(MARKER, row + MARKER), encoding="utf-8")
    return target


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--slug", required=True)
    parser.add_argument("--type", required=True, choices=TYPES)
    args = parser.parse_args()
    try:
        target = create_change(args.slug, args.type)
    except (ValueError, FileExistsError) as error:
        print(error)
        return 1
    print(f"created {target.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
