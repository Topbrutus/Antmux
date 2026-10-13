# ASTRA CHECKPOINT — Brutus Co1 Archive

Date : 2026-10-13

Statut final : `LIVE_VALIDATED_PERSISTENCE_BOUNDARY`

Position officielle :

`S5 Index rapide → Co1 Archive → Co2 Chaîne de preuve → Co3 Checkpoint → Co4 Reprise`

## Contrat source

Le prototype `laboratoire/brutus-colonne-37/brutus37.py` place `CO1_ARCHIVE` immédiatement après `S5_FAST_INDEX` et avant `CO2_PROOF_CHAIN`.

La mesure prototype de Co1 est :

`{"archive": false}`

La vitrine `laboratoire/brutus-colonne-37/index.html` décrit Co1 ainsi :

`Sort l’ancien du circuit chaud sans le perdre.`

Aucune règle source autoritative ne définit actuellement :

- un âge minimal d’archivage ;
- un seuil HOT→WARM/COLD ;
- une politique d’éviction physique ;
- une règle scientifique de promotion par archivage.

Co1 v1 implémente donc uniquement la frontière non destructive de persistance : archiver sans réécrire le passé et sans inventer une politique d’éviction.

## Définition Co1 v1

Chaque entrée S5 techniquement valide peut produire un enregistrement JSONL durable identifié par :

`archive_id = A1- + SHA256(canonical({c2_fingerprint, formula_id, z_id}))`

Le fichier live est :

`~/brotoculateur/data/co1/archive-v1.jsonl`

Chaque nouvel enregistrement conserve notamment :

- l’empreinte C2 complète ;
- le bucket37 obtenu par la fonction C3 existante ;
- le `formula_id` exact ;
- le `z_id` existant ;
- les champs structurels canoniques C2 : valeur, profondeur, chaîne de formules, état, Z-ID, Z parent, Z origine ;
- le Z source observé lors du premier archivage.

Co1 ne remplace pas S2 pour la provenance complète et ne remplace pas Co2 pour la chaîne de preuve.

## Propriétés de sûreté

- `authority = PERSISTENCE_ONLY`
- `persistent = true`
- `append_only = true`
- `fsync_on_new_record = true`
- `deduplicates_by_archive_id = true`
- `thread_safe_deduplication = true`
- `rewrites_existing_records = false`
- `preexisting_duplicate_lines_preserved = true`
- `archive_copy_only = true`
- `age_policy_defined = false`
- `hot_removal_enabled = false`
- `hot_evictions = 0`
- `hash_chain_enabled = false`
- `co2_owns_hash_chain = true`
- `co2_proof_chain_input = true`
- `s5_fast_index_mutated = false`
- `scientific_proof_claim = false`
- `validation_state_mutated = false`
- `controls_routing = false`
- `controls_scheduling = false`
- `controls_calculation = false`
- `reserves_resources = false`
- `executes_replay = false`
- `schedules_replay = false`
- `compute_skips = 0`
- `value_mutated = false`
- `proof_promotion = false`

L’archive Co1 est une trace technique persistante. Elle ne constitue pas, à elle seule, une preuve scientifique.

# 1. Hygiène dépôt avant Co1

Avant la vraie branche Co1, un fichier placeholder a été créé accidentellement directement sur `main`, puis supprimé immédiatement :

- ajout accidentel : `bfa46aa139856f2a98da9805b4297b1de2b42c41`
- retrait : `88df2137ea897296b2cb4c8109949e41304d4a75`

Après retrait, le tree Git est revenu exactement au tree S5 :

`c34f11eeb2ae99614152445e5f0f5c58e764ff0f`

Aucun fichier moteur existant et aucun état VPS n’a été modifié par cet incident.

# 2. Première implémentation — PR #319

Branche :

`astra/brutus-co1-archive-20261013`

La branche ajoutait uniquement Co1, ses tests et ses workflows.

QA PR :

- run `38402574189`
- job `115313685175`
- `CO1_PR_PYCOMPILE=PASS`
- `CO1_PR_STATIC_GUARDS=PASS`

PR #319 mergée :

`01c9fb3680e02a1d9ecd5cfb7289e58ecae84a81`

SHA initial Co1 :

`b9f40b13e1a861625b667b8639541442cedd174767852e023c1cdc5769d00c03`

# 3. PRE_CO1 initial

Workflow : `38405846244`

Résultat : `PASS`

État observé :

