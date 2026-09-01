"""Export or verify the public ScenarioSpec JSON Schema."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API_SRC = ROOT / "apps" / "api" / "src"
OUTPUT = ROOT / "packages" / "scenarios" / "scenario-v1.schema.json"

if str(API_SRC) not in sys.path:
    sys.path.insert(0, str(API_SRC))

from arena.domain.models import ScenarioSpec  # noqa: E402


def rendered_schema() -> str:
    payload = ScenarioSpec.model_json_schema()
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check", action="store_true", help="fail when the committed schema drifts"
    )
    args = parser.parse_args()
    expected = rendered_schema()
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_text(encoding="utf-8") != expected:
            print("scenario schema is stale; run make export-scenario-schema")
            return 1
        print("scenario schema is current")
        return 0
    OUTPUT.write_text(expected, encoding="utf-8")
    print(f"wrote {OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
