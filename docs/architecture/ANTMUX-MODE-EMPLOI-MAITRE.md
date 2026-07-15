# Antmux — Mode d’emploi maître

## 0. Statut du document

- **Type :** spécification d’architecture et mode d’emploi directeur
- **Autorité :** décisions dictées par Brutus
- **État :** version initiale consolidée
- **But :** réunir dans un seul document la vision complète d’Antmux avant de passer à l’exécution par phases
- **Règle de lecture :** ce document décrit le système cible; les documents de phase décrivent comment le construire réellement

### Légende

- **ACTÉ** : décision confirmée par Brutus
- **PROVISOIRE** : valeur de départ qui pourra évoluer
- **FUTUR** : idée conservée, mais non activée dans la première construction

---

## 1. Principe général

Antmux est un système de travail à agents construit autour d’une interface centrale appelée **Reine-Linuxia**.

Brutus écrit directement à Reine-Linuxia. Elle reçoit la demande, décide si elle l’exécute elle-même ou si elle la délègue, surveille le travail, vérifie le résultat et revient présenter la réponse finale.

Antmux ne doit pas être une foule d’agents qui parlent tous à Brutus. Il doit ressembler à une organisation claire :

```text
Brutus
  ↓
Reine-Linuxia
  ↓
Pipeline de jobs
  ↓
Libraire et mémoire
  ↓
Choix de famille et de niveau
  ↓
Orchestrateur actif
  ↓
Deux travailleurs
  ↓
Inspection et résumé
  ↓
GitHub et bibliothèque
```

Le système doit toujours savoir :

1. quelle job est en cours;
2. qui en est responsable;
3. quel niveau de difficulté lui a été attribué;
4. quelle mémoire a été consultée;
5. qui a travaillé dessus;
6. quels fichiers ont été touchés;
7. quel résultat a été obtenu;
8. où se trouve le résumé final.

---

## 2. Fondation physique et identité

### 2.1 Disque dédié — ACTÉ

