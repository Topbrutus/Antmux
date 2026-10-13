from __future__ import annotations

import hashlib, shutil, sys
from pathlib import Path

PRE_DASH = "6f717f1af70e0ccc5da67221cced408106a95100c185ed17afecd06d47eff1f0"
PRE_T12 = "582566a439ce1fdb9665237a81398f52476e4a85b715ee855d310ed7d407a4f9"

def sha(p: Path) -> str: return hashlib.sha256(p.read_bytes()).hexdigest()

def replace_once(text: str, old: str, new: str, label: str) -> str:
    if text.count(old) != 1: raise RuntimeError(f"{label}: expected 1 occurrence")
    return text.replace(old, new, 1)

def main(root: Path) -> None:
    pkg = root / "src" / "brotoculateur"
    dash, t12 = pkg / "dashboard.py", pkg / "t12_candidate.py"
    dst, src = pkg / "l1_crystal_score.py", Path(__file__).with_name("l1_crystal_score.py")
    if not all(p.is_file() for p in (dash, t12, src)): raise RuntimeError("missing dashboard/T12/L1")
    if dst.is_file() and '"l1_crystal_score": self.l1_crystal_score.status(),' in dash.read_text(encoding="utf-8"):
        print("L1_PATCH=ALREADY_APPLIED"); print("DASHBOARD.PY_SHA256="+sha(dash)); print("L1_CRYSTAL_SCORE.PY_SHA256="+sha(dst)); return
    if sha(dash) != PRE_DASH: raise RuntimeError("dashboard pre-hash mismatch")
    if sha(t12) != PRE_T12: raise RuntimeError("T12 pre-hash mismatch")
    d = dash.read_text(encoding="utf-8")
    d = replace_once(d, "from .t12_candidate import T12CandidateTelemetry\n", "from .t12_candidate import T12CandidateTelemetry\nfrom .l1_crystal_score import L1CrystalScoreTelemetry\n", "import")
    d = replace_once(d, "        self.t12_candidate = T12CandidateTelemetry()\n        self._lock = threading.RLock()\n", "        self.t12_candidate = T12CandidateTelemetry()\n        self.l1_crystal_score = L1CrystalScoreTelemetry()\n        self._lock = threading.RLock()\n", "init")
    d = replace_once(d, "            self.t12_candidate = T12CandidateTelemetry()\n            self._session_started_monotonic = None\n", "            self.t12_candidate = T12CandidateTelemetry()\n            self.l1_crystal_score = L1CrystalScoreTelemetry()\n            self._session_started_monotonic = None\n", "reset")
    d = replace_once(d, "        self.t12_candidate.observe(formula_id, source, out, t11_outcome)\n", "        t12_outcome = self.t12_candidate.observe(formula_id, source, out, t11_outcome)\n        self.l1_crystal_score.observe(formula_id, source, out, t8_outcome, t9_outcome, t10_outcome, t11_outcome, t12_outcome)\n", "callback")
    d = replace_once(d, '            "t12_candidate": self.t12_candidate.status(),\n', '            "t12_candidate": self.t12_candidate.status(),\n            "l1_crystal_score": self.l1_crystal_score.status(),\n', "status")
    dash.write_text(d, encoding="utf-8", newline="\n"); shutil.copyfile(src, dst)
    print("L1_PATCH=PASS"); print("DASHBOARD.PY_SHA256="+sha(dash)); print("T12_CANDIDATE.PY_SHA256="+sha(t12)); print("L1_CRYSTAL_SCORE.PY_SHA256="+sha(dst))

if __name__ == "__main__": main(Path(sys.argv[1]))
