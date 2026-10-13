from __future__ import annotations

import hashlib
import shutil
import sys
from pathlib import Path

PRE = {
    "orchestrator.py": "1dcf3c224e0a8cdfbf819a6ce97a8f5e3c19757a0a310444c1d477418f2c4012",
    "dashboard.py": "6eb9c68e143f6488c15d8d96861c59980555c124895b2128f3676a0d56b9d44b",
    "t1_family.py": "e68643e72c4c0551b3d7187fde05f5d3a37c45b7e5f0d30cd750869378a32320",
    "t2_exact_duplicate.py": "52b9a8a39480e0e5201d524eec330effdabb1642988fdeefebb47d00c2421e12",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly 1 occurrence, got {count}")
    return text.replace(old, new, 1)


def main() -> None:
    root = Path(sys.argv[1]).resolve()
    pkg = root / "src" / "brotoculateur"
    orch = pkg / "orchestrator.py"
    dash = pkg / "dashboard.py"
    t1 = pkg / "t1_family.py"
    t2 = pkg / "t2_exact_duplicate.py"
    t3 = pkg / "t3_neighborhood.py"
    source_t3 = Path(__file__).with_name("t3_neighborhood.py")

    if t3.exists() and "BRUTUS_T3_SEMANTIC_NEIGHBORHOOD_V1" in t3.read_text(encoding="utf-8-sig"):
        if "def t3_status(" in orch.read_text(encoding="utf-8-sig"):
            print("T3_PATCH=ALREADY_APPLIED")
            for p in (t1, t2, t3, orch, dash):
                print(f"{p.name.upper()}_SHA256={sha(p)}")
            return

    for name, expected in PRE.items():
        path = pkg / name
        got = sha(path)
        if got != expected:
            raise RuntimeError(f"pre-hash mismatch {name}: {got} != {expected}")

    shutil.copyfile(source_t3, t3)

    text = orch.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "from .t2_exact_duplicate import T2ExactDuplicate\n",
        "from .t2_exact_duplicate import T2ExactDuplicate\nfrom .t3_neighborhood import T3SemanticNeighborhood\n",
        "orch import",
    )
    text = replace_once(
        text,
        "        t2_duplicate: T2ExactDuplicate | None = None,\n",
        "        t2_duplicate: T2ExactDuplicate | None = None,\n        t3_neighborhood: T3SemanticNeighborhood | None = None,\n",
        "orch arg",
    )
    text = replace_once(
        text,
        "        self.t2_duplicate = t2_duplicate\n",
        "        self.t2_duplicate = t2_duplicate\n        self.t3_neighborhood = t3_neighborhood\n",
        "orch assign",
    )
    text = replace_once(
        text,
        '        self.t2_requested = os.getenv("BROTO_T2_ENABLED", "0").strip().lower() in {"1", "true", "yes", "on"}\n        self.t2_enabled = bool(self.t2_requested and self.t1_enabled and self.t2_duplicate is not None)\n',
        '        self.t2_requested = os.getenv("BROTO_T2_ENABLED", "0").strip().lower() in {"1", "true", "yes", "on"}\n        self.t2_enabled = bool(self.t2_requested and self.t1_enabled and self.t2_duplicate is not None)\n        self.t3_requested = os.getenv("BROTO_T3_ENABLED", "0").strip().lower() in {"1", "true", "yes", "on"}\n        self.t3_enabled = bool(self.t3_requested and self.t2_enabled and self.t3_neighborhood is not None)\n',
        "orch flags",
    )
    old = '''            if self.t2_enabled and self.t2_duplicate is not None:\n                self.t2_duplicate.observe(\n                    packet,\n                    fingerprint,\n                    family=t1_family_name or "OTHER",\n                )\n'''
    new = '''            t2_event = "T2_DISABLED"\n            if self.t2_enabled and self.t2_duplicate is not None:\n                t2_event = self.t2_duplicate.observe(\n                    packet,\n                    fingerprint,\n                    family=t1_family_name or "OTHER",\n                )\n            if self.t3_enabled and self.t3_neighborhood is not None:\n                self.t3_neighborhood.observe(\n                    packet,\n                    fingerprint,\n                    family=t1_family_name or "OTHER",\n                    t2_event=t2_event,\n                )\n'''
    text = replace_once(text, old, new, "orch observe")
    marker = "    def t2_status(self) -> dict[str, object]:\n"
    method = '''    def t3_status(self) -> dict[str, object]:\n        if self.t3_neighborhood is None:\n            return {\n                "mode": "BRUTUS_T3_SEMANTIC_NEIGHBORHOOD_V1",\n                "enabled": False,\n                "requested": self.t3_requested,\n                "authority": "SHADOW_ONLY",\n                "metric": "PACKET_SEMANTICS_NOT_HASH_DISTANCE",\n                "observations": 0,\n                "hash_distance_used": False,\n                "scientific_similarity_claim": False,\n                "controls_routing": False,\n                "controls_scheduling": False,\n                "compute_skips": 0,\n                "proof_promotion": False,\n            }\n        current = dict(self.t3_neighborhood.status())\n        current["enabled"] = self.t3_enabled\n        current["requested"] = self.t3_requested\n        current["t2_required"] = True\n        current["t2_enabled"] = self.t2_enabled\n        return current\n\n'''
    text = replace_once(text, marker, method + marker, "orch t3 status")
    orch.write_text(text, encoding="utf-8", newline="\n")

    text = dash.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "from .t2_exact_duplicate import T2ExactDuplicate\n",
        "from .t2_exact_duplicate import T2ExactDuplicate\nfrom .t3_neighborhood import T3SemanticNeighborhood\n",
        "dash import",
    )
    text = replace_once(
        text,
        "        self.t2_duplicate = T2ExactDuplicate()\n        self._lock = threading.RLock()\n",
        "        self.t2_duplicate = T2ExactDuplicate()\n        self.t3_neighborhood = T3SemanticNeighborhood()\n        self._lock = threading.RLock()\n",
        "dash init",
    )
    text = replace_once(
        text,
        "            t2_duplicate=self.t2_duplicate,\n",
        "            t2_duplicate=self.t2_duplicate,\n            t3_neighborhood=self.t3_neighborhood,\n",
        "dash runner",
    )
    text = replace_once(
        text,
        "            self.t2_duplicate = T2ExactDuplicate()\n            self._session_started_monotonic = None\n",
        "            self.t2_duplicate = T2ExactDuplicate()\n            self.t3_neighborhood = T3SemanticNeighborhood()\n            self._session_started_monotonic = None\n",
        "dash reset",
    )
    text = replace_once(
        text,
        '            "t2_exact_duplicate": self._runner.t2_status(),\n',
        '            "t2_exact_duplicate": self._runner.t2_status(),\n            "t3_neighborhood": self._runner.t3_status(),\n',
        "dash status",
    )
    dash.write_text(text, encoding="utf-8", newline="\n")

    print("T3_PATCH=PASS")
    for p in (t1, t2, t3, orch, dash):
        print(f"{p.name.upper()}_SHA256={sha(p)}")


if __name__ == "__main__":
    main()
