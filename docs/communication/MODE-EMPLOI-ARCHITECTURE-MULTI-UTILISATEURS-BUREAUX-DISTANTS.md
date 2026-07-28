# MODE D’EMPLOI DIRECTEUR — ARCHITECTURE MULTI-UTILISATEURS, BUREAUX DISTANTS ET MOTEURS LOCAUX

**Projet :** LinuxIA / Antmux  
**Décideur final :** Brutus  
**Constructeur principal :** Rob  
**Version :** 1.0 — proposition directrice à challenger  
**Date :** 27 juillet 2026  
**Statut :** document d’architecture avant construction du premier building  
**Portée :** local-first, multi-utilisateurs, bureaux persistants, moteurs interchangeables, mémoire privée et bibliothèque commune  

---

## 0. But du document

Ce document définit une architecture permettant à Antmux de commencer sur un seul ordinateur, avec les moteurs et les bureaux sur le disque `D:\`, puis d’évoluer sans rupture vers une plateforme multi-utilisateurs accessible par un nom de domaine.

L’objectif n’est pas de créer immédiatement une plateforme mondiale. L’objectif est de construire une fondation qui ne devra pas être jetée lorsque d’autres utilisateurs arriveront.

Le système cible doit permettre :

- à chaque utilisateur de posséder son espace privé;
- à chaque organisation de posséder ses espaces d’équipe;
- à chaque profil de travailleur de conserver une identité durable;
- aux moteurs d’exécution de rester locaux, distants ou hybrides;
- aux bureaux d’être accessibles par un domaine sans devenir publics;
- à l’expérience individuelle de rester privée par défaut;
- aux leçons utiles de devenir communes uniquement après filtrage et validation;
- au système de fonctionner temporairement hors ligne;
- à l’utilisateur de reprendre son travail sur une autre machine;
- à Antmux de changer de moteur sans perdre la mémoire du travailleur;
- à la gouvernance de rester séparée de l’orchestration;
- à toute action importante d’être traçable, révisable et réversible.

---

# 1. Décision fondatrice

## 1.1 Formule cible

```text
Moteurs d’exécution
    principalement sur les machines des utilisateurs

Bureaux persistants
    locaux au départ
    synchronisables vers une plateforme distante

Nom de domaine
    porte d’accès sécurisée
    jamais emplacement logique unique des données

Mémoire
    privée par défaut

Bibliothèque commune
    alimentée uniquement par des connaissances validées

Gouvernance
    centrale, versionnée et vérifiable
```

## 1.2 Correction d’une hypothèse dangereuse

L’expression « les bureaux seront sur un nom de domaine » est utile pour visualiser le produit, mais techniquement inexacte.

Un nom de domaine ne stocke rien. Il dirige vers une plateforme.

La formulation correcte est :

```text
Le domaine donne accès à une plateforme multi-utilisateurs.
La plateforme localise, protège et synchronise les bureaux.
Chaque bureau demeure un espace isolé appartenant à un utilisateur ou à une organisation.
```

Cette distinction protège le projet contre une architecture confuse où l’interface web, la base de données, les fichiers, les moteurs et les identités seraient mélangés.

---

# 2. Vision générale

## 2.1 L’utilisateur voit une ville de bureaux

L’utilisateur peut se représenter le système ainsi :

```text
antmux.example
│
├── Mon espace
│   ├── Mes projets
│   ├── Mes travailleurs
│   ├── Mes bureaux
│   ├── Ma mémoire privée
│   └── Mes moteurs connectés
│
├── Organisation A
│   ├── Bureaux d’équipe
│   ├── Projets partagés
│   ├── Travailleurs autorisés
│   └── Bibliothèque interne
│
└── Bibliothèque Antmux
    ├── procédures validées
    ├── compétences
    ├── patrons
    ├── politiques
    └── leçons anonymisées et approuvées
```

## 2.2 Le système réel derrière l’image

```text
[Interface Web / Desktop]
          │
          ▼
[API de contrôle Antmux]
          │
    ┌─────┴──────────────┐
    ▼                    ▼
[Services distants]   [Agent local]
    │                    │
    │                    ├── moteurs CLI
    │                    ├── fichiers locaux
    │                    ├── secrets locaux
    │                    └── exécution autorisée
    │
    ├── identités
    ├── registre des bureaux
    ├── synchronisation
    ├── permissions
    ├── mémoire persistante
    ├── bibliothèque commune
    └── audit
