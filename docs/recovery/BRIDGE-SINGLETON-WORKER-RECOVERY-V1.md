# Récupération Bridge / Singleton / Worker v1

## Statut

- **État :** `PROPOSED_RECOVERY`
- **Branche :** `recovery/bridge-singleton-worker-v1`
- **Fusion automatique :** interdite
- **Validation runtime :** non exécutée au moment de la création
- **Compatibilité ciblée :** Windows PowerShell 5.1

## But

Reconstruire prudemment deux ensembles de fonctions qui avaient été créés localement sans être intégrés à `main` :

1. la sélection canonique de la tuile Nino ChatGPT;
2. la protection singleton du cœur Antmux et le lancement séparé des workers.

Les diagnostics historiques sont utilisés comme preuves d’intention, pas comme preuve que le runtime actuel fonctionne déjà.

## Artefacts reconstruits

### Cible ChatGPT canonique

- `config/chatgpt-bridge-target.example.json`
- `modules/chatgpt-bridge/ChatGPT.BridgeTarget.psm1`

Le module expose :

```text
Get-ChatGPTBridgeTarget
Test-ChatGPTBridgeTarget
Set-ChatGPTBridgeTarget
Clear-ChatGPTBridgeTarget
```

Le résolveur :

- lit une configuration locale explicite;
- sélectionne un numéro de tuile déterminé;
- exige un préfixe URL autorisé;
- peut exiger que la tuile soit visible, chargée et munie d’un élément de saisie;
- rapporte les autres tuiles ChatGPT sans les sélectionner;
- n’effectue aucun envoi, aucune automatisation clavier et aucune requête réseau.

`Clear-ChatGPTBridgeTarget` archive la configuration au lieu de la supprimer silencieusement.

### Cœur singleton

- `demarage/Start-AntmuxSingleton.ps1`

Le wrapper :

- utilise le mutex `Global\Antmux-Core`;
- refuse de choisir entre plusieurs processus `D:\antmux.exe`;
- ne ferme aucun processus;
- inscrit l’état dans `demarage/state/antmux-core.json`;
- inscrit le PID connu dans `demarage/state/antmux-core.pid`;
- écrit les événements dans `demarage/logs/startup.log`;
- appelle le lanceur existant uniquement après acquisition du verrou.

Il n’est pas encore branché automatiquement à la commande publique `antmux`.

### Worker séparé

- `demarage/Start-AntmuxWorker.ps1`

Le lanceur :

- exige exactement un cœur Antmux vérifié;
- refuse un état ambigu;
- définit les variables d’identité du worker;
- force `ANTMUX_WORKER_ONLY=1`, `ANTMUX_NO_CLI=1` et `ANTMUX_NO_BRIDGE=1`;
- écrit un profil dans `demarage/state/workers/<InstanceId>.json`;
- ne lance aucune commande sans le commutateur explicite `-Launch`.

## Validation sans effet externe

Depuis la racine du dépôt :

```powershell
git fetch origin
git switch recovery/bridge-singleton-worker-v1
& ".\tools\recovery\Test-BridgeSingletonWorkerRecovery.ps1"
```

Résultat attendu :

```text
TOTAL: 26
PASSED: 26
FAILED: 0
ALL_TESTS: PASS
```

Ce validateur :

- parse les trois scripts avec le parseur PowerShell;
- contrôle les interdictions statiques;
- utilise uniquement des fichiers temporaires;
- vérifie la sélection déterministe de la tuile 1;
- vérifie le refus d’une URL non autorisée;
- vérifie le refus d’une tuile invisible;
- vérifie que la suppression logique archive la configuration.

## Vérifications locales supplémentaires

### Singleton, sans démarrage

```powershell
& ".\demarage\Start-AntmuxSingleton.ps1" -ValidationOnly
```

Cette commande inspecte seulement les préconditions et les processus correspondants.

### Cible Nino réelle, sans envoi

Après création de `D:\config\chatgpt-bridge-target.json` à partir de l’exemple :

```powershell
Import-Module ".\modules\chatgpt-bridge\ChatGPT.BridgeTarget.psm1" -Force -Prefix Recovery
Test-RecoveryChatGPTBridgeTarget
```

Le statut recherché est :

```text
TARGET_RESOLVED_BY_CONFIGURATION
```

avec :

```text
Valid       : True
TileNumber  : 1
```

### Préparer un profil worker sans lancer de processus

```powershell
& ".\demarage\Start-AntmuxWorker.ps1" `
  -InstanceId "worker-test-01" `
  -DisplayName "Worker Test 01" `
  -Role "worker" `
  -Workspace "D:\workers\worker-test-01"
```

Sans `-Launch`, le résultat doit être `WORKER_PROFILE_PREPARED`.

## Limites obligatoires

Cette branche ne prouve pas encore :

- qu’une tuile Nino réelle est actuellement visible par le format JSON attendu;
- que le pont existant utilise automatiquement le nouveau résolveur;
- qu’un message est envoyé à ChatGPT;
- que la commande publique `antmux` utilise le wrapper singleton;
- qu’un worker réel démarre correctement;
- que le mutex protège toutes les anciennes voies de démarrage.

Aucun de ces points ne doit être présenté comme `VALIDATED` avant les essais locaux correspondants.

## Jalon suivant

Après le passage `26/26` :

1. tester la résolution réelle de la tuile Nino en lecture seule;
2. tester le singleton avec `-ValidationOnly`;
3. préparer un worker sans `-Launch`;
4. seulement ensuite proposer l’intégration au pont et à la commande publique.
