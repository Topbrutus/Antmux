# ASTRA CHECKPOINT — Brutus C3 Bibliothèque 37

Date: 2026-10-13
Status: exact-source local validation complete; guarded VPS deployment not yet executed at checkpoint creation.

## Position in the recorded Brutus 37 path

C1 Entrée / Cortex Z -> C2 Empreinte canonique -> C3 Bibliothèque.

C3 is the first memory layer behind the canonical C2 fingerprint. This canary is intentionally shadow-only: it observes and counts knowledge reuse but does not skip calculations or influence scheduling.

## C3 identity and 37-way routing

- Identity is the full 256-bit C2 fingerprint.
- C2 volatile exclusions remain unchanged: packet UUIDs, parent UUIDs, and branch path do not enter the canonical fingerprint.
- C3 converts the 64 hexadecimal C2 digest characters to 32 raw bytes for a compact dictionary key.
- Bucket route = first 64 bits of the full C2 digest modulo 37.
- The bucket number is routing only; the full 256-bit key remains the identity.
- There are exactly 37 in-memory buckets.

## Bounded memory

Canary default:

- `BROTO_C3_ENABLED=1`
- `BROTO_C3_MAX_ENTRIES=131072`

When the library reaches the entry cap, a previously unseen fingerprint is counted as a capacity rejection and is not retained. Existing retained entries continue to produce hits. C3 therefore has a hard growth bound at the application-entry level.

Stored per retained fingerprint:

- 32-byte C2 key;
- integer observation count.

C3 does not store a second copy of the packet, branch path, formula trace object, or crystal payload.

## Safety contract

C3 status explicitly reports:

- `authority = SHADOW_ONLY`
- `persistent = false`
- `query_before_compute = false`
- `compute_skips = 0`
- `scheduling_influence = false`
- `value_mutated = false`
- `proof_promotion = false`

The current canary cannot replace a formula evaluation. It only measures whether a C2 fingerprint was already known in the current Brotoculateur session.

## Session and round behavior

The library belongs to `DashboardService`, not to a single `ExperimentRunner`.

- A normal runner/round rollover receives the same C3 library instance.
- A full experiment reset creates a fresh C3 library.
- A service restart creates a fresh C3 library.
- This version is intentionally non-persistent on disk.

This placement lets repeated structural states across rounds become C3 hits without changing runner scheduling.

## Exact live source baseline

C3 is built against the exact post-C2 VPS source hashes:

- engine.py: `ac956512699ab0bb527449e08fdaeafab9c883eea3565c4abc5d8e4fcc9ac31b`
- orchestrator.py: `20e019e58f77fbd0ea5a983112b8ed5809bad236d8f02df52ea3c65f710f0f83`
- dashboard.py: `5410dc0aebb273eddf616dc3b08e53666f6473c25eb5a00ebb44003f2bb00ce2`
- sleeping_pool.py: `1fe651ff70e4cad7afc8ec216cbad5f361ff839c072408dcc0233e0a0c637124`

Expected post-C3 hashes from the exact-source local patch:

- c3_library.py: `b7970583e688488d0f9fd8a90838d9163d00b08b7e6afedd499434e79a06c434`
- orchestrator.py: `2ba8a93967e3f01147acbd2a5220857830cd89ce3bdcba879e8d5630292fdb87`
- dashboard.py: `2602f91205457dc8b474ab098a0ed4453153054ff0ef4f9f73b9c2eca4ccc157`

Engine and Sleeping Pool are not modified by C3.

## Local validation

Exact post-C2 source copy patched to C3:

- Python compile: PASS
- patch idempotency: PASS
- workflow YAML parse: PASS
- 37-bucket shape: PASS
- volatile C2-equivalent packets collapse to one C3 entry: PASS
- semantic C2 change produces a distinct C3 entry: PASS
- 37-entry capacity guard test: PASS
- current five-seed Z 10 percent canary bridge C2 -> C3: PASS
- shared library survives runner rollover: PASS
- second `343` root in a new runner becomes a C3 hit: PASS
- `compute_skips = 0`: PASS

Observed local canary bridge test:

`C3_CANARY_10=PASS 2 2 0 2`

Observed rollover test:

`C3_ROLLOVER=PASS 2 1 1`

## Local performance probes

These are local implementation probes, not VPS throughput claims.

- 200,000 repeated observations of one fingerprint: 0.396936 s; 199,999 hits; one retained entry.
- 100,000 unique observations: 1.982558 s.
- `tracemalloc` peak for that 100,000-unique Python probe: approximately 9.636 MiB.

The probe supports trying the bounded shadow canary; it does not establish universal memory or latency complexity for the full VPS process.

## Last pre-C3 live audit

Before C3 deployment work, the C2 audit remained healthy:

- state: RUNNING
- processed packets: 45,995
- crystals: 1,567,903
- Z-STAMP: enabled at 10 percent
- Z roots / children: 19 / 154,420
- C2 roots / children: 19 / 154,420
- C2 total fingerprints: 154,439
- Papillon rarity: 10 percent
- root disk: 58 percent used
- no source hash drift

## Deployment gate

The C3 workflow must:

1. recognize exact PRE_C3 or POST_C3 source hashes;
2. require healthy C2 and Z-STAMP 10 percent before canary start;
3. patch and test an exact staged copy before pausing the live service;
4. save and pause through the official API;
5. create a rollback backup;
6. install the bounded C3 feature drop-in;
7. restart and verify no worker error;
8. require C3 observations to equal C2 total fingerprints;
9. require hits + misses = observations;
10. require `compute_skips = 0`;
11. restore prior source/drop-in/running state automatically on any post-mutation error.

## Next gate after a successful C3 canary

Do not enable query-before-compute yet. First measure live:

- hit rate;
- unique-entry growth rate;
- capacity saturation;
- 37-bucket balance;
- process memory impact;
- equality C2 fingerprints == C3 observations over time.

Only after those measurements should C4 Nouveauté or a guarded read-before-compute experiment be considered.
