from __future__ import annotations

import copy
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ["ANTMUX_X72_DATA_DIR"] = tempfile.mkdtemp(prefix="antmux-x72-chakra-pump-test-")

from app.chakra_pump import ChakraPumpConfig, ProgressiveChakraPump
from app.server import QueenCore


class ProgressiveChakraPumpTests(unittest.TestCase):
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
        self.assertAlmostEqual(s2.retained_boost, 0.2)

        states = []
        for tick in range(3, 7):
            states.append(
                pump.step(
                    queen_tick=tick,
                    integrity_ready=True,
                    stability_ready=True,
                )
            )
        self.assertEqual(
            [(s.current_level, s.direction) for s in states],
            [(2, "UP"), (3, "DOWN"), (2, "DOWN"), (1, "UP")],
        )
        self.assertEqual(states[-1].target_level, 4)
        self.assertEqual(states[-1].completed_cycles, 2)
        self.assertAlmostEqual(states[-1].retained_boost, 0.4)

    def test_progression_reaches_seven_then_repeats_without_overflow(self):
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
        cycles_before = pump.completed_cycles

        for _ in range(12):
            tick += 1
            pump.step(queen_tick=tick, integrity_ready=True, stability_ready=True)

        self.assertEqual(pump.target_level, 7)
        self.assertEqual(pump.current_level, 1)
        self.assertEqual(pump.completed_cycles, cycles_before + 1)
        self.assertAlmostEqual(pump.retained_boost, 1.0)

    def test_stability_gate_blocks_progress_without_accumulation(self):
        pump = ProgressiveChakraPump(ChakraPumpConfig(ticks_per_level=3))
        for tick in range(1, 20):
            state = pump.step(
                queen_tick=tick,
                integrity_ready=True,
                stability_ready=False,
            )
        self.assertEqual(state.current_level, 1)
        self.assertEqual(state.phase_ticks, 0)
        self.assertEqual(state.blocked_reason, "WAIT_STABILITY")

        pump.step(queen_tick=20, integrity_ready=True, stability_ready=True)
        pump.step(queen_tick=21, integrity_ready=True, stability_ready=True)
        state = pump.step(queen_tick=22, integrity_ready=True, stability_ready=True)
        self.assertEqual(state.current_level, 2)
        self.assertEqual(state.direction, "DOWN")

    def test_integrity_gate_has_priority(self):
        pump = self.make_pump()
        state = pump.step(
            queen_tick=1,
            integrity_ready=False,
            stability_ready=True,
        )
        self.assertEqual(state.current_level, 1)
        self.assertEqual(state.blocked_reason, "WAIT_INTEGRITY")

    def test_checkpoint_roundtrip_and_continuation(self):
        pump = self.make_pump()
        for tick in range(1, 9):
            pump.step(queen_tick=tick, integrity_ready=True, stability_ready=True)

        restored = ProgressiveChakraPump.from_checkpoint(
            copy.deepcopy(pump.to_checkpoint())
        )
        self.assertEqual(restored.snapshot().to_dict(), pump.snapshot().to_dict())

        expected = pump.step(
            queen_tick=9,
            integrity_ready=True,
            stability_ready=True,
        )
        actual = restored.step(
            queen_tick=9,
            integrity_ready=True,
            stability_ready=True,
        )
        self.assertEqual(actual.to_dict(), expected.to_dict())

    def test_corrupt_checkpoint_is_rejected(self):
        pump = self.make_pump()
        pump.step(queen_tick=1, integrity_ready=True, stability_ready=True)
        checkpoint = pump.to_checkpoint()
        checkpoint["state"]["current_level"] = 99
        with self.assertRaises(ValueError):
            ProgressiveChakraPump.from_checkpoint(checkpoint)

    def test_payload_declares_candidate_observation_only(self):
        payload = self.make_pump().visual_payload()
        self.assertEqual(payload["status"], "CANDIDATE")
        self.assertEqual(payload["authority"], "OBSERVATION_ONLY")
        self.assertFalse(payload["mutates_queen"])
        self.assertFalse(payload["mutates_noyau"])
        self.assertFalse(payload["physical_claim"])


class ChakraPumpQueenMountTests(unittest.TestCase):
    def test_mount_is_visible_checkpointed_and_hash_neutral(self):
        queen = QueenCore(seed=72)
        initial = queen.visual_state()["chakra_pump"]
        self.assertEqual(initial["state"]["current_level"], 1)
        self.assertEqual(initial["state"]["target_level"], 2)
        self.assertEqual(initial["state"]["blocked_reason"], "WAIT_STABILITY")

        stable_seen = False
        progressed_seen = False
        for _ in range(800):
            queen.step()
            pump_state = queen.visual_state()["chakra_pump"]["state"]
            stable_seen = stable_seen or pump_state["stability_ready"]
            progressed_seen = progressed_seen or pump_state["current_level"] > 1
            if stable_seen and progressed_seen:
                break

        self.assertTrue(stable_seen)
        self.assertTrue(progressed_seen)

        before_hash = queen.whole_h256()
        checkpoint = queen.to_checkpoint()
        restored = QueenCore.from_checkpoint(copy.deepcopy(checkpoint))

        self.assertEqual(
            restored.visual_state()["chakra_pump"],
            queen.visual_state()["chakra_pump"],
        )
        self.assertEqual(restored.whole_h256(), before_hash)

        legacy = copy.deepcopy(checkpoint)
        legacy.pop("chakra_pump", None)
        legacy_restored = QueenCore.from_checkpoint(legacy)
        legacy_state = legacy_restored.visual_state()["chakra_pump"]["state"]
        self.assertEqual(legacy_state["current_level"], 1)
        self.assertEqual(legacy_state["target_level"], 2)
        self.assertEqual(legacy_state["queen_tick"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
