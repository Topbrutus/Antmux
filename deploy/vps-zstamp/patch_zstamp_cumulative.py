from __future__ import annotations

import hashlib
import sys
from pathlib import Path

EXPECTED_DASH = "1892c2abf4b3dc535a2b1feeb08678e372bfe925bb786dadeaab1a85c49d61e9"
MARKER = "total_children_stamped"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected 1 replacement, found {count}")
    return text.replace(old, new, 1)


def patch(root: Path) -> None:
    path = root / "src" / "brotoculateur" / "dashboard.py"
    text = path.read_text(encoding="utf-8")
    if MARKER in text:
        print("ZSTAMP_CUMULATIVE_PATCH=ALREADY_APPLIED")
        print(f"DASHBOARD_SHA256={sha(path)}")
        return
    actual = sha(path)
    if actual != EXPECTED_DASH:
        raise RuntimeError(f"dashboard hash drift: {actual} != {EXPECTED_DASH}")

    text = replace_once(
        text,
        "        self._cumulative_processed = 0\n        self._session_started_monotonic: float | None = None\n",
        "        self._cumulative_processed = 0\n        self._zstamp_cumulative = {\"root_selected\": 0, \"root_passthrough\": 0, \"children_stamped\": 0}\n        self._session_started_monotonic: float | None = None\n",
        "init cumulative",
    )
    text = replace_once(
        text,
        "            self._cumulative_processed = 0\n            self._session_started_monotonic = None\n",
        "            self._cumulative_processed = 0\n            self._zstamp_cumulative = {\"root_selected\": 0, \"root_passthrough\": 0, \"children_stamped\": 0}\n            self._session_started_monotonic = None\n",
        "reset cumulative",
    )
    text = replace_once(
        text,
        "    def _advance_round_unlocked(self) -> None:\n",
        "    def _zstamp_rollup_unlocked(self) -> None:\n        current = self._runner.zstamp_status()\n        for key in (\"root_selected\", \"root_passthrough\", \"children_stamped\"):\n            self._zstamp_cumulative[key] += int(current.get(key) or 0)\n\n    def _zstamp_status_unlocked(self) -> dict[str, Any]:\n        current = dict(self._runner.zstamp_status())\n        current[\"total_root_selected\"] = self._zstamp_cumulative[\"root_selected\"] + int(current.get(\"root_selected\") or 0)\n        current[\"total_root_passthrough\"] = self._zstamp_cumulative[\"root_passthrough\"] + int(current.get(\"root_passthrough\") or 0)\n        current[\"total_children_stamped\"] = self._zstamp_cumulative[\"children_stamped\"] + int(current.get(\"children_stamped\") or 0)\n        current[\"cumulative_across_rounds\"] = True\n        return current\n\n    def _advance_round_unlocked(self) -> None:\n",
        "cumulative helpers",
    )
    text = replace_once(
        text,
        "        self._cumulative_processed += self._runner.processed_packets\n        self._round_seeds = self._next_round_seeds_unlocked()\n",
        "        self._cumulative_processed += self._runner.processed_packets\n        self._zstamp_rollup_unlocked()\n        self._round_seeds = self._next_round_seeds_unlocked()\n",
        "rollup on round",
    )
    text = replace_once(
        text,
        "            \"brutus_cortex\": self._runner.zstamp_status(),\n",
        "            \"brutus_cortex\": self._zstamp_status_unlocked(),\n",
        "status cumulative",
    )

    # Force LF bytes on every platform so the expected post-patch hash is stable.
    path.write_bytes(text.replace("\r\n", "\n").encode("utf-8"))
    print("ZSTAMP_CUMULATIVE_PATCH=PASS")
    print(f"DASHBOARD_SHA256={sha(path)}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: patch_zstamp_cumulative.py <brotoculateur-root>")
    patch(Path(sys.argv[1]).resolve())
