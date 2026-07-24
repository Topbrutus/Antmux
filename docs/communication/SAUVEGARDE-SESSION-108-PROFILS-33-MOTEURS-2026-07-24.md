# Sauvegarde de session — LinuxIA / Antmux

**Date :** 24 juillet 2026  
**Auteur de la sauvegarde :** Rob  
**Décideur final :** Brutus  
**Projet :** LinuxIA / Antmux  
**Type :** transfert structuré vers une nouvelle session  
**Statut :** état de travail consolidé, sans remplacer les journaux bruts

---

## 1. Objet de cette sauvegarde

Cette sauvegarde conserve les décisions, validations, outils installés, essais réalisés et idées d’architecture discutés pendant la session.

Le point central atteint est la séparation nette entre :

- les **profils persistants de travailleurs**;
- les **moteurs CLI ou modèles** qui exécutent temporairement leur travail;
- la **bibliothèque commune**;
- les **bureaux individuels**;
- les **composants logiques de communication**;
- la **gouvernance spéciale** du système.

Décision actuelle :

```text
108 profils persistants de travailleurs
33 moteurs CLI/modèles partagés
15 départements logiciels
32 composants logiques de communication
1 composant spécial de gouvernance, appelé le 33e
```

Ces nombres ne décrivent pas la même couche et ne doivent plus être mélangés.

---

## 2. État de LinuxIA Interprète et du terminal

### 2.1 Interprète

LinuxIA Interprète 4B est actuellement la couche conversationnelle branchée au Shell.

Son rôle reste limité :

- traduire;
- reformuler;
- résumer;
- préserver les faits, nombres et états;
- ne pas exécuter;
- ne pas décider;
- ne pas inventer de progression.

Les orchestrateurs, la Reine, System Job, les ouvrières et le réviseur ne doivent pas être branchés aveuglément avant stabilisation des fondations.

### 2.2 Zone de saisie multilignes

Le défaut de saisie sur une seule ligne a été corrigé et testé visuellement.

Résultats observés :

- quatre lignes restent visibles;
- la zone de saisie s’agrandit vers le haut;
- la fourmi ASCII/3D reste affichée;
- un appui sur Entrée envoie tout le bloc comme une seule demande.

Statut de test :

```text
INPUT_COMPOSER_VISUAL = PASS
INPUT_COMPOSER_SUBMIT = PASS
```

### 2.3 Bégaiement

Le bégaiement était la priorité immédiate avant tout enrichissement vocal ou orchestration. Dans l’état observé en fin de session, Brutus considère le comportement corrigé et l’affichage stable.

Règle de continuité :

- au prochain démarrage, refaire un test court de non-régression;
- ne pas ajouter d’effets vocaux avant que l’orchestration de base soit stable;
- traiter la voix comme une couche d’habillage séparée.

---

## 3. Outils installés ou validés pendant la session

### 3.1 Obsidian CLI

Installation validée :

```text
Obsidian 1.12.7
installer 1.12.7
```

La commande `obsidian version` fonctionne après activation de la CLI dans Obsidian et réouverture de PowerShell.

### 3.2 Z.AI Coding Helper

Installation validée :

```text
Coding Helper v0.0.7
```

Le paquet utilisé est :

```text
@z_ai/coding-helper
```

Le Coding Plan Z.AI a été synchronisé avec OpenCode.

État confirmé :

```text
Chelper Configuration:
  Coding Plan: GLM Coding Plan Global
  API Key: Set

OpenCode Configuration:
  Coding Plan: GLM Coding Plan Global
  API Key: Set

Configuration synchronized
```

Aucune clé complète ne doit être copiée dans les documents ou les journaux.

### 3.3 OpenCode

Installation validée :

```text
OpenCode 1.18.4
```

Commande utilisée :

```powershell
npm install -g opencode-ai
```

OpenCode a été lancé dans :

```text
D:\tools\ninoscreens
```

### 3.4 Modèles gratuits visibles dans OpenCode

Modèles gratuits observés dans la liste OpenCode Zen :

