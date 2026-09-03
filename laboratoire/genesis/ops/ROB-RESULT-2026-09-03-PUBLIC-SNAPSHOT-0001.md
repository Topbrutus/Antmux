# ROB RESULT — PUBLIC SNAPSHOT 0001 — 2026-09-03

## Verdict

`PUBLIC_SNAPSHOT_0001 = COMPLETE_VALIDATED_ON_BRANCH`

Le premier snapshot public figé dérivé d'un état Seed Genesis vérifié a été construit comme **projection publique minimale**. Aucune donnée privée brute ni identifiant privé de source n'est recopié dans le snapshot.

## Références publiques

- repository: `Topbrutus/Antmux`
- base main: `61ad089166ec0ef6ee915e259348a9b732298200`
- branch: `genesis/snapshot-validation-0001`
- PR: `#13`
- validation run: `33722011884`
- run conclusion: `SUCCESS`
- publication: `GENESIS-PUBLIC-SNAPSHOT-0001`
- mode: `SNAPSHOT`
- source_status: `PUBLIC_SNAPSHOT`
- integrity_status: `VERIFIED_PUBLIC`

## Source et projection

Une lecture minimale de la preuve de clôture GENESIS-003/C060 et de son audit de clôture a été effectuée avant la projection. Les identifiants privés de cette source ne sont pas publiés.

Faits publiés :

- `GENESIS-003 C041-C060 = COMPLETE_VALIDATED`;
- `selected_experiment_status = PLANNED_NOT_EXECUTED`;
- `hypothesis_selection_performed = false`;
- `probabilities_produced = false`;
- `evidence_ledger_auto_promotion = false`;
- `source_closure_audit = SUCCESS`.

Digest déterministe de cette projection publique :

`sha256:4202421e82f9d7e39f8b2f9a734dc2e7e2e30d94dd2212ace238d3deb96bee2f`

Ce digest est celui de la projection publique, **pas** un ROOT digest privé.

## Correctif de frontière

Avant le snapshot, le validateur v2 autorisait `SNAPSHOT` mais imposait encore les invariants DEMO. La validation distingue maintenant strictement :

- `DEMO + SYNTHETIC`;
- `SNAPSHOT + PUBLIC_SNAPSHOT`;
- `LIVE_READ_ONLY` interdit à cette phase.

Les payloads SNAPSHOT peuvent rester minimaux conformément au contrat : l'absence d'une catégorie signifie qu'aucune donnée de cette catégorie n'est publiée.

## Tests

Sur le run `33722011884` :

- historique v1 adversarial: `12/12 PASS`;
- public v2 adversarial: `35/35 PASS`;
- Public Adapter adversarial: `16/16 PASS`;
- Snapshot 0001 validator: `PASS`;
- Snapshot 0001 adversarial: `15/15 PASS`;
- smoke HTTP: `PASS`;
- Chromium desktop/mobile: `PASS`;
- navigation publique: `PASS`;
- browser console errors: `0`;
- browser page errors: `0`.

Snapshot validator :

- `private_raw_data_copied=false`;
- `live_read_only_enabled=false`;
- projection SHA-256 recalculée et identique;
- fichier commité identique à la sortie déterministe de l'Adapter.

## Artifact

- name: `genesis-public-snapshot-0001`
- artifact id: `9880552954`
- artifact zip sha256: `4c8c1b12818af377ee5a025358ba17328a2e6cbe71179436e226800eb053bdb9`

## Gates

- `contract-v2 = PASSED`;
- `adapter = PASSED`;
- `snapshot = PASSED`;
- `live-read-only = PENDING`;
- `current_gate = LIVE_READ_ONLY_PENDING`.

## Limites préservées

- aucune donnée privée brute dans le snapshot;
- aucun identifiant privé de source dans le snapshot;
- aucun ROOT digest privé;
- aucune écriture navigateur vers Genesis;
- aucun `LIVE_READ_ONLY`;
- aucun fichier `/generator/` modifié;
- aucun déploiement VPS effectué.

Le bundle VPS actuel reste volontairement le bundle DEMO et **n'embarque pas encore** ce snapshot. Sa publication sur le VPS exige donc une phase distincte et explicite.

## Prochaine phase

`DEPLOY_PUBLIC_SNAPSHOT_0001` ou, si Topbrutus préfère d'abord préparer l'interface, `PREPARE_SNAPSHOT_VIEW`.
