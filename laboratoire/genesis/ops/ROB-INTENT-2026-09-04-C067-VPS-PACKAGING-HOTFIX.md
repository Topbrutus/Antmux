# ROB INTENT — C067 VPS packaging hotfix

Date: 2026-09-04
Authority: Topbrutus
Base main: `cfc499b9ed4c646db994817692809b44bf3c6eec`
Branch: `genesis/c067-vps-packaging-hotfix-20260904`

## Cause prouvée

Le déploiement C067 a validé le code, le préflight privé et les checksums, puis a échoué uniquement après installation parce que `bridge-public-progressive.mjs` importe `./build-public-source-progressive-c067.mjs`, tandis que le package VPS n'installait le builder que sous le nom `build-public-source-progressive.mjs`.

Erreur observée : `ERR_MODULE_NOT_FOUND` pour `build-public-source-progressive-c067.mjs`.

## Correction minimale

Conserver le nom runtime standard utilisé par le script de sync **et** installer une seconde copie byte-identical sous le nom attendu par l'import ESM du bridge C067.

Aucun code scientifique, aucune donnée Genesis, aucun cockpit, aucun generator, aucune permission et aucune capacité d'écriture ne sont modifiés.

## Validation attendue

- checksums dupliqués valides ;
- runtime C067 démarre sur le VPS ;
- source publique reste C065 pendant cette préparation ;
- cron 2 minutes et write capability NONE conservés.
