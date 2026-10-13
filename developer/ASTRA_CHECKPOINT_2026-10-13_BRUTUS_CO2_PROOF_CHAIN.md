# ASTRA CHECKPOINT — Brutus Co2 Chaîne de preuve

Date : 2026-10-13

Statut actuel : `READY_FOR_LIVE_CANARY`

**Ce statut n’est PAS `LIVE_VALIDATED`.** Le module, son patch exact-live et son runner sont validés, mais aucun déploiement Co2 n’a encore été appliqué au VPS.

Position officielle :

`Co1 Archive → Co2 Chaîne de preuve → Co3 Checkpoint → Co4 Reprise`

Co2 est la vertèbre 31/33 de la Colonne 37.

## 1. Contrat source récupéré

Le prototype `laboratoire/brutus-colonne-37/brutus37.py` place `CO2_PROOF_CHAIN` immédiatement après `CO1_ARCHIVE` et avant `CO3_CHECKPOINT`.

Sa mesure prototype est une trace technique SHA-256 construite à partir du Z-ID et de l’empreinte C2.

La vitrine `laboratoire/brutus-colonne-37/index.html` décrit Co2 par :

`Conserve continuité et provenance.`

Le module Co1 live déclare explicitement :

- `hash_chain_enabled = false`
- `co2_owns_hash_chain = true`
- `co2_proof_chain_input = true`

Aucune source autoritative récupérée ne donne à Co2 le droit de convertir une chaîne cryptographique en vérité scientifique.

## 2. Frontière de sens retenue

Co2 v1 est un **ledger d’intégrité de trace**.

Il chaîne l’ordre physique réel des enregistrements append-only Co1 et non l’ordre d’arrivée concurrent des callbacks.

Pour chaque ligne physique Co1 :

- `sequence`
- `archive_line`
- `archive_id`
- `archive_record_sha256 = SHA256(canonical(full Co1 record))`
- `previous_chain_hash`
- `chain_hash = SHA256(canonical(link payload))`

Le hash genesis est 64 zéros.

Le fichier cible prévu est :

`~/brotoculateur/data/co2/proof-chain-v1.jsonl`

Le fichier source reste :

`~/brotoculateur/data/co1/archive-v1.jsonl`

## 3. Garde scientifique

Co2 revendique uniquement l’intégrité de la trace liée.

Il ne revendique pas :

- la vérité du contenu scientifique ;
- une validation indépendante ;
- une antériorité historique externe ;
- un horodatage tiers ;
- une signature numérique ;
- un ancrage de confiance externe.

Le backfill initial de l’archive Co1 existante est donc explicitement :

`backfill_is_retrospective_integrity_binding = true`

et :

`historical_attestation_claim = false`

Règle : **TRACE INTEGRITY ≠ TRUTH OF CLAIM**.

## 4. Propriétés Co2 v1

- `authority = TRACE_INTEGRITY_ONLY`
- `source_of_truth = CO1_ARCHIVE_PHYSICAL_ORDER`
- `hash_algorithm = SHA-256`
- `chain_definition = PHYSICAL_CO1_ARCHIVE_RECORD_ORDER`
- `detects_archive_record_change = true`
- `detects_proof_link_change = true`
- `detects_omission_in_bound_prefix = true`
- `detects_reordering_in_bound_prefix = true`
- `detects_insertion_in_bound_prefix = true`
- `append_only = true`
- `fsync_on_runtime_link = true`
- `atomic_initial_backfill = true`
- `rewrites_existing_links = false`
- `co1_archive_mutated = false`
- `external_trust_anchor = false`
- `digital_signature_enabled = false`
- `trace_integrity_claim = true`
- `scientific_proof_claim = false`
- `truth_of_claim_established = false`
- `validation_state_mutated = false`
- `proof_promotion = false`
- `controls_routing = false`
- `controls_scheduling = false`
- `controls_calculation = false`
- `reserves_resources = false`
- `executes_replay = false`
- `schedules_replay = false`
- `compute_skips = 0`
- `value_mutated = false`
- `co3_checkpoint_input = true`

## 5. Implémentation mergée

PR #323 : `feat: add Brutus Co2 proof-chain integrity ledger`

Merge :

`66a8033c704b40a601699c8b9ed3da14873a0f4c`

Fichiers ajoutés :