- Le disque dédié porte le nom **Antmux**.
- Son chemin initial est `D:\`.
- Antmux est installé directement à la racine du disque.
- Aucun dossier principal `D:\Antmux` n’est requis.
- Les outils, caches, données, configurations, journaux et fichiers temporaires appartenant au projet doivent rester sur ce disque autant que techniquement possible.

### 2.2 Identité — ACTÉ

- La commande publique est `antmux`.
- Le produit technique amont peut conserver ses noms internes, mais l’identité d’usage du système est **Antmux**.
- Reine-Linuxia est la première agente centrale du système.

### 2.3 Principe absolu

> Tout ce qui appartient à Antmux reste sur le disque Antmux.

---

## 3. Reine-Linuxia

### 3.1 Rôle — ACTÉ

Reine-Linuxia est :

- l’interface principale;
- l’interlocutrice directe de Brutus;
- l’orchestratrice centrale;
- une exécutante principale autorisée;
- la décideuse de délégation;
- la responsable de la vérification globale;
- la responsable de la réponse finale.

### 3.2 Relation avec Brutus — ACTÉ

Quand Brutus ouvre Antmux et écrit, il parle à Reine-Linuxia.

Aucun routeur, valet, libraire ou orchestrateur secondaire ne doit se placer entre Brutus et elle dans l’interface de départ.

### 3.3 Profil initial — ACTÉ POUR LE DÉPART

- **Modèle logique :** `gpt-5.4-mini`
- **Raisonnement :** `extra_high`
- **Vérification :** `extra_high`

Cette valeur est un profil de départ. La disponibilité réelle du modèle doit être vérifiée au moment du chargement.

### 3.4 Pouvoir d’exécution — ACTÉ

Reine-Linuxia peut :

- répondre directement;
- planifier;
- lire et modifier des fichiers;
- lancer des commandes;
- faire de la recherche;
- déléguer;
- reprendre une tâche;
- arrêter une branche;
- escalader une tâche;
- demander une inspection finale;
- produire le résultat final.

---

## 4. Les extensions de la Reine

### 4.1 Famille Qwen — ACTÉ COMME DIRECTION

Les modèles Qwen seront les extensions internes de Reine-Linuxia.

Ils ne constituent pas une seconde interface pour Brutus. Ils travaillent derrière la reine et peuvent servir à :

- classer;
- résumer;
- détecter une intention;
- lire une fiche de job;
- vérifier un format;
- assister le libraire;
- accomplir des tâches simples ou intermédiaires;
- préparer des plans.

### 4.2 Règle de visibilité

- Brutus parle à Reine-Linuxia.
- Reine-Linuxia parle aux extensions Qwen.
- Les extensions retournent leurs résultats à Reine-Linuxia ou à l’orchestrateur qui les a appelées.
- Les variantes Qwen précises seront définies dans une phase ultérieure.

---

## 5. Les deux entrées du pipeline

Antmux possède deux chemins d’entrée.

### 5.1 Entrée principale : Brutus → Reine-Linuxia — ACTÉ

Brutus formule une idée, une demande, un problème ou un mode d’emploi directement dans Antmux.

Reine-Linuxia transforme cette demande en entrée de pipeline.

### 5.2 Deuxième entrée : GitHub → Jules → queue — ACTÉ COMME CIBLE

ChatGPT ou une autre source peut produire plusieurs modes d’emploi ou fichiers dans :

```text
communication/inbox-chatgpt/
```

Jules surveille cet emplacement sur GitHub à intervalle régulier, initialement toutes les minutes.

Lorsqu’il voit un ou plusieurs nouveaux fichiers :

1. il les détecte;
2. il les importe;
3. il les transforme en entrées de jobs;
4. il les place dans la queue;
5. il évite de les perdre ou de les écraser.

Jules ne décide pas du niveau ni de l’orchestrateur. Il agit comme pont d’entrée et de publication.

---

## 6. Le registre d’entrée : valet, journaliste et numéro de job

### 6.1 Fonction — ACTÉ DANS LE FLUX

Une fonction légère d’enregistrement reçoit la demande brute avant l’analyse du libraire.

Cette fonction peut être appelée :

- **valet de réception**;
- **journaliste de job**;
- **registre d’entrée**.

Le nom définitif pourra être choisi plus tard. Son travail reste le même.

### 6.2 Ce qu’il fait

Il :

1. reçoit la demande;
2. attribue un numéro unique;
3. crée la fiche de job;
4. conserve le texte original;
5. note la source;
6. horodate la réception;
7. place la job dans la queue;
8. maintient le suivi jusqu’au résumé final.

### 6.3 Ce qu’il ne fait pas

Il ne :

- choisit pas la famille Grok ou Codex;
- juge pas seul la complexité;
- exécute pas la tâche;
- modifie pas le sens de la demande;
- remplace pas le libraire.

### 6.4 Numérotation — ACTÉ

Chaque job reçoit un identifiant permanent :

```text
JOB-000001
JOB-000002
JOB-000003
```

Le même numéro suit la job pendant tout son cycle.

Exemples :

```text
JOB-000014.md
JOB-000014-EVENTS.jsonl
JOB-000014-RESUME.md
```

Le résumé ne reçoit pas un numéro sans rapport avec la job. Il réutilise le numéro de la job.

---

## 7. La queue

### 7.1 But — ACTÉ

La queue évite que plusieurs demandes partent en désordre.

Elle donne aussi au libraire le temps de retrouver les souvenirs, erreurs, documents et décisions utiles avant le lancement.

### 7.2 États minimaux

```text
INBOX
QUEUED
LIBRARY_REVIEW
READY
ASSIGNED
RUNNING
VERIFYING
COMPLETED
BLOCKED
```

Une phase ultérieure pourra ajouter d’autres états, mais ces états suffisent au premier noyau.

### 7.3 Règles

- Une job ne doit pas disparaître entre deux étapes.
- Une job ne doit pas être prise simultanément par deux libraires.
- Une job ne doit pas être exécutée avant son passage au libraire, sauf urgence explicitement décidée par Reine-Linuxia.
- Une job peut attendre si la branche requise est déjà occupée.
- La queue peut recevoir plusieurs jobs d’un coup.

### 7.4 Capacité initiale — PROVISOIRE

L’interface peut présenter dix emplacements visibles au départ, par exemple jobs 1 à 10. Ce nombre est un choix d’affichage, pas une limite définitive du système.

---

## 8. Le Libraire

### 8.1 Place dans le pipeline — ACTÉ

Après l’enregistrement et la mise en queue, le **Libraire** est le premier agent analytique à prendre la job.

### 8.2 Source de mémoire — ACTÉ

Le Libraire travaille directement avec **Obsidian** comme bibliothèque vivante.

Il peut consulter :

- les erreurs déjà rencontrées;
- les solutions déjà utilisées;
- les modes d’emploi;
- les décisions antérieures;
- les projets associés;
- les fichiers fréquemment touchés;
- les avertissements noirs;
- les jobs actuellement en cours;
- les résumés précédents;
- les instructions futures.

### 8.3 Mission

Pour chaque job, le Libraire :

1. lit la demande originale;
2. identifie le projet, le langage, le dossier ou le type d’erreur;
3. cherche les souvenirs utiles;
4. relie les documents pertinents;
5. ajoute un dossier mémoire à la job;
6. estime la difficulté;
7. choisit une famille de traitement;
8. choisit un niveau;
9. choisit le gestionnaire de tâches ou orchestrateur approprié;
10. remet la job enrichie à la branche choisie.

### 8.4 Nature de sa décision

Le Libraire suggère et route. Il ne doit pas cacher ses raisons.

Sa fiche doit expliquer :

- pourquoi cette famille;
- pourquoi ce niveau;
- quels souvenirs ont été trouvés;
- quels risques sont connus;
- si une escalade immédiate est conseillée.

### 8.5 Plusieurs niveaux de Libraire — FUTUR

Le rôle de Libraire pourra lui-même exister en plusieurs niveaux. Un libraire léger pourra traiter les demandes évidentes; un libraire plus fort pourra reprendre les demandes ambiguës ou complexes.

---

## 9. Échelle de difficulté de 1 à 9

### 9.1 Principe — ACTÉ

Le Libraire attribue un niveau de **1 à 9**.

Les quatre premiers niveaux utilisent les quatre efforts du profil mini. Les cinq niveaux suivants montent par familles de modèles.

### 9.2 Échelle initiale

| Niveau | Profil logique initial | Usage général |
|---:|---|---|
| 1 | GPT-5.4 mini — low | copie simple, renommage, lecture courte, classement évident |
| 2 | GPT-5.4 mini — medium | petite transformation, résumé court, vérification simple |
| 3 | GPT-5.4 mini — high | petite planification, modification limitée, diagnostic courant |
| 4 | GPT-5.4 mini — extra | tâche mini exigeante, triage délicat, préparation structurée |
| 5 | GPT-5.4 | travail standard nécessitant davantage de raisonnement |
| 6 | GPT-5.5 | travail complexe ou multi-fichiers |
| 7 | GPT-5.6 Luna | analyse forte, coordination importante |
| 8 | GPT-5.6 Terra | problème difficile, risque élevé, reprise d’échecs |
| 9 | GPT-5.6 Sol | mode chirurgical, critique, inspection maximale |

### 9.3 Statut des noms — PROVISOIRE

Les noms `Luna`, `Terra` et `Sol` sont les profils choisis par Brutus dans son environnement. Le chargeur devra vérifier leur disponibilité réelle au démarrage et refuser silencieusement de substituer un autre profil sans trace.

### 9.4 Règle d’escalade

- Si une job dépasse le niveau de l’agent ou du planificateur, elle monte.
- Elle ne doit pas être forcée à rester dans un niveau insuffisant.
- Une escalade doit conserver tout le contexte déjà produit.
- Le niveau rouge chirurgical correspond normalement au niveau 9.

---

## 10. Les deux familles d’orchestration

### 10.1 Familles — ACTÉ

Antmux possède deux branches principales :

1. **branche Codex**;
2. **branche Grok**.

Le Libraire choisit la famille selon la nature de la job.

### 10.2 Orientation générale

#### Codex

Préféré pour :

- code local;
- dépôts;
- scripts;
- fichiers;
- tests;
- réparations techniques;
- exécution structurée dans le workspace.

#### Grok

Préféré pour :

- recherche externe;
- contradiction;
- exploration;
- critique;
- comparaison de sources;
- réflexion nécessitant une perspective extérieure.

### 10.3 Trois niveaux par famille — ACTÉ

Chaque famille possède trois catégories de gestion :

- facile;
- moyen;
- difficile.

Les niveaux 1 à 9 permettent de sélectionner plus précisément le modèle et l’effort à l’intérieur de ces catégories.

### 10.4 Administrateurs de niveau — ACTÉ COMME CONCEPT

Chaque catégorie peut avoir un administrateur ou gardien de porte.

Il :

- reçoit la job routée;
- vérifie que le niveau convient;
- attend si l’orchestrateur de sa famille est occupé;
- déclenche l’orchestrateur lorsque la place est libre;
- escalade si le niveau est insuffisant.

---

## 11. Limite d’orchestrateurs actifs

### 11.1 Concurrence — ACTÉ

À un instant donné, Antmux autorise au maximum :

- **un orchestrateur Codex actif**;
- **un orchestrateur Grok actif**.

Donc, maximum deux orchestrateurs actifs simultanément.

### 11.2 Important

Il ne s’agit pas d’une limite de deux jobs totales. Plusieurs jobs peuvent attendre dans la queue.

Il s’agit d’une limite de deux chefs d’orchestration actifs : un par famille.

### 11.3 Niveau de l’orchestrateur

L’orchestrateur actif prend le niveau requis par la job : facile, moyen ou difficile, avec un profil logique correspondant à l’échelle 1 à 9.

---

## 12. Travailleurs de l’orchestrateur

### 12.1 Taille d’équipe — ACTÉ

Chaque orchestrateur actif peut appeler **deux travailleurs**.

Structure maximale normale :

```text
Orchestrateur Codex
  ├─ Travailleur Codex A
  └─ Travailleur Codex B

