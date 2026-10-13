from __future__ import annotations

import hashlib
import shutil
import sys
from pathlib import Path

PRE_DASH = "4476ae0d83542226a1c37ab1b069a11a59d106f8e8ee0807b697ddc9e0f67bb0"
PRE_L4 = "9f8ff4d83cec6721eefe0a04bfd333861d47e7e10b17a85dec2dcaf1b9dc336d"


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
    l4 = pkg / "l4_canon.py"
    dst = pkg / "l5_placement.py"
    src = Path(__file__).with_name("l5_placement.py")
    if not all(p.is_file() for p in (dash, l4, src)):
        raise RuntimeError("missing dashboard/L4/L5")

    d0 = dash.read_text(encoding="utf-8")
    if dst.is_file() and '"l5_placement": self.l5_placement.status(),' in d0:
        print("L5_PATCH=ALREADY_APPLIED")
        print("DASHBOARD.PY_SHA256=" + sha(dash))
        print("L5_PLACEMENT.PY_SHA256=" + sha(dst))
        return

    if sha(dash) != PRE_DASH:
        raise RuntimeError("dashboard pre-hash mismatch")
    if sha(l4) != PRE_L4:
        raise RuntimeError("L4 pre-hash mismatch")

    d = d0
    d = replace_once(
        d,
        "from .l4_canon import L4CanonTelemetry\n",
        "from .l4_canon import L4CanonTelemetry\nfrom .l5_placement import L5PlacementTelemetry\n",
        "import",
    )
    d = replace_once(
        d,
        "        self.l4_canon = L4CanonTelemetry()\n        self._lock = threading.RLock()\n",
        "        self.l4_canon = L4CanonTelemetry()\n        self.l5_placement = L5PlacementTelemetry()\n        self._lock = threading.RLock()\n",
        "init",
    )
    d = replace_once(
        d,
        "            self.l4_canon = L4CanonTelemetry()\n            self._session_started_monotonic = None\n",
        "            self.l4_canon = L4CanonTelemetry()\n            self.l5_placement = L5PlacementTelemetry()\n            self._session_started_monotonic = None\n",
        "reset",
    )
    old = "        self.l4_canon.observe(formula_id, source, out, l3_outcome)\n"
    new = "        l4_outcome = self.l4_canon.observe(formula_id, source, out, l3_outcome)\n        self.l5_placement.observe(formula_id, source, out, l4_outcome)\n"
    d = replace_once(d, old, new, "callback")
    d = replace_once(
        d,
        '            "l4_canon": self.l4_canon.status(),\n',
        '            "l4_canon": self.l4_canon.status(),\n            "l5_placement": self.l5_placement.status(),\n',
        "status",
    )

    dash.write_text(d, encoding="utf-8", newline="\n")
    shutil.copyfile(src, dst)
    print("L5_PATCH=PASS")
    print("DASHBOARD.PY_SHA256=" + sha(dash))
    print("L4_CANON.PY_SHA256=" + sha(l4))
    print("L5_PLACEMENT.PY_SHA256=" + sha(dst))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
