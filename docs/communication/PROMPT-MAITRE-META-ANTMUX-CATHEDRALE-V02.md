# PROMPT MAÎTRE POUR META — ANTMUX / LINUXIA CATHÉDRALE V02

**Projet :** ANTMUX / LINUXIA  
**Cible :** Meta AI  
**Rôle du document :** mandat complet de conception et de livraison  
**Version :** 1.0  
**Date :** 27 juillet 2026  
**Statut :** prêt à être transmis avec les deux fichiers HTML de référence

---

## PROMPT À DONNER À META

Tu es l’ingénieur principal chargé de construire la prochaine version du prototype ANTMUX / LINUXIA.

Tu recevras deux fichiers HTML en pièces jointes :

1. `Ouvrir-ANTMUX-LINUXIA-META-V01-Cathédrale.html`
2. `ai_studio_code.html`

Tu dois lire et comparer les deux fichiers avant de produire quoi que ce soit.

Le premier fichier possède la meilleure richesse visuelle, la meilleure représentation de la Cathédrale, une navigation très complète et une bonne discipline d’étiquetage entre fonctions réelles, simulées, visuelles et futures. Il est cependant compilé/minifié et difficile à maintenir.

Le second fichier possède un code HTML/CSS/JavaScript beaucoup plus lisible et auditable. Il contient toutefois plusieurs régressions et plusieurs fonctions qui prétendent être actives alors qu’elles sont absentes, automatiques ou simulées.

Ta mission n’est pas de choisir l’un des deux fichiers.

Ta mission est de construire une **V02 originale** qui conserve :

- l’identité visuelle et la richesse fonctionnelle du premier fichier;
- la lisibilité, la simplicité et l’auditabilité du second fichier;
- uniquement les fonctions qui peuvent être honnêtement démontrées dans un navigateur local.

Tu dois livrer un seul fichier complet nommé :

```text
ANTMUX-LINUXIA-META-V02-CATHEDRALE.html
```

---

# 1. OBJECTIF RÉEL DE LA V02

La V02 doit devenir le **contrat visuel exécutable du premier building local**.

Le premier building actif doit contenir exactement :

```text
1 tenant local
1 profil de travailleur actif
1 instance de travailleur
1 bureau actif
1 moteur local déterministe
1 JOB actif à la fois
1 reviewer distinct
1 journal de preuves
```

Les éléments suivants peuvent demeurer visibles comme registres ou architecture cible, mais ils ne doivent pas être présentés comme réellement actifs :

```text
108 profils
108 bureaux
33 moteurs
12 fourmis
33 hamsters
32 + 1 composants
multi-utilisateurs
organisations
synchronisation distante
GitHub
modèles externes
nom de domaine
```

La V02 doit montrer comment le premier building fonctionnera réellement, sans prétendre que l’infrastructure finale existe déjà.

---

# 2. RÈGLE ABSOLUE D’HONNÊTETÉ

Toute fonction visible doit porter exactement une étiquette parmi :

```text
LOCAL_FUNCTIONAL
LOCAL_SIMULATION
VISUAL_DEMO
FUTURE_DISABLED
UNVERIFIED
```

Définitions :

- `LOCAL_FUNCTIONAL` : la fonction exécute réellement ce qu’elle annonce dans ce fichier HTML.
- `LOCAL_SIMULATION` : la logique fonctionne, mais elle simule un composant externe ou futur.
- `VISUAL_DEMO` : représentation visuelle seulement.
- `FUTURE_DISABLED` : fonction volontairement absente et contrôle désactivé.
- `UNVERIFIED` : élément déclaré, mais non testé ou non confirmé.

Interdictions :

