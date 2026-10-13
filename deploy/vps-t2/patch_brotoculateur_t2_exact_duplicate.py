from __future__ import annotations

import hashlib
import shutil
import sys
from pathlib import Path

PRE = {
    "orchestrator.py": "453c06a2064e743e08a042ced8dc7406492ab323c664dea16b1f6de1aaa9f526",
    "dashboard.py": "c54737bfa9213d1625f8134a7588ee37a99712b44e7aa37a2246743c5c344355",
    "t1_family.py": "e68643e72c4c0551b3d7187fde05f5d3a37c45b7e5f0d30cd750869378a32320",
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
    source_t2 = Path(__file__).with_name("t2_exact_duplicate.py")

    if t2.exists() and "BRUTUS_T2_EXACT_DUPLICATE_V1" in t2.read_text(encoding="utf-8-sig"):
        if "def t2_status(" in orch.read_text(encoding="utf-8-sig"):
            print("T2_PATCH=ALREADY_APPLIED")
            for p in (t1, t2, orch, dash):
                print(f"{p.name.upper()}_SHA256={sha(p)}")
            return

    for name, expected in PRE.items():
        path = pkg / name
        got = sha(path)
        if got != expected:
            raise RuntimeError(f"pre-hash mismatch {name}: {got} != {expected}")

    shutil.copyfile(source_t2, t2)

    text = orch.read_text(encoding="utf-8")
    text = replace_once(text,
        "from .t1_family import T1FamilyClassifier\n",
        "from .t1_family import T1FamilyClassifier\nfrom .t2_exact_duplicate import T2ExactDuplicate\n",
        "orch import")
    text = replace_once(text,
        "        t1_family: T1FamilyClassifier | None = None,\n",
        "        t1_family: T1FamilyClassifier | None = None,\n        t2_duplicate: T2ExactDuplicate | None = None,\n",
        "orch arg")
    text = replace_once(text,
        "        self.t1_family = t1_family\n",
        "        self.t1_family = t1_family\n        self.t2_duplicate = t2_duplicate\n",
        "orch assign")
    text = replace_once(text,
        '        self.t1_requested = os.getenv("BROTO_T1_ENABLED", "0").strip().lower() in {"1", "true", "yes", "on"}\n        self.t1_enabled = bool(self.t1_requested and self.c7_enabled and self.t1_family is not None)\n',
        '        self.t1_requested = os.getenv("BROTO_T1_ENABLED", "0").strip().lower() in {"1", "true", "yes", "on"}\n        self.t1_enabled = bool(self.t1_requested and self.c7_enabled and self.t1_family is not None)\n        self.t2_requested = os.getenv("BROTO_T2_ENABLED", "0").strip().lower() in {"1", "true", "yes", "on"}\n        self.t2_enabled = bool(self.t2_requested and self.t1_enabled and self.t2_duplicate is not None)\n',
        "orch flags")
    old = '''            if self.t1_enabled and self.t1_family is not None:\n                self.t1_family.observe(\n                    packet,\n                    fingerprint,\n                    c7_route=c7_route or "OBSERVE_ONLY",\n                )\n'''
    new = '''            t1_family_name = None\n            if self.t1_enabled and self.t1_family is not None:\n                t1_family_name = self.t1_family.observe(\n                    packet,\n                    fingerprint,\n                    c7_route=c7_route or "OBSERVE_ONLY",\n                )\n            if self.t2_enabled and self.t2_duplicate is not None:\n                self.t2_duplicate.observe(\n                    packet,\n                    fingerprint,\n                    family=t1_family_name or "OTHER",\n                )\n'''
    text = replace_once(text, old, new, "orch observe")
    marker = "    def t1_status(self) -> dict[str, object]:\n"
    method = '''    def t2_status(self) -> dict[str, object]:\n        if self.t2_duplicate is None:\n            return {\n                "mode": "BRUTUS_T2_EXACT_DUPLICATE_V1",\n                "enabled": False,\n                "requested": self.t2_requested,\n                "authority": "SHADOW_ONLY",\n                "observations": 0,\n                "deduplication_applied": False,\n                "packets_collapsed": 0,\n                "controls_routing": False,\n                "controls_scheduling": False,\n                "compute_skips": 0,\n                "proof_promotion": False,\n            }\n        current = dict(self.t2_duplicate.status())\n        current["enabled"] = self.t2_enabled\n        current["requested"] = self.t2_requested\n        current["t1_required"] = True\n        current["t1_enabled"] = self.t1_enabled\n        return current\n\n'''
    text = replace_once(text, marker, method + marker, "orch t2 status")
    orch.write_text(text, encoding="utf-8", newline="\n")

    text = dash.read_text(encoding="utf-8")
    text = replace_once(text,
        "from .t1_family import T1FamilyClassifier\n",
        "from .t1_family import T1FamilyClassifier\nfrom .t2_exact_duplicate import T2ExactDuplicate\n",
        "dash import")
    text = replace_once(text,
        "        self.t1_family = T1FamilyClassifier()\n        self._lock = threading.RLock()\n",
        "        self.t1_family = T1FamilyClassifier()\n        self.t2_duplicate = T2ExactDuplicate()\n        self._lock = threading.RLock()\n",
        "dash init")
    text = replace_once(text,
        "            t1_family=self.t1_family,\n",
        "            t1_family=self.t1_family,\n            t2_duplicate=self.t2_duplicate,\n",
        "dash runner")
    text = replace_once(text,
        "            self.t1_family = T1FamilyClassifier()\n            self._session_started_monotonic = None\n",
        "            self.t1_family = T1FamilyClassifier()\n            self.t2_duplicate = T2ExactDuplicate()\n            self._session_started_monotonic = None\n",
        "dash reset")
    text = replace_once(text,
        '            "t1_family": self._runner.t1_status(),\n',
        '            "t1_family": self._runner.t1_status(),\n            "t2_exact_duplicate": self._runner.t2_status(),\n',
        "dash status")
    dash.write_text(text, encoding="utf-8", newline="\n")

    print("T2_PATCH=PASS")
    for p in (t1, t2, orch, dash):
        print(f"{p.name.upper()}_SHA256={sha(p)}")


if __name__ == "__main__":
    main()
