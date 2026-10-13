from __future__ import annotations

import hashlib, shutil, sys
from pathlib import Path

PRE_DASH = "fea396adeba7611f0c5a1fddf67088646e484eeb25d7e2bffbffe4474adeea65"
PRE_L2 = "912b662ee544a76f5b7db6f37d265ba0bb748f8b3d5a32287df93d2b12c0b898"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if text.count(old) != 1:
        raise RuntimeError(f"{label}: expected 1 occurrence, found {text.count(old)}")
    return text.replace(old, new, 1)


def main(root: Path) -> None:
    pkg = root / "src" / "brotoculateur"
    dash = pkg / "dashboard.py"
    l2 = pkg / "l2_threshold.py"
    dst = pkg / "l3_press.py"
    src = Path(__file__).with_name("l3_press.py")
    if not all(p.is_file() for p in (dash, l2, src)):
        raise RuntimeError("missing dashboard/L2/L3")

    if dst.is_file() and '"l3_press": self.l3_press.status(),' in dash.read_text(encoding="utf-8"):
        print("L3_PATCH=ALREADY_APPLIED")
        print("DASHBOARD.PY_SHA256=" + sha(dash))
        print("L3_PRESS.PY_SHA256=" + sha(dst))
        return

    if sha(dash) != PRE_DASH:
        raise RuntimeError("dashboard pre-hash mismatch")
    if sha(l2) != PRE_L2:
        raise RuntimeError("L2 pre-hash mismatch")

    d = dash.read_text(encoding="utf-8")
    d = replace_once(
        d,
        "from .l2_threshold import L2ThresholdTelemetry\n",
        "from .l2_threshold import L2ThresholdTelemetry\nfrom .l3_press import L3PressTelemetry\n",
        "import",
    )
    d = replace_once(
        d,
        "        self.l2_threshold = L2ThresholdTelemetry()\n        self._lock = threading.RLock()\n",
        "        self.l2_threshold = L2ThresholdTelemetry()\n        self.l3_press = L3PressTelemetry()\n        self._lock = threading.RLock()\n",
        "init",
    )
    d = replace_once(
        d,
        "            self.l2_threshold = L2ThresholdTelemetry()\n            self._session_started_monotonic = None\n",
        "            self.l2_threshold = L2ThresholdTelemetry()\n            self.l3_press = L3PressTelemetry()\n            self._session_started_monotonic = None\n",
        "reset",
    )
    old = "        self.l2_threshold.observe(formula_id, source, out, t8_outcome, t9_outcome, t10_outcome, t11_outcome, t12_outcome, l1_outcome)\n"
    new = "        l2_outcome = self.l2_threshold.observe(formula_id, source, out, t8_outcome, t9_outcome, t10_outcome, t11_outcome, t12_outcome, l1_outcome)\n        self.l3_press.observe(formula_id, source, out, l2_outcome)\n"
    d = replace_once(d, old, new, "callback")
    d = replace_once(
        d,
        '            "l2_threshold": self.l2_threshold.status(),\n',
        '            "l2_threshold": self.l2_threshold.status(),\n            "l3_press": self.l3_press.status(),\n',
        "status",
    )

    dash.write_text(d, encoding="utf-8", newline="\n")
    shutil.copyfile(src, dst)
    print("L3_PATCH=PASS")
    print("DASHBOARD.PY_SHA256=" + sha(dash))
    print("L2_THRESHOLD.PY_SHA256=" + sha(l2))
    print("L3_PRESS.PY_SHA256=" + sha(dst))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