```

---

# 3. Les six couches à ne jamais mélanger

## 3.1 Utilisateur

Une personne réelle ou un compte de service.

Il possède :

- une identité;
- des appareils;
- des permissions;
- des organisations;
- des projets;
- des bureaux;
- des préférences;
- des politiques de confidentialité;
- des quotas;
- un historique d’audit.

## 3.2 Profil de travailleur

Le profil est une identité durable spécialisée.

Exemples :

- Travailleur API REST;
- Travailleur sécurité applicative;
- Travailleur tests d’intégration;
- Travailleur mémoire d’agents.

Le profil définit :

- sa mission;
- ses compétences;
- ses responsabilités;
- ses permissions possibles;
- ses réviseurs;
- ses moteurs compatibles;
- ses critères de réussite;
- ses interdictions.

Le profil n’appartient pas nécessairement à un seul utilisateur. Il peut exister comme modèle global, puis être instancié dans plusieurs espaces privés.

## 3.3 Instance de travailleur

L’instance est la version concrète d’un profil dans un tenant.

Exemple :

```text
Profil global : worker.software.backend.rest

Instance privée de Brutus :
worker-instance.user.brutus.rest.001

Instance d’une organisation :
worker-instance.org.linuxia.rest.003
```

Deux instances du même profil ne partagent jamais automatiquement leur mémoire privée.

## 3.4 Bureau

Le bureau est l’espace persistant d’une instance de travailleur.

Il contient :

- l’identité de l’instance;
- l’état courant;
- les tâches;
- la mémoire privée;
- les décisions;
- les leçons locales;
- les incidents;
- les fichiers de travail;
- les checkpoints;
- les sorties;
- les permissions;
- les liens vers les moteurs autorisés.

## 3.5 Moteur

Le moteur est une capacité d’exécution interchangeable.

Exemples :

- OpenCode;
- Codex;
- Gemini CLI;
- Claude Code;
- Kimi Code;
- Hermes;
- modèle local;
- serveur vLLM;
- futur moteur Antmux.

Un moteur ne possède pas la mémoire durable du travailleur.

## 3.6 Bibliothèque

La bibliothèque contient ce qui peut être réutilisé sans révéler la vie privée d’un utilisateur.

Elle peut exister à trois niveaux :

```text
Bibliothèque globale Antmux
Bibliothèque d’organisation
Bibliothèque privée d’utilisateur
```

---

# 4. Modèle multi-utilisateurs

## 4.1 Le tenant

Le système doit être multi-tenant.

Un tenant est une frontière de propriété et de sécurité.

Types initiaux :

```text
USER_TENANT
ORGANIZATION_TENANT
SYSTEM_TENANT
```

### USER_TENANT

Espace privé d’un utilisateur.

### ORGANIZATION_TENANT

Espace partagé par des membres autorisés.

### SYSTEM_TENANT

Espace réservé aux composants Antmux : profils globaux, politiques, bibliothèque publique validée, schémas et gouvernance.

## 4.2 Règle d’isolation

Toute donnée doit avoir un `tenant_id` explicite.

Une donnée sans tenant est invalide, sauf les artefacts globaux explicitement classés `SYSTEM_PUBLIC`.

```yaml
tenant_id: tenant.user.brutus
owner_type: USER
visibility: PRIVATE
```

## 4.3 Niveaux de visibilité

```text
PRIVATE
PROJECT
TEAM
ORGANIZATION
SYSTEM_REVIEW
SYSTEM_PUBLIC
```

Aucune promotion vers un niveau plus large ne doit être automatique.

---

# 5. Les quatre espaces de mémoire

## 5.1 Mémoire de session

Courte durée.

Contient :

- contexte de la conversation;
- outils appelés;
- résultats temporaires;
- brouillons;
- erreurs de session;
- état de travail courant.

Elle peut être supprimée à la fin d’une session selon la politique du tenant.

## 5.2 Mémoire privée du bureau

Longue durée et isolée.

Contient :

- décisions spécifiques au projet;
- préférences utilisateur;
- incidents;
- habitudes de travail;
- leçons privées;
- données propres à l’entreprise;
- historique du travailleur;
- évaluations des moteurs dans ce contexte.

Elle ne devient jamais publique automatiquement.

## 5.3 Mémoire d’organisation

Partagée uniquement avec les membres autorisés.

Contient :

- normes internes;
- conventions;
- décisions d’architecture;
- procédures;
- schémas;
- connaissances de projet;
- leçons approuvées par l’organisation.

## 5.4 Bibliothèque commune Antmux

Contient seulement des connaissances :

- généralisables;
- nettoyées;
- non personnelles;
- non secrètes;
- validées;
- versionnées;
- accompagnées d’une provenance;
- accompagnées d’un niveau de confiance.

---

# 6. Le pipeline d’expérience

L’idée « toute l’expérience se ramasse dans les bureaux » doit être raffinée.

L’expérience brute demeure dans les bureaux privés.

La connaissance commune suit un pipeline contrôlé.

```text
Expérience brute privée
        ↓
