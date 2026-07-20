# state.checkpoint.v1 — Contrat de checkpoint immuable

## Statut

- **Skill ID :** `state.checkpoint`
- **Version proposée :** `1.0.0`
- **Statut :** `PROPOSED`
- **Spécification parente :** `antmux-agent-skill-v1`
- **Portée :** persistance locale, reprise, embranchement, vérification d’intégrité et journalisation d’un état d’exécution
- **Moteur d’exécution :** non implémenté dans ce document
- **Activation :** interdite avant validation de tous les contrats

---

## 1. But

`state.checkpoint.v1` conserve un état d’exécution Antmux de manière locale, immuable, traçable et vérifiable.

Il doit permettre de :

1. créer un checkpoint après une transition significative;
2. vérifier l’intégrité d’un checkpoint et de sa chaîne de parents;
3. reprendre une tâche après interruption sans dupliquer les effets;
4. créer une nouvelle branche depuis un ancien checkpoint;
5. proposer un rollback sans supprimer ni réécrire l’historique;
6. reconstruire la projection JSONL depuis SQLite;
7. associer chaque état à ses artefacts, permissions, métriques Rent et décisions humaines.

Un checkpoint ne contient pas la vérité complète du projet. Il contient une photographie minimale et suffisante pour expliquer, vérifier et reprendre une exécution.

---

## 2. Principes obligatoires

### 2.1 Immutabilité

Un checkpoint commis ne peut jamais être modifié en place.

Toute correction produit :

- un nouveau checkpoint;
- une nouvelle empreinte SHA-256;
- un lien explicite vers le parent;
- un événement expliquant la raison de la correction.

### 2.2 Aucun rollback destructif

Restaurer un ancien état ne supprime jamais les checkpoints plus récents.

La restauration crée une nouvelle branche :

```text
CHK-0004
├── CHK-0005
│   └── CHK-0006
└── CHK-0007-RESTORE
```

`CHK-0007-RESTORE` cite `CHK-0004` comme point de reprise et conserve la provenance de la branche abandonnée.

### 2.3 Refus par défaut

Tout outil, chemin, modèle, réseau ou mutation non explicitement autorisé est interdit.

### 2.4 État explicite

Aucun état critique ne doit exister uniquement dans le contexte d’un modèle.

Les états, transitions, erreurs, approbations, artefacts et métriques doivent être inscrits dans :

- SQLite pour l’état transactionnel;
- JSONL pour l’audit append-only;
- des artefacts JSON immuables pour les snapshots;
- SHA-256 pour l’intégrité.

### 2.5 Idempotence

La répétition de la même opération avec la même clé d’idempotence doit retourner le checkpoint existant, sans créer une seconde écriture.

### 2.6 Pas de secret

Un checkpoint ne doit jamais contenir :

- mot de passe;
- jeton;
- cookie;
- clé API;
- contenu de fichier classé secret;
- variable d’environnement sensible;
- texte privé non nécessaire à la reprise.

Les secrets sont remplacés par des références opaques non réversibles.

---

## 3. Position dans LinuxIA

```text
LinuxIA CLI
    ↓
Antmux Orchestrator
    ↓
state.checkpoint.v1
    ├── SQLite
    ├── JSONL
    └── artefacts SHA-256
    ↓
Skills spécialisés
```

L’orchestrateur reste l’autorité des transitions. `state.checkpoint.v1` ne décide pas seul qu’une tâche est validée, rejetée ou autorisée.

---

## 4. États distincts

Deux familles d’états doivent rester séparées.

### 4.1 État de la tâche

```text
DISCOVERED
SELECTED
LOADED
AUTHORIZED
RUNNING
UNDER_REVIEW
VALIDATED
REJECTED
FAILED
ROLLED_BACK
```

### 4.2 État du checkpoint

```text
COMMITTED
VERIFIED
CORRUPT
SUPERSEDED
```

Un checkpoint peut représenter une tâche `RUNNING` tout en étant lui-même `VERIFIED`.

---

## 5. Opérations autorisées

### `CREATE`

