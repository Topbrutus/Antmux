# ROB — INTENT — EVALUATE_LIVE_READ_ONLY

Date: 2026-09-03
Authority: Topbrutus
Executor: Rob

## Base

- repository: `Topbrutus/Antmux`
- base branch: `main`
- base HEAD: `b228a227255e97d23fb7e54524766fa404ec705e`
- work branch: `genesis/evaluate-live-read-only`

## Mission

Évaluer la frontière `LIVE_READ_ONLY` sans l'activer.

## Preuves lues avant écriture

- le Vision Center public est actuellement `SNAPSHOT / PUBLIC_SNAPSHOT`;
- le contrat v2 prévoit conceptuellement `LIVE_READ_ONLY`;
- l'Adapter de production refuse encore explicitement `LIVE_READ_ONLY`;
- la source Genesis privée a été inspectée via un accès GitHub autorisé uniquement pour confirmer qu'une source privée réelle existe;
- aucun contenu privé brut, aucune seed, aucun résultat brut, aucun chemin privé, aucun token, aucun SHA privé et aucun ROOT privé ne seront copiés dans Antmux.

## Invariants

1. `LIVE_READ_ONLY` reste `PENDING` pendant toute cette mission.
2. Aucune capacité d'écriture vers Genesis.
3. Le navigateur public ne lit jamais directement le dépôt privé, le filesystem privé ou un endpoint privé.
4. Toute future lecture réelle doit passer par un bridge serveur à privilège minimal puis par une whitelist publique stricte.
5. Source périmée, validation échouée ou bridge indisponible => refus fermé et retour possible au snapshot figé.
6. Aucun secret dans le dépôt, les logs, les artifacts ou le navigateur.
7. Aucun `/generator/` modifié.
8. Aucun déploiement VPS dans cette mission d'évaluation.
9. Une réussite de la batterie signifie seulement `READY_FOR_CONTROLLED_IMPLEMENTATION_NOT_ACTIVATED`, jamais `LIVE_READ_ONLY=PASSED`.

## Fichiers prévus

- `laboratoire/genesis/live/LIVE-READ-ONLY-POLICY-v1.md`
- `laboratoire/genesis/live/fixtures/live-public-candidate.json`
- `laboratoire/genesis/live/evaluate-live-read-only.mjs`
- `laboratoire/genesis/live/test-live-read-only.mjs`
- `.github/workflows/genesis-demo-validation.yml`

## Sortie attendue

Un verdict mécanique sur l'éligibilité architecturale à une future implémentation contrôlée. L'activation réelle nécessitera une phase explicite séparée.
