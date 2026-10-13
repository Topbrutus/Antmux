from __future__ import annotations

import hashlib
import shutil
import sys
from pathlib import Path

PRE_DASH = "82b57cca014d6eee3d9e039e6f483317f248caddef8d21b37cbf226ce27903af"
PRE_S5 = "de885d1f4748d236a0050cbea87560cf26fc74a08a95a8a02b119241ce6b0334"
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
    s5 = pkg / "s5_fast_index.py"
    c3 = pkg / "c3_library.py"
    engine = pkg / "engine.py"
    dst = pkg / "co1_archive.py"
    src = Path(__file__).with_name("co1_archive.py")
    if not all(p.is_file() for p in (dash, s5, c3, engine, src)):
        raise RuntimeError("missing dashboard/S5/C3/engine/Co1")

    d0 = dash.read_text(encoding="utf-8")
    if dst.is_file() and '"co1_archive": self.co1_archive.status(),' in d0:
        print("CO1_PATCH=ALREADY_APPLIED")
        print("DASHBOARD.PY_SHA256=" + sha(dash))
        print("CO1_ARCHIVE.PY_SHA256=" + sha(dst))
        return

    if sha(dash) != PRE_DASH:
        raise RuntimeError("dashboard pre-hash mismatch")
    if sha(s5) != PRE_S5:
        raise RuntimeError("S5 pre-hash mismatch")
    if sha(c3) != PRE_C3:
        raise RuntimeError("C3 pre-hash mismatch")
    if "def c2_fingerprint(" not in engine.read_text(encoding="utf-8"):
        raise RuntimeError("existing C2 fingerprint helper missing")

    d = d0
    d = replace_once(
        d,
        "from .s5_fast_index import S5FastIndexTelemetry\n",
        "from .s5_fast_index import S5FastIndexTelemetry\nfrom .co1_archive import Co1ArchiveTelemetry\n",
        "import",
    )
    d = replace_once(
        d,
        "        self.s5_fast_index = S5FastIndexTelemetry()\n        self._lock = threading.RLock()\n",
        "        self.s5_fast_index = S5FastIndexTelemetry()\n        self.co1_archive = Co1ArchiveTelemetry()\n        self._lock = threading.RLock()\n",
        "init",
    )
    d = replace_once(
        d,
        "            self.s5_fast_index = S5FastIndexTelemetry()\n            self._session_started_monotonic = None\n",
        "            self.s5_fast_index = S5FastIndexTelemetry()\n            self.co1_archive = Co1ArchiveTelemetry()\n            self._session_started_monotonic = None\n",
        "reset",
    )
    d = replace_once(
        d,
        "        self.s5_fast_index.observe(formula_id, source, out, s4_outcome)\n",
        "        s5_outcome = self.s5_fast_index.observe(formula_id, source, out, s4_outcome)\n        self.co1_archive.observe(formula_id, source, out, s5_outcome)\n",
        "callback",
    )
    d = replace_once(
        d,
        '            "s5_fast_index": self.s5_fast_index.status(),\n',
        '            "s5_fast_index": self.s5_fast_index.status(),\n            "co1_archive": self.co1_archive.status(),\n',
        "status",
    )

    dash.write_text(d, encoding="utf-8", newline="\n")
    shutil.copyfile(src, dst)
    print("CO1_PATCH=PASS")
    print("DASHBOARD.PY_SHA256=" + sha(dash))
    print("S5_FAST_INDEX.PY_SHA256=" + sha(s5))
    print("C3_LIBRARY.PY_SHA256=" + sha(c3))
    print("CO1_ARCHIVE.PY_SHA256=" + sha(dst))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: patch_brotoculateur_co1_archive.py <brotoculateur-root>")
    main(Path(sys.argv[1]).resolve())
