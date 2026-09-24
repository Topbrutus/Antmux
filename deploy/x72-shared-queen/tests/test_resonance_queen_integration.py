from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME_DIR = Path(tempfile.mkdtemp(prefix="antmux-x72-resonance-queen-"))
os.environ["ANTMUX_X72_DATA_DIR"] = str(RUNTIME_DIR)
sys.path.insert(0, str(ROOT))

from app.chakra_pump import ChakraPumpConfig, ProgressiveChakraPump
from app.resonance_bridge import ResonanceWheelBridge
from app.resonance_structure import ResonanceConfig, ResonanceStructure
from app.server import QueenCore


class ResonanceQueenIntegrationTests(unittest.TestCase):
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(RUNTIME_DIR, ignore_errors=True)

    def test_wheel_runs_alone_without_resonance_mount(self):
        queen = QueenCore(seed=72)
        for _ in range(240):
            queen.step()
        state = queen.visual_state()
        self.assertEqual(state["tick_count"], 240)
        self.assertTrue(state["integrity_match"])
        self.assertNotIn("chakra_pump", state)
        self.assertNotIn("resonance_structure", state)
        self.assertNotIn("resonance_bridge", state)

    def test_real_queen_plus_bridge_is_read_only_by_default(self):
        queen = QueenCore(seed=72)
        for _ in range(120):
            queen.step()
        structure = ResonanceStructure(
            ResonanceConfig(sample_rate_hz=128.0, carrier_hz=8.0)
        )
        bridge = ResonanceWheelBridge(
            structure,
            wheel_state_reader=queen.visual_state,
        )

        before_protected = queen.protected_h256()
        before_whole = queen.whole_h256()
        observed = bridge.read_wheel()
        self.assertEqual(observed["entity_id"], queen.entity_id)
        self.assertEqual(observed["tick_count"], queen.tick)

        structure.run_synthetic_test(
            "SYNCHRONOUS",
            source_channel="C1",
            duration_seconds=1.0,
        )

        self.assertEqual(queen.protected_h256(), before_protected)
        self.assertEqual(queen.whole_h256(), before_whole)
        self.assertFalse(bridge.snapshot()["commands_enabled"])
        self.assertFalse(bridge.snapshot()["mutates_wheel_by_default"])

    def test_architecture_a_replay_and_bridge_b_are_measurably_separate(self):
        direct_queen = QueenCore(seed=72)
        control_queen = QueenCore(seed=72)
        legacy = ProgressiveChakraPump(ChakraPumpConfig(ticks_per_level=1))

        direct_calls = 0
        for _ in range(720):
            direct_queen.step()
            control_queen.step()
            noyau = direct_queen.noyau_runtime.visual_payload()["noyau"]
            legacy.step(
                queen_tick=direct_queen.tick,
                integrity_ready=direct_queen.integrity_match(),
                stability_ready=bool(noyau["basin1"]["crystallized"]),
            )
            direct_calls += 1

        self.assertEqual(direct_calls, 720)
        self.assertEqual(direct_queen.protected_h256(), control_queen.protected_h256())
        self.assertEqual(direct_queen.whole_h256(), control_queen.whole_h256())

        structure = ResonanceStructure(
            ResonanceConfig(sample_rate_hz=128.0, carrier_hz=8.0)
        )
        bridge = ResonanceWheelBridge(
            structure,
            wheel_state_reader=control_queen.visual_state,
        )
        before = control_queen.whole_h256()
        for _ in range(7):
            bridge.read_wheel()
        structure.run_synthetic_test(
            "ASCENDING",
            source_channel="C1",
            duration_seconds=1.0,
        )
        after = control_queen.whole_h256()

        self.assertEqual(before, after)
        self.assertEqual(bridge.snapshot()["read_count"], 7)
        self.assertEqual(len(bridge.snapshot()["commands"]), 0)

        comparison = {
            "schema": "ANTMUX-X72-ARCHITECTURE-A-B-COMPARISON-v0.1",
            "architecture_a": {
                "mode": "LEGACY_DIRECT_COUPLING_REPLAY",
                "coupling_calls": direct_calls,
                "queen_hash_changed_by_external_pump": False,
                "pump_state": legacy.snapshot().to_dict(),
            },
            "architecture_b": {
                "mode": "INDEPENDENT_STRUCTURE_PLUS_BRIDGE",
                "bridge_reads": bridge.snapshot()["read_count"],
                "commands_delivered": 0,
                "queen_hash_changed_by_bridge_or_structure": False,
                "standalone_structure": structure.snapshot()["standalone"],
            },
            "verdict": "PASS",
        }
        print(json.dumps(comparison, sort_keys=True))


if __name__ == "__main__":
    unittest.main(verbosity=2)
