from __future__ import annotations

import os
import tempfile
from pathlib import Path

from brotoculateur.dashboard import DashboardService
from brotoculateur.orchestrator import ExperimentSpec


def main() -> None:
    os.environ["BROTO_ZSTAMP_ENABLED"] = "1"
    os.environ["BROTO_ZSTAMP_PERCENT"] = "10"
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        spec = ExperimentSpec(duration_seconds=60, max_depth=2, max_active_branches=32, max_packets=300)
        service = DashboardService(
            Path(tmp) / "store",
            spec=spec,
            tick_seconds=0.01,
            sleeping_pool_enabled=True,
        )
        try:
            service.reset((343, 703, 2701, 6337, 11611))
            service.step(1)
            before = service.status()["brutus_cortex"]
            assert int(before["total_root_selected"]) == 1, before
            assert int(before["children_stamped"]) > 0, before
            assert int(before["total_children_stamped"]) > 0, before
            saved_total = int(before["total_children_stamped"])
            with service._lock:
                service._zstamp_rollup_unlocked()
                service._runner = service._new_runner((703,))
            after = service.status()["brutus_cortex"]
            assert int(after["children_stamped"]) == 0, after
            assert int(after["total_children_stamped"]) >= saved_total, after
            assert after["cumulative_across_rounds"] is True
            print("ZSTAMP_CUMULATIVE=PASS", saved_total, after["total_children_stamped"])
        finally:
            service.close()


if __name__ == "__main__":
    main()
