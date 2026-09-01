"""Run the real API and web console together for the local risk-audit demo."""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON = ROOT / ".venv" / "bin" / "python"


def main() -> int:
    python = str(PYTHON if PYTHON.exists() else Path(sys.executable))
    environment = {**os.environ, "CELERY_TASK_ALWAYS_EAGER": "true"}
    processes = [
        subprocess.Popen(
            [
                python,
                "-m",
                "uvicorn",
                "arena.interfaces.http.app:app",
                "--app-dir",
                "apps/api/src",
                "--host",
                "127.0.0.1",
                "--port",
                "8000",
            ],
            cwd=ROOT,
            env=environment,
        ),
        subprocess.Popen(["pnpm", "dev"], cwd=ROOT / "apps" / "web", env=environment),
    ]

    def stop(*_args) -> None:
        for process in processes:
            if process.poll() is None:
                process.send_signal(signal.SIGTERM)

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)
    print("Risk demo ready at http://127.0.0.1:5173")
    try:
        while True:
            for process in processes:
                return_code = process.poll()
                if return_code is not None:
                    return return_code
            time.sleep(0.25)
    finally:
        stop()


if __name__ == "__main__":
    raise SystemExit(main())
