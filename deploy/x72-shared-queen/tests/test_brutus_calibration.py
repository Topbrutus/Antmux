from __future__ import annotations

import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.server import QueenCore, SERVER_VERSION
from app.timing import (
    ENGINE_TARGET_HZ,
    brutus_calibration,
    synchronization_contract,
    synchronization_state,
)


def run() -> None:
    assert SERVER_VERSION == "0.2.2-rc1"
    assert ENGINE_TARGET_HZ == 240.1

    exact = brutus_calibration(240.1)
    assert exact["k_b"] == 1.0
    assert exact["correction_ppm"] == 0.0
    assert exact["status"] == "CANDIDATE_OBSERVATION_ONLY"

    measured = brutus_calibration(240.0949154444952)
    assert math.isclose(measured["k_b"], 1.000021177371603, abs_tol=1e-15)
    assert measured["correction_ppm"] > 0.0

    sync = synchronization_contract()
    clocks = sync["clocks"]
    assert clocks["relation_sample"]["alignment_seconds"] == 600.0
    assert clocks["z3_sample"]["alignment_seconds"] == 600.0
    assert clocks["z3_frame"]["alignment_seconds"] == 2400.0
    assert clocks["mode_event"]["alignment_seconds"] == 3600.0
    assert clocks["mode_cycle"]["alignment_seconds"] == 18000.0
    assert clocks["generation"]["alignment_seconds"] == 72000.0
    assert sync["full_alignment_seconds"] == 72000.0
    assert sync["full_alignment_ticks"] == 17287200

    # Exactly one hour at 240.1 Hz = 864,360 ticks.
    hour = synchronization_state(864360)
    assert hour["clocks"]["relation_sample"]["aligned_now"] is True
    assert hour["clocks"]["z3_sample"]["aligned_now"] is True
    assert hour["clocks"]["mode_event"]["aligned_now"] is True
    assert hour["clocks"]["z3_frame"]["aligned_now"] is False
    assert hour["full_alignment"]["aligned_now"] is False

    # At 40 minutes the 2401 cycle, Z3 sample, and Z3 frame coincide.
    forty_minutes = synchronization_state(576240)
    assert forty_minutes["clocks"]["relation_sample"]["aligned_now"] is True
    assert forty_minutes["clocks"]["z3_sample"]["aligned_now"] is True
    assert forty_minutes["clocks"]["z3_frame"]["aligned_now"] is True

    queen = QueenCore(seed=72)
    visual = queen.visual_state()
    assert visual["brutus_calibration"]["status"] == "INSUFFICIENT_SAMPLE"
    assert "brutus_sync" in visual

    for _ in range(60):
        queen.step()
    visual = queen.visual_state()
    assert visual["brutus_calibration"]["status"] == "CANDIDATE_OBSERVATION_ONLY"


if __name__ == "__main__":
    run()
