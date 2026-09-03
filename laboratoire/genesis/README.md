# ANTMUX — GENESIS VISION CENTER

## Cible publique

`https://antmux.com/laboratoire/genesis/`

Dépôt public :

`Topbrutus/Antmux`

Périmètre de cette interface :

`laboratoire/genesis/`

Les zones `/generator/`, `/index.html`, `/styles.css`, `/app.js` et le noyau privé `Topbrutus/seedgenesis` restent séparés.

---

## Statut

`LAB-004`

Phase actuelle :

`VISION_CENTER_V2_DEMO_READY`

Contrat courant :

`PUBLIC-CONTRACT-v2.md` — `2.0.0-draft`

Snapshot canonique :

`demo/genesis-demo-v2.json`

Mode :

`DEMO / SYNTHETIC DATA`

Aucune donnée privée Genesis n'est lue par le navigateur.

---

## Mission

Genesis Vision Center est l'observatoire public associé au programme Genesis.

Il ne constitue pas Genesis lui-même.

Il doit montrer uniquement ce qui peut être publié et défendu publiquement, avec séparation stricte entre :

`MEASURED != DERIVED != INTERPRETED != HYPOTHESIS != UNKNOWN`

Il doit aussi conserver visuellement les rejets, échecs et états inconnus lorsqu'ils font partie du raisonnement expérimental.

---

## Architecture v2 affichée

### 1. ROOT / identité minimale

La page expose un bloc public de démonstration pour identité de la graine, statut ROOT, version publique, digest public et règle de continuité.

En mode DEMO, ces valeurs sont synthétiques et ne sont pas des copies du noyau privé.

### 2. GENESIS-002 / continuité

La page peut représenter cycle, checkpoint précédent, checkpoint courant, lien parent, identité ROOT, acceptés, rejetés et retour.

Principe :

`même ROOT -> cycle suivant -> lien parent -> acceptés/rejetés séparés -> retour`

### 3. GENESIS-003 / méta-apprentissage

La page peut représenter hypothèses concurrentes, incertitude, prochain test recommandé, justification et état C041–C060.

Principe public :

`choisir le prochain test qui réduit le plus l'incertitude`

Une recommandation affichée ne constitue pas une preuve d'autonomie.

### 4. Pyramide / terrain d'entraînement

Le cockpit fournit une zone dédiée aux données du terrain d'entraînement en conservant leur classe :

- `MEASURED`
- `DERIVED`
- `INTERPRETED`
- `HYPOTHESIS`
- `UNKNOWN`

Le mode DEMO n'utilise aucune valeur réelle de la pyramide. Il illustre seulement la discipline de classification.

Le cockpit ne doit jamais présenter un modèle, une valeur dérivée ou une interprétation comme mesure brute.

### 5. GESIS / observatoire

Le cockpit peut représenter publiquement état FFT, dernier export public, nombre de pics, épisodes, état Block Score et règle scientifique.

Règle obligatoire :

`MESURE != INTERPRÉTATION`

Une proximité fréquentielle ou un score ne devient pas automatiquement une découverte.

---

## Cycle public

`SOURCE`
→ `DESCENTE`
→ `ZÉRO`
→ `FORMATION`
→ `EXPLORATION`
→ `VALIDATION`
→ `RETOUR SOURCE`

Ce cycle est une représentation logicielle du programme Genesis.

Il ne constitue pas une affirmation sur l'intention historique de la Grande Pyramide.

---

## Frontière de confiance

`PRIVATE GENESIS`
→ `GENESIS PUBLIC ADAPTER`
→ `PUBLIC CONTRACT v2`
→ `SNAPSHOT / READ-ONLY API`
→ `GENESIS VISION CENTER`

Principe :

`DENY BY DEFAULT`

Puis :

`EXPLICIT WHITELIST -> PUBLIC`

Le navigateur public ne doit jamais accéder directement au dépôt privé, au filesystem privé, aux secrets, aux seeds privées, aux audits privés, aux sorties oracle, aux credentials ou à la topologie serveur privée.

---

## Modes de données

### DEMO

Données artificielles pour construire et vérifier l'interface.

Affichage obligatoire : `DEMO / SYNTHETIC DATA`

### SNAPSHOT

Publication publique figée produite par un processus explicitement autorisé.

### LIVE_READ_ONLY

Future vue publique en lecture seule.

Ce mode reste bloqué tant que le Genesis Public Adapter n'est pas validé.

---

## Gates de publication

`CONTRAT -> ADAPTER -> SNAPSHOT -> LIVE_READ_ONLY`

Le contrat v2 est prêt pour la démonstration.

L'Adapter public réel n'est pas connecté par ce changement.

---

## Relation avec le générateur Antmux

Le Vision Center affiche un lien de navigation vers `/generator/`.

Le générateur reste un produit séparé.

Cette évolution ne modifie aucun fichier du générateur et ne crée aucun couplage automatique avec le noyau privé Genesis.

---

## Tests

Validation historique v1 :

`node laboratoire/genesis/validate-demo.mjs`

Tests adversariaux v1 :

`node laboratoire/genesis/test-validator.mjs`

Validation v2 :

`node laboratoire/genesis/validate-public-v2.mjs`

Tests adversariaux v2 :

`node laboratoire/genesis/test-public-v2.mjs`

Smoke test HTTP :

`node laboratoire/genesis/smoke-cockpit.mjs`

Test Chromium desktop/mobile :

`node laboratoire/genesis/browser-cockpit.mjs`

Bundle public :

`node laboratoire/genesis/build-public-bundle.mjs`

Le workflow GitHub Actions exécute ces validations avant toute décision de déploiement.

---

## Déploiement

Le déploiement VPS reste volontairement séparé du développement.

La route cible est `/laboratoire/genesis/`.

Une branche ou une PR validée doit être revue avant intégration à `main`.

Le serveur ne doit pas être modifié par les tests de développement.

---

## Règle scientifique finale

Le Centre de Vision doit rendre visible ce qui est observé, calculé, interprété, supposé, échoué, rejeté, validé ou encore inconnu.

Il ne doit jamais fabriquer l'apparence d'une preuve.

`UNKNOWN / PENDING > INVENTED`
