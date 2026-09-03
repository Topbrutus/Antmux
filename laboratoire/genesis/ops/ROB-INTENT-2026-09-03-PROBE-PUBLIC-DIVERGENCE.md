# ROB INTENT — Genesis public divergence probe

Date: 2026-09-03
Authority: Topbrutus
Scope: diagnostic only

## Observed discrepancy

- GitHub/VPS deployment verification reported the interactive Genesis Vision Center and LIVE_READ_ONLY endpoint as valid.
- A later independent web crawler returned the older SNAPSHOT-only HTML.

## Goal

Establish a fresh three-way proof without modifying production content:

1. repository `main` expected `laboratoire/genesis/index.html`;
2. public `https://antmux.com/laboratoire/genesis/` response with cache-busting request;
3. same HTTPS virtual host forced directly to the pinned VPS origin.

Also validate the public and direct-origin LIVE JSON semantically for C062.

## Safety boundary

- diagnostic branch only;
- no production file mutation;
- no Seed Genesis mutation;
- no GESIS mutation;
- no generator mutation;
- no secret value printed;
- VPS host secret is used only through `curl --resolve` and remains masked;
- no C063;
- no real experiment execution.

## Classification

- all three index bodies identical + C062 LIVE valid: `PROBE_PASS_CRAWLER_STALE`;
- origin matches repository but public differs: `EXTERNAL_CACHE_OR_ROUTING_DIVERGENCE`;
- public and origin agree but differ from repository: `ORIGIN_DEPLOYMENT_DIVERGENCE`;
- origin itself differs from repository: fail closed and diagnose before any scientific continuation.
