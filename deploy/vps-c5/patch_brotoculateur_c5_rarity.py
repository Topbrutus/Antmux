from __future__ import annotations

import hashlib
import sys
from pathlib import Path


EXPECTED_ORCH = "0c29aae538c5ea69a3f3a235d7fd377bddd83b339a7f6cda5b091bbd9ae2642f"
EXPECTED_DASH = "a55b055ee31816fda113f71d28499b1c4a697a8b123ee01dc852d86984dbc7fe"
EXPECTED_C3 = "b7970583e688488d0f9fd8a90838d9163d00b08b7e6afedd499434e79a06c434"
EXPECTED_C4 = "d9669cdcdbd300529ff63a07fc088be6a9e60fdc65315015b1904f83d42e10f2"
MARKER = "BRUTUS_C5_STRUCTURAL_RARITY_V1"


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
    module_path = pkg / "c5_rarity.py"
    module_source = Path(__file__).with_name("c5_rarity.py")
    if not module_source.is_file():
        raise RuntimeError("c5_rarity.py staging source missing")

    module_bytes = module_source.read_bytes().replace(b"\r\n", b"\n")
    module_hash = hashlib.sha256(module_bytes).hexdigest()
    orch_text = orch_path.read_text(encoding="utf-8")
    dash_text = dash_path.read_text(encoding="utf-8")

    if MARKER in orch_text and '"c5_rarity"' in dash_text:
        if not module_path.is_file() or sha(module_path) != module_hash:
            raise RuntimeError("C5 marker present but c5_rarity.py hash drifted")
        print("C5_PATCH=ALREADY_APPLIED")
        print(f"C5_RARITY_SHA256={sha(module_path)}")
        print(f"ORCHESTRATOR_SHA256={sha(orch_path)}")
        print(f"DASHBOARD_SHA256={sha(dash_path)}")
        return

    expected = ((orch_path, EXPECTED_ORCH), (dash_path, EXPECTED_DASH), (c3_path, EXPECTED_C3), (c4_path, EXPECTED_C4))
    for path, digest in expected:
        if not path.is_file() or sha(path) != digest:
            raise RuntimeError(f"hash drift: {path.name} {sha(path) if path.exists() else 'ABSENT'} != {digest}")
    if module_path.exists():
        raise RuntimeError("unexpected pre-existing c5_rarity.py")
    module_path.write_bytes(module_bytes)

    orch = orch_text
    orch = replace_once(
        orch,
        "from .c4_novelty import C4Novelty\n",
        "from .c4_novelty import C4Novelty\nfrom .c5_rarity import C5StructuralRarity\n",
        "orchestrator C5 import",
    )
    orch = replace_once(
        orch,
        "        c3_library: C3Library37 | None = None,\n        c4_novelty: C4Novelty | None = None,\n    ) -> None:\n",
        "        c3_library: C3Library37 | None = None,\n        c4_novelty: C4Novelty | None = None,\n        c5_rarity: C5StructuralRarity | None = None,\n    ) -> None:\n",
        "runner C5 parameter",
    )
    orch = replace_once(
        orch,
        "        self.c3_library = c3_library\n        self.c4_novelty = c4_novelty\n        self.spec = spec or ExperimentSpec()\n",
        "        self.c3_library = c3_library\n        self.c4_novelty = c4_novelty\n        self.c5_rarity = c5_rarity\n        self.spec = spec or ExperimentSpec()\n",
        "runner C5 assignment",
    )
    orch = replace_once(
        orch,
        "        self.c4_requested = os.getenv(\"BROTO_C4_ENABLED\", \"0\").strip().lower() in {\"1\", \"true\", \"yes\", \"on\"}\n        self.c4_enabled = bool(self.c4_requested and self.c3_enabled and self.c4_novelty is not None)\n        self.c2_roots = 0\n",
        "        self.c4_requested = os.getenv(\"BROTO_C4_ENABLED\", \"0\").strip().lower() in {\"1\", \"true\", \"yes\", \"on\"}\n        self.c4_enabled = bool(self.c4_requested and self.c3_enabled and self.c4_novelty is not None)\n        self.c5_requested = os.getenv(\"BROTO_C5_ENABLED\", \"0\").strip().lower() in {\"1\", \"true\", \"yes\", \"on\"}\n        self.c5_enabled = bool(self.c5_requested and self.c4_enabled and self.c5_rarity is not None)\n        self.c2_roots = 0\n",
        "runner C5 flags",
    )
    orch = replace_once(
        orch,
        "            c3_hit = self.c3_library.observe(fingerprint)\n            if self.c4_enabled and self.c4_novelty is not None:\n                self.c4_novelty.observe(\n                    fingerprint,\n                    c3_hit=c3_hit,\n                    c3_retained=self.c3_library.contains(fingerprint),\n                )\n",
        "            c3_hit = self.c3_library.observe(fingerprint)\n            c3_retained = self.c3_library.contains(fingerprint)\n            if self.c4_enabled and self.c4_novelty is not None:\n                self.c4_novelty.observe(\n                    fingerprint,\n                    c3_hit=c3_hit,\n                    c3_retained=c3_retained,\n                )\n            if self.c5_enabled and self.c5_rarity is not None:\n                self.c5_rarity.observe(\n                    fingerprint,\n                    observation_count=self.c3_library.count(fingerprint),\n                    c3_retained=c3_retained,\n                )\n",
        "C3 to C4/C5 observation",
    )
    orch = replace_once(
        orch,
        "    def c4_status(self) -> dict[str, object]:\n",
        "    def c5_status(self) -> dict[str, object]:\n        if self.c5_rarity is None:\n            return {\n                \"mode\": \"BRUTUS_C5_STRUCTURAL_RARITY_V1\",\n                \"enabled\": False,\n                \"requested\": self.c5_requested,\n                \"authority\": \"SHADOW_ONLY\",\n                \"subject\": \"C2_STRUCTURAL_FINGERPRINT_RECURRENCE\",\n                \"observations\": 0,\n                \"controls_scheduling\": False,\n                \"compute_skips\": 0,\n                \"proof_promotion\": False,\n            }\n        current = dict(self.c5_rarity.status())\n        current[\"enabled\"] = self.c5_enabled\n        current[\"requested\"] = self.c5_requested\n        current[\"c4_required\"] = True\n        current[\"c4_enabled\"] = self.c4_enabled\n        current[\"c3_required\"] = True\n        current[\"c3_enabled\"] = self.c3_enabled\n        return current\n\n    def c4_status(self) -> dict[str, object]:\n",
        "runner C5 status",
    )
    orch_path.write_bytes(orch.replace("\r\n", "\n").encode("utf-8"))

    dash = dash_text
    dash = replace_once(
        dash,
        "from .c4_novelty import C4Novelty\n",
        "from .c4_novelty import C4Novelty\nfrom .c5_rarity import C5StructuralRarity\n",
        "dashboard C5 import",
    )
    dash = replace_once(
        dash,
        "        self.c3_library = C3Library37()\n        self.c4_novelty = C4Novelty()\n        self._lock = threading.RLock()\n",
        "        self.c3_library = C3Library37()\n        self.c4_novelty = C4Novelty()\n        self.c5_rarity = C5StructuralRarity()\n        self._lock = threading.RLock()\n",
        "dashboard C5 init",
    )
    dash = replace_once(
        dash,
        "            c3_library=self.c3_library,\n            c4_novelty=self.c4_novelty,\n        )\n",
        "            c3_library=self.c3_library,\n            c4_novelty=self.c4_novelty,\n            c5_rarity=self.c5_rarity,\n        )\n",
        "dashboard pass C5",
    )
    dash = replace_once(
        dash,
        "            self.c3_library = C3Library37()\n            self.c4_novelty = C4Novelty()\n            self._session_started_monotonic = None\n",
        "            self.c3_library = C3Library37()\n            self.c4_novelty = C4Novelty()\n            self.c5_rarity = C5StructuralRarity()\n            self._session_started_monotonic = None\n",
        "dashboard C5 reset",
    )
    dash = replace_once(
        dash,
        "            \"c3_library\": self._runner.c3_status(),\n            \"c4_novelty\": self._runner.c4_status(),\n            \"hierarchical_rarity\": self._runner.rarity_status(),\n",
        "            \"c3_library\": self._runner.c3_status(),\n            \"c4_novelty\": self._runner.c4_status(),\n            \"c5_rarity\": self._runner.c5_status(),\n            \"hierarchical_rarity\": self._runner.rarity_status(),\n",
        "dashboard C5 status",
    )
    dash_path.write_bytes(dash.replace("\r\n", "\n").encode("utf-8"))

    print("C5_PATCH=PASS")
    print(f"C5_RARITY_SHA256={sha(module_path)}")
    print(f"ORCHESTRATOR_SHA256={sha(orch_path)}")
    print(f"DASHBOARD_SHA256={sha(dash_path)}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: patch_brotoculateur_c5_rarity.py <brotoculateur-root>")
    patch(Path(sys.argv[1]).resolve())