- Ne jamais écrire `LOCAL_FUNCTIONAL` si la fonction ne fait qu’afficher un message de succès.
- Ne jamais déclarer une preuve SHA-256 si aucun SHA-256 réel n’a été calculé.
- Ne jamais déclarer un rejeu déterministe si l’état n’a pas réellement été reconstruit depuis le journal.
- Ne jamais déclarer un journal append-only si l’interface peut silencieusement modifier un événement existant.
- Ne jamais déclarer une isolation multi-tenant puisque la V02 ne contient qu’un tenant de démonstration.
- Ne jamais déclarer un moteur IA réel puisque la V02 utilise seulement un moteur déterministe local.
- Ne jamais déclarer qu’un reviewer est indépendant si sa décision est codée automatiquement dans le même flux sans règles vérifiables.

Le panneau **Vérité du prototype** doit être permanent, précis et dérivé de l’état réel du code.

---

# 3. CONTRAINTES TECHNIQUES NON NÉGOCIABLES

Le fichier doit :

- fonctionner hors ligne;
- fonctionner en ouvrant directement le fichier dans un navigateur moderne;
- ne faire aucun appel réseau;
- ne charger aucun CDN;
- ne charger aucune police distante;
- ne contenir aucune clé API;
- ne demander aucune installation;
- ne dépendre d’aucun serveur;
- contenir tout le HTML, CSS et JavaScript dans un seul fichier;
- utiliser du JavaScript lisible, indenté et commenté;
- éviter tout bundle minifié ou code React compilé;
- ne contenir aucun `eval`, `new Function` ou exécution de code importé;
- ne produire aucune erreur dans la console au chargement ou pendant les scénarios prévus.

Tu peux utiliser les API natives du navigateur, notamment :

- IndexedDB;
- Web Crypto API;
- `crypto.randomUUID()`;
- Blob;
- FileReader;
- AbortController;
- `structuredClone()`;
- `TextEncoder`.

Utilise `localStorage` uniquement pour de petites préférences visuelles si nécessaire. L’état du premier building et le journal doivent utiliser IndexedDB ou une couche de stockage clairement structurée.

---

# 4. ARCHITECTURE INTERNE OBLIGATOIRE

Le code doit être divisé logiquement en composants lisibles, même s’ils demeurent dans un seul fichier :

```text
CONFIG
SCHEMAS
REGISTRIES
STORAGE
CRYPTO
EVENT LOG
REDUCER
COMMANDS
PERMISSIONS
ENGINE
EVIDENCE
REVIEWER
RUNTIME
UI RENDERERS
SELF TESTS
BOOTSTRAP
```

Sépare strictement :

```text
commande
événement
projection
preuve
verdict
interface
```

Une commande demande une action.

Un événement décrit ce qui s’est réellement produit.

Le reducer reconstruit l’état uniquement à partir des événements acceptés.

L’interface affiche la projection reconstruite.

Le reviewer vérifie les preuves avant l’état final.

---

# 5. JOURNAL ÉVÉNEMENTIEL RÉEL

Chaque événement doit respecter un schéma similaire à :

```json
{
  "schema_version": "antmux.event.v2",
  "event_id": "uuid",
  "sequence": 1,
  "timestamp_utc": "ISO-8601",
  "tenant_id": "tenant.local.brutus",
  "project_id": "project.local.antmux",
  "profile_id": "worker.software.backend.rest",
  "instance_id": "worker-instance.local.brutus.rest.001",
  "office_id": "office.local.001",
  "job_id": "job uuid ou NONE",
  "actor_type": "USER|GOVERNOR|ENGINE|REVIEWER|SYSTEM",
  "actor_id": "identifiant",
  "event_type": "TYPE_EXPLICITE",
  "payload": {},
  "truth_label": "LOCAL_FUNCTIONAL|LOCAL_SIMULATION",
  "previous_hash": "sha256 précédent ou GENESIS",
  "event_hash": "sha256 calculé"
}
```

Exigences :

