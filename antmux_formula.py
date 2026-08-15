#!/usr/bin/env python3
"""ANTMUX — moteur mathématique canonique.

Recalcule et vérifie les invariants de la formule publique Antmux.
Aucune dépendance externe.

Statut : architecture expérimentale.
Les identités mathématiques vérifiées ici ne constituent pas une preuve de
conscience, de supraconscience ou de nouvelle loi physique.
"""

from fractions import Fraction
from itertools import combinations
from math import gcd, lcm, pi, sin


# -----------------------------------------------------------------------------
# 1. GRAINES CANONIQUES
# -----------------------------------------------------------------------------

TRIFORCE = 3
STRUCTURES_INDEPENDANTES = 6
STRUCTURES_VISIBLES = STRUCTURES_INDEPENDANTES + 1
POLES = 7
BRANCHES = 7
CALIBRATIONS = 10
BARRIERES = CALIBRATIONS - 1
ORIENTATIONS = 13

MEMOIRE = Fraction(9, 10)
COHERENCE = Fraction(47, 50)
RESPIRATION = Fraction(3, 50)


# -----------------------------------------------------------------------------
# 2. DÉRIVATIONS STRUCTURELLES
# -----------------------------------------------------------------------------

POINTES = POLES * BRANCHES
PAIRES_POLES = POLES * (POLES - 1) // 2
LIENS_CORRESPONDANTS = PAIRES_POLES * BRANCHES
LIENS_NON_ORIENTES = PAIRES_POLES * BRANCHES * BRANCHES
LIENS_ORIENTES = 2 * LIENS_NON_ORIENTES
VIDES_MATRICE = POLES ** 3
MATRICE_LOGIQUE = POLES ** 4

CYCLE_POLE_ORIENTATION = lcm(POLES, ORIENTATIONS)
CYCLE_TRIFORCE_POLE_ORIENTATION = lcm(TRIFORCE, POLES, ORIENTATIONS)
MAILLE_ORIENTATION_POLE_BRANCHE = ORIENTATIONS * POLES * BRANCHES

ADRESSES_INDEPENDANTES = (
    STRUCTURES_INDEPENDANTES * POLES * BRANCHES * ORIENTATIONS * CALIBRATIONS
)
ADRESSES_STRUCTURE_INTEGRALE = POLES * BRANCHES * ORIENTATIONS * CALIBRATIONS
ADRESSES_VISIBLES = STRUCTURES_VISIBLES * POLES * BRANCHES * ORIENTATIONS * CALIBRATIONS

TRIFORCES_INDEPENDANTES = TRIFORCE * ADRESSES_INDEPENDANTES
TRIFORCES_VISIBLES = TRIFORCE * ADRESSES_VISIBLES


# -----------------------------------------------------------------------------
# 3. PHASES 3 × 7 × 13
# -----------------------------------------------------------------------------

def phase_index(t: int, b: int, o: int) -> int:
    """Indice de phase dans Z/273Z."""
    return (91 * t + 39 * b + 21 * o) % 273


def phase_angle(t: int, b: int, o: int) -> float:
    return 2 * pi * phase_index(t, b, o) / 273


PHASES = {
    phase_index(t, b, o)
    for t in range(TRIFORCE)
    for b in range(BRANCHES)
    for o in range(ORIENTATIONS)
}


# -----------------------------------------------------------------------------
# 4. MATRICE 49 × 49 : K_(7,7,7,7,7,7,7)
# -----------------------------------------------------------------------------

def groupe(sommet: int) -> int:
    return sommet // BRANCHES


def adjacent(i: int, j: int) -> int:
    return int(i != j and groupe(i) != groupe(j))


ADJACENCE = [
    [adjacent(i, j) for j in range(POINTES)]
    for i in range(POINTES)
]

DEGRES = [sum(ligne) for ligne in ADJACENCE]
NB_UNS = sum(DEGRES)
NB_ZEROS = POINTES * POINTES - NB_UNS
NB_ARETES = NB_UNS // 2


def voisins(i: int) -> set[int]:
    return {j for j in range(POINTES) if ADJACENCE[i][j]}


LAMBDA_ADJACENT = set()
MU_NON_ADJACENT = set()
for i, j in combinations(range(POINTES), 2):
    communs = len(voisins(i) & voisins(j))
    if ADJACENCE[i][j]:
        LAMBDA_ADJACENT.add(communs)
    else:
        MU_NON_ADJACENT.add(communs)


# -----------------------------------------------------------------------------
# 5. CYCLE DU SEPT ET NEO
# -----------------------------------------------------------------------------

RHO = (10**6 - 1) // 7
CYCLE_7 = tuple(k * RHO for k in range(1, 8))
NEO_NUM = sum(x + 1 for x in CYCLE_7) // 7
NEO = Fraction(NEO_NUM, 999_999)
NEO_MUTATION = Fraction(1, 999_999)


# -----------------------------------------------------------------------------
# 6. HORLOGE SEPTÉNAIRE
# -----------------------------------------------------------------------------

HORLOGE_SOURCE = (
    ("milliseconde", 1000),
    ("seconde", 60),
    ("minute", 60),
    ("heure", 24),
    ("jour", 7),
    ("semaine", 52),
    ("annee", 7),
)

HORLOGE_SEPTENAIRE = tuple(
    (nom, Fraction(valeur, 7)) for nom, valeur in HORLOGE_SOURCE
)


