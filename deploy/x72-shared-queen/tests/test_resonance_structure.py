from __future__ import annotations

import json
import math
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.resonance_structure import (
    ACTIVITY_MEAN_EXACT,
    FOUNDATION_NUMBER,
    LCM_3_7_13,
    ROUTE_A_EDGES,
    ROUTE_A_NODES,
    SEVEN_POW_FOUR,
    ExperimentJournal,
    ResonanceConfig,
    ResonanceStructure,
    SignalAnalyzer,
    SignalGenerator,
    brutus_residue,
    research_constants,
    route_a_payload,
)


class ResonanceStructureTests(unittest.TestCase):
    def test_research_constants_are_exact_and_reference_only(self):
        constants = research_constants()
        self.assertEqual(SEVEN_POW_FOUR, 2401)
        self.assertEqual(LCM_3_7_13, 273)
        self.assertEqual(FOUNDATION_NUMBER, 1203930)
        self.assertAlmostEqual(float(ACTIVITY_MEAN_EXACT), 0.4074285714285714)
        self.assertEqual(constants["usage"], "REFERENCE_ONLY_DO_NOT_FORCE")
        self.assertEqual(brutus_residue(0, 0, 0), 0)
        self.assertTrue(0 <= brutus_residue(3, 7, 13) < 273)

    def test_route_a_encodes_current_brutus_order(self):
        payload = route_a_payload()
        self.assertEqual(payload["first_accumulation"], "MAUVE_A1")
        self.assertEqual(payload["second_accumulation"], "A2")
        self.assertEqual(payload["third_accumulation"], "C3")
        self.assertEqual(payload["mirror_pair"], ["RED_1", "GREEN_1"])
        self.assertIn(("BOTTOM", "MAUVE_A1"), ROUTE_A_EDGES)
        self.assertIn(("RED_1", "GREEN_1"), ROUTE_A_EDGES)
        self.assertIn(("GREEN_1", "A2"), ROUTE_A_EDGES)
        self.assertIn(("RED_2", "BLUE"), ROUTE_A_EDGES)
        self.assertIn(("BLUE", "C3"), ROUTE_A_EDGES)
        self.assertIn(("C3", "BOTTOM_RETURN"), ROUTE_A_EDGES)
        self.assertIn("GROUND_ECHO", ROUTE_A_NODES)
        self.assertEqual(payload["status"], "HYPOTHESIS")
        self.assertFalse(payload["physical_claim"])

    def test_generators_cover_required_test_markers(self):
        cfg = ResonanceConfig(sample_rate_hz=128.0, carrier_hz=8.0)
        gen = SignalGenerator(cfg)
        self.assertEqual(len(gen.sine(128)), 128)
        self.assertEqual(len(gen.impulse(128)), 128)
        self.assertEqual(len(gen.chirp(128, start_hz=2.0, end_hz=30.0)), 128)
        env = gen.breathing_envelope(128)
        self.assertTrue(all(0.0 <= x <= 1.0 for x in env))

    def test_fft_finds_known_frequency(self):
        cfg = ResonanceConfig(sample_rate_hz=128.0, carrier_hz=8.0)
        gen = SignalGenerator(cfg)
        analyzer = SignalAnalyzer(cfg.sample_rate_hz)
        signal = gen.sine(256, frequency_hz=8.0)
        self.assertAlmostEqual(analyzer.dominant_frequency(signal), 8.0, places=6)

    def test_gain_delay_phase_and_coherence_are_measurable(self):
        cfg = ResonanceConfig(sample_rate_hz=128.0, carrier_hz=8.0, max_delay_seconds=0.2)
        gen = SignalGenerator(cfg)
        analyzer = SignalAnalyzer(cfg.sample_rate_hz, cfg.max_delay_seconds)
        ref = gen.chirp(512, start_hz=2.0, end_hz=30.0)
        delay = 4
        out = [0.0] * delay + [0.5 * x for x in ref[:-delay]]
        m = analyzer.analyze(ref, out, "C2")
        self.assertAlmostEqual(m.gain, 0.5, delta=0.02)
        self.assertAlmostEqual(m.delay_seconds, delay / cfg.sample_rate_hz, delta=1 / cfg.sample_rate_hz)
        self.assertIsNotNone(m.phase_delta_rad)
        self.assertIsNotNone(m.coherence)
        self.assertGreater(m.coherence, 0.85)

    def test_bandwidth_is_extracted_from_multitone_transfer(self):
        sr = 128.0
        analyzer = SignalAnalyzer(sr)
        n = 1024
        freqs = [2, 4, 6, 8, 10, 12, 14, 16]
        ref = [sum(math.sin(2 * math.pi * f * i / sr) for f in freqs) for i in range(n)]
        out = [
            sum((1.0 if f <= 10 else 0.1) * math.sin(2 * math.pi * f * i / sr) for f in freqs)
            for i in range(n)
        ]
        low, high, width = analyzer.bandwidth(ref, out)
        self.assertIsNotNone(low)
        self.assertIsNotNone(high)
        self.assertIsNotNone(width)
        self.assertLessEqual(low, 4.0)
        self.assertGreaterEqual(high, 8.0)
        self.assertLess(high, 12.0)

    def test_synchronous_ascending_descending_and_sources(self):
        structure = ResonanceStructure(ResonanceConfig(sample_rate_hz=128.0, carrier_hz=8.0))
        sync = structure.run_synthetic_test("SYNCHRONOUS", source_channel="C1", duration_seconds=2.0)
        asc = structure.run_synthetic_test("ASCENDING", source_channel="C1", duration_seconds=2.0)
        desc = structure.run_synthetic_test("DESCENDING", source_channel="C1", duration_seconds=2.0)
        c4 = structure.run_synthetic_test("BREATHING", source_channel="C4", duration_seconds=2.0)
        for report in (sync, asc, desc, c4):
            self.assertEqual(report["schema"], "ANTMUX-X72-RESONANCE-MEASUREMENT-v0.1")
            self.assertEqual(set(report["measurements"]), {f"C{i}" for i in range(1, 8)})
            self.assertEqual(
                set(report["links"]),
                {f"C{i}<->C{i+1}" for i in range(1, 7)},
            )
            for link in report["links"].values():
                self.assertIsNotNone(link["coherence"])
                self.assertIsNotNone(link["delay_seconds"])
                self.assertIsNotNone(link["phase_delta_rad"])
                self.assertIsNotNone(link["bandwidth_hz"])
            self.assertIsNotNone(report["upper_lower_ratio_M"]["value"])
        self.assertAlmostEqual(c4["measurements"]["C4"]["gain"], 1.0, delta=0.02)
        self.assertAlmostEqual(c4["measurements"]["C4"]["delay_seconds"], 0.0, delta=1/128)
        self.assertNotAlmostEqual(
            asc["measurements"]["C7"]["phase_delta_rad"],
            desc["measurements"]["C7"]["phase_delta_rad"],
            delta=0.05,
        )

    def test_fixed_impulse_and_chirp_protocols(self):
        structure = ResonanceStructure(ResonanceConfig(sample_rate_hz=128.0, carrier_hz=8.0))
        for name in ("FIXED_SINE", "IMPULSE", "CHIRP"):
            report = structure.run_synthetic_test(name, source_channel="C1", duration_seconds=2.0)
            self.assertEqual(report["status"], "MEASURED")
            self.assertEqual(report["input_parameters"]["synthetic_demo"], True)

    def test_stereo_sum_and_diff(self):
        stereo = ResonanceStructure.stereo([1, 2, 3], [3, 2, 1])
        self.assertEqual(stereo["SUM"], [4.0, 4.0, 4.0])
        self.assertEqual(stereo["DIFF"], [-2.0, 0.0, 2.0])

    def test_route_sensors_exist_at_every_node(self):
        structure = ResonanceStructure()
        for index, node in enumerate(ROUTE_A_NODES):
            structure.record_route_sample(node, index / 10)
        payload = structure.snapshot()
        self.assertEqual(set(payload["route_sensors"]), set(ROUTE_A_NODES))
        self.assertTrue(all(v["authority"] == "MEASURED" for v in payload["route_sensors"].values()))

    def test_jsonl_journal_records_complete_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "measurements.jsonl"
            journal = ExperimentJournal(path)
            structure = ResonanceStructure(
                ResonanceConfig(sample_rate_hz=128.0, carrier_hz=8.0),
                journal=journal,
            )
            structure.run_synthetic_test("SYNCHRONOUS", duration_seconds=1.0)
            self.assertEqual(len(journal.records), 1)
            line = json.loads(path.read_text(encoding="utf-8").splitlines()[0])
            self.assertEqual(line["conclusion"], "DATA_ONLY")
            self.assertFalse(line["physical_claim"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
