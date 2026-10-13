# ASTRA CHECKPOINT — Brutus Co2 PRE refresh

Date : 2026-10-13

Statut : `READY_FOR_LIVE_CANARY`

Ce fichier complète le checkpoint principal Co2 sans modifier son statut.

## Transport admin

Le canal SSH admin local a été vérifié avec succès avant le PRE :

- `SSH_OK=YES`
- hôte : `server1.antmux.com`
- utilisateur : `rob`

Les fichiers Co2 exacts de `main` ont également été récupérés et hashés localement avant staging.

SHA-256 :

- `co2_proof_chain.py` : `2e5fe79712cf1efd5f65391c3ec9106c2934973449f7053634696f27a7ec0580`
- `patch_brotoculateur_co2_proof_chain.py` : `439ba096803013cdf827b8d5692071483c98ad25428330eafa341308947a61b5`
- `run_co2_vps.sh` : `c6d5602e5b9d941bdb23edaf104981c180a86de20bdcefde29f821a28cb94e0e`
- `test_co2_proof_chain.py` : `1d3b58bac1143a35d2fd4f6c375895c43bb6c9e024c2d14d0c666a4a29399898`
- `verify_co2_chain_files.py` : `ca02af68883ac134bbe50c49810c4f4418e2e13c479a79b7022e991bc9127743`

## PRE_CO2 direct versionné

Le runner Co2 versionné a été exécuté en mode non-mutant `MODE=audit` contre le VPS.

Résultat : `CO2_AUDIT_ONLY=PASS`.

État observé :

- source : `PRE_CO2`
- dashboard : `210abbe5d72fd4dcc4b154cb3d13a8d954567ac29ef5435381fe2f16fbce109b`
- module Co2 : `ABSENT`
- module Co2 attendu : `2e5fe79712cf1efd5f65391c3ec9106c2934973449f7053634696f27a7ec0580`
- moteur : `RUNNING`
- processed : `211114`
- cristaux : `1949197`
- S5 observations : `1204213`
- S5 indexed : `400819`
- Co1 observations : `1204213`
- Co1 eligible : `400819`
- Co1 appended : `48143`
- Co1 already present : `352676`
- Co1 physical au snapshot : `48238`
- Co1 load errors : `0`
- Co1 write errors : `0`
- archive physique lors du comptage : `48243` lignes
- archive SHA-256 : `0fe5443ea53c8035046df363d3d54fb14ad5619565cc3ab7f5ead6766d373d6d`
- disque racine : `61%`

Le léger écart entre `physical_records_seen=48238` et le comptage physique `48243` est cohérent avec un moteur encore `RUNNING` : cinq lignes ont été ajoutées après le snapshot status et avant le `wc -l`. Aucune conclusion d'intégrité n'est tirée d'une comparaison non quiescente.

## Audit non-mutant le plus frais

Après le refus du canary mutatif, un nouvel audit Co1 V2 non-mutant a été exécuté pour confirmer que le live était resté sain.

Run GitHub Actions : `38420261490`

Résultat : `success` et `CO1V2_AUDIT_ONLY=PASS`.

État le plus frais :

- moteur : `RUNNING`
- processed : `222629`
- cristaux : `1950600`
- S5 observations : `1271449`
- S5 indexed : `467890`
- S5 blocked : `803559`
- S5 unique entries : `52697`
- S5 unique Z : `1717`
- Co1 observations : `1271449`
- Co1 eligible : `467890`
- Co1 appended : `52602`
- Co1 already present : `415288`
- Co1 loaded records : `95`
- Co1 loaded duplicate IDs : `0`
- Co1 physical records : `52697`
- Co1 unique records : `52697`
- Co1 unique Z : `1717`
- Co1 buckets : `37`
- Co1 load errors : `0`
- Co1 write errors : `0`
- archive physique : `52697` lignes
- archive SHA-256 : `f3a76b1ce6316327d61c7b28d603a5653d62c7d2e44f833b829b68ae05ba2a70`
- disque racine : `61%`

## Canary mutatif

L'invocation suivante devait lancer exactement le runner versionné en `MODE=canary_start`, avec les mêmes garde-fous, backup et rollback que documentés dans le checkpoint principal.

Elle a été refusée par les contrôles de sécurité de l'environnement **avant exécution de la commande SSH mutative**.

Conséquences :

- aucun patch Co2 appliqué ;
- aucun restart Brotoculateur déclenché par Co2 ;
- aucun fichier de chaîne Co2 créé par ce canary ;
- aucune donnée Co1 modifiée ;
- Co2 reste `READY_FOR_LIVE_CANARY` ;
- Co3 et Co4 restent `NOT_STARTED`.

Aucun contournement de ce garde n'a été tenté.
