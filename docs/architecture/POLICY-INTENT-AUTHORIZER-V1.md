# policy.intent-authorizer.v1 — Contrat d’autorisation par intention

## Statut

- **Skill ID :** `policy.intent-authorizer`
- **Version proposée :** `1.0.0`
- **Statut :** `PROPOSED`
- **Spécification parente :** `antmux-agent-skill-v1`
- **Portée :** vérifier qu’une action proposée correspond à l’intention explicite de l’utilisateur, aux permissions statiques et aux approbations requises
- **Moteur d’exécution :** absent
- **Modèle :** aucun modèle autorisé dans la V1
- **Réseau :** interdit
- **Activation :** interdite avant validation complète du paquet déclaratif et des tests

---

## 1. But

`policy.intent-authorizer.v1` produit une décision déterministe avant chaque action contrôlée.

Il répond à trois questions distinctes :

1. **Permission statique :** le skill et l’agent possèdent-ils normalement le droit d’utiliser cet outil sur cette ressource ?
2. **Alignement d’intention :** l’action précise demandée correspond-elle à ce que l’utilisateur a explicitement autorisé ?
3. **Approbation humaine :** l’action exige-t-elle une approbation supplémentaire avant exécution ?

Le skill ne remplace pas le système de permissions. Il ajoute une barrière plus étroite : une capacité disponible n’est pas automatiquement une action autorisée.

Exemple :

```text
Permission statique : filesystem.write est disponible
Intention utilisateur : analyser le fichier sans le modifier
Action proposée : écraser le fichier
Décision : DENY / INTENT_SCOPE_MISMATCH
```

---

## 2. Principe fondamental

### Le modèle ne s’autorise jamais lui-même

Un agent ou un modèle ne peut pas :

- élargir l’intention de l’utilisateur;
- déclarer une ambiguïté résolue en sa faveur;
- produire lui-même l’approbation qui lui manque;
- modifier l’enveloppe d’intention qu’il doit respecter;
- transformer une permission générale en consentement particulier.

La V1 ne lit pas directement une conversation libre pour deviner l’intention. Elle reçoit une **enveloppe d’intention structurée**, créée en amont par l’orchestrateur et, lorsque nécessaire, confirmée par l’utilisateur.

Cette séparation empêche qu’un même modèle interprète la demande, propose l’action et s’accorde ensuite l’autorisation.

---

## 3. Position dans LinuxIA

```text
Utilisateur
    ↓
Intent Envelope
    ↓
Antmux Orchestrator
    ↓
policy.intent-authorizer.v1
    ├── permissions statiques
    ├── contraintes d’intention
    ├── politique de risque
    └── approbations humaines
    ↓
ALLOW / DENY / REQUIRE_HUMAN_APPROVAL
    ↓
Exécution éventuelle de l’outil
```

L’autorité finale d’exécution demeure l’orchestrateur.

`policy.intent-authorizer.v1` ne lance aucun outil métier. Il retourne uniquement une décision structurée et vérifiable.

---

## 4. Les trois couches de contrôle

### 4.1 Couche A — Permission statique

Elle vérifie notamment :

- l’outil figure dans `permissions.tools.allow`;
- l’outil ne figure pas dans une liste de refus;
- le rôle et l’agent correspondent;
- le chemin respecte les préfixes autorisés;
- le réseau est autorisé ou interdit;
- le modèle demandé est autorisé;
- le nombre maximal de tentatives n’est pas dépassé;
- les identifiants d’exécution sont présents.

Un échec à cette couche produit toujours `DENY`.

### 4.2 Couche B — Alignement d’intention

Elle compare l’action proposée à l’enveloppe d’intention :

- type d’action;
- outil;
- ressources ciblées;
- opérations permises;
- opérations interdites;
- portée des données;
- destination;
- limite temporelle;
- budget Rent;
- nombre maximal d’éléments;
- effets externes autorisés;
- mutations autorisées;
- conditions d’arrêt.

Une action plus large que l’intention produit `DENY` ou `REQUIRE_HUMAN_APPROVAL`, selon la politique explicite.

### 4.3 Couche C — Approbation humaine

