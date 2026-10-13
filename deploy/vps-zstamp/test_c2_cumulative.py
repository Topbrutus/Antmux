from __future__ import annotations

import os
import tempfile
from pathlib import Path

from brotoculateur.dashboard import DashboardService
from brotoculateur.orchestrator import ExperimentSpec


def main() -> None:
    os.environ["BROTO_ZSTAMP_ENABLED"] = "1"
    os.environ["BROTO_ZSTAMP_PERCENT"] = "100"
    os.environ["BROTO_C2_ENABLED"] = "1"
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        service = DashboardService(
            Path(tmp) / "store",
            spec=ExperimentSpec(duration_seconds=60, max_depth=2, max_active_branches=32, max_packets=300),
            tick_seconds=0.01,
            sleeping_pool_enabled=True,
        )
        try:
            service.reset((343,))
            service.step(1)
            before = service.status()["c2_fingerprint"]
            assert int(before["total_roots_fingerprinted"]) == 1, before
            assert int(before["total_children_fingerprinted"]) > 0, before
            saved_children = int(before["total_children_fingerprinted"])
            saved_first = before["session_first_fingerprint"]
            with service._lock:
                service._c2_rollup_unlocked()
                service._zstamp_rollup_unlocked()
                service._runner = service._new_runner((703,))
            after = service.status()["c2_fingerprint"]
            assert int(after["children_fingerprinted"]) == 0, after
            assert int(after["total_children_fingerprinted"]) >= saved_children, after
            assert after["session_first_fingerprint"] == saved_first, after
            assert after["cumulative_across_rounds"] is True
            print(
                "C2_CUMULATIVE=PASS",
                saved_children,
                after["total_children_fingerprinted"],
                after["session_first_fingerprint"],
            )
        finally:
            service.close()


if __name__ == "__main__":
    main()
