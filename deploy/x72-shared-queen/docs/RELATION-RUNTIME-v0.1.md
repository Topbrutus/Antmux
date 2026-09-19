# X72 Relation Runtime v0.1

Status: CANDIDATE  
Authority: OBSERVATION_ONLY  
Mutates Queen: NO  
Physical claim: NO

## Why this exists

The Queen now has seven synapses with the complete undirected K7 topology:
21 relations, with degree six at every synapse.

Before this module, the gold dots on those lines were only browser animation.
They showed that a relation was visually active, but there was no server-side
counter telling us how many sampled pulses had occurred, when they occurred,
or what activity difference existed between the two endpoints.

Relation Runtime v0.1 moves those measurements to the Queen server.

## Sampling rule

The server samples all 21 relations every 60 Queen ticks.

At the current 240 Hz simulation cadence:

```text
240 / 60 = 4 relation samples per second
```

For relation A--B:

```text
signal_level = (activity_A + activity_B) / 2
pulse_active = endpoints healthy AND signal_level > 0.25
activity_delta = activity_B - activity_A
activity_gap = abs(activity_delta)
memory_gap = abs(memory_B - memory_A)
crystal_gap = abs(crystal_B - crystal_A)
```

The threshold 0.25 is not a new hidden constant: it formalizes the same
threshold that the original frontend already used to decide whether the gold
marker should be visible.

## Pulse count

At each 60-tick sample, an active relation increments its own pulse counter by
one. Each relation therefore exposes:

- pulse_count;
- last_pulse_tick;
- last_pulse_generation;
- current signal_level;
- current activity/memory/crystal gaps.

The runtime also exposes the total pulse count and the number of currently
active relations.

## Direction

v0.1 exposes an `activity_gradient_direction`.

The convention is:

```text
higher endpoint activity -> lower endpoint activity
```

This direction exists to make the software visualization deterministic and
measurable. It is not evidence of physical transport, neuroscience, or a real
particle moving between endpoints.

The API labels this explicitly as:

```text
HIGHER_ACTIVITY_TO_LOWER_ACTIVITY_VISUAL_CANDIDATE
physical_claim = false
```

## Integrity and checkpoints

Relation Runtime is observation-only and does not alter the Queen's protected
identity. Its counters are persisted in checkpoints so they survive a normal
service restart.

The relation telemetry is intentionally excluded from the authoritative Queen
whole-state hash. This allows a K7 checkpoint created before Relation Runtime
v0.1 to remain restorable without forcing another clean birth.

## Frontend

The browser now consumes the server Relation Runtime when it draws the K7
mesh. The current line level and whether a gold pulse is active come from the
server telemetry. The browser may interpolate the marker position for smooth
rendering, but it does not invent relation activity.

The telemetry panel exposes:

```text
RELATIONS    current / 21
REL. ACTIVES current active sampled relations
PULSES REL.  cumulative sampled pulses
```

## Validation

Dedicated contract:

```text
test_relation_runtime.py
16 / 16 PASS
```

It verifies sampling cadence, all 21 relations, pulse counting, explicit
gradient direction, checkpoint persistence, protected-state non-mutation,
whole-hash compatibility, and compatibility with a K7 checkpoint that predates
the telemetry module.
