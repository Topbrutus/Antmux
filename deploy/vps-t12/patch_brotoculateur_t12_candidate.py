from __future__ import annotations

import hashlib
import shutil
import sys
from pathlib import Path

PRE_DASH = "9991bbb5513101ea66d22411dfe7da8e1ba79ebc2d1bea668ef07acec3546021"
PRE_T8 = "a93bd6cd9aaaf0fe832604de9e390e6d69de7dfb8b853e558d8c9955761cce9e"
PRE_T9 = "c0e0309dfe6d571c1d786010f72bc6f8bf3ccdada1f5fa960ab6f428e3640dd1"
PRE_T10 = "9fe9b3bbb9a42c790d02e2d85638b2ea11e067750dc1cc5c6812b2c42f40a3be"
PRE_T11 = "559824ead9ed8f824955e10cbe4d3826da4eb4673a43a64125cf46e01985221d"


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
    t11 = pkg / "t11_budget.py"
    dst = pkg / "t12_candidate.py"
    src = Path(__file__).with_name("t12_candidate.py")
    if not all(p.is_file() for p in (dash, t8, t9, t10, t11, src)):
        raise RuntimeError("missing dashboard, T8, T9, T10, T11, or T12 module")

    already = dst.is_file() and '"t12_candidate": self.t12_candidate.status(),' in dash.read_text(encoding="utf-8")
    if already:
        print("T12_PATCH=ALREADY_APPLIED")
        for label, path in (
            ("DASHBOARD.PY_SHA256", dash),
            ("T8_COUNTERTEST.PY_SHA256", t8),
            ("T9_STABILITY.PY_SHA256", t9),
            ("T10_REPLAY.PY_SHA256", t10),
            ("T11_BUDGET.PY_SHA256", t11),
            ("T12_CANDIDATE.PY_SHA256", dst),
        ):
            print(label + "=" + sha(path))
        return

    expected = ((dash, PRE_DASH, "dashboard"), (t8, PRE_T8, "T8"), (t9, PRE_T9, "T9"), (t10, PRE_T10, "T10"), (t11, PRE_T11, "T11"))
    for path, digest, label in expected:
        if sha(path) != digest:
            raise RuntimeError(f"{label} pre-hash mismatch")

    d = dash.read_text(encoding="utf-8")
    d = replace_once(
        d,
        "from .t11_budget import T11BudgetTelemetry\n",
        "from .t11_budget import T11BudgetTelemetry\nfrom .t12_candidate import T12CandidateTelemetry\n",
        "dashboard import",
    )
    d = replace_once(
        d,
        "        self.t11_budget = T11BudgetTelemetry()\n        self._lock = threading.RLock()\n",
        "        self.t11_budget = T11BudgetTelemetry()\n        self.t12_candidate = T12CandidateTelemetry()\n        self._lock = threading.RLock()\n",
        "dashboard init",
    )
    d = replace_once(
        d,
        "            self.t11_budget = T11BudgetTelemetry()\n            self._session_started_monotonic = None\n",
        "            self.t11_budget = T11BudgetTelemetry()\n            self.t12_candidate = T12CandidateTelemetry()\n            self._session_started_monotonic = None\n",
        "dashboard reset",
    )
    d = replace_once(
        d,
        "        self.t11_budget.observe(formula_id, source, out, t10_outcome)\n",
        "        t11_outcome = self.t11_budget.observe(formula_id, source, out, t10_outcome)\n"
        "        self.t12_candidate.observe(formula_id, source, out, t11_outcome)\n",
        "formula result callback",
    )
    d = replace_once(
        d,
        '            "t11_budget": self.t11_budget.status(),\n',
        '            "t11_budget": self.t11_budget.status(),\n'
        '            "t12_candidate": self.t12_candidate.status(),\n',
        "dashboard status",
    )

    dash.write_text(d, encoding="utf-8", newline="\n")
    shutil.copyfile(src, dst)
    print("T12_PATCH=PASS")
    for label, path in (
        ("DASHBOARD.PY_SHA256", dash),
        ("T8_COUNTERTEST.PY_SHA256", t8),
        ("T9_STABILITY.PY_SHA256", t9),
        ("T10_REPLAY.PY_SHA256", t10),
        ("T11_BUDGET.PY_SHA256", t11),
        ("T12_CANDIDATE.PY_SHA256", dst),
    ):
        print(label + "=" + sha(path))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