Crée un nouveau checkpoint immuable à partir d’un état courant autorisé.

### `VERIFY`

Recalcule les empreintes et vérifie :

- le snapshot;
- les artefacts référencés;
- le parent;
- la chaîne d’événements;
- la cohérence SQLite/JSONL.

### `LIST`

Retourne les métadonnées minimales des checkpoints accessibles.

### `READ`

Lit un checkpoint précis après contrôle des permissions.

### `FORK`

Crée une nouvelle branche depuis un checkpoint historique sans modifier la branche d’origine.

### `RESTORE_PLAN`

Produit un plan de restauration vérifiable, sans exécuter les effets externes.

### `ACTIVATE_BRANCH`

Déplace le pointeur actif vers une branche déjà créée. Cette opération exige une approbation humaine lorsque la branche courante a dépassé `AUTHORIZED`.

### `REBUILD_AUDIT_PROJECTION`

Reconstruit les lignes JSONL manquantes depuis l’outbox SQLite, sans modifier les checkpoints.

---

## 6. Outils proposés

```text
checkpoint.create
checkpoint.verify
checkpoint.list
checkpoint.read
checkpoint.fork
checkpoint.restore_plan
checkpoint.activate_branch
checkpoint.rebuild_audit
```

Outils explicitement interdits :

```text
filesystem.delete
github.push
github.write
network.request
process.kill
process.spawn
checkpoint.rewrite
checkpoint.delete
```

---

## 7. Permissions proposées

```yaml
permissions:
  default_deny: true

  tools:
    allow:
      - checkpoint.create
      - checkpoint.verify
      - checkpoint.list
      - checkpoint.read
      - checkpoint.fork
      - checkpoint.restore_plan
      - checkpoint.activate_branch
      - checkpoint.rebuild_audit
    deny:
      - checkpoint.rewrite
      - checkpoint.delete
      - filesystem.delete
      - github.push
      - github.write
      - process.kill
      - process.spawn
      - network.request

  filesystem:
    read:
      - state/checkpoints/**
      - state/events/**
      - state/approvals/**
      - artifacts/**
    write:
      - state/checkpoints/**
      - state/events/**
      - state/outbox/**
    deny:
      - .git/**
      - secrets/**
      - credentials/**
      - "**/../**"

  network:
    allowed: false
    destinations: []

  models:
    allow: []
```

Le skill ne nécessite aucun modèle Ollama.

---

## 8. Sécurité proposée

```yaml
safety:
  risk_level: medium
  read_only: false
  destructive: false
  idempotent: true
  open_world: false
  mutation_allowed: true
  mutation_scope: append_only_checkpoint_records
  human_approval:
    before_start: false
    before_external_write: true
    before_destructive_action: true
    before_activate_branch_after_running: true
```

`mutation_allowed: true` autorise uniquement l’ajout de nouveaux enregistrements immuables et la mise à jour transactionnelle du pointeur de branche actif.

---

## 9. Identité d’un checkpoint

Format recommandé :

```text
CHK-<TASK_ID>-<RUN_ID>-<SEQUENCE>
```

Exemple :

```text
CHK-TASK-0042-RUN-20260720-0042-0005
```

Chaque checkpoint doit aussi posséder :

- `checkpoint_sha256` — empreinte du snapshot canonique;
- `payload_sha256` — empreinte du contenu fonctionnel;
- `parent_checkpoint_id` — parent immédiat;
- `root_checkpoint_id` — racine de la lignée;
- `branch_id` — branche logique;
- `sequence` — numéro monotone dans la branche;
- `idempotency_key` — clé de déduplication;
- `created_at_utc` — horodatage UTC;
- `created_by_agent_id` — identité du créateur;
- `correlation_id` — corrélation de l’opération.

---

## 10. Contenu minimal du snapshot