Elle vérifie les approbations nécessaires pour :

- écriture externe;
- action destructive;
- publication;
- envoi de message;
- push GitHub;
- activation d’une branche sensible;
- installation;
- activation d’un modèle;
- dépassement de budget;
- changement de portée;
- accès à une nouvelle destination.

Une approbation doit être liée à l’action exacte, à son empreinte et à une période de validité.

---

## 5. Décisions possibles

La V1 retourne exactement une décision principale :

```text
ALLOW
DENY
REQUIRE_HUMAN_APPROVAL
```

### `ALLOW`

Toutes les conditions sont satisfaites :

- permission statique valide;
- action incluse dans l’intention;
- aucune contrainte violée;
- approbations requises présentes et valides;
- empreintes cohérentes.

### `DENY`

L’action est interdite ou incompatible avec le contrat.

Un refus est final pour cette proposition précise. Une nouvelle proposition peut être soumise avec une portée différente ou une nouvelle intention confirmée.

### `REQUIRE_HUMAN_APPROVAL`

L’action peut être techniquement permise, mais elle nécessite une décision humaine supplémentaire.

Ce résultat ne signifie jamais « autorisé en attendant ». L’exécution reste interdite jusqu’à réception d’une approbation valide et nouvelle évaluation.

---

## 6. Enveloppe d’intention

L’enveloppe d’intention est un objet immuable qui représente ce que l’utilisateur a autorisé pour une tâche donnée.

Exemple minimal :

```json
{
  "$schema": "antmux://schemas/intent-envelope-v1",
  "schema_version": "intent-envelope-v1",
  "intent_id": "INTENT-TASK-0042-001",
  "task_id": "TASK-0042",
  "created_at_utc": "2026-07-20T22:00:00Z",
  "created_by": "orchestrator-01",
  "confirmed_by_user": true,
  "objective": "Analyser le rapport sans modifier les fichiers sources.",
  "allowed_actions": [
    "READ",
    "ANALYZE",
    "WRITE_REPORT"
  ],
  "denied_actions": [
    "DELETE",
    "OVERWRITE_SOURCE",
    "PUBLISH",
    "SEND_MESSAGE"
  ],
  "allowed_tools": [
    "source.read",
    "report.write"
  ],
  "resource_scopes": [
    {
      "mode": "read",
      "pattern": "inputs/**"
    },
    {
      "mode": "write",
      "pattern": "reports/**"
    }
  ],
  "network_allowed": false,
  "external_effects_allowed": false,
  "destructive_actions_allowed": false,
  "max_items": 25,
  "rent_budget": {
    "max_tool_calls": 20,
    "max_inference_ms": 120000,
    "max_bytes_written": 200000
  },
  "expires_at_utc": "2026-07-21T02:00:00Z",
  "intent_sha256": "sha256:..."
}
```

---

## 7. Règles de l’enveloppe d’intention

### 7.1 Immutabilité

Une enveloppe confirmée ne peut pas être modifiée en place.

Toute extension crée :

- un nouvel `intent_id`;
- une nouvelle empreinte;
- un lien vers l’intention précédente;
- une justification;
- une nouvelle confirmation lorsque la portée augmente.

### 7.2 Portée minimale

L’enveloppe doit exprimer la plus petite portée suffisante.

Les formulations générales comme celles-ci sont interdites dans un environnement contrôlé :

```text
faire tout ce qui est nécessaire
gérer le projet
utiliser tous les outils disponibles
corriger automatiquement tous les problèmes
```

### 7.3 Refus par défaut

Tout élément absent de l’enveloppe est considéré non autorisé.

### 7.4 Expiration

Une intention expirée ne peut produire `ALLOW`.

### 7.5 Zéro secret

L’enveloppe ne contient aucun jeton, mot de passe, cookie, clé API ou secret brut.

---

## 8. Action proposée

L’action proposée est la requête exacte que l’orchestrateur envisage d’exécuter.

Exemple :

