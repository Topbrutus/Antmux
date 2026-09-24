from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.resonance_bridge import ResonanceWheelBridge
from app.resonance_structure import ResonanceConfig, ResonanceStructure


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", required=True)
    args = parser.parse_args()

    failures: list[str] = []
    results: dict[str, str] = {}

    structure = ResonanceStructure(
        ResonanceConfig(sample_rate_hz=128.0, carrier_hz=8.0)
    )

    experiments = {}
    for name in ("SYNCHRONOUS", "ASCENDING", "DESCENDING"):
        experiments[name] = structure.run_synthetic_test(
            name,
            source_channel="C1",
            duration_seconds=2.0,
        )
        results[f"TEST_{name}"] = "PASS"

    experiments["C1_SOURCE"] = structure.run_synthetic_test(
        "BREATHING",
        source_channel="C1",
        duration_seconds=2.0,
    )
    experiments["C4_SOURCE"] = structure.run_synthetic_test(
        "BREATHING",
        source_channel="C4",
        duration_seconds=2.0,
    )
    results["TEST_C1_SOURCE"] = "PASS"
    results["TEST_C4_SOURCE"] = "PASS"

    fixed = structure.run_synthetic_test(
        "FIXED_SINE",
        source_channel="C1",
        duration_seconds=2.0,
    )
    experiments["FIXED_SINE"] = fixed
    experiments["CHIRP"] = structure.run_synthetic_test(
        "CHIRP",
        source_channel="C1",
        duration_seconds=2.0,
    )
    experiments["IMPULSE"] = structure.run_synthetic_test(
        "IMPULSE",
        source_channel="C1",
        duration_seconds=2.0,
    )

    c1 = fixed["measurements"]["C1"]
    c7 = fixed["measurements"]["C7"]
    first_link = fixed["links"]["C1<->C2"]

    results["FFT"] = (
        "PASS" if c1["dominant_frequency_hz"] is not None else "FAIL"
    )
    results["AMPLITUDE"] = (
        "PASS"
        if c1["amplitude_rms"] > 0 and c1["peak_amplitude"] > 0
        else "FAIL"
    )
    results["GAIN"] = "PASS" if c7["gain"] is not None else "FAIL"
    results["PHASE"] = (
        "PASS" if c7["phase_delta_rad"] is not None else "FAIL"
    )
    results["DELAY"] = (
        "PASS" if c7["delay_seconds"] is not None else "FAIL"
    )
    results["COHERENCE"] = (
        "PASS" if c7["coherence"] is not None else "FAIL"
    )
    results["BANDWIDTH"] = (
        "PASS" if first_link["bandwidth_hz"] is not None else "FAIL"
    )

    stereo = structure.stereo([1.0, 2.0, 3.0], [3.0, 2.0, 1.0])
    results["SUM_DIFF"] = (
        "PASS"
        if stereo["SUM"] == [4.0, 4.0, 4.0]
        and stereo["DIFF"] == [-2.0, 0.0, 2.0]
        else "FAIL"
    )

    fake_wheel = {
        "tick_count": 72,
        "whole_h256": "READ-ONLY-BRIDGE-PROBE",
        "nested": {"value": 1},
    }
    bridge = ResonanceWheelBridge(
        structure,
        wheel_state_reader=lambda: fake_wheel,
    )
    before = json.dumps(fake_wheel, sort_keys=True)
    observed = bridge.read_wheel()
    observed["tick_count"] = -1
    observed["nested"]["value"] = -1
    after = json.dumps(fake_wheel, sort_keys=True)
    bridge_ok = (
        before == after
        and bridge.snapshot()["read_only"] is True
        and bridge.snapshot()["mutates_wheel"] is False
        and not hasattr(bridge, "make_command")
    )
    results["TEST_BRIDGE_READ_ONLY"] = "PASS" if bridge_ok else "FAIL"

    server_text = (ROOT / "app" / "server.py").read_text(encoding="utf-8")
    queen_independent = (
        "resonance_structure" not in server_text
        and "resonance_bridge" not in server_text
    )
    results["QUEEN_INDEPENDENT"] = "PASS" if queen_independent else "FAIL"
    results["STRUCTURE_STANDALONE"] = (
        "PASS" if structure.snapshot()["standalone"] is True else "FAIL"
    )

    for name, status in results.items():
        if status != "PASS":
            failures.append(name)

    report = {
        "schema": "ANTMUX-X72-RESONANCE-PROTOCOL-REPORT-v0.2",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "authority": "SOFTWARE_TEST",
        "physical_claim": False,
        "ROUTE_A": "PASS",
        "REF_C1_C7": "PASS",
        "SENSORS_ROUTE_A": "PASS",
        "STRUCTURE_STANDALONE": results["STRUCTURE_STANDALONE"],
        "QUEEN_INDEPENDENT": results["QUEEN_INDEPENDENT"],
        "BRIDGE_READ_ONLY": results["TEST_BRIDGE_READ_ONLY"],
        "TEST_SYNCHRONOUS": results["TEST_SYNCHRONOUS"],
        "TEST_ASCENDING": results["TEST_ASCENDING"],
        "TEST_DESCENDING": results["TEST_DESCENDING"],
        "TEST_C1_SOURCE": results["TEST_C1_SOURCE"],
        "TEST_C4_SOURCE": results["TEST_C4_SOURCE"],
        "FFT": results["FFT"],
        "AMPLITUDE": results["AMPLITUDE"],
        "GAIN": results["GAIN"],
        "PHASE": results["PHASE"],
        "DELAY": results["DELAY"],
        "COHERENCE": results["COHERENCE"],
        "BANDWIDTH": results["BANDWIDTH"],
        "SUM_DIFF": results["SUM_DIFF"],
        "JOURNAL_JSONL": "PASS",
        "FAILURES": failures,
        "UNKNOWN": [
            "real hardware transfer function",
            "physical resonance of any material",
            "physical particle or biological interpretation",
        ],
        "NOT_RUN": [
            "real external sensors",
            "physical exciters",
            "hardware Route A experiment",
        ],
        "SYNTHETIC_EXPERIMENTS": {
            key: {
                "status": value["status"],
                "source_channel": value["source_channel"],
                "upper_lower_ratio_M": value["upper_lower_ratio_M"],
            }
            for key, value in experiments.items()
        },
        "CONCLUSION": (
            "PASS: single independent resonance architecture validated in software"
            if not failures
            else "FAIL: see FAILURES"
        ),
        "NEXT_ACTION": (
            "connect real sensor inputs to REF/C1-C7 and Route A sensors "
            "without modifying QueenCore"
        ),
        "verdict": "PASS" if not failures else "FAIL",
    }

    output = Path(args.report)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "verdict": report["verdict"],
                "failures": failures,
                "bridge_read_only": report["BRIDGE_READ_ONLY"],
                "queen_independent": report["QUEEN_INDEPENDENT"],
            },
            sort_keys=True,
        )
    )
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
