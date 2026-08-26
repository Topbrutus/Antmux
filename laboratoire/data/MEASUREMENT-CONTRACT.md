# ANTMUX — CONTRAT DE MESURE SCIENTIFIQUE

## But

Chaque mesure publiée dans le laboratoire Antmux doit pouvoir être retracée jusqu'à sa source et distinguée des conversions, reconstructions et calculs effectués par Antmux/Genesis.

## Identifiant

Chaque mesure reçoit un identifiant stable.

Format recommandé :

`<OBJET>-<ELEMENT>-<NUMERO>`

Exemples de structure seulement :

`G1A-BASE-001`
`G1B-CHAMBER-001`

Ces exemples ne constituent pas encore des données validées.

## Champs obligatoires

Chaque enregistrement doit conserver :

* `id`
* `structure`
* `element`
* `status`
* `value_original`
* `unit_original`
* `value_si`
* `unit_si`
* `conversion_method`
* `source_author`
* `source_title`
* `source_date`
* `source_page_or_plate`
* `source_locator`
* `measurement_context`
* `uncertainty`
* `conflict_group`
* `notes`

## Statuts autorisés

Pour les données de mesure :

* `SOURCE_DATA`
* `PUBLISHED_MEASUREMENT`

Pour les valeurs produites ensuite par le laboratoire :

* `DERIVED_CALCULATION`
* `HYPOTHESIS`
* `TEST_PROTOCOL`
* `TEST_RESULT`
* `INDEPENDENT_REPLICATION`
* `CORRECTION`
* `REJECTED`

Une valeur calculée par Antmux ne doit jamais être reclassée comme `PUBLISHED_MEASUREMENT`.

## Valeur originale

`value_original` doit conserver la valeur telle qu'elle apparaît dans la source.

Ne pas remplacer silencieusement :

* pieds par mètres ;
* pouces par centimètres ;
* coudées par mètres ;
* degrés/minutes/secondes par degrés décimaux.

La conversion doit être enregistrée séparément.

## Conversion SI

`value_si` est une valeur dérivée.

La méthode de conversion doit être explicitée dans :

`conversion_method`

Une conversion ne doit jamais écraser la donnée originale.

## Provenance

Une mesure n'est pas considérée comme correctement sourcée si elle ne permet pas de retrouver raisonnablement son origine.

Conserver lorsque disponibles :

* auteur ;
* titre ;
* année ;
* page ;
* planche ;
* tableau ;
* URL ou identifiant documentaire.

Une URL seule n'est pas une provenance suffisante lorsqu'une référence bibliographique plus précise est disponible.

## Conflits entre sources

Si deux relevés donnent des valeurs différentes :

NE PAS choisir silencieusement une valeur.

Créer deux enregistrements distincts.

Ils doivent partager un même :

`conflict_group`

Exemple conceptuel :

`G1A-BASE-CONFLICT-001`

Le laboratoire pourra ensuite comparer les méthodes et expliquer la divergence.

## Incertitude

Le champ :

`uncertainty`

doit distinguer :

* incertitude explicitement publiée ;
* tolérance estimée par l'auteur ;
* valeur approximative ;
* reconstruction ;
* incertitude inconnue.

Ne jamais inventer une précision absente de la source.

## Mesure directe et reconstruction

Une reconstruction architecturale n'est pas automatiquement une mesure directe.

Le champ `measurement_context` doit pouvoir préciser notamment :

* mesure de vestige ;
* dimension reconstruite ;
* dimension théorique ;
* excavation brute ;
* chambre finie ;
* projection horizontale ;
* longueur sur pente ;
* estimation.

## Calculs Genesis / Antmux

Les rapports, proportions, normalisations ou autres transformations réalisées par Antmux/Genesis doivent être enregistrés séparément des mesures sources.

Principe :

`SOURCE -> MESURE -> CONVERSION -> CALCUL -> HYPOTHÈSE -> TEST`

Chaque étape doit rester identifiable.

## Interdictions

Il est interdit :

* d'ajuster une mesure pour la faire correspondre à une hypothèse ;
* de supprimer une valeur conflictuelle sans justification ;
* d'augmenter artificiellement le nombre de décimales ;
* de présenter une reconstruction comme une mesure directe ;
* de présenter un calcul Genesis comme une donnée archéologique ;
* de citer une source non consultée comme si elle avait été vérifiée.

## Règle de publication

Une mesure peut entrer dans la collection publique seulement lorsque :

1. son origine est identifiable ;
2. sa valeur originale est conservée ;
3. la conversion éventuelle est séparée ;
4. son statut est explicite ;
5. les conflits connus sont conservés ;
6. aucune hypothèse Genesis n'a modifié la donnée source.
