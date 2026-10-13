from __future__ import annotations

import os
from dataclasses import asdict, replace

from brotoculateur.engine import (
    Formula,
    FormulaRegistry,
    TracePacket,
    c2_fingerprint,
    z_stamp_child,
    z_stamp_root,
)
from brotoculateur.orchestrator import ExperimentRunner, ExperimentSpec


def registry() -> FormulaRegistry:
    reg = FormulaRegistry()
    reg.register(Formula("PLUS1", "x+1", "plus", lambda x: x + 1))
    return reg


def semantic_packet() -> TracePacket:
    parent = z_stamp_root(TracePacket(343, packet_id="root-fixed"))
    child = TracePacket(
        344,
        packet_id="child-a",
        parent_id=parent.packet_id,
        branch_path="ROOT/Y:T",
        depth=2,
        formula_chain=("PLUS1",),
    )
    return z_stamp_child(child, parent)


def main() -> None:
    packet = semantic_packet()
    before = asdict(packet)
    fp = c2_fingerprint(packet)
    assert fp.startswith("C2-") and len(fp) == 67, fp
    assert asdict(packet) == before

    # Volatile physical provenance changes do not change the canonical C2 identity.
    physical_twin = replace(
        packet,
        packet_id="child-b",
        parent_id="another-physical-parent",
        branch_path="ROOT/Y:E",
    )
    assert physical_twin.state_hash != packet.state_hash
    assert c2_fingerprint(physical_twin) == fp

    # Semantic / Z-lineage fields do change C2.
    assert c2_fingerprint(replace(packet, value=345)) != fp
    assert c2_fingerprint(replace(packet, depth=3)) != fp
    assert c2_fingerprint(replace(packet, formula_chain=("DOUBLE",))) != fp
    assert c2_fingerprint(replace(packet, z_parent_id="Z-" + "0" * 32)) != fp
    assert c2_fingerprint(replace(packet, z_origin_id="Z-" + "1" * 32)) != fp

    os.environ["BROTO_ZSTAMP_ENABLED"] = "1"
    os.environ["BROTO_ZSTAMP_PERCENT"] = "100"
    os.environ["BROTO_C2_ENABLED"] = "0"
    off = ExperimentRunner(
        registry(),
        ExperimentSpec(max_depth=2, max_active_branches=16, max_packets=100),
        papillon_enabled=False,
    )
    off.seed([TracePacket(343)])
    off.run_steps(1)
    off_status = off.c2_status()
    assert off_status["fingerprints"] == 0

    os.environ["BROTO_C2_ENABLED"] = "1"
    on = ExperimentRunner(
        registry(),
        ExperimentSpec(max_depth=2, max_active_branches=16, max_packets=100),
        papillon_enabled=False,
    )
    on.seed([TracePacket(343)])
    seeded = on.c2_status()
    assert seeded["roots_fingerprinted"] == 1, seeded
    assert seeded["children_fingerprinted"] == 0, seeded
    on.run_steps(1)
    live = on.c2_status()
    assert live["roots_fingerprinted"] == 1, live
    assert live["children_fingerprinted"] > 0, live
    assert live["materialized_on_packet"] is False
    assert live["c2_changes_state_hash"] is False
    assert live["value_mutated"] is False
    os.environ["BROTO_ZSTAMP_PERCENT"] = "10"
    canary = ExperimentRunner(
        registry(),
        ExperimentSpec(max_depth=2, max_active_branches=32, max_packets=200),
        papillon_enabled=False,
    )
    canary.seed([TracePacket(v, packet_id=f"seed-{v}") for v in (343, 703, 2701, 6337, 11611)])
    z_status = canary.zstamp_status()
    c2_seeded = canary.c2_status()
    assert z_status["root_selected"] == 1, z_status
    assert c2_seeded["roots_fingerprinted"] == 1, c2_seeded
    canary.run_steps(1)
    c2_canary = canary.c2_status()
    assert c2_canary["children_fingerprinted"] > 0, c2_canary
    print("C2_CANARY_10=PASS", c2_canary["roots_fingerprinted"], c2_canary["children_fingerprinted"])

    print("C2_FINGERPRINT=PASS", fp, live["fingerprints"])


if __name__ == "__main__":
    main()
