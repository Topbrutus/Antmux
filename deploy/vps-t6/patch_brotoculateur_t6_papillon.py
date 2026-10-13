from __future__ import annotations

import hashlib
import shutil
import sys
from pathlib import Path

PRE = {
    "papillon_engine.py": "ca45f4ebd9ac4efc241626b9322c2e6d57870873d27982f287d99a9f773871ef",
    "t5_independence.py": "22d71b4d3d52093ee10aa78a5ea0f620abc4c5c06e5bddfe6ddf09b9a638a3c6",
    "orchestrator.py": "461a18418bf2abc0c4f434287e5783d1e29bfaf67d9837d9e388b8a6f1b8fb7c",
    "dashboard.py": "dc7d1fe9212a30f40371381b8abfcca91d5ea490227859a4759412d72ca59c10",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected 1 occurrence, found {count}")
    return text.replace(old, new, 1)


def write_lf(path: Path, text: str) -> None:
    path.write_text(text.replace("\r\n", "\n"), encoding="utf-8", newline="\n")


def main(root: Path) -> None:
    pkg = root / "src" / "brotoculateur"
    src_t6 = Path(__file__).with_name("t6_papillon.py")
    if not pkg.is_dir():
        raise RuntimeError(f"missing package: {pkg}")

    t6 = pkg / "t6_papillon.py"
    already = t6.exists() and "BRUTUS_T6_PAPILLON_AFFINITY_V1" in t6.read_text(encoding="utf-8")
    if already:
        print("T6_PATCH=ALREADY_APPLIED")
    else:
        for name, expected in PRE.items():
            got = sha(pkg / name)
            if got != expected:
                raise RuntimeError(f"PRE hash mismatch {name}: {got} != {expected}")
        shutil.copyfile(src_t6, t6)

        pap = (pkg / "papillon_engine.py").read_text(encoding="utf-8")
        pap = replace_once(
            pap,
            "        return acc % self.shard_count\n\n    @staticmethod\n    def _packet",
            "        return acc % self.shard_count\n\n    def shard_index(self, formula_id: str, value: int) -> int:\n        \"\"\"Pure public view of the exact live Papillon shard function.\"\"\"\n        return self._index(str(formula_id), int(value))\n\n    @staticmethod\n    def _packet",
            "papillon public shard index",
        )
        write_lf(pkg / "papillon_engine.py", pap)

        orch = (pkg / "orchestrator.py").read_text(encoding="utf-8")
        orch = replace_once(orch, "from .t5_independence import T5OperationalIndependence\n", "from .t5_independence import T5OperationalIndependence\nfrom .t6_papillon import T6PapillonAffinity\n", "orch import")
        orch = replace_once(orch, "        t5_independence: T5OperationalIndependence | None = None,\n    ) -> None:", "        t5_independence: T5OperationalIndependence | None = None,\n        t6_papillon: T6PapillonAffinity | None = None,\n    ) -> None:", "orch arg")
        orch = replace_once(orch, "        self.t5_independence = t5_independence\n        self.spec = spec or ExperimentSpec()", "        self.t5_independence = t5_independence\n        self.t6_papillon = t6_papillon\n        self.spec = spec or ExperimentSpec()", "orch attr")
        orch = replace_once(orch, "        self.t5_enabled = bool(self.t5_requested and self.t4_enabled and self.t5_independence is not None)\n        self.c2_roots", "        self.t5_enabled = bool(self.t5_requested and self.t4_enabled and self.t5_independence is not None)\n        self.t6_requested = os.getenv(\"BROTO_T6_ENABLED\", \"0\").strip().lower() in {\"1\", \"true\", \"yes\", \"on\"}\n        self.t6_enabled = bool(self.t6_requested and self.t5_enabled and self.t6_papillon is not None and self.papillon is not None)\n        self.c2_roots", "orch enable")
        orch = replace_once(
            orch,
            "            if self.t5_enabled and self.t5_independence is not None:\n                self.t5_independence.observe(\n                    packet,\n                    fingerprint,\n                    t4_event=t4_event,\n                    t4_summary=t4_summary,\n                )\n        return fingerprint",
            "            t5_tier = \"T5_DISABLED\"\n            if self.t5_enabled and self.t5_independence is not None:\n                t5_tier = self.t5_independence.observe(\n                    packet,\n                    fingerprint,\n                    t4_event=t4_event,\n                    t4_summary=t4_summary,\n                )\n            if self.t6_enabled and self.t6_papillon is not None and self.papillon is not None:\n                self.t6_papillon.observe(\n                    packet,\n                    fingerprint,\n                    t5_tier=t5_tier,\n                    papillon=self.papillon,\n                )\n        return fingerprint",
            "orch observe",
        )
        orch = replace_once(
            orch,
            "    def t5_status(self) -> dict[str, object]:\n",
            "    def t6_status(self) -> dict[str, object]:\n        if self.t6_papillon is None:\n            return {\n                \"mode\": \"BRUTUS_T6_PAPILLON_AFFINITY_V1\",\n                \"enabled\": False,\n                \"requested\": self.t6_requested,\n                \"authority\": \"SHADOW_ONLY\",\n                \"observations\": 0,\n                \"actual_papillon_routes_applied\": 0,\n                \"controls_papillon\": False,\n                \"compute_skips\": 0,\n                \"proof_promotion\": False,\n            }\n        current = dict(self.t6_papillon.status())\n        current[\"enabled\"] = self.t6_enabled\n        current[\"requested\"] = self.t6_requested\n        current[\"t5_required\"] = True\n        current[\"t5_enabled\"] = self.t5_enabled\n        current[\"papillon_enabled\"] = self.papillon is not None\n        return current\n\n    def t5_status(self) -> dict[str, object]:\n",
            "orch status",
        )
        write_lf(pkg / "orchestrator.py", orch)

        dash = (pkg / "dashboard.py").read_text(encoding="utf-8")
        dash = replace_once(dash, "from .t5_independence import T5OperationalIndependence\n", "from .t5_independence import T5OperationalIndependence\nfrom .t6_papillon import T6PapillonAffinity\n", "dash import")
        dash = replace_once(dash, "        self.t4_convergence = T4Convergence()\n        self.t5_independence = T5OperationalIndependence()\n        self._lock", "        self.t4_convergence = T4Convergence()\n        self.t5_independence = T5OperationalIndependence()\n        self.t6_papillon = T6PapillonAffinity()\n        self._lock", "dash init")
        dash = replace_once(dash, "            t4_convergence=self.t4_convergence,\n            t5_independence=self.t5_independence,\n        )", "            t4_convergence=self.t4_convergence,\n            t5_independence=self.t5_independence,\n            t6_papillon=self.t6_papillon,\n        )", "dash runner")
        dash = replace_once(dash, "            self.t4_convergence = T4Convergence()\n            self.t5_independence = T5OperationalIndependence()\n            self._session_started_monotonic", "            self.t4_convergence = T4Convergence()\n            self.t5_independence = T5OperationalIndependence()\n            self.t6_papillon = T6PapillonAffinity()\n            self._session_started_monotonic", "dash reset")
        dash = replace_once(dash, "            \"t5_independence\": self._runner.t5_status(),\n            \"hierarchical_rarity\":", "            \"t5_independence\": self._runner.t5_status(),\n            \"t6_papillon\": self._runner.t6_status(),\n            \"hierarchical_rarity\":", "dash status")
        write_lf(pkg / "dashboard.py", dash)
        print("T6_PATCH=PASS")

    for name in ("papillon_engine.py", "t5_independence.py", "t6_papillon.py", "orchestrator.py", "dashboard.py"):
        print(f"{name.upper()}_SHA256={sha(pkg / name)}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: patch_brotoculateur_t6_papillon.py ROOT")
    main(Path(sys.argv[1]))