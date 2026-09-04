# ROB INTENT — Genesis progressive LIVE C068

Date: 2026-09-04
Authority: Topbrutus
Operator: ChatGPT/Rob
Base Antmux main: `460d870338eb104987e0428f448c143112786132`

## Objective

Prepare the existing server-side fail-closed public read-only bridge to accept an eventual Seed Genesis C068 public projection without publishing C068 now and without exposing private generator identity evidence.

## Public C068 contract

C068 may expose only the following new public facts beyond exact C067:

- `genesis003_validated_through=C068`
- `genesis003_c068=VALIDATED_10_OF_10`
- `execution_bindings_bound=6`
- `execution_bindings_unbound=5`
- `real_generator_identity_frozen=true`
- `real_generator_bindings_added=3`
- `runtime_compatibility_verified=false`
- `language_coverage_verified=false`
- `language_confound_registered=true`
- `next_scientific_action=FREEZE_REAL_GENERATION_REQUEST_PROFILE`

The existing C067 public facts remain preserved, including no real experiment execution and the read-only bridge boundary.

## Forbidden public data

The public bridge must reject or never project:

- generator provider value;
- model name;
- model version/build or immutable model revision;
- runtime repository/revision;
- private Seed Genesis C068 SHA/digests;
- prompt bytes/hashes;
- private paths/branches/repositories;
- credentials or secrets.

## Fail-closed requirements

- preserve exact C060–C067 support;
- accept only exact whitelisted C068 key/value projection;
- reject C068 with an extra key, missing key, mutated count, invented runtime compatibility or invented language coverage;
- public output remains `LIVE_READ_ONLY`, source `PUBLIC_READ_ONLY`, integrity `VERIFIED_PUBLIC`, write capability `NONE`;
- package smoke test must execute the exact assembled runtime before VPS upload;
- current public C067 must remain accepted during deployment.

## Boundary

This Antmux change prepares capability only. It does not scientifically close C068, does not publish C068 from Seed Genesis, does not select or expose the private model identity, does not execute any model, does not create audio, and does not start C069.