- source : `PRE_CO1`
- dashboard : `82b57cca014d6eee3d9e039e6f483317f248caddef8d21b37cbf226ce27903af`
- Co1 absent
- moteur : `RUNNING`
- processed : `189 597`
- cristaux : `1 920 732`
- S5 observations : `1 086 332`
- S5 indexées : `245 419`
- S5 blocages amont : `840 913`
- S5 capacity_rejections : `0`
- S5 entrées uniques : `34 926`
- S5 Z uniques : `1 407`
- disque root : `61%`

# 4. Premier canary Co1 — run refusé

Workflow : `38405984333`

Résultat global : `FAIL`

Le run ne doit pas être décrit comme un PASS, même si les tests internes et le premier battement live avaient réussi.

## Tests internes réussis

- append-only + reprise : PASS
- payload structurel : PASS
- même Z / structures différentes conservées : PASS
- portes d’entrée : PASS
- corruption → fail closed : PASS
- autorité persistence-only : PASS
- lockstep callback sur 17 observations à travers 16 modules : PASS
- exact-copy stage : PASS

Backup :

`~/brotoculateur/backups/co1-20261013T133418Z`

## Premier battement live

- moteur : `RUNNING`
- S5 observations/indexées : `43 / 43`
- Co1 observations/éligibles : `43 / 43`
- appended : `26`
- already_present : `17`
- unique archive records : `26`
- Z uniques : `18`
- buckets : `20`
- archive bytes : `18 236`
- `CO1_LIVE_VERIFY=PASS`

## Échec de clôture

La garde finale comparait un compteur issu d’un snapshot live avec un fichier JSONL qui continuait d’être alimenté pendant que le moteur tournait.

Cette comparaison a échoué ; le workflow a correctement refusé de produire un PASS global et a déclenché le rollback.

Le rollback a restauré code et configuration mais a volontairement conservé l’archive append-only.

# 5. Audit après premier rollback

Workflow : `38406118889`

Résultat : `PASS`

- source : `PRE_CO1`
- ancien dashboard restauré
- module Co1 absent
- archive conservée : `43` lignes
- archive SHA : `987c323d0e66abf72bf726a9f6e906575115d53462d8beb023bb0ef7092116d8`
- disque : `61%`

À ce stade, une première interprétation a attribué l’écart observé à des écritures dupliquées concurrentes. Cette interprétation n’était pas encore démontrée et sera corrigée plus bas à partir d’une preuve de rechargement.

# 6. Durcissement concurrence — PR #320

Le module a été durci pour sérialiser la séquence :

`check archive_id → append → enregistrement mémoire`

avec un `threading.RLock`.

Le statut est également capturé sous le même verrou.

Nouveaux compteurs/gardes :

- `physical_records_seen`
- `thread_safe_deduplication = true`
- `preexisting_duplicate_lines_preserved = true`

Un test de concurrence a été ajouté :

- 128 callbacks parallèles sur la même entrée ;
- exactement `1` append ;
- exactement `127` already-present ;
- fichier physique : `1` ligne.

Un test séparé prouve aussi que des lignes dupliquées déjà présentes dans un fichier historique seraient conservées et comptées, jamais supprimées silencieusement.

QA PR :

- run `38407509431`
- job `115330882557`
- syntaxe : PASS
- gardes statiques : PASS

PR #320 merge :

`f3a4d93c9d69f8994761d1dea1a483215532d14b`

SHA Co1 durci et final :

`032ba9e665349b7d426e32c19d3c532467a0245e35a27da2cd66e2d1209864d2`

Le verrou est conservé comme durcissement valable. Il ne doit toutefois pas être présenté comme la correction d’un doublon live prouvé, car la preuve suivante a corrigé ce diagnostic.

# 7. PRE V2

Workflow : `38407621903`

Résultat : `PASS`

- source : `PRE_CO1`
- module absent
- archive toujours exactement `43` lignes
- archive SHA toujours `987c323d0e66abf72bf726a9f6e906575115d53462d8beb023bb0ef7092116d8`
- SHA Co1 attendu : `032ba9e665349b7d426e32c19d3c532467a0245e35a27da2cd66e2d1209864d2`

# 8. Deuxième canary V2 — diagnostic corrigé

Workflow : `38407697861`

Résultat global : `FAIL`

Le stage exact-copy et tous les tests Co1 ont réussi :

