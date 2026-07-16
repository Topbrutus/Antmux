# MODULE ANTMUX — NINOSCREEN

## Utilisation

Copier tout le bloc **INSTRUCTION À EXÉCUTER** dans Antmux CLI.

---

## INSTRUCTION À EXÉCUTER

Tu agis comme responsable d’installation, d’audit et de réparation du projet **NinoScreen**.

### 1. Identité du projet

- Nom : `NinoScreen`
- Dépôt GitHub canonique : `https://github.com/Topbrutus/ninoscreens.git`
- Branche : `main`
- Projet Antmux proposé : `PROJECT-000001`, seulement si ce numéro est libre dans le registre; sinon utiliser le prochain numéro permanent disponible.
- Destination obligatoire : `D:\tools\ninoscreens`
- Le disque doit porter le nom de volume `Antmux`.
- Aucun fichier permanent de NinoScreen ne doit être installé ailleurs que sur le disque Antmux.

### 2. Mission

Installer ou mettre à jour NinoScreen sur `D:\tools\ninoscreens`, préserver les données existantes, auditer son état réel, réparer les défauts qui empêchent son fonctionnement, rendre ses données portables sur `D:\`, créer un lanceur simple et produire un rapport complet.

Ne pas redessiner l’application. Ne pas supprimer des fonctions existantes. Réparer d’abord ce qui existe.

### 3. État connu à vérifier

Le code actuel est une application Python utilisant PySide6 et Qt WebEngine.

L’état attendu du code comprend :

- `main.py` comme point d’entrée;
- `app/` comme paquet principal;
- `requirements.txt`;
- 3 pages de 12 carreaux, donc 36 carreaux;
- une page RUN supplémentaire;
- persistance des URL, du zoom, de la fenêtre, du focus et des sessions;
- affichage en grille et en mode focus;
- vue divisée;
- intégration ou espace de travail RUN;
- dépendances minimales `PySide6>=6.6` et `keyring>=25.0`.

Le README peut contenir des informations plus anciennes parlant de 9 carreaux. Le code réel prévaut. Corriger la documentation seulement après validation du comportement réel.

### 4. Règles de sécurité

1. Vérifier que `D:\` existe, est accessible et porte le label `Antmux`.
2. Ne jamais écraser un dossier existant sans sauvegarde.
3. Si `D:\tools\ninoscreens` existe déjà :
   - vérifier s’il s’agit d’un dépôt Git;
   - enregistrer l’état Git;
   - sauvegarder les fichiers modifiés et non suivis;
   - ne pas faire de `reset --hard`;
   - ne pas supprimer les profils web, cookies, sessions ou fichiers utilisateur.
4. Ne jamais stocker de clé, mot de passe ou jeton dans le dépôt.
5. Ne rien installer globalement dans Windows si une installation locale sur `D:\` est possible.
6. En cas de conflit Git ou de données ambiguës, arrêter l’étape destructive et produire un diagnostic précis.

### 5. Installation ou mise à jour du code

Créer `D:\tools` si nécessaire.

Si le projet n’existe pas :

```powershell
git clone https://github.com/Topbrutus/ninoscreens.git D:\tools\ninoscreens
```

S’il existe déjà et que le dépôt est propre :

```powershell
git -C D:\tools\ninoscreens fetch origin main
git -C D:\tools\ninoscreens checkout main
git -C D:\tools\ninoscreens pull --ff-only origin main
```

S’il n’est pas propre, sauvegarder l’état avant toute mise à jour et rapporter les différences.

### 6. Python portable et environnement virtuel

Chercher d’abord un Python 3.11 ou plus récent déjà disponible sur le disque Antmux.

Ordre recommandé :

1. `D:\python\python.exe`
2. `D:\tools\python\python.exe`
3. un Python accessible dans `PATH`, seulement pour créer l’environnement local sur `D:\`.

Créer l’environnement virtuel ici :

```text
D:\tools\ninoscreens\.venv
```

Commandes typiques :

```powershell
python -m venv D:\tools\ninoscreens\.venv
D:\tools\ninoscreens\.venv\Scripts\python.exe -m pip install --upgrade pip
D:\tools\ninoscreens\.venv\Scripts\python.exe -m pip install -r D:\tools\ninoscreens\requirements.txt
```

Tous les caches temporaires créés pendant l’installation doivent pointer vers un dossier sous `D:\temp\ninoscreens` ou `D:\cache\ninoscreens` lorsque possible.

Si aucun Python compatible n’est disponible, ne pas installer Python sur `C:\`. Produire un diagnostic et préparer une installation portable sur `D:\`.

### 7. Portabilité obligatoire des données

Le code actuel peut utiliser `QStandardPaths`, ce qui place normalement les données dans le profil Windows de l’utilisateur. Corriger ce comportement proprement.

Créer une racine de données portable :

```text
D:\tools\ninoscreens\data
```

Implémentation recommandée :

- ajouter la variable d’environnement `NINO_DATA_ROOT`;
- modifier `app/config.py` pour utiliser `NINO_DATA_ROOT` lorsqu’elle est définie;
- conserver `QStandardPaths` comme repli uniquement;
- faire pointer le lanceur vers `NINO_DATA_ROOT=D:\tools\ninoscreens\data`;
- placer le fichier de session et le profil WebEngine sous cette racine;
- migrer ou copier les anciennes données seulement après sauvegarde;
- ne jamais supprimer automatiquement les anciennes données du profil Windows.

Comportement attendu :

```python
root_override = os.environ.get("NINO_DATA_ROOT")
if root_override:
    path = Path(root_override)
