"""Fail CI if public Git state contains runtime data, likely secrets, or private artifacts."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_PATHS = re.compile(
    r"(^|/)(\.env($|\.)|runtime|traces|reports/private|node_modules)(/|$)|\.(db|sqlite3?|pem|key)$",
    re.I,
)
SECRET_PATTERNS = (
    re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"MODEL_API_KEY\s*=\s*[^\s#]+"),
)


def candidate_files() -> tuple[str, ...]:
    output = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    return tuple(line for line in output.splitlines() if line)


def violations() -> list[str]:
    problems: list[str] = []
    for relative in candidate_files():
        if FORBIDDEN_PATHS.search(relative):
            problems.append(f"forbidden tracked path: {relative}")
            continue
        path = ROOT / relative
        if not path.is_file() or path.stat().st_size > 2_000_000:
            continue
        if relative == "tools/security_guard.py":
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if relative == ".env.example":
            text = text.replace("MODEL_API_KEY=", "")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                problems.append(f"possible secret in: {relative}")
                break
    return problems


if __name__ == "__main__":
    found = violations()
    if found:
        raise SystemExit("\n".join(found))
    print("security guard passed")