Détection d’une leçon potentielle
        ↓
Création d’un candidat anonymisé
        ↓
Analyse des secrets et données personnelles
        ↓
Révision humaine ou par gouverneur
        ↓
Tests ou preuves
        ↓
Approbation
        ↓
Publication dans la bibliothèque appropriée
```

## 6.1 Types de leçons

```text
PRIVATE_LESSON
PROJECT_LESSON
ORG_LESSON
GLOBAL_CANDIDATE
GLOBAL_VALIDATED
GLOBAL_REJECTED
```

## 6.2 Règle absolue

```text
Les conversations, fichiers, secrets et souvenirs bruts d’un utilisateur
ne servent jamais directement à enrichir les autres utilisateurs.
```

La promotion exige :

- consentement;
- anonymisation;
- suppression des secrets;
- preuve de généralité;
- validation;
- journal d’audit.

---

# 7. Architecture local-first

## 7.1 Pourquoi commencer local

Commencer sur `D:\` permet :

- de construire sans infrastructure coûteuse;
- de comprendre le format réel des bureaux;
- de tester la persistance;
- d’éviter une plateforme multi-utilisateurs prématurée;
- de garder les secrets et le code sur la machine;
- de stabiliser les contrats avant le réseau.

## 7.2 Structure locale initiale

```text
D:\Antmux\
├── tenants\
│   └── tenant.user.brutus\
│       ├── tenant.yaml
│       ├── identity\
│       ├── projects\
│       ├── workers\
│       ├── libraries\
│       ├── audit\
│       └── sync\
│
├── engines\
│   ├── registry\
│   ├── adapters\
│   ├── launchers\
│   ├── health\
│   └── policies\
│
├── governance\
├── schemas\
├── runtime\
└── backups\
```

## 7.3 Bureau local canonique

```text
D:\Antmux\tenants\tenant.user.brutus\workers\011-api-rest\
├── worker.yaml
├── instance.yaml
├── STATE.md
├── permissions.yaml
├── engine-policy.yaml
├── sync-policy.yaml
├── memory\
│   ├── decisions.jsonl
│   ├── lessons.jsonl
│   ├── incidents.jsonl
│   ├── preferences.json
│   └── index.json
├── jobs\
├── inbox\
├── outbox\
├── workspace\
├── checkpoints\
├── artifacts\
└── logs\
```

---

# 8. Évolution vers les bureaux distants

## 8.1 Principe de migration

La transition ne doit pas transformer le bureau en une nouvelle chose.

Le même identifiant de bureau doit survivre :

```text
Local seulement
→ local + sauvegarde distante
→ local + synchronisation bidirectionnelle
→ bureau principal distant + cache local
→ bureau accessible sur plusieurs appareils
```

## 8.2 Modes de fonctionnement

### MODE_LOCAL_ONLY

- aucune donnée de bureau ne quitte la machine;
- moteurs locaux ou API externes selon politique;
- sauvegardes locales seulement.

### MODE_LOCAL_BACKUP

- bureau principal local;
- sauvegarde distante chiffrée;
- pas d’édition distante.

### MODE_SYNC_HYBRID

- bureau local utilisable hors ligne;
- synchronisation bidirectionnelle;
- résolution de conflits;
- journal d’événements.

### MODE_CLOUD_PRIMARY

- bureau principal distant;
- cache local;
- accès multi-appareils;
- moteurs locaux connectés par agent.

### MODE_ORGANIZATION_MANAGED

- politiques imposées par l’organisation;
- résidence des données;
- rétention;
- audit;
- moteurs autorisés;
- bibliothèque interne.

---

# 9. Architecture de contrôle et d’exécution

## 9.1 Plan de contrôle distant

Le plan de contrôle gère :

- authentification;
- utilisateurs;
- organisations;
- abonnements;
- registres des profils;
- registres des bureaux;
- permissions;
- politiques;
- tâches;
- synchronisation;
- audit;
- métadonnées des moteurs;
- notifications.

Il ne doit pas exécuter automatiquement des commandes sur les machines.

## 9.2 Plan d’exécution local

Un composant nommé provisoirement `Antmux Local Agent` fonctionne sur la machine de l’utilisateur.

Il peut :

- détecter les moteurs installés;
- lancer un moteur autorisé;
- transmettre une tâche;
- lire les chemins autorisés;
- écrire dans le workspace autorisé;
- recueillir les résultats;
- produire des preuves;
- synchroniser les événements;
- fonctionner hors ligne;
- refuser toute commande invalide.

## 9.3 Flux d’une tâche

```text
Utilisateur
   ↓