- la séquence doit être strictement croissante;
- chaque événement doit chaîner le hash de l’événement précédent;
- `event_hash` doit être calculé avec Web Crypto SHA-256;
- le contenu haché doit être canonique et reproductible;
- un événement déjà enregistré ne doit jamais être modifié;
- toute modification logique doit créer un nouvel événement compensateur;
- l’import doit vérifier le schéma, les séquences et toute la chaîne de hash;
- une chaîne invalide doit être rejetée sans remplacer l’état courant;
- l’utilisateur doit voir la raison précise du rejet.

Le journal doit rester inspectable dans l’interface.

---

# 6. REPLAY ET PROJECTION RÉELS

Crée un reducer pur :

```text
projection = reduce(initialState, acceptedEvents)
```

La fonction de replay doit :

1. repartir d’un état initial vide;
2. relire les événements dans l’ordre;
3. valider chaque transition;
4. reconstruire le JOB, le bureau, la fourmi courante, les permissions, les preuves et le verdict;
5. produire une nouvelle empreinte de projection;
6. comparer cette empreinte avec celle de la projection courante;
7. afficher `PROJECTION_MATCH` ou `PROJECTION_DIVERGENCE` selon le résultat réel.

Il est interdit de simplement afficher `PROJECTION_MATCH` sans calcul.

Ajoute un bouton de test permettant de provoquer volontairement une divergence dans une copie temporaire, sans corrompre l’état sauvegardé.

---

# 7. CYCLE DU JOB

Le cycle doit être une machine à états contrôlée.

États minimaux :

```text
DRAFT
STRUCTURED
PENDING_RISK_REVIEW
PENDING_AUTHORIZATION
AUTHORIZED
RUNNING
PAUSED
INTERRUPTED
UNDER_REVIEW
REJECTED
NEEDS_MORE_EVIDENCE
COMPLETED
FAILED
```

Transitions interdites :

- `DRAFT → RUNNING`
- `STRUCTURED → AUTHORIZED` sans action explicite de l’utilisateur;
- `RUNNING → COMPLETED` sans reviewer;
- `REJECTED → COMPLETED` sans nouveau cycle de correction;
- toute exécution si la permission effective est absente.

L’application ne doit jamais autoriser automatiquement un JOB.

Flux obligatoire :

```text
intention brute
→ intention structurée
→ JOB DRAFT
→ évaluation de risque déterministe
→ permissions proposées
→ confirmation explicite de Brutus
→ AUTHORIZED
→ exécution
→ preuves
→ UNDER_REVIEW
→ verdict
→ COMPLETED ou REJECTED ou NEEDS_MORE_EVIDENCE
```

Le moteur déterministe peut simuler une transformation locale, mais le statut doit demeurer `LOCAL_SIMULATION` pour le travail produit.

---

# 8. DOUZE FOURMIS PILOTES

Conserve les douze fourmis comme étapes du cycle, mais transforme-les en transitions vérifiables plutôt qu’en animations automatiques.

Chaque fourmi doit posséder :

```text
id
nom
mission
préconditions
entrée
sortie attendue
événements autorisés
preuves attendues
état
cause d’échec
```

Les douze étapes recommandées :

1. analyser l’intention;
2. vérifier les invariants;
3. sélectionner le tenant;
4. sélectionner le profil;
5. ouvrir l’instance;
6. réveiller le bureau;
7. définir le JOB;
8. calculer les permissions et demander l’autorisation;
9. louer le moteur et exécuter;
10. produire et sceller les preuves;
11. réviser contradictoirement;
12. rejouer, vérifier et finaliser.

Une fourmi ne peut devenir `VALIDATED` que si ses préconditions et ses preuves sont réellement présentes.

Le mode automatique peut exister, mais il doit utiliser exactement les mêmes commandes et validations que le mode pas-à-pas.

---

# 9. PERMISSIONS

Implémente réellement la règle conceptuelle :

```text
permissions_effectives = intersection(
  profil,
  instance,
  tenant,
  projet,
  bureau,
  compétence,
  JOB,
  fourmi,
  appareil,
  approbation,
  temps
)
```

Dans la V02, utilise un sous-ensemble déterministe et compréhensible :

