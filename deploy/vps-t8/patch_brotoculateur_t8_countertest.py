from __future__ import annotations

import hashlib
import shutil
import sys
from pathlib import Path

PRE_DASH = "e9bf39bfd632a2945bd976373a3e749d28140ca26160c7faeb07297cbf5af690"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected 1 occurrence, found {count}")
    return text.replace(old, new, 1)


def replace_n(text: str, old: str, new: str, count_expected: int, label: str) -> str:
    count = text.count(old)
    if count != count_expected:
        raise RuntimeError(f"{label}: expected {count_expected} occurrences, found {count}")
    return text.replace(old, new)


def main(root: Path) -> None:
    pkg = root / "src" / "brotoculateur"
    dash = pkg / "dashboard.py"
    dst = pkg / "t8_countertest.py"
    src = Path(__file__).with_name("t8_countertest.py")
    if not dash.is_file() or not src.is_file():
        raise RuntimeError("missing dashboard or T8 module")

    already = dst.is_file() and '"t8_countertest": self.t8_countertest.status(),' in dash.read_text(encoding="utf-8")
    if already:
        print("T8_PATCH=ALREADY_APPLIED")
        print("DASHBOARD.PY_SHA256=" + sha(dash))
        print("T8_COUNTERTEST.PY_SHA256=" + sha(dst))
        return

    if sha(dash) != PRE_DASH:
        raise RuntimeError("dashboard pre-hash mismatch")

    d = dash.read_text(encoding="utf-8")
    d = replace_once(
        d,
        "from .t7_calculation import T7CalculationTelemetry\n",
        "from .t7_calculation import T7CalculationTelemetry\nfrom .t8_countertest import T8CountertestTelemetry\n",
        "dashboard import",
    )
    d = replace_once(
        d,
        "        self.t7_calculation = T7CalculationTelemetry()\n        self._lock = threading.RLock()\n",
        "        self.t7_calculation = T7CalculationTelemetry()\n        self.t8_countertest = T8CountertestTelemetry()\n        self._lock = threading.RLock()\n",
        "dashboard init",
    )
    d = replace_once(
        d,
        "            self.t7_calculation = T7CalculationTelemetry()\n            self._session_started_monotonic = None\n",
        "            self.t7_calculation = T7CalculationTelemetry()\n            self.t8_countertest = T8CountertestTelemetry()\n            self._session_started_monotonic = None\n",
        "dashboard reset",
    )
    d = replace_once(
        d,
        "    def _observe_formula_result(self, formula_id: str, source: TracePacket, out: TracePacket) -> None:\n        self.brutomagique.observe_formula_result(formula_id, source, out)\n",
        "    def _observe_formula_result(self, formula_id: str, source: TracePacket, out: TracePacket) -> None:\n        self.brutomagique.observe_formula_result(formula_id, source, out)\n        self.t8_countertest.observe(formula_id, source, out)\n",
        "formula result callback",
    )
    d = replace_once(
        d,
        '            "t7_calculation": self._runner.t7_status(),\n',
        '            "t7_calculation": self._runner.t7_status(),\n            "t8_countertest": self.t8_countertest.status(),\n',
        "dashboard status",
    )

    dash.write_text(d, encoding="utf-8", newline="\n")
    shutil.copyfile(src, dst)
    print("T8_PATCH=PASS")
    print("DASHBOARD.PY_SHA256=" + sha(dash))
    print("T8_COUNTERTEST.PY_SHA256=" + sha(dst))


if __name__ == "__main__":
    main(Path(sys.argv[1]))