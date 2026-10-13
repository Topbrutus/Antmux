#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

EXPECTED_ORCH_SHA256 = "e68f662ff17e1b70dfb3ca393e45e92326df131565c061f67d49b35fe6396e77"
EXPECTED_DASH_SHA256 = "87ae9f700e72a035f2a58d53120670c64d7e5934c7632385d5f0e171fbb1d26c"
MARKER = "PAPILLON_HIERARCHICAL_RARITY_V1"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly 1 match, got {count}")
    return text.replace(old, new, 1)


def patch(root: Path) -> None:
    orch = root / "src" / "brotoculateur" / "orchestrator.py"
    dash = root / "src" / "brotoculateur" / "dashboard.py"
    if not orch.is_file() or not dash.is_file():
        raise SystemExit("Brotoculateur source files not found")

    ot = orch.read_text(encoding="utf-8")
    dt = dash.read_text(encoding="utf-8")
    if MARKER in ot:
        print("PATCH_ALREADY_PRESENT")
        return

    actual_orch = sha256(orch)
    actual_dash = sha256(dash)
    if actual_orch != EXPECTED_ORCH_SHA256:
        raise SystemExit(f"orchestrator source drift: {actual_orch}")
    if actual_dash != EXPECTED_DASH_SHA256:
        raise SystemExit(f"dashboard source drift: {actual_dash}")

    ot = replace_once(
        ot,
        "from dataclasses import dataclass, field\n",
        "import os\nfrom dataclasses import dataclass, field\n",
        "import os",
    )

    ot = replace_once(
        ot,
        "    def records(self) -> tuple[ResultRecord, ...]:\n        return tuple(self._records.values())\n\n",
        "    def records(self) -> tuple[ResultRecord, ...]:\n        return tuple(self._records.values())\n\n"
        "    def get(self, value: int) -> ResultRecord | None:\n"
        "        return self._records.get(int(value))\n\n",
        "ResultLedger.get",
    )

    ot = replace_once(
        ot,
        "        self.suppressed_branches = 0\n        self.started_at: float | None = None\n",
        "        self.suppressed_branches = 0\n"
        "        self.started_at: float | None = None\n"
        "        self.rarity_enabled = os.getenv(\"BROTO_RARITY_ENABLED\", \"0\").strip().lower() in {\"1\", \"true\", \"yes\", \"on\"}\n"
        "        self.rarity_percent = self._env_percent(\"BROTO_RARITY_PERCENT\", 0)\n"
        "        self.papillon_master_enabled = os.getenv(\"BROTO_PAPILLON_MASTER_ENABLED\", \"0\").strip().lower() in {\"1\", \"true\", \"yes\", \"on\"}\n"
        "        self.papillon_master_percent = self._env_percent(\"BROTO_PAPILLON_MASTER_PERCENT\", 0)\n"
        "        self.rarity_suppressed = 0\n"
        "        self.rarity_replays = 0\n"
        "        self.rarity_control_passes = 0\n"
        "        self.rarity_selected_packets = 0\n"
        "        self.rarity_passthrough_packets = 0\n"
        "        self._value_process_counts: dict[int, int] = {}\n"
        "        self._value_control_bucket: dict[int, int] = {}\n",
        "rarity init",
    )

    old_priority = '''    def _priority(self, packet: TracePacket) -> float:\n        rec = self.ledger.observe(packet)\n        # Favorise les convergences indépendantes sans prétendre mesurer la nouveauté.\n        return 1.0 + rec.independent_paths + 0.5 * rec.formula_diversity\n\n'''
    new_priority = '''    @staticmethod\n    def _env_percent(name: str, default: int = 0) -> int:\n        try:\n            value = int(os.getenv(name, str(default)))\n        except (TypeError, ValueError):\n            value = int(default)\n        return max(0, min(100, value))\n\n    @staticmethod\n    def _rollout_bucket(value: int) -> int:\n        x = int(value) & 0xFFFFFFFFFFFFFFFF\n        x = (x * 11400714819323198485) & 0xFFFFFFFFFFFFFFFF\n        x ^= x >> 29\n        return int(x % 100)\n\n    def _rarity_selected(self, packet: TracePacket) -> bool:\n        return bool(\n            self.rarity_enabled\n            and self.rarity_percent > 0\n            and self._rollout_bucket(packet.value) < self.rarity_percent\n        )\n\n    def _papillon_master_selected(self, packet: TracePacket) -> bool:\n        return bool(\n            self.papillon_master_enabled\n            and self.papillon_master_percent > 0\n            and self._rollout_bucket(packet.value) < self.papillon_master_percent\n        )\n\n    @staticmethod\n    def _rarity_rights(hits: int) -> int:\n        if hits <= 2:\n            return 8\n        if hits <= 4:\n            return 6\n        if hits <= 8:\n            return 4\n        if hits <= 16:\n            return 2\n        return 1\n\n    @staticmethod\n    def _rarity_class(hits: int) -> str:\n        if hits <= 2:\n            return \"RARE_8\"\n        if hits <= 4:\n            return \"RARE_6\"\n        if hits <= 8:\n            return \"SCARCE_4\"\n        if hits <= 16:\n            return \"CONVERGENT_2\"\n        return \"COMMON_1_CONTROL\"\n\n    def _priority_from_record(self, rec: ResultRecord) -> float:\n        rights = self._rarity_rights(rec.hits)\n        path_bonus = 0.25 * min(max(rec.independent_paths - 1, 0), 4)\n        formula_bonus = 0.25 * min(max(rec.formula_diversity - 1, 0), 4)\n        return max(0.1, rights * (1.0 + path_bonus + formula_bonus))\n\n    def _priority(self, packet: TracePacket) -> float:\n        rec = self.ledger.observe(packet)\n        if self._rarity_selected(packet):\n            return self._priority_from_record(rec)\n        return 1.0 + rec.independent_paths + 0.5 * rec.formula_diversity\n\n    def _allow_by_rarity(self, packet: TracePacket) -> bool:\n        rec = self.ledger.get(packet.value)\n        hits = 1 if rec is None else max(1, rec.hits)\n        rights = self._rarity_rights(hits)\n        used = self._value_process_counts.get(packet.value, 0)\n        if used < rights:\n            self._value_process_counts[packet.value] = used + 1\n            return True\n        if hits > 16:\n            bucket = (hits - 17) // 32\n            previous = self._value_control_bucket.get(packet.value, -1)\n            if bucket > previous:\n                self._value_control_bucket[packet.value] = bucket\n                self._value_process_counts[packet.value] = used + 1\n                self.rarity_control_passes += 1\n                return True\n        self.rarity_suppressed += 1\n        return False\n\n    def _enqueue_rarity_replay(self, packet: TracePacket) -> None:\n        rec = self.ledger.get(packet.value)\n        if rec is None:\n            return\n        rights = self._rarity_rights(rec.hits)\n        used = self._value_process_counts.get(packet.value, 0)\n        if used >= rights:\n            return\n        replay_priority = max(0.1, self._priority_from_record(rec) * 0.35)\n        if self._enqueue(BranchTask(packet, priority=replay_priority)):\n            self.rarity_replays += 1\n\n'''
    ot = replace_once(ot, old_priority, new_priority, "rarity methods")

    old_step_head = '''    def step(self) -> bool:\n        if not self._queue:\n            return False\n        _, _, task = heappop(self._queue)\n        packet = task.packet\n        self.processed_packets += 1\n\n'''
    new_step_head = '''    def step(self) -> bool:\n        task: BranchTask | None = None\n        while self._queue:\n            _, _, candidate = heappop(self._queue)\n            if self._rarity_selected(candidate.packet):\n                self.rarity_selected_packets += 1\n                if self._allow_by_rarity(candidate.packet):\n                    task = candidate\n                    break\n            else:\n                self.rarity_passthrough_packets += 1\n                task = candidate\n                break\n        if task is None:\n            return False\n        packet = task.packet\n        self.processed_packets += 1\n\n'''
    ot = replace_once(ot, old_step_head, new_step_head, "step head")

    old_eval = '''            if self.papillon is not None and formula_id in self.papillon.cacheable:\n                out = self.papillon.evaluate(formula, packet)\n                if out is None:\n                    continue\n            else:\n                if not formula.is_applicable(packet):\n                    continue\n                out = formula.apply(packet)\n'''
    new_eval = '''            use_papillon = self.papillon is not None and (\n                formula_id in self.papillon.cacheable or self._papillon_master_selected(packet)\n            )\n            if use_papillon:\n                out = self.papillon.evaluate(formula, packet)\n                if out is None:\n                    continue\n            else:\n                if not formula.is_applicable(packet):\n                    continue\n                out = formula.apply(packet)\n'''
    ot = replace_once(ot, old_eval, new_eval, "Papillon master rollout")

    ot = replace_once(
        ot,
        "            self._enqueue(BranchTask(explore, priority=explore_priority))\n\n        return True\n\n    def papillon_status",
        "            self._enqueue(BranchTask(explore, priority=explore_priority))\n\n"
        "        if self._rarity_selected(packet):\n"
        "            self._enqueue_rarity_replay(packet)\n"
        "        return True\n\n"
        "    def rarity_status(self) -> dict[str, object]:\n"
        "        return {\n"
        f"            \"mode\": \"{MARKER}\",\n"
        "            \"enabled\": self.rarity_enabled,\n"
        "            \"rollout_percent\": self.rarity_percent,\n"
        "            \"law\": \"rarer_values_receive_more_recalculation_rights\",\n"
        "            \"tiers\": [\n"
        "                {\"hits\": \"1-2\", \"rights\": 8, \"class\": \"RARE_8\"},\n"
        "                {\"hits\": \"3-4\", \"rights\": 6, \"class\": \"RARE_6\"},\n"
        "                {\"hits\": \"5-8\", \"rights\": 4, \"class\": \"SCARCE_4\"},\n"
        "                {\"hits\": \"9-16\", \"rights\": 2, \"class\": \"CONVERGENT_2\"},\n"
        "                {\"hits\": \"17+\", \"rights\": 1, \"class\": \"COMMON_1_CONTROL\"},\n"
        "            ],\n"
        "            \"common_control_interval_hits\": 32,\n"
        "            \"selected_queue_pops\": self.rarity_selected_packets,\n"
        "            \"passthrough_queue_pops\": self.rarity_passthrough_packets,\n"
        "            \"rarity_replays_enqueued\": self.rarity_replays,\n"
        "            \"rarity_suppressed\": self.rarity_suppressed,\n"
        "            \"control_passes\": self.rarity_control_passes,\n"
        "            \"tracked_values\": len(self._value_process_counts),\n"
        "        }\n\n"
        "    def papillon_status",
        "rarity status/replay",
    )

    ot = replace_once(
        ot,
        '        return {"enabled": True, **self.papillon.status()}\n',
        '        return {\n'
        '            "enabled": True,\n'
        '            "routing_mode": "PAPILLON_MASTER_ROLLOUT",\n'
        '            "master_enabled": self.papillon_master_enabled,\n'
        '            "master_rollout_percent": self.papillon_master_percent,\n'
        '            **self.papillon.status(),\n'
        '        }\n',
        "papillon status rollout",
    )

    dt = replace_once(
        dt,
        '            "papillon": self._runner.papillon_status(),\n            "sleeping_pool": self._runner.sleeping_pool_status(),\n',
        '            "papillon": self._runner.papillon_status(),\n'
        '            "hierarchical_rarity": self._runner.rarity_status(),\n'
        '            "sleeping_pool": self._runner.sleeping_pool_status(),\n',
        "dashboard rarity status",
    )

    orch.write_text(ot, encoding="utf-8")
    dash.write_text(dt, encoding="utf-8")
    print("PATCH_APPLIED")
    print("ORCHESTRATOR_SHA256=" + sha256(orch))
    print("DASHBOARD_SHA256=" + sha256(dash))


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.home() / "brotoculateur"
    patch(target)