else:
    location = QStandardPaths.writableLocation(...)
    path = Path(location) / APP_NAME
```

### 8. Lanceur

Créer :

```text
D:\tools\ninoscreens\NinoScreen.cmd
```

Le lanceur doit :

- calculer son propre dossier;
- définir `NINO_DATA_ROOT` sous le dossier du projet;
- définir `PYTHONUTF8=1`;
- utiliser uniquement `.venv\Scripts\python.exe`;
- lancer `main.py`;
- retourner le vrai code de sortie;
- ne dépendre d’aucun chemin utilisateur fixe.

Exemple logique :

```bat
@echo off
setlocal
set "NINO_ROOT=%~dp0"
set "NINO_DATA_ROOT=%NINO_ROOT%data"
set "PYTHONUTF8=1"
"%NINO_ROOT%.venv\Scripts\python.exe" "%NINO_ROOT%main.py"
exit /b %ERRORLEVEL%
```

Créer aussi, si utile :

```text
D:\tools\NinoScreen.cmd
```

Ce second lanceur doit seulement appeler le lanceur canonique du projet.

### 9. Audit technique avant lancement

Exécuter au minimum :

```powershell
D:\tools\ninoscreens\.venv\Scripts\python.exe -m compileall D:\tools\ninoscreens
D:\tools\ninoscreens\.venv\Scripts\python.exe -c "import PySide6; import keyring; import app.config; print('imports-ok')"
```

Vérifier :

- syntaxe Python;
- imports;
- absence de fichier tronqué ou corrompu;
- cohérence de `main.py`;
- existence des modules importés au démarrage;
- cohérence des constantes 36 carreaux et page RUN;
- chemins de session;
- création du profil WebEngine sur `D:\`;
- encodage UTF-8;
- absence de secret commité;
- état Git avant et après réparation.

### 10. Test fonctionnel manuel

Lancer `NinoScreen.cmd` et vérifier :

1. l’application ouvre sans trace d’erreur;
2. la fenêtre conserve une taille utilisable;
3. les 3 pages de 12 carreaux existent;
4. les 36 carreaux sont accessibles;
5. la page RUN existe;
6. les pages déjà configurées ou préchargées sont restaurées;
7. une URL peut être chargée dans un carreau;
8. retour, avancer et recharger fonctionnent;
9. le zoom par carreau fonctionne;
10. le mode focus fonctionne;
11. la vue divisée fonctionne;
12. la fermeture puis la relance restaurent la session;
13. les données sont écrites sous `D:\tools\ninoscreens\data`;
14. aucun nouveau fichier de session NinoScreen n’est créé sur `C:\` pendant le test.

Ne pas considérer l’installation réussie si l’application démarre mais perd ses 36 pages, ses sessions ou ses profils.

### 11. Réparations

Réparer seulement les défauts reproduits ou démontrés.

Ordre de priorité :

1. démarrage impossible;
2. dépendances manquantes;
3. imports ou fichiers corrompus;
4. données écrites hors de `D:\`;
5. perte de session;
6. erreur des 36 carreaux ou de la page RUN;
7. problèmes de focus, vue divisée ou navigation;
8. corruption d’encodage;
9. documentation périmée.

Pour chaque réparation :

- identifier la cause exacte;
- sauvegarder le fichier;
- effectuer le changement minimal;
- exécuter un test ciblé;
- exécuter ensuite les tests généraux;
- committer sur GitHub avec un message précis seulement si les tests passent;
- ne jamais déclarer un succès sans preuve.

### 12. Intégration Antmux

Enregistrer NinoScreen comme projet permanent dans Antmux.

Le registre doit contenir au minimum :

- numéro de projet permanent;
- nom `NinoScreen`;
- dépôt `Topbrutus/ninoscreens`;
- chemin local `D:\tools\ninoscreens`;
- technologie `Python / PySide6 / Qt WebEngine`;
- état d’installation;
- dernière version Git;
- chemin des données;
- chemin du lanceur;
- problèmes connus;
- dernier test réussi.

Chaque intervention future doit recevoir un numéro `JOB-xxxxxx` depuis le pipeline. Ne pas inventer un numéro de job manuellement si le registre n’est pas disponible.

### 13. Résultat exigé

À la fin, produire :

```text
🚦 DÉBUT DU RÉSUMÉ

Projet : NinoScreen
Projet Antmux : PROJECT-xxxxxx
Dépôt : Topbrutus/ninoscreens
Chemin : D:\tools\ninoscreens

État initial :
...

Installation effectuée :
...

Réparations effectuées :
...

Données portables :
...

Tests réussis :
...

Tests échoués ou non exécutés :
...

Fichiers modifiés :
...

Commits GitHub :
...

Problèmes restants :
...

Niveau de confiance :
...

Prochaine action recommandée :
...

🏁 FIN DU TERMINAL
```

Enregistrer le résumé localement dans `D:\communication\resumes\` et le publier dans le dossier GitHub canonique des résumés Antmux.

### 14. Condition de réussite

La mission est réussie uniquement si :

- NinoScreen est installé sous `D:\tools\ninoscreens`;
- son environnement Python est local au projet;
- son lanceur fonctionne;
- ses données persistantes résident sur `D:\`;
- les 36 carreaux et la page RUN sont présents;
- les fonctions principales sont testées;
- aucune donnée existante n’a été perdue;
- les modifications sont documentées;
- un résumé final vérifiable est produit.

Commence par un audit non destructif, puis exécute les étapes dans l’ordre. Ne demande confirmation que pour une action destructive, une migration de données ambiguë ou une authentification externe.