Interface Antmux
   ↓
Création du JOB
   ↓
Autorisation
   ↓
Sélection du profil
   ↓
Sélection de l’instance de travailleur
   ↓
Sélection du moteur
   ↓
Envoi au Local Agent ou moteur distant
   ↓
Exécution isolée
   ↓
Preuves et résultats
   ↓
Révision
   ↓
Commit de mémoire
   ↓
Synchronisation
```

---

# 10. Identité et authentification

## 10.1 Identités humaines

Support futur :

- courriel et mot de passe;
- passkeys;
- fournisseurs OAuth;
- SSO d’entreprise;
- authentification multifacteur.

## 10.2 Identités machines

Chaque appareil possède :

```yaml
device_id:
user_id:
public_key:
status:
last_seen_at:
capabilities:
attestation_level:
```

## 10.3 Identités des travailleurs

Un travailleur ne se connecte pas comme un humain.

Il agit avec :

- une identité de service;
- un tenant;
- un bureau;
- une tâche;
- une permission temporaire;
- un moteur affecté;
- une durée de validité.

## 10.4 Jetons à portée limitée

Ne jamais donner au moteur un jeton général du compte.

Créer des capacités temporaires :

```text
Lire ce dossier
Écrire dans ce workspace
Accéder à cette tâche
Pendant 20 minutes
Sans accès aux autres bureaux
```

---

# 11. Modèle de permissions

## 11.1 Combinaison RBAC + ABAC

RBAC : rôle de l’acteur.

ABAC : contexte de l’action.

Exemple :

```yaml
actor_role: WORKER_INSTANCE
actor_id: worker-instance.user.brutus.rest.001
action: WRITE
resource: project.api.workspace
conditions:
  job_id: job-2026-000001
  path_prefix: /workspace/api/
  expires_at: 2026-07-27T22:00:00-04:00
  reviewer_required: true
```

## 11.2 Permission minimale

Le profil définit le maximum possible.

Le tenant réduit ce maximum.

Le projet réduit encore.

Le JOB accorde uniquement le nécessaire.

```text
Permissions effectives
=
intersection(
profil,
tenant,
organisation,
projet,
job,
appareil,
contexte
)
```

## 11.3 Actions sensibles

Toujours soumises à confirmation ou politique forte :

- suppression;
- changement de permissions;
- publication;
- déploiement;
- dépenses;
- accès aux secrets;
- exécution administrative;
- synchronisation globale;
- promotion d’une leçon vers la bibliothèque commune.

---

# 12. Secrets

## 12.1 Règles

Les secrets :

- ne vont pas dans GitHub;
- ne vont pas dans les logs;
- ne vont pas dans la mémoire du travailleur;
- ne vont pas dans les prompts sauf nécessité explicite;
- ne sont jamais synchronisés en clair;
- ne sont jamais transmis à un moteur non autorisé.

## 12.2 Stockage local

Utiliser le coffre du système :

- Windows Credential Manager;
- DPAPI;
- futur coffre Antmux;
- gestionnaire de secrets d’organisation.

## 12.3 Références de secrets

Le bureau stocke une référence :

```yaml
secret_ref: secret://tenant.user.brutus/openrouter/default
```

Pas la valeur.

---

# 13. Synchronisation

## 13.1 Principe event-sourced léger

Ne pas synchroniser seulement des fichiers entiers.

Conserver un journal d’événements :

```json
{
  "event_id": "evt-...",
  "tenant_id": "tenant.user.brutus",
  "office_id": "office-...",
  "device_id": "device-...",
  "sequence": 142,
  "type": "MEMORY_DECISION_ADDED",
  "created_at": "...",
  "payload_hash": "..."
}
```

## 13.2 Avantages

- audit;
- reprise;
- synchronisation incrémentale;
- résolution de conflits;
- preuve de provenance;
- reconstruction de l’état;
- réplication sélective.

## 13.3 Conflits

Catégories :

```text
NO_CONFLICT
AUTO_MERGE
USER_REVIEW
ADMIN_REVIEW
REJECT_REMOTE
REJECT_LOCAL
```

Les décisions et permissions ne doivent pas être fusionnées automatiquement par simple concaténation.

## 13.4 Mode hors ligne

Le Local Agent doit pouvoir :

- créer des JOB locaux;
- exécuter des moteurs locaux;
- écrire dans le journal local;
- marquer les événements `PENDING_SYNC`;
- resynchroniser plus tard;
- détecter les conflits.

---

# 14. Stockage distant

## 14.1 Séparer les catégories de données

### Base relationnelle

Pour :

- utilisateurs;
- tenants;
- organisations;
- permissions;
- registres;
- tâches;
- états;
- audit indexé;
- abonnements;
- métadonnées.

### Stockage objet

Pour :

- artefacts;
- pièces jointes;
- snapshots;
- checkpoints volumineux;
- exports;
- sauvegardes chiffrées.

### Recherche

Pour :

- index textuel;
- index sémantique;
- bibliothèque;
- mémoire autorisée.

### File de messages

Pour :

- tâches asynchrones;
- synchronisation;
- indexation;
- notifications;
- révision;
- promotion de leçons.

## 14.2 Chiffrement

- TLS en transit;
- chiffrement au repos;
- clés séparées par environnement;
- possibilité future de clés par tenant;
- chiffrement côté client pour le mode privé renforcé;
- rotation de clés;
- journal des accès.

---

# 15. Noms de domaine et routage

## 15.1 Domaine principal

Exemple conceptuel :

```text
app.antmux.example
api.antmux.example
sync.antmux.example
status.antmux.example
```

## 15.2 Organisations

Deux options :

```text
app.antmux.example/org/linuxia
```

ou plus tard :

```text
linuxia.antmux.example
```

## 15.3 Bureaux

Ne pas exposer les identifiants sensibles dans les URL.

Utiliser :

```text
app.antmux.example/workspaces/{opaque_id}
```

Pas :

```text
app.antmux.example/brutus/private-secret-project/api-worker
```

---

# 16. Modèle de données minimal

## 16.1 Tenant

```yaml
schema_version: antmux.tenant.v1
id: tenant.user.brutus
type: USER
owner_id: user.brutus
status: ACTIVE
data_policy:
  default_visibility: PRIVATE
  allow_global_learning: false
  retention_days: null
