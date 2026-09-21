from __future__ import annotations

# ANTMUX v0.2.1 cadence correction.
# 2401 = 7^4 is the exact size of the canonical base-7 address space.
BASE7_ADDRESS_SPACE = 7 ** 4
BASE7_CYCLE_SECONDS = 10.0
ENGINE_TARGET_HZ = BASE7_ADDRESS_SPACE / BASE7_CYCLE_SECONDS
DT_SIM_SECONDS = 1.0 / ENGINE_TARGET_HZ

# Scheduler granularity is implementation timing, not the simulation cadence.
SCHEDULER_SLEEP_SECONDS = 0.005


def timing_contract() -> dict[str, float | int | str]:
    return {
        "address_space": BASE7_ADDRESS_SPACE,
        "cycle_seconds": BASE7_CYCLE_SECONDS,
        "target_hz": ENGINE_TARGET_HZ,
        "dt_sim_seconds": DT_SIM_SECONDS,
        "basis": "7^4 / 10 s",
    }
