from __future__ import annotations

import hashlib
import shutil
import sys
from pathlib import Path

PRE = {
    "orchestrator.py": "49585752a6bba0c830193be10743a7f44388cc295183478c1f8e7b8f3df8f862",
    "dashboard.py": "943f075765282b448c8f3d01cb3d03e54ae5d5d84bfd18dd92d79fd6b7f7f131",
    "t3_neighborhood.py": "f4144e566508d6bd0e17279690d3ff9edd72e85a93d5a0d8dead2beeab1310d6",
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
    t3 = pkg / "t3_neighborhood.py"
    t2 = pkg / "t2_exact_duplicate.py"
    t4 = pkg / "t4_convergence.py"
    source_t4 = Path(__file__).with_name("t4_convergence.py")

    if t4.exists() and "BRUTUS_T4_CONVERGENCE_V1" in t4.read_text(encoding="utf-8-sig"):
        if "def t4_status(" in orch.read_text(encoding="utf-8-sig"):
            print("T4_PATCH=ALREADY_APPLIED")
            for p in (t2, t3, t4, orch, dash):
                print(f"{p.name.upper()}_SHA256={sha(p)}")
            return

    for name, expected in PRE.items():
        path = pkg / name
        got = sha(path)
        if got != expected:
            raise RuntimeError(f"pre-hash mismatch {name}: {got} != {expected}")

    shutil.copyfile(source_t4, t4)

    text = orch.read_text(encoding="utf-8")
    text = replace_once(text,
        "from .t3_neighborhood import T3SemanticNeighborhood\n",
        "from .t3_neighborhood import T3SemanticNeighborhood\nfrom .t4_convergence import T4Convergence\n",
        "orch import")
    text = replace_once(text,
        "        t3_neighborhood: T3SemanticNeighborhood | None = None,\n",
        "        t3_neighborhood: T3SemanticNeighborhood | None = None,\n        t4_convergence: T4Convergence | None = None,\n",
        "orch arg")
    text = replace_once(text,
        "        self.t3_neighborhood = t3_neighborhood\n",
        "        self.t3_neighborhood = t3_neighborhood\n        self.t4_convergence = t4_convergence\n",
        "orch assign")
    text = replace_once(text,
        '        self.t3_requested = os.getenv("BROTO_T3_ENABLED", "0").strip().lower() in {"1", "true", "yes", "on"}\n        self.t3_enabled = bool(self.t3_requested and self.t2_enabled and self.t3_neighborhood is not None)\n',
        '        self.t3_requested = os.getenv("BROTO_T3_ENABLED", "0").strip().lower() in {"1", "true", "yes", "on"}\n        self.t3_enabled = bool(self.t3_requested and self.t2_enabled and self.t3_neighborhood is not None)\n        self.t4_requested = os.getenv("BROTO_T4_ENABLED", "0").strip().lower() in {"1", "true", "yes", "on"}\n        self.t4_enabled = bool(self.t4_requested and self.t3_enabled and self.t4_convergence is not None)\n',
        "orch flags")
    old = '''            if self.t3_enabled and self.t3_neighborhood is not None:\n                self.t3_neighborhood.observe(\n                    packet,\n                    fingerprint,\n                    family=t1_family_name or "OTHER",\n                    t2_event=t2_event,\n                )\n'''
    new = '''            t3_class = "T3_DISABLED"\n            if self.t3_enabled and self.t3_neighborhood is not None:\n                t3_class = self.t3_neighborhood.observe(\n                    packet,\n                    fingerprint,\n                    family=t1_family_name or "OTHER",\n                    t2_event=t2_event,\n                )\n            if self.t4_enabled and self.t4_convergence is not None:\n                self.t4_convergence.observe(\n                    packet,\n                    fingerprint,\n                    family=t1_family_name or "OTHER",\n                    t2_event=t2_event,\n                    t3_class=t3_class,\n                )\n'''
    text = replace_once(text, old, new, "orch observe")
    marker = "    def t3_status(self) -> dict[str, object]:\n"
    method = '''    def t4_status(self) -> dict[str, object]:\n        if self.t4_convergence is None:\n            return {\n                "mode": "BRUTUS_T4_CONVERGENCE_V1",\n                "enabled": False,\n                "requested": self.t4_requested,\n                "authority": "SHADOW_ONLY",\n                "observations": 0,\n                "exact_duplicate_counts_as_convergence": False,\n                "scientific_convergence_claim": False,\n                "controls_scheduling": False,\n                "compute_skips": 0,\n                "proof_promotion": False,\n            }\n        current = dict(self.t4_convergence.status())\n        current["enabled"] = self.t4_enabled\n        current["requested"] = self.t4_requested\n        current["t3_required"] = True\n        current["t3_enabled"] = self.t3_enabled\n        current["t2_required"] = True\n        current["t2_enabled"] = self.t2_enabled\n        return current\n\n'''
    text = replace_once(text, marker, method + marker, "orch t4 status")
    orch.write_text(text, encoding="utf-8", newline="\n")

    text = dash.read_text(encoding="utf-8")
    text = replace_once(text,
        "from .t3_neighborhood import T3SemanticNeighborhood\n",
        "from .t3_neighborhood import T3SemanticNeighborhood\nfrom .t4_convergence import T4Convergence\n",
        "dash import")
    text = replace_once(text,
        "        self.t3_neighborhood = T3SemanticNeighborhood()\n        self._lock = threading.RLock()\n",
        "        self.t3_neighborhood = T3SemanticNeighborhood()\n        self.t4_convergence = T4Convergence()\n        self._lock = threading.RLock()\n",
        "dash init")
    text = replace_once(text,
        "            t3_neighborhood=self.t3_neighborhood,\n",
        "            t3_neighborhood=self.t3_neighborhood,\n            t4_convergence=self.t4_convergence,\n",
        "dash runner")
    text = replace_once(text,
        "            self.t3_neighborhood = T3SemanticNeighborhood()\n            self._session_started_monotonic = None\n",
        "            self.t3_neighborhood = T3SemanticNeighborhood()\n            self.t4_convergence = T4Convergence()\n            self._session_started_monotonic = None\n",
        "dash reset")
    text = replace_once(text,
        '            "t3_neighborhood": self._runner.t3_status(),\n',
        '            "t3_neighborhood": self._runner.t3_status(),\n            "t4_convergence": self._runner.t4_status(),\n',
        "dash status")
    dash.write_text(text, encoding="utf-8", newline="\n")

    print("T4_PATCH=PASS")
    for p in (t2, t3, t4, orch, dash):
        print(f"{p.name.upper()}_SHA256={sha(p)}")


if __name__ == "__main__":
    main()