```text
EXECUTE_LOCAL_SIMULATOR
READ_LOCAL_STATE
WRITE_LOCAL_EVENT
EXPORT_STATE
IMPORT_VALIDATED_STATE
PROMOTE_LOCAL_LESSON
```

Les permissions suivantes doivent rester absentes et marquées `FUTURE_DISABLED` :

```text
NETWORK_ACCESS
SYSTEM_COMMAND_EXECUTION
GITHUB_WRITE
REMOTE_MODEL_CALL
CROSS_TENANT_READ
```

Le refus par défaut est obligatoire.

Une case visuelle ne doit jamais suffire à accorder une permission interdite. Les contrôles futurs doivent être désactivés et expliqués.

---

# 10. MOTEUR LOCAL

Le seul moteur actif est :

```text
engine.local-deterministic.001
```

Il doit :

- fonctionner sans réseau;
- accepter une commande structurée;
- produire une sortie déterministe;
- pouvoir échouer selon un scénario de test;
- produire une trace d’entrée et de sortie;
- respecter un AbortSignal;
- ne posséder aucune mémoire durable indépendante;
- être loué temporairement au bureau;
- libérer son bail après fin, échec ou interruption.

Les 32 autres emplacements moteurs peuvent être affichés comme `UNVERIFIED` ou `FUTURE_DISABLED`, jamais comme actifs.

---

# 11. INTERRUPTION, PAUSE ET REPRISE

La V02 doit corriger le problème des minuteries qui continuent après une interruption.

Exigences :

- toutes les tâches programmées doivent être enregistrées;
- toutes doivent être annulables;
- l’interruption doit annuler immédiatement les timers, promesses contrôlées et opérations moteur;
- aucun événement `VALIDATED` ne doit apparaître après `INTERRUPTED`, sauf événement explicite de reprise;
- la pause ne doit pas terminer une étape en arrière-plan;
- la reprise doit repartir de la dernière transition durable valide;
- un rechargement du navigateur doit reconstruire le même état depuis le journal;
- le bail moteur doit être libéré ou marqué expiré après crash simulé.

Ajoute un scénario automatisé :

```text
lancer
→ interrompre pendant ANT-009
→ recharger la page
→ vérifier l’état INTERRUPTED
→ reprendre
→ terminer
→ replay identique
```

---

# 12. PREUVES ET REVIEWER

Les preuves ne doivent jamais être des chaînes fixes prétendant être des hashes.

Un paquet de preuve doit contenir au minimum :

```json
{
  "proof_id": "uuid",
  "job_id": "uuid",
  "ant_id": "ANT-010",
  "input_hash": "sha256 réel",
  "output_hash": "sha256 réel",
  "event_range": [1, 12],
  "checks": [],
  "created_at": "ISO-8601",
  "truth_label": "LOCAL_FUNCTIONAL"
}
```

Le reviewer doit être une logique séparée qui reçoit :

- le JOB;
- les critères d’acceptation;
- la projection;
- les preuves;
- les anomalies;
- la chaîne événementielle.

Verdicts :

```text
ACCEPT
REJECT
NEEDS_MORE_EVIDENCE
```

Règles minimales :

- preuve absente → `NEEDS_MORE_EVIDENCE`;
- hash invalide → `REJECT`;
- séquence invalide → `REJECT`;
- permission absente → `REJECT`;
- interruption non reprise → `REJECT`;
- toutes les conditions satisfaites → `ACCEPT`.

Seul `ACCEPT` peut produire `JOB_COMPLETED`.

Le reviewer ne doit pas être présenté comme une IA. Il s’agit d’un reviewer déterministe local dans cette version.

---

# 13. STOCKAGE ET IMPORT/EXPORT

Le stockage doit conserver au minimum :

- manifest de version;
- tenant;
- profil actif;
- instance active;
- bureau actif;
- registre des bureaux dormants;
- registre des moteurs;
- JOB;
- journal événementiel;
- preuves;
- reviewer verdicts;
- permissions;
- état des fourmis;
- Bermuda;
- préférences d’interface.