```json
{
  "$schema": "antmux://schemas/state-checkpoint-v1",
  "schema_version": "state-checkpoint-v1",
  "checkpoint_id": "CHK-TASK-0042-RUN-20260720-0042-0005",
  "checkpoint_status": "COMMITTED",
  "task_id": "TASK-0042",
  "run_id": "RUN-20260720-0042",
  "correlation_id": "CORR-20260720-0042-005",
  "agent_id": "orchestrator-01",
  "skill_id": "reviewer.scientific",
  "skill_version": "1.0.0",
  "task_state": "UNDER_REVIEW",
  "attempt": 1,
  "branch_id": "BRANCH-MAIN",
  "sequence": 5,
  "root_checkpoint_id": "CHK-TASK-0042-RUN-20260720-0042-0001",
  "parent_checkpoint_id": "CHK-TASK-0042-RUN-20260720-0042-0004",
  "restore_source_checkpoint_id": null,
  "idempotency_key": "sha256:...",
  "permissions_snapshot_sha256": "sha256:...",
  "inputs": [
    {
      "artifact_id": "ART-INPUT-001",
      "path": "artifacts/input/source.md",
      "sha256": "sha256:...",
      "bermuda_state": "VALIDATED"
    }
  ],
  "outputs": [
    {
      "artifact_id": "ART-OUTPUT-001",
      "path": "artifacts/output/review.json",
      "sha256": "sha256:...",
      "bermuda_state": "UNDER_REVIEW"
    }
  ],
  "tool_calls": {
    "count": 3,
    "denied": 0,
    "last_correlation_id": "CORR-20260720-0042-004"
  },
  "rent": {
    "messages_in": 4,
    "messages_out": 2,
    "bytes_read": 18342,
    "bytes_written": 4811,
    "prompt_chars": 9211,
    "response_chars": 2844,
    "wait_ms": 314,
    "inference_ms": 18432,
    "retries": 0,
    "denied_calls": 0
  },
  "approval_refs": [],
  "error": null,
  "next_action": "independent_review",
  "created_at_utc": "2026-07-20T20:30:00Z",
  "payload_sha256": "sha256:...",
  "checkpoint_sha256": "sha256:..."
}
```

---

## 11. Canonicalisation et empreintes

Avant calcul SHA-256 :

1. encodage UTF-8 sans BOM;
2. fins de ligne LF;
3. clés JSON triées ordinalement;
4. aucun espace non significatif;
5. dates UTC en ISO 8601;
6. chemins relatifs avec `/`;
7. chaînes Unicode normalisées en NFC;
8. champs d’empreinte exclus du calcul qu’ils décrivent.

Le résultat canonique est l’autorité d’intégrité.

---

## 12. Transaction atomique

SQLite est la source transactionnelle de vérité.

Une création suit cet ordre logique :

1. valider le contrat d’entrée;
2. vérifier les permissions;
3. vérifier le parent attendu;
4. calculer la clé d’idempotence;
5. construire le snapshot canonique;
6. calculer les empreintes;
7. écrire l’artefact temporaire;
8. ouvrir une transaction SQLite;
9. insérer le checkpoint;
10. insérer l’événement d’audit dans l’outbox;
11. mettre à jour le pointeur actif avec verrou optimiste;
12. valider la transaction;
13. renommer atomiquement l’artefact temporaire;
14. projeter l’événement vers JSONL;
15. marquer l’événement d’outbox comme livré.

Si l’étape JSONL échoue après le commit SQLite, `REBUILD_AUDIT_PROJECTION` doit pouvoir la rejouer sans dupliquer la ligne.

---

## 13. SQLite proposé

Tables minimales :

```text
checkpoints
checkpoint_artifacts
checkpoint_approvals
branches
active_branch_pointers
audit_outbox
idempotency_keys
```

Contraintes obligatoires :

- clé primaire sur `checkpoint_id`;
- unicité de `(branch_id, sequence)`;
- unicité de `idempotency_key`;
- clé étrangère vers le parent;
- un seul pointeur actif par `run_id`;
- aucune mise à jour du payload d’un checkpoint commis;
- suppression interdite par l’API applicative.

---

## 14. Concurrence

La création exige :

```text
expected_parent_checkpoint_id
expected_sequence
```

Si le pointeur actif a changé, l’opération échoue avec :

