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

from app.resonance_bridge import ResonanceWheelBridge
from app.resonance_structure import ResonanceConfig, ResonanceStructure
from app.server import QueenCore


class ResonanceQueenIntegrationTests(unittest.TestCase):
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(RUNTIME_DIR, ignore_errors=True)

    def test_queen_runs_alone_without_resonance_mount(self):
        queen = QueenCore(seed=72)
        for _ in range(240):
            queen.step()
        state = queen.visual_state()
        self.assertEqual(state["tick_count"], 240)
        self.assertTrue(state["integrity_match"])
        self.assertNotIn("resonance_structure", state)
        self.assertNotIn("resonance_bridge", state)

    def test_resonance_structure_runs_alone(self):
        structure = ResonanceStructure(
            ResonanceConfig(sample_rate_hz=128.0, carrier_hz=8.0)
        )
        report = structure.run_synthetic_test(
            "ASCENDING",
            source_channel="C1",
            duration_seconds=1.0,
        )
        self.assertEqual(report["status"], "MEASURED")
        self.assertTrue(structure.snapshot()["standalone"])
        self.assertFalse(structure.snapshot()["mutates_wheel"])

    def test_real_queen_bridge_is_read_only_and_hash_neutral(self):
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

        for _ in range(7):
            observed = bridge.read_wheel()
            self.assertEqual(observed["entity_id"], queen.entity_id)
            self.assertEqual(observed["tick_count"], queen.tick)

        structure.run_synthetic_test(
            "SYNCHRONOUS",
            source_channel="C1",
            duration_seconds=1.0,
        )

        after_protected = queen.protected_h256()
        after_whole = queen.whole_h256()

        self.assertEqual(after_protected, before_protected)
        self.assertEqual(after_whole, before_whole)
        self.assertEqual(bridge.snapshot()["read_count"], 7)
        self.assertTrue(bridge.snapshot()["read_only"])
        self.assertFalse(bridge.snapshot()["mutates_wheel"])
        self.assertFalse(hasattr(bridge, "make_command"))

        result = {
            "schema": "ANTMUX-X72-RESONANCE-QUEEN-INTEGRATION-v0.1",
            "queen_runs_alone": True,
            "structure_runs_alone": True,
            "bridge_read_only": True,
            "bridge_reads": bridge.snapshot()["read_count"],
            "protected_h256_before": before_protected,
            "protected_h256_after": after_protected,
            "whole_h256_before": before_whole,
            "whole_h256_after": after_whole,
            "queen_hash_unchanged": (
                before_protected == after_protected
                and before_whole == after_whole
            ),
            "verdict": "PASS",
        }
        print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    unittest.main(verbosity=2)