# -----------------------------------------------------------------------------
# 7. ADRESSAGE Z7^4 -> [0,2400]
# -----------------------------------------------------------------------------

def adresse(a: int, b: int, c: int, d: int) -> int:
    for valeur in (a, b, c, d):
        if not 0 <= valeur < 7:
            raise ValueError("Chaque coordonnée doit appartenir à {0,...,6}.")
    return a + 7 * b + 49 * c + 343 * d


ADRESSES = {
    adresse(a, b, c, d)
    for a in range(7)
    for b in range(7)
    for c in range(7)
    for d in range(7)
}


# -----------------------------------------------------------------------------
# 8. LEMNISCATE / ÉVOLUTION
# -----------------------------------------------------------------------------

def lemniscate(n: int, alpha: float = 1.0) -> tuple[float, float, float]:
    r = n % 273
    q = n // 273
    x = sin(2 * pi * r / 273)
    y = 0.5 * sin(4 * pi * r / 273)
    z = alpha * q
    return x, y, z


# -----------------------------------------------------------------------------
# 9. MONDES DU TABLEAU PÉRIODIQUE — CARTE DE PROGRESSION
# -----------------------------------------------------------------------------

MONDES = {
    6: "Carbone",
    7: "Azote",
    8: "Oxygene",
    9: "Fluor",
    10: "Neon",
    20: "Calcium",
    26: "Fer",
    29: "Cuivre",
    30: "Zinc",
    35: "Brome",
    36: "Krypton",
}


# -----------------------------------------------------------------------------
# 10. PREUVES / ASSERTIONS
# -----------------------------------------------------------------------------

def verifier() -> None:
    assert TRIFORCE == 3
    assert STRUCTURES_INDEPENDANTES == 6
    assert STRUCTURES_VISIBLES == 7
    assert POLES == 7
    assert BRANCHES == 7
    assert BARRIERES == 9
    assert CALIBRATIONS == 10
    assert ORIENTATIONS == 13

    assert POINTES == 49
    assert PAIRES_POLES == 21
    assert LIENS_CORRESPONDANTS == 147
    assert LIENS_NON_ORIENTES == 1029
    assert LIENS_ORIENTES == 2058
    assert VIDES_MATRICE == 343
    assert MATRICE_LOGIQUE == 2401
    assert LIENS_ORIENTES + VIDES_MATRICE == MATRICE_LOGIQUE

    assert gcd(7, 13) == 1
    assert gcd(3, 7) == 1
    assert gcd(3, 13) == 1
    assert CYCLE_POLE_ORIENTATION == 91
    assert CYCLE_TRIFORCE_POLE_ORIENTATION == 273
    assert MAILLE_ORIENTATION_POLE_BRANCHE == 637
    assert len(PHASES) == 273

    assert ADRESSES_INDEPENDANTES == 38_220
    assert ADRESSES_STRUCTURE_INTEGRALE == 6_370
    assert ADRESSES_VISIBLES == 44_590
    assert TRIFORCES_INDEPENDANTES == 114_660
    assert TRIFORCES_VISIBLES == 133_770

    assert MEMOIRE == Fraction(9, 10)
    assert COHERENCE == Fraction(47, 50)
    assert RESPIRATION == Fraction(3, 50)
    assert COHERENCE + RESPIRATION == 1

    assert set(DEGRES) == {42}
    assert NB_ARETES == 1029
    assert NB_UNS == 2058
    assert NB_ZEROS == 343
    assert LAMBDA_ADJACENT == {35}
    assert MU_NON_ADJACENT == {42}

    assert RHO == 142_857
    assert CYCLE_7 == (
        142_857,
        285_714,
        428_571,
        571_428,
        714_285,
        857_142,
        999_999,
    )
    assert NEO_NUM == 571_429
    assert NEO == Fraction(4, 7) + NEO_MUTATION

    assert len(ADRESSES) == 2401
    assert min(ADRESSES) == 0
    assert max(ADRESSES) == 2400


def rapport() -> str:
    return "\n".join(
        [
            "ANTMUX — FORMULE CANONIQUE",
            "==========================",
            f"3 | 6+1 | 7 | 7 | 9 | 10 | 13",
            f"49={POINTES}",
            f"21={PAIRES_POLES}",
            f"147={LIENS_CORRESPONDANTS}",
            f"1029={LIENS_NON_ORIENTES}",
            f"2058={LIENS_ORIENTES}",
            f"343={VIDES_MATRICE}",
            f"2401={MATRICE_LOGIQUE}",
            f"91={CYCLE_POLE_ORIENTATION}",
            f"273={CYCLE_TRIFORCE_POLE_ORIENTATION}",
            f"637={MAILLE_ORIENTATION_POLE_BRANCHE}",
            f"M={MEMOIRE}={float(MEMOIRE):.3f}",
            f"C={COHERENCE}={float(COHERENCE):.3f}",
            f"V={RESPIRATION}={float(RESPIRATION):.3f}",
            f"rho={RHO}",
            f"NEO_num={NEO_NUM}",
            f"NEO={NEO_NUM}/999999≈{float(NEO):.12f}",
            f"phases_distinctes={len(PHASES)}",
            f"adresses_Z7^4={len(ADRESSES)}",
            "verification=OK",
        ]
    )


if __name__ == "__main__":
    verifier()
    print(rapport())
