import json
import math
import unittest

from noyau_engine import CENTER_GATES, DOWN_ROUTE, SCHEMA, UP_ROUTE, NoyauEngine
from server_adapter import ADAPTER_SCHEMA, NoyauServerAdapter


class NoyauEngineTests(unittest.TestCase):
    def test_routes_pass_through_all_centers(self):
        self.assertEqual(UP_ROUTE, ("SOURCE", "C1", "C2", "C3", "SORTIE"))
        self.assertEqual(DOWN_ROUTE, ("SORTIE", "C3", "C2", "C1", "SOURCE"))
        for gate in CENTER_GATES:
            self.assertIn(gate, UP_ROUTE)
            self.assertIn(gate, DOWN_ROUTE)

    def test_state_is_serializable_and_hashed(self):
        engine = NoyauEngine()
        state = engine.step(8)
        self.assertEqual(state.schema, SCHEMA)
        self.assertTrue(NoyauEngine.verify_state(state))
        encoded = json.dumps(state.to_dict(), sort_keys=True, allow_nan=False)
        self.assertIn(state.whole_h256, encoded)
        self.assertEqual(len(state.whole_h256), 64)

    def test_counter_rotation_is_opposed(self):
        engine = NoyauEngine()
        state = engine.step()
        phase_sum = (state.phase_left + state.phase_right) % (2.0 * math.pi)
        self.assertLess(min(abs(phase_sum), abs(phase_sum - 2.0 * math.pi)), 1e-8)

    def test_injection_raises_basin_input(self):
        base = NoyauEngine()
        injected = NoyauEngine()
        base_state = base.step()
        injected.inject(1.15)
        injected_state = injected.step()
        self.assertGreater(injected_state.basin1.inflow, base_state.basin1.inflow)

    def test_interception_reduces_basin_output(self):
        base = NoyauEngine()
        intercepted = NoyauEngine()
        base_state = base.step()
        intercepted.intercept(0.50)
        intercepted_state = intercepted.step()
        self.assertLess(intercepted_state.basin1.outflow, base_state.basin1.outflow)

    def test_world_switch_is_explicit(self):
        engine = NoyauEngine()
        engine.switch_world(3)
        state = engine.step()
        self.assertEqual(state.world_index, 3)
        self.assertEqual(state.world_name, "OBSIDIAN")
        with self.assertRaises(ValueError):
            engine.switch_world(4)

    def test_deterministic_same_commands_same_hash(self):
        a = NoyauEngine()
        b = NoyauEngine()
        a.inject(0.7)
        b.inject(0.7)
        a.set_feedback(0.42)
        b.set_feedback(0.42)
        sa = a.step(30)
        sb = b.step(30)
        self.assertEqual(sa.to_dict(), sb.to_dict())
        self.assertEqual(sa.whole_h256, sb.whole_h256)

    def test_snapshot_is_not_alias(self):
        engine = NoyauEngine()
        state = engine.step(5)
        snap = engine.snapshot()
        snap.node_signals["B1"] = 999.0
        self.assertNotEqual(engine.snapshot().node_signals["B1"], 999.0)
        self.assertEqual(state.whole_h256, engine.snapshot().whole_h256)

    def test_cold_snapshot_does_not_advance_engine(self):
        engine = NoyauEngine()
        before = engine.to_checkpoint()
        first = engine.snapshot()
        second = engine.snapshot()
        after = engine.to_checkpoint()
        self.assertEqual(first.tick, 0)
        self.assertEqual(second.tick, 0)
        self.assertEqual(first.to_dict(), second.to_dict())
        self.assertEqual(before, after)

    def test_adapter_contract(self):
        adapter = NoyauServerAdapter()
        adapter.tick(3)
        payload = adapter.visual_payload()
        self.assertEqual(payload["schema"], ADAPTER_SCHEMA)
        self.assertEqual(payload["authority"], "NOYAU_ENGINE_HEADLESS")
        self.assertIn("noyau", payload)
        self.assertTrue(payload["noyau"]["whole_h256"])

    def test_engine_checkpoint_roundtrip_and_continuation(self):
        original = NoyauEngine()
        original.inject(0.8)
        original.set_feedback(0.44)
        original.switch_world(2)
        before = original.step(40)
        restored = NoyauEngine.from_checkpoint(original.to_checkpoint())
        self.assertEqual(before.to_dict(), restored.snapshot().to_dict())
        self.assertEqual(original.step(25).to_dict(), restored.step(25).to_dict())

    def test_corrupt_checkpoint_state_is_rejected(self):
        engine = NoyauEngine()
        engine.step(5)
        checkpoint = engine.to_checkpoint()
        checkpoint["last_state"]["whole_h256"] = "0" * 64
        with self.assertRaises(ValueError):
            NoyauEngine.from_checkpoint(checkpoint)

    def test_adapter_checkpoint_roundtrip(self):
        adapter = NoyauServerAdapter()
        adapter.tick(12)
        restored = NoyauServerAdapter.from_checkpoint(adapter.to_checkpoint())
        self.assertEqual(
            adapter.visual_payload()["noyau"],
            restored.visual_payload()["noyau"],
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)

[executed on device: Topbrutus (e13fd46c-c560-41e2-9c1c-bd2561c44abb)]