- `.github/workflows/qa-brotoculateur-co2-pr.yml`
- `deploy/vps-co2/co2_proof_chain.py`
- `deploy/vps-co2/patch_brotoculateur_co2_proof_chain.py`
- `deploy/vps-co2/run_co2_vps.sh`
- `deploy/vps-co2/test_co2_proof_chain.py`
- `deploy/vps-co2/verify_co2_chain_files.py`

Module Co2 SHA-256 :

`2e5fe79712cf1efd5f65391c3ec9106c2934973449f7053634696f27a7ec0580`

## 6. QA PR #323

Run : `38412120566`

Job : `115346861257`

Résultats :

- `CO2_PR_SYNTAX=PASS`
- `CO2_PR_STANDALONE_CHAIN=PASS`
- `CO2_PR_STATIC_GUARDS=PASS`

La QA autonome a prouvé :

1. backfill initial de 3 lignes ;
2. vérification fichier 3/3, aucun lien manquant ;
3. append runtime d’une quatrième ligne → `CHAIN_ADVANCED_1` ;
4. restart charge les 4 liens existants ;
5. modification d’un ancien enregistrement Co1 → Co2 indisponible/fail-closed ;
6. garde `TRACE_INTEGRITY_ONLY` présente.

## 7. PRE_CO2 live non-mutant

Workflow autorisé utilisé uniquement en audit :

`.github/workflows/deploy-brotoculateur-co1-v2-vps.yml`

Run : `38412864719`

Résultat : PASS.

État observé :

- source : `POST_CO1`
- dashboard : `210abbe5d72fd4dcc4b154cb3d13a8d954567ac29ef5435381fe2f16fbce109b`
- Co1 : `032ba9e665349b7d426e32c19d3c532467a0245e35a27da2cd66e2d1209864d2`
- état moteur : `RUNNING`
- processed : `119986`
- cristaux : `1938563`
- S5 observations : `693692`
- S5 indexed : `167869`
- S5 blocked : `525823`
- S5 unique entries : `30235`
- S5 unique Z : `1469`
- Co1 observations : `693692`
- Co1 eligible : `167869`
- Co1 appended : `30140`
- Co1 already present : `137729`
- Co1 loaded records : `95`
- Co1 loaded duplicate IDs : `0`
- Co1 physical records : `30235`
- Co1 unique records : `30235`
- Co1 unique Z : `1469`
- Co1 buckets : `37`
- Co1 load errors : `0`
- Co1 write errors : `0`
- archive lines observées : `30235`
- archive SHA-256 observé : `cca9d526d8bf1c1929c0b56832ddf2db86d696bb9a25734fd343f7dabd90e10c`
- disque racine : `61%`

Le PRE prouve que la frontière Co1 est saine avant Co2.

## 8. Capture read-only de la source live exacte

Workflow :

`.github/workflows/capture-brotoculateur-live-source.yml`

Run : `38412945924`

Artifact : `brotoculateur-live-source`

Artifact ID : `11822257744`

Digest artifact :

`sha256:517fd71f70832057f553589bc16775cfacbe3b7853094dd2beb11ef502f2ff91`

La capture a permis de tester le patch Co2 sur les octets/source réellement en production, sans mutation VPS.

## 9. Défaut de patch découvert avant déploiement

Le premier patcher Co2 attendait :

`co1_outcome = self.co1_archive.observe(...)`

La capture live exacte a montré que la ligne réelle était :

`self.co1_archive.observe(formula_id, source, out, s5_outcome)`

Le patcher a donc refusé avec :

`callback: expected 1 occurrence, found 0`

Ce refus est classé **PASS de garde / FAIL de compatibilité initiale** : aucun changement live n’a été appliqué.

## 10. Correction exact-live

PR #324 : `fix: bind Co2 to actual live Co1 callback`

Merge :

`79a309106e922b73129eb757af364dc6a76fc7a3`

La correction modifie uniquement l’ancre du patcher :

`self.co1_archive.observe(...)`

est transformé en :

`co1_outcome = self.co1_archive.observe(...)`

puis :

`self.co2_proof_chain.observe(..., co1_outcome)`

Aucune sémantique interne Co1 n’est changée.

QA PR #324 :

Run `38413578396` → PASS.

## 11. Test exact-capture après correction

Sur la source live capturée :

