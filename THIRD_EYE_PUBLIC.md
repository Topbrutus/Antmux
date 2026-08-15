# Third Eye — Surface publique Antmux

## 2026-08-15 — Résultat — Rob

**Dépôt :** `Topbrutus/Antmux`  
**Branche :** `main`

### Intention de référence

La décision de séparer strictement la surface publique de l’application complète a été enregistrée dans `THIRD_EYE_WEB.md` avant les modifications.

### Frontière créée

- `PUBLIC_SCOPE.md` définit ce qui peut être publié et ce qui doit rester hors du dépôt.
- `NOTICE.md` conserve le dépôt sans licence open source générale par défaut et documente les droits réservés sur l’expression et l’implémentation, sans revendiquer les mathématiques abstraites comme telles.
- `.gitignore` exclut par défaut les secrets, clés, certificats, données privées et répertoires associés au serveur dédié ou à l’infrastructure privée.

### Vérificateur public

Deux fichiers ont été ajoutés dans la surface GitHub Pages :

- `generator/verify.html`
- `generator/verifier.js`

Le vérificateur :

- fonctionne entièrement dans le navigateur ;
- ne contacte aucun serveur Antmux ;
- ne contient aucune implémentation du serveur dédié ;
- recalcule les identités arithmétiques, les 273 phases distinctes et les propriétés principales du graphe public ;
- produit un résultat PASS/FAIL ;
- permet d’exporter un rapport JSON.

### Vérifications

Recalcul local indépendant du vérificateur :

- `28/28` contrôles : PASS ;
- phases distinctes : `273` ;
- degré du graphe : `42` ;
- arêtes : `1029` ;
- uns de la matrice : `2058` ;
- zéros : `343` ;
- lambda : `35` ;
- mu : `42` ;
- NEO public recalculé : `571429/999999`.

GitHub Actions :

- Checkout : PASS ;
- validation syntaxique JavaScript des quatre moteurs publics : PASS ;
- configuration GitHub Pages : ÉCHEC, car GitHub Pages n’est pas encore activé/configuré comme source de déploiement pour le dépôt ;
- aucun échec de syntaxe du code public détecté.

### Commits

- intention frontière publique : `a255d7c3ee76b80da04e69fa4f2104059b1c7be3`
- frontière publique : `06952bfd79867936d413b75007783d5da7e2b5f1`
- avis de droits : `6941625fb8641c8ed4ee1673a87dd9dbdde33e63`
- exclusions privées : `101885b07ca30a5cabaf5f55c21d662a5fb2a4af`
- interface du vérificateur : `db9411104ea2cc70e3d1bc33c171d731a64ab05b`
- moteur du vérificateur : `a6c73170ed1862bd8b2aaf7bda7c5973e83a955f`
- lien générateur → vérificateur : `500aacb722a217a7e8c15624bbc2b4dcccca6763`
- validation CI du vérificateur : `e74b3d6d2789d92cbbbfc0d6b3e11563b81230c5`

### Statut

**OK — surface publique séparée et vérifiable. Aucun composant du serveur dédié n’a été ajouté.**

### Reprise

1. Activer GitHub Pages avec **GitHub Actions** comme source.
2. Vérifier publiquement le générateur et `verify.html`.
3. Toute future intégration de fournisseur, mémoire privée, API, serveur ou orchestration doit être développée hors du dépôt public, puis exposée seulement par une interface minimale et documentée.
4. Avant toute nouvelle publication technique majeure, vérifier si elle révèle un mécanisme que l’on souhaite garder privé ou éventuellement évaluer pour une protection de propriété intellectuelle.

**Signé : Rob**