- `CO1_ARCHIVE=PASS`
- `CO1_PARALLEL_DEDUP=PASS 1 127`
- `CO1_LEGACY_DUPLICATES_PRESERVED=PASS 3 2`
- `CO1_CONCURRENCY=PASS`
- `CO1V2_EXACT_LIVE_STAGE=PASS`

Backup :

`~/brotoculateur/backups/co1v2-20261013T134638Z`

## Preuve qui corrige l’interprétation précédente

Lors du rechargement de l’archive héritée :

- `loaded_records = 43`
- `loaded_duplicate_ids = 0`

Les 43 lignes héritées étaient donc 43 identités d’archive valides et uniques.

La conclusion précédente « 17 lignes dupliquées » n’était pas supportée par les données et est explicitement retirée.

Le test parallèle reste utile comme durcissement, mais il ne prouve pas qu’un défaut de duplication s’était produit en live.

## Battement live V2

- S5 : `59 / 59`
- Co1 : `59 / 59`
- appended : `31`
- already_present : `28`
- loaded_records : `43`
- loaded_duplicate_ids : `0`
- physical_records_seen : `74`
- unique_records : `74`
- Z uniques : `30`
- buckets : `31`
- `CO1V2_LIVE_VERIFY=PASS`

Le run a ensuite échoué de nouveau sur la comparaison finale entre un snapshot pris pendant `RUNNING` et un fichier qui continuait à croître.

Le rollback a de nouveau préservé toutes les lignes de l’archive.

# 9. Audit après deuxième rollback

Workflow : `38407858617`

Résultat : `PASS`

- source : `PRE_CO1`
- code Co1 retiré du live après rollback
- moteur : `RUNNING`
- cristaux : `1 921 769`
- S5 observations/indexées : `35 800 / 35 800`
- archive : `95` lignes
- archive SHA : `d7d9b89f059e044afc46493dd3c290c87dbdc094b7ec93be2e909e81262d716e`

Les lignes passées de 43 à 95 représentent les écritures append-only effectuées avant rollback. Elles n’ont pas été supprimées.

# 10. Correction de la preuve — PR #321

La vraie faiblesse de clôture était un problème TOCTOU :

1. snapshot du statut pendant `RUNNING` ;
2. le moteur continue ;
3. l’archive reçoit de nouvelles lignes ;
4. comparaison du snapshot ancien avec le fichier plus récent.

La preuve a été remplacée par une frontière quiescente :

1. save ;
2. pause ;
3. attendre `PAUSED` ;
4. compter l’archive ;
5. attendre une seconde ;
6. recompter ;
7. exiger un nombre de lignes stable ;
8. capturer le statut Co1 au même état quiescent ;
9. exiger `physical_records_seen == lignes physiques` ;
10. vérifier les SHA ;
11. redémarrer ;
12. attendre et prouver `RUNNING`.

PR #321 merge :

`5ba94b2f24f142defd03203fb909d7b3b263d4e6`

# 11. Canary final quiescent

Workflow : `38408403027`

Résultat global : `PASS`

## PRE de ce run

- source : `PRE_CO1`
- archive initiale : `95` lignes
- archive SHA initial : `d7d9b89f059e044afc46493dd3c290c87dbdc094b7ec93be2e909e81262d716e`
- dashboard PRE : `82b57cca014d6eee3d9e039e6f483317f248caddef8d21b37cbf226ce27903af`
- Co1 attendu : `032ba9e665349b7d426e32c19d3c532467a0245e35a27da2cd66e2d1209864d2`
- moteur : `RUNNING`
- cristaux : `1 924 102`
- S5 observations/indexées : `147 789 / 147 789`

## Stage exact-copy

- patch : PASS
- dashboard POST : `210abbe5d72fd4dcc4b154cb3d13a8d954567ac29ef5435381fe2f16fbce109b`
- Co1 SHA : `032ba9e665349b7d426e32c19d3c532467a0245e35a27da2cd66e2d1209864d2`
- tests fonctionnels : PASS
- corruption fail-closed : PASS
- callback lockstep : PASS
- concurrence : `1 append / 127 already-present` : PASS
- test legacy duplicate preservation : PASS
- `CO1_CONCURRENCY=PASS`
- `CO1V2_EXACT_LIVE_STAGE=PASS`

Backup :

`~/brotoculateur/backups/co1v2-20261013T135139Z`

## Premier snapshot live

