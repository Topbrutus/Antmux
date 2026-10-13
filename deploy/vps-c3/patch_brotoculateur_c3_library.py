from __future__ import annotations

import hashlib
import sys
from pathlib import Path


EXPECTED_ORCH = "20e019e58f77fbd0ea5a983112b8ed5809bad236d8f02df52ea3c65f710f0f83"
EXPECTED_DASH = "5410dc0aebb273eddf616dc3b08e53666f6473c25eb5a00ebb44003f2bb00ce2"
MARKER = "BRUTUS_C3_LIBRARY37_V1"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected 1 replacement, found {count}")
    return text.replace(old, new, 1)


def patch(root: Path) -> None:
    pkg = root / "src" / "brotoculateur"
    orch_path = pkg / "orchestrator.py"
    dash_path = pkg / "dashboard.py"
    module_path = pkg / "c3_library.py"
    module_source = Path(__file__).with_name("c3_library.py")
    if not module_source.is_file():
        raise RuntimeError("c3_library.py staging source missing")

    module_bytes = module_source.read_bytes().replace(b"\r\n", b"\n")
    module_hash = hashlib.sha256(module_bytes).hexdigest()
    orch_text = orch_path.read_text(encoding="utf-8")
    dash_text = dash_path.read_text(encoding="utf-8")

    if MARKER in orch_text and '"c3_library"' in dash_text:
        if not module_path.is_file() or sha(module_path) != module_hash:
            raise RuntimeError("C3 marker present but c3_library.py hash drifted")
        print("C3_PATCH=ALREADY_APPLIED")
        print(f"C3_LIBRARY_SHA256={sha(module_path)}")
        print(f"ORCHESTRATOR_SHA256={sha(orch_path)}")
        print(f"DASHBOARD_SHA256={sha(dash_path)}")
        return

    if sha(orch_path) != EXPECTED_ORCH:
        raise RuntimeError(f"orchestrator hash drift: {sha(orch_path)} != {EXPECTED_ORCH}")
    if sha(dash_path) != EXPECTED_DASH:
        raise RuntimeError(f"dashboard hash drift: {sha(dash_path)} != {EXPECTED_DASH}")
    if module_path.exists():
        raise RuntimeError("unexpected pre-existing c3_library.py")

    module_path.write_bytes(module_bytes)

    orch = orch_text
    orch = replace_once(
        orch,
        "from .papillon_engine import Papillon144\nfrom .sleeping_pool import PapillonSleepingPool\n",
        "from .papillon_engine import Papillon144\nfrom .sleeping_pool import PapillonSleepingPool\nfrom .c3_library import C3Library37\n",
        "orchestrator C3 import",
    )
    orch = replace_once(
        orch,
        "        papillon_enabled: bool = True,\n        sleeping_pool_enabled: bool = False,\n    ) -> None:\n",
        "        papillon_enabled: bool = True,\n        sleeping_pool_enabled: bool = False,\n        c3_library: C3Library37 | None = None,\n    ) -> None:\n",
        "runner C3 parameter",
    )
    orch = replace_once(
        orch,
        "        self.sleeping_pool_enabled = bool(sleeping_pool_enabled)\n        self.sleeping_pool = PapillonSleepingPool() if self.sleeping_pool_enabled else None\n        self.spec = spec or ExperimentSpec()\n",
        "        self.sleeping_pool_enabled = bool(sleeping_pool_enabled)\n        self.sleeping_pool = PapillonSleepingPool() if self.sleeping_pool_enabled else None\n        self.c3_library = c3_library\n        self.spec = spec or ExperimentSpec()\n",
        "runner C3 library assignment",
    )
    orch = replace_once(
        orch,
        "        self.c2_enabled = os.getenv(\"BROTO_C2_ENABLED\", \"0\").strip().lower() in {\"1\", \"true\", \"yes\", \"on\"}\n        self.c2_roots = 0\n",
        "        self.c2_enabled = os.getenv(\"BROTO_C2_ENABLED\", \"0\").strip().lower() in {\"1\", \"true\", \"yes\", \"on\"}\n        self.c3_requested = os.getenv(\"BROTO_C3_ENABLED\", \"0\").strip().lower() in {\"1\", \"true\", \"yes\", \"on\"}\n        self.c3_enabled = bool(self.c3_requested and self.c2_enabled and self.c3_library is not None)\n        self.c2_roots = 0\n",
        "runner C3 flags",
    )
    orch = replace_once(
        orch,
        "        if self.c2_first is None:\n            self.c2_first = fingerprint\n        self.c2_last = fingerprint\n        return fingerprint\n",
        "        if self.c2_first is None:\n            self.c2_first = fingerprint\n        self.c2_last = fingerprint\n        if self.c3_enabled and self.c3_library is not None:\n            self.c3_library.observe(fingerprint)\n        return fingerprint\n",
        "C2 to C3 observation",
    )
    orch = replace_once(
        orch,
        "    def c2_status(self) -> dict[str, object]:\n",
        "    def c3_status(self) -> dict[str, object]:\n        if self.c3_library is None:\n            return {\n                \"mode\": \"BRUTUS_C3_LIBRARY37_V1\",\n                \"enabled\": False,\n                \"requested\": self.c3_requested,\n                \"scope\": \"C2_FINGERPRINTS_ONLY\",\n                \"authority\": \"SHADOW_ONLY\",\n                \"bucket_count\": 37,\n                \"observations\": 0,\n                \"hits\": 0,\n                \"misses\": 0,\n                \"unique_entries\": 0,\n                \"compute_skips\": 0,\n                \"proof_promotion\": False,\n            }\n        current = dict(self.c3_library.status())\n        current[\"enabled\"] = self.c3_enabled\n        current[\"requested\"] = self.c3_requested\n        current[\"scope\"] = \"C2_FINGERPRINTS_ONLY\"\n        current[\"inherits_zstamp_canary\"] = True\n        current[\"c2_required\"] = True\n        current[\"c2_enabled\"] = self.c2_enabled\n        return current\n\n    def c2_status(self) -> dict[str, object]:\n",
        "runner C3 status",
    )
    orch_path.write_bytes(orch.replace("\r\n", "\n").encode("utf-8"))

    dash = dash_text
    dash = replace_once(
        dash,
        "from .brutomagique import Brutomagique49_50\n",
        "from .brutomagique import Brutomagique49_50\nfrom .c3_library import C3Library37\n",
        "dashboard C3 import",
    )
    dash = replace_once(
        dash,
        "        self.sleeping_pool_enabled = bool(sleeping_pool_enabled)\n        self._lock = threading.RLock()\n",
        "        self.sleeping_pool_enabled = bool(sleeping_pool_enabled)\n        self.c3_library = C3Library37()\n        self._lock = threading.RLock()\n",
        "dashboard C3 init",
    )
    dash = replace_once(
        dash,
        "            observation_sink=self._observe_formula_result,\n            sleeping_pool_enabled=self.sleeping_pool_enabled,\n        )\n",
        "            observation_sink=self._observe_formula_result,\n            sleeping_pool_enabled=self.sleeping_pool_enabled,\n            c3_library=self.c3_library,\n        )\n",
        "dashboard pass C3 library",
    )
    dash = replace_once(
        dash,
        "            self._c2_cumulative = {\"roots_fingerprinted\": 0, \"children_fingerprinted\": 0, \"first_fingerprint\": None, \"last_fingerprint\": None}\n            self._session_started_monotonic = None\n",
        "            self._c2_cumulative = {\"roots_fingerprinted\": 0, \"children_fingerprinted\": 0, \"first_fingerprint\": None, \"last_fingerprint\": None}\n            self.c3_library = C3Library37()\n            self._session_started_monotonic = None\n",
        "dashboard C3 reset",
    )
    dash = replace_once(
        dash,
        "            \"c2_fingerprint\": self._c2_status_unlocked(),\n            \"hierarchical_rarity\": self._runner.rarity_status(),\n",
        "            \"c2_fingerprint\": self._c2_status_unlocked(),\n            \"c3_library\": self._runner.c3_status(),\n            \"hierarchical_rarity\": self._runner.rarity_status(),\n",
        "dashboard C3 status",
    )
    dash_path.write_bytes(dash.replace("\r\n", "\n").encode("utf-8"))

    print("C3_PATCH=PASS")
    print(f"C3_LIBRARY_SHA256={sha(module_path)}")
    print(f"ORCHESTRATOR_SHA256={sha(orch_path)}")
    print(f"DASHBOARD_SHA256={sha(dash_path)}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: patch_brotoculateur_c3_library.py <brotoculateur-root>")
    patch(Path(sys.argv[1]).resolve())
