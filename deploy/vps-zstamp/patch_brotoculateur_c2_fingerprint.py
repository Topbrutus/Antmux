from __future__ import annotations

import hashlib
import sys
from pathlib import Path

EXPECTED = {
    "engine.py": "4aa5c6b9f8feed9559ded55b1db72016ebb45c00d2fbc00ff9e92b74ea677db5",
    "orchestrator.py": "d562dede20d171684d7d5d6d4bcd3f001260fce6b716ce28c1e91168623a0b06",
    "dashboard.py": "1c47b3f596cf8341f7a0ea54b6118f725349e41b7941e2494684a17766fd43f6",
}
MARKER = "BRUTUS_C2_FINGERPRINT_V1"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected 1 replacement, found {count}")
    return text.replace(old, new, 1)


def write_lf(path: Path, text: str) -> None:
    path.write_bytes(text.replace("\r\n", "\n").encode("utf-8"))


def patch(root: Path) -> None:
    pkg = root / "src" / "brotoculateur"
    paths = {name: pkg / name for name in EXPECTED}
    if all(path.is_file() for path in paths.values()) is False:
        raise RuntimeError("Brotoculateur C2 source files not found")

    engine_path = paths["engine.py"]
    orch_path = paths["orchestrator.py"]
    dash_path = paths["dashboard.py"]
    if MARKER in engine_path.read_text(encoding="utf-8"):
        print("C2_PATCH=ALREADY_APPLIED")
        for name, path in paths.items():
            print(f"{name.upper()}_SHA256={sha(path)}")
        return

    for name, path in paths.items():
        actual = sha(path)
        if actual != EXPECTED[name]:
            raise RuntimeError(f"C2 source drift {name}: {actual} != {EXPECTED[name]}")

    engine = engine_path.read_text(encoding="utf-8")
    engine = replace_once(
        engine,
        "from __future__ import annotations\n\nfrom dataclasses import dataclass, field, replace\n",
        "from __future__ import annotations\n\nimport json\nfrom dataclasses import dataclass, field, replace\n",
        "engine json import",
    )
    anchor = '''def z_stamp_child(packet: TracePacket, parent: TracePacket) -> TracePacket:\n    z_id = z_identity_for_value(packet.value)\n    parent_z = parent.z_id or z_identity_for_value(parent.value)\n    origin_z = parent.z_origin_id or parent_z\n    return replace(packet, z_id=z_id, z_parent_id=parent_z, z_origin_id=origin_z)\n\n\n'''
    addition = anchor + '''C2_FINGERPRINT_SCHEMA = "BRUTUS_C2_FINGERPRINT_V1"\n\ndef c2_fingerprint(packet: TracePacket) -> str:\n    """Canonical structural trace fingerprint; provenance path/UUIDs stay external."""\n    payload = {\n        "schema": C2_FINGERPRINT_SCHEMA,\n        "value": str(int(packet.value)),\n        "depth": int(packet.depth),\n        "formula_chain": list(packet.formula_chain),\n        "state": packet.state.value,\n        "z_id": packet.z_id,\n        "z_parent_id": packet.z_parent_id,\n        "z_origin_id": packet.z_origin_id,\n    }\n    raw = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))\n    return "C2-" + sha256(raw.encode("utf-8")).hexdigest()\n\n\n'''
    engine = replace_once(engine, anchor, addition, "engine C2 helper")
    write_lf(engine_path, engine)

    orch = orch_path.read_text(encoding="utf-8")
    orch = replace_once(
        orch,
        "    z_stamp_root, z_stamp_child,\n",
        "    z_stamp_root, z_stamp_child, c2_fingerprint,\n",
        "orchestrator C2 import",
    )
    orch = replace_once(
        orch,
        "        self.zstamp_children = 0\n        self.rarity_suppressed = 0\n",
        "        self.zstamp_children = 0\n"
        "        self.c2_enabled = os.getenv(\"BROTO_C2_ENABLED\", \"0\").strip().lower() in {\"1\", \"true\", \"yes\", \"on\"}\n"
        "        self.c2_roots = 0\n"
        "        self.c2_children = 0\n"
        "        self.c2_first: str | None = None\n"
        "        self.c2_last: str | None = None\n"
        "        self.rarity_suppressed = 0\n",
        "orchestrator C2 init",
    )
    orch = replace_once(
        orch,
        "            self.ledger.observe(packet)\n            self._enqueue(BranchTask(packet, priority=1.0))\n",
        "            self._observe_c2(packet, root=True)\n"
        "            self.ledger.observe(packet)\n"
        "            self._enqueue(BranchTask(packet, priority=1.0))\n",
        "C2 root observation",
    )
    method_anchor = '''    def _rarity_selected(self, packet: TracePacket) -> bool:\n'''
    method_addition = '''    def _observe_c2(self, packet: TracePacket, *, root: bool) -> str | None:\n        if not self.c2_enabled or packet.z_id is None:\n            return None\n        fingerprint = c2_fingerprint(packet)\n        if root:\n            self.c2_roots += 1\n        else:\n            self.c2_children += 1\n        if self.c2_first is None:\n            self.c2_first = fingerprint\n        self.c2_last = fingerprint\n        return fingerprint\n\n''' + method_anchor
    orch = replace_once(orch, method_anchor, method_addition, "C2 observer method")
    orch = replace_once(
        orch,
        "            if packet.z_id is not None:\n                out = z_stamp_child(out, packet)\n                self.zstamp_children += 1\n            if self.observation_sink is not None:\n",
        "            if packet.z_id is not None:\n"
        "                out = z_stamp_child(out, packet)\n"
        "                self.zstamp_children += 1\n"
        "            self._observe_c2(out, root=False)\n"
        "            if self.observation_sink is not None:\n",
        "C2 child observation",
    )
    status_anchor = '''    def zstamp_status(self) -> dict[str, object]:\n'''
    status_addition = '''    def c2_status(self) -> dict[str, object]:\n        return {\n            "mode": "BRUTUS_C2_FINGERPRINT_V1",\n            "enabled": self.c2_enabled,\n            "scope": "Z_STAMPED_PACKETS_ONLY",\n            "roots_fingerprinted": self.c2_roots,\n            "children_fingerprinted": self.c2_children,\n            "fingerprints": self.c2_roots + self.c2_children,\n            "first_fingerprint": self.c2_first,\n            "last_fingerprint": self.c2_last,\n            "canonical_fields": ["value", "depth", "formula_chain", "state", "z_id", "z_parent_id", "z_origin_id"],\n            "excluded_volatile_fields": ["packet_id", "parent_id", "branch_path"],\n            "materialized_on_packet": False,\n            "c2_changes_state_hash": False,\n            "value_mutated": False,\n            "proof_promotion": False,\n        }\n\n''' + status_anchor
    orch = replace_once(orch, status_anchor, status_addition, "C2 status")
    write_lf(orch_path, orch)

    dash = dash_path.read_text(encoding="utf-8")
    dash = replace_once(
        dash,
        '        self._zstamp_cumulative = {"root_selected": 0, "root_passthrough": 0, "children_stamped": 0}\n        self._session_started_monotonic: float | None = None\n',
        '        self._zstamp_cumulative = {"root_selected": 0, "root_passthrough": 0, "children_stamped": 0}\n'
        '        self._c2_cumulative = {"roots_fingerprinted": 0, "children_fingerprinted": 0, "first_fingerprint": None, "last_fingerprint": None}\n'
        '        self._session_started_monotonic: float | None = None\n',
        "dashboard C2 init",
    )
    dash = replace_once(
        dash,
        '            self._zstamp_cumulative = {"root_selected": 0, "root_passthrough": 0, "children_stamped": 0}\n            self._session_started_monotonic = None\n',
        '            self._zstamp_cumulative = {"root_selected": 0, "root_passthrough": 0, "children_stamped": 0}\n'
        '            self._c2_cumulative = {"roots_fingerprinted": 0, "children_fingerprinted": 0, "first_fingerprint": None, "last_fingerprint": None}\n'
        '            self._session_started_monotonic = None\n',
        "dashboard C2 reset",
    )
    helper_anchor = '''    def _advance_round_unlocked(self) -> None:\n'''
    helper_addition = '''    def _c2_rollup_unlocked(self) -> None:\n        current = self._runner.c2_status()\n        self._c2_cumulative["roots_fingerprinted"] += int(current.get("roots_fingerprinted") or 0)\n        self._c2_cumulative["children_fingerprinted"] += int(current.get("children_fingerprinted") or 0)\n        if self._c2_cumulative["first_fingerprint"] is None and current.get("first_fingerprint"):\n            self._c2_cumulative["first_fingerprint"] = current.get("first_fingerprint")\n        if current.get("last_fingerprint"):\n            self._c2_cumulative["last_fingerprint"] = current.get("last_fingerprint")\n\n    def _c2_status_unlocked(self) -> dict[str, Any]:\n        current = dict(self._runner.c2_status())\n        current["total_roots_fingerprinted"] = self._c2_cumulative["roots_fingerprinted"] + int(current.get("roots_fingerprinted") or 0)\n        current["total_children_fingerprinted"] = self._c2_cumulative["children_fingerprinted"] + int(current.get("children_fingerprinted") or 0)\n        current["total_fingerprints"] = current["total_roots_fingerprinted"] + current["total_children_fingerprinted"]\n        current["session_first_fingerprint"] = self._c2_cumulative["first_fingerprint"] or current.get("first_fingerprint")\n        current["session_last_fingerprint"] = current.get("last_fingerprint") or self._c2_cumulative["last_fingerprint"]\n        current["cumulative_across_rounds"] = True\n        return current\n\n''' + helper_anchor
    dash = replace_once(dash, helper_anchor, helper_addition, "dashboard C2 helpers")
    dash = replace_once(
        dash,
        "        self._zstamp_rollup_unlocked()\n        self._round_seeds = self._next_round_seeds_unlocked()\n",
        "        self._zstamp_rollup_unlocked()\n        self._c2_rollup_unlocked()\n        self._round_seeds = self._next_round_seeds_unlocked()\n",
        "dashboard C2 rollup",
    )
    dash = replace_once(
        dash,
        '            "brutus_cortex": self._zstamp_status_unlocked(),\n            "hierarchical_rarity": self._runner.rarity_status(),\n',
        '            "brutus_cortex": self._zstamp_status_unlocked(),\n'
        '            "c2_fingerprint": self._c2_status_unlocked(),\n'
        '            "hierarchical_rarity": self._runner.rarity_status(),\n',
        "dashboard C2 status",
    )
    write_lf(dash_path, dash)

    print("C2_PATCH=PASS")
    for name, path in paths.items():
        print(f"{name.upper()}_SHA256={sha(path)}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: patch_brotoculateur_c2_fingerprint.py <brotoculateur-root>")
    patch(Path(sys.argv[1]).resolve())
