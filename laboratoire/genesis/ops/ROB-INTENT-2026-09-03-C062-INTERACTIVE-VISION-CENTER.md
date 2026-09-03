# ROB — INTENT — Genesis Vision Center / C062

Date: 2026-09-03
Authority: Topbrutus
Executor: Rob
Repository: Topbrutus/Antmux
Branch: genesis/c062-interactive-vision-center-20260903
Base main: 9f7b93076b3bbf3fb3bfd1bbe34632d900cb6175

## Mission

Préparer le Vision Center public pour l'état C062 et le rendre plus interactif tout en conservant la frontière stricte lecture seule.

## Évolution LIVE

Le runtime progressif doit accepter exactement:

- C060 historique;
- C061 validé avec sélection synthétique bloquée;
- C062 validé avec `REAL-EXPERIMENT-SPEC-001` gelée mais non sélectionnée et non exécutée.

Toute autre combinaison doit échouer fail-closed.

## Interaction publique autorisée

Le navigateur peut:

- afficher une timeline C060/C061/C062;
- ouvrir les détails publics d'une étape;
- afficher la fiche publique de l'expérience candidate;
- actualiser manuellement la projection LIVE;
- activer/désactiver un rafraîchissement local 30 secondes;
- mémoriser localement la dernière étape vue pour afficher « ce qui a changé »;
- copier un résumé public.

Le navigateur ne peut jamais:

- écrire dans Seed Genesis;
- lancer une expérience;
- appeler un dépôt privé;
- recevoir des credentials privés;
- modifier le publisher ou le VPS;
- promouvoir une hypothèse ou une preuve.

## Frontières

- `LIVE_READ_ONLY / PUBLIC_READ_ONLY / VERIFIED_PUBLIC` obligatoire;
- snapshot fallback conservé;
- aucune donnée brute Seed Genesis;
- aucun SHA, nom de branche ou chemin privé dans le JSON public;
- aucune modification du générateur Antmux;
- aucun GESIS;
- aucune exécution scientifique.

## Fichiers prévus

- `laboratoire/genesis/live-v2/build-public-source-progressive.mjs`
- `laboratoire/genesis/live-v2/bridge-public-progressive.mjs`
- `laboratoire/genesis/live-v2/test-progressive-live.mjs`
- `laboratoire/genesis/index.html`
- tests cockpit si nécessaire;
- workflows de validation/déploiement adaptés au statut C062.

## Règle d'arrêt

Pas de fusion si validation progressive, Vision Center complet, Chromium ou déploiement bundle échoue.
