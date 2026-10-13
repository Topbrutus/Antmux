from __future__ import annotations

import hashlib
import sys
from pathlib import Path

EXPECTED_ORCH = "0582f5c443d67015ab88286591cbca71650a574ef38859b1563223a93c53285d"
EXPECTED_DASH = "1f571adba61d948d0e5189843e0565ebb225f20bbeed9d9159f1f719e804efe9"
EXPECTED_C5 = "d8a02ccecffddffc6db8d8810e84875184861d5446eea8304d23cc8adc483999"
MARKER = "BRUTUS_C6_PROVENANCE_V1"


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
    c5_path = pkg / "c5_rarity.py"
    module_path = pkg / "c6_provenance.py"
    module_source = Path(__file__).with_name("c6_provenance.py")
    if not module_source.is_file():
        raise RuntimeError("c6_provenance.py staging source missing")

    module_bytes = module_source.read_bytes().replace(b"\r\n", b"\n")
    module_hash = hashlib.sha256(module_bytes).hexdigest()
    orch_text = orch_path.read_text(encoding="utf-8")
    dash_text = dash_path.read_text(encoding="utf-8")

    if MARKER in orch_text and '"c6_provenance"' in dash_text:
        if not module_path.is_file() or sha(module_path) != module_hash:
            raise RuntimeError("C6 marker present but c6_provenance.py hash drifted")
        print("C6_PATCH=ALREADY_APPLIED")
        print(f"C6_PROVENANCE_SHA256={sha(module_path)}")
        print(f"ORCHESTRATOR_SHA256={sha(orch_path)}")
        print(f"DASHBOARD_SHA256={sha(dash_path)}")
        return

    if sha(orch_path) != EXPECTED_ORCH:
        raise RuntimeError(f"orchestrator hash drift: {sha(orch_path)} != {EXPECTED_ORCH}")
    if sha(dash_path) != EXPECTED_DASH:
        raise RuntimeError(f"dashboard hash drift: {sha(dash_path)} != {EXPECTED_DASH}")
    if sha(c5_path) != EXPECTED_C5:
        raise RuntimeError(f"c5 hash drift: {sha(c5_path)} != {EXPECTED_C5}")
    if module_path.exists():
        raise RuntimeError("unexpected pre-existing c6_provenance.py")

    module_path.write_bytes(module_bytes)

    orch = orch_text
    orch = replace_once(
        orch,
        "from .c5_rarity import C5StructuralRarity\n",
        "from .c5_rarity import C5StructuralRarity\nfrom .c6_provenance import C6Provenance\n",
        "orchestrator C6 import",
    )
    orch = replace_once(
        orch,
        "        c5_rarity: C5StructuralRarity | None = None,\n    ) -> None:\n",
        "        c5_rarity: C5StructuralRarity | None = None,\n        c6_provenance: C6Provenance | None = None,\n    ) -> None:\n",
        "runner C6 parameter",
    )
    orch = replace_once(
        orch,
        "        self.c5_rarity = c5_rarity\n        self.spec = spec or ExperimentSpec()\n",
        "        self.c5_rarity = c5_rarity\n        self.c6_provenance = c6_provenance\n        self.spec = spec or ExperimentSpec()\n",
        "runner C6 assignment",
    )
    orch = replace_once(
        orch,
        "        self.c5_requested = os.getenv(\"BROTO_C5_ENABLED\", \"0\").strip().lower() in {\"1\", \"true\", \"yes\", \"on\"}\n        self.c5_enabled = bool(self.c5_requested and self.c4_enabled and self.c5_rarity is not None)\n        self.c2_roots = 0\n",
        "        self.c5_requested = os.getenv(\"BROTO_C5_ENABLED\", \"0\").strip().lower() in {\"1\", \"true\", \"yes\", \"on\"}\n        self.c5_enabled = bool(self.c5_requested and self.c4_enabled and self.c5_rarity is not None)\n        self.c6_requested = os.getenv(\"BROTO_C6_ENABLED\", \"0\").strip().lower() in {\"1\", \"true\", \"yes\", \"on\"}\n        self.c6_enabled = bool(self.c6_requested and self.c5_enabled and self.c6_provenance is not None)\n        self.c2_roots = 0\n",
        "runner C6 flags",
    )
    orch = replace_once(
        orch,
        "            if self.c5_enabled and self.c5_rarity is not None:\n                self.c5_rarity.observe(\n                    fingerprint,\n                    observation_count=self.c3_library.count(fingerprint),\n                    c3_retained=c3_retained,\n                )\n        return fingerprint\n",
        "            c5_class = None\n            if self.c5_enabled and self.c5_rarity is not None:\n                c5_class = self.c5_rarity.observe(\n                    fingerprint,\n                    observation_count=self.c3_library.count(fingerprint),\n                    c3_retained=c3_retained,\n                )\n            if self.c6_enabled and self.c6_provenance is not None:\n                self.c6_provenance.observe(\n                    packet,\n                    fingerprint,\n                    c3_retained=c3_retained,\n                    c5_class=c5_class,\n                )\n        return fingerprint\n",
        "C5 to C6 observation",
    )
    orch = replace_once(
        orch,
        "    def c5_status(self) -> dict[str, object]:\n",
        "    def c6_status(self) -> dict[str, object]:\n        if self.c6_provenance is None:\n            return {\n                \"mode\": \"BRUTUS_C6_PROVENANCE_V1\",\n                \"enabled\": False,\n                \"requested\": self.c6_requested,\n                \"authority\": \"SHADOW_ONLY\",\n                \"observations\": 0,\n                \"scientific_independence_claim\": False,\n                \"controls_scheduling\": False,\n                \"compute_skips\": 0,\n                \"proof_promotion\": False,\n            }\n        current = dict(self.c6_provenance.status())\n        current[\"enabled\"] = self.c6_enabled\n        current[\"requested\"] = self.c6_requested\n        current[\"c5_required\"] = True\n        current[\"c5_enabled\"] = self.c5_enabled\n        current[\"c4_required\"] = True\n        current[\"c4_enabled\"] = self.c4_enabled\n        return current\n\n    def c5_status(self) -> dict[str, object]:\n",
        "runner C6 status",
    )
    orch_path.write_bytes(orch.replace("\r\n", "\n").encode("utf-8"))

    dash = dash_text
    dash = replace_once(
        dash,
        "from .c5_rarity import C5StructuralRarity\n",
        "from .c5_rarity import C5StructuralRarity\nfrom .c6_provenance import C6Provenance\n",
        "dashboard C6 import",
    )
    dash = replace_once(
        dash,
        "        self.c5_rarity = C5StructuralRarity()\n        self._lock = threading.RLock()\n",
        "        self.c5_rarity = C5StructuralRarity()\n        self.c6_provenance = C6Provenance()\n        self._lock = threading.RLock()\n",
        "dashboard C6 init",
    )
    dash = replace_once(
        dash,
        "            c5_rarity=self.c5_rarity,\n        )\n",
        "            c5_rarity=self.c5_rarity,\n            c6_provenance=self.c6_provenance,\n        )\n",
        "dashboard pass C6",
    )
    dash = replace_once(
        dash,
        "            self.c5_rarity = C5StructuralRarity()\n            self._session_started_monotonic = None\n",
        "            self.c5_rarity = C5StructuralRarity()\n            self.c6_provenance = C6Provenance()\n            self._session_started_monotonic = None\n",
        "dashboard C6 reset",
    )
    dash = replace_once(
        dash,
        "            \"c5_rarity\": self._runner.c5_status(),\n            \"hierarchical_rarity\": self._runner.rarity_status(),\n",
        "            \"c5_rarity\": self._runner.c5_status(),\n            \"c6_provenance\": self._runner.c6_status(),\n            \"hierarchical_rarity\": self._runner.rarity_status(),\n",
        "dashboard C6 status",
    )
    dash_path.write_bytes(dash.replace("\r\n", "\n").encode("utf-8"))

    print("C6_PATCH=PASS")
    print(f"C6_PROVENANCE_SHA256={sha(module_path)}")
    print(f"ORCHESTRATOR_SHA256={sha(orch_path)}")
    print(f"DASHBOARD_SHA256={sha(dash_path)}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: patch_brotoculateur_c6_provenance.py <brotoculateur-root>")
    patch(Path(sys.argv[1]).resolve())
