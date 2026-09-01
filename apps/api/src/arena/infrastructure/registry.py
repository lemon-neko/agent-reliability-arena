"""Read-only public leaderboard built from reviewed attestation files."""

from __future__ import annotations

import json
from pathlib import Path

from arena.domain.risk import Attestation, VerificationLevel


def load_public_leaderboard(root: Path) -> list[dict]:
    values: list[Attestation] = []
    for path in sorted((root / "entries").glob("*.json")):
        values.append(Attestation.model_validate_json(path.read_text(encoding="utf-8")))
    ranked = [
        item
        for item in values
        if item.verification in {VerificationLevel.REPRODUCIBLE, VerificationLevel.VERIFIED}
    ]
    ranked.sort(
        key=lambda item: (
            -item.score,
            item.finding_counts.get("critical", 0),
            item.finding_counts.get("high", 0),
            item.volatility_percent,
            item.agent_name.casefold(),
        )
    )
    return [
        {
            "rank": index,
            **item.model_dump(mode="json"),
        }
        for index, item in enumerate(ranked, 1)
    ]


def write_public_leaderboard(root: Path, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(load_public_leaderboard(root), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
