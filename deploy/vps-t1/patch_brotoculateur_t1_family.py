from __future__ import annotations

import hashlib
import shutil
import sys
from pathlib import Path

PRE = {
    "orchestrator.py": "e22f0f8dc54765243f2e62a20c2dc841efa6d6bb860a3f0b48fa8f67b7cfb7ee",
    "dashboard.py": "a146aa18a5ff01c82a879e8810a9a58b359709dd469cb1aa94c571c44224ab6e",
    "c7_router.py": "9290fd8db6a34b0df3e94ad0281963ee3b7c5531fa955eb946e1aa10675c30f6",
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
    c7 = pkg / "c7_router.py"
    t1 = pkg / "t1_family.py"
    source_t1 = Path(__file__).with_name("t1_family.py")

    if t1.exists() and "BRUTUS_T1_FAMILY_V1" in t1.read_text(encoding="utf-8-sig"):
        if "def t1_status(" in orch.read_text(encoding="utf-8-sig"):
            print("T1_PATCH=ALREADY_APPLIED")
            for p in (c7, t1, orch, dash):
                print(f"{p.name.upper()}_SHA256={sha(p)}")
            return

    for name, expected in PRE.items():
        path = pkg / name
        got = sha(path)
        if got != expected:
            raise RuntimeError(f"pre-hash mismatch {name}: {got} != {expected}")

    shutil.copyfile(source_t1, t1)

    text = orch.read_text(encoding="utf-8")
    text = replace_once(text,
        "from .c7_router import C7ShadowRouter\n",
        "from .c7_router import C7ShadowRouter\nfrom .t1_family import T1FamilyClassifier\n",
        "orch import")
    text = replace_once(text,
        "        c7_router: C7ShadowRouter | None = None,\n",
        "        c7_router: C7ShadowRouter | None = None,\n        t1_family: T1FamilyClassifier | None = None,\n",
        "orch arg")
    text = replace_once(text,
        "        self.c7_router = c7_router\n",
        "        self.c7_router = c7_router\n        self.t1_family = t1_family\n",
        "orch assign")
    text = replace_once(text,
        '        self.c7_requested = os.getenv("BROTO_C7_ENABLED", "0").strip().lower() in {"1", "true", "yes", "on"}\n        self.c7_enabled = bool(self.c7_requested and self.c6_enabled and self.c7_router is not None)\n',
        '        self.c7_requested = os.getenv("BROTO_C7_ENABLED", "0").strip().lower() in {"1", "true", "yes", "on"}\n        self.c7_enabled = bool(self.c7_requested and self.c6_enabled and self.c7_router is not None)\n        self.t1_requested = os.getenv("BROTO_T1_ENABLED", "0").strip().lower() in {"1", "true", "yes", "on"}\n        self.t1_enabled = bool(self.t1_requested and self.c7_enabled and self.t1_family is not None)\n',
        "orch flags")
    old = '''            if self.c7_enabled and self.c7_router is not None:\n                self.c7_router.observe(\n                    fingerprint,\n                    c3_hit=c3_hit,\n                    c3_retained=c3_retained,\n                    c5_class=c5_class,\n                    c6_summary=c6_summary,\n                )\n'''
    new = '''            c7_route = None\n            if self.c7_enabled and self.c7_router is not None:\n                c7_route = self.c7_router.observe(\n                    fingerprint,\n                    c3_hit=c3_hit,\n                    c3_retained=c3_retained,\n                    c5_class=c5_class,\n                    c6_summary=c6_summary,\n                )\n            if self.t1_enabled and self.t1_family is not None:\n                self.t1_family.observe(\n                    packet,\n                    fingerprint,\n                    c7_route=c7_route or "OBSERVE_ONLY",\n                )\n'''
    text = replace_once(text, old, new, "orch observe")
    marker = "    def c7_status(self) -> dict[str, object]:\n"
    method = '''    def t1_status(self) -> dict[str, object]:\n        if self.t1_family is None:\n            return {\n                "mode": "BRUTUS_T1_FAMILY_V1",\n                "enabled": False,\n                "requested": self.t1_requested,\n                "authority": "SHADOW_ONLY",\n                "observations": 0,\n                "scientific_taxonomy_claim": False,\n                "controls_routing": False,\n                "controls_scheduling": False,\n                "actual_routes_applied": 0,\n                "compute_skips": 0,\n                "proof_promotion": False,\n            }\n        current = dict(self.t1_family.status())\n        current["enabled"] = self.t1_enabled\n        current["requested"] = self.t1_requested\n        current["c7_required"] = True\n        current["c7_enabled"] = self.c7_enabled\n        return current\n\n'''
    text = replace_once(text, marker, method + marker, "orch t1 status")
    orch.write_text(text, encoding="utf-8", newline="\n")

    text = dash.read_text(encoding="utf-8")
    text = replace_once(text,
        "from .c7_router import C7ShadowRouter\n",
        "from .c7_router import C7ShadowRouter\nfrom .t1_family import T1FamilyClassifier\n",
        "dash import")
    text = replace_once(text,
        "        self.c7_router = C7ShadowRouter()\n        self._lock = threading.RLock()\n",
        "        self.c7_router = C7ShadowRouter()\n        self.t1_family = T1FamilyClassifier()\n        self._lock = threading.RLock()\n",
        "dash init")
    text = replace_once(text,
        "            c7_router=self.c7_router,\n",
        "            c7_router=self.c7_router,\n            t1_family=self.t1_family,\n",
        "dash runner")
    text = replace_once(text,
        "            self.c7_router = C7ShadowRouter()\n            self._session_started_monotonic = None\n",
        "            self.c7_router = C7ShadowRouter()\n            self.t1_family = T1FamilyClassifier()\n            self._session_started_monotonic = None\n",
        "dash reset")
    text = replace_once(text,
        '            "c7_router": self._runner.c7_status(),\n',
        '            "c7_router": self._runner.c7_status(),\n            "t1_family": self._runner.t1_status(),\n',
        "dash status")
    dash.write_text(text, encoding="utf-8", newline="\n")

    print("T1_PATCH=PASS")
    for p in (c7, t1, orch, dash):
        print(f"{p.name.upper()}_SHA256={sha(p)}")


if __name__ == "__main__":
    main()
