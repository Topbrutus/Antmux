from __future__ import annotations

import hashlib
import shutil
import sys
from pathlib import Path

PRE_DASH = "b39265fedc454b0187d7ec3a2d2e29dba2840716590db52960b89b6300e3e3ea"
PRE_S3 = "35b76679778254e179dcb2df8b2415aa9634319dbc511408eb23bf544f4b9ca3"


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
    s3 = pkg / "s3_route_index.py"
    dst = pkg / "s4_formula_index.py"
    src = Path(__file__).with_name("s4_formula_index.py")
    if not all(p.is_file() for p in (dash, s3, src)):
        raise RuntimeError("missing dashboard/S3/S4")

    d0 = dash.read_text(encoding="utf-8")
    if dst.is_file() and '"s4_formula_index": self.s4_formula_index.status(),' in d0:
        print("S4_PATCH=ALREADY_APPLIED")
        print("DASHBOARD.PY_SHA256=" + sha(dash))
        print("S4_FORMULA_INDEX.PY_SHA256=" + sha(dst))
        return

    if sha(dash) != PRE_DASH:
        raise RuntimeError("dashboard pre-hash mismatch")
    if sha(s3) != PRE_S3:
        raise RuntimeError("S3 pre-hash mismatch")

    d = d0
    d = replace_once(
        d,
        "from .s3_route_index import S3RouteIndexTelemetry\n",
        "from .s3_route_index import S3RouteIndexTelemetry\nfrom .s4_formula_index import S4FormulaIndexTelemetry\n",
        "import",
    )
    d = replace_once(
        d,
        "        self.s3_route_index = S3RouteIndexTelemetry()\n        self._lock = threading.RLock()\n",
        "        self.s3_route_index = S3RouteIndexTelemetry()\n        self.s4_formula_index = S4FormulaIndexTelemetry()\n        self._lock = threading.RLock()\n",
        "init",
    )
    d = replace_once(
        d,
        "            self.s3_route_index = S3RouteIndexTelemetry()\n            self._session_started_monotonic = None\n",
        "            self.s3_route_index = S3RouteIndexTelemetry()\n            self.s4_formula_index = S4FormulaIndexTelemetry()\n            self._session_started_monotonic = None\n",
        "reset",
    )
    d = replace_once(
        d,
        "        self.s3_route_index.observe(formula_id, source, out, s2_outcome, papillon=papillon)\n",
        "        s3_outcome = self.s3_route_index.observe(formula_id, source, out, s2_outcome, papillon=papillon)\n        self.s4_formula_index.observe(formula_id, source, out, s3_outcome)\n",
        "callback",
    )
    d = replace_once(
        d,
        '            "s3_route_index": self.s3_route_index.status(),\n',
        '            "s3_route_index": self.s3_route_index.status(),\n            "s4_formula_index": self.s4_formula_index.status(),\n',
        "status",
    )

    dash.write_text(d, encoding="utf-8", newline="\n")
    shutil.copyfile(src, dst)
    print("S4_PATCH=PASS")
    print("DASHBOARD.PY_SHA256=" + sha(dash))
    print("S3_ROUTE_INDEX.PY_SHA256=" + sha(s3))
    print("S4_FORMULA_INDEX.PY_SHA256=" + sha(dst))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
