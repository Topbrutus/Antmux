from __future__ import annotations

import hashlib
import sys
from pathlib import Path


EXPECTED_ORCH = "2ba8a93967e3f01147acbd2a5220857830cd89ce3bdcba879e8d5630292fdb87"
EXPECTED_DASH = "2602f91205457dc8b474ab098a0ed4453153054ff0ef4f9f73b9c2eca4ccc157"
EXPECTED_C3 = "b7970583e688488d0f9fd8a90838d9163d00b08b7e6afedd499434e79a06c434"
MARKER = "BRUTUS_C4_NOVELTY_V1"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected 1 match, got {count}")
    return text.replace(old, new, 1)


def patch(root: Path) -> None:
    pkg = root / "src" / "brotoculateur"
    orch_path = pkg / "orchestrator.py"
    dash_path = pkg / "dashboard.py"
    c3_path = pkg / "c3_library.py"
    c4_path = pkg / "c4_novelty.py"
    c4_source = Path(__file__).with_name("c4_novelty.py")
    if not c4_source.is_file():
        raise RuntimeError("c4_novelty.py staging source missing")

    c4_bytes = c4_source.read_bytes().replace(b"\r\n", b"\n")
    c4_hash = hashlib.sha256(c4_bytes).hexdigest()
    orch_text = orch_path.read_text(encoding="utf-8")
    dash_text = dash_path.read_text(encoding="utf-8")

    if MARKER in orch_text and '"c4_novelty"' in dash_text:
        if not c4_path.is_file() or sha(c4_path) != c4_hash:
            raise RuntimeError("C4 marker present but c4_novelty.py hash drifted")
        print("C4_PATCH=ALREADY_APPLIED")
        print(f"C4_NOVELTY_SHA256={sha(c4_path)}")
        print(f"ORCHESTRATOR_SHA256={sha(orch_path)}")
        print(f"DASHBOARD_SHA256={sha(dash_path)}")
        return

    if sha(orch_path) != EXPECTED_ORCH:
        raise RuntimeError(f"orchestrator hash drift: {sha(orch_path)} != {EXPECTED_ORCH}")
    if sha(dash_path) != EXPECTED_DASH:
        raise RuntimeError(f"dashboard hash drift: {sha(dash_path)} != {EXPECTED_DASH}")
    if not c3_path.is_file() or sha(c3_path) != EXPECTED_C3:
        raise RuntimeError("C4 requires exact C3 library source")
    if c4_path.exists():
        raise RuntimeError("unexpected pre-existing c4_novelty.py")

    c4_path.write_bytes(c4_bytes)

    orch = orch_text
    orch = replace_once(
        orch,
        "from .c3_library import C3Library37\n",
        "from .c3_library import C3Library37\nfrom .c4_novelty import C4Novelty\n",
        "orchestrator C4 import",
    )
    orch = replace_once(
        orch,
        "        sleeping_pool_enabled: bool = False,\n        c3_library: C3Library37 | None = None,\n    ) -> None:\n",
        "        sleeping_pool_enabled: bool = False,\n        c3_library: C3Library37 | None = None,\n        c4_novelty: C4Novelty | None = None,\n    ) -> None:\n",
        "runner C4 parameter",
    )
    orch = replace_once(
        orch,
        "        self.c3_library = c3_library\n        self.spec = spec or ExperimentSpec()\n",
        "        self.c3_library = c3_library\n        self.c4_novelty = c4_novelty\n        self.spec = spec or ExperimentSpec()\n",
        "runner C4 assignment",
    )
    orch = replace_once(
        orch,
        "        self.c3_requested = os.getenv(\"BROTO_C3_ENABLED\", \"0\").strip().lower() in {\"1\", \"true\", \"yes\", \"on\"}\n        self.c3_enabled = bool(self.c3_requested and self.c2_enabled and self.c3_library is not None)\n        self.c2_roots = 0\n",
        "        self.c3_requested = os.getenv(\"BROTO_C3_ENABLED\", \"0\").strip().lower() in {\"1\", \"true\", \"yes\", \"on\"}\n        self.c3_enabled = bool(self.c3_requested and self.c2_enabled and self.c3_library is not None)\n        self.c4_requested = os.getenv(\"BROTO_C4_ENABLED\", \"0\").strip().lower() in {\"1\", \"true\", \"yes\", \"on\"}\n        self.c4_enabled = bool(self.c4_requested and self.c3_enabled and self.c4_novelty is not None)\n        self.c2_roots = 0\n",
        "runner C4 flags",
    )
    orch = replace_once(
        orch,
        "        if self.c3_enabled and self.c3_library is not None:\n            self.c3_library.observe(fingerprint)\n        return fingerprint\n",
        "        if self.c3_enabled and self.c3_library is not None:\n            c3_hit = self.c3_library.observe(fingerprint)\n            if self.c4_enabled and self.c4_novelty is not None:\n                self.c4_novelty.observe(\n                    fingerprint,\n                    c3_hit=c3_hit,\n                    c3_retained=self.c3_library.contains(fingerprint),\n                )\n        return fingerprint\n",
        "C3 to C4 observation",
    )
    orch = replace_once(
        orch,
        "    def c3_status(self) -> dict[str, object]:\n",
        "    def c4_status(self) -> dict[str, object]:\n        if self.c4_novelty is None:\n            return {\n                \"mode\": \"BRUTUS_C4_NOVELTY_V1\",\n                \"enabled\": False,\n                \"requested\": self.c4_requested,\n                \"authority\": \"SHADOW_ONLY\",\n                \"source_of_truth\": \"C3_EXACT_HIT_MISS\",\n                \"observations\": 0,\n                \"known\": 0,\n                \"novel_candidates\": 0,\n                \"scientific_discovery_claim\": False,\n                \"compute_skips\": 0,\n                \"proof_promotion\": False,\n            }\n        current = dict(self.c4_novelty.status())\n        current[\"enabled\"] = self.c4_enabled\n        current[\"requested\"] = self.c4_requested\n        current[\"c3_required\"] = True\n        current[\"c3_enabled\"] = self.c3_enabled\n        current[\"scope\"] = \"C3_EXACT_HIT_MISS_ONLY\"\n        return current\n\n    def c3_status(self) -> dict[str, object]:\n",
        "runner C4 status",
    )
    orch_path.write_bytes(orch.replace("\r\n", "\n").encode("utf-8"))

    dash = dash_text
    dash = replace_once(
        dash,
        "from .c3_library import C3Library37\n",
        "from .c3_library import C3Library37\nfrom .c4_novelty import C4Novelty\n",
        "dashboard C4 import",
    )
    dash = replace_once(
        dash,
        "        self.c3_library = C3Library37()\n        self._lock = threading.RLock()\n",
        "        self.c3_library = C3Library37()\n        self.c4_novelty = C4Novelty()\n        self._lock = threading.RLock()\n",
        "dashboard C4 init",
    )
    dash = replace_once(
        dash,
        "            c3_library=self.c3_library,\n        )\n",
        "            c3_library=self.c3_library,\n            c4_novelty=self.c4_novelty,\n        )\n",
        "dashboard pass C4",
    )
    dash = replace_once(
        dash,
        "            self.c3_library = C3Library37()\n            self._session_started_monotonic = None\n",
        "            self.c3_library = C3Library37()\n            self.c4_novelty = C4Novelty()\n            self._session_started_monotonic = None\n",
        "dashboard C4 reset",
    )
    dash = replace_once(
        dash,
        "            \"c3_library\": self._runner.c3_status(),\n            \"hierarchical_rarity\": self._runner.rarity_status(),\n",
        "            \"c3_library\": self._runner.c3_status(),\n            \"c4_novelty\": self._runner.c4_status(),\n            \"hierarchical_rarity\": self._runner.rarity_status(),\n",
        "dashboard C4 status",
    )
    dash_path.write_bytes(dash.replace("\r\n", "\n").encode("utf-8"))

    print("C4_PATCH=PASS")
    print(f"C4_NOVELTY_SHA256={sha(c4_path)}")
    print(f"ORCHESTRATOR_SHA256={sha(orch_path)}")
    print(f"DASHBOARD_SHA256={sha(dash_path)}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: patch_brotoculateur_c4_novelty.py <brotoculateur-root>")
    patch(Path(sys.argv[1]).resolve())
