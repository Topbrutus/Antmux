from __future__ import annotations

import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.server import QueenCore, SERVER_VERSION, observability_snapshot
from app.timing import BASE7_ADDRESS_SPACE, BASE7_CYCLE_SECONDS, DT_SIM_SECONDS, ENGINE_TARGET_HZ


def run() -> None:
    assert SERVER_VERSION == "0.2.1"
    assert BASE7_ADDRESS_SPACE == 2401
    assert ENGINE_TARGET_HZ == 240.1
    assert math.isclose(DT_SIM_SECONDS, 10.0 / 2401.0, rel_tol=0.0, abs_tol=1e-15)

    queen = QueenCore(seed=72)
    for _ in range(BASE7_ADDRESS_SPACE):
        queen.step()
    assert queen.tick == 2401
    assert math.isclose(queen.sim_time, BASE7_CYCLE_SECONDS, rel_tol=0.0, abs_tol=1e-10)

    # v0.2.1 changes engine cadence, not historical logical tick contracts.
    assert queen.generation == 0
    for _ in range(7200 - BASE7_ADDRESS_SPACE):
        queen.step()
    assert queen.tick == 7200
    assert queen.generation == 1

    contract = observability_snapshot()["timing_contract"]
    assert contract["address_space"] == 2401
    assert contract["target_hz"] == 240.1
    assert contract["basis"] == "7^4 / 10 s"


if __name__ == "__main__":
    run()
