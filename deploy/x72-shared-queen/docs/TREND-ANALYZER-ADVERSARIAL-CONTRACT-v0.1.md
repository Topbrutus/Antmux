# X72 Trend Analyzer — Adversarial Contract v0.1

Status: independent validation harness prepared by Worker 2.

## Purpose

This suite is intentionally separate from the future X72TrendAnalyzer implementation.
It defines adversarial windows and expected dispositions without importing Worker 1 code.

Target binding expected by the runner:
- module: `trend_analyzer`
- class: `X72TrendAnalyzer`
- callable surface: `analyze(history: X72ObservationHistory)`

The harness builds every candidate input through the public
`X72ObservationHistory.append(ObservationEnvelope)` interface. It never
constructs private invalid History state. Invalid adversarial inputs rejected
there are classified `EXPECTED_REJECTION_UPSTREAM`.

If the target is absent, the runner returns a structured BLOCKER rather than
inventing an implementation-level pass.

## Read-only boundary

The suite validates only observation-history inputs. It does not:
- call Queen mutation routes;
- inject faults into the live Queen;
- repair the Queen;
- deploy;
- create a local QueenCore.

The source guard rejects a candidate containing local QueenCore authority or mutation transport markers.

## Adversarial coverage

The corpus covers:
- empty and incomplete histories;
- entity identity mismatch and mid-window identity change;
- tick regression, duplicate tick, and very large tick;
- missing r_exec/f_rt;
- NaN, infinity, wrong numeric types, and impossible negatives;
- event_count regression;
- incoherent synapse counts;
- repeated STALE and repeated RECONNECTED observations;
- fault without repair and repair without prior fault;
- H256 contradiction and H256 restoration;
- reversed history order;
- UNKNOWN / SCHEMA_MISMATCH;
- exact bounded capacity and over-capacity rejection.

## Determinism

The contract manifest is canonically serialized and hashed.
The corpus self-check verifies:
- fixed case IDs;
- expected rejection classification;
- input immutability;
- deterministic manifest independent of construction order;
- bounded maximum input window.

When a candidate exists, accepted bounded Histories are analyzed twice through
`X72TrendAnalyzer.analyze(history)`. Byte-equivalent canonical outputs are
required, and History records plus its deterministic report must remain
unchanged before/after analysis.

## Current blocker

At baseline `96880747b53e12b85c3c0a38e795303745aff5ea`,
`trend_analyzer.X72TrendAnalyzer` is not present on main, so PR #54 remains a
standalone hardening layer.

A temporary detached integration worktree was built from candidate PR #55 at
`e80732878192eafd87c10ecdb72a92b5910ba112`, with only this harness copied
into it. Real candidate cross-validation passed 30/30 checks with seven
`EXPECTED_REJECTION_UPSTREAM` cases and no candidate failure.
