# Genesis Vision Center — LIVE_READ_ONLY Policy v1

Status: `EVALUATION_ONLY / NOT_ACTIVATED`

## Goal

Define the minimum security and scientific boundary required before a real `LIVE_READ_ONLY` public feed can exist.

## Required architecture

`PRIVATE GENESIS -> SERVER-SIDE READ-ONLY BRIDGE -> STRICT PUBLIC WHITELIST -> PUBLIC_READ_ONLY ENVELOPE -> VISION CENTER`

The browser must never receive credentials and must never contact the private source directly.

## Mandatory controls

- dedicated least-privilege read-only credential, isolated from the browser;
- no write API, write token, push permission or mutation route in the bridge;
- deny-by-default field projection with an explicit public whitelist;
- no raw private files, seeds, raw experiment bodies, private ROOT digests, private paths, internal network topology or credentials;
- public output validated against the public contract before release;
- bounded freshness window;
- stale data => reject/fail closed, never silently relabel stale data as live;
- bridge failure => fail closed; the already validated frozen snapshot may remain available as a separate fallback view;
- public integrity digest over the released public projection;
- rate limiting/cache at the public boundary;
- audit metadata may record success/failure but must not log private payload bodies or secrets;
- explicit kill switch capable of returning the Vision Center to `SNAPSHOT` without touching private Genesis;
- public browser requests to private-looking routes must remain denied/not found;
- `MESURE != INTERPRÉTATION` and all epistemic classes remain preserved.

## Source eligibility

A private canonical file is not automatically a public source. Raw private source material must first be reduced to an opaque public attestation and an explicitly whitelisted projection.

Public live output may expose only facts already classified for public release. It must not expose private repository identifiers, private branch names, private commit identifiers, private ROOT values, raw seed lists or raw scientific result bodies unless each item has undergone a separate explicit publication decision.

## Evaluation semantics

Passing the evaluation battery means only:

`READY_FOR_CONTROLLED_IMPLEMENTATION_NOT_ACTIVATED`

It does not mean:

- `LIVE_READ_ONLY=PASSED`;
- a real private connection exists;
- the public site is live-connected;
- Genesis has write capability;
- a private scientific claim has been promoted to public evidence.

During this phase the publication gate remains:

`LIVE_READ_ONLY=PENDING`

## Activation gates for a later phase

Before activation, a separate implementation must prove all of the following on an isolated branch and CI:

1. server-side bridge authentication works with read-only permissions only;
2. browser has zero private credentials and zero direct private requests;
3. whitelist projection rejects unknown/private fields;
4. freshness and stale rejection are tested;
5. network/bridge failure is fail-closed;
6. public integrity digest is verified;
7. private source mutation is impossible through the public path;
8. rollback/kill-switch to the frozen snapshot is tested;
9. HTTP + Chromium tests show `PUBLIC_READ_ONLY` only after all preceding controls pass;
10. deployment requires a separate explicit authorization.
