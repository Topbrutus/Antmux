from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.server import QueenCore

GENERATIONS = 20
queen = QueenCore(seed=72)
queen.z3_runtime.observe = lambda **_: False
queen.relation_runtime.observe = lambda **_: False

for _ in range(7200 * GENERATIONS):
    queen.step()

memory = [synapse.memory for synapse in queen.synapses]
crystal = [synapse.crystal for synapse in queen.synapses]

assert queen.generation == GENERATIONS
assert queen.integrity_match() is True
assert max(memory) < 0.70
assert max(crystal) < 0.70
assert min(memory) > 0.10
assert min(crystal) > 0.10

print(json.dumps({
    "schema": "ANTMUX-X72-LONG-RUN-HOMEOSTASIS-v0.1",
    "generations": queen.generation,
    "max_memory": max(memory),
    "max_crystal": max(crystal),
    "integrity_match": queen.integrity_match(),
    "verdict": "PASS",
}, sort_keys=True))
