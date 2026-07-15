# Pont ChatGPT — écran 3

## But

Le pont transmet automatiquement un résumé Antmux à l’application ChatGPT après une publication GitHub réussie par Jules.

```text
nouveau résumé
  ↓
Jules valide, commit et pousse sur GitHub
  ↓
pont ChatGPT
  ↓
fenêtre ChatGPT unique sur \\.\DISPLAY3
  ↓
Ctrl+V
  ↓
attente de sécurité
  ↓
Entrée
```

## Fichiers

```text
modules/chatgpt-bridge/ChatGPT.Bridge.psm1
modules/chatgpt-bridge/Send-AntmuxToChatGPT.ps1
config/chatgpt-bridge.json
INSTALL-CHATGPT-BRIDGE.ps1
modules/jules/Watch-AntmuxSummaries.ps1
```

## Verrous de sécurité

Le pont refuse l’envoi lorsque :

- aucune fenêtre dont le titre contient `ChatGPT` n’est trouvée sur `\\.\DISPLAY3`;
- plusieurs fenêtres ChatGPT sont présentes sur cet écran;
- Windows refuse d’activer la fenêtre choisie;
- le titre, l’écran ou le premier plan changent avant le collage;
- le titre, l’écran ou le premier plan changent pendant la pause précédant Entrée;
- le même contenu a déjà été envoyé avec succès.

Le pont ne clique pas dans la zone de saisie. La conversation voulue doit être ouverte, et le curseur doit déjà se trouver dans sa zone de message.

## Portabilité

Tous les chemins sont relatifs à la racine du volume nommé `Antmux`. Le disque peut changer de lettre sur une autre machine.

La cible graphique reste le périphérique Windows :

```text
\\.\DISPLAY3
```

Si la disposition des écrans change, modifier `display_device` dans :

```text
<racine-Antmux>\config\chatgpt-bridge.json
```

## Installation

```powershell
Invoke-WebRequest -UseBasicParsing `
  "https://raw.githubusercontent.com/Topbrutus/Antmux/main/INSTALL-CHATGPT-BRIDGE.ps1" `
  -OutFile "D:\INSTALL-CHATGPT-BRIDGE.ps1"

Set-ExecutionPolicy -Scope Process Bypass -Force
& "D:\INSTALL-CHATGPT-BRIDGE.ps1"
```

## Test sûr sans collage

Placer l’application ChatGPT sur l’écran 3, ouvrir la conversation voulue, puis lancer :

```powershell
& "D:\modules\chatgpt-bridge\Send-AntmuxToChatGPT.ps1" `
  -SummaryPath "D:\communication\resumes\JOB-000001-TEST.md" `
  -TestOnly
```

Résultat attendu :

```text
Status        : test-only
WindowTitle   : ...ChatGPT...
DisplayDevice : \\.\DISPLAY3
```

## Test avec collage, sans Entrée

```powershell
& "D:\modules\chatgpt-bridge\Send-AntmuxToChatGPT.ps1" `
  -SummaryPath "D:\communication\resumes\JOB-000001-TEST.md" `
  -NoEnter
```

Le texte doit apparaître dans ChatGPT sans être envoyé.

## Fonctionnement automatique

Après l’installation, redémarrer le veilleur Jules :

```powershell
& "D:\jules-watch.cmd"
```

Le veilleur mis à jour publie d’abord le résumé sur GitHub. Seulement après réussite, il appelle le pont ChatGPT. Le pont colle le résumé, attend trois secondes, revérifie la fenêtre, puis appuie sur Entrée.

## Journaux et anti-doublon

```text
communication/chatgpt-bridge/events.jsonl
communication/chatgpt-bridge/sent-hashes.txt
```

`events.jsonl` enregistre les envois et les blocages. `sent-hashes.txt` contient les empreintes SHA-256 des résumés déjà envoyés avec succès.

## Limite assumée

C’est une automatisation d’interface Windows. Elle dépend donc de l’application ChatGPT ouverte, de la session Windows déverrouillée et du curseur déjà placé dans la zone de message. Elle ne remplace pas une API officielle.
