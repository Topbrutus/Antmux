from __future__ import annotations

import hashlib
import shutil
import sys
from pathlib import Path

PRE_DASH = "210abbe5d72fd4dcc4b154cb3d13a8d954567ac29ef5435381fe2f16fbce109b"
PRE_CO1 = "032ba9e665349b7d426e32c19d3c532467a0245e35a27da2cd66e2d1209864d2"
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
    co1 = pkg / "co1_archive.py"
    s5 = pkg / "s5_fast_index.py"
    c3 = pkg / "c3_library.py"
    dst = pkg / "co2_proof_chain.py"
    src = Path(__file__).with_name("co2_proof_chain.py")
    if not all(p.is_file() for p in (dash, co1, s5, c3, src)):
        raise RuntimeError("missing dashboard/Co1/S5/C3/Co2")

    d0 = dash.read_text(encoding="utf-8")
    if dst.is_file() and '"co2_proof_chain": self.co2_proof_chain.status(),' in d0:
        print("CO2_PATCH=ALREADY_APPLIED")
        print("DASHBOARD.PY_SHA256=" + sha(dash))
        print("CO2_PROOF_CHAIN.PY_SHA256=" + sha(dst))
        return

    if sha(dash) != PRE_DASH:
        raise RuntimeError("dashboard pre-hash mismatch")
    if sha(co1) != PRE_CO1:
        raise RuntimeError("Co1 pre-hash mismatch")
    if sha(s5) != PRE_S5:
        raise RuntimeError("S5 pre-hash mismatch")
    if sha(c3) != PRE_C3:
        raise RuntimeError("C3 pre-hash mismatch")

    d = d0
    d = replace_once(
        d,
        "from .co1_archive import Co1ArchiveTelemetry\n",
        "from .co1_archive import Co1ArchiveTelemetry\nfrom .co2_proof_chain import Co2ProofChainTelemetry\n",
        "import",
    )
    d = replace_once(
        d,
        "        self.co1_archive = Co1ArchiveTelemetry()\n        self._lock = threading.RLock()\n",
        "        self.co1_archive = Co1ArchiveTelemetry()\n        self.co2_proof_chain = Co2ProofChainTelemetry()\n        self._lock = threading.RLock()\n",
        "init",
    )
    d = replace_once(
        d,
        "            self.co1_archive = Co1ArchiveTelemetry()\n            self._session_started_monotonic = None\n",
        "            self.co1_archive = Co1ArchiveTelemetry()\n            self.co2_proof_chain = Co2ProofChainTelemetry()\n            self._session_started_monotonic = None\n",
        "reset",
    )
    d = replace_once(
        d,
        "        self.co1_archive.observe(formula_id, source, out, s5_outcome)\n",
        "        co1_outcome = self.co1_archive.observe(formula_id, source, out, s5_outcome)\n        self.co2_proof_chain.observe(formula_id, source, out, co1_outcome)\n",
        "callback",
    )
    d = replace_once(
        d,
        '            "co1_archive": self.co1_archive.status(),\n',
        '            "co1_archive": self.co1_archive.status(),\n            "co2_proof_chain": self.co2_proof_chain.status(),\n',
        "status",
    )

    dash.write_text(d, encoding="utf-8", newline="\n")
    shutil.copyfile(src, dst)
    print("CO2_PATCH=PASS")
    print("DASHBOARD.PY_SHA256=" + sha(dash))
    print("CO1_ARCHIVE.PY_SHA256=" + sha(co1))
    print("S5_FAST_INDEX.PY_SHA256=" + sha(s5))
    print("C3_LIBRARY.PY_SHA256=" + sha(c3))
    print("CO2_PROOF_CHAIN.PY_SHA256=" + sha(dst))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: patch_brotoculateur_co2_proof_chain.py <brotoculateur-root>")
    main(Path(sys.argv[1]).resolve())
