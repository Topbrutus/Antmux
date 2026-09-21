from __future__ import annotations

import math

# ANTMUX v0.2.1 exact cadence basis.
# 2401 = 7^4 is the exact size of the canonical base-7 address space.
BASE7_ADDRESS_SPACE = 7 ** 4
BASE7_CYCLE_SECONDS = 10.0
ENGINE_TARGET_HZ = BASE7_ADDRESS_SPACE / BASE7_CYCLE_SECONDS
DT_SIM_SECONDS = 1.0 / ENGINE_TARGET_HZ

# Scheduler granularity is implementation timing, not the simulation cadence.
SCHEDULER_SLEEP_SECONDS = 0.005

# ANTMUX v0.2.2 candidate observation clocks.
# These values already exist in the runtime. They are collected here only to
# measure exact simultaneous tick boundaries; this module does not mutate them.
SYNC_CLOCKS_TICKS = {
    "relation_sample": 60,
    "z3_sample": 60,
    "z3_frame": 240,
    "mode_event": 360,
    "mode_cycle": 1800,
    "generation": 7200,
}
BRUTUS_CALIBRATION_SCHEMA = "ANTMUX-X72-BRUTUS-CALIBRATION-v0.1"


def _alignment_ticks(period_ticks: int) -> int:
    return math.lcm(BASE7_ADDRESS_SPACE, int(period_ticks))


def synchronization_contract() -> dict[str, object]:
    clocks: dict[str, object] = {}
    for name, period_ticks in SYNC_CLOCKS_TICKS.items():
        common_ticks = _alignment_ticks(period_ticks)
        clocks[name] = {
            "period_ticks": period_ticks,
            "alignment_ticks": common_ticks,
            "alignment_seconds": common_ticks / ENGINE_TARGET_HZ,
        }

    full_alignment_ticks = math.lcm(
        BASE7_ADDRESS_SPACE,
        *SYNC_CLOCKS_TICKS.values(),
    )
    return {
        "schema": "ANTMUX-X72-2401-SYNC-v0.1",
        "status": "CANDIDATE_OBSERVATION_ONLY",
        "base_cycle_ticks": BASE7_ADDRESS_SPACE,
        "base_cycle_seconds": BASE7_CYCLE_SECONDS,
        "clocks": clocks,
        "full_alignment_ticks": full_alignment_ticks,
        "full_alignment_seconds": full_alignment_ticks / ENGINE_TARGET_HZ,
    }


def synchronization_state(tick: int) -> dict[str, object]:
    tick = int(tick)
    contract = synchronization_contract()
    state: dict[str, object] = {}
    for name, item in contract["clocks"].items():
        alignment_ticks = int(item["alignment_ticks"])
        remainder = tick % alignment_ticks
        ticks_to_next = 0 if remainder == 0 else alignment_ticks - remainder
        state[name] = {
            "aligned_now": remainder == 0,
            "alignment_ticks": alignment_ticks,
            "ticks_to_next": ticks_to_next,
            "seconds_to_next": ticks_to_next / ENGINE_TARGET_HZ,
        }

    full_ticks = int(contract["full_alignment_ticks"])
    full_remainder = tick % full_ticks
    full_to_next = 0 if full_remainder == 0 else full_ticks - full_remainder
    return {
        "tick": tick,
        "clocks": state,
        "full_alignment": {
            "aligned_now": full_remainder == 0,
            "alignment_ticks": full_ticks,
            "ticks_to_next": full_to_next,
            "seconds_to_next": full_to_next / ENGINE_TARGET_HZ,
        },
    }


def brutus_calibration(measured_hz: float) -> dict[str, object]:
    measured_hz = float(measured_hz)
    if not math.isfinite(measured_hz):
        raise ValueError("measured_hz must be finite")

    if measured_hz <= 0.0:
        return {
            "schema": BRUTUS_CALIBRATION_SCHEMA,
            "status": "INSUFFICIENT_SAMPLE",
            "target_hz": ENGINE_TARGET_HZ,
            "measured_hz": measured_hz,
            "k_b": None,
            "correction_ppm": None,
            "frequency_error_ppm": None,
        }

    k_b = ENGINE_TARGET_HZ / measured_hz
    return {
        "schema": BRUTUS_CALIBRATION_SCHEMA,
        "status": "CANDIDATE_OBSERVATION_ONLY",
        "target_hz": ENGINE_TARGET_HZ,
        "measured_hz": measured_hz,
        "k_b": k_b,
        "correction_ppm": (k_b - 1.0) * 1_000_000.0,
        "frequency_error_ppm": ((measured_hz - ENGINE_TARGET_HZ) / ENGINE_TARGET_HZ)
        * 1_000_000.0,
    }


def timing_contract() -> dict[str, object]:
    return {
        "address_space": BASE7_ADDRESS_SPACE,
        "cycle_seconds": BASE7_CYCLE_SECONDS,
        "target_hz": ENGINE_TARGET_HZ,
        "dt_sim_seconds": DT_SIM_SECONDS,
        "basis": "7^4 / 10 s",
        "synchronization": synchronization_contract(),
    }
