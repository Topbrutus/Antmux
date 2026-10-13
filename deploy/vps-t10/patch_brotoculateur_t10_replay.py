from __future__ import annotations

import hashlib
import shutil
import sys
from pathlib import Path

PRE_DASH = "c8e4e06b74d7028f6db233d21cb630a93f9f8265e287cad58916e43ffdf8a34d"
PRE_T8 = "a93bd6cd9aaaf0fe832604de9e390e6d69de7dfb8b853e558d8c9955761cce9e"
PRE_T9 = "c0e0309dfe6d571c1d786010f72bc6f8bf3ccdada1f5fa960ab6f428e3640dd1"


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
    t8 = pkg / "t8_countertest.py"
    t9 = pkg / "t9_stability.py"
    dst = pkg / "t10_replay.py"
    src = Path(__file__).with_name("t10_replay.py")
    if not dash.is_file() or not t8.is_file() or not t9.is_file() or not src.is_file():
        raise RuntimeError("missing dashboard, T8 module, T9 module, or T10 module")

    already = (
        dst.is_file()
        and '"t10_replay": self.t10_replay.status(),' in dash.read_text(encoding="utf-8")
    )
    if already:
        print("T10_PATCH=ALREADY_APPLIED")
        print("DASHBOARD.PY_SHA256=" + sha(dash))
        print("T8_COUNTERTEST.PY_SHA256=" + sha(t8))
        print("T9_STABILITY.PY_SHA256=" + sha(t9))
        print("T10_REPLAY.PY_SHA256=" + sha(dst))
        return

    if sha(dash) != PRE_DASH:
        raise RuntimeError("dashboard pre-hash mismatch")
    if sha(t8) != PRE_T8:
        raise RuntimeError("T8 pre-hash mismatch")
    if sha(t9) != PRE_T9:
        raise RuntimeError("T9 pre-hash mismatch")

    d = dash.read_text(encoding="utf-8")
    d = replace_once(
        d,
        "from .t9_stability import T9StabilityTelemetry\n",
        "from .t9_stability import T9StabilityTelemetry\nfrom .t10_replay import T10ReplayTelemetry\n",
        "dashboard import",
    )
    d = replace_once(
        d,
        "        self.t9_stability = T9StabilityTelemetry()\n        self._lock = threading.RLock()\n",
        "        self.t9_stability = T9StabilityTelemetry()\n        self.t10_replay = T10ReplayTelemetry()\n        self._lock = threading.RLock()\n",
        "dashboard init",
    )
    d = replace_once(
        d,
        "            self.t9_stability = T9StabilityTelemetry()\n            self._session_started_monotonic = None\n",
        "            self.t9_stability = T9StabilityTelemetry()\n            self.t10_replay = T10ReplayTelemetry()\n            self._session_started_monotonic = None\n",
        "dashboard reset",
    )
    d = replace_once(
        d,
        "        t8_outcome = self.t8_countertest.observe(formula_id, source, out)\n"
        "        self.t9_stability.observe(formula_id, source, out, t8_outcome)\n",
        "        t8_outcome = self.t8_countertest.observe(formula_id, source, out)\n"
        "        t9_outcome = self.t9_stability.observe(formula_id, source, out, t8_outcome)\n"
        "        self.t10_replay.observe(formula_id, source, out, t8_outcome, t9_outcome)\n",
        "formula result callback",
    )
    d = replace_once(
        d,
        '            "t9_stability": self.t9_stability.status(),\n',
        '            "t9_stability": self.t9_stability.status(),\n'
        '            "t10_replay": self.t10_replay.status(),\n',
        "dashboard status",
    )

    dash.write_text(d, encoding="utf-8", newline="\n")
    shutil.copyfile(src, dst)
    print("T10_PATCH=PASS")
    print("DASHBOARD.PY_SHA256=" + sha(dash))
    print("T8_COUNTERTEST.PY_SHA256=" + sha(t8))
    print("T9_STABILITY.PY_SHA256=" + sha(t9))
    print("T10_REPLAY.PY_SHA256=" + sha(dst))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
