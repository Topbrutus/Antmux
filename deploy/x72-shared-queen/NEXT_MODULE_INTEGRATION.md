# X72 — Next Module Integration Contract

## Architecture verrouillée

`Queen Server -> API / WebSocket -> VisualState -> Horloge de la Vie`

Le prochain module est un **consommateur du VisualState serveur**. Il ne possède,
ne reconstruit et ne simule jamais une Queen locale.

## Autorité serveur

Les champs suivants restent exclusivement autoritaires côté serveur :

- `tick_count`
- `protected_h256`
- `reference_h256`
- `whole_h256`
- `synapses`
- `integrity_match`
- `generation`
- EventBus / `recent_events`

Le frontend peut interpoler uniquement des valeurs graphiques temporaires.
`_visualTick` n'est jamais renvoyé au serveur et n'est jamais un tick officiel.

## Transport

- état initial / diagnostic : `GET ./api/state`
- flux autoritaire : `WebSocket ./ws`
- source attendue : `QUEEN_SERVER_V0_2`

## Déconnexion et reconnexion

À la perte WebSocket :

1. afficher `CORE DISCONNECTED`;
2. conserver le dernier VisualState reçu;
3. ne lancer aucun tick, EventBus ou QueenCore local;
4. retenter la connexion sans reset destructif.

À la reconnexion, le premier VisualState serveur redevient immédiatement la
source de vérité; l'interpolation visuelle peut repartir depuis l'image gelée.

## État READY

Quand `integrity_match == true`, un verdict serveur historique `INVALID`
signifiant « aucune réparation à exécuter » ne doit pas être présenté comme
une panne rouge. L'interface affiche `READY / AUCUNE PANNE`; le verdict
serveur brut reste visible dans le panneau de preuve.

## Runtime

`R_exec` et `F_rt` mesurent uniquement le processus courant. Le tick
persistant reste historique après restart, mais `runtime_start_tick` est
réinitialisé au tick restauré.

## Barrière d'intégration

Avant intégration : syntaxe JS/Python, `git diff --check`, copies frontend
identiques, aucune QueenCore frontend, aucun faux tick local, test multi-client,
fault/repair local, hash protégé restauré, restart runtime et reconnexion.
