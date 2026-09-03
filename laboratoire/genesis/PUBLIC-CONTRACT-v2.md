# ANTMUX — GENESIS PUBLIC CONTRACT v2

## Statut

`LAB-004`

Version du contrat :

`2.0.0-draft`

Phase :

`VISION_CENTER_GENESIS003_DEMO`

Ce contrat étend le contrat public v1 afin que Genesis Vision Center puisse représenter l'architecture actuelle du programme Genesis sans exposer le noyau privé.

Le principe reste :

`PRIVATE UNTIL EXPLICITLY PUBLISHED`

et :

`DENY BY DEFAULT -> EXPLICIT WHITELIST -> PUBLIC`

---

## Modes autorisés

- `DEMO`
- `SNAPSHOT`
- `LIVE_READ_ONLY`

`DEMO` utilise exclusivement des données synthétiques.

`SNAPSHOT` désigne une publication publique figée issue d'un processus autorisé.

`LIVE_READ_ONLY` reste interdit tant que le Genesis Public Adapter n'a pas été validé.

Le mode doit toujours être visible dans l'interface.

Pour `DEMO`, l'interface doit afficher :

`DEMO / SYNTHETIC DATA`

---

## Enveloppe publique

Champs de premier niveau autorisés :

- `contract_version`
- `mode`
- `publication_id`
- `published_at`
- `source_status`
- `integrity_status`
- `payload`

Aucun autre champ de premier niveau n'est autorisé.

Valeurs autorisées pour `source_status` :

- `SYNTHETIC`
- `PUBLIC_SNAPSHOT`
- `PUBLIC_READ_ONLY`

Valeurs autorisées pour `integrity_status` :

- `NOT_APPLICABLE`
- `UNVERIFIED`
- `VERIFIED_PUBLIC`
- `FAILED_PUBLIC_CHECK`

---

## Catégories payload autorisées

Le contrat v2 autorise :

- `identity`
- `continuity`
- `metacognition`
- `pipeline`
- `training_field`
- `observatory`
- `publication_gates`
- `metrics`
- `evidence`
- `integrity`

L'absence d'une catégorie signifie seulement qu'aucune donnée publique de cette catégorie n'est fournie.

---

## `payload.identity` — ROOT public

Champs autorisés :

- `seed_label`
- `root_status`
- `root_version`
- `root_digest`
- `continuity_policy`

Ce bloc représente uniquement une identité **publique** de la graine. Un digest privé ne doit jamais être copié automatiquement.

---

## `payload.continuity` — GENESIS-002

Champs autorisés :

- `cycle`
- `previous_checkpoint_ref`
- `current_checkpoint_ref`
- `parent_link_status`
- `root_identity_status`
- `accepted_candidates`
- `rejected_candidates`
- `return_status`

Cette vue doit permettre de vérifier publiquement l'idée :

`même ROOT -> cycle suivant -> lien parent -> acceptés/rejetés séparés -> retour`

Aucune référence ne doit pointer vers un chemin privé.

---

## `payload.metacognition` — GENESIS-003

Champs autorisés :

- `status`
- `competing_hypotheses`
- `uncertainty`
- `next_test`
- `rationale`
- `c041_c060_status`

Le champ `next_test` décrit une recommandation publique, pas une preuve que Genesis agit de manière autonome.

Le principe visé est :

`choisir le prochain test qui réduit le plus l'incertitude`

---

## `payload.pipeline`

Champs autorisés :

- `steps`

Chaque étape peut contenir :

- `id`
- `label`
- `status`

Statuts autorisés :

- `PENDING`
- `RUNNING_PUBLIC`
- `PASSED`
- `FAILED`
- `REJECTED`
- `NOT_APPLICABLE`

Le pipeline public recommandé est :

`SOURCE -> DESCENTE -> ZÉRO -> FORMATION -> EXPLORATION -> VALIDATION -> RETOUR SOURCE`

---

## `payload.training_field` — terrain d'entraînement

Champs autorisés :

- `label`
- `purpose`
- `observations`

Chaque observation peut contenir :

- `id`
- `label`
- `value`
- `unit`
- `semantic_class`
- `status`
- `provenance_ref`

`semantic_class` doit être une des valeurs :

