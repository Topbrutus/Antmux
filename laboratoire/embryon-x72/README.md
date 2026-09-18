# Embryon X72 — Horloge de la Vie

Cette section publique d’Antmux expose une visualisation expérimentale du cerveau de la Reine MYRMIX.

## Principe

```text
CORE
→ TELEMETRY
→ VisualState
→ VISUAL
```

La page démarre en **DEMO TELEMETRY — NOT CORE**. Elle calcule une simulation locale déterministe, permet d’injecter une panne sur S3 et d’observer une réparation.

Elle tente aussi de lire périodiquement :

```text
./live/public-read-only.json
```

Si un processus Python publie un état valide à cet emplacement, l’interface passe en **LIVE READ-ONLY TELEMETRY** et désactive les contrôles qui pourraient prétendre modifier le Core.

## Contrat minimal du flux live

Exemple :

```json
{
  "mode": "LIVE_READ_ONLY",
  "visual_state": {
    "mode": "STABLE",
    "dt_sim": 0.016667,
    "r_exec": 1.0,
    "f_rt": 60,
    "tick": 123,
    "generation": 0,
    "event_count": 42,
    "activity": 0.35,
    "memory": 0.46,
    "crystallization": 0.28,
    "repair": 0.0,
    "error": 0.0,
    "synapses": [
      {"id":"S1","active":true,"activity":0.31,"memory":0.40,"crystallization":0.21,"repair":0.0},
      {"id":"S2","active":true,"activity":0.33,"memory":0.42,"crystallization":0.22,"repair":0.0},
      {"id":"S3","active":true,"activity":0.34,"memory":0.43,"crystallization":0.23,"repair":0.0},
      {"id":"S4","active":true,"activity":0.36,"memory":0.45,"crystallization":0.24,"repair":0.0},
      {"id":"S5","active":true,"activity":0.37,"memory":0.47,"crystallization":0.25,"repair":0.0},
      {"id":"S6","active":true,"activity":0.39,"memory":0.49,"crystallization":0.26,"repair":0.0},
      {"id":"S7","active":true,"activity":0.40,"memory":0.50,"crystallization":0.27,"repair":0.0}
    ]
  }
}
```

## Frontière importante

- Une animation n’est pas une preuve.
- Le hash affiché en mode DEMO est le vrai SHA-256 du `VisualState` synthétique courant, pas le hash d’un Core réel.
- Base36 est une représentation du hash.
- Le frontend ne doit jamais inventer un état LIVE.
- Le futur Core Python doit rester indépendant de l’interface graphique.

## Étape suivante

Le branchement serveur prévu est :

```text
Queen Core Python
→ télémétrie publique read-only
→ /laboratoire/embryon-x72/live/public-read-only.json
→ Horloge de la Vie
```

Une évolution WebSocket pourra être ajoutée ensuite sans rendre le Core dépendant du navigateur.
