# ANTMUX — GENESIS PUBLIC CONTRACT v1

## Statut

`LAB-004`

Version du contrat :

`1.0.0-draft`

Phase :

`PUBLIC_CONTRACT_ONLY`

Ce document définit l'interface publique conceptuelle que Genesis Vision Center pourra consommer.

Il ne connecte pas le dépôt public au noyau privé Genesis.

---

## Principe

Le contrat public est une frontière de publication.

Règle par défaut :

`DENY BY DEFAULT`

Seuls les champs explicitement autorisés par ce contrat peuvent être publiés.

Tout champ absent de la liste blanche reste privé.

---

## Modes autorisés

Le champ `mode` doit prendre exactement une des valeurs suivantes :

- `DEMO`
- `SNAPSHOT`
- `LIVE_READ_ONLY`

`DEMO` utilise uniquement des données synthétiques.

`SNAPSHOT` désigne une capture publique figée issue d'un processus de publication autorisé.

`LIVE_READ_ONLY` est réservé à une future interface de lecture seule après validation du Genesis Public Adapter.

---

## Enveloppe publique minimale

Une réponse publique doit pouvoir être décrite par les champs suivants :

- `contract_version`
- `mode`
- `publication_id`
- `published_at`
- `source_status`
- `integrity_status`
- `payload`

Aucun autre champ de premier niveau n'est autorisé dans la version 1 sans révision explicite du contrat.

---

## contract_version

Type : chaîne.

Valeur attendue pour ce contrat :

`1.0.0-draft`

Le cockpit doit refuser silencieusement toute interprétation automatique d'une version majeure inconnue.

---

## mode

Type : chaîne énumérée.

Valeurs autorisées :

- `DEMO`
- `SNAPSHOT`
- `LIVE_READ_ONLY`

Le mode doit toujours être visible dans l'interface.

Pour `DEMO`, l'interface doit afficher explicitement :

`DEMO / SYNTHETIC DATA`

---

## publication_id

Type : chaîne.

But : identifier de façon stable la publication publique affichée.

Cet identifiant ne doit contenir aucun chemin privé, secret, hostname privé, token ou identifiant d'infrastructure sensible.

---

## published_at

Type : chaîne de date/heure publique normalisée.

Cette valeur décrit l'heure de publication de la vue publique et non nécessairement l'heure d'un événement interne privé.

---

## source_status

Type : chaîne énumérée.

Valeurs autorisées :

- `SYNTHETIC`
- `PUBLIC_SNAPSHOT`
- `PUBLIC_READ_ONLY`

`SYNTHETIC` est obligatoire pour les données de démonstration.

---

## integrity_status

Type : chaîne énumérée.

Valeurs autorisées :

- `NOT_APPLICABLE`
- `UNVERIFIED`
- `VERIFIED_PUBLIC`
- `FAILED_PUBLIC_CHECK`

Le mot `VERIFIED_PUBLIC` ne signifie jamais que l'ensemble du noyau privé a été vérifié.

Il signifie uniquement que les contrôles publics définis pour la publication concernée ont réussi.

---

## payload

`payload` contient uniquement les catégories publiques autorisées ci-dessous.

Les catégories possibles sont :

- `experiment`
- `continuity`
- `pipeline`
- `metrics`
- `evidence`
- `integrity`

Une catégorie peut être absente si aucune donnée publiable n'existe.

L'absence d'une catégorie ne doit jamais être interprétée comme une valeur nulle cachée.

---

## payload.experiment

Champs autorisés :

- `public_experiment_id`
- `label`
- `status`
- `generation`

`generation` peut être omis lorsque le concept ne s'applique pas à la publication.

Aucun identifiant interne privé ne doit être publié par simple copie.

---

## payload.continuity

Champs autorisés :

- `stage`
- `origin_ref`
- `previous_publication_ref`
- `return_status`

Cette catégorie sert à représenter publiquement la continuité :

`origine -> entrée -> transformation -> test -> résultat -> mémoire -> retour`

Les références doivent pointer uniquement vers des identifiants publics.

---

## payload.pipeline

Champs autorisés :

- `steps`

Chaque élément public de `steps` peut contenir :

- `id`
- `label`
- `status`

Valeurs de `status` autorisées :

- `PENDING`
- `RUNNING_PUBLIC`
- `PASSED`
- `FAILED`
- `REJECTED`
- `NOT_APPLICABLE`