```json
{
  "$schema": "antmux://schemas/proposed-action-v1",
  "schema_version": "proposed-action-v1",
  "action_id": "ACTION-TASK-0042-017",
  "task_id": "TASK-0042",
  "run_id": "RUN-20260720-0042",
  "correlation_id": "CORR-20260720-0042-017",
  "agent_id": "worker-01",
  "skill_id": "reviewer.scientific",
  "skill_version": "1.0.0",
  "operation": "WRITE_REPORT",
  "tool_name": "report.write",
  "arguments": {
    "path": "reports/source-123-review.md",
    "mode": "create"
  },
  "arguments_sha256": "sha256:...",
  "estimated_rent": {
    "tool_calls": 1,
    "bytes_written": 12000,
    "inference_ms": 0
  },
  "external_effect": false,
  "destructive": false,
  "action_sha256": "sha256:..."
}
```

Les arguments sensibles peuvent être remplacés par des références opaques. L’empreinte doit toutefois couvrir la représentation canonique réellement évaluée.

---

## 9. Contrat d’entrée proposé

```json
{
  "schema_version": "intent-authorization-input-v1",
  "task_id": "TASK-0042",
  "run_id": "RUN-20260720-0042",
  "correlation_id": "CORR-20260720-0042-017",
  "authorizer_id": "intent-authorizer-01",
  "intent_envelope": {},
  "proposed_action": {},
  "permission_snapshot": {},
  "risk_policy": {},
  "approval_refs": [],
  "current_rent": {},
  "evaluated_at_utc": "2026-07-20T22:01:00Z"
}
```

Champs obligatoires :

- `schema_version`;
- `task_id`;
- `run_id`;
- `correlation_id`;
- `authorizer_id`;
- `intent_envelope`;
- `proposed_action`;
- `permission_snapshot`;
- `risk_policy`;
- `approval_refs`;
- `current_rent`;
- `evaluated_at_utc`.

---

## 10. Contrat de sortie proposé

```json
{
  "schema_version": "intent-authorization-output-v1",
  "decision_id": "DECISION-TASK-0042-017",
  "task_id": "TASK-0042",
  "run_id": "RUN-20260720-0042",
  "correlation_id": "CORR-20260720-0042-017",
  "decision": "ALLOW",
  "reason_codes": [
    "STATIC_PERMISSION_MATCH",
    "INTENT_SCOPE_MATCH",
    "APPROVAL_NOT_REQUIRED",
    "RENT_WITHIN_BUDGET"
  ],
  "matched_constraints": [
    "tool_name",
    "operation",
    "write_scope",
    "network_allowed",
    "max_bytes_written"
  ],
  "violated_constraints": [],
  "required_approvals": [],
  "intent_sha256": "sha256:...",
  "action_sha256": "sha256:...",
  "permission_snapshot_sha256": "sha256:...",
  "policy_sha256": "sha256:...",
  "decision_payload_sha256": "sha256:...",
  "evaluated_at_utc": "2026-07-20T22:01:00Z",
  "expires_at_utc": "2026-07-20T22:06:00Z"
}
```

La décision doit être courte durée. Une modification de l’action, de ses arguments, de l’intention, des permissions ou de la politique invalide la décision.

---

## 11. Ordre déterministe d’évaluation

L’ordre suivant est obligatoire :

1. valider le schéma d’entrée;
2. vérifier l’identité de tâche, run et corrélation;
3. vérifier les empreintes de l’intention, de l’action et des permissions;
4. vérifier l’expiration de l’intention;
5. vérifier les permissions statiques;
6. vérifier les refus absolus;
7. comparer l’outil et l’opération à l’intention;
8. comparer les ressources et destinations;
9. vérifier les effets externes;
10. vérifier les propriétés destructives;
11. vérifier les limites quantitatives;
12. vérifier le budget Rent courant et estimé;
13. déterminer les approbations nécessaires;
14. vérifier les approbations présentes;
15. produire la décision;
16. calculer l’empreinte de décision;
17. journaliser le résultat.

Une étape échouée ne peut pas être compensée par une étape suivante.

---

## 12. Règles de comparaison

### 12.1 Pas d’élargissement implicite

L’action proposée doit être incluse dans l’intention, jamais seulement « compatible en esprit ».

