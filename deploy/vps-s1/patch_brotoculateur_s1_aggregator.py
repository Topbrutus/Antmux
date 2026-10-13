from __future__ import annotations

import hashlib
import shutil
import sys
from pathlib import Path

PRE_DASH = "f2854516dcff8ff606870c101f6517fda091bf24fb3d9273d4891c59c2533192"
PRE_L5 = "cd1d0fa824ddf753c5471d7c8c2d04211f364a3b411ae55a57dc25a653e0e55d"


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
    l5 = pkg / "l5_placement.py"
    dst = pkg / "s1_aggregator.py"
    src = Path(__file__).with_name("s1_aggregator.py")
    if not all(p.is_file() for p in (dash, l5, src)):
        raise RuntimeError("missing dashboard/L5/S1")

    d0 = dash.read_text(encoding="utf-8")
    if dst.is_file() and '"s1_aggregator": self.s1_aggregator.status(),' in d0:
        print("S1_PATCH=ALREADY_APPLIED")
        print("DASHBOARD.PY_SHA256=" + sha(dash))
        print("S1_AGGREGATOR.PY_SHA256=" + sha(dst))
        return

    if sha(dash) != PRE_DASH:
        raise RuntimeError("dashboard pre-hash mismatch")
    if sha(l5) != PRE_L5:
        raise RuntimeError("L5 pre-hash mismatch")

    d = d0
    d = replace_once(
        d,
        "from .l5_placement import L5PlacementTelemetry\n",
        "from .l5_placement import L5PlacementTelemetry\nfrom .s1_aggregator import S1AggregatorTelemetry\n",
        "import",
    )
    d = replace_once(
        d,
        "        self.l5_placement = L5PlacementTelemetry()\n        self._lock = threading.RLock()\n",
        "        self.l5_placement = L5PlacementTelemetry()\n        self.s1_aggregator = S1AggregatorTelemetry()\n        self._lock = threading.RLock()\n",
        "init",
    )
    d = replace_once(
        d,
        "            self.l5_placement = L5PlacementTelemetry()\n            self._session_started_monotonic = None\n",
        "            self.l5_placement = L5PlacementTelemetry()\n            self.s1_aggregator = S1AggregatorTelemetry()\n            self._session_started_monotonic = None\n",
        "reset",
    )
    old = "        self.l5_placement.observe(formula_id, source, out, l4_outcome)\n"
    new = "        l5_outcome = self.l5_placement.observe(formula_id, source, out, l4_outcome)\n        self.s1_aggregator.observe(formula_id, source, out, l5_outcome)\n"
    d = replace_once(d, old, new, "callback")
    d = replace_once(
        d,
        '            "l5_placement": self.l5_placement.status(),\n',
        '            "l5_placement": self.l5_placement.status(),\n            "s1_aggregator": self.s1_aggregator.status(),\n',
        "status",
    )

    dash.write_text(d, encoding="utf-8", newline="\n")
    shutil.copyfile(src, dst)
    print("S1_PATCH=PASS")
    print("DASHBOARD.PY_SHA256=" + sha(dash))
    print("L5_PLACEMENT.PY_SHA256=" + sha(l5))
    print("S1_AGGREGATOR.PY_SHA256=" + sha(dst))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
