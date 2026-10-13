from __future__ import annotations

import hashlib
import shutil
import sys
from pathlib import Path

PRE_DASH = "8a294e39869babd68ff7c5456afbbd5d740ca44aec360e60a0f5bd8a1335e94e"
PRE_T8 = "a93bd6cd9aaaf0fe832604de9e390e6d69de7dfb8b853e558d8c9955761cce9e"


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
    dst = pkg / "t9_stability.py"
    src = Path(__file__).with_name("t9_stability.py")
    if not dash.is_file() or not t8.is_file() or not src.is_file():
        raise RuntimeError("missing dashboard, T8 module, or T9 module")

    already = (
        dst.is_file()
        and '"t9_stability": self.t9_stability.status(),' in dash.read_text(encoding="utf-8")
    )
    if already:
        print("T9_PATCH=ALREADY_APPLIED")
        print("DASHBOARD.PY_SHA256=" + sha(dash))
        print("T8_COUNTERTEST.PY_SHA256=" + sha(t8))
        print("T9_STABILITY.PY_SHA256=" + sha(dst))
        return

    if sha(dash) != PRE_DASH:
        raise RuntimeError("dashboard pre-hash mismatch")
    if sha(t8) != PRE_T8:
        raise RuntimeError("T8 pre-hash mismatch")

    d = dash.read_text(encoding="utf-8")
    d = replace_once(
        d,
        "from .t8_countertest import T8CountertestTelemetry\n",
        "from .t8_countertest import T8CountertestTelemetry\nfrom .t9_stability import T9StabilityTelemetry\n",
        "dashboard import",
    )
    d = replace_once(
        d,
        "        self.t8_countertest = T8CountertestTelemetry()\n        self._lock = threading.RLock()\n",
        "        self.t8_countertest = T8CountertestTelemetry()\n        self.t9_stability = T9StabilityTelemetry()\n        self._lock = threading.RLock()\n",
        "dashboard init",
    )
    d = replace_once(
        d,
        "            self.t8_countertest = T8CountertestTelemetry()\n            self._session_started_monotonic = None\n",
        "            self.t8_countertest = T8CountertestTelemetry()\n            self.t9_stability = T9StabilityTelemetry()\n            self._session_started_monotonic = None\n",
        "dashboard reset",
    )
    d = replace_once(
        d,
        "        self.brutomagique.observe_formula_result(formula_id, source, out)\n        self.t8_countertest.observe(formula_id, source, out)\n",
        "        self.brutomagique.observe_formula_result(formula_id, source, out)\n        t8_outcome = self.t8_countertest.observe(formula_id, source, out)\n        self.t9_stability.observe(formula_id, source, out, t8_outcome)\n",
        "formula result callback",
    )
    d = replace_once(
        d,
        '            "t8_countertest": self.t8_countertest.status(),\n',
        '            "t8_countertest": self.t8_countertest.status(),\n            "t9_stability": self.t9_stability.status(),\n',
        "dashboard status",
    )

    dash.write_text(d, encoding="utf-8", newline="\n")
    shutil.copyfile(src, dst)
    print("T9_PATCH=PASS")
    print("DASHBOARD.PY_SHA256=" + sha(dash))
    print("T8_COUNTERTEST.PY_SHA256=" + sha(t8))
    print("T9_STABILITY.PY_SHA256=" + sha(dst))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
