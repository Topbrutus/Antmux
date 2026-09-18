# Embryon X72 — Horloge de la Vie — Shared Queen V0.2

Cette section publique d’Antmux affiche l’état d’une **Reine X72 partagée et autoritaire côté serveur**.
Le navigateur est un client de visualisation : il reçoit `VisualState` par WebSocket et n’exécute aucun tick local.
La source Python historique `ANTMUX_X72_LIFE_V02.py` reste publiée comme référence de la logique V0.2.

## Source de référence

Le fichier Python original est publié ici :

```text
core/ANTMUX_X72_LIFE_V02.py
```

Le rapport de test fourni avec cette version est publié ici :

```text
core/ANTMUX_X72_CORE_V02_TEST_REPORT.json
```

## Architecture V0.2

```text
QueenCore
→ EventBus
→ RepairEngine
→ Telemetry
→ VisualState
→ Visual
```

Le serveur partagé reprend les paramètres et la logique visibles dans la V0.2 :

- graine 72 ;
- 7 synapses internes ;
- `dt_sim = 1 / 240` ;
- modes `SLEEP / EVENT / BURST / STABLE / FAULT / AUTO_REPAIR` ;
- relations du graphe V0.2 ;
- dynamique activité / mémoire / cristallisation ;
- panne protégée ;
- progression de réparation `+0.0075` par étape ;
- fermeture de l’intégrité structurelle sur la référence ;
- engrenages 36 / 28 / 20 dents ;
- cadrans cristallisation / mémoire / activité ;
- particules de relation ;
- état H256 et vue Base36_50.

## Important

Le runtime public actuel est **server-authoritative** : `deploy/x72-shared-queen/app/server.py`
maintient l’entité `QUEEN-X72-0072`, la persistance et les mutations contrôlées.

Le frontend `deploy/x72-shared-queen/frontend/app.js` ne calcule pas l’état cognitif : il affiche
le dernier `VisualState` reçu et gèle l’affichage si le WebSocket est déconnecté.

Le fichier Python original reste une référence publiée pour audit; il n’est pas présenté comme
le processus live servi au navigateur.

## Observabilité publique

Le serveur expose des interfaces en lecture pour distinguer l’état fonctionnel de l’état opérationnel :

- `GET /api/health` : disponibilité minimale et identité de la Reine ;
- `GET /api/state` : `VisualState` fonctionnel partagé ;
- `GET /api/telemetry` : télémétrie opérationnelle `ANTMUX-X72-OBSERVABILITY-v1` ;
- `GET /api/events` : fenêtre récente du bus d’événements ;
- `GET /api/report` : dernier rapport de réparation ;
- `WS /ws` : flux partagé du `VisualState` autoritaire.

La télémétrie d’observabilité décrit le fonctionnement du service; elle ne constitue pas une preuve
scientifique indépendante de la sémantique cognitive des métriques affichées.

## Rapport de test fourni

Le rapport V0.2 fourni documente notamment :

```text
seed: 72
synapse_fault: S4
repair_steps: 134
verdict: PASS
```

avec restauration exacte du hash protégé sur la référence autorisée.

## Règle

```text
ÉTAT
→ TÉLÉMÉTRIE
→ VISUALISATION
```

Le visuel ne doit pas inventer un état absent.
