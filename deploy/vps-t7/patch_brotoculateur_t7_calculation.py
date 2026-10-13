from __future__ import annotations

import hashlib
import shutil
import sys
from pathlib import Path


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def one(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected 1 occurrence, found {count}")
    return text.replace(old, new, 1)


def main(root: Path) -> None:
    pkg = root / "src" / "brotoculateur"
    pap = pkg / "papillon_engine.py"
    orch = pkg / "orchestrator.py"
    dash = pkg / "dashboard.py"
    t7 = pkg / "t7_calculation.py"

    if t7.exists() and "BRUTUS_T7_CALCULATION_TELEMETRY_V1" in orch.read_text(encoding="utf-8"):
        print("T7_PATCH=ALREADY_APPLIED")
        for path in (pap, t7, orch, dash):
            print(f"{path.name.upper()}_SHA256={sha(path)}")
        return

    shutil.copy2(Path(__file__).with_name("t7_calculation.py"), t7)

    p = pap.read_text(encoding="utf-8")
    p = one(
        p,
        "    def status(self) -> dict[str, Any]:\n",
        "    def telemetry_counters(self) -> dict[str, int]:\n"
        "        return {\n"
        "            \"evaluations\": self._evaluations,\n"
        "            \"direct_evaluations\": self._direct,\n"
        "            \"cacheable_evaluations\": self._cacheable_evaluations,\n"
        "            \"cache_hits\": self._hits,\n"
        "            \"cache_misses\": self._misses,\n"
        "            \"predicate_calls\": self._predicate_calls,\n"
        "            \"formula_calls\": self._formula_calls,\n"
        "        }\n\n"
        "    def status(self) -> dict[str, Any]:\n",
        "pap telemetry",
    )
    pap.write_text(p, encoding="utf-8", newline="\n")

    o = orch.read_text(encoding="utf-8")
    o = one(o, "from .t6_papillon import T6PapillonAffinity\n", "from .t6_papillon import T6PapillonAffinity\nfrom .t7_calculation import T7CalculationTelemetry\n", "orch import")
    o = one(o, "        t6_papillon: T6PapillonAffinity | None = None,\n", "        t6_papillon: T6PapillonAffinity | None = None,\n        t7_calculation: T7CalculationTelemetry | None = None,\n", "orch param")
    o = one(o, "        self.t6_papillon = t6_papillon\n", "        self.t6_papillon = t6_papillon\n        self.t7_calculation = t7_calculation\n", "orch assign")
    o = one(
        o,
        "        self.t6_requested = os.getenv(\"BROTO_T6_ENABLED\", \"0\").strip().lower() in {\"1\", \"true\", \"yes\", \"on\"}\n        self.t6_enabled = bool(self.t6_requested and self.t5_enabled and self.t6_papillon is not None and self.papillon is not None)\n",
        "        self.t6_requested = os.getenv(\"BROTO_T6_ENABLED\", \"0\").strip().lower() in {\"1\", \"true\", \"yes\", \"on\"}\n        self.t6_enabled = bool(self.t6_requested and self.t5_enabled and self.t6_papillon is not None and self.papillon is not None)\n        self.t7_requested = os.getenv(\"BROTO_T7_ENABLED\", \"0\").strip().lower() in {\"1\", \"true\", \"yes\", \"on\"}\n        self.t7_enabled = bool(self.t7_requested and self.t6_enabled and self.t7_calculation is not None and self.papillon is not None)\n",
        "orch flags",
    )
    o = one(
        o,
        "        packet = task.packet\n        self.processed_packets += 1\n\n        for formula_id in self.registry.ids():\n",
        "        packet = task.packet\n        self.processed_packets += 1\n\n        formula_ids = self.registry.ids()\n        t7_pap_before = self.papillon.telemetry_counters() if self.t7_enabled and self.papillon is not None else {}\n        t7_native_attempts = 0\n        t7_native_predicates = 0\n        t7_native_formula_calls = 0\n        t7_outputs = 0\n\n        for formula_id in formula_ids:\n",
        "step begin",
    )
    o = one(
        o,
        "            else:\n                if not formula.is_applicable(packet):\n                    continue\n                out = formula.apply(packet)\n",
        "            else:\n                if self.t7_enabled:\n                    t7_native_attempts += 1\n                    if formula.predicate is not None:\n                        t7_native_predicates += 1\n                if not formula.is_applicable(packet):\n                    continue\n                if self.t7_enabled:\n                    if formula.predicate is not None:\n                        t7_native_predicates += 1\n                    t7_native_formula_calls += 1\n                out = formula.apply(packet)\n",
        "native accounting",
    )
    o = one(
        o,
        "            if out.value == packet.value:\n                continue\n            if packet.z_id is not None:\n",
        "            if out.value == packet.value:\n                continue\n            if self.t7_enabled:\n                t7_outputs += 1\n            if packet.z_id is not None:\n",
        "output accounting",
    )
    o = one(
        o,
        "            self._enqueue(BranchTask(explore, priority=explore_priority))\n\n        if self._rarity_selected(packet):\n            self._enqueue_rarity_replay(packet)\n",
        "            self._enqueue(BranchTask(explore, priority=explore_priority))\n\n        if self.t7_enabled and self.t7_calculation is not None and self.papillon is not None:\n            self.t7_calculation.observe_packet(\n                packet_value=packet.value,\n                logical_formula_attempts=len(formula_ids),\n                native_attempts=t7_native_attempts,\n                native_predicate_calls=t7_native_predicates,\n                native_formula_calls=t7_native_formula_calls,\n                papillon_before=t7_pap_before,\n                papillon_after=self.papillon.telemetry_counters(),\n                outputs_emitted=t7_outputs,\n            )\n\n        if self._rarity_selected(packet):\n            self._enqueue_rarity_replay(packet)\n",
        "step end",
    )
    o = one(
        o,
        "    def t6_status(self) -> dict[str, object]:\n",
        "    def t7_status(self) -> dict[str, object]:\n"
        "        if self.t7_calculation is None:\n"
        "            return {\n"
        "                \"mode\": \"BRUTUS_T7_CALCULATION_TELEMETRY_V1\",\n"
        "                \"enabled\": False,\n"
        "                \"requested\": self.t7_requested,\n"
        "                \"authority\": \"SHADOW_ONLY\",\n"
        "                \"packet_observations\": 0,\n"
        "                \"controls_formula_selection\": False,\n"
        "                \"compute_skips\": 0,\n"
        "                \"proof_promotion\": False,\n"
        "            }\n"
        "        current = dict(self.t7_calculation.status())\n"
        "        current[\"enabled\"] = self.t7_enabled\n"
        "        current[\"requested\"] = self.t7_requested\n"
        "        current[\"t6_required\"] = True\n"
        "        current[\"t6_enabled\"] = self.t6_enabled\n"
        "        return current\n\n"
        "    def t6_status(self) -> dict[str, object]:\n",
        "orch status",
    )
    orch.write_text(o, encoding="utf-8", newline="\n")

    d = dash.read_text(encoding="utf-8")
    d = one(d, "from .t6_papillon import T6PapillonAffinity\n", "from .t6_papillon import T6PapillonAffinity\nfrom .t7_calculation import T7CalculationTelemetry\n", "dash import")
    d = one(d, "        self.t5_independence = T5OperationalIndependence()\n        self.t6_papillon = T6PapillonAffinity()\n        self._lock = threading.RLock()\n", "        self.t5_independence = T5OperationalIndependence()\n        self.t6_papillon = T6PapillonAffinity()\n        self.t7_calculation = T7CalculationTelemetry()\n        self._lock = threading.RLock()\n", "dash init")
    d = one(d, "            self.t5_independence = T5OperationalIndependence()\n            self.t6_papillon = T6PapillonAffinity()\n            self._session_started_monotonic = None\n", "            self.t5_independence = T5OperationalIndependence()\n            self.t6_papillon = T6PapillonAffinity()\n            self.t7_calculation = T7CalculationTelemetry()\n            self._session_started_monotonic = None\n", "dash reset")
    d = one(d, "            t6_papillon=self.t6_papillon,\n", "            t6_papillon=self.t6_papillon,\n            t7_calculation=self.t7_calculation,\n", "dash runner")
    d = one(d, "            \"t6_papillon\": self._runner.t6_status(),\n", "            \"t6_papillon\": self._runner.t6_status(),\n            \"t7_calculation\": self._runner.t7_status(),\n", "dash status")
    dash.write_text(d, encoding="utf-8", newline="\n")

    print("T7_PATCH=PASS")
    for path in (pap, t7, orch, dash):
        print(f"{path.name.upper()}_SHA256={sha(path)}")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