Orchestrateur Grok
  ├─ Travailleur Grok A
  └─ Travailleur Grok B
```

### 12.2 Même famille et même niveau — ACTÉ

- Un orchestrateur Codex choisit des travailleurs Codex.
- Un orchestrateur Grok choisit des travailleurs Grok.
- Les travailleurs sont choisis au même niveau général que l’orchestrateur.
- Une équipe basse ne doit pas s’attribuer secrètement des capacités supérieures.

### 12.3 Division de la job

L’orchestrateur peut diviser une job en deux sous-tâches complémentaires pour accélérer le travail.

Exemples :

- un travailleur analyse pendant que l’autre prépare;
- un travailleur modifie pendant que l’autre teste;
- un travailleur recherche pendant que l’autre critique;
- un travailleur examine le code pendant que l’autre examine les journaux.

### 12.4 Escalade

Si l’équipe ne peut pas accomplir la job :

1. elle arrête proprement;
2. elle écrit ce qu’elle a tenté;
3. elle conserve les erreurs;
4. elle renvoie la job au niveau supérieur;
5. elle ne recommence pas éternellement la même stratégie.

---

## 13. Voie problématique

### 13.1 Répertoire spécialisé — ACTÉ COMME CONCEPT

Une job peut être placée dans une voie marquée :

```text
problematic/
```

### 13.2 Critères possibles

- erreurs répétées;
- incohérence de mémoire;
- risque élevé;
- tâche déjà échouée plusieurs fois;
- comportement inattendu;
- fichiers critiques;
- demande rouge;
- contradiction entre agents.

### 13.3 Traitement

Les jobs problématiques sont prises par le meilleur profil disponible, normalement niveau 9, avec une méthode chirurgicale et une inspection renforcée.

---

## 14. Spécialistes appelables

Les spécialistes ne deviennent pas automatiquement des orchestrateurs supplémentaires. Ils sont appelés au besoin.

### 14.1 Obsidian

- bibliothèque permanente;
- mémoire du Libraire;
- décisions;
- erreurs;
- instructions;
- modes d’emploi;
- résumés classés.

### 14.2 GitHub

- archive versionnée;
- dépôt des modes d’emploi;
- dépôt des résumés;
- vérité du code publié;
- seconde entrée de pipeline.

### 14.3 Copilot

- spécialiste de réparation de code;
- revue ciblée;
- proposition de correction;
- intervention sur demande;
- résultat vérifié ensuite par la branche Codex ou l’inspecteur final.

### 14.4 Jules

Jules possède deux fonctions prévues :

1. surveiller l’entrée GitHub `communication/inbox-chatgpt/`;
2. publier les résumés dans `communication/resumes/`.

Jules ne rédige pas le résumé final. Il transporte, importe ou publie les fichiers.

### 14.5 Inspecteur final

Un profil ChatGPT fort peut être appelé à la fin pour :

- relire le résultat;
- vérifier les critères;
- inspecter les changements;
- détecter les incohérences;
- refuser une validation insuffisante;
- déclencher une reprise.

Le niveau 9 est recommandé pour les jobs rouges, problématiques ou critiques.

---

## 15. Suivi complet de chaque job

### 15.1 Principe — ACTÉ

Toutes les jobs doivent laisser une trace.

### 15.2 Fiche centrale

Chaque job doit contenir au minimum :

- `job_id`;
- titre;
- demande originale;
- source;
- date de création;
- statut;
- projet;
- catégorie;
- niveau 1 à 9;
- famille choisie;
- orchestrateur;
- travailleurs;
- souvenirs liés;
- fichiers ciblés;
- risques;
- événements;
- résultat;
- résumé final.

### 15.3 Journal d’événements

Chaque acteur inscrit :

- ce qu’il a reçu;
- ce qu’il a décidé;
- ce qu’il a fait;
- les fichiers touchés;
- les commandes importantes;
- les erreurs;
- le niveau de confiance;
- ce qui doit arriver ensuite.

### 15.4 Propriétaire unique

À chaque instant, une job doit avoir un propriétaire actif unique. Les deux travailleurs peuvent contribuer, mais l’orchestrateur demeure responsable de l’ensemble.

---

## 16. Résumé final

### 16.1 Auteur logique — ACTÉ

Le registre d’entrée ou journaliste qui a ouvert le dossier garde le fil de la job et compile le résumé final à partir des traces.

L’inspecteur final peut le valider avant publication.

### 16.2 Numéro — ACTÉ

Le résumé reprend le numéro de job.

Exemple :

```text
JOB-000014-RESUME.md
```

### 16.3 Contenu minimal

```markdown
---
job_id: JOB-000014
created_at: 2026-07-15T03:44:04-04:00
project: Antmux
tags: []
status: a-classer
family: codex
level: 4
---

