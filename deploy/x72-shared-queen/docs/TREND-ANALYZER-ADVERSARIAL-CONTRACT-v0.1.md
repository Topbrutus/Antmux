# X72 Trend Analyzer — Adversarial Contract v0.1

Status: independent validation harness prepared by Worker 2.

## Purpose

This suite is intentionally separate from the future X72TrendAnalyzer implementation.
It defines adversarial windows and expected dispositions without importing Worker 1 code.

Target binding expected by the runner:
- module: `observation_trend`
- class: `X72TrendAnalyzer`
- callable surface: `analyze(records)`, `analyze_window(records)`, or callable instance.

If the target is absent, the runner returns a structured BLOCKER rather than inventing a pass.

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

When a candidate exists, accepted cases are executed twice on deep-copied inputs.
Byte-equivalent canonical outputs are required.

## Current blocker

At baseline `96880747b53e12b85c3c0a38e795303745aff5ea`,
`observation_trend.X72TrendAnalyzer` is not present on main.
The validation layer is ready, but implementation-level adversarial execution is therefore blocked until a candidate exists.
