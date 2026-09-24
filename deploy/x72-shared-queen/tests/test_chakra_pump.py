from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.chakra_pump import ChakraPumpConfig, ProgressiveChakraPump


class LegacyDirectCandidateTests(unittest.TestCase):
    """Keep the previous pump candidate reproducible without mounting it in QueenCore."""

    def make_pump(self) -> ProgressiveChakraPump:
        return ProgressiveChakraPump(ChakraPumpConfig(ticks_per_level=1))

    def test_exact_progressive_paths(self):
        pump = self.make_pump()
        s1 = pump.step(queen_tick=1, integrity_ready=True, stability_ready=True)
        self.assertEqual((s1.current_level, s1.target_level, s1.direction), (2, 2, "DOWN"))
        s2 = pump.step(queen_tick=2, integrity_ready=True, stability_ready=True)
        self.assertEqual(
            (s2.current_level, s2.target_level, s2.direction, s2.completed_cycles),
            (1, 3, "UP", 1),
        )
        self.assertEqual(s2.up_route, ("CH1", "CH2", "CH3"))
        self.assertEqual(s2.down_route, ("CH3", "CH2", "CH1"))

    def test_progression_reaches_seven_without_overflow(self):
        pump = self.make_pump()
        tick = 0
        while pump.target_level < 7 or pump.current_level != 1 or pump.completed_cycles < 5:
            tick += 1
            pump.step(queen_tick=tick, integrity_ready=True, stability_ready=True)
            self.assertLessEqual(pump.current_level, 7)
            self.assertLessEqual(pump.target_level, 7)
            self.assertLess(tick, 100)
        self.assertEqual(pump.target_level, 7)
        self.assertAlmostEqual(pump.retained_boost, 1.0)

    def test_gates_block_progress(self):
        pump = ProgressiveChakraPump(ChakraPumpConfig(ticks_per_level=3))
        for tick in range(1, 10):
            state = pump.step(queen_tick=tick, integrity_ready=True, stability_ready=False)
        self.assertEqual(state.current_level, 1)
        self.assertEqual(state.phase_ticks, 0)
        self.assertEqual(state.blocked_reason, "WAIT_STABILITY")

    def test_checkpoint_roundtrip(self):
        pump = self.make_pump()
        for tick in range(1, 9):
            pump.step(queen_tick=tick, integrity_ready=True, stability_ready=True)
        restored = ProgressiveChakraPump.from_checkpoint(copy.deepcopy(pump.to_checkpoint()))
        self.assertEqual(restored.snapshot().to_dict(), pump.snapshot().to_dict())

    def test_payload_keeps_candidate_labels(self):
        payload = self.make_pump().visual_payload()
        self.assertEqual(payload["status"], "CANDIDATE")
        self.assertEqual(payload["authority"], "OBSERVATION_ONLY")
        self.assertFalse(payload["mutates_queen"])
        self.assertFalse(payload["mutates_noyau"])
        self.assertFalse(payload["physical_claim"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
