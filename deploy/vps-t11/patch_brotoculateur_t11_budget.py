from __future__ import annotations

import hashlib
import shutil
import sys
from pathlib import Path

PRE_DASH = "8b97522a6210f0c6ec2feaa1a3786bd00ffda5362aed9feee2c1966768bd61d4"
PRE_T8 = "a93bd6cd9aaaf0fe832604de9e390e6d69de7dfb8b853e558d8c9955761cce9e"
PRE_T9 = "c0e0309dfe6d571c1d786010f72bc6f8bf3ccdada1f5fa960ab6f428e3640dd1"
PRE_T10 = "9fe9b3bbb9a42c790d02e2d85638b2ea11e067750dc1cc5c6812b2c42f40a3be"


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
    t10 = pkg / "t10_replay.py"
    dst = pkg / "t11_budget.py"
    src = Path(__file__).with_name("t11_budget.py")
    if not dash.is_file() or not t8.is_file() or not t9.is_file() or not t10.is_file() or not src.is_file():
        raise RuntimeError("missing dashboard, T8, T9, T10, or T11 module")

    already = (
        dst.is_file()
        and '"t11_budget": self.t11_budget.status(),' in dash.read_text(encoding="utf-8")
    )
    if already:
        print("T11_PATCH=ALREADY_APPLIED")
        print("DASHBOARD.PY_SHA256=" + sha(dash))
        print("T8_COUNTERTEST.PY_SHA256=" + sha(t8))
        print("T9_STABILITY.PY_SHA256=" + sha(t9))
        print("T10_REPLAY.PY_SHA256=" + sha(t10))
        print("T11_BUDGET.PY_SHA256=" + sha(dst))
        return

    if sha(dash) != PRE_DASH:
        raise RuntimeError("dashboard pre-hash mismatch")
    if sha(t8) != PRE_T8:
        raise RuntimeError("T8 pre-hash mismatch")
    if sha(t9) != PRE_T9:
        raise RuntimeError("T9 pre-hash mismatch")
    if sha(t10) != PRE_T10:
        raise RuntimeError("T10 pre-hash mismatch")

    d = dash.read_text(encoding="utf-8")
    d = replace_once(
        d,
        "from .t10_replay import T10ReplayTelemetry\n",
        "from .t10_replay import T10ReplayTelemetry\nfrom .t11_budget import T11BudgetTelemetry\n",
        "dashboard import",
    )
    d = replace_once(
        d,
        "        self.t10_replay = T10ReplayTelemetry()\n        self._lock = threading.RLock()\n",
        "        self.t10_replay = T10ReplayTelemetry()\n        self.t11_budget = T11BudgetTelemetry()\n        self._lock = threading.RLock()\n",
        "dashboard init",
    )
    d = replace_once(
        d,
        "            self.t10_replay = T10ReplayTelemetry()\n            self._session_started_monotonic = None\n",
        "            self.t10_replay = T10ReplayTelemetry()\n            self.t11_budget = T11BudgetTelemetry()\n            self._session_started_monotonic = None\n",
        "dashboard reset",
    )
    d = replace_once(
        d,
        "        t9_outcome = self.t9_stability.observe(formula_id, source, out, t8_outcome)\n"
        "        self.t10_replay.observe(formula_id, source, out, t8_outcome, t9_outcome)\n",
        "        t9_outcome = self.t9_stability.observe(formula_id, source, out, t8_outcome)\n"
        "        t10_outcome = self.t10_replay.observe(formula_id, source, out, t8_outcome, t9_outcome)\n"
        "        self.t11_budget.observe(formula_id, source, out, t10_outcome)\n",
        "formula result callback",
    )
    d = replace_once(
        d,
        '            "t10_replay": self.t10_replay.status(),\n',
        '            "t10_replay": self.t10_replay.status(),\n'
        '            "t11_budget": self.t11_budget.status(),\n',
        "dashboard status",
    )

    dash.write_text(d, encoding="utf-8", newline="\n")
    shutil.copyfile(src, dst)
    print("T11_PATCH=PASS")
    print("DASHBOARD.PY_SHA256=" + sha(dash))
    print("T8_COUNTERTEST.PY_SHA256=" + sha(t8))
    print("T9_STABILITY.PY_SHA256=" + sha(t9))
    print("T10_REPLAY.PY_SHA256=" + sha(t10))
    print("T11_BUDGET.PY_SHA256=" + sha(dst))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
