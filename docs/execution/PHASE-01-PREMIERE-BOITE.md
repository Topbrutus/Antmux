# Antmux — Phase 1 : Première boîte

## 0. But de cette phase

Construire le tout premier circuit fonctionnel d’Antmux sans encore connecter les orchestrateurs Grok, Codex, les travailleurs, Obsidian ou la macro couleur.

La Phase 1 doit seulement permettre de :

1. recevoir une demande;
2. lui attribuer un numéro permanent;
3. créer une fiche de job;
4. placer cette fiche dans une queue persistante;
5. permettre au Libraire de la réclamer;
6. conserver une trace minimale;
7. effectuer un test complet sans exécuter la job elle-même.

> **Principe :** la première boîte organise le travail; elle ne réalise pas encore le travail.

---

## 1. Résultat attendu

À la fin de cette phase, la commande ou le mécanisme d’entrée doit pouvoir prendre un texte comme :

```text
Copier le fichier A vers le dossier B.
```

et produire :

```text
JOB-000001
```

avec une fiche persistante, placée dans la queue, puis réclamée par le Libraire.

Aucun orchestrateur ni travailleur ne doit encore être lancé.

---

## 2. Limites de la phase

### Inclus

- arborescence du pipeline;
- compteur de jobs;
- identifiant `JOB-xxxxxx`;
- modèle de fiche;
- queue `pending`;
- état `claimed`;
- journal minimal;
- simulation du Libraire;
- test manuel;
- critères d’acceptation.

### Exclu

- recherche Obsidian réelle;
- notation 1 à 9 automatisée;
- choix Codex ou Grok;
- lancement d’orchestrateurs;
- lancement de travailleurs;
- surveillance Jules toutes les minutes;
- publication automatique GitHub;
- interprétation des couleurs;
- instructions futures;
- exécution réelle de la tâche contenue dans la job.

---

## 3. Arborescence à créer

```text
D:\pipeline\
├─ inbox\
├─ queue\
│  ├─ pending\
│  ├─ claimed\
│  ├─ running\
│  ├─ blocked\
│  └─ completed\
├─ jobs\
├─ events\
├─ state\
├─ templates\
└─ problematic\
```

Créer également :

```text
D:\communication\inbox-chatgpt\
```

Ce deuxième dossier ne sera pas surveillé automatiquement dans la Phase 1; il est seulement préparé.

---

## 4. Fichiers de base à prévoir

```text
D:\pipeline\state\next-job.json
D:\pipeline\state\pipeline-state.json
D:\pipeline\templates\job-template.json
D:\pipeline\templates\event-template.json
D:\pipeline\README.md
```

Scripts prévus pour l’implémentation :

```text
D:\pipeline\New-AntmuxJob.ps1
D:\pipeline\Claim-AntmuxJob.ps1
D:\pipeline\Get-AntmuxQueue.ps1
D:\pipeline\Test-AntmuxPhase1.ps1
```

Les noms peuvent évoluer avant codage, mais les responsabilités doivent rester séparées.

---

## 5. Format du compteur

Fichier :

```text
D:\pipeline\state\next-job.json
```

Contenu initial :

```json
{
  "next_number": 1,
  "updated_at": null
}
```

### Règles

1. Le compteur commence à `1`.
2. Le format visible est toujours sur six chiffres.
3. Le numéro ne doit jamais être réutilisé.
4. Une création incomplète doit être détectable.
5. L’écriture du compteur doit être atomique.
6. Deux créations simultanées ne doivent pas recevoir le même numéro.

---

## 6. Format d’une fiche de job

Exemple :

```json
{
  "job_id": "JOB-000001",
  "title": "Copier un fichier",
  "original_request": "Copier le fichier A vers le dossier B.",
  "source": "brutus-terminal",
  "created_at": "2026-07-15T03:44:04-04:00",
  "updated_at": "2026-07-15T03:44:04-04:00",
  "status": "QUEUED",
  "owner": null,
  "project": null,
  "category": null,
  "difficulty_level": null,
  "family": null,
  "memory_links": [],
  "target_files": [],
  "risks": [],
  "notes": [],
  "next_action": "LIBRARY_REVIEW"
}
```

### Règles