- Ling-3.0-flash Free;
- Laguna S 2.1 Free;
- North Mini Code Free;
- Nemotron 3 Ultra Free;
- DeepSeek V4 Flash Free;
- MiMo V2.5 Free;
- Big Pickle, dont le statut exact doit rester à vérifier.

Fournisseur Z.AI Coding Plan visible :

- GLM-5.2;
- GLM-5V-Turbo;
- GLM-5.1;
- GLM-5-Turbo;
- GLM-4.7;
- GLM-4.5-Air.

`GLM-4.7-Flash` n’a pas été observé dans cette liste précise. Ne pas confondre `GLM-4.7` avec `GLM-4.7-Flash`.

### 3.5 Kimi Code

Le forfait gratuit **Adagio** a été identifié comme piste prioritaire.

Capacités recopiées du tableau fourni par Brutus :

- 1 tâche Agent simultanée;
- 2 tâches planifiées;
- 2 tâches de widget;
- 2 projets;
- 500 Mo de stockage;
- plus de 15 plugins.

Un script d’installation Kimi Code pour le disque D a été préparé :

```text
Install-Kimi-Code-D.ps1
```

Cible de données proposée :

```text
D:\tools\kimi-code-home
```

L’installation finale et la connexion `/login` n’ont pas été confirmées dans cette session.

### 3.6 Autres outils déjà utilisés ou présents dans l’écosystème

Gratuits, inclus dans un abonnement ou déjà disponibles :

- Gemini CLI;
- Antigravity;
- Hermes Agent;
- Jules;
- OpenCode;
- Z.AI Coding Helper;
- modèles gratuits OpenCode.

Payants ou à crédits :

- Codex;
- Grok;
- Claude selon les crédits disponibles;
- modèles Gemini selon le compte et le quota.

Noms découverts mais pas encore validés comme robots CLI opérationnels :

- Fable;
- Dopus;
- Kimi CLI avant validation finale;
- Cursor Agent CLI.

Ne pas compter un modèle et son interface comme deux CLI distinctes. Exemple : Laguna est un moteur utilisé dans OpenCode, pas une deuxième interface indépendante.

---

## 4. Test Laguna S 2.1 Free

Laguna a été testé sur le dépôt :

```text
D:\tools\ninoscreens
```

### 4.1 Première analyse

Laguna a lu `README.md` et `pyproject.toml`, puis a affirmé à tort que :

- `app.terminal` était manquant;
- `app/secret_store.py` était inexistant;
- le point d’entrée `main:main` risquait d’être invalide.

Cause principale : conclusions tirées à partir d’une documentation partielle, sans vérifier l’arborescence réelle.

### 4.2 Correction par preuve

Après instruction d’utiliser `git ls-files`, Laguna a confirmé :

- `main.py` à la racine;
- `app/terminal/__init__.py`;
- `app/terminal/runtime.py`;
- `app/secret_store.py`;
- `app/widgets`;
- `app/windows`.

Il a ensuite réfuté ses propres conclusions initiales.

### 4.3 Test du point d’entrée

Premier test exécuté avec le mauvais Python :

```powershell
python -c "from main import main; print(callable(main))"
```

Résultat :

```text
ModuleNotFoundError: No module named 'PySide6'
```

Laguna a conclu trop vite `ENTRYPOINT_BROKEN`.

Cette erreur prouvait seulement que l’interpréteur global n’avait pas PySide6.

Test corrigé avec l’environnement virtuel réel :

```powershell
& "D:\tools\ninoscreens\.venv\Scripts\python.exe" `
  -c "from main import main; print(callable(main))"