### 12.2 Paramètres exacts

Les paramètres sensibles doivent être comparés :

- chemin;
- méthode;
- destination;
- destinataire;
- branche;
- dépôt;
- commande;
- modèle;
- quantité;
- durée;
- budget.

### 12.3 Chemins

Un chemin est autorisé uniquement s’il :

- est relatif;
- ne contient aucune traversée `..`;
- correspond à un préfixe autorisé;
- ne tombe pas sous un préfixe interdit;
- respecte le mode lecture ou écriture déclaré.

### 12.4 Ensembles

Une liste proposée doit être un sous-ensemble de la liste autorisée.

### 12.5 Limites numériques

La somme `consommation actuelle + coût estimé` ne doit pas dépasser la limite.

### 12.6 Valeurs absentes

Une limite absente ne signifie jamais illimitée. Elle signifie que l’action nécessitant cette limite n’est pas autorisée.

---

## 13. Approbations humaines

Une approbation est un artefact distinct :

```json
{
  "schema_version": "human-approval-v1",
  "approval_id": "APPROVAL-BRUTUS-001",
  "approved_by": "Brutus",
  "task_id": "TASK-0042",
  "intent_sha256": "sha256:...",
  "action_sha256": "sha256:...",
  "approval_scope": "EXACT_ACTION",
  "created_at_utc": "2026-07-20T22:02:00Z",
  "expires_at_utc": "2026-07-20T22:12:00Z",
  "approval_sha256": "sha256:..."
}
```

Règles :

- une approbation ne peut pas être réutilisée pour une action différente;
- une approbation expirée est invalide;
- une approbation liée à une ancienne empreinte est invalide;
- une approbation ne remplace pas une permission statique absente;
- une approbation ne peut pas autoriser un refus absolu de sécurité;
- une approbation ne peut pas être créée par l’agent bénéficiaire.

---

## 14. Refus absolus proposés

La V1 refuse toujours :

- action dont l’identité est invalide;
- outil absent des permissions statiques;
- action explicitement interdite dans l’intention;
- traversée de chemin;
- secret brut dans les journaux ou contrats;
- empreinte invalide;
- intention expirée;
- action modifiée après approbation;
- décision d’autorisation produite par l’agent bénéficiaire;
- usage d’un modèle pour contourner une règle déterministe;
- activation automatique d’un modèle;
- réécriture de l’intention confirmée;
- exécution avant obtention de la décision;
- exécution après expiration de la décision.

---

## 15. Codes de décision proposés

### Validation et identité

```text
INPUT_INVALID
IDENTITY_INVALID
SCHEMA_VERSION_UNSUPPORTED
SHA256_INVALID
HASH_MISMATCH
```

### Permissions statiques

```text
TOOL_NOT_ALLOWED
ROLE_NOT_ALLOWED
SKILL_NOT_ALLOWED
MODEL_NOT_ALLOWED
NETWORK_NOT_ALLOWED
PATH_NOT_ALLOWED
MAX_ATTEMPTS_EXCEEDED
```

### Intention

```text
INTENT_EXPIRED
INTENT_NOT_CONFIRMED
INTENT_SCOPE_MISMATCH
OPERATION_NOT_ALLOWED
RESOURCE_SCOPE_MISMATCH
DESTINATION_NOT_ALLOWED
EXTERNAL_EFFECT_NOT_ALLOWED
DESTRUCTIVE_ACTION_NOT_ALLOWED
ITEM_LIMIT_EXCEEDED
RENT_BUDGET_EXCEEDED
STOP_CONDITION_REACHED
```

### Approbation

```text
APPROVAL_REQUIRED
APPROVAL_INVALID
APPROVAL_EXPIRED
APPROVAL_SCOPE_MISMATCH
APPROVAL_HASH_MISMATCH
```

### Réussite

```text
STATIC_PERMISSION_MATCH
INTENT_SCOPE_MATCH
APPROVAL_VALID
APPROVAL_NOT_REQUIRED
RENT_WITHIN_BUDGET
ACTION_AUTHORIZED
```

---

## 16. Permissions proposées du skill

