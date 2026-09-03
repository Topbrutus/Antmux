# ROB INTENT - PREPARE_SNAPSHOT_VIEW VALIDATE DEPLOY VPS

Mission: PREPARE_SNAPSHOT_VIEW -> VALIDATE -> DEPLOY VPS
Date: 2026-09-03
Branch: prepare-snapshot-view-validate-deploy
Base: origin/main b0ec8a1a6987133307f961da657a8cab930d90ad

Scope:
- Display the frozen public snapshot in Genesis Vision Center.
- Keep historical DEMO files available but separated from SNAPSHOT mode.
- Include the public snapshot JSON in the deployable Genesis bundle and existing VPS workflow.
- Keep LIVE_READ_ONLY blocked at PENDING.

Forbidden:
- No direct seedgenesis access.
- No private ROOT, private raw data, or secrets.
- No generator path or generator file changes.
- No LIVE_READ_ONLY unlock.
