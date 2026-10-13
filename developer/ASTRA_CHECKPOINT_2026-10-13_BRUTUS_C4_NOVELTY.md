# ASTRA CHECKPOINT — BRUTUS C4 NOUVEAUTÉ

Date: 2026-10-13
Branche: `astra/brutus-c4-novelty-20261013`
Base: `a4eb00828ee63949119cea7925fa82bd3cac3e47`

## But

Ajouter le quatrième instrument du parcours officiel Brutus 37 :

`C1 Entrée/Z-STAMP -> C2 Empreinte -> C3 Bibliothèque -> C4 Nouveauté`

C4 ne déclare aucune découverte scientifique. Il classe uniquement le résultat exact de C3 :

- hit C3 -> `KNOWN`
- miss C3 -> `NOVEL_CANDIDATE`

`NOVEL_CANDIDATE` signifie seulement que l'empreinte C2 exacte n'était pas encore présente dans la bibliothèque C3 au moment de l'observation.

## Garde-fous

- `authority = SHADOW_ONLY`
- `scientific_discovery_claim = false`
- `proof_promotion = false`
- `compute_skips = 0`
- `query_before_compute = false`
- `scheduling_influence = false`
- `value_mutated = false`
- C4 exige C3 actif; C3 exige C2; C2 n'observe que les paquets Z estampillés.
- Le canary C4 hérite donc du canary Z actuel à 10 %.

## Mémoire

C4 ne duplique pas les 37 dictionnaires C3. Il conserve des compteurs et au maximum 37 empreintes candidates récentes.

Les misses C3 rejetés par la limite de capacité restent explicitement comptés dans `untracked_capacity`; ils ne sont jamais transformés silencieusement en `KNOWN`.

## Hashes exacts attendus après patch

- `orchestrator.py`: `0c29aae538c5ea69a3f3a235d7fd377bddd83b339a7f6cda5b091bbd9ae2642f`
- `dashboard.py`: `a55b055ee31816fda113f71d28499b1c4a697a8b123ee01dc852d86984dbc7fe`
- `c3_library.py` inchangé: `b7970583e688488d0f9fd8a90838d9163d00b08b7e6afedd499434e79a06c434`
- `c4_novelty.py`: `d9669cdcdbd300529ff63a07fc088be6a9e60fdc65315015b1904f83d42e10f2`

## Tests locaux contre la copie exacte POST-C3

Résultat :

- `C4_CHAIN=PASS 4 1 3`
- `C4_ROLLOVER=PASS 2 1 1`
- `C4_NOVELTY=PASS`
- YAML workflow parse: PASS
- patch idempotent: PASS

## Invariants de chaîne

Quand C4 est actif :

`C2 total_fingerprints == C3 observations == C4 observations`

`C4 known == C3 hits`

`C4 novel_candidates == C3 misses`

`C4 known + C4 novel_candidates == C4 observations`

Ces égalités mesurent la cohérence de la chaîne; elles ne prouvent pas la nouveauté scientifique des résultats.

## Déploiement

Workflow: `.github/workflows/deploy-brotoculateur-c4-vps.yml`

Modes : `audit`, `canary_start`, `disable`.

Le workflow :

- vérifie les hashes C1/C2/C3 exacts;
- refuse C4 si C3 n'est pas actif et cohérent;
- sauvegarde et pause par API avant mutation;
- teste une copie exacte avant installation;
- dispose d'un rollback automatique;
- redémarre et vérifie les invariants C2/C3/C4;
- ne modifie ni la promotion de preuve ni le calcul numérique.
