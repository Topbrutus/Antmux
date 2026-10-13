from __future__ import annotations

import hashlib
import sys
from pathlib import Path

MARKER = "BRUTUS_CORTEX_ZSTAMP_V1"
EXPECTED = {
    "engine.py": "cb29f5df30af3e68cff933cc9ac26354ab146582d144c1b2c6174a880b8abc6b",
    "orchestrator.py": "90ddcc9abf82e5eec4d8b1fa50b2cef4540680bde2a5b87e8e2963e2cd0041c1",
    "dashboard.py": "71e204d3ab814b27c6c98bea9f2c755f396a6625fce713b2e5568f0521d80117",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected 1 replacement, found {count}")
    return text.replace(old, new, 1)


def patch(root: Path) -> None:
    pkg = root / "src" / "brotoculateur"
    files = {name: pkg / name for name in EXPECTED}
    if (
        MARKER in files["engine.py"].read_text(encoding="utf-8")
        and MARKER in files["orchestrator.py"].read_text(encoding="utf-8")
        and "\"brutus_cortex\"" in files["dashboard.py"].read_text(encoding="utf-8")
    ):
        print("ZSTAMP_PATCH=ALREADY_APPLIED")
        return
    for name, path in files.items():
        actual = sha(path)
        if actual != EXPECTED[name]:
            raise RuntimeError(f"hash drift {name}: {actual} != {EXPECTED[name]}")

    engine_path = files["engine.py"]
    engine = engine_path.read_text(encoding="utf-8")
    engine = replace_once(
        engine,
        "    formula_chain: tuple[str, ...] = ()\n    state: ValidationState = ValidationState.EXACT\n",
        "    formula_chain: tuple[str, ...] = ()\n    state: ValidationState = ValidationState.EXACT\n    z_id: str | None = None\n    z_parent_id: str | None = None\n    z_origin_id: str | None = None\n",
        "engine fields",
    )
    engine = replace_once(
        engine,
        "        raw = (\n            f\"{self.value}|{self.packet_id}|{self.parent_id}|\"\n            f\"{self.branch_path}|{self.depth}|{self.formula_chain}|{self.state.value}\"\n        )\n        return sha256(raw.encode(\"utf-8\")).hexdigest()\n\n\n@dataclass(frozen=True)\nclass Formula:\n",
        "        raw = (\n            f\"{self.value}|{self.packet_id}|{self.parent_id}|\"\n            f\"{self.branch_path}|{self.depth}|{self.formula_chain}|{self.state.value}\"\n        )\n        # Backward compatible: an unstamped packet keeps the exact legacy state hash.\n        if self.z_id is not None:\n            raw += f\"|Z:{self.z_id}|ZP:{self.z_parent_id}|ZO:{self.z_origin_id}\"\n        return sha256(raw.encode(\"utf-8\")).hexdigest()\n\n\nZSTAMP_SCHEMA = \"BRUTUS_CORTEX_ZSTAMP_V1\"\n\ndef z_identity_for_value(value: int) -> str:\n    digest = sha256(f\"ZSTAMP-V1|{int(value)}\".encode(\"utf-8\")).hexdigest()\n    return \"Z-\" + digest[:32]\n\ndef z_stamp_root(packet: TracePacket) -> TracePacket:\n    z_id = z_identity_for_value(packet.value)\n    return replace(packet, z_id=z_id, z_parent_id=None, z_origin_id=z_id)\n\ndef z_stamp_child(packet: TracePacket, parent: TracePacket) -> TracePacket:\n    z_id = z_identity_for_value(packet.value)\n    parent_z = parent.z_id or z_identity_for_value(parent.value)\n    origin_z = parent.z_origin_id or parent_z\n    return replace(packet, z_id=z_id, z_parent_id=parent_z, z_origin_id=origin_z)\n\n\n@dataclass(frozen=True)\nclass Formula:\n",
        "engine helpers",
    )
    engine_path.write_text(engine, encoding="utf-8")

    orch_path = files["orchestrator.py"]
    orch = orch_path.read_text(encoding="utf-8")
    orch = replace_once(orch, "import os\n", "import os\nfrom hashlib import sha256\n", "orchestrator hashlib")
    orch = replace_once(
        orch,
        "from .engine import FormulaRegistry, TracePacket, ValidationState, y_split\n",
        "from .engine import (\n    FormulaRegistry, TracePacket, ValidationState, y_split,\n    z_stamp_root, z_stamp_child,\n)\n",
        "orchestrator imports",
    )
    orch = replace_once(
        orch,
        "        self.papillon_master_percent = self._env_percent(\"BROTO_PAPILLON_MASTER_PERCENT\", 0)\n",
        "        self.papillon_master_percent = self._env_percent(\"BROTO_PAPILLON_MASTER_PERCENT\", 0)\n        self.zstamp_enabled = os.getenv(\"BROTO_ZSTAMP_ENABLED\", \"0\").strip().lower() in {\"1\", \"true\", \"yes\", \"on\"}\n        self.zstamp_percent = self._env_percent(\"BROTO_ZSTAMP_PERCENT\", 0)\n        self.zstamp_roots = 0\n        self.zstamp_passthrough_roots = 0\n        self.zstamp_children = 0\n",
        "orchestrator init",
    )
    orch = replace_once(
        orch,
        "    def seed(self, packets: Iterable[TracePacket]) -> None:\n        for packet in packets:\n            self.ledger.observe(packet)\n            self._enqueue(BranchTask(packet, priority=1.0))\n",
        "    def seed(self, packets: Iterable[TracePacket]) -> None:\n        for packet in packets:\n            if packet.z_id is None and self.zstamp_enabled:\n                if self._zstamp_selected(packet):\n                    packet = z_stamp_root(packet)\n                    self.zstamp_roots += 1\n                else:\n                    self.zstamp_passthrough_roots += 1\n            self.ledger.observe(packet)\n            self._enqueue(BranchTask(packet, priority=1.0))\n",
        "orchestrator seed",
    )
    orch = replace_once(
        orch,
        "    @staticmethod\n    def _rollout_bucket(value: int) -> int:\n        x = int(value) & 0xFFFFFFFFFFFFFFFF\n        x = (x * 11400714819323198485) & 0xFFFFFFFFFFFFFFFF\n        x ^= x >> 29\n        return int(x % 100)\n\n    def _rarity_selected(self, packet: TracePacket) -> bool:\n",
        "    @staticmethod\n    def _rollout_bucket(value: int) -> int:\n        x = int(value) & 0xFFFFFFFFFFFFFFFF\n        x = (x * 11400714819323198485) & 0xFFFFFFFFFFFFFFFF\n        x ^= x >> 29\n        return int(x % 100)\n\n    @staticmethod\n    def _zstamp_bucket(value: int) -> int:\n        digest = sha256(f\"ZSTAMP-V1|{int(value)}\".encode(\"utf-8\")).digest()\n        return int.from_bytes(digest[:8], \"big\") % 100\n\n    def _zstamp_selected(self, packet: TracePacket) -> bool:\n        return bool(\n            self.zstamp_enabled\n            and self.zstamp_percent > 0\n            and self._zstamp_bucket(packet.value) < self.zstamp_percent\n        )\n\n    def _rarity_selected(self, packet: TracePacket) -> bool:\n",
        "orchestrator z selection",
    )
    orch = replace_once(
        orch,
        "            if out.value == packet.value:\n                continue\n            if self.observation_sink is not None:\n",
        "            if out.value == packet.value:\n                continue\n            if packet.z_id is not None:\n                out = z_stamp_child(out, packet)\n                self.zstamp_children += 1\n            if self.observation_sink is not None:\n",
        "orchestrator child stamp",
    )
    orch = replace_once(
        orch,
        "    def rarity_status(self) -> dict[str, object]:\n",
        "    def zstamp_status(self) -> dict[str, object]:\n        return {\n            \"mode\": \"BRUTUS_CORTEX_ZSTAMP_V1\",\n            \"enabled\": self.zstamp_enabled,\n            \"rollout_percent\": self.zstamp_percent,\n            \"root_selected\": self.zstamp_roots,\n            \"root_passthrough\": self.zstamp_passthrough_roots,\n            \"children_stamped\": self.zstamp_children,\n            \"identity_law\": \"Z = sha256('ZSTAMP-V1|' + integer_value)[:32]\",\n            \"identity_excludes_path\": True,\n            \"provenance_fields\": [\"parent_id\", \"branch_path\", \"formula_chain\"],\n            \"lineage_fields\": [\"z_parent_id\", \"z_origin_id\"],\n            \"value_mutated\": False,\n            \"proof_promotion\": False,\n        }\n\n    def rarity_status(self) -> dict[str, object]:\n",
        "orchestrator status",
    )
    orch_path.write_text(orch, encoding="utf-8")

    dash_path = files["dashboard.py"]
    dash = dash_path.read_text(encoding="utf-8")
    dash = replace_once(
        dash,
        "            \"papillon\": self._runner.papillon_status(),\n            \"hierarchical_rarity\": self._runner.rarity_status(),\n",
        "            \"papillon\": self._runner.papillon_status(),\n            \"brutus_cortex\": self._runner.zstamp_status(),\n            \"hierarchical_rarity\": self._runner.rarity_status(),\n",
        "dashboard status",
    )
    dash_path.write_text(dash, encoding="utf-8")

    print("ZSTAMP_PATCH=PASS")
    for name, path in files.items():
        print(f"{name.upper()}_SHA256={sha(path)}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: patch_brotoculateur_zstamp.py <brotoculateur-root>")
    patch(Path(sys.argv[1]).resolve())
