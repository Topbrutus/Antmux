# BrutoBac — vitrine Fourmi Aquarium 3D

Route publique : `/laboratoire/brutobac/`.

La page enveloppe le BrutoBac servi par le Queen Server à `/laboratoire/embryon-x72/api/brutobac/`. Le monde Fourmi et l’état de la poussière sont lus depuis la Queen; la vitrine n’écrit ni dans la Reine ni dans le registre de ressources.

## Poussière Brotoculateur

La vitrine lit l’état autoritaire à `GET /laboratoire/embryon-x72/api/brutobac/dust/state`. La réponse expose la quantité disponible, les totaux produits et consommés, le total source, le débit par transit, le carrier et sa position. Elle ne calcule pas la quantité à partir d’un compte local du navigateur.

Si l’état de ressource est indisponible, la vitrine n’invente ni ne reconstitue une quantité; elle affiche l’état indisponible. La pluie de particules est une représentation visuelle de cette quantité, sans écriture côté navigateur.

L’ingestion Brotoculateur et la consommation d’une ressource passent par des opérations côté serveur protégées. Aucun jeton d’ingestion ni secret n’est envoyé à la vitrine publique.

## Sources réelles

- Fourmis, positions et matériaux : Queen Server `QUEEN_SERVER_V0_2` → BrutoBac public SSE/snapshot.
- Poussière : registre SQLite de la Queen → endpoint public en lecture seule `/api/brutobac/dust/state`.
- Ingestion source : pont Brotoculateur authentifié côté serveur.

La ressource de poussière est un état logiciel du monde Fourmi; elle ne constitue pas une preuve mathématique ni une affirmation de mouvement physique.