```

## 16.2 Office

```yaml
schema_version: antmux.office.v1
id: office-01J...
tenant_id: tenant.user.brutus
worker_instance_id: worker-instance.user.brutus.rest.001
project_id: project.antmux
name: Bureau API REST
storage_mode: LOCAL_ONLY
primary_device_id: device-brutus-main
sync_status: DISABLED
```

## 16.3 Worker instance

```yaml
schema_version: antmux.worker-instance.v1
id: worker-instance.user.brutus.rest.001
tenant_id: tenant.user.brutus
profile_id: worker.software.backend.rest
status: DORMANT
memory_scope: PRIVATE
reviewers:
  - worker.software.testing.integration
  - worker.software.security.review
```

## 16.4 Job

```yaml
schema_version: antmux.job.v1
id: job-2026-000001
tenant_id: tenant.user.brutus
office_id: office-01J...
worker_instance_id: worker-instance.user.brutus.rest.001
requested_by: user.brutus
engine_id: opencode
status: AUTHORIZED
permissions:
  read_paths:
    - D:\projects\antmux
  write_paths:
    - D:\projects\antmux\workspace
review_required: true
```

## 16.5 Knowledge item

```yaml
schema_version: antmux.knowledge-item.v1
id: knowledge-01J...
source_scope: PRIVATE
current_scope: SYSTEM_REVIEW
source_tenant_id: tenant.user.brutus
content_classification: NON_PERSONAL
secret_scan: PASS
provenance:
  source_events:
    - evt-...
validation:
  tests: PASS
  reviewers:
    - reviewer.security
    - reviewer.architecture