- moteur : `RUNNING`
- S5 observations/indexées : `121 / 121`
- Co1 observations/éligibles : `121 / 121`
- appended : `41`
- already_present : `80`
- loaded_records : `95`
- loaded_duplicate_ids : `0`
- physical_records_seen au snapshot : `136`
- unique_records au snapshot : `136`
- Z uniques : `30`
- buckets : `36`
- archive bytes : `98 657`
- `CO1V2_LIVE_VERIFY=PASS`

## Preuve quiescente décisive

Après `save + pause`, les callbacks déjà en vol ont terminé puis l’archive s’est stabilisée :

- premier comptage stable : `152`
- second comptage une seconde plus tard : `152`
- `physical_records_seen` au statut quiescent : `152`
- lignes physiques JSONL : `152`
- égalité : `152 = 152`
- `CO1V2_QUIESCENT_PHYSICAL_MATCH=PASS`

Archive SHA à cette frontière stable :

`bf540e324859c9873edf5374d015ef2ec610368680021b40fce4e23101a28639`

Le moteur a ensuite été redémarré :

`CO1V2_RESTART_AFTER_PROOF=PASS`

Puis :

`CO1V2_WORKFLOW=PASS`

# 12. POST_CO1 indépendant

Workflow : `38408521468`

Résultat : `PASS`

État observé :

- source : `POST_CO1`
- dashboard : `210abbe5d72fd4dcc4b154cb3d13a8d954567ac29ef5435381fe2f16fbce109b`
- module Co1 : `032ba9e665349b7d426e32c19d3c532467a0245e35a27da2cd66e2d1209864d2`
- moteur : `RUNNING`
- processed : `2 748`
- cristaux : `1 924 420`
- S5 observations : `14 981`
- S5 indexées : `14 981`
- S5 bloquées : `0`
- S5 entrées uniques : `3 956`
- S5 Z uniques : `226`
- Co1 observations : `14 981`
- Co1 éligibles : `14 981`
- Co1 appended : `3 861`
- Co1 already_present : `11 120`
- Co1 loaded_records : `95`
- Co1 loaded_duplicate_ids : `0`
- Co1 physical_records_seen au snapshot : `3 956`
- Co1 unique_records au snapshot : `3 956`
- Co1 Z uniques : `226`
- Co1 buckets : `37`
- archive bytes au snapshot : `2 921 814`
- load errors : `0`
- write errors : `0`
- `CO1V2_AUDIT_ONLY=PASS`
- disque root : `61%`

Comptabilité :

`3 861 + 11 120 = 14 981`

et :

`95 loaded + 3 861 appended = 3 956 physical_records_seen`

Le nombre de Z uniques Co1 (`226`) est égal au nombre de Z uniques S5 (`226`) dans cette fenêtre.

Le fichier physique a été observé quelques instants plus tard à `3 964` lignes avec SHA :

`db71ac1af1e0e65ffab1aef349b5403be069cd8ff8bd9a8a12aa97b93725f1aa`

Cet écart `3 956` snapshot → `3 964` fichier n’est pas une erreur : le moteur était `RUNNING`, donc huit nouvelles écritures valides ont eu lieu entre les deux lectures. La preuve d’égalité physique est celle du canary quiescent, où statut et fichier ont été comparés à la même frontière stable : `152 = 152`.

# 13. Interprétation

Co1 est maintenant une vraie frontière de persistance append-only.

Il sait :

- recevoir les résultats techniques S5 ;
- matérialiser durablement chaque nouvelle identité d’archive ;
- recharger un historique existant ;
- reconnaître une identité déjà archivée ;
- résister à un callback parallèle répété sans créer deux lignes pour la même identité dans le test contrôlé ;
- refuser une archive corrompue plutôt que la réécrire ;
- conserver les données lors des rollbacks ;
- être vérifié physiquement à une frontière quiescente.

Il ne sait volontairement pas encore :

- construire une chaîne de hash entre archives ;
- déclarer la continuité de preuve ;
- décider qu’un objet est « vieux » ;
- évincer un objet HOT ;
- transformer une archive en preuve scientifique.

Ces responsabilités ne doivent pas être inventées dans Co1.

La prochaine vertèbre, Co2, possède explicitement la responsabilité de chaîne de preuve.

# Statut final

`LIVE_VALIDATED_PERSISTENCE_BOUNDARY`

Co1 — Archive est actif et validé opérationnellement comme frontière durable append-only entre S5 et Co2.

Prochaine vertèbre officielle :

`Co2 — Chaîne de preuve`
