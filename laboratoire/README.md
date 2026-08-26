# ANTMUX — LABORATOIRE PUBLIC

## Mission

Le laboratoire public Antmux sert à publier des recherches vérifiables, reproductibles et critiquables.

Il doit permettre à un tiers de distinguer immédiatement :

1. les données provenant de sources externes ;
2. les mesures publiées ;
3. les calculs dérivés par Antmux/Genesis ;
4. les hypothèses ;
5. les protocoles de test ;
6. les résultats obtenus ;
7. les réplications indépendantes ;
8. les corrections et hypothèses rejetées.

## Règle fondamentale

Aucune hypothèse ne doit être présentée comme un fait établi.

Une correspondance numérique, géométrique ou symbolique n'est pas une preuve de causalité.

Toute affirmation importante doit pouvoir être reliée à sa provenance, son calcul ou son protocole de test.

## Statuts canoniques

* `SOURCE_DATA`
* `PUBLISHED_MEASUREMENT`
* `DERIVED_CALCULATION`
* `HYPOTHESIS`
* `TEST_PROTOCOL`
* `TEST_RESULT`
* `INDEPENDENT_REPLICATION`
* `CORRECTION`
* `REJECTED`

## Première collection scientifique

La première collection prévue concerne les pyramides secondaires du complexe de Khéops :

* `G1-a`
* `G1-b`
* `G1-c`

Les mesures historiques devront conserver :

* la valeur originale publiée ;
* l'unité originale si disponible ;
* la conversion SI séparée ;
* l'auteur ;
* l'ouvrage ou publication ;
* la page ou plan lorsque disponible ;
* l'incertitude ou divergence entre relevés ;
* le statut de la donnée.

Aucune valeur conflictuelle ne doit être silencieusement remplacée.

## Genesis

Genesis est traité comme un programme expérimental.

Le laboratoire doit permettre de documenter :

`origine -> entrée -> transformation -> test -> résultat -> mémoire -> retour`

Les nombres ou motifs associés à Genesis ne deviennent pas des constantes physiques par leur seule présence dans une construction mathématique ou architecturale.

## Fourminoïdes

Les Fourminoïdes ne sont pas encore construits.

Le laboratoire peut documenter leur future conception et les hypothèses qui pourraient conduire à leur architecture.

Il est interdit de les présenter comme existants, actifs ou validés sans preuve d'implémentation et d'exécution.

## Antmux

Antmux fournit le cadre public permettant de :

* conserver les données ;
* documenter leur provenance ;
* recalculer les résultats ;
* comparer plusieurs hypothèses ;
* conserver les échecs ;
* permettre la reproduction indépendante.

## Frontière publique / privée

Le laboratoire public ne doit contenir :

* aucun mot de passe ;
* aucune clé API ;
* aucun jeton ;
* aucun certificat privé ;
* aucune donnée personnelle ;
* aucune topologie privée ;
* aucune configuration d'infrastructure sensible ;
* aucun secret provenant de Memoria ou d'autres dépôts privés.

## Protection de la devanture

Le laboratoire est développé séparément sous :

`/laboratoire/`

Pendant cette phase, les fichiers suivants sont hors périmètre et ne doivent pas être modifiés :

* `/index.html`
* `/styles.css`
* `/app.js`

Le laboratoire devra fonctionner indépendamment avant qu'un éventuel bouton vers celui-ci soit ajouté à la devanture.

## Discipline de construction

Construire petit.

Vérifier.

Comparer.

Conserver la preuve.

Seulement ensuite étendre.

Aucune grande refonte ne doit être effectuée pour introduire le laboratoire.

## Principe scientifique

Une idée intéressante n'est pas protégée de la critique.

Au contraire, le laboratoire doit rendre aussi facile de démontrer qu'une hypothèse est fausse que de montrer qu'elle résiste aux tests.