- `MEASURED`
- `DERIVED`
- `INTERPRETED`
- `HYPOTHESIS`
- `UNKNOWN`

La classification décrit la nature logique de la donnée. Elle ne remplace pas `source_status`.

En mode `DEMO`, une donnée peut illustrer la catégorie `MEASURED` tout en restant **synthétique**. La bannière DEMO demeure obligatoire.

Le terrain pyramide ne doit jamais présenter une valeur interprétée ou un modèle comme une mesure brute.

---

## `payload.observatory` — GESIS

Champs autorisés :

- `label`
- `mode`
- `fft_status`
- `latest_export_ref`
- `peak_count`
- `episode_count`
- `block_score_status`
- `scientific_rule`

Le cockpit doit maintenir la règle :

`MESURE != INTERPRÉTATION`

Une proximité de fréquence, un pic FFT ou un Block Score ne devient jamais automatiquement une découverte.

---

## `payload.publication_gates`

Champs autorisés :

- `current_gate`
- `recommended_next_step`
- `gates`

Chaque gate peut contenir :

- `id`
- `label`
- `status`

Ce bloc montre explicitement les étapes avant publication réelle :

`CONTRAT -> ADAPTER -> SNAPSHOT -> LIVE_READ_ONLY`

Tant que l'Adapter n'est pas validé, `LIVE_READ_ONLY` doit rester `PENDING` ou équivalent.

---

## `payload.metrics`

Chaque métrique peut contenir uniquement :

- `id`
- `label`
- `value`
- `unit`
- `status`
- `provenance_ref`

`value` peut être une chaîne, un booléen ou un nombre fini.

Une métrique calculée ne doit jamais être présentée comme une mesure observée.

---

## `payload.evidence`

Chaque élément peut contenir :

- `id`
- `type`
- `status`
- `public_ref`
- `hash`

Types recommandés :

- `PUBLIC_DOCUMENT`
- `PUBLIC_RESULT`
- `PUBLIC_HASH`
- `PUBLIC_TEST`

Toutes les références doivent être publiques.

---

## `payload.integrity`

Champs autorisés :

- `status`
- `checks`

Chaque contrôle peut contenir :

- `id`
- `status`
- `public_ref`

Statuts autorisés :

- `PASSED`
- `FAILED`
- `NOT_RUN`
- `NOT_APPLICABLE`

---

## Frontière privée

Le navigateur public ne doit jamais lire directement :

- le dépôt privé `Topbrutus/seedgenesis` ;
- le filesystem privé ;
- une base privée ;
- des secrets ou tokens ;
- des seeds privées ;
- des audits privés ;
- des sorties oracle ;
- des credentials ;
- une topologie réseau privée ;
- une configuration serveur privée.

Architecture cible :

`PRIVATE GENESIS`
→ `GENESIS PUBLIC ADAPTER`
→ `PUBLIC CONTRACT v2`
→ `SNAPSHOT / READ-ONLY API`
→ `GENESIS VISION CENTER`

Le navigateur ne possède aucune capacité d'écriture vers Genesis.

---

## Générateur Antmux

`/generator/` reste un produit public séparé.

Genesis Vision Center peut offrir un lien de navigation vers le générateur, mais cette mission ne modifie ni son code, ni ses données, ni son comportement.

Aucun couplage implicite `Generator -> private Genesis` n'est autorisé.

---

## Discipline scientifique

Les catégories doivent rester séparées :

`MEASURED != DERIVED != INTERPRETED != HYPOTHESIS != UNKNOWN`

Le cockpit doit afficher les échecs et rejets publiables lorsqu'ils font partie de la preuve.

Une animation n'est pas une preuve d'activité réelle.

Le Centre de Vision ne prouve ni autonomie, ni conscience, ni intention historique, ni nouvelle loi physique.

---

## Règle de migration v1 -> v2

Le contrat v1 reste conservé comme historique.

Le cockpit v2 consomme `demo/genesis-demo-v2.json`.

Aucune donnée réelle privée n'est publiée par cette migration.

Le premier passage à `SNAPSHOT` devra faire l'objet d'une publication publique explicitement autorisée et validée.

---

## Verrou final

`PUBLIC CONTRACT BEFORE PUBLIC DATA`

et :

`UNKNOWN / PENDING > INVENTED`
