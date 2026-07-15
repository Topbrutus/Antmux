# Correction Antmux — Windows PowerShell 5.1

## Erreur observée

```text
La propriété « OSArchitecture » est introuvable dans cet objet.
FullyQualifiedErrorId : PropertyNotFoundStrict
```

Puis :

```text
antmux : Le terme « antmux » n'est pas reconnu
```

## Cause

La première version de `INSTALL-ANTMUX-D.ps1` utilisait :

```powershell
[System.Runtime.InteropServices.RuntimeInformation]::OSArchitecture
```

Cette propriété n'est pas disponible dans l'environnement Windows PowerShell 5.1 utilisé sur la machine de Brutus. L'installation s'arrêtait donc avant le téléchargement de Node.js et avant la création de `D:\antmux.cmd`.

La commande `antmux` absente était une conséquence directe de cet arrêt anticipé, et non une deuxième panne indépendante.

## Correction appliquée

Le script détecte maintenant l'architecture avec les variables Windows compatibles PowerShell 5.1 :

- `PROCESSOR_ARCHITEW6432`;
- `PROCESSOR_ARCHITECTURE`;
- repli par `Get-CimInstance` ou `Get-WmiObject`.

Le script reconnaît :

- Windows x64 → archive Node.js `win-x64-zip`;
- Windows ARM64 → archive Node.js `win-arm64-zip`.

La correction ajoute également :

- `-UseBasicParsing` pour les téléchargements sous Windows PowerShell 5.1;
- redirection de `HOME`, `APPDATA`, `LOCALAPPDATA`, `TEMP`, `TMP`, caches npm et configuration npm vers `D:\`;
- détection dynamique du point d'entrée du paquet `@openai/codex`;
- conservation de la commande publique `D:\antmux.cmd`.

## Reprise de l'installation

Depuis PowerShell :

```powershell
Remove-Item "D:\INSTALL-ANTMUX-D.ps1" -Force -ErrorAction SilentlyContinue

Invoke-WebRequest -UseBasicParsing `
  "https://raw.githubusercontent.com/Topbrutus/Antmux/main/INSTALL-ANTMUX-D.ps1" `
  -OutFile "D:\INSTALL-ANTMUX-D.ps1"

Set-ExecutionPolicy -Scope Process Bypass -Force
& "D:\INSTALL-ANTMUX-D.ps1"
```

Après l'affichage `INSTALLATION TERMINÉE`, vérifier :

```powershell
& "D:\antmux.cmd" --version
antmux
```

## État des restes du premier essai

Le premier essai s'est interrompu avant l'installation de Node.js et du paquet OpenAI. Les dossiers techniques cachés éventuellement créés à la racine de `D:\` sont réutilisés sans danger par le script corrigé. Il n'est pas nécessaire de les supprimer avant la reprise.
