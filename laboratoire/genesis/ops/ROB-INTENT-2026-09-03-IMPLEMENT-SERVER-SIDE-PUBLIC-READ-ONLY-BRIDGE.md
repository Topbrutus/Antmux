# ROB INTENT - IMPLEMENT_SERVER_SIDE_PUBLIC_READ_ONLY_BRIDGE

Mission: IMPLEMENT_SERVER_SIDE_PUBLIC_READ_ONLY_BRIDGE
Date: 2026-09-03
Branch: implement-server-side-public-read-only-bridge
Base: origin/main 1b4933884e4e5f4f95a48c6f168775118ba31b08

Scope:
- Implement a server-side public read-only bridge harness.
- Produce only a strict public `LIVE_READ_ONLY / PUBLIC_READ_ONLY` envelope from an explicitly whitelisted server-side source projection.
- Validate freshness, fail-closed behavior, public digest, no browser private credentials, no write capability, and snapshot fallback.
- Keep the deployed Vision Center source on the frozen public snapshot until a separate deployment/activation mission.

Forbidden:
- No direct seedgenesis access.
- No browser credential path.
- No write or mutation route.
- No private ROOT, raw source, private branch, private path, or secret exposure.
- No generator file changes.
