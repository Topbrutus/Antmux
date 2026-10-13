from __future__ import annotations

import hashlib
import shutil
import sys
from pathlib import Path

PRE_ORCH = "1ee7c8e61d538f4d8c5617179a64bc3b15e8c3084ea096a909fa4343afbf737e"
PRE_DASH = "0d2a7f64fe8082186060210891ded1fc12ddeef01daacfbaff496f9e63d41cc6"
PRE_T4 = "736f19b2b2bf25b65d7fa32e17576c3dac3125fb8bf3cb063bb00e6629482ed5"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected 1 occurrence, found {count}")
    return text.replace(old, new, 1)


def main(root: Path) -> None:
    pkg = root / "src" / "brotoculateur"
    orch = pkg / "orchestrator.py"
    dash = pkg / "dashboard.py"
    t4 = pkg / "t4_convergence.py"
    t5 = pkg / "t5_independence.py"
    if not (orch.exists() and dash.exists() and t4.exists()):
        raise SystemExit("missing Brotoculateur POST-T4 sources")

    already = t5.exists() and "T5OperationalIndependence" in orch.read_text(encoding="utf-8")
    if already:
        print("T5_PATCH=ALREADY_APPLIED")
    else:
        if sha(orch) != PRE_ORCH or sha(dash) != PRE_DASH or sha(t4) != PRE_T4:
            raise SystemExit(
                f"pre-hash mismatch ORCH={sha(orch)} DASH={sha(dash)} T4={sha(t4)}"
            )
        shutil.copy2(Path(__file__).with_name("t5_independence.py"), t5)

        t4_text = t4.read_text(encoding="utf-8")
        t4_text = replace_once(
            t4_text,
            "    def status(self) -> dict[str, Any]:\n",
            "    def target_summary(self, z_id: str | None) -> dict[str, Any] | None:\n"
            "        if not isinstance(z_id, str) or not z_id.startswith(\"Z-\"):\n"
            "            return None\n"
            "        rec = self._targets.get(z_id)\n"
            "        if rec is None:\n"
            "            return None\n"
            "        distinct_c2 = len(rec.c2_sigs)\n"
            "        return {\n"
            "            \"z_id\": z_id,\n"
            "            \"distinct_c2\": distinct_c2,\n"
            "            \"families\": len(rec.families),\n"
            "            \"origins\": len(rec.origin_sigs),\n"
            "            \"parents\": len(rec.parent_sigs),\n"
            "            \"observations\": rec.observations,\n"
            "            \"convergent\": distinct_c2 >= 2,\n"
            "        }\n\n"
            "    def status(self) -> dict[str, Any]:\n",
            "t4 target_summary",
        )
        t4.write_text(t4_text, encoding="utf-8", newline="\n")

        o = orch.read_text(encoding="utf-8")
        o = replace_once(o, "from .t4_convergence import T4Convergence\n", "from .t4_convergence import T4Convergence\nfrom .t5_independence import T5OperationalIndependence\n", "orch import")
        o = replace_once(o, "        t4_convergence: T4Convergence | None = None,\n", "        t4_convergence: T4Convergence | None = None,\n        t5_independence: T5OperationalIndependence | None = None,\n", "orch ctor param")
        o = replace_once(o, "        self.t4_convergence = t4_convergence\n", "        self.t4_convergence = t4_convergence\n        self.t5_independence = t5_independence\n", "orch attr")
        o = replace_once(
            o,
            "        self.t4_requested = os.getenv(\"BROTO_T4_ENABLED\", \"0\").strip().lower() in {\"1\", \"true\", \"yes\", \"on\"}\n        self.t4_enabled = bool(self.t4_requested and self.t3_enabled and self.t4_convergence is not None)\n",
            "        self.t4_requested = os.getenv(\"BROTO_T4_ENABLED\", \"0\").strip().lower() in {\"1\", \"true\", \"yes\", \"on\"}\n        self.t4_enabled = bool(self.t4_requested and self.t3_enabled and self.t4_convergence is not None)\n        self.t5_requested = os.getenv(\"BROTO_T5_ENABLED\", \"0\").strip().lower() in {\"1\", \"true\", \"yes\", \"on\"}\n        self.t5_enabled = bool(self.t5_requested and self.t4_enabled and self.t5_independence is not None)\n",
            "orch enable",
        )
        o = replace_once(
            o,
            "            if self.t4_enabled and self.t4_convergence is not None:\n                self.t4_convergence.observe(\n                    packet,\n                    fingerprint,\n                    family=t1_family_name or \"OTHER\",\n                    t2_event=t2_event,\n                    t3_class=t3_class,\n                )\n",
            "            t4_event = \"T4_DISABLED\"\n            t4_summary = None\n            if self.t4_enabled and self.t4_convergence is not None:\n                t4_event = self.t4_convergence.observe(\n                    packet,\n                    fingerprint,\n                    family=t1_family_name or \"OTHER\",\n                    t2_event=t2_event,\n                    t3_class=t3_class,\n                )\n                t4_summary = self.t4_convergence.target_summary(packet.z_id)\n            if self.t5_enabled and self.t5_independence is not None:\n                self.t5_independence.observe(\n                    packet,\n                    fingerprint,\n                    t4_event=t4_event,\n                    t4_summary=t4_summary,\n                )\n",
            "orch observe",
        )
        o = replace_once(
            o,
            "    def t4_status(self) -> dict[str, object]:\n",
            "    def t5_status(self) -> dict[str, object]:\n"
            "        if self.t5_independence is None:\n"
            "            return {\n"
            "                \"mode\": \"BRUTUS_T5_OPERATIONAL_INDEPENDENCE_V1\",\n"
            "                \"enabled\": False,\n"
            "                \"requested\": self.t5_requested,\n"
            "                \"authority\": \"SHADOW_ONLY\",\n"
            "                \"observations\": 0,\n"
            "                \"scientific_independence_claim\": False,\n"
            "                \"operational_candidate_only\": True,\n"
            "                \"controls_scheduling\": False,\n"
            "                \"compute_skips\": 0,\n"
            "                \"proof_promotion\": False,\n"
            "            }\n"
            "        current = dict(self.t5_independence.status())\n"
            "        current[\"enabled\"] = self.t5_enabled\n"
            "        current[\"requested\"] = self.t5_requested\n"
            "        current[\"t4_required\"] = True\n"
            "        current[\"t4_enabled\"] = self.t4_enabled\n"
            "        return current\n\n"
            "    def t4_status(self) -> dict[str, object]:\n",
            "orch t5 status",
        )
        orch.write_text(o, encoding="utf-8", newline="\n")

        d = dash.read_text(encoding="utf-8")
        d = replace_once(d, "from .t4_convergence import T4Convergence\n", "from .t4_convergence import T4Convergence\nfrom .t5_independence import T5OperationalIndependence\n", "dash import")
        d = replace_once(d, "        self.t3_neighborhood = T3SemanticNeighborhood()\n        self.t4_convergence = T4Convergence()\n        self._lock = threading.RLock()\n", "        self.t3_neighborhood = T3SemanticNeighborhood()\n        self.t4_convergence = T4Convergence()\n        self.t5_independence = T5OperationalIndependence()\n        self._lock = threading.RLock()\n", "dash init")
        d = replace_once(d, "            t4_convergence=self.t4_convergence,\n", "            t4_convergence=self.t4_convergence,\n            t5_independence=self.t5_independence,\n", "dash runner")
        # reset has a second constructor occurrence; keep it explicit.
        d = replace_once(d, "            self.t4_convergence = T4Convergence()\n            self._session_started_monotonic = None\n", "            self.t4_convergence = T4Convergence()\n            self.t5_independence = T5OperationalIndependence()\n            self._session_started_monotonic = None\n", "dash reset")
        d = replace_once(d, "            \"t4_convergence\": self._runner.t4_status(),\n", "            \"t4_convergence\": self._runner.t4_status(),\n            \"t5_independence\": self._runner.t5_status(),\n", "dash status")
        dash.write_text(d, encoding="utf-8", newline="\n")
        print("T5_PATCH=PASS")

    for p in (t4, t5, orch, dash):
        print(f"{p.name.upper()}_SHA256={sha(p)}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: patch_brotoculateur_t5_independence.py ROOT")
    main(Path(sys.argv[1]))
