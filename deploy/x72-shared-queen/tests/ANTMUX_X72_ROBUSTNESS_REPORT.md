# ANTMUX-X72 — Rapport de robustesse Worker 2

- Verdict: **PASS**
- Tests: **30/30 PASS**
- Queen: `QUEEN-X72-0072`
- Reference H256: `49e75d92d8fde33f402c3b60482bc5dcf13c12f09bd8c07c7937961d42ceaff9`
- Final protected H256: `49e75d92d8fde33f402c3b60482bc5dcf13c12f09bd8c07c7937961d42ceaff9`
- Integrity match: `True`
- Durée: `6.156 s`

## Catégories

- **concurrency** — PASS 2 / FAIL 0
- **errors** — PASS 3 / FAIL 0
- **fault** — PASS 1 / FAIL 0
- **health** — PASS 1 / FAIL 0
- **integrity** — PASS 3 / FAIL 0
- **multi-client** — PASS 2 / FAIL 0
- **persistence** — PASS 3 / FAIL 0
- **rate-limit** — PASS 1 / FAIL 0
- **repair** — PASS 2 / FAIL 0
- **restart** — PASS 1 / FAIL 0
- **security** — PASS 6 / FAIL 0
- **stress** — PASS 1 / FAIL 0
- **websocket** — PASS 4 / FAIL 0

## Tests

- `PASS` **no arbitrary execution/read channel** (security)
- `PASS` **Nginx X72 overwrites client X-Forwarded-For** (security) — trusted=True legacy=False
- `PASS` **health source/entity** (health) — source=QUEEN_SERVER_V0_2 entity=QUEEN-X72-0072
- `PASS` **baseline reference/integrity** (integrity)
- `PASS` **120 concurrent state reads** (stress)
- `PASS` **invalid synapse rejected** (errors) — {'detail': 'fault must be S1..S7 or RANDOM'}
- `PASS` **unsupported method rejected** (errors)
- `PASS` **admin surface absent /api/reset** (security)
- `PASS` **admin surface absent /api/reseed** (security)
- `PASS` **admin surface absent /api/exec** (security)
- `PASS` **admin surface absent /api/shell** (security)
- `PASS` **concurrent faults serialize to one winner** (concurrency) — [409, 409, 409, 409, 409, 409, 409, 200]
- `PASS` **concurrent repairs produce one PASS and no corrupt result** (concurrency) — pass_count=1 responses=[(409, None), (409, None), (409, None), (200, 'PASS'), (409, None), (409, None)]
- `PASS` **concurrent repair final hash closes** (integrity)
- `PASS` **clean repair command is explicit INVALID** (errors)
- `PASS` **same-IP mutation rate-limited** (rate-limit) — {'detail': 'rate limit: one public mutation per IP per 3 seconds'}
- `PASS` **16 simultaneous WebSocket clients** (websocket)
- `PASS` **two clients share entity/reference** (multi-client)
- `PASS` **S4 mutation accepted** (fault)
- `PASS` **S4 fault shared to both WebSockets** (multi-client)
- `PASS` **repair returns PASS** (repair) — {'verdict': 'PASS', 'reason': 'Protected state restored to reference.', 'changed_synapses': ['S4'], 'before_protected_h256': 'c5f711409cb91e33aee5a977d8d9622f040ae18c537fff3acb86f9ecf4f07861', 'after_protected_h256': '49e75d92d8fde33f402c3b60482bc5dcf13c12f09bd8c07c7937961d42ceaff9', 'reference_protected_h256': '49e75d92d8fde33f402c3b60482bc5dcf13c12f09bd8c07c7937961d42ceaff9', 'whole_state_h256': '9934df185d3123e7c8b512a8baed2c06992d43a58a845143644e164c338afd56'}
- `PASS` **repair hash closes for both clients** (repair)
- `PASS` **closing WebSocket client does not stop Queen** (websocket) — before=37 after=42
- `PASS` **restart restores latest persisted Queen checkpoint** (restart) — persisted=72 before=82 after=74
- `PASS` **WebSocket reconnect after restart** (websocket)
- `PASS` **SQLite checkpoint database exists** (persistence) — queen.db present
- `PASS` **multiple checkpoints persisted** (persistence) — rows=9
- `PASS` **corrupt newest checkpoint is rejected with fallback** (persistence) — entity=QUEEN-X72-0072 integrity=True
- `PASS` **8 simultaneous WebSocket clients** (websocket)
- `PASS` **final protected H256 equals reference** (integrity)