- Le texte original doit rester intact.
- Les champs inconnus restent `null` ou vides.
- La Phase 1 ne doit pas deviner le niveau.
- La Phase 1 ne doit pas choisir Codex ou Grok.
- Le Libraire remplira ces champs dans une phase ultérieure.

---

## 7. Emplacements d’une job

### Fiche canonique

```text
D:\pipeline\jobs\JOB-000001.json
```

### Ticket dans la queue

```text
D:\pipeline\queue\pending\JOB-000001.queue.json
```

### Journal d’événements

```text
D:\pipeline\events\JOB-000001.jsonl
```

La fiche canonique est la vérité principale. Le ticket de queue sert uniquement à l’aiguillage.

---

## 8. Format du ticket de queue

```json
{
  "job_id": "JOB-000001",
  "status": "QUEUED",
  "queued_at": "2026-07-15T03:44:04-04:00",
  "priority": "normal",
  "requested_stage": "LIBRARY_REVIEW"
}
```

Le ticket ne doit pas recopier toute la demande. Il pointe vers la fiche canonique.

---

## 9. Format du journal d’événements

Chaque ligne du fichier JSONL représente un événement.

Exemple :

```json
{"timestamp":"2026-07-15T03:44:04-04:00","job_id":"JOB-000001","actor":"intake","event":"job_created","status":"QUEUED","details":"Job créée depuis brutus-terminal."}
{"timestamp":"2026-07-15T03:45:10-04:00","job_id":"JOB-000001","actor":"librarian","event":"job_claimed","status":"LIBRARY_REVIEW","details":"Job réclamée pour analyse mémoire."}
```

### Règles

- ajouter une ligne, ne pas réécrire tout l’historique;
- inclure l’horodatage;
- inclure l’acteur;
- inclure l’événement;
- inclure le nouvel état;
- rester lisible par un futur agent.

---

## 10. Étapes d’exécution

### Étape 1 — Vérifier le disque

Vérifier :