L’export doit produire un seul JSON complet avec :

```text
format_version
exported_at
manifest
registries
snapshot indicatif
journal source de vérité
proofs
projection_hash
```

La projection exportée n’est pas la source de vérité : elle doit pouvoir être reconstruite depuis le journal.

L’import doit :

- limiter la taille du fichier;
- parser sans exécuter;
- valider une liste blanche de propriétés;
- vérifier les types;
- vérifier les séquences;
- vérifier les hashes;
- effectuer un replay temporaire;
- montrer un rapport de validation;
- demander confirmation avant remplacement;
- conserver l’état courant si l’import échoue.

Aucune donnée importée ne doit être injectée avec `innerHTML`.

Utilise `textContent`, `createElement()` et des attributs contrôlés pour toute donnée variable.

---

# 14. INTERFACE VISUELLE

Conserve l’identité Cathédrale :

- fond sombre bleu-pierre;
- or;
- cyan;
- rouge pour les refus;
- vert pour les validations;
- représentation verticale de 12 étages;
- 9 bureaux par étage;
- sensation de ville de travailleurs;
- mouvements sobres et compréhensibles;
- fourmis visibles pendant les transitions;
- état du JOB toujours visible;
- bureau et moteur actifs toujours visibles;
- panneau de vérité accessible en permanence.

Conserve les 22 espaces seulement s’ils sont tous utiles et fonctionnels.

Chaque bouton doit respecter l’une des règles suivantes :

1. il exécute une vraie fonction;
2. il est désactivé avec `FUTURE_DISABLED` et une explication visible.

Aucun bouton ne doit appeler une méthode inexistante.

Ajoute une vérification automatique au démarrage qui compare tous les attributs `onclick` ou événements liés avec les fonctions réellement disponibles. Toute fonction manquante doit apparaître comme échec dans les auto-tests.

---

# 15. ACCESSIBILITÉ

La V02 doit inclure :

- navigation clavier;
- focus visible;
- contrastes suffisants;
- textes redimensionnables;
- `prefers-reduced-motion` respecté automatiquement;
- bouton de pause globale des animations;
- aucun clignotement dangereux;
- boutons avec libellés explicites;
- régions principales sémantiques;
- attributs ARIA lorsque nécessaires;
- état non communiqué uniquement par couleur.

N’affiche pas une case « WCAG » cochée si aucun contrôle réel n’est associé.

---

# 16. AUTO-TESTS OBLIGATOIRES

Crée un panneau d’auto-tests exécutables avec résultat `PASS` ou `FAIL` et explication.

Tests minimaux :

1. chargement sans erreur;
2. tous les boutons liés à une fonction existante;
3. refus d’exécution sans JOB;
4. refus d’exécution sans autorisation explicite;
5. calcul de hash SHA-256 réel;
6. chaîne événementielle valide;
7. rejet d’un événement doublon;
8. rejet d’un trou de séquence;
9. rejet d’un import au hash altéré;
10. import valide dans un espace temporaire;
11. replay produisant le même hash de projection;
12. divergence détectée sur projection altérée;
13. interruption annulant toutes les opérations en attente;
14. aucune validation après interruption;
15. reprise après rechargement;
16. reviewer bloquant une preuve absente;
17. reviewer rejetant une permission absente;
18. état complet persistant après rechargement;
19. aucune requête réseau;
20. aucune utilisation non sécurisée de données importées dans `innerHTML`.

Le rapport final doit être dérivé des résultats réels de ces tests et du journal.

---

# 17. DÉFAUTS DES VERSIONS PRÉCÉDENTES À CORRIGER EXPLICITEMENT

Tu dois corriger tous les défauts suivants :