```yaml
permissions:
  default_deny: true

  tools:
    allow:
      - policy.intent.evaluate
      - policy.intent.explain
    deny:
      - filesystem.write
      - filesystem.delete
      - github.write
      - github.push
      - network.request
      - process.spawn
      - process.kill
      - model.invoke
      - tool.execute

  filesystem:
    read:
      - state/intents/**
      - state/permissions/**
      - state/approvals/**
      - state/policies/**
      - state/rent/**
    write: []
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

Le journal de décision est écrit par l’orchestrateur ou un composant append-only distinct. L’auteur de la décision ne doit pas posséder un outil général d’écriture.

---

## 17. Sécurité proposée

```yaml
safety:
  risk_level: high
  read_only: true
  destructive: false
  idempotent: true
  open_world: false
  mutation_allowed: false
  human_approval:
    before_start: false
    before_external_write: false
    before_destructive_action: false
```

Le niveau de risque est `high` non parce que le skill produit directement un effet, mais parce qu’une erreur d’autorisation pourrait permettre un effet dangereux ailleurs.

---

## 18. Idempotence

Avec les mêmes éléments :

- `intent_sha256`;
- `action_sha256`;
- `permission_snapshot_sha256`;
- `policy_sha256`;
- `approval_sha256`;
- `current_rent_sha256`;

le skill doit retourner la même décision logique et les mêmes codes de raison, hors identifiants techniques et horodatages explicitement exclus.

Une clé recommandée :

```text
sha256(intent + action + permissions + policy + approvals + rent)
```

---

## 19. Canonicalisation

Avant SHA-256 :

1. UTF-8 sans BOM;
2. fins de ligne LF;
3. JSON avec clés triées ordinalement;
4. aucun espace non significatif;
5. dates UTC ISO 8601;
6. chemins normalisés avec `/`;
7. Unicode NFC;
8. listes dont l’ordre n’est pas sémantique triées;
9. champs d’empreinte exclus de leur propre calcul;
10. valeurs secrètes remplacées par références opaques.

---

## 20. Journalisation

Chaque évaluation doit produire un événement append-only contenant :

- identité de tâche et de run;
- identifiant de décision;
- décision;
- codes de raison;
- empreintes de l’intention et de l’action;
- empreinte des permissions et de la politique;
- approbations utilisées;
- coût Rent de l’évaluation;
- horodatage;
- expiration de la décision.

Le journal ne contient pas les arguments secrets ni le texte complet de la conversation.

---

## 21. Télémétrie Rent

Mesures proposées :

```text
intent_bytes_read
action_bytes_read
permission_rules_evaluated
constraints_evaluated
approvals_checked
decision_ms
cache_hit
denied_count
approval_required_count
```

Aucun coût d’inférence n’est attendu dans la V1, puisqu’aucun modèle n’est autorisé.

---

## 22. Relations avec les autres skills

### `state.checkpoint.v1`

Conserve les empreintes de l’intention, de l’action et de la décision d’autorisation.

### `approval.interrupt.v1`

Collecte une approbation humaine lorsque la décision est `REQUIRE_HUMAN_APPROVAL`.

### `orchestrator.delegate.v1`

Ne délègue une action exécutable qu’après décision `ALLOW` valide.

### `planner.task-graph.v1`

Produit des tâches proposées, mais ne leur accorde aucune autorisation.

### `memory.semantic-retriever.v1`

Peut retrouver des ressources, uniquement dans les portées de lecture autorisées par l’intention.

---

## 23. Scénarios minimaux de validation

### Autorisations attendues

- lecture d’un fichier explicitement inclus;
- création d’un rapport dans le répertoire autorisé;
- action non destructive sous le budget Rent;
- action sensible avec approbation exacte valide.

### Refus attendus

- outil techniquement disponible mais absent de l’intention;
- écriture lorsque l’utilisateur a demandé une analyse seulement;
- destination externe absente de l’intention;
- action destructive interdite;
- dépassement du nombre d’éléments;
- dépassement du budget Rent;
- chemin hors périmètre;
- approbation liée à une autre empreinte;
- intention expirée;
- action modifiée après décision;
- tentative du modèle de produire sa propre approbation.

### Approbations attendues

- publication explicitement envisagée mais non encore approuvée;
- mutation externe permise sous confirmation;
- extension de portée demandée par l’agent;
- installation ou activation d’un modèle;
- dépassement contrôlé d’un budget.

---

## 24. Tests minimaux obligatoires

### Manifeste

- refus par défaut;
- aucun modèle;
- aucun réseau;
- aucun outil d’exécution;
- lecture seule;
- statut `proposed`;
- schémas et checksums présents.

### Contrats

- entrée valide acceptée;
- sortie valide acceptée;
- décision inconnue refusée;
- tableau brut refusé;
- empreinte majuscule refusée;
- secret brut refusé;
- champ obligatoire absent refusé.

### Permissions statiques

- outil autorisé et intention compatible;
- outil interdit malgré intention compatible;
- chemin autorisé;
- chemin hors périmètre;
- réseau refusé;
- modèle refusé.

### Alignement d’intention

- sous-portée acceptée;
- portée élargie refusée;
- opération interdite refusée;
- liste proposée sous-ensemble acceptée;
- élément supplémentaire refusé;
- budget exact accepté;
- budget dépassé refusé.

### Approbations

- approbation absente;
- approbation valide;
- approbation expirée;
- empreinte différente;
- approbation réutilisée pour une autre action.

### Déterminisme

- mêmes entrées, même décision;
- ordre non sémantique des listes sans effet;
- changement d’un argument modifie l’empreinte et invalide la décision précédente.

Résultat obligatoire avant toute activation :

```text
ALL_TESTS: PASS
```

---

## 25. Critères d’acceptation V1

La V1 est acceptée lorsque :

1. l’autorisation reste entièrement déterministe;
2. aucun modèle n’est invoqué;
3. aucune action métier n’est exécutée;
4. un outil permis peut être refusé lorsque l’intention ne le couvre pas;
5. une approbation ne peut pas élargir une permission statique;
6. une action modifiée invalide automatiquement l’autorisation;
7. les limites Rent sont appliquées;
8. les décisions sont explicables par codes stables;
9. les empreintes sont vérifiées;
10. les journaux ne contiennent aucun secret;
11. les scénarios de contournement échouent;
12. tous les tests passent sous Windows PowerShell 5.1.

---

## 26. Non-objectifs V1

La première version ne cherche pas à :

- comprendre librement une conversation complète;
- utiliser un LLM pour décider l’autorisation;
- remplacer les permissions Antmux;
- exécuter l’action autorisée;
- écrire dans GitHub;
- installer ou activer un modèle;
- résoudre automatiquement une ambiguïté;
- donner une autorisation durable ou générale;
- supprimer l’approbation humaine des actions sensibles;
- devenir une politique universelle pour tous les systèmes externes.

---

## 27. Paquet déclaratif recommandé

```text
skills/
└── policy.intent-authorizer.v1/
    ├── README.md
    ├── skill.yaml
    ├── instructions.md
    ├── prompts/
    │   └── explain-decision.md
    ├── resources/
    │   ├── decision-rules.md
    │   ├── reason-codes.md
    │   └── approval-rules.md
    ├── schemas/
    │   ├── intent-envelope.schema.json
    │   ├── proposed-action.schema.json
    │   ├── input.schema.json
    │   └── output.schema.json
    ├── tests/
    │   ├── manifest.tests.json
    │   ├── permissions.tests.json
    │   ├── intent.tests.json
    │   ├── approvals.tests.json
    │   └── contracts.tests.json
    ├── tools/
    │   └── Test-IntentAuthorizerSkill.ps1
    └── checksums.sha256
```

Le prompt sert uniquement à expliquer une décision déjà calculée à partir de codes structurés. Il ne produit pas la décision d’autorisation.

---

## 28. Prochaine action unique

Construire le paquet déclaratif :

```text
skills/policy.intent-authorizer.v1/
```

avec un validateur PowerShell 5.1 strictement en lecture seule.

Aucune intégration dans l’orchestrateur et aucune activation réelle ne sont autorisées avant validation complète des contrats.
