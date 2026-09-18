# Embryon X72 — Horloge de la Vie — Core V0.2

Cette section publique d’Antmux héberge le **port Web fidèle** de l’application Python
`ANTMUX_X72_LIFE_V02.py`.

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

Le port Web reprend les paramètres et la logique visibles dans la V0.2 :

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

Le navigateur exécute un **port JavaScript** des règles du Core V0.2 afin de rendre l’interface
accessible directement sur Antmux.

Le fichier Python original reste la source de référence publiée pour audit.

Le port Web ne prétend pas être le processus Python Tkinter lui-même.

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
