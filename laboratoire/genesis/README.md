# ANTMUX — GENESIS VISION CENTER

## Statut

`LAB-004`

Phase actuelle :

`DEMO_PIPELINE_READY`

État démontré dans cette phase :

* cockpit public DEMO présent sous `/laboratoire/genesis/` ;
* données explicitement marquées `DEMO / SYNTHETIC DATA` ;
* contrat public versionné ;
* validation du snapshot DEMO et tests adversariaux présents ;
* smoke test HTTP présent ;
* rendu automatisé dans un navigateur Chromium réel validé en CI ;
* captures de preuve desktop et mobile produites par la CI ;
* construction automatisée d'un bundle public avec manifeste SHA-256.

Le test navigateur vérifie notamment le rendu du cockpit, la bannière DEMO, les valeurs publiques attendues, l'absence d'état fatal, l'absence d'erreurs JavaScript/console et l'absence de débordement horizontal sur les deux viewports testés.

Il s'agit d'un test de rendu navigateur réel avec captures de preuve, et non encore d'un test de régression visuelle pixel-à-pixel avec image de référence figée.

Limites actuelles :

* aucun déploiement sur `antmux.com` n'est déclaré par ce document ;
* aucune connexion au noyau privé Genesis n'est active ;
* aucune donnée Genesis privée ou réelle n'est publiée par le cockpit DEMO.

---

## Mission

Genesis Vision Center est l'instrument public de visualisation scientifique associé au programme expérimental Genesis.

Son objectif est de permettre de voir, comparer et auditer les états publiables de Genesis sans exposer le noyau privé.

Le Centre de Vision ne constitue pas Genesis lui-même.

Il constitue une interface d'observation séparée.

---

## Architecture de confiance

Architecture cible :

`PRIVATE GENESIS`
→ `GENESIS PUBLIC ADAPTER`
→ `PUBLIC CONTRACT`
→ `READ-ONLY API`
→ `GENESIS VISION CENTER`

Chaque frontière doit rester explicite.

---

## Frontière privée

Le dépôt privé :

`Topbrutus/seedgenesis`

reste une source privée.

Le navigateur public ne doit jamais accéder directement :

* au dépôt privé ;
* au filesystem privé ;
* à une base privée ;
* aux variables d'environnement ;
* aux secrets ;
* aux seeds privées ;
* aux programmes cachés ;
* aux audits privés ;
* aux sorties oracle privées ;
* aux credentials ;
* à la topologie serveur privée.

---

## Genesis Public Adapter

Une future couche appelée :

`Genesis Public Adapter`

devra constituer la seule frontière autorisée entre le noyau privé et la vue publique.

Principe obligatoire :

`DENY BY DEFAULT`

Puis :

`EXPLICIT WHITELIST -> PUBLIC`

Tout champ non explicitement autorisé reste privé.

L'absence d'une interdiction explicite ne constitue jamais une autorisation de publication.

---

## Lecture seule

Le flux public initial est strictement :

`Genesis -> Adapter -> API -> Vision Center`

Jamais :

`Vision Center -> Genesis`

Le navigateur public ne possède aucune capacité d'écriture vers le noyau Genesis.

Toute future expérimentation publique devra utiliser une frontière séparée, validée et sandboxée.

---

## Modes de données

Le Centre de Vision devra distinguer au minimum :

### DEMO

Données artificielles destinées au développement de l'interface.

Affichage obligatoire :

`DEMO / SYNTHETIC DATA`

### SNAPSHOT

Capture publique figée provenant d'un export autorisé.

### LIVE_READ_ONLY

État public obtenu par une interface de lecture seule.

Le mode :

`LIVE_READ_ONLY`

ne pourra être utilisé qu'après validation du Genesis Public Adapter.

---

## Règle de vérité visuelle

Une animation n'est pas une preuve d'activité du noyau Genesis.

Une interface animée alimentée par des données de démonstration doit rester explicitement marquée comme démonstration.

Les mots :

* vivant ;
* autonome ;
* conscient ;
* actif ;
* auto-évolutif ;

ne doivent pas être utilisés comme conclusions scientifiques sans critères opérationnels et preuves correspondantes.

