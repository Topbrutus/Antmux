from __future__ import annotations

import hashlib
import shutil
import sys
from pathlib import Path

PRE = {
    "orchestrator.py": "ad079319b4dfc3c6d0f3994d2638a81ae686015bae9b7aa3a9b5052df69afa74",
    "dashboard.py": "5af116fe28120ee9c463a4a980751101294fc51e086c54594482b46f37dc7296",
    "c6_provenance.py": "e8aa78c5834bf21a97eb11e7ce0b80a65b405a82282837485f4f23fffb2b0d84",
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
    c6 = pkg / "c6_provenance.py"
    c7 = pkg / "c7_router.py"
    source_c7 = Path(__file__).with_name("c7_router.py")

    if c7.exists() and "BRUTUS_C7_SHADOW_ROUTER_V1" in c7.read_text(encoding="utf-8-sig"):
        if "def c7_status(" in orch.read_text(encoding="utf-8-sig"):
            print("C7_PATCH=ALREADY_APPLIED")
            for p in (c6, c7, orch, dash): print(f"{p.name.upper()}_SHA256={sha(p)}")
            return

    for name, expected in PRE.items():
        path = pkg / name
        got = sha(path)
        if got != expected:
            raise RuntimeError(f"pre-hash mismatch {name}: {got} != {expected}")

    shutil.copyfile(source_c7, c7)

    t = c6.read_text(encoding="utf-8-sig")
    marker = "    def status(self) -> dict[str, Any]:\n"
    method = '''    def target_summary(self, z_id: str | None) -> dict[str, Any] | None:\n        if not z_id:\n            return None\n        rec = self._records.get(str(z_id))\n        if rec is None:\n            return None\n        return {\n            "z_id": str(z_id),\n            "observations": rec.observations,\n            "distinct_c2": len(rec.fingerprints),\n            "distinct_paths": len(rec.paths),\n            "distinct_formula_chains": len(rec.formulas),\n            "distinct_parents": len(rec.parents),\n            "distinct_origins": len(rec.origins),\n            "operational_independence_candidate": rec.independence_candidate,\n        }\n\n'''
    t = replace_once(t, marker, method + marker, "c6 target_summary")
    c6.write_text(t, encoding="utf-8", newline="\n")

    t = orch.read_text(encoding="utf-8")
    t = replace_once(t, "from .c6_provenance import C6Provenance\n", "from .c6_provenance import C6Provenance\nfrom .c7_router import C7ShadowRouter\n", "orch import")
    t = replace_once(t, "        c6_provenance: C6Provenance | None = None,\n", "        c6_provenance: C6Provenance | None = None,\n        c7_router: C7ShadowRouter | None = None,\n", "orch arg")
    t = replace_once(t, "        self.c6_provenance = c6_provenance\n", "        self.c6_provenance = c6_provenance\n        self.c7_router = c7_router\n", "orch assign")
    t = replace_once(t,
        '        self.c6_requested = os.getenv("BROTO_C6_ENABLED", "0").strip().lower() in {"1", "true", "yes", "on"}\n        self.c6_enabled = bool(self.c6_requested and self.c5_enabled and self.c6_provenance is not None)\n',
        '        self.c6_requested = os.getenv("BROTO_C6_ENABLED", "0").strip().lower() in {"1", "true", "yes", "on"}\n        self.c6_enabled = bool(self.c6_requested and self.c5_enabled and self.c6_provenance is not None)\n        self.c7_requested = os.getenv("BROTO_C7_ENABLED", "0").strip().lower() in {"1", "true", "yes", "on"}\n        self.c7_enabled = bool(self.c7_requested and self.c6_enabled and self.c7_router is not None)\n',
        "orch flags")
    old = '''            if self.c6_enabled and self.c6_provenance is not None:\n                self.c6_provenance.observe(\n                    packet,\n                    fingerprint,\n                    c3_retained=c3_retained,\n                    c5_class=c5_class,\n                )\n'''
    new = '''            c6_summary = None\n            if self.c6_enabled and self.c6_provenance is not None:\n                self.c6_provenance.observe(\n                    packet,\n                    fingerprint,\n                    c3_retained=c3_retained,\n                    c5_class=c5_class,\n                )\n                c6_summary = self.c6_provenance.target_summary(packet.z_id)\n            if self.c7_enabled and self.c7_router is not None:\n                self.c7_router.observe(\n                    fingerprint,\n                    c3_hit=c3_hit,\n                    c3_retained=c3_retained,\n                    c5_class=c5_class,\n                    c6_summary=c6_summary,\n                )\n'''
    t = replace_once(t, old, new, "orch observe")
    marker = "    def c6_status(self) -> dict[str, object]:\n"
    method = '''    def c7_status(self) -> dict[str, object]:\n        if self.c7_router is None:\n            return {\n                "mode": "BRUTUS_C7_SHADOW_ROUTER_V1",\n                "enabled": False,\n                "requested": self.c7_requested,\n                "authority": "SHADOW_ONLY",\n                "observations": 0,\n                "controls_scheduling": False,\n                "actual_routes_applied": 0,\n                "compute_skips": 0,\n                "proof_promotion": False,\n            }\n        current = dict(self.c7_router.status())\n        current["enabled"] = self.c7_enabled\n        current["requested"] = self.c7_requested\n        current["c6_required"] = True\n        current["c6_enabled"] = self.c6_enabled\n        return current\n\n'''
    t = replace_once(t, marker, method + marker, "orch c7 status")
    orch.write_text(t, encoding="utf-8", newline="\n")

    t = dash.read_text(encoding="utf-8")
    t = replace_once(t, "from .c6_provenance import C6Provenance\n", "from .c6_provenance import C6Provenance\nfrom .c7_router import C7ShadowRouter\n", "dash import")
    t = replace_once(t, "        self.c5_rarity = C5StructuralRarity()\n        self.c6_provenance = C6Provenance()\n", "        self.c5_rarity = C5StructuralRarity()\n        self.c6_provenance = C6Provenance()\n        self.c7_router = C7ShadowRouter()\n", "dash init")
    t = replace_once(t, "            c6_provenance=self.c6_provenance,\n", "            c6_provenance=self.c6_provenance,\n            c7_router=self.c7_router,\n", "dash runner")
    t = replace_once(t, "            self.c5_rarity = C5StructuralRarity()\n            self.c6_provenance = C6Provenance()\n", "            self.c5_rarity = C5StructuralRarity()\n            self.c6_provenance = C6Provenance()\n            self.c7_router = C7ShadowRouter()\n", "dash reset")
    t = replace_once(t, '            "c6_provenance": self._runner.c6_status(),\n', '            "c6_provenance": self._runner.c6_status(),\n            "c7_router": self._runner.c7_status(),\n', "dash status")
    dash.write_text(t, encoding="utf-8", newline="\n")

    print("C7_PATCH=PASS")
    for p in (c6, c7, orch, dash): print(f"{p.name.upper()}_SHA256={sha(p)}")


if __name__ == "__main__":
    main()

