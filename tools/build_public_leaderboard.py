"""Build the public Pages leaderboard from reviewed attestation entries."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from arena.infrastructure.registry import load_public_leaderboard

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "packages" / "registry"
OUTPUT = ROOT / "apps" / "web" / "public" / "data" / "public-leaderboard.json"


def rendered() -> str:
    return json.dumps(load_public_leaderboard(REGISTRY), ensure_ascii=False, indent=2) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    value = rendered()
    if args.check:
        if not OUTPUT.is_file() or OUTPUT.read_text(encoding="utf-8") != value:
            raise SystemExit("public leaderboard artifact is stale")
        print("public leaderboard artifact passed")
        return 0
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(value, encoding="utf-8")
    print(f"wrote {OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
