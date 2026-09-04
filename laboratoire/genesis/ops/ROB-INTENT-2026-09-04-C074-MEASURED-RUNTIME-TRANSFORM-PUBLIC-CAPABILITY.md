# ROB INTENT — Antmux C074 measured runtime-transform public capability

Date: 2026-09-04
Authority: Topbrutus
Parent Antmux main: `c86f67dc6d9c6126e60908c3b6adc27e9334cd82`
Seed C074 closure: `84582b2a7c53c7c51d4b7a18ac6650365135e8e1`
Current public LIVE before work: C073 / 95 lines.

## Objective
Extend the existing progressive Genesis public read-only runtime so it can validate and render an exact future C074 public projection while keeping the currently active Seed source at C073 until a separate explicit manual publication.

## Public meaning to preserve
C074 scientific closure is VALIDATED while its deterministic decode verification verdict is a measured negative finding:
- stage = `VALIDATED_10_OF_10`;
- claim class = `MEASURED`;
- verdict = `FAIL_RUNTIME_DECODE_TRANSFORM`;
- finding = `AUDIO_CONTEXT_SAMPLE_RATE_TRANSFORM_DETECTED`;
- encoded control rate = 48000 Hz;
- recorded runtime AudioContext rate = 44100 Hz;
- decoded rate = 44100 Hz;
- decoded frames = 44099;
- repeated same-runtime receipt match = true;
- cross-runtime equivalence remains false.

The runtime must never rewrite this into `PASS_EXACT_REFERENCE` and must never imply that a failed verification verdict means the C074 scientific audit failed.

## Public projection boundary
Only non-sensitive semantic fields may be projected. Internal repository names, commits, candidate/closure SHAs, audit/run IDs, runtime identity digest, ingest/handoff digests, PCM hashes, receipt hash, measurement-record digest, file paths, provider/model/prompt/style metadata, and credentials remain private.

## Runtime boundary
- Reuse the existing progressive builder/bridge chain.
- Reuse the existing PR validation workflow and privileged VPS deploy workflow; create no new privileged deployment path.
- Runtime remains `LIVE_READ_ONLY`, write capability `NONE`.
- Current C073 source must remain accepted unchanged.
- C074 becomes only the maximum supported runtime stage until Seed publication.
- No write to Seed Genesis or GESIS.
- No real experiment and no experimental audio generation.
- No C075 implementation.
