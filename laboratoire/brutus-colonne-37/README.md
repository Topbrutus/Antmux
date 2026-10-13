# BRUTUS — Colonne 37 (prototype)

Prototype isolé du live VPS.

## Architecture

- 33 vertèbres = 33 instruments déterministes de mesure.
- 4 organes maîtres = Constante Brutus, Papillon, Bibliothèque rapide 37, Reine/Fourmis.
- Total = 37 postes.
- Papillon conserve ses 144 routes et ajoute une voie locale 0..36.
- La bibliothèque utilise 37 buckets et une identité canonique SHA-256.

## Constante Brutus

`B = 7^21 / 10^17 = 5.58545864083284007`

La constante est transportée comme référence. Elle n'est **pas** multipliée automatiquement dans les valeurs. Un instrument doit déclarer explicitement son usage avant toute transformation future.

## Poussière / fourmis

Une répétition n'est pas matérialisée comme un nouveau gros objet.

Pour une même identité `(valeur, formule, niveau)` :

- un seul cristal canonique ;
- compteur d'occurrences ;
- ensemble de chemins indépendants ;
- première et dernière observation ;
- empreinte de la trace des 33 instruments ;
- quota de replay par rareté : 8 → 6 → 4 → 2 → 1.

Ainsi, 245 000 poussières identiques peuvent être représentées comme 1 cristal canonique avec `count=245000`, au lieu de 245 000 copies lourdes.

## Bibliothèque ultra-rapide

La première observation traverse les 33 instruments. Une observation déjà connue fait un hit mémoire et met seulement à jour compteur + provenance. Le prototype vérifie que les 33 instruments ne sont pas recalculés sur un doublon exact.

## 37 et la famille 111…999

Le prototype mesure explicitement `mod 37`, le quotient et la divisibilité. Pour la famille connue :

- `111 = 37 × 3`
- `222 = 37 × 6`
- …
- `999 = 37 × 27`

Cette relation est mesurée ; elle n'est pas utilisée comme justification générale de tout le système.

## Jeu de graines

Le moteur accepte n'importe quelle liste d'entiers. `demo.py` n'invente pas la pancarte complète : il utilise seulement les valeurs explicitement établies dans le chantier actuel. La liste officielle des 45 nombres devra être importée depuis sa source autoritative, puis `11611` ajouté comme convenu.

## Exécution

```powershell
cd laboratoire/brutus-colonne-37
python -m pytest -q test_brutus37.py
python demo.py
```

## Statut scientifique

Prototype d'architecture et de stockage. Il ne constitue ni une preuve mathématique, ni une validation d'une nouvelle loi physique. Les 33 instruments actuels sont des mesures déterministes destinées à rendre le squelette observable et falsifiable avant d'y brancher des transformations plus ambitieuses.
