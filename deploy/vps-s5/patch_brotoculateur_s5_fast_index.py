from __future__ import annotations

import hashlib
import shutil
import sys
from pathlib import Path

PRE_DASH = "5161995d53af3bbefa39aec6fd6a69b6aaa7af10d1295eef5d61fc133cb15f5e"
PRE_S4 = "3c9431bbdf7fc0be33d1eae38455d1584ec87b250b4fe09e0bc849cbc117ebc9"
PRE_C3 = "b7970583e688488d0f9fd8a90838d9163d00b08b7e6afedd499434e79a06c434"


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
    s4 = pkg / "s4_formula_index.py"
    c3 = pkg / "c3_library.py"
    engine = pkg / "engine.py"
    dst = pkg / "s5_fast_index.py"
    src = Path(__file__).with_name("s5_fast_index.py")
    if not all(p.is_file() for p in (dash, s4, c3, engine, src)):
        raise RuntimeError("missing dashboard/S4/C3/engine/S5")

    d0 = dash.read_text(encoding="utf-8")
    if dst.is_file() and '"s5_fast_index": self.s5_fast_index.status(),' in d0:
        print("S5_PATCH=ALREADY_APPLIED")
        print("DASHBOARD.PY_SHA256=" + sha(dash))
        print("S5_FAST_INDEX.PY_SHA256=" + sha(dst))
        return

    if sha(dash) != PRE_DASH:
        raise RuntimeError("dashboard pre-hash mismatch")
    if sha(s4) != PRE_S4:
        raise RuntimeError("S4 pre-hash mismatch")
    if sha(c3) != PRE_C3:
        raise RuntimeError("C3 pre-hash mismatch")
    if "def c2_fingerprint(" not in engine.read_text(encoding="utf-8"):
        raise RuntimeError("existing C2 fingerprint helper missing")

    d = d0
    d = replace_once(
        d,
        "from .s4_formula_index import S4FormulaIndexTelemetry\n",
        "from .s4_formula_index import S4FormulaIndexTelemetry\nfrom .s5_fast_index import S5FastIndexTelemetry\n",
        "import",
    )
    d = replace_once(
        d,
        "        self.s4_formula_index = S4FormulaIndexTelemetry()\n        self._lock = threading.RLock()\n",
        "        self.s4_formula_index = S4FormulaIndexTelemetry()\n        self.s5_fast_index = S5FastIndexTelemetry()\n        self._lock = threading.RLock()\n",
        "init",
    )
    d = replace_once(
        d,
        "            self.s4_formula_index = S4FormulaIndexTelemetry()\n            self._session_started_monotonic = None\n",
        "            self.s4_formula_index = S4FormulaIndexTelemetry()\n            self.s5_fast_index = S5FastIndexTelemetry()\n            self._session_started_monotonic = None\n",
        "reset",
    )
    d = replace_once(
        d,
        "        self.s4_formula_index.observe(formula_id, source, out, s3_outcome)\n",
        "        s4_outcome = self.s4_formula_index.observe(formula_id, source, out, s3_outcome)\n        self.s5_fast_index.observe(formula_id, source, out, s4_outcome)\n",
        "callback",
    )
    d = replace_once(
        d,
        '            "s4_formula_index": self.s4_formula_index.status(),\n',
        '            "s4_formula_index": self.s4_formula_index.status(),\n            "s5_fast_index": self.s5_fast_index.status(),\n',
        "status",
    )

    dash.write_text(d, encoding="utf-8", newline="\n")
    shutil.copyfile(src, dst)
    print("S5_PATCH=PASS")
    print("DASHBOARD.PY_SHA256=" + sha(dash))
    print("S4_FORMULA_INDEX.PY_SHA256=" + sha(s4))
    print("C3_LIBRARY.PY_SHA256=" + sha(c3))
    print("S5_FAST_INDEX.PY_SHA256=" + sha(dst))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
