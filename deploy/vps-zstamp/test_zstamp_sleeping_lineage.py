from __future__ import annotations

import os

from brotoculateur.engine import TracePacket, z_stamp_child, z_stamp_root
from brotoculateur.sleeping_pool import PapillonSleepingPool


def main() -> None:
    os.environ["BROTO_ZSTAMP_ENABLED"] = "1"
    os.environ["BROTO_ZSTAMP_PERCENT"] = "10"

    parent = z_stamp_root(TracePacket(343, packet_id="0123456789abcdef0123456789abcdef"))
    child = z_stamp_child(
        TracePacket(
            344,
            packet_id="fedcba9876543210fedcba9876543210",
            parent_id=parent.packet_id,
            branch_path="ROOT/Y:T",
            depth=1,
            formula_chain=("PLUS1",),
        ),
        parent,
    )

    pool = PapillonSleepingPool()
    pool.add(child, priority=2.5, reason="max_active_branches")
    status = pool.status()
    assert status["exact_z_lineage_preserved"] is True, status
    assert int(status["packed_z_ids"]) == 3, status

    woke = pool.pop_first_wakeable()
    assert woke is not None
    restored, priority = woke
    assert priority == 2.5
    assert restored.value == child.value
    assert restored.packet_id == child.packet_id
    assert restored.parent_id == child.parent_id
    assert restored.branch_path == child.branch_path
    assert restored.formula_chain == child.formula_chain
    assert restored.z_id == child.z_id
    assert restored.z_parent_id == child.z_parent_id
    assert restored.z_origin_id == child.z_origin_id
    print("ZSTAMP_SLEEPING_LINEAGE=PASS", restored.z_id, restored.z_parent_id, restored.z_origin_id)


if __name__ == "__main__":
    main()
