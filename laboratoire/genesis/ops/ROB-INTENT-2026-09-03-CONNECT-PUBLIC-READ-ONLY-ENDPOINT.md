# ROB INTENT — CONNECT PUBLIC READ-ONLY ENDPOINT

Date: 2026-09-03
Base main: 9d907315c93f02740a004b477924902babb61a40
Branch: genesis/connect-public-read-only-endpoint

## Objective
Connect the validated server-side Genesis public read-only bridge to a public endpoint consumed by the Genesis Vision Center, so the page can follow a sanitized server-produced projection without redeploying the cockpit for each data update.

## Required architecture
PRIVATE SOURCE -> SERVER-SIDE READ ONLY -> STRICT WHITELIST/BRIDGE -> PUBLIC READ-ONLY ENDPOINT -> BROWSER

## Safety invariants
- Browser must never access Topbrutus/seedgenesis directly.
- No private credentials, private repo URL, private branch/ref, raw seed list, raw per-seed results, private ROOT digest, token, key, or filesystem path may reach the public endpoint.
- Server source access is READ_ONLY; write capability to private Genesis is NONE.
- Public bridge is fail-closed.
- Stale or future-dated source is rejected.
- Frozen snapshot 0001 remains mandatory fallback.
- /generator/ is out of scope and must not change.
- Existing public site remains functional during rollout.
- No claim of LIVE_READ_ONLY activation until endpoint, cockpit fallback, deployment, and public verification all pass.

## First action
Run a non-secret VPS capability probe. Report only capability booleans (no credentials or private content): private repo read access yes/no, node/python/curl/crontab availability, target write access.

## Publication discipline
Read/probe first. Implement only after capability evidence. PR + CI before merge. VPS deployment remains explicit and verified.
