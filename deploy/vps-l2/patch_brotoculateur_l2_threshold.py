from __future__ import annotations

import hashlib, shutil, sys
from pathlib import Path

PRE_DASH = "b0f450f62bd6096fe4481fb1bed5a9072a866d117e4b772d91ab8663f0485749"
PRE_L1 = "2f5d674410d284e0e274a2ef347666d3cd18aa4a0235a4cc5fdabcb37469bca4"


def sha(p: Path) -> str: return hashlib.sha256(p.read_bytes()).hexdigest()

def replace_once(text: str, old: str, new: str, label: str) -> str:
    if text.count(old) != 1: raise RuntimeError(f"{label}: expected 1 occurrence")
    return text.replace(old, new, 1)

def main(root: Path) -> None:
    pkg=root/"src"/"brotoculateur"; dash=pkg/"dashboard.py"; l1=pkg/"l1_crystal_score.py"; dst=pkg/"l2_threshold.py"; src=Path(__file__).with_name("l2_threshold.py")
    if not all(p.is_file() for p in (dash,l1,src)): raise RuntimeError("missing dashboard/L1/L2")
    if dst.is_file() and '"l2_threshold": self.l2_threshold.status(),' in dash.read_text(encoding="utf-8"):
        print("L2_PATCH=ALREADY_APPLIED"); print("DASHBOARD.PY_SHA256="+sha(dash)); print("L2_THRESHOLD.PY_SHA256="+sha(dst)); return
    if sha(dash)!=PRE_DASH: raise RuntimeError("dashboard pre-hash mismatch")
    if sha(l1)!=PRE_L1: raise RuntimeError("L1 pre-hash mismatch")
    d=dash.read_text(encoding="utf-8")
    d=replace_once(d,"from .l1_crystal_score import L1CrystalScoreTelemetry\n","from .l1_crystal_score import L1CrystalScoreTelemetry\nfrom .l2_threshold import L2ThresholdTelemetry\n","import")
    d=replace_once(d,"        self.l1_crystal_score = L1CrystalScoreTelemetry()\n        self._lock = threading.RLock()\n","        self.l1_crystal_score = L1CrystalScoreTelemetry()\n        self.l2_threshold = L2ThresholdTelemetry()\n        self._lock = threading.RLock()\n","init")
    d=replace_once(d,"            self.l1_crystal_score = L1CrystalScoreTelemetry()\n            self._session_started_monotonic = None\n","            self.l1_crystal_score = L1CrystalScoreTelemetry()\n            self.l2_threshold = L2ThresholdTelemetry()\n            self._session_started_monotonic = None\n","reset")
    old="        self.l1_crystal_score.observe(formula_id, source, out, t8_outcome, t9_outcome, t10_outcome, t11_outcome, t12_outcome)\n"
    new="        l1_outcome = self.l1_crystal_score.observe(formula_id, source, out, t8_outcome, t9_outcome, t10_outcome, t11_outcome, t12_outcome)\n        self.l2_threshold.observe(formula_id, source, out, t8_outcome, t9_outcome, t10_outcome, t11_outcome, t12_outcome, l1_outcome)\n"
    d=replace_once(d,old,new,"callback")
    d=replace_once(d,'            "l1_crystal_score": self.l1_crystal_score.status(),\n','            "l1_crystal_score": self.l1_crystal_score.status(),\n            "l2_threshold": self.l2_threshold.status(),\n',"status")
    dash.write_text(d,encoding="utf-8",newline="\n"); shutil.copyfile(src,dst)
    print("L2_PATCH=PASS"); print("DASHBOARD.PY_SHA256="+sha(dash)); print("L1_CRYSTAL_SCORE.PY_SHA256="+sha(l1)); print("L2_THRESHOLD.PY_SHA256="+sha(dst))

if __name__=="__main__": main(Path(sys.argv[1]))
