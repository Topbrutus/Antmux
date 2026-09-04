# ROB INTENT — Deploy progressive LIVE runtime through corrected C070

Date: 2026-09-04
Authority: Topbrutus
Operator: ChatGPT/Rob
Parent Antmux main: `55082affbfd7cc3f86dabac9ccdc3b337ea2a448`

## Purpose

Upgrade the existing trusted progressive LIVE deployment package from maximum stage C068 to corrected C070 capability before any Seed public projection advances beyond C068.

## Required progression

- preserve legacy C060-C068 behavior;
- accept corrected C069 only as signal/GESIS technical reproducibility with bindings 11/6/5;
- accept C070 only with analysis decision rule bound and bindings 11/7/4;
- preserve LIVE_READ_ONLY / PUBLIC_READ_ONLY / VERIFIED_PUBLIC;
- package C069 and C070 parser/bridge modules and make C070 the progressive top-level runtime alias;
- allow source line counts 61 and 63 in addition to historical counts;
- do not change the current public Seed source;
- do not start C071;
- do not expose private provider/model/repository identifiers or private digests.

## Safety

Use the existing deployment workflow and existing VPS credentials only. Validate via pull request first. No new secret, credential, endpoint, or deployment mechanism is introduced. If the existing workflow update is blocked by platform security, do not bypass it.