- que `D:\` existe;
- que le volume porte le nom `Antmux`;
- que `D:\` n’est pas le disque système;
- que le dossier racine est accessible en écriture.

**Arrêt obligatoire** si une vérification échoue.

### Étape 2 — Créer l’arborescence

Créer tous les répertoires de la section 3.

Vérifier chaque chemin après création.

### Étape 3 — Créer les fichiers d’état

Créer :

- `next-job.json`;
- `pipeline-state.json`.

Le fichier `pipeline-state.json` peut commencer ainsi :

```json
{
  "phase": 1,
  "status": "INITIALIZED",
  "active_codex_orchestrators": 0,
  "active_grok_orchestrators": 0,
  "updated_at": null
}
```

Les compteurs d’orchestrateurs restent à zéro pendant toute la Phase 1.

### Étape 4 — Créer le modèle de job

Créer `job-template.json` avec tous les champs prévus.

Valider que le JSON est lisible.

### Étape 5 — Créer le modèle d’événement

Créer `event-template.json`.

Exemple :

```json
{
  "timestamp": null,
  "job_id": null,
  "actor": null,
  "event": null,
  "status": null,
  "details": null
}
```

### Étape 6 — Construire le générateur de numéro

Le générateur doit :

1. lire `next_number`;
2. verrouiller le compteur;
3. produire `JOB-xxxxxx`;
4. augmenter le compteur;
5. écrire le nouveau compteur de manière atomique;
6. libérer le verrou.

### Étape 7 — Construire la création de job

`New-AntmuxJob.ps1` doit recevoir au minimum :

- le texte de la demande;
- la source;
- un titre facultatif.

Il doit créer :

- la fiche canonique;
- le ticket de queue;
- le premier événement.

### Étape 8 — Refuser les entrées vides

Le script doit refuser :

- un texte vide;
- un texte composé seulement d’espaces;
- une source vide;
- un identifiant déjà existant.

### Étape 9 — Préserver le texte original

Le texte d’entrée ne doit pas être résumé ni corrigé dans `original_request`.

Une version reformulée pourra être ajoutée plus tard dans un autre champ.

### Étape 10 — Afficher la confirmation

Après création, afficher seulement les informations essentielles :

```text
JOB CRÉÉE : JOB-000001
STATUT     : QUEUED
PROCHAINE  : LIBRARY_REVIEW
```

### Étape 11 — Construire la lecture de queue

`Get-AntmuxQueue.ps1` doit lister les tickets `pending` dans l’ordre de création.

Affichage minimal :

```text
JOB-000001 | normal | LIBRARY_REVIEW
JOB-000002 | normal | LIBRARY_REVIEW
```

### Étape 12 — Construire la réclamation par le Libraire

`Claim-AntmuxJob.ps1` doit :

1. prendre la plus ancienne job `pending`;
2. créer un verrou;
3. déplacer son ticket vers `claimed`;
4. mettre la fiche canonique à jour;
5. définir `owner: librarian`;
6. définir `status: LIBRARY_REVIEW`;
7. ajouter l’événement `job_claimed`;
8. libérer le verrou.

### Étape 13 — Interdire la double réclamation

Deux appels simultanés ne doivent jamais réclamer la même job.

Un second appel doit prendre la job suivante ou annoncer qu’aucune job n’est disponible.

### Étape 14 — Ne pas exécuter la demande

La réclamation du Libraire s’arrête après le changement d’état.

Dans la Phase 1 :

- aucun fichier cible n’est copié;
- aucune commande métier n’est lancée;
- aucune famille n’est choisie;
- aucun niveau n’est attribué.

### Étape 15 — Créer le test de bout en bout

`Test-AntmuxPhase1.ps1` doit :

1. créer une demande de test;
2. confirmer le numéro;
3. confirmer la fiche canonique;
4. confirmer le ticket `pending`;
5. confirmer le premier événement;
6. réclamer la job comme Libraire;
7. confirmer le déplacement vers `claimed`;
8. confirmer le changement de propriétaire;
9. confirmer le nouvel événement;
10. confirmer qu’aucune exécution métier n’a eu lieu.

### Étape 16 — Tester trois jobs consécutives

Créer trois jobs et vérifier :

```text
JOB-000001
JOB-000002
JOB-000003
```

Elles doivent conserver l’ordre de la queue.

### Étape 17 — Tester une reprise

Fermer PowerShell, le rouvrir, puis vérifier :

- que le compteur n’est pas revenu à 1;
- que les jobs sont toujours visibles;
- que les événements sont toujours présents;
- que la prochaine job reçoit le prochain numéro.

### Étape 18 — Produire le rapport de phase

Créer :

```text
D:\pipeline\PHASE-01-RESULTAT.md
```

Le rapport doit indiquer :

- dossiers créés;
- fichiers créés;
- tests exécutés;
- résultats;
- anomalies;
- niveau de confiance;
- prochaine action unique.

---

## 11. Critères d’acceptation

La Phase 1 est acceptée seulement si :

- [ ] le disque Antmux est validé;
- [ ] l’arborescence existe;
- [ ] le compteur persiste;
- [ ] les numéros ne se répètent pas;
- [ ] une job vide est refusée;
- [ ] le texte original est conservé;
- [ ] la fiche canonique est créée;
- [ ] le ticket de queue est créé;
- [ ] le journal JSONL est créé;
- [ ] la queue respecte l’ordre;
- [ ] le Libraire peut réclamer une job;
- [ ] une job ne peut pas être réclamée deux fois;
- [ ] aucun orchestrateur n’est lancé;
- [ ] aucune tâche métier n’est exécutée;
- [ ] un redémarrage ne fait perdre aucun état;
- [ ] le rapport de phase existe.

---

## 12. Test manuel de référence

Demande de test :

```text
Copier plus tard le fichier D:\exemple-source.txt vers D:\exemple-destination.txt.
```

Résultat attendu de la Phase 1 :

```text
JOB-000001 créée et placée dans pending.
```

Puis :

```text
JOB-000001 réclamée par librarian et placée dans claimed.
```

Résultat interdit dans cette phase :

```text
Le fichier a été copié.
```

La copie réelle appartient à une phase ultérieure.

---

## 13. Sortie vers la Phase 2

Quand la Phase 1 est validée, la Phase 2 pourra commencer avec une seule responsabilité nouvelle :

> Le Libraire lit la job réclamée, consulte la mémoire Obsidian et attache les souvenirs pertinents.

La Phase 2 ne doit être ouverte qu’après validation complète de la checklist de la Phase 1.

---

## 14. Prochaine action unique

Créer le script d’installation de la Phase 1 qui met en place l’arborescence et les fichiers de base, sans encore créer les scripts métier de numérotation et de queue.