🚦 DÉBUT DU RÉSUMÉ

Objectif :

Travail effectué :

Fichiers créés ou modifiés :

Vérifications :

Blocages ou risques :

Niveau de confiance :

Prochaine action unique :

🏁 FIN DU TERMINAL
```

### 16.4 Emplacement local

```text
D:\communication\resumes\
```

### 16.5 Emplacement GitHub — ACTÉ

```text
communication/resumes/
```

Chaque résumé doit rester visible sur GitHub. GitHub devient une grande bibliothèque chronologique et versionnée des jobs.

### 16.6 Aucun écrasement

- Chaque résumé garde son numéro de job.
- Aucun ancien résumé ne doit être remplacé.
- `LATEST.md` peut exister comme raccourci local, mais ne remplace jamais l’archive numérotée.

### 16.7 Classement futur dans Obsidian

Un agent bibliothécaire pourra plus tard lire les résumés GitHub et les copier dans Obsidian.

L’original reste sur GitHub. Obsidian reçoit une version classée et reliée à la mémoire.

---

## 17. Code couleur et macro

### 17.1 Principe — ACTÉ

La couleur apparaît comme premier caractère d’une ligne placée vers la fin du terminal ou du résumé.

La couleur n’est pas interprétée directement par ChatGPT. **La macro de Brutus interprète la couleur et envoie ensuite une instruction texte claire.**

### 17.2 Échelle initiale — ACTÉ COMME POINT DE DÉPART

| Couleur | Sens général |
|---|---|
| 🔵 Bleu | première apparition ou faible activité |
| 🟢 Vert | sujet revenu ou activité normale |
| 🟡 Jaune | sujet fréquent ou importance croissante |
| 🟠 Orange | sujet persistant, attention forte |
| 🔴 Rouge | traitement chirurgical, complet, étape par étape |
| ⚫ Noir | avertissement mémoire ou instruction future fondamentale |

### 17.3 Rouge

Quand la macro envoie une **instruction rouge** :

- le système ralentit;
- il traite le sujet méticuleusement;
- il avance étape par étape;
- il vérifie chaque étape;
- il utilise un profil fort;
- il produit un résumé détaillé;
- il évite les raccourcis.

### 17.4 Noir

Quand la macro envoie une **instruction noire** :

- le contenu est considéré comme une règle à retenir;
- il peut s’agir d’un avertissement du type « si cette condition apparaît, arrêter et ne pas toucher »;
- la règle doit être préparée pour le fichier `INSTRUCTIONS-FUTURES.md`;
- l’automatisation complète de cette fonction est prévue pour plus tard.

### 17.5 Autorité de la macro

La macro traduit la couleur en consigne explicite. Exemple :

```text
INSTRUCTION ROUGE — Traite JOB-000014 en mode chirurgical.
```

ou :

```text
INSTRUCTION NOIRE — Ajoute cette règle à INSTRUCTIONS-FUTURES.md.
```

---

## 18. Instructions futures

### 18.1 Fichier prévu — FUTUR

```text
INSTRUCTIONS-FUTURES.md
```

### 18.2 But

Ce fichier contiendra des règles compactes destinées à améliorer les prochaines sessions.

### 18.3 Format envisagé

Chaque capsule noire pourra contenir :

- déclencheur;
- action obligatoire;
- action interdite;
- source;
- priorité;
- job d’origine.

Exemple :

```markdown
## IF-0007

