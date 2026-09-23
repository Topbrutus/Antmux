# X72 — Noyau dynamique v0.2 — rapport d'intégration

Date : 2026-09-23  
Dépôt : `Topbrutus/Antmux`  
Branche : `astra/x72-noyau-dynamique-v01-20260923`  
Base `main` vérifiée : `f3edf4c3d722d511dfb4b422e6633bbc0022e30d`  
HEAD code vérifié avant ce rapport : `16eea1ba776443c4de0ec4275b6446560f0758d0`

## Résultat

Le noyau dynamique a été séparé de la visualisation puis monté dans le runtime Shared Queen en mode **lecture seule côté API**.

Chaîne actuelle :

```text
NoyauEngine
  -> NoyauState + H256
  -> NoyauServerAdapter
  -> QueenCore
  -> VisualState
  -> WebSocket / clients
```

## Invariants vérifiés

- trois portes centrales obligatoires : `C1 -> C2 -> C3` à la montée et au retour ;
- rotation gauche/droite opposée ;
- entrée, sortie, injection et interception du bassin 1 représentées dans l'état ;
- état du noyau sérialisable et scellé par SHA-256 ;
- checkpoint du noyau scellé par SHA-256 ;
- lecture de `visual_state()` sans avancement du noyau ;
- exactement un tick noyau par tick Queen ;
- cadence noyau montée sur `QueenCore.dt_sim = 1/240` ;
- restauration checkpoint exacte ;
- checkpoint serveur historique sans noyau accepté avec naissance d'un noyau compatible ;
- noyau volontairement absent de `QueenCore.whole_projection()` pour préserver le hash autoritaire historique ;
- aucune route publique d'injection, d'interception ou de changement de monde ajoutée à cette étape.

## Preuves locales sur clone frais de la branche

### Compilation

```text
python -m py_compile server.py engine.py adapter.py test_noyau_runtime_mount.py
PASS
```

### Tests noyau v0.2

```text
13 / 13 PASS
```

### Test du montage Shared Queen

```text
8 / 8 PASS
```

### Régression X72

Tous les scripts `deploy/x72-shared-queen/tests/test_*.py` ont été exécutés séquentiellement sur le clone frais.

```text
23 / 23 scripts PASS
```

Cela inclut les tests K7, observation, relations, stereo27, ternary echo, trend analyzer, Z3, provenance, checkpoints et le nouveau montage noyau.

## Vérification GitHub

- branche : 5 commits devant `main`, 0 derrière avant ajout de ce rapport ;
- PR #83 : ouverte, draft, mergeable ;
- sources noyau du runtime = sources locales vérifiées de `D:\noyau` ;
- aucun artefact de transport `[executed on device: ...]` présent dans les sources GitHub ;
- `main` n'a pas été modifié.

## Statut

**PRÊT POUR REVUE, PAS POUR DÉPLOIEMENT AUTOMATIQUE.**

La prochaine action irréversible est le merge vers `main`; elle reste volontairement non exécutée.