```

Résultat :

```text
True
ENTRYPOINT_OK
```

Verdict sur Laguna :

```text
Éclaireur utile sous supervision.
Capable de se corriger face aux preuves.
Ne doit pas être juge final sans contre-vérification.
```

### 4.4 Limites fournisseur

Erreur observée :

```text
provider rate limit exceeded
```

Comportement observé :

- compte à rebours d’environ huit minutes;
- reprise ou nouvelle tentative après le délai;
- un travail peut rester en attente entre deux fenêtres de quota;
- un temps total affiché peut inclure beaucoup d’attente et non seulement du calcul.

État conseillé pour ce cas :

```text
WAITING_RATE_LIMIT
```

Ne pas déclarer la tâche terminée tant qu’un verdict final explicite n’est pas affiché.

---

## 5. Décision d’architecture principale

### 5.1 Formule retenue

```text
108 profils persistants
33 moteurs partagés
1 orchestrateur d’affectation futur
1 cadre de gouvernance
```

### 5.2 Ce qu’est un profil de travailleur

Un travailleur possède durablement :

- une identité;
- une mission;
- un bureau;
- une mémoire;
- des permissions;
- une expérience;
- des décisions;
- des leçons;
- des incidents;
- des compétences;
- des relations avec d’autres travailleurs.

Un travailleur n’est pas un modèle et n’est pas une CLI.

### 5.3 Ce qu’est un moteur

Un moteur est une capacité d’exécution temporaire :

- OpenCode;
- Kimi;
- Gemini CLI;
- Hermes;
- Jules;
- Codex;
- Grok;
- Claude;
- un modèle local;
- un futur CLI.

Le même profil peut changer de moteur sans perdre son identité.

### 5.4 Affectation dynamique

Exemple :

```text
Travailleur API REST
→ Laguna pour une inspection gratuite
→ Kimi pour une tâche longue
→ Claude ou Codex pour une revue délicate
→ modèle local pour un contenu sensible
```

Il ne doit pas exister de liaison rigide :

```text
Profil 1 = moteur 1
```

Le moteur est choisi selon :

- domaine;
- qualité;
- vitesse;
- coût;
- quota;
- confidentialité;
- contexte maximal;
- disponibilité;
- outils autorisés;
- historique de fiabilité.

---

## 6. Les 108 profils logiciels

Brutus a fourni une liste complète de 108 travailleurs logiciels.

Ils sont organisés en 15 départements :

1. Architecture et conception;
2. Backend;
3. Frontend;
4. Fullstack et intégration;
5. Systèmes et performance;
6. Mobile;
7. Embarqué et IoT;
8. Données;
9. Data et pipelines;
10. Machine Learning et MLOps;
11. LLM et agents;
12. Plateforme et DevOps;
13. Qualité et tests;
14. Sécurité applicative;
15. Fiabilité et observabilité.

Chaque spécialisation est désormais considérée comme un véritable **profil de travailleur avec bureau**, mais elle reste dormante lorsqu’elle n’est pas sollicitée.

Règle :

```text
108 profils enregistrés
≠ 108 processus actifs
```

---

## 7. Les bureaux

Chaque profil possède un bureau isolé et léger.

Exemple :

```text
D:\workers\
└── software\
    └── 011-api-rest\
        ├── worker.yaml
        ├── STATE.md
        ├── memory\
        ├── workspace\
        ├── inbox\
        ├── outbox\
        ├── logs\
        └── checkpoints\