`RUNNING_PUBLIC` ne constitue pas une affirmation d'autonomie ou de conscience.

---

## payload.metrics

`metrics` est une liste de métriques publiques.

Chaque métrique peut contenir uniquement :

- `id`
- `label`
- `value`
- `unit`
- `status`
- `provenance_ref`

Le champ `value` peut être numérique, booléen ou chaîne selon la métrique documentée.

Les unités doivent être explicites lorsqu'elles s'appliquent.

Une métrique calculée ne doit jamais être présentée comme une mesure observée.

---

## payload.evidence

`evidence` est une liste de références publiques de preuve.

Chaque élément peut contenir :

- `id`
- `type`
- `status`
- `public_ref`
- `hash`

Valeurs de `type` recommandées :

- `PUBLIC_DOCUMENT`
- `PUBLIC_RESULT`
- `PUBLIC_HASH`
- `PUBLIC_TEST`

Le champ `hash` est optionnel.

Il ne doit jamais servir à exposer un contenu privé non publié.

---

## payload.integrity

Champs autorisés :

- `status`
- `checks`

Chaque contrôle public peut contenir :

- `id`
- `status`
- `public_ref`

Valeurs de statut :

- `PASSED`
- `FAILED`
- `NOT_RUN`
- `NOT_APPLICABLE`

---

## Provenance obligatoire

Toute donnée réelle publiée doit être reliée à une provenance publique suffisante.

Une provenance publique peut référencer :

- un document public ;
- un résultat public ;
- un protocole public ;
- un hash public ;
- un identifiant de snapshot public.

Une provenance ne doit jamais contenir un chemin de fichier privé ou une URL privée.

---

## Catégories explicitement interdites

Le contrat v1 interdit la publication de tout champ contenant directement ou indirectement :

- mot de passe ;
- token ;
- clé privée ;
- secret ;
- variable d'environnement privée ;
- seed privée ;
- programme caché ;
- audit privé ;
- sortie oracle privée ;
- credential ;
- cookie de session ;
- chemin absolu privé ;
- hostname privé ;
- adresse IP privée d'infrastructure ;
- topologie réseau privée ;
- configuration Nginx privée ;
- contenu brut d'un export privé ;
- identifiant interne dont la publication n'a pas été autorisée.

Cette liste ne limite pas le principe `DENY BY DEFAULT`.

Un champ non listé comme interdit reste néanmoins privé s'il n'est pas explicitement autorisé.

---

## Données de démonstration

Toute donnée de démonstration doit :

- être créée sans copie d'un export privé ;
- être clairement synthétique ;
- ne pas reproduire accidentellement un secret ou un identifiant réel ;
- utiliser `mode = DEMO` ;
- utiliser `source_status = SYNTHETIC` ;
- utiliser `integrity_status = NOT_APPLICABLE` ou `UNVERIFIED` selon le cas.

Le cockpit ne doit jamais faire passer une démonstration pour un état réel de Genesis.

---

## Lecture seule

Ce contrat décrit uniquement des données sortantes vers le Centre de Vision.

Il ne définit aucun :

- endpoint d'écriture ;
- commande ;
- mutation ;
- upload ;
- déclenchement d'expérience ;
- modification d'état privé.

Toute future capacité d'expérimentation publique devra être conçue dans un contrat séparé et sandboxé.

---

## Validation minimale avant publication

Avant qu'une réponse ne soit considérée conforme au contrat public v1, le futur Adapter devra vérifier au minimum :

1. la version du contrat ;
2. le mode ;
3. la liste blanche des champs ;
4. l'absence de champs interdits ;
5. la provenance exigée pour les données réelles ;
6. le statut d'intégrité public ;
7. l'absence d'écriture vers Genesis.

Si une validation échoue :

`DO NOT PUBLISH`

---

## Règle d'évolution

Toute modification de la liste blanche exige une nouvelle révision explicite du contrat.

Une nouvelle donnée interne disponible dans Genesis ne devient jamais automatiquement publique.

Le contrat public doit évoluer volontairement, par preuve et revue.

---

## Limite scientifique

Le contrat organise la publication des observations et résultats.

Il ne transforme pas une hypothèse en fait.

Il ne constitue pas une preuve de conscience, d'autonomie ou d'une nouvelle loi physique.

---

## Verrou final

`PRIVATE UNTIL EXPLICITLY PUBLISHED`

et

`PUBLIC CONTRACT BEFORE PUBLIC DATA`
