# Jules — veilleur du dossier de résumés

## But

Le veilleur transforme le dossier local suivant en source d’événements :

```text
<racine-Antmux>\communication\resumes\
```

Lorsqu’un nouveau fichier Markdown apparaît, le veilleur appelle immédiatement le module Jules de publication.

```text
nouveau résumé local
  → détection du fichier
  → validation Jules
  → classement par projet et job
  → commit Git
  → push vers Topbrutus/Antmux
```

## Règles

- seuls les nouveaux fichiers `.md` du dossier racine sont observés;
- `LATEST.md` est ignoré pour éviter une publication en double;
- les sous-dossiers ne sont pas surveillés;
- deux événements rapprochés pour le même fichier sont fusionnés;
- le veilleur ne fabrique pas le résumé;
- le module `Send-AntmuxSummary.ps1` reste responsable de la validation et du push;
- le projet par défaut est `PROJECT-000000`;
- le veilleur reste actif tant que sa fenêtre PowerShell demeure ouverte;
- `Ctrl+C` arrête le veilleur.

## Installation

```powershell
Invoke-WebRequest -UseBasicParsing `
  "https://raw.githubusercontent.com/Topbrutus/Antmux/main/INSTALL-JULES-SUMMARY-WATCHER.ps1" `
  -OutFile "D:\INSTALL-JULES-SUMMARY-WATCHER.ps1"

Set-ExecutionPolicy -Scope Process Bypass -Force
& "D:\INSTALL-JULES-SUMMARY-WATCHER.ps1"
```

## Démarrage

```powershell
& "D:\jules-watch.cmd"
```

Résultat attendu :

```text
JULES SUMMARY WATCHER ACTIVE
Folder  : D:\communication\resumes
Project : PROJECT-000000
```

## Test contrôlé

1. Démarrer `D:\jules-watch.cmd`.
2. Produire un nouveau résumé complet dans `D:\communication\resumes\`.
3. Ne pas utiliser `LATEST.md` comme fichier de test.
4. Vérifier que Jules affiche le fichier détecté.
5. Vérifier ensuite la présence du résumé dans GitHub sous :

```text
communication/resumes/PROJECT-000000/
```

## Portabilité

Le lanceur `jules-watch.cmd` déduit la lettre du disque depuis son propre emplacement. Le disque peut donc recevoir une autre lettre sur une autre machine, à condition :

- que le volume conserve le nom `Antmux`;
- que Git soit installé et authentifié sur la machine;
- que le module Jules soit présent sur le disque.

## Étape ultérieure

Le démarrage du veilleur pourra être intégré au lancement général d’Antmux. Cette intégration n’est pas encore activée afin de tester le veilleur séparément avant de le rendre automatique au démarrage.
