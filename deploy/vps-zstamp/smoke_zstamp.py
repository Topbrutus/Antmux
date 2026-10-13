from __future__ import annotations

import hashlib
import os
from brotoculateur.engine import Formula, FormulaRegistry, TracePacket
from brotoculateur.orchestrator import ExperimentRunner, ExperimentSpec


def legacy_hash(packet: TracePacket) -> str:
    raw = f"{packet.value}|{packet.packet_id}|{packet.parent_id}|{packet.branch_path}|{packet.depth}|{packet.formula_chain}|{packet.state.value}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def registry() -> FormulaRegistry:
    reg = FormulaRegistry()
    reg.register(Formula("PLUS1", "x+1", "plus", lambda x: x + 1))
    return reg

def test_disabled() -> None:
    os.environ["BROTO_ZSTAMP_ENABLED"] = "0"
    os.environ["BROTO_ZSTAMP_PERCENT"] = "0"
    packet = TracePacket(703, packet_id="fixed", branch_path="ROOT")
    assert packet.state_hash == legacy_hash(packet)
    runner = ExperimentRunner(registry(), ExperimentSpec(max_depth=2, max_active_branches=16, max_packets=100))
    runner.seed([packet])
    runner.run_steps(1)
    status = runner.zstamp_status()
    assert status["root_selected"] == 0
    assert status["children_stamped"] == 0
    assert all(item[2].packet.z_id is None for item in runner._queue)
    print("ZSTAMP_DISABLED_COMPAT=PASS")

def test_canary() -> None:
    os.environ["BROTO_ZSTAMP_ENABLED"] = "1"
    os.environ["BROTO_ZSTAMP_PERCENT"] = "10"
    runner = ExperimentRunner(registry(), ExperimentSpec(max_depth=1, max_active_branches=32, max_packets=100))
    values = [343, 703, 2701, 6337, 11611]
    runner.seed([TracePacket(v, packet_id=f"p{v}") for v in values])
    rows = sorted((item[2].packet.value, item[2].packet.z_id is not None) for item in runner._queue)
    print("CANARY_ROWS=" + repr(rows))
    assert rows == [(343, False), (703, False), (2701, False), (6337, True), (11611, False)]
    assert runner.zstamp_status()["root_selected"] == 1
    print("ZSTAMP_CANARY_10=PASS")


if __name__ == "__main__":
    test_disabled()
    test_canary()
