from __future__ import annotations

import hashlib
import shutil
import sys
from pathlib import Path

PRE_DASH = "71ab037d40892a4b815f5676e8deaa539583717f8f9df2cf7ce19befca9e914b"
PRE_S2 = "6fbfc62780fcacdd1b79a7feb83cdda8a56985a8ba7ba033b6835cd08b4885b6"


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
    s2 = pkg / "s2_lineage_index.py"
    dst = pkg / "s3_route_index.py"
    src = Path(__file__).with_name("s3_route_index.py")
    if not all(p.is_file() for p in (dash, s2, src)):
        raise RuntimeError("missing dashboard/S2/S3")

    d0 = dash.read_text(encoding="utf-8")
    if dst.is_file() and '"s3_route_index": self.s3_route_index.status(),' in d0:
        print("S3_PATCH=ALREADY_APPLIED")
        print("DASHBOARD.PY_SHA256=" + sha(dash))
        print("S3_ROUTE_INDEX.PY_SHA256=" + sha(dst))
        return

    if sha(dash) != PRE_DASH:
        raise RuntimeError("dashboard pre-hash mismatch")
    if sha(s2) != PRE_S2:
        raise RuntimeError("S2 pre-hash mismatch")

    d = d0
    d = replace_once(
        d,
        "from .s2_lineage_index import S2LineageIndexTelemetry\n",
        "from .s2_lineage_index import S2LineageIndexTelemetry\nfrom .s3_route_index import S3RouteIndexTelemetry\n",
        "import",
    )
    d = replace_once(
        d,
        "        self.s2_lineage_index = S2LineageIndexTelemetry()\n        self._lock = threading.RLock()\n",
        "        self.s2_lineage_index = S2LineageIndexTelemetry()\n        self.s3_route_index = S3RouteIndexTelemetry()\n        self._lock = threading.RLock()\n",
        "init",
    )
    d = replace_once(
        d,
        "            self.s2_lineage_index = S2LineageIndexTelemetry()\n            self._session_started_monotonic = None\n",
        "            self.s2_lineage_index = S2LineageIndexTelemetry()\n            self.s3_route_index = S3RouteIndexTelemetry()\n            self._session_started_monotonic = None\n",
        "reset",
    )
    d = replace_once(
        d,
        "        self.s2_lineage_index.observe(formula_id, source, out, s1_outcome)\n",
        "        s2_outcome = self.s2_lineage_index.observe(formula_id, source, out, s1_outcome)\n        papillon = getattr(getattr(self, \"_runner\", None), \"papillon\", None)\n        self.s3_route_index.observe(formula_id, source, out, s2_outcome, papillon=papillon)\n",
        "callback",
    )
    d = replace_once(
        d,
        '            "s2_lineage_index": self.s2_lineage_index.status(),\n',
        '            "s2_lineage_index": self.s2_lineage_index.status(),\n            "s3_route_index": self.s3_route_index.status(),\n',
        "status",
    )

    dash.write_text(d, encoding="utf-8", newline="\n")
    shutil.copyfile(src, dst)
    print("S3_PATCH=PASS")
    print("DASHBOARD.PY_SHA256=" + sha(dash))
    print("S2_LINEAGE_INDEX.PY_SHA256=" + sha(s2))
    print("S3_ROUTE_INDEX.PY_SHA256=" + sha(dst))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
