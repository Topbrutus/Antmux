"""Point d'entrée : un moteur, sa configuration, ses composants."""

from __future__ import annotations

from moteur.composants import tous
from moteur.config import charger, fragments_defaut
from moteur.noyau import Moteur


def moteur_par_defaut(config: dict | None = None) -> Moteur:
    if config is None:
        config, avertissements = charger()
    else:
        avertissements = []
    return Moteur(config, tous(), avertissements)


def moteur_nu(config: dict | None = None) -> Moteur:
    """Moteur sans lire le fichier, pour les tests déterministes."""
    return Moteur(config or fragments_defaut(), tous())
