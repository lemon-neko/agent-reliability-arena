"""Export or verify public risk-case and attestation JSON Schemas."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from arena.domain.risk import Attestation, RiskCase

ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = {
    ROOT / "packages" / "risk-packs" / "risk-case-v1.schema.json": RiskCase,
    ROOT / "packages" / "registry" / "attestation-v1.schema.json": Attestation,
}


def rendered_schema(model) -> str:
    return json.dumps(model.model_json_schema(), ensure_ascii=False, indent=2) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    stale: list[str] = []
    for output, model in OUTPUTS.items():
        rendered = rendered_schema(model)
        if args.check:
            if not output.is_file() or output.read_text(encoding="utf-8") != rendered:
                stale.append(str(output.relative_to(ROOT)))
        else:
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(rendered, encoding="utf-8")
    if stale:
        raise SystemExit("stale generated schemas: " + ", ".join(stale))
    print("risk contract schemas passed" if args.check else "risk contract schemas exported")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