```

Le bureau ne contient jamais une copie complète d’OpenCode, Kimi, Codex ou d’un autre moteur.

Les moteurs sont installés et entretenus une seule fois dans un pool commun.

---

## 8. Bibliothèque et mémoire

### 8.1 GitHub

GitHub conserve le savoir durable et validé :

- identités;
- rôles;
- permissions;
- procédures;
- décisions validées;
- leçons durables;
- index;
- modèles de fichiers;
- états stables;
- documentation;
- historique versionné.

### 8.2 Disque D

Le disque D conserve l’atelier vivant :

- travail en cours;
- contexte temporaire;
- sorties non validées;
- journaux volumineux;
- caches;
- sessions;
- artefacts;
- checkpoints runtime;
- files d’attente.

### 8.3 Secrets

Les secrets ne vont ni dans GitHub ni dans les journaux.

Ils doivent utiliser :

- le gestionnaire d’identifiants du système;
- Keyring;
- une variable injectée au runtime;
- un stockage sécurisé explicitement approuvé.

---

## 9. Les 32 composants logiques et le 33e spécial

La session a clarifié que les 32 composants logiques ne sont pas les 108 travailleurs et ne sont pas les 33 moteurs.

Ils appartiennent à la couche de communication interne :

- états;
- événements;
- contrats;
- routes;
- enveloppes;
- permissions;
- validations;
- signaux;
- transitions.

Le 33e spécial appartient à la gouvernance :

- constitution;
- cohérence;
- arbitrage;
- règles absolues;
- autorisation;
- sécurité.

La liste exacte des 32 composants n’a pas été redéfinie dans cette session. Elle ne doit pas être inventée. Il faudra la relire depuis la source canonique existante avant intégration.

---

## 10. Idée de recherchiste CLI

Brutus a identifié une idée forte :

> maintenir un recherchiste permanent spécialisé dans la découverte des nouveaux robots CLI.

Méthode artisanale utilisée par Brutus :

```text
nom d’un modèle + CLI
```

Cette méthode trouve des sites, fournisseurs et nouveaux outils.

Le futur workflow pourra classer chaque découverte :

```text
TESTER
SURVEILLER
IGNORER
```

Critères :

- gratuité réelle;
- licence;
- activité du projet;
- Windows, WSL ou Linux;
- installation;
- coût;
- quotas;
- confidentialité;
- accès outils;
- compatibilité dépôt;
- possibilité de mode lecture seule;
- qualité des preuves;
- capacité à se corriger.

Ce recherchiste ne doit jamais installer automatiquement un outil.

---

## 11. Règles non négociables

1. Une chose à la fois.
2. Aucun déploiement des 108 profils en une seule passe.
3. Aucun démarrage simultané de 33 moteurs.
4. Aucun moteur ne possède la mémoire d’un travailleur.
5. Aucun secret dans GitHub.
6. Aucun résultat déclaré validé sans preuve.
7. Aucun agent gratuit considéré fiable après un seul test.
8. Les erreurs d’environnement ne doivent pas être confondues avec des défauts du dépôt.
9. Les attentes de quota doivent être représentées comme un état explicite.
10. Aucun push ou commit autonome sans autorisation prévue par la gouvernance.

---

## 12. Prochaine étape logique unique

Ne pas construire l’orchestrateur maintenant.

Ne pas créer immédiatement les 108 bureaux.

Ne pas installer immédiatement les 33 moteurs.

La prochaine étape unique est :

```text
Créer et valider le profil canonique d’un travailleur.
```

Ce modèle doit définir :

- identité;
- mission;
- département;
- bureau;
- mémoire durable;
- mémoire temporaire;
- permissions;
- entrées;
- sorties;
- états;
- moteurs compatibles;
- réviseurs;
- protocole de pause et reprise;
- protocole de validation.

Une fois ce modèle validé, il pourra servir à un premier profil pilote.

---

## 13. Prompt de reprise pour une nouvelle session

```text
Reconnecte-toi au dépôt Topbrutus/Antmux et au brain Topbrutus/MonCerveauGPT.

Lis en priorité :
- docs/communication/SAUVEGARDE-SESSION-108-PROFILS-33-MOTEURS-2026-07-24.md
- docs/communication/MODE-EMPLOI-ARCHITECTURE-108-PROFILS-33-MOTEURS.md

État actuel :
- 108 profils persistants de travailleurs;
- 33 moteurs CLI/modèles partagés;
- 15 départements logiciels;
- 32 composants logiques de communication distincts;
- 1 composant spécial de gouvernance;
- OpenCode 1.18.4 installé;
- Z.AI Coding Helper 0.0.7 synchronisé;
- Laguna S 2.1 Free validé comme éclaireur sous supervision;
- Obsidian CLI 1.12.7 fonctionnel;
- Kimi Code préparé mais installation finale non confirmée;
- saisie multilignes du Shell validée.

Action suivante unique :
créer le modèle canonique d’un profil de travailleur.
Ne crée pas encore les 108 profils.
Ne construis pas encore l’orchestrateur.
```

---

## 14. Statut final de la session

```text
Mémoire récente utile : consolidée
État actuel : architecture séparée et clarifiée
Prochaine étape logique : profil canonique d’un travailleur
Niveau de confiance : élevé sur les décisions de structure
Points non confirmés : installation finale Kimi, liste exacte des 32 composants
```
