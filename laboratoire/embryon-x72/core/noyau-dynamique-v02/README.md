# Noyau dynamique X72 — v0.2 headless

## But

Séparer le calcul du noyau de son affichage afin que le serveur X72 et les visualisations puissent consommer le même état canonique.

```text
NoyauEngine
  -> NoyauState + H256
  -> NoyauServerAdapter
  -> futur branchement QueenCore / EventBus / Telemetry / WebSocket
```

La v0.1 visualisable reste intacte dans le dossier voisin `noyau-dynamique-v01`.

## Invariant central

```text
UP   = SOURCE -> C1 -> C2 -> C3 -> SORTIE
DOWN = SORTIE -> C3 -> C2 -> C1 -> SOURCE
```

Les trois portes centrales C1, C2 et C3 sont donc obligatoires dans les deux directions.

## Bassin 1

Etat exporté :
- inflow
- outflow
- crystal_index
- injection_pending
- interception_pending
- stable_cycles
- crystallized

Commandes du moteur :
- `inject(strength)`
- `intercept(strength)`
- `switch_world(index)`
- `set_speed(value)`
- `set_coherence(value)`
- `set_feedback(value)`

## Autorité

`noyau_engine.py` ne dépend ni de Matplotlib ni de NumPy. Il est conçu comme moteur headless déterministe.

Chaque `NoyauState` est sérialisable et reçoit un SHA-256 canonique `whole_h256`.

## Tests locaux vérifiés

```text
python -m unittest -v test_noyau_engine.py
9 tests / 9 PASS
```

Couverture : routes centrales, H256, rotations opposées, injection, interception, mondes, déterminisme, snapshots non aliasés et contrat serveur.

## Garde-fou

Cette étape ne modifie pas encore `deploy/x72-shared-queen/app/server.py`. Le runtime public actuel reste autoritaire. Le prochain chantier est le montage derrière `QueenCore` avec checkpoint et tests serveur avant toute activation.
