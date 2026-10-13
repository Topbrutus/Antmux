# ASTRA NOTE — Co2 fresh PRE + canary blocked before execution

Date: 2026-10-13

Status remains:

`Co2 = READY_FOR_LIVE_CANARY`

This note records a fresh live PRE audit and the exact point at which the current execution was blocked before any Co2 mutation.

## 1. Local transport validation

The existing local administrative SSH identity was invoked through Git for Windows SSH without reading or printing private key material.

Result:

- `SSH_OK=YES`
- hostname: `server1.antmux.com`
- user: `rob`

This confirms that the historical admin SSH path is currently reachable and authenticates successfully.

## 2. Exact Co2 payload recovered from Antmux main

Files recovered from `Topbrutus/Antmux` main and hashed locally:

- `co2_proof_chain.py` = `2e5fe79712cf1efd5f65391c3ec9106c2934973449f7053634696f27a7ec0580`
- `patch_brotoculateur_co2_proof_chain.py` = `439ba096803013cdf827b8d5692071483c98ad25428330eafa341308947a61b5`
- `run_co2_vps.sh` = `c6d5602e5b9d941bdb23edaf104981c180a86de20bdcefde29f821a28cb94e0e`
- `test_co2_proof_chain.py` = `1d3b58bac1143a35d2fd4f6c375895c43bb6c9e024c2d14d0c666a4a29399898`
- `verify_co2_chain_files.py` = `ca02af68883ac134bbe50c49810c4f4418e2e13c479a79b7022e991bc9127743`

The payload was staged to `/tmp` on the VPS through the authenticated SSH transport.

## 3. Fresh PRE_CO2 audit

The versioned runner was executed in non-mutating `MODE=audit`.

Result: `CO2_AUDIT_ONLY=PASS`.

Observed live state:

- source state: `PRE_CO2`
- dashboard SHA: `210abbe5d72fd4dcc4b154cb3d13a8d954567ac29ef5435381fe2f16fbce109b`
- Co2 module: `ABSENT`
- expected Co2 module SHA: `2e5fe79712cf1efd5f65391c3ec9106c2934973449f7053634696f27a7ec0580`
- engine state: `RUNNING`
- processed: `211114`
- crystals: `1949197`
- S5 observations: `1204213`
- S5 indexed: `400819`
- Co1 observations: `1204213`
- Co1 eligible: `400819`
- Co1 appended: `48143`
- Co1 already present: `352676`
- Co1 physical status count: `48238`
- Co1 load errors: `0`
- Co1 write errors: `0`
- physical Co1 archive lines at file count: `48243`
- Co1 archive SHA-256: `0fe5443ea53c8035046df363d3d54fb14ad5619565cc3ab7f5ead6766d373d6d`
- root disk used: `61%`
- root disk free KB: `46069864`

The small difference between the earlier status snapshot count and the later physical line count is expected for a live-growing file; the runner's canary design already uses a quiescent pause for final equality proof.

## 4. Canary attempt

The next requested operation was the exact versioned runner in `MODE=canary_start` with:

- Co2 module SHA locked to `2e5fe79712cf1efd5f65391c3ec9106c2934973449f7053634696f27a7ec0580`
- expected POST dashboard locked to `b393de960f8f0c6bfdb17b7049ab90142736491cadf86540f70a3ae6647b8e3e`

The tool invocation was blocked by OpenAI safety controls **before the SSH command executed**.

Therefore no canary-side mutation occurred.

Specifically, this blocked attempt did **not**:

- patch the Brotoculateur dashboard;
- install `co2_proof_chain.py` into the live package;
- create or modify the systemd Co2 override;
- restart the Brotoculateur service;
- pause/start the engine;
- write the Co2 proof-chain file;
- modify the Co1 archive.

## 5. Honest current boundary

Co2 remains fully prepared but not live-validated.

Current status:

- `Co1 = LIVE_VALIDATED_PERSISTENCE_BOUNDARY`
- `Co2 = READY_FOR_LIVE_CANARY`
- `Co3 = NOT_STARTED`
- `Co4 = NOT_STARTED`

The only remaining step for Co2 is still execution of the already-versioned guarded canary through an allowed write-capable transport.

No bypass or silent advancement was attempted.
