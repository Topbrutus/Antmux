"""Fonctions pures du moteur. Aucune horloge murale, aucun aléa."""

from __future__ import annotations

import math
from fractions import Fraction


def pgcd(a: int, b: int) -> int:
    a, b = abs(int(a)), abs(int(b))
    while b:
        a, b = b, a % b
    return a


def ppcm(a: int, b: int) -> int:
    if a == 0 or b == 0:
        return 0
    return abs(a // pgcd(a, b) * b)


def ppcm_liste(valeurs: list[int] | tuple[int, ...]) -> int:
    resultat = 1
    for valeur in valeurs:
        resultat = ppcm(resultat, int(valeur))
    return resultat


def periode_roue(vitesse: int, anneau: int) -> int:
    if anneau <= 0 or vitesse <= 0:
        raise ValueError("anneau et vitesse doivent être positifs")
    return anneau // pgcd(anneau, vitesse)


def periodes(vitesses: list[int], anneau: int) -> list[int]:
    return [periode_roue(vitesse, anneau) for vitesse in vitesses]


def premier_tic_convergence(roues: list[dict], anneau: int) -> int | None:
    """Premier tic > 0 où chaque roue active est revenue à son départ.

    Une roue en pause ne participe pas : sa position éditée ne bouge pas.
    Le départ n'entre pas dans la période : (d + v t) ≡ d (mod n)
    équivaut à v t ≡ 0 (mod n).
    """
    actifs = [roue["vitesse"] for roue in roues if roue.get("actif", True)]
    if not actifs:
        return None
    return ppcm_liste([periode_roue(vitesse, anneau) for vitesse in actifs])


def position_roue(roue: dict, tic: int, anneau: int) -> int:
    depart = int(roue["depart"]) % anneau
    if not roue.get("actif", True):
        return depart
    return (depart + int(roue["vitesse"]) * tic) % anneau


def alignees(roues: list[dict], tic: int, anneau: int) -> bool:
    actifs = [roue for roue in roues if roue.get("actif", True)]
    if not actifs:
        return False
    return all(position_roue(roue, tic, anneau) == int(roue["depart"]) % anneau for roue in actifs)


def avancer_horloge(phase: int, reste: int, phases: int, hz: int, n: int = 1) -> tuple[int, int, list[int]]:
    """Récurrence documentée : total = reste + phases, pas = total // hz."""
    if phases <= 0 or hz <= 0 or n < 0:
        raise ValueError("paramètres d'horloge invalides")
    pas_liste: list[int] = []
    for _ in range(n):
        total = reste + phases
        pas = total // hz
        reste = total % hz
        phase = (phase + pas) % phases
        pas_liste.append(pas)
    return phase, reste, pas_liste


def fibonacci(n: int) -> int:
    """F(0) = 0, F(1) = 1. La graine n sélectionne F(n)."""
    if n < 0:
        raise ValueError("indice négatif")
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def premier(n: int) -> int:
    """n-ième nombre premier, n ≥ 1, p(1) = 2."""
    if n < 1:
        raise ValueError("l'indice des premiers commence à 1")
    trouves: list[int] = []
    candidat = 2
    while len(trouves) < n:
        if all(candidat % p for p in trouves if p * p <= candidat):
            trouves.append(candidat)
        candidat += 1 if candidat == 2 else 2
    return trouves[-1]


def index_temple(ligne: int, colonne: int, cote: int = 12) -> int:
    if cote < 1 or not 1 <= ligne <= cote or not 1 <= colonne <= cote:
        raise ValueError("ligne ou colonne hors grille")
    return cote * (ligne - 1) + (colonne - 1)


def ligne_colonne(index: int, cote: int = 12) -> tuple[int, int]:
    cellules = cote * cote
    if not 0 <= index < cellules:
        raise ValueError("index hors grille")
    return index // cote + 1, index % cote + 1


def etages_en_sept(depart: int = 2401) -> tuple[int, ...]:
    valeur = depart
    etages = []
    while True:
        etages.append(valeur)
        if valeur == 1:
            return tuple(etages)
        if valeur % 7 != 0:
            raise RuntimeError("cascade non divisible par 7")
        valeur //= 7


def decomposer_base7(phase: int, phases: int = 2401) -> tuple[int, int, int, int]:
    if not 0 <= phase < phases:
        raise ValueError("phase hors tour")
    return (
        phase % 7,
        (phase // 7) % 7,
        (phase // 49) % 7,
        (phase // 343) % 7,
    )


def recomposer_base7(chiffres: tuple[int, int, int, int]) -> int:
    a, b, c, d = chiffres
    return a + 7 * b + 49 * c + 343 * d


def position_roche(tic: int, nombre: int) -> int:
    if nombre <= 0:
        raise ValueError("aucune roche")
    return tic % nombre


def angle_degre(position: int, nombre: int) -> Fraction:
    return Fraction(360 * position, nombre)


def alertes_grille(nombre: int) -> list[str]:
    if nombre == 30:
        return []
    return [
        "La grille n'a plus 30 positions. L'emboîtement du Polybrutus "
        "(roches 0, 10, 15 et 20) et les cycles ppcm(30, 3, 7, 13) = 2730 "
        "et ppcm(30, 3, 7, 13, 2401) = 936390 supposent 30 positions de 12°."
    ]


def echo_roche(gain: int, courant: int, etat: str) -> int:
    """Une roche réservée n'amplifie pas : écho nul."""
    if etat != "installee":
        return 0
    return int(gain) * int(courant)


def intensite(roches: list[dict], courant: int) -> int:
    return sum(echo_roche(roche["gain"], courant, roche["etat"]) for roche in roches)


def profils_distincts(roches: list[dict]) -> bool:
    signatures = {(roche["gain"], roche["delai"], roche["timbre"]) for roche in roches}
    return len(signatures) == len(roches)


# Coordonnées exactes, R = 1. x est le coefficient de √3.
_POINTS = (
    ("P1", Fraction(0), Fraction(0), Fraction(1), "nord"),
    ("P2", Fraction(1, 2), Fraction(0), Fraction(1, 2), "nord"),
    ("P3", Fraction(-1, 4), Fraction(3, 4), Fraction(1, 2), "nord"),
    ("P4", Fraction(-1, 4), Fraction(-3, 4), Fraction(1, 2), "nord"),
    ("P5", Fraction(0), Fraction(0), Fraction(-1), "sud"),
    ("P6", Fraction(1, 2), Fraction(0), Fraction(-1, 2), "sud"),
    ("P7", Fraction(-1, 2), Fraction(0), Fraction(-1, 2), "sud"),
)

_RADICAL = {
    4: "1",
    7: "√7/2",
    9: "3/2",
    12: "√3",
    13: "√13/2",
    16: "2",
}

_ROCHE_0 = {"P2": 0, "P3": 10, "P4": 20, "P6": 0, "P7": 15}
_CENTRES = {"P1", "P5"}


def coordonnees() -> list[dict]:
    texte = {
        "P1": "(0, 0, R)",
        "P2": "(√3·R/2, 0, R/2)",
        "P3": "(−√3·R/4, 3R/4, R/2)",
        "P4": "(−√3·R/4, −3R/4, R/2)",
        "P5": "(0, 0, −R)",
        "P6": "(√3·R/2, 0, −R/2)",
        "P7": "(−√3·R/2, 0, −R/2)",
    }
    return [
        {
            "point": nom,
            "x_sqrt3": str(coef_x),
            "y": str(y),
            "z": str(z),
            "hemisphere": hemisphere,
            "texte": texte[nom],
        }
        for nom, coef_x, y, z, hemisphere in _POINTS
    ]


def k_paires() -> list[dict]:
    """k = 4 d²/R², avec x = coef · √3."""
    sortie = []
    for i in range(len(_POINTS)):
        for j in range(i + 1, len(_POINTS)):
            a = _POINTS[i]
            b = _POINTS[j]
            dp, dq, dz = a[1] - b[1], a[2] - b[2], a[3] - b[3]
            k = 4 * (3 * dp * dp + dq * dq + dz * dz)
            if k.denominator != 1:
                raise RuntimeError(f"k non entier: {a[0]} {b[0]} {k}")
            sortie.append({"a": a[0], "b": b[0], "k": int(k)})
    return sortie


def familles_k() -> list[dict]:
    from collections import Counter

    compte = Counter(paire["k"] for paire in k_paires())
    return [
        {
            "k": k,
            "multiplicite": compte[k],
            "d_sur_R": _RADICAL[k],
            "etiquette": "CALCUL EXACT",
        }
        for k in sorted(compte)
    ]


def somme_k() -> int:
    return sum(item["k"] * item["multiplicite"] for item in familles_k())


def centroide_z() -> Fraction:
    return sum((point[3] for point in _POINTS), Fraction(0)) / len(_POINTS)


def projection_polybrutus(rotation: int, positions: int = 30) -> list[dict]:
    """Projection XY sur la grille de 30. P1 et P5 restent au centre.

    La forme spécifique s'emboîte. Un heptagone régulier, non :
    pgcd(7, 30) = 1. Coïncidence géométrique exacte, pas une preuve physique.
    """
    if positions != 30:
        raise ValueError("la projection calculée suppose la grille de 30")
    if not 0 <= rotation < 30:
        raise ValueError("rotation hors 0..29")
    points = []
    for nom, *_reste in _POINTS:
        if nom in _CENTRES:
            points.append({"point": nom, "lieu": "centre", "roche": None})
        else:
            points.append({
                "point": nom,
                "lieu": "roche",
                "roche": (_ROCHE_0[nom] + rotation) % 30,
            })
    return points


def ensemble_roches(rotation: int) -> frozenset[int]:
    return frozenset(
        point["roche"]
        for point in projection_polybrutus(rotation)
        if point["roche"] is not None
    )


def cycle_stonehenge() -> dict[str, int]:
    return {
        "ppcm_30_3_7_13": ppcm_liste([30, 3, 7, 13]),
        "ppcm_avec_2401": ppcm_liste([30, 3, 7, 13, 2401]),
        "ppcm_30_3_7_13_sur_273": ppcm_liste([30, 3, 7, 13]) // 273,
    }


def observer_cristal(etat, cle: str, seuil: int, promus: int, niveau_max: int) -> None:
    """Règle 8 → 7 + 1, répétée de niveau en niveau jusqu'à L7.

    Quand `seuil` observations de même clé sont en tête, `promus` d'entre
    elles forment un cristal du niveau suivant et `seuil - promus` restent.
    Étiquette d'usage : CANDIDAT pour l'accumulation, DOCUMENTÉ pour 8 → 7 + 1.
    """
    if seuil < 2 or not 1 <= promus < seuil:
        raise ValueError("règle de cristallisation invalide")
    while len(etat.piles) <= niveau_max:
        etat.piles.append([])
    etat.piles[0].append(cle)
    _reduire(etat, 0, seuil, promus, niveau_max)


def _reduire(etat, niveau: int, seuil: int, promus: int, niveau_max: int) -> None:
    if niveau >= niveau_max:
        return
    file = etat.piles[niveau]
    while len(file) >= seuil:
        lot = file[:seuil]
        gardes = lot[:promus]
        if len(set(gardes)) != 1:
            break
        file[:seuil] = lot[promus:]
        etat.piles[niveau + 1].append(gardes[0])
        etat.cristaux.append({
            "niveau": niveau + 1,
            "cle": gardes[0],
            "effectif": promus,
            "etiquette": "CANDIDAT",
        })
        _reduire(etat, niveau + 1, seuil, promus, niveau_max)


def lcm_builtin_check() -> int:
    """ppcm(37, 144) via la bibliothèque, pour croiser le produit."""
    return math.lcm(37, 144)
