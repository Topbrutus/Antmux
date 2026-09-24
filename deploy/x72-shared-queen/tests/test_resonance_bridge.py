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
        structure = ResonanceStructure(ResonanceConfig(sample_rate_hz=128.0, carrier_hz=8.0))
        report = structure.run_synthetic_test("SYNCHRONOUS", duration_seconds=1.0)
        self.assertEqual(report["status"], "MEASURED")
        self.assertTrue(structure.snapshot()["standalone"])

    def test_bridge_runs_without_wheel(self):
        bridge = ResonanceWheelBridge(ResonanceStructure())
        self.assertIsNone(bridge.read_wheel())
        snap = bridge.snapshot()
        self.assertTrue(snap["wheel_optional"])
        self.assertTrue(snap["read_only_default"])
        self.assertFalse(snap["commands_enabled"])

    def test_bridge_read_is_copy_and_does_not_mutate_source(self):
        wheel = {"tick_count": 10, "nested": {"value": 2}}
        bridge = ResonanceWheelBridge(ResonanceStructure(), wheel_state_reader=lambda: wheel)
        observed = bridge.read_wheel()
        observed["nested"]["value"] = 999
        self.assertEqual(wheel["nested"]["value"], 2)
        self.assertEqual(bridge.snapshot()["read_count"], 1)

    def test_commands_are_not_delivered_by_default(self):
        delivered = []
        bridge = ResonanceWheelBridge(
            ResonanceStructure(),
            wheel_command_sink=lambda name, payload: delivered.append((name, payload)),
        )
        command = bridge.make_command("MARK_TEST", {"id": 72})
        self.assertFalse(command.delivered)
        self.assertEqual(delivered, [])

    def test_explicit_command_gate_is_required(self):
        delivered = []
        bridge = ResonanceWheelBridge(
            ResonanceStructure(),
            wheel_command_sink=lambda name, payload: delivered.append((name, payload)),
            allow_commands=True,
        )
        command = bridge.make_command("SET_TEST_SIGNAL", {"frequency_hz": 8.0})
        self.assertTrue(command.delivered)
        self.assertEqual(delivered, [("SET_TEST_SIGNAL", {"frequency_hz": 8.0})])

    def test_unknown_command_is_rejected(self):
        bridge = ResonanceWheelBridge(ResonanceStructure())
        with self.assertRaises(ValueError):
            bridge.make_command("EXECUTE_ARBITRARY", {})

    def test_comparison_payload_keeps_direct_candidate_separate(self):
        bridge = ResonanceWheelBridge(ResonanceStructure())
        payload = bridge.comparison_payload(legacy_direct_present=True)
        self.assertEqual(payload["architecture_direct"]["status"], "EXPERIENCE_CANDIDATE")
        self.assertEqual(payload["architecture_direct"]["coupling"], "IN_QUEEN_STEP")
        self.assertTrue(payload["architecture_bridge"]["standalone_structure"])
        self.assertFalse(payload["architecture_bridge"]["default_mutation"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