- méthodes appelées mais inexistantes;
- auto-autorisation du JOB;
- risque toujours fixé à `FAIBLE`;
- permissions seulement décoratives;
- preuves statiques;
- faux hashes;
- reviewer toujours positif;
- replay qui ne reconstruit rien;
- projection déclarée valide sans comparaison;
- journal modifiable par import non validé;
- import JSON trop permissif;
- utilisation de `innerHTML` avec données variables;
- interruption qui laisse des timers actifs;
- pause qui permet à une étape de finir en arrière-plan;
- persistance partielle;
- état des bureaux perdu au rechargement;
- fourmi courante perdue au rechargement;
- permissions perdues au rechargement;
- export limité au journal seulement;
- fonctions futures présentées comme réelles;
- affirmations « zéro fuite » non démontrables;
- confusion entre registre des 108 bureaux et 108 bureaux réellement opérationnels.

---

# 18. CE QU’IL NE FAUT PAS FAIRE

Ne fais pas :

- une nouvelle démonstration purement décorative;
- un fichier minifié;
- un framework lourd;
- un serveur fictif;
- un faux appel IA;
- un bouton qui affiche seulement `SUCCESS`;
- un hash écrit à la main;
- une autorisation automatique;
- une multiplication de fonctions supplémentaires;
- une simulation de multi-utilisateurs;
- une connexion réseau cachée;
- une télémétrie;
- un système de comptes;
- un domaine;
- une intégration GitHub;
- une exécution système;
- une prétention de production.

Ne construis pas les 108 bureaux réels ni les 33 moteurs réels dans cette version.

La priorité est le premier building vérifiable.

---

# 19. CRITÈRES D’ACCEPTATION FINAUX

La livraison est acceptée seulement si :

```text
[ ] le fichier s’ouvre localement
[ ] aucune dépendance réseau
[ ] aucune erreur console dans les scénarios normaux
[ ] aucun bouton cassé
[ ] aucune méthode inexistante
[ ] aucun JOB auto-autorisé
[ ] une autorisation explicite est obligatoire
[ ] le journal possède une chaîne SHA-256 réelle
[ ] le replay reconstruit réellement la projection
[ ] la divergence est détectable
[ ] l’interruption annule toutes les tâches
[ ] le rechargement restaure l’état
[ ] le reviewer peut empêcher COMPLETED
[ ] les preuves sont calculées et non décoratives
[ ] les imports invalides sont rejetés
[ ] les données importées ne peuvent pas injecter du HTML
[ ] toutes les étiquettes de vérité correspondent au code
[ ] le premier building est compréhensible visuellement
[ ] les 108 bureaux et 33 moteurs sont clairement présentés comme registres cibles
[ ] le panneau d’auto-tests montre les résultats réels
[ ] le rapport final est dérivé du journal et des tests
```

---

# 20. FORMAT DE TA RÉPONSE

Retourne d’abord le fichier complet dans un seul bloc :

```html
<!DOCTYPE html>
...
</html>
```

Règles de livraison :

- aucun morceau omis;
- aucun `...`;
- aucun « reste inchangé »;
- aucun pseudo-code;
- aucune dépendance à un second fichier;
- aucun code tronqué volontairement;
- aucun lien externe;
- aucun commentaire disant qu’une fonction sera ajoutée plus tard si le bouton est actif.

Après le bloc HTML, ajoute seulement un tableau compact contenant :

```text
fonction
étiquette de vérité
preuve d’implémentation
auto-test associé
```

Puis ajoute la liste des limites réelles restantes.

Si la place disponible menace la complétude, priorise le fichier HTML complet et réduis l’explication. Ne sacrifie jamais le code complet pour une longue introduction.

---

# 21. VERDICT ATTENDU

Le résultat attendu n’est pas encore la plateforme finale ANTMUX.

Le résultat attendu est :

> une Cathédrale V02 visuellement forte, localement exécutable, honnêtement étiquetée, maintenable, persistante, rejouable et capable de prouver le cycle minimal du premier building sans inventer les capacités futures.
