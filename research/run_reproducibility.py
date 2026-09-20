from __future__ import annotations

import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TESTS = ROOT / "deploy" / "x72-shared-queen" / "tests"

COMMANDS = [
    [sys.executable, str(TESTS / "test_z3_center_coupling.py")],
    [sys.executable, str(TESTS / "test_z3_center_coupling_adversarial.py")],
    [sys.executable, str(TESTS / "test_stereo_source.py")],
    [sys.executable, str(TESTS / "test_z3_runtime_bridge.py")],
    [sys.executable, str(TESTS / "test_eye_render.py")],
    [sys.executable, str(TESTS / "test_cat_mode_ui.py")],
]


def git_head() -> str:
    result = subprocess.run(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"],
        text=True,
        capture_output=True,
        check=True,
    )
    return result.stdout.strip()


def run_one(command: list[str]) -> dict[str, object]:
    completed = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    return {
        "command": command,
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
        "passed": completed.returncode == 0,
    }


def main() -> int:
    results = [run_one(command) for command in COMMANDS]
    report = {
        "schema": "ANTMUX-X72-REPRODUCIBILITY-v0.1",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "git_head": git_head(),
        "python": sys.version,
        "platform": platform.platform(),
        "tests_total": len(results),
        "tests_passed": sum(1 for item in results if item["passed"]),
        "results": results,
    }

    output = ROOT / "research" / "reproducibility_report.json"
    output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["tests_total"] == report["tests_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