---

## Provenance

Chaque donnée réelle affichée ultérieurement devra pouvoir fournir au minimum :

* identifiant ;
* type ;
* statut ;
* origine ;
* date ou génération ;
* transformation éventuelle ;
* preuve ou référence ;
* niveau d'intégrité ;
* mode de publication.

Une valeur sans provenance suffisante ne doit pas apparaître comme résultat scientifique validé.

---

## Séparation des couches

Le Centre de Vision devra distinguer visuellement :

1. données observées ;
2. calculs dérivés ;
3. hypothèses ;
4. prédictions ;
5. résultats de tests ;
6. échecs ;
7. réplications ;
8. corrections.

Ces catégories ne doivent jamais être fusionnées silencieusement.

---

## Vision future du cockpit

Le cockpit pourra ultérieurement représenter notamment :

* état de la graine ;
* génération ;
* pipeline expérimental ;
* lignées ;
* branches ;
* puzzles ;
* échecs ;
* nouveauté ;
* budget de calcul public ;
* résultats ;
* preuves ;
* intégrité ;
* retour à la source.

Cette liste est une intention d'interface.

Elle ne prouve pas que chaque donnée est déjà disponible ou publiable.

---

## Continuité Genesis

Une représentation future pourra suivre la boucle :

`origine`
→ `entrée`
→ `transformation`
→ `test`
→ `résultat`
→ `mémoire`
→ `retour`

Le Centre de Vision doit conserver les branches rejetées et les échecs publiables lorsque ceux-ci font partie de la preuve expérimentale.

---

## Contrat public

Avant toute connexion réelle avec Genesis, un contrat public versionné devra définir exactement :

* les champs autorisés ;
* leurs types ;
* leurs statuts ;
* leur provenance ;
* leurs limites ;
* les champs interdits ;
* la version du contrat.

Le cockpit devra consommer ce contrat public et non la structure interne brute du noyau privé.

---

## Infrastructure

Le dépôt public Antmux peut contenir :

* interface publique ;
* JavaScript/CSS public ;
* contrats ;
* schémas ;
* données de démonstration ;
* tests publics ;
* documentation reproductible.

Le dépôt public ne doit pas contenir :

* mots de passe ;
* tokens ;
* clés privées ;
* certificats privés ;
* configuration privée du VPS ;
* topologie réseau privée ;
* secrets Nginx ;
* secrets Genesis ;
* exports privés.

---

## Nginx

Nginx appartient à la couche de déploiement serveur.

Le Centre de Vision ne dépendra pas d'une configuration Nginx secrète enregistrée dans le dépôt public.

Une documentation générique reproductible pourra éventuellement être publiée séparément si elle ne révèle aucune infrastructure sensible.

---

## Protection de la devanture Antmux

Pendant LAB-004 :

les fichiers suivants restent hors périmètre :

`/index.html`
`/styles.css`
`/app.js`

Aucun bouton Genesis ne doit encore être ajouté à la devanture.

Le Centre de Vision devra d'abord fonctionner indépendamment sous :

`/laboratoire/genesis/`

---

## Première règle de construction

Ordre obligatoire :

`CONTRAT`
→ `DEMO`
→ `TEST LOCAL`
→ `VÉRIFICATION`
→ `PUBLICATION BRANCHE`
→ `ADAPTER`
→ `LECTURE RÉELLE`

Ne jamais connecter d'abord le noyau privé puis essayer de sécuriser après.

---

## Principe de sécurité

La frontière publique est une frontière scientifique autant qu'une frontière de sécurité.

Une donnée cachée peut compromettre :

* un secret ;
* une expérience ;
* une hypothèse aveugle ;
* une réplication ;
* une validation future.

Par conséquent :

`PRIVATE UNTIL EXPLICITLY PUBLISHED`

---

## Principe final

Genesis Vision Center doit montrer uniquement ce que nous pouvons défendre publiquement.

Il doit rendre visible :

* ce qui est observé ;
* ce qui est calculé ;
* ce qui est supposé ;
* ce qui a échoué ;
* ce qui a résisté aux tests.

Il ne doit jamais fabriquer l'apparence d'une preuve.
