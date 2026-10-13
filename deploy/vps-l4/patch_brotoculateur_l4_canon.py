from __future__ import annotations

import hashlib
import shutil
import sys
from pathlib import Path

PRE_DASH = "b00131bb87a21ffb55baec337e809fcdf39c03d3498d63f1690beda43541ef84"
PRE_L3 = "373f2bf054ec595e72c1012228b3a39ec0279e9a2c8cefa9d7122c7e113fb42d"


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
    l3 = pkg / "l3_press.py"
    dst = pkg / "l4_canon.py"
    src = Path(__file__).with_name("l4_canon.py")
    if not all(p.is_file() for p in (dash, l3, src)):
        raise RuntimeError("missing dashboard/L3/L4")

    if dst.is_file() and '"l4_canon": self.l4_canon.status(),' in dash.read_text(encoding="utf-8"):
        print("L4_PATCH=ALREADY_APPLIED")
        print("DASHBOARD.PY_SHA256=" + sha(dash))
        print("L4_CANON.PY_SHA256=" + sha(dst))
        return

    if sha(dash) != PRE_DASH:
        raise RuntimeError("dashboard pre-hash mismatch")
    if sha(l3) != PRE_L3:
        raise RuntimeError("L3 pre-hash mismatch")

    d = dash.read_text(encoding="utf-8")
    d = replace_once(
        d,
        "from .l3_press import L3PressTelemetry\n",
        "from .l3_press import L3PressTelemetry\nfrom .l4_canon import L4CanonTelemetry\n",
        "import",
    )
    d = replace_once(
        d,
        "        self.l3_press = L3PressTelemetry()\n        self._lock = threading.RLock()\n",
        "        self.l3_press = L3PressTelemetry()\n        self.l4_canon = L4CanonTelemetry()\n        self._lock = threading.RLock()\n",
        "init",
    )
    d = replace_once(
        d,
        "            self.l3_press = L3PressTelemetry()\n            self._session_started_monotonic = None\n",
        "            self.l3_press = L3PressTelemetry()\n            self.l4_canon = L4CanonTelemetry()\n            self._session_started_monotonic = None\n",
        "reset",
    )
    old = "        self.l3_press.observe(formula_id, source, out, l2_outcome)\n"
    new = "        l3_outcome = self.l3_press.observe(formula_id, source, out, l2_outcome)\n        self.l4_canon.observe(formula_id, source, out, l3_outcome)\n"
    d = replace_once(d, old, new, "callback")
    d = replace_once(
        d,
        '            "l3_press": self.l3_press.status(),\n',
        '            "l3_press": self.l3_press.status(),\n            "l4_canon": self.l4_canon.status(),\n',
        "status",
    )

    dash.write_text(d, encoding="utf-8", newline="\n")
    shutil.copyfile(src, dst)
    print("L4_PATCH=PASS")
    print("DASHBOARD.PY_SHA256=" + sha(dash))
    print("L3_PRESS.PY_SHA256=" + sha(l3))
    print("L4_CANON.PY_SHA256=" + sha(dst))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
