# Antmux — Générateur temporel autonome

Cette page est volontairement séparée de la façade officielle.

## Point d’entrée

`generator/index.html`

La page charge un **Web Component natif** défini dans `generator/antmux-generator.js`.

Aucun React, aucun framework, aucun backend et aucune dépendance CDN.

## Chaîne de dépendance

```text
horloge UTC de la Terre
-> 7 phases temporelles liées
-> code base 7
-> Triforce / branche / orientation
-> phase 273
-> pôle
-> 7 fonctions internes
-> emblème SVG
-> capture / empreinte / réincarnation
```

## Sept cycles

```text
700 ms / 7 = 100 ms
7 s / 7 = 1 s
7 min / 7 = 1 min
7 h / 7 = 1 h
7 jours / 7 = 1 jour
7 semaines / 7 = 1 semaine
7 années / 7 = 1 année
```

Les six premières couches sont ancrées sur l’époque Unix UTC. La couche annuelle utilise l’année UTC calendaire modulo sept.

## État dérivé

Aucune valeur secondaire n’est saisie indépendamment. Elles sont toutes recalculées depuis l’instant source.

```text
code7 = somme(phase_i * 7^i)
T = code7 mod 3
B = code7 mod 7
O = code7 mod 13
r = (91*T + 39*B + 21*O) mod 273
pole = r mod 7
adresse = code7 mod 2401
```

Les sept poids fonctionnels sont normalisés pour totaliser un.

## Chronomètre interactif

- `Pause / Reprendre`
- `+ 100 ms`
- `+ 1 s`
- saisie manuelle d’un timestamp Unix en millisecondes
- `Capturer`
- `Réincarner`
- `Exporter JSON`

Une capture fige le quantum de cent millisecondes. La réincarnation recalcule entièrement l’état à partir de cette valeur unique et compare son empreinte SHA-256.

## Bouton à ajouter plus tard à la façade officielle

Si le générateur est servi sous le même domaine :

```html
<a href="/generator/">Ouvrir le générateur Antmux</a>
```

Ne pas remplacer la façade officielle par cette page.

## Statut

Il s’agit d’un lecteur **d’états synthétiques dérivés du temps**. Il ne lit aucun neurone biologique et ne constitue pas une mesure de conscience.