- Déclencheur : le disque cible n’est pas nommé Antmux
- Action : arrêter avant toute installation
- Interdit : écrire sur le disque système
- Source : JOB-000021
- Priorité : noire
```

### 18.4 Statut

Le fichier peut être créé tôt comme réserve, mais la compression automatique et l’injection dans les sessions seront développées plus tard.

---

## 19. Flux complet d’une job

### 19.1 Entrée directe

```text
Brutus écrit à Reine-Linuxia
→ la demande entre dans le pipeline
→ le registre attribue JOB-xxxxxx
→ la job entre dans la queue
→ le Libraire consulte Obsidian
→ le Libraire ajoute les souvenirs
→ le Libraire attribue famille et niveau
→ l’administrateur de niveau attend une place
→ l’orchestrateur actif prend la job
→ deux travailleurs sont appelés
→ l’orchestrateur consolide
→ l’inspecteur vérifie au besoin
→ le journaliste compile le résumé
→ le résumé est sauvegardé localement
→ Jules le publie dans communication/resumes
→ la job passe à COMPLETED
```

### 19.2 Entrée GitHub

```text
ChatGPT produit un ou plusieurs modes d’emploi
→ fichiers déposés dans communication/inbox-chatgpt
→ Jules les détecte
→ Jules les importe dans la queue
→ chaque fichier reçoit un JOB-xxxxxx
→ le Libraire traite chaque job séparément
→ le flux normal continue
```

---

## 20. Principes de sécurité et de qualité

1. Aucun agent ne s’accorde lui-même plus de permissions.
2. Toute action irréversible demande une décision humaine ou une politique explicite.
3. Une job garde un propriétaire unique.
4. Deux agents ne doivent pas modifier simultanément le même workspace sans coordination.
5. Toute escalade conserve l’historique.
6. Toute erreur utile doit être enregistrée.
7. Une réussite ne doit pas être déclarée sans vérification.
8. Le résultat final doit indiquer un niveau de confiance.
9. Une job problématique ne doit pas être recyclée indéfiniment dans la même stratégie.
10. Les secrets ne doivent pas être inscrits dans les résumés, les prompts ou GitHub.
11. Les résumés doivent être utiles à un futur agent qui ne connaît pas la conversation d’origine.
12. Reine-Linuxia conserve l’autorité finale.

---

## 21. Arborescence cible initiale

```text
D:\
├─ AGENTS.md
├─ INSTRUCTIONS-FUTURES.md              # réserve future
├─ communication\
│  ├─ inbox-chatgpt\                    # deuxième entrée
│  └─ resumes\                          # résumés locaux
├─ pipeline\
│  ├─ inbox\
│  ├─ queue\
│  │  ├─ pending\
│  │  ├─ claimed\
│  │  ├─ running\
│  │  ├─ blocked\
│  │  └─ completed\
│  ├─ jobs\
│  ├─ events\
│  ├─ problematic\
│  ├─ state\
│  └─ templates\
├─ library\                              # point de montage ou vault Obsidian futur
├─ config\
│  ├─ agents\
│  ├─ models\
│  ├─ routing\
│  └─ policies\
├─ hooks\
├─ logs\
└─ runtime\
```

Dans GitHub :

```text
communication/
├─ inbox-chatgpt/
└─ resumes/