```text
CHECKPOINT_CONFLICT
```

Les workers parallèles utilisent des `run_id` ou `branch_id` distincts. Une fusion ne se fait jamais par écrasement; elle produit un checkpoint d’intégration avec références aux branches sources.

---

## 15. Reprise après panne

Au démarrage, l’orchestrateur doit :

1. lire le pointeur actif SQLite;
2. vérifier le checkpoint et sa chaîne;
3. vérifier les artefacts nécessaires;
4. rejouer l’outbox non livrée;
5. détecter les opérations préparées mais non commises;
6. reconstruire la prochaine action autorisée;
7. refuser la reprise si un effet externe ne peut pas être prouvé idempotent.

États de reprise :

```text
RESUME_SAFE
RESUME_REQUIRES_APPROVAL
RESUME_BLOCKED_CORRUPT
RESUME_BLOCKED_NON_IDEMPOTENT
```

---

## 16. Restauration et embranchement

`RESTORE_PLAN` doit produire :

- checkpoint source;
- branche actuelle;
- artefacts à réutiliser;
- artefacts devenus obsolètes;
- effets externes déjà réalisés;
- risques de duplication;
- approbations nécessaires;
- état cible proposé;
- nouvelle branche proposée.

`ACTIVATE_BRANCH` ne doit jamais :

- supprimer une branche;
- modifier un checkpoint;
- réutiliser un `run_id` ambigu;
- répéter un effet externe sans preuve d’idempotence.

---

## 17. Sortie proposée

```json
{
  "$schema": "antmux://schemas/state-checkpoint-result-v1",
  "schema_version": "state-checkpoint-result-v1",
  "ok": true,
  "operation": "CREATE",
  "checkpoint_id": "CHK-TASK-0042-RUN-20260720-0042-0005",
  "checkpoint_status": "VERIFIED",
  "task_state": "UNDER_REVIEW",
  "branch_id": "BRANCH-MAIN",
  "sequence": 5,
  "created": true,
  "deduplicated": false,
  "checkpoint_sha256": "sha256:...",
  "payload_sha256": "sha256:...",
  "parent_checkpoint_id": "CHK-TASK-0042-RUN-20260720-0042-0004",
  "next_action": "independent_review",
  "warnings": []
}
```

---

## 18. Erreurs structurées

```text
CHECKPOINT_NOT_FOUND
CHECKPOINT_CONFLICT
CHECKPOINT_CORRUPT
CHECKPOINT_CHAIN_BROKEN
CHECKPOINT_HASH_MISMATCH
ARTIFACT_HASH_MISMATCH
INVALID_STATE_TRANSITION
IDEMPOTENCY_KEY_REUSED_WITH_DIFFERENT_PAYLOAD
APPROVAL_REQUIRED
PATH_NOT_ALLOWED
PATH_TRAVERSAL
TOOL_NOT_ALLOWED
NETWORK_NOT_ALLOWED
AUDIT_PROJECTION_INCOMPLETE
NON_IDEMPOTENT_EFFECT_DETECTED
```

Une erreur ne doit jamais être convertie silencieusement en réussite partielle.

---

## 19. Télémétrie Rent

Chaque opération journalise au minimum :

```text
checkpoints_read
checkpoints_written
artifacts_verified
bytes_read
bytes_written
sqlite_reads
sqlite_writes
jsonl_lines_written
hashes_computed
wait_ms
retries
conflicts
denied_calls
outbox_replays
```

Aucun seuil universel n’est fixé. Les coûts seront comparés expérimentalement.

---

## 20. Tests minimaux

### Manifeste

1. identifiant et version exacts;
2. réseau interdit;
3. aucun modèle autorisé;
4. permissions append-only;
5. outils destructifs refusés;
6. chemins référencés présents;
7. checksums valides.

### Contrats

