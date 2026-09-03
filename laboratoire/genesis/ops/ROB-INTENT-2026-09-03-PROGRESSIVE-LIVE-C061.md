# ROB — INTENTION — GENESIS PROGRESSIVE LIVE / C061

Date: 2026-09-03
Authority: Topbrutus
Executor: Rob
Repository: Topbrutus/Antmux
Base main: 11818638261c9f033eeab278d1eaf861d1105538
Branch: genesis/progressive-live-c061-20260903

## Mission

Permettre au Genesis Vision Center public de suivre l'évolution scientifique au-delà de C060 sans exposer le dépôt privé et sans recoder le site pour chaque nouvelle phase.

## Stratégie

Ajouter un runtime progressif v2 qui:
- conserve le même endpoint public `/laboratoire/genesis/live/public-read-only.json`;
- accepte le schéma public C060 historique et le nouveau schéma C061 explicitement whiteliste;
- projette `validated-through`, le gate d'exécution et la prochaine action comme métriques publiques;
- garde `LIVE_READ_ONLY`, `PUBLIC_READ_ONLY`, `VERIFIED_PUBLIC`, écriture `NONE`;
- rejette tout champ ou état scientifique non explicitement autorisé;
- réutilise le fetch privé éphémère et la clé deploy read-only côté VPS;
- remplace le cron actif seulement après validation et sauvegarde;
- laisse le snapshot fallback intact.

## Frontières

- aucun accès privé depuis le navigateur;
- aucune branche/URI/SHA privée dans le JSON public;
- aucun changement GESIS;
- aucun changement generator;
- aucune exécution scientifique par Antmux;
- C061 public doit signifier `BLOCKED_SYNTHETIC_SELECTION`, pas expérience réelle exécutée.
