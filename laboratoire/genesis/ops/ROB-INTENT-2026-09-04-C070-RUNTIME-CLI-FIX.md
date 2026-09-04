# ROB INTENT — C070 runtime CLI fix

Date: 2026-09-04
Authority: Topbrutus
Operator: ChatGPT/Rob
Parent Antmux main: `f6fd8bcb3ec856950aaad34f023129243d694b22`
Failed deploy run: `33854296833`

## Evidence-driven cause

The corrected C069/C070 functional batteries pass, but the C070 builder and bridge are export-only modules. The deploy smoke step invokes them as CLI files, so no output artifact is written and validation fails before any VPS/SSH step.

## Exact fix

- add the same CLI façade pattern already used by C069 to `build-public-source-progressive-c070.mjs`;
- add the same CLI façade pattern already used by C069 to `bridge-public-progressive-c070.mjs`;
- add an explicit C070 CLI smoke check to the existing C069/C070 test battery;
- preserve all scientific assertions, public projection values, privacy scans, and read-only boundaries;
- do not touch Seed LIVE, GESIS, or C071.

No VPS state was modified by the failed run because upload/install steps were skipped.