1. création initiale valide;
2. parent obligatoire après le premier checkpoint;
3. séquence monotone;
4. identifiant dupliqué refusé;
5. clé d’idempotence identique et payload identique dédupliqués;
6. clé d’idempotence identique et payload différent refusés;
7. chemin absolu refusé;
8. traversée de chemin refusée;
9. empreinte en majuscules refusée;
10. état de tâche inconnu refusé;
11. état de checkpoint inconnu refusé;
12. propriété supplémentaire refusée;
13. secret détecté refusé;
14. parent inexistant refusé;
15. parent d’une autre tâche refusé;
16. branche incorrecte refusée;
17. compteur Rent négatif refusé;
18. tableau brut en sortie refusé;
19. rollback destructif refusé;
20. restauration sans plan refusée.

### Intégrité

1. snapshot intact accepté;
2. snapshot modifié détecté;
3. artefact modifié détecté;
4. parent modifié détecté;
5. chaîne brisée détectée;
6. projection JSONL manquante reconstruite;
7. projection JSONL dupliquée évitée.

### Cycle de vie

1. transition normale complète;
2. transition illégale refusée;
3. reprise idempotente;
4. conflit concurrent refusé;
5. fork valide;
6. activation de branche avec approbation;
7. activation sans approbation refusée;
8. branche ancienne conservée;
9. checkpoint corrompu bloque la reprise;
10. effet non idempotent bloque la reprise.

Résultat obligatoire avant activation :

```text
ALL_TESTS: PASS
```

---

## 21. Structure future du paquet

```text
skills/state.checkpoint.v1/
├── README.md
├── skill.yaml
├── instructions.md
├── resources/
│   ├── lifecycle-rules.md
│   ├── canonicalization-rules.md
│   ├── recovery-rules.md
│   └── error-codes.md
├── schemas/
│   ├── input.schema.json
│   ├── checkpoint.schema.json
│   └── output.schema.json
├── tests/
│   ├── manifest.tests.json
│   ├── permissions.tests.json
│   ├── contracts.tests.json
│   ├── integrity.tests.json
│   └── lifecycle.tests.json
├── migrations/
│   └── 001-state-checkpoint-v1.sql
└── checksums.sha256
```

---

## 22. Commandes CLI proposées

```powershell
linuxia checkpoints list --task TASK-0042
linuxia checkpoints inspect CHK-TASK-0042-RUN-20260720-0042-0005
linuxia checkpoints verify CHK-TASK-0042-RUN-20260720-0042-0005
linuxia checkpoints restore-plan CHK-TASK-0042-RUN-20260720-0042-0004
linuxia checkpoints fork CHK-TASK-0042-RUN-20260720-0042-0004
linuxia checkpoints activate BRANCH-RESTORE-0001
linuxia checkpoints rebuild-audit --run RUN-20260720-0042
```

Ces commandes ne constituent pas encore une implémentation.

---

## 23. Critères d’acceptation

`state.checkpoint.v1` sera prêt pour prototype lorsque :

1. le paquet complet existe;
2. tous les schémas Draft 7 sont verrouillés;
3. la migration SQLite est testée sur une base temporaire;
4. une interruption simulée est reprise sans duplication;
5. une corruption d’artefact bloque correctement la reprise;
6. un fork conserve entièrement la branche d’origine;
7. un conflit concurrent est refusé;
8. l’outbox reconstruit JSONL sans doublon;
9. aucun secret n’apparaît dans les snapshots;
10. le validateur PowerShell 5.1 retourne `ALL_TESTS: PASS`.

---

## 24. Non-objectifs de la V1

La première version ne doit pas :

- orchestrer elle-même les agents;
- lancer Ollama;
- prendre une décision scientifique;
- écrire sur GitHub;
- supprimer des checkpoints;
- synchroniser avec un cloud;
- fusionner automatiquement des branches concurrentes;
- restaurer un effet externe non idempotent;
- permettre à un modèle de modifier directement SQLite;
- remplacer la validation humaine des restaurations sensibles.

---

## 25. Prochaine action unique

Construire uniquement le paquet déclaratif et son validateur en lecture seule :

```text
skills/state.checkpoint.v1/
```

Aucune base SQLite réelle, aucune restauration et aucun moteur d’exécution ne seront activés avant validation complète du paquet.