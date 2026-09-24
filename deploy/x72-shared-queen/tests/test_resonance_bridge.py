from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.resonance_bridge import ResonanceWheelBridge
from app.resonance_structure import ResonanceConfig, ResonanceStructure


class ResonanceBridgeTests(unittest.TestCase):
    def test_structure_runs_without_wheel(self):
        structure = ResonanceStructure(
            ResonanceConfig(sample_rate_hz=128.0, carrier_hz=8.0)
        )
        report = structure.run_synthetic_test(
            "SYNCHRONOUS",
            duration_seconds=1.0,
        )
        self.assertEqual(report["status"], "MEASURED")
        self.assertTrue(structure.snapshot()["standalone"])

    def test_bridge_runs_without_wheel(self):
        bridge = ResonanceWheelBridge(ResonanceStructure())
        self.assertIsNone(bridge.read_wheel())
        snap = bridge.snapshot()
        self.assertTrue(snap["wheel_optional"])
        self.assertTrue(snap["read_only"])
        self.assertFalse(snap["mutates_wheel"])
        self.assertFalse(snap["wheel_reader_attached"])

    def test_bridge_read_is_copy_and_does_not_mutate_source(self):
        wheel = {"tick_count": 10, "nested": {"value": 2}}
        bridge = ResonanceWheelBridge(
            ResonanceStructure(),
            wheel_state_reader=lambda: wheel,
        )
        observed = bridge.read_wheel()
        self.assertIsNotNone(observed)
        observed["nested"]["value"] = 999
        self.assertEqual(wheel["nested"]["value"], 2)
        self.assertEqual(bridge.snapshot()["read_count"], 1)

    def test_bridge_exposes_no_command_surface(self):
        bridge = ResonanceWheelBridge(ResonanceStructure())
        self.assertFalse(hasattr(bridge, "make_command"))
        self.assertFalse(hasattr(bridge, "wheel_command_sink"))
        self.assertFalse(hasattr(bridge, "allow_commands"))

    def test_multiple_reads_remain_observation_only(self):
        wheel = {"tick_count": 0}
        bridge = ResonanceWheelBridge(
            ResonanceStructure(),
            wheel_state_reader=lambda: wheel,
        )
        for index in range(7):
            wheel["tick_count"] = index
            observed = bridge.read_wheel()
            self.assertEqual(observed["tick_count"], index)
        snap = bridge.snapshot()
        self.assertEqual(snap["read_count"], 7)
        self.assertTrue(snap["read_only"])
        self.assertFalse(snap["mutates_wheel"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
