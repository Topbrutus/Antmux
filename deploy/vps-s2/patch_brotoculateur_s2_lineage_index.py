from __future__ import annotations

import hashlib
import shutil
import sys
from pathlib import Path

PRE_DASH = "7f68744ad3458e77b9b8be74722943f3457318ad58a4c23bf23b793a67d13f6b"
PRE_S1 = "7c08763dc64d7ce7122885b6afc1bc63b9f43a8f90699f5286bf4a6042afe357"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected 1 occurrence, found {count}")
    return text.replace(old, new, 1)


def main(root: Path) -> None:
    pkg = root / "src" / "brotoculateur"
    dash = pkg / "dashboard.py"
    s1 = pkg / "s1_aggregator.py"
    dst = pkg / "s2_lineage_index.py"
    src = Path(__file__).with_name("s2_lineage_index.py")
    if not all(p.is_file() for p in (dash, s1, src)):
        raise RuntimeError("missing dashboard/S1/S2")

    d0 = dash.read_text(encoding="utf-8")
    if dst.is_file() and '"s2_lineage_index": self.s2_lineage_index.status(),' in d0:
        print("S2_PATCH=ALREADY_APPLIED")
        print("DASHBOARD.PY_SHA256=" + sha(dash))
        print("S2_LINEAGE_INDEX.PY_SHA256=" + sha(dst))
        return

    if sha(dash) != PRE_DASH:
        raise RuntimeError("dashboard pre-hash mismatch")
    if sha(s1) != PRE_S1:
        raise RuntimeError("S1 pre-hash mismatch")

    d = d0
    d = replace_once(
        d,
        "from .s1_aggregator import S1AggregatorTelemetry\n",
        "from .s1_aggregator import S1AggregatorTelemetry\nfrom .s2_lineage_index import S2LineageIndexTelemetry\n",
        "import",
    )
    d = replace_once(
        d,
        "        self.s1_aggregator = S1AggregatorTelemetry()\n        self._lock = threading.RLock()\n",
        "        self.s1_aggregator = S1AggregatorTelemetry()\n        self.s2_lineage_index = S2LineageIndexTelemetry()\n        self._lock = threading.RLock()\n",
        "init",
    )
    d = replace_once(
        d,
        "            self.s1_aggregator = S1AggregatorTelemetry()\n            self._session_started_monotonic = None\n",
        "            self.s1_aggregator = S1AggregatorTelemetry()\n            self.s2_lineage_index = S2LineageIndexTelemetry()\n            self._session_started_monotonic = None\n",
        "reset",
    )
    d = replace_once(
        d,
        "        self.s1_aggregator.observe(formula_id, source, out, l5_outcome)\n",
        "        s1_outcome = self.s1_aggregator.observe(formula_id, source, out, l5_outcome)\n        self.s2_lineage_index.observe(formula_id, source, out, s1_outcome)\n",
        "callback",
    )
    d = replace_once(
        d,
        '            "s1_aggregator": self.s1_aggregator.status(),\n',
        '            "s1_aggregator": self.s1_aggregator.status(),\n            "s2_lineage_index": self.s2_lineage_index.status(),\n',
        "status",
    )

    dash.write_text(d, encoding="utf-8", newline="\n")
    shutil.copyfile(src, dst)
    print("S2_PATCH=PASS")
    print("DASHBOARD.PY_SHA256=" + sha(dash))
    print("S1_AGGREGATOR.PY_SHA256=" + sha(s1))
    print("S2_LINEAGE_INDEX.PY_SHA256=" + sha(dst))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