docs/
├─ architecture/
└─ execution/
```

---

## 22. Phases de construction

### Phase 1 — Première boîte

Construire uniquement :

- l’entrée de job;
- la numérotation;
- la fiche de job;
- la queue;
- la remise au Libraire;
- un test manuel complet.

### Phase 2 — Libraire et mémoire

- connecter Obsidian;
- rechercher les souvenirs;
- attacher les sources;
- produire l’évaluation 1 à 9.

### Phase 3 — Routage

- branche Codex;
- branche Grok;
- catégories facile, moyen, difficile;
- administrateurs de niveau.

### Phase 4 — Orchestrateurs et travailleurs

- un orchestrateur actif par famille;
- deux travailleurs;
- verrous de concurrence;
- escalade.

### Phase 5 — Suivi et événements

- journal par job;
- propriétaire;
- fichiers;
- erreurs;
- confiance;
- reprise.

### Phase 6 — Résumés GitHub

- résumé numéroté;
- publication par Jules;
- visibilité GitHub;
- préparation au classement Obsidian.

### Phase 7 — Deuxième entrée

- surveillance `communication/inbox-chatgpt`;
- import périodique;
- déduplication;
- création automatique de jobs.

### Phase 8 — Couleurs et macro

- protocole bleu à noir;
- instruction rouge;
- instruction noire;
- intégration à la macro.

### Phase 9 — Instructions futures

- capsules noires;
- compression;
- lecture au démarrage;
- amélioration continue.

### Phase 10 — Spécialistes et inspection

- Copilot;
- GitHub;
- Jules;
- inspecteur final;
- voie problématique niveau 9.

---

## 23. Décisions encore ouvertes

Les points suivants ne doivent pas être inventés sans Brutus :

1. nom final du valet ou journaliste d’entrée;
2. variantes Qwen exactes;
3. modèle précis des Libraires;
4. correspondance exacte entre niveaux 5 à 9 et efforts internes;
5. format technique de la base d’état;
6. fréquence définitive de Jules;
7. branche GitHub utilisée pour les publications automatiques;
8. règle exacte de fusion de résumés;
9. signification finale de chaque couleur pour la macro;
10. format final de `INSTRUCTIONS-FUTURES.md`;
11. identité exacte de l’inspecteur final;
12. politique d’approbation des actions irréversibles.

---

## 24. Définition de réussite du système

Antmux sera considéré fonctionnel lorsque :

- Brutus peut écrire une demande à Reine-Linuxia;
- la demande reçoit automatiquement un numéro de job;
- la job reste visible dans une queue;
- le Libraire consulte la mémoire avant l’exécution;
- la famille et le niveau sont justifiés;
- les limites d’orchestrateurs sont respectées;
- chaque job conserve son suivi;
- chaque résultat est vérifié;
- chaque job terminée produit un résumé du même numéro;
- chaque résumé apparaît dans `communication/resumes/` sur GitHub;
- un redémarrage ne fait perdre ni la queue, ni les jobs, ni les résumés.

---

## 25. Prochaine action autorisée

La prochaine action n’est pas de construire tout Antmux d’un coup.

La prochaine action est d’exécuter uniquement la **Phase 1 — Première boîte** selon le document :

```text
docs/execution/PHASE-01-PREMIERE-BOITE.md
```