- `CO2_PATCH=PASS`
- dashboard POST calculé : `b393de960f8f0c6bfdb17b7049ab90142736491cadf86540f70a3ae6647b8e3e`
- Co1 SHA : `032ba9e665349b7d426e32c19d3c532467a0245e35a27da2cd66e2d1209864d2`
- S5 SHA : `de885d1f4748d236a0050cbea87560cf26fc74a08a95a8a02b119241ce6b0334`
- C3 SHA : `b7970583e688488d0f9fd8a90838d9163d00b08b7e6afedd499434e79a06c434`
- Co2 module SHA : `2e5fe79712cf1efd5f65391c3ec9106c2934973449f7053634696f27a7ec0580`
- `CO2_BOOTSTRAP_RESTART=PASS`
- `CO2_RUNTIME_ORDER=PASS`
- `CO2_PHYSICAL_DUPLICATE_PRESERVED=PASS`
- `CO2_ARCHIVE_TAMPER=PASS`
- `CO2_CHAIN_TAMPER_OMISSION=PASS`
- `CO2_TRACE_INTEGRITY_ONLY=PASS`
- `CO2_CALLBACK_LOCKSTEP=PASS`
- `CO2_PROOF_CHAIN=PASS`
- `CO2_EXACT_CAPTURE_TEST=PASS`

Le test lockstep a observé 17 événements sur chaque instrument de T8 jusqu’à Co2.

## 12. Runner VPS prêt

Runner versionné :

`deploy/vps-co2/run_co2_vps.sh`

Séquence prévue :

1. audit hashes PRE exacts ;
2. copie du package live ;
3. patch exact-copy ;
4. tests Co2 complets ;
5. save + pause ;
6. backup code + état + archive Co1 + chaîne Co2 existante ;
7. installation dashboard + module Co2 + activation ;
8. restart ;
9. canary live ;
10. save + pause ;
11. stabilisation quiescente ;
12. preuve `Co1 archive lines == Co2 chain lines == status.chain_links` ;
13. vérification indépendante `verify_co2_chain_files.py` ;
14. vérification hashes ;
15. restart et preuve `RUNNING`.

Rollback :

- restaure seulement code/config ;
- ne réécrit pas l’archive Co1 ;
- ne réécrit pas une chaîne Co2 déjà produite.

## 13. Blocage de transport actuel

La tentative de créer un nouveau fichier workflow :

`.github/workflows/deploy-brotoculateur-co2-vps.yml`

a été bloquée par les contrôles de sécurité de la plateforme avant écriture.

Le poste local contient des identités SSH, mais aucune voie SSH locale autorisée testée n’a authentifié le VPS en BatchMode ; les contrôles ont également refusé une tentative de forcer directement un fichier de clé.

Les workflows VPS existants sont verrouillés sur leurs propres vertèbres. Ils n’ont pas été détournés pour transporter Co2.

**Aucun contournement n’a été effectué.**

## 14. Ce qui reste pour passer à LIVE_VALIDATED

Une seule capacité manque : un transport d’écriture VPS autorisé pouvant exécuter le runner Co2 versionné.

Dès qu’un tel canal est disponible, la suite doit rester :

`PRE_CO2 → exact-live stage → backup → canary → quiescent file proof → restart → independent POST_CO2 audit → checkpoint LIVE`

Les hashes de référence à conserver sont :

- PRE dashboard : `210abbe5d72fd4dcc4b154cb3d13a8d954567ac29ef5435381fe2f16fbce109b`
- POST dashboard attendu : `b393de960f8f0c6bfdb17b7049ab90142736491cadf86540f70a3ae6647b8e3e`
- Co2 module : `2e5fe79712cf1efd5f65391c3ec9106c2934973449f7053634696f27a7ec0580`
- Co1 : `032ba9e665349b7d426e32c19d3c532467a0245e35a27da2cd66e2d1209864d2`
- S5 : `de885d1f4748d236a0050cbea87560cf26fc74a08a95a8a02b119241ce6b0334`
- C3 : `b7970583e688488d0f9fd8a90838d9163d00b08b7e6afedd499434e79a06c434`

## 15. Interdiction d’avancer silencieusement

Co3 — Checkpoint ne doit pas être déclaré démarré/live tant que Co2 n’a pas reçu sa preuve live complète.

État honnête actuel :

`Co1 = LIVE_VALIDATED_PERSISTENCE_BOUNDARY`

`Co2 = READY_FOR_LIVE_CANARY`

`Co3 = NOT_STARTED`

`Co4 = NOT_STARTED`
