# ROB INTENT — PUBLIC SNAPSHOT 0001 — 2026-09-03

## Base

- repository: `Topbrutus/Antmux`
- base branch: `main`
- base HEAD: `61ad089166ec0ef6ee915e259348a9b732298200`
- work branch: `genesis/snapshot-validation-0001`

## Mission

Créer et valider le premier snapshot public figé réellement dérivé d'un état Seed Genesis vérifié, sans publier les données privées brutes ni les identifiants privés de la source.

## Source autorisée

Lecture minimale d'une preuve de clôture GENESIS-003/C060 et de son audit GitHub Actions dans le dépôt privé Seed Genesis. Les identifiants privés de source ne sont pas recopiés dans l'enveloppe publique.

## Faits publics candidats

- `GENESIS-003 C041-C060 = COMPLETE_VALIDATED`;
- état du test sélectionné = `PLANNED_NOT_EXECUTED`;
- aucune hypothèse gagnante sélectionnée;
- aucune probabilité produite;
- aucune promotion automatique Evidence Ledger;
- audit de clôture de la source = `SUCCESS`.

Ces faits sont une attestation d'état logiciel, pas une mesure physique ni une preuve d'autonomie.

## Corrections nécessaires avant publication

Le validateur actuel autorise `SNAPSHOT`, mais impose encore des invariants DEMO. La mission doit d'abord séparer strictement les invariants `DEMO` et `SNAPSHOT`, et imposer les paires exactes :

- `DEMO + SYNTHETIC`;
- `SNAPSHOT + PUBLIC_SNAPSHOT`;
- `LIVE_READ_ONLY` interdit.

## Limites

- `DENY BY DEFAULT -> EXPLICIT WHITELIST -> PUBLIC`;
- aucun contenu privé brut dans Antmux;
- aucun chemin, token, credential, endpoint privé ou secret;
- aucun digest ROOT privé;
- aucun `LIVE_READ_ONLY`;
- aucune écriture navigateur vers Genesis;
- aucun `/generator/`;
- aucun déploiement VPS dans cette phase.

## Critère de fermeture

`PUBLIC_SNAPSHOT_0001 = COMPLETE_VALIDATED_ON_BRANCH` uniquement si le snapshot passe le contrat v2 corrigé, les tests adversariaux SNAPSHOT et la CI complète, sans régression DEMO.
