# BRUTUS — TURNKEY CHECKPOINT — 2026-09-26

## Scope
Software control desk checkpoint for laboratoire/parazone-x72-d13-v2/.

## Ready path
REFERENCE TABLE -> PRESET -> GENERATOR CONFIG -> SOURCE -> SAMPLER -> AMPLITUDE / CADENCE / ACTIVITY

## Source modes
- MICROPHONE-SOURCE-01: real local browser microphone input with explicit browser permission.
- Microphone amplitude is digital RMS and is not calibrated dB SPL.
- T1 remains available as a local fallback/test source.

## Controls
- START: prepares an active source, arms a saved preset when available, starts sampling.
- PAUSE: stops sampling without destroying configuration.
- STOP: stops sampler, stops automatic frequency table, clears generator config, and closes microphone input.
- Automated frequency table changes configuration references only. It does not claim physical effects.

## Measurement truth
- AMPLITUDE: current source amplitude.
- CADENCE: effective local sampling/update cadence.
- ACTIVITY: absolute amplitude change between consecutive observations.
- Connection-only stages T2-T5 are not called measurements.
- Proof hashes document software records; they do not prove physical efficacy.

## Output boundary
OUTPUT-ADAPTER-01 adds an explicit browser-audio output path.
- Manual enable is required.
- Sine wave only.
- Frequency range: 20–20000 Hz.
- Gain is capped at 0.05 and derived from preset amplitude.
- The automatic frequency table does not start audio by itself.
- MASTER STOP always disables audio output.
- No non-audio external actuator is enabled by this checkpoint.

## Acceptance checks
1. JavaScript syntax passes node --check.
2. git diff --check passes.
3. Deployment marker BRUTUS // MOTEUR DE RÉSONANCE remains present.
4. Frequency table previous/next/auto changes preset configuration.
5. Essential monitor exposes amplitude, cadence, activity.
6. START/PAUSE/STOP transition without stale sampler state.
7. Browser microphone path is permission-gated and can be stopped cleanly.
