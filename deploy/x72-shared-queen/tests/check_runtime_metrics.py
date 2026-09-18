from __future__ import annotations

import json
import os
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME_DIR = ROOT / ".contract-runtime"
if RUNTIME_DIR.exists():
    shutil.rmtree(RUNTIME_DIR)
RUNTIME_DIR.mkdir(parents=True, exist_ok=True)

os.environ["ANTMUX_X72_DATA_DIR"] = str(RUNTIME_DIR)
sys.path.insert(0, str(ROOT))

from app.server import QueenCore  # noqa: E402

queen = QueenCore(seed=72)
for _ in range(120):
    queen.step()

historical_tick = queen.tick
checkpoint = queen.to_checkpoint()
restored = QueenCore.from_checkpoint(checkpoint)
assert restored.tick == historical_tick
assert restored.runtime_start_tick == historical_tick
assert restored.entity_id == queen.entity_id
assert restored.reference_h256() == queen.reference_h256()

fresh = restored.visual_state()
assert fresh["tick_count"] == historical_tick
assert fresh["r_exec"] == 0.0
assert fresh["f_rt"] == 0.0

time.sleep(0.05)
for _ in range(12):
    restored.step()
time.sleep(0.05)
running = restored.visual_state()

assert running["tick_count"] == historical_tick + 12
assert 1.0 < running["r_exec"] < 1000.0
expected_frt = running["r_exec"] * restored.dt_sim
assert abs(running["f_rt"] - expected_frt) < 0.01

print(json.dumps({
    "verdict": "PASS",
    "historical_tick": historical_tick,
    "restored_tick": fresh["tick_count"],
    "runtime_r_exec": running["r_exec"],
    "runtime_f_rt": running["f_rt"],
}, sort_keys=True))

shutil.rmtree(RUNTIME_DIR, ignore_errors=True)