status: CANDIDATE
```

---

# 17. Gouvernance

## 17.1 Gouverneur séparé

Le gouverneur ne choisit pas seulement le moteur.

Il vérifie :

- autorisation;
- confidentialité;
- portée;
- coûts;
- politiques;
- risques;
- preuves;
- conflits;
- promotion de mémoire;
- publication.

## 17.2 Règles constitutionnelles

```text
1. Un utilisateur possède ses données.
2. La mémoire privée reste privée par défaut.
3. Aucune expérience brute n’est mutualisée automatiquement.
4. Le moteur ne possède pas le travailleur.
5. Le domaine n’est pas une frontière de confiance suffisante.
6. Toute action sensible exige une autorisation vérifiable.
7. Toute connaissance commune exige une provenance.
8. Toute permission est minimale, temporaire et révocable.
9. Toute synchronisation doit être traçable.
10. Tout utilisateur doit pouvoir exporter et supprimer ses données.
```

---

# 18. Propriété, export et suppression

Chaque utilisateur doit pouvoir :

- voir les données détenues;
- exporter ses bureaux;
- télécharger son historique;
- révoquer un appareil;
- désactiver la synchronisation;
- supprimer un projet;
- supprimer son compte;
- demander la suppression des sauvegardes selon la politique;
- retirer une leçon encore privée;
- voir si une connaissance a été proposée à une bibliothèque plus large.

Une connaissance déjà généralisée et publiée ne doit pas conserver de lien personnel inutile vers son auteur.

---

# 19. Observabilité et audit

## 19.1 Logs techniques

Contiennent :

- démarrages;
- erreurs;
- latence;
- santé des moteurs;
- synchronisation;
- consommation;
- événements système.

Ils ne contiennent pas les secrets ni le contenu brut par défaut.

## 19.2 Audit de sécurité

Contient :

- qui;
- quoi;
- quand;
- sur quelle ressource;
- avec quelle permission;
- depuis quel appareil;
- résultat;
- justification;
- preuve.

## 19.3 Audit utilisateur

L’utilisateur doit pouvoir consulter :

- les moteurs utilisés;
- les données transmises;
- les outils appelés;
- les fichiers touchés;
- les permissions accordées;
- les connaissances proposées au partage.

---

# 20. Menaces principales

## 20.1 Fuite entre tenants

Risque : un utilisateur lit les données d’un autre.

Protection :

- tenant obligatoire;
- filtres au niveau données;
- tests d’isolation;
- permissions explicites;
- chiffrement;
- audit.

## 20.2 Moteur compromis

Risque : un moteur tente d’accéder à d’autres fichiers.

Protection :

- sandbox;
- chemins autorisés;
- jetons temporaires;
- Local Agent comme médiateur;
- absence de secrets dans le prompt;
- journal d’actions.

## 20.3 Prompt injection

Risque : un document externe commande le travailleur.

Protection :

- contenu externe classé `UNTRUSTED_DATA`;
- séparation instructions/données;
- validation des tool calls;
- interdiction de modifier les politiques depuis le contenu;
- réviseur.

## 20.4 Empoisonnement de la bibliothèque

Risque : une mauvaise leçon devient commune.

Protection :

- candidats isolés;
- provenance;
- tests;
- plusieurs réviseurs;
- rollback;
- réputation de source;
- versionnement.

## 20.5 Vol d’appareil

Protection :

- chiffrement disque;
- révocation distante;
- clés locales protégées;
- sessions courtes;
- MFA;
- sauvegarde chiffrée.

## 20.6 Abus d’un administrateur

Protection :

- séparation des rôles;
- double validation;
- journaux append-only;
- accès justifié;
- alertes;
- portée minimale.

---

# 21. Expérience utilisateur cible

## 21.1 Première connexion

L’utilisateur :

1. crée son compte;
2. crée son tenant privé;
3. installe le Local Agent;
4. associe son appareil;
5. détecte ses moteurs;
6. choisit son mode de stockage;
7. crée son premier projet;
8. instancie son premier travailleur;
9. ouvre son bureau;
10. lance un premier JOB.

## 21.2 Vue d’un bureau

Afficher :

- identité du travailleur;
- mission;
- moteur actuel;
- statut;
- tâche en cours;
- permissions actives;
- preuves;
- mémoire récente;
- décisions;
- réviseur;
- synchronisation;
- prochaine action.

## 21.3 Vue « ville »

Afficher :

- bureaux dormants;
- bureaux actifs;
- moteurs disponibles;
- tâches;
- blocages;
- revues;
- alertes;
- bibliothèque;
- état de synchronisation.

L’animation doit représenter des événements réels.

---

# 22. Architecture de déploiement progressive

## Phase 0 — Contrats avant code

Produire et valider :

- schéma tenant;
- schéma worker profile;
- schéma worker instance;
- schéma office;
- schéma job;
- schéma event;
- schéma permissions;
- schéma knowledge item;
- états officiels;
- règles de gouvernance.

Critère de sortie : les objets ont une identité stable et ne dépendent pas d’une technologie particulière.

## Phase 1 — Premier building local

Créer un seul tenant local :

```text
tenant.user.brutus
```

Créer un seul profil canonique.

Créer une seule instance.

Créer un seul bureau.

Connecter un seul moteur.

Exécuter un JOB en lecture seule.

Critères :

- état persistant;
- permissions vérifiées;
- logs;
- preuves;
- reprise après redémarrage;
- aucun accès hors périmètre.

## Phase 2 — Écriture contrôlée

Autoriser l’écriture dans un workspace isolé.

Ajouter :

- diff;
- checkpoint;
- rollback;
- réviseur;
- validation avant intégration.

## Phase 3 — Plusieurs moteurs

Ajouter trois moteurs maximum.

Mesurer :

- qualité;
- coût;
- temps;
- taux d’erreur;
- respect des permissions;
- réussite des tests.

Ne pas créer 33 moteurs avant que le registre et les métriques soient stables.

## Phase 4 — Plusieurs travailleurs locaux

Créer trois profils pilotes :

- constructeur;
- réviseur;
- gouverneur.

Puis douze instances pilotes maximum.

Valider les communications sans mémoire croisée illégitime.

## Phase 5 — Sauvegarde distante chiffrée

Ajouter :

- compte utilisateur;
- appareil;
- authentification;
- upload de snapshot chiffré;
- restauration;
- révocation.

Pas encore de synchronisation bidirectionnelle.

## Phase 6 — Synchronisation événementielle

Ajouter :

- journal d’événements;
- curseurs;
- reprise;
- conflits;
- mode hors ligne;
- test de deux appareils.

## Phase 7 — Interface par nom de domaine

Déployer :

- interface web;
- API;
- authentification;
- registre des bureaux;
- vue de synchronisation.

Les moteurs restent locaux par défaut.

## Phase 8 — Deuxième utilisateur

Créer un second tenant réel de test.

Tests obligatoires :

- aucune lecture croisée;
- aucun moteur croisé;
- aucun secret croisé;
- export séparé;
- suppression séparée;
- audit séparé.

## Phase 9 — Organisation pilote

Ajouter :

- invitations;
- rôles;
- projets partagés;
- bibliothèque d’organisation;
- révocation d’un membre;
- transfert de propriété.

## Phase 10 — Pipeline de connaissances

Ajouter :

- extraction de candidats;
- anonymisation;
- secret scan;
- validation;
- provenance;
- publication;
- rollback.

## Phase 11 — Échelle contrôlée

Ajouter progressivement :

- plus de profils;
- plus de moteurs;
- files de tâches;
- quotas;
- coûts;
- observabilité;
- haute disponibilité.

## Phase 12 — Plateforme publique

Seulement après :

- test de pénétration;
- conformité;
- sauvegardes vérifiées;
- restauration testée;
- gestion d’incidents;
- conditions d’utilisation;
- politique de confidentialité;
- suppression réelle;
- support.

---

# 23. Premier building recommandé

Le premier building ne doit pas être « le cloud Antmux ».

Il doit être :

```text
Un tenant local
+ un profil canonique
+ une instance de travailleur
+ un bureau persistant
+ un moteur
+ un JOB
+ un réviseur
+ un journal de preuves
```

## 23.1 Démonstration minimale

Scénario :

1. Brutus ouvre Antmux;
2. le tenant local est chargé;
3. le bureau du travailleur apparaît;
4. le moteur est détecté;
5. Brutus demande une inspection en lecture seule;
6. un JOB est créé;
7. le gouverneur vérifie la permission;
8. le moteur exécute;
9. le résultat et les preuves sont enregistrés;
10. le réviseur confirme ou rejette;
11. l’état du bureau est mis à jour;
12. l’application redémarre;
13. le bureau reprend exactement au bon état.

Si ce scénario ne fonctionne pas parfaitement, le domaine ne doit pas encore être construit.

---

# 24. Décisions à ne pas prendre trop tôt

Ne pas choisir définitivement maintenant :

- le fournisseur cloud;
- la base de données finale;
- Kubernetes;
- microservices complets;
- blockchain;
- vector database globale;
- chiffrement de bout en bout universel;
- marketplace;
- facturation complexe;
- 108 bureaux créés d’un coup;
- 33 moteurs installés d’un coup;
- entraînement collectif sur les données utilisateurs.

Les contrats doivent survivre à ces choix.

---

# 25. Indicateurs de réussite

## 25.1 Sécurité

- zéro fuite entre tenants;
- zéro secret dans les logs;
- 100 % des actions sensibles auditées;
- permissions refusées correctement;
- révocation d’appareil fonctionnelle.

## 25.2 Fiabilité

- reprise après interruption;
- synchronisation idempotente;
- aucun JOB perdu;
- rollback vérifié;
- restauration de sauvegarde testée.

## 25.3 Qualité des travailleurs

- taux de tâches réussies;
- taux de revue acceptée;
- taux d’hallucination détecté;
- preuves suffisantes;
- respect du périmètre;
- coût moyen;
- latence;
- progression par version.

## 25.4 Connaissance commune

- nombre de candidats;
- taux de rejet;
- provenance complète;
- absence de données privées;
- utilité mesurée;
- possibilité de rollback.

---

# 26. Anti-objectifs

Antmux ne doit pas devenir :

- un disque réseau géant sans isolation;
- une mémoire collective brute;
- un système qui entraîne ses modèles sur tout le monde par défaut;
- un panneau web contrôlant librement les ordinateurs;
- un moteur unique déguisé en travailleurs;
- un système où les administrateurs voient tout;
- un système où un prompt peut modifier les permissions;
- un système où la bibliothèque absorbe automatiquement les conversations;
- un système impossible à quitter;
- une démonstration spectaculaire sans preuves.

---

# 27. Questions critiques à faire analyser par d’autres IA

Le document peut être transmis intégralement à deux ou trois IA différentes avec la demande suivante.

## Mandat de révision

```text
Tu es réviseur d’architecture senior.

