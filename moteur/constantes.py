"""Constantes par défaut du moteur, étiquetées.

Étiquettes :
- CALCUL EXACT : identité arithmétique ;
- DOCUMENTÉ : trace du README ou de la reconstruction, pas une mesure ;
- CANDIDAT : couplage ou paramètre non démontré ;
- INCONNU : point non résolu ;
- DÉCISION DU PROPRIÉTAIRE : choix explicite, pas une mesure.

Les nombres 2400 et 2401 désignent ici des objets différents.
On ne les substitue pas l'un à l'autre.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


ETIQUETTES = frozenset({
    "CALCUL EXACT",
    "DOCUMENTÉ",
    "CANDIDAT",
    "INCONNU",
    "DÉCISION DU PROPRIÉTAIRE",
})

VERSION = "0.1.0"


@dataclass(frozen=True)
class Constante:
    nom: str
    valeur: Any
    etiquette: str
    note: str
    unite: str = ""
    role: str = ""

    def __post_init__(self) -> None:
        if self.etiquette not in ETIQUETTES:
            raise ValueError(self.etiquette)


# --- Horloge v0.1 (objet distinct du canal 2400 Hz) ---

FREQUENCE_LOGIQUE_HZ = Constante(
    "frequence_logique_hz",
    37,
    "DOCUMENTÉ",
    "37 pas par seconde idéale. Fréquence de modèle, pas un relevé.",
    "Hz logique",
)

PHASES_PAR_TOUR = Constante(
    "phases_par_tour",
    7**4,
    "CALCUL EXACT",
    "7**4 = 2401 phases d'un tour. Ce n'est ni le canal 2400 Hz ni la cible V1.2.",
    "phases",
)

FREQUENCE_CIBLE_V12_HZ = Constante(
    "frequence_cible_v12_hz",
    2401,
    "CANDIDAT",
    "Cible V1.2 : 2401 → 343 → 49 → 7 → 1 Hz. Cadence non mesurée.",
    "Hz",
    "CIBLE",
)

# Le canal des pierres est 2400, par décision du propriétaire.
# Valeurs candidates historiques, qui ne sont PAS le canal :
#   240,1 Hz (référence femtoseconde) et 2401 Hz (cible V1.2).
FREQUENCE_CANAL_HZ = Constante(
    "frequence_canal_hz",
    2400,
    "DÉCISION DU PROPRIÉTAIRE",
    "Nombre de Z, « point de poussière », battu 2400 fois par seconde. "
    "Onde qui traverse les 30 pierres. Pas une mesure.",
    "Hz",
)

FREQUENCE_FOURMI_BRUTUS_HZ = Constante(
    "frequence_fourmi_brutus_hz",
    2401,
    "DÉCISION DU PROPRIÉTAIRE",
    "La fourmi et Brutus fonctionnent à 2401 Hz « et des poussières ». "
    "Brutus est le nom du moteur, pas un insecte. "
    "Distinct des 2401 phases et de la cible V1.2, même si le nombre coïncide.",
    "Hz",
)

OBSERVATION_2400_2401 = Constante(
    "observation_2400_egal_2401_moins_1",
    2401 - 2400,
    "CALCUL EXACT",
    "2400 = 2401 − 1. Observation arithmétique, sans conclusion physique.",
)

QUOTIENT_PAS = Constante(
    "quotient_pas",
    2401 // 37,
    "CALCUL EXACT",
    "2401 / 37 = 64 + 33/37. Chaque coup avance de 64 ou 65 phases.",
    "phases",
)

RESIDU_PAS = Constante(
    "residu_pas",
    2401 % 37,
    "CALCUL EXACT",
    "2401 = 37×64 + 33.",
    "phases",
)

COTE_TEMPLE = Constante(
    "cote_temple",
    12,
    "CALCUL EXACT",
    "Temple Z144 : 12 rangées × 12 colonnes.",
)

CELLULES_TEMPLE = Constante(
    "cellules_temple",
    144,
    "CALCUL EXACT",
    "12×12 = 144 cellules, index 0..143.",
)

GRAINES = Constante(
    "graines",
    (4, 7, 9, 12, 13, 16),
    "DOCUMENTÉ",
    "Six indices communs des roues A et B. Pas la liste de douze termes de l'Horloge de Vie v0.1.",
)

CYCLE_COUPS = Constante(
    "cycle_coups",
    37 * 144,
    "CALCUL EXACT",
    "ppcm(37, 144) = 5328 coups, soit 144 secondes idéales. Période de compteurs.",
    "coups",
)

# --- Six roues et anneau ---

VITESSES_ROUES = Constante(
    "vitesses_roues",
    (2, 3, 4, 5, 6, 7),
    "DÉCISION DU PROPRIÉTAIRE",
    "Six roues qui avancent de 2, 3, 4, 5, 6 et 7 unités par tic.",
)

TAILLE_ANNEAU = Constante(
    "taille_anneau",
    3 * 7 * 13,
    "CANDIDAT",
    "Anneau de 273 = 3×7×13. La spec et le README connaissent 273 ; "
    "l'usage comme anneau commun des six roues est une modélisation à confirmer.",
    "positions",
)

# --- Stonehenge idéal ---

NOMBRE_ROCHES = Constante(
    "nombre_roches",
    30,
    "DOCUMENTÉ",
    "Grille idéale : 30 positions. 360°/30 = 12°. Pas une métrologie du site réel.",
)

DEGRES_PAR_ROCHE = Constante(
    "degres_par_roche",
    12,
    "CALCUL EXACT",
    "360/30 = 12 degrés par position, sur la grille de 30.",
    "degrés",
)

# --- Polybrutus ---

GRAINES_K = Constante(
    "familles_k",
    (4, 7, 9, 12, 13, 16),
    "DOCUMENTÉ",
    "Familles de distances après normalisation k = 4d²/R². "
    "La liste coïncide avec les graines ; un avantage dynamique reste CANDIDAT.",
)

# --- Colonie : phrases du README, ligne 30 ---

ROLES_COLONIE = (
    ("fourmi", "La Fourmi porte la mémoire, la stigmergie et le routage."),
    ("abeille", "L'Abeille cherche le quorum et le consensus."),
    ("scarabee", "Le Scarabée transporte et transforme."),
    ("papillon", "Le Papillon explore de nouvelles représentations."),
    ("mante", "La Mante sélectionne et inhibe."),
    ("libellule", "La Libellule observe les anomalies."),
    ("termite", "La Termite rend la construction persistante."),
)

# --- Base 39 ---

# Aucun alphabet base 39 n'existe dans le dépôt (recherche : base39, base 39, b39, BASE39).
# Les occurrences « b39… » sont des empreintes hexadécimales, pas un encodeur.
ALPHABET_BASE39 = Constante(
    "alphabet_base39",
    "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ-_.",
    "CANDIDAT",
    "Alphabet par défaut, à confirmer par le propriétaire : "
    "0-9, A-Z, puis « - », « _ » et « . » (symboles sûrs pour une URL).",
)

# --- Cristallisation documentée 8 → 7 + 1 ---

SEUIL_CRISTAL = Constante(
    "seuil_cristal",
    8,
    "DOCUMENTÉ",
    "Règle 8 → 7 + 1 : huit observations, dont sept promues et une laissée libre. "
    "La version antérieure 50 → 49 + 1 n'est pas interchangeable. Le détail d'accumulation est CANDIDAT.",
)

# --- Épitagores et capsule : définitions absentes des sources ---

DIMENSION_EPITAGORE_DEPART = Constante(
    "dimension_epitagore_depart",
    6,
    "CANDIDAT",
    "Énoncé du propriétaire : passage de la sixième dimension à la suivante. Définition des 12 Épitagores introuvable.",
)

DIMENSION_EPITAGORE_ARRIVEE = Constante(
    "dimension_epitagore_arrivee",
    7,
    "CANDIDAT",
    "« La dimension suivante » après la sixième. Pas une mesure.",
)

NOMBRE_EPITAGORES = Constante(
    "nombre_epitagores",
    12,
    "DÉCISION DU PROPRIÉTAIRE",
    "Douze emplacements. Le contenu de chacun est INCONNU.",
)

REGISTRE = (
    FREQUENCE_LOGIQUE_HZ,
    PHASES_PAR_TOUR,
    FREQUENCE_CIBLE_V12_HZ,
    FREQUENCE_CANAL_HZ,
    FREQUENCE_FOURMI_BRUTUS_HZ,
    OBSERVATION_2400_2401,
    QUOTIENT_PAS,
    RESIDU_PAS,
    COTE_TEMPLE,
    CELLULES_TEMPLE,
    GRAINES,
    CYCLE_COUPS,
    VITESSES_ROUES,
    TAILLE_ANNEAU,
    NOMBRE_ROCHES,
    DEGRES_PAR_ROCHE,
    GRAINES_K,
    ALPHABET_BASE39,
    SEUIL_CRISTAL,
    DIMENSION_EPITAGORE_DEPART,
    DIMENSION_EPITAGORE_ARRIVEE,
    NOMBRE_EPITAGORES,
)
