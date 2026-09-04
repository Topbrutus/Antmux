# ROB INTENT — FIX C067 PROGRESSIVE LIVE PACKAGE IMPORT

Date: 2026-09-04
Authority: Topbrutus
Operator: Rob / ChatGPT
Repository: `Topbrutus/Antmux`
Branch: `genesis/fix-progressive-live-c067-package-import-20260904`
Base main SHA: `cfc499b9ed4c646db994817692809b44bf3c6eec`
Failed deployment run: `33835234575`

## Proven failure

The progressive C066/C067 runtime source and adversarial tests passed, but VPS deployment failed before the cron switch.

The deployed package renamed:
- `build-public-source-progressive-c067.mjs` to `build-public-source-progressive.mjs`;
- `bridge-public-progressive-c067.mjs` to `bridge-public-progressive.mjs`.

The bridge source still imports `./build-public-source-progressive-c067.mjs`, so the VPS runtime raised `ERR_MODULE_NOT_FOUND` after installation.

## Intent

Fix only the deployment packaging/import boundary without changing Genesis scientific semantics or public projection semantics.

## Minimal safe change

- Preserve the original C067 builder and bridge filenames in the deploy package.
- Install those exact filenames on the VPS.
- Point `GENESIS_BUILDER` and `GENESIS_BRIDGE` at those exact filenames.
- Add a pre-upload smoke test that executes the packaged builder and bridge from the package layout itself, so relative imports are proven before SSH/VPS mutation.
- Keep the existing VPS SSH/deploy workflow and existing read-only Seed Genesis source path; create no new privileged channel.
- Keep fail-closed source line counts C060 through C067.
- Verify the public endpoint after deploy.

## Boundaries

- Do not modify Seed Genesis science.
- Do not modify GESIS.
- Do not close C067.
- Do not start C068.
- Do not change browser/write capability boundaries.
- Do not expose private repository data, credentials, hashes, binding values, or source paths publicly.
- If package smoke test, VPS preflight, deploy, or public verification fails, stop fail-closed and preserve the existing public endpoint.
