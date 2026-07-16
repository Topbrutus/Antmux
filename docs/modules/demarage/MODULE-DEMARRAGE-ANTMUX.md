# MODULE — Démarrage unifié d’Antmux

## But

Créer un point d’entrée unique : lorsque Brutus tape simplement :

```powershell
antmux
```

le système doit préparer et démarrer l’environnement Antmux complet sans demander plusieurs commandes manuelles.

Ce module ne demande pas un démarrage automatique à l’ouverture de Windows. Le démarrage se produit uniquement lorsque l’utilisateur tape `antmux` dans un terminal.

---

## Règles obligatoires

1. Le disque Antmux doit être `D:\` et porter l’étiquette de volume `Antmux`.
2. Tous les fichiers permanents du système doivent rester sur `D:\`.
3. La commande publique est `antmux`, jamais `codex`.
4. Le mécanisme doit être idempotent : taper `antmux` deux fois ne doit pas lancer deux Jules.
5. Aucun service ne doit être déclaré actif sans vérification réelle du processus.
6. Aucun secret ne doit être écrit dans les scripts, les journaux ou les fichiers d’état.
7. Le lanceur doit fonctionner sous Windows PowerShell 5.1 avec `-ExecutionPolicy Bypass`.
8. Les erreurs d’un service doivent être affichées clairement sans empêcher l’ouverture du terminal lorsque cela demeure sécuritaire.

---

## Répertoire canonique à créer

```text
D:\demarage\
├─ bin\
│  └─ antmux.cmd
├─ config\
│  └─ services.json
├─ logs\
├─ state\
├─ Start-Antmux.ps1
├─ Stop-Antmux.ps1
├─ Restart-Antmux.ps1
├─ Get-AntmuxStatus.ps1
├─ Install-AntmuxCommand.ps1
└─ README.md
```

Le nom `demarage` est conservé volontairement comme nom de répertoire demandé par Brutus.

---

## Services initiaux

### Jules Summary Watcher

Lanceur existant :

```text
D:\jules-watch.cmd
```

Jules surveille :

```text
D:\communication\resumes\
```

Il publie les nouveaux résumés et peut ensuite appeler le pont ChatGPT. Le pont ChatGPT n’est donc pas un service permanent distinct à démarrer au lancement d’Antmux.

### Services futurs

Le fichier `D:\demarage\config\services.json` doit permettre d’ajouter plus tard d’autres services sans réécrire tout le lanceur, par exemple :

- pipeline de jobs;
- NinoScreen;
- serveur local;
- indexeur Obsidian;
- surveillance GitHub;
- orchestrateurs locaux.

Le fichier initial peut contenir seulement Jules.

Exemple :

```json
{
  "services": [
    {
      "id": "jules-summary-watcher",
      "enabled": true,
      "type": "process",
      "launcher": "D:\\jules-watch.cmd",
      "match": "Watch-AntmuxSummaries.ps1",
      "window": "hidden",
      "required": true
    }
  ]
}
```

---

## Travail demandé au terminal CLI

### Étape 1 — Audit non destructif

Avant toute modification :

- confirmer que `D:\` existe;
- confirmer que l’étiquette du volume est `Antmux`;
- vérifier la présence de `D:\jules-watch.cmd`;
- vérifier la présence de `D:\modules\jules\Watch-AntmuxSummaries.ps1`;
- détecter le véritable programme CLI actuellement utilisé;
- vérifier si `D:\demarage\bin` est déjà dans le PATH utilisateur;
- vérifier si une installation précédente existe;
- conserver les fichiers existants et créer des sauvegardes horodatées avant remplacement.

Ne pas supposer que Jules est actif seulement parce qu’un ancien fichier PID existe.

### Étape 2 — Installer les scripts de démarrage

Créer les scripts décrits ci-dessous.

#### `Start-Antmux.ps1`

Responsabilités :

1. valider le volume Antmux;
2. définir :

```powershell
$env:ANTMUX_ROOT = "D:\"
```

3. créer les répertoires `logs` et `state`;
4. charger `services.json`;
5. pour chaque service activé :
   - rechercher un processus réellement actif correspondant;
   - ne rien relancer lorsqu’il est déjà actif;
   - supprimer les fichiers PID périmés;
   - lancer le service en arrière-plan;
   - enregistrer PID, heure de départ et commande;
   - confirmer que le processus demeure actif après un court délai;
6. afficher un tableau d’état simple;
7. démarrer ensuite le véritable terminal interactif Antmux au premier plan.

Le terminal interactif peut techniquement utiliser un moteur installé comme Codex, mais l’utilisateur ne doit voir et taper que `antmux`.

Prévenir toute récursion : `Start-Antmux.ps1` ne doit jamais rappeler `antmux.cmd` comme moteur interne.

#### `Get-AntmuxStatus.ps1`

Afficher pour chaque service :

- nom;
- état `ACTIVE`, `STOPPED` ou `ERROR`;
- PID réel;
- heure de départ;
- chemin du journal;
- raison d’une erreur éventuelle.

#### `Stop-Antmux.ps1`

- arrêter seulement les processus démarrés et vérifiés par Antmux;
- ne jamais tuer un processus sur la seule base d’un nom générique;
- valider le PID, le chemin de commande et l’identité du service;
- nettoyer les fichiers d’état périmés;
- produire un rapport final.

#### `Restart-Antmux.ps1`

Exécuter proprement l’arrêt, puis le démarrage.

#### `Install-AntmuxCommand.ps1`

- ajouter `D:\demarage\bin` au PATH utilisateur sans supprimer les entrées existantes;
- ne pas ajouter le même chemin deux fois;
- créer `D:\demarage\bin\antmux.cmd`;
- expliquer qu’un terminal déjà ouvert peut devoir être fermé puis rouvert pour recevoir le nouveau PATH.

### Étape 3 — Commande publique

Le fichier `D:\demarage\bin\antmux.cmd` doit accepter :

```text
antmux
antmux start
antmux status
antmux stop
antmux restart
```

Comportement :

- `antmux` et `antmux start` : démarrer les services manquants puis ouvrir le CLI;
- `antmux status` : afficher l’état sans ouvrir le CLI;
- `antmux stop` : arrêter les services Antmux;
- `antmux restart` : redémarrer proprement les services puis ouvrir le CLI;
- commande inconnue : afficher l’aide et retourner un code d’erreur non nul.

Toutes les commandes PowerShell doivent utiliser :

```text
powershell.exe -NoProfile -ExecutionPolicy Bypass
```

### Étape 4 — Journaux

Créer au minimum :

```text
D:\demarage\logs\startup.log
D:\demarage\logs\jules-summary-watcher.log
D:\demarage\logs\errors.log
```

Chaque entrée doit contenir une date ISO 8601, l’identité du service, l’action et le résultat.

Limiter la croissance des journaux avec une rotation simple; ne pas laisser un fichier croître indéfiniment.

### Étape 5 — Test obligatoire

Exécuter cette séquence :

1. `antmux status` avant démarrage;
2. `antmux start`;
3. vérifier qu’un seul Jules est actif;
4. exécuter une deuxième fois `antmux start`;
5. confirmer qu’aucun deuxième Jules n’a été créé;
6. `antmux status`;
7. `antmux stop`;
8. confirmer l’arrêt;
9. `antmux start` une dernière fois;
10. confirmer que Jules surveille bien `D:\communication\resumes`.

Ne pas effectuer un vrai envoi ChatGPT ou une vraie publication GitHub pendant le test initial. Utiliser un mode de validation sûr lorsque disponible.

---

## Affichage attendu

Exemple :

```text
ANTMUX STARTUP
Drive  : D:\ [Antmux]
Jules  : ACTIVE PID=12345
Bridge : READY — invoked by Jules when needed
CLI    : STARTING
```

Si Jules est déjà actif :

```text
Jules  : ALREADY ACTIVE PID=12345
```

---

## Critères de réussite

Le module est terminé seulement lorsque :

- `antmux` est reconnu dans un nouveau terminal;
- Jules démarre automatiquement avec cette commande;
- Jules ne démarre jamais en double;
- `antmux status`, `stop` et `restart` fonctionnent;
- les journaux et fichiers d’état sont stockés sous `D:\demarage`;
- l’interface CLI demeure au premier plan;
- le pont ChatGPT reste déclenché par Jules et non lancé inutilement comme processus permanent;
- l’installation est documentée dans `D:\demarage\README.md`;
- toutes les modifications sont enregistrées dans GitHub avec un résumé clair.

---

## Rapport final exigé

À la fin, afficher :

```text
DÉMARRAGE ANTMUX INSTALLÉ
Commande : antmux
Jules    : ACTIVE ou raison précise de l’échec
Services : nombre actifs / nombre configurés
Chemin   : D:\demarage
PATH     : installé ou action restante
Tests    : succès / échecs détaillés
GitHub   : commit ou raison précise de l’absence de commit
```