Analyse ce document comme s’il devait devenir une plateforme multi-utilisateurs réelle.

Ne cherche pas à être agréable.

1. Identifie les hypothèses fausses ou fragiles.
2. Identifie les risques de sécurité et de confidentialité.
3. Identifie les éléments impossibles ou trop coûteux.
4. Identifie les frontières de services manquantes.
5. Vérifie si le modèle local-first peut réellement évoluer vers le cloud.
6. Vérifie l’isolation multi-tenant.
7. Vérifie la gestion de mémoire privée et commune.
8. Vérifie la synchronisation hors ligne.
9. Vérifie la propriété, l’export et la suppression des données.
10. Propose un premier building plus petit si celui-ci reste trop large.
11. Classe les problèmes : CRITIQUE, MAJEUR, MOYEN, MINEUR.
12. Pour chaque critique, fournis une correction concrète.
13. Termine par un verdict GO, GO AVEC CONDITIONS ou NO-GO.

Ne réécris pas le document en entier.
Produis un rapport de revue falsifiable et orienté construction.
```

## Questions spécialisées

### IA 1 — Architecture distribuée

```text
Le découpage plan de contrôle distant / agent local est-il correct?
Quels contrats d’API et événements sont indispensables?
Quelles parties doivent rester monolithiques au début?
```

### IA 2 — Sécurité et confidentialité

```text
Comment empêcher une fuite entre tenants?
Comment protéger les secrets face aux moteurs?
Quels abus du Local Agent faut-il anticiper?
La promotion des connaissances est-elle suffisamment sûre?
```

### IA 3 — Produit et exécution

```text
Le premier building est-il assez petit?
Quelle démonstration prouverait une vraie valeur utilisateur?
Quelles fonctions doivent être supprimées des six premiers mois?
```

---

# 28. Points à challenger explicitement

Les autres IA doivent tenter de réfuter ces hypothèses :

1. Les moteurs peuvent rester majoritairement locaux.
2. Les bureaux peuvent migrer du local vers le distant sans changer d’identité.
3. Une synchronisation événementielle est préférable à une simple copie de dossiers.
4. Une bibliothèque commune peut être alimentée sans aspirer la vie privée.
5. Un système multi-tenant peut rester compréhensible pour un petit projet.
6. Le premier building peut être construit sans choisir tout le cloud.
7. Trois profils pilotes suffisent pour valider la colonie.
8. Le Local Agent peut être sécurisé suffisamment pour un usage public.
9. Les organisations peuvent partager des bureaux sans mélanger les mémoires privées.
10. Le système peut offrir une expérience fluide même avec des moteurs locaux parfois hors ligne.

---

# 29. Verdict directeur

La vision est réalisable, mais seulement si une séparation stricte est maintenue entre :

```text
identité humaine
profil de travailleur
instance de travailleur
bureau
moteur
projet
tenant
mémoire
bibliothèque
gouvernance
```

La plus grande erreur serait de créer immédiatement un site web où tous les bureaux sont stockés ensemble et où tous les moteurs peuvent les consulter.

La bonne direction est :

```text
Local-first
→ identité stable
→ bureau canonique
→ permissions minimales
→ preuves
→ sauvegarde distante
→ synchronisation
→ deuxième utilisateur
→ organisation
→ bibliothèque commune validée
→ échelle
```

Le premier objectif n’est pas d’être « plus grand que tout le monde ».

Le premier objectif est de posséder une fondation que les autres systèmes n’ont pas :

- des travailleurs persistants;
- des moteurs interchangeables;
- une mémoire compartimentée;
- une expérience partageable sans vol de données;
- une gouvernance vérifiable;
- une migration du local vers le réseau sans reconstruction totale.

---

# 30. Prochaine étape unique

```text
Créer le contrat officiel du premier building local :

1 tenant
1 profil
1 instance
1 bureau
1 moteur
1 JOB
1 réviseur
1 journal de preuves
```

Aucun domaine public ne doit être construit avant que ce cycle fonctionne de bout en bout, survive à un redémarrage et refuse correctement une action non autorisée.
