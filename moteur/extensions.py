"""Interfaces vides. Aucune logique inventée.

TODO Cristaux de vibration : trente cristaux individuels, un par pierre
de la grille idéale, chacun entre sa roche et le cadran. Chaque tic
devra produire des vibrations différentes. À définir par le propriétaire.

TODO Lecteur de structures : recevra plus tard des relevés, des plans,
des mesures ou des modèles, et produira une lecture via le moteur.
Aucune donnée de pyramide n'est fournie ici.
"""

from __future__ import annotations


class EmplacementCristalVibration:
    """Emplacement indexable entre une roche et le cadran. Interface vide."""

    def __init__(self, index: int, nombre_positions: int) -> None:
        if nombre_positions < 1 or not 0 <= index < nombre_positions:
            raise ValueError("index de pierre hors de la grille courante")
        self.index = index
        self.nombre_positions = nombre_positions
        self.implemente = False

    def transformer(self, vibration, tic: int):
        """TODO : aucune transformation n'est définie."""
        raise NotImplementedError(
            "Cristal de vibration non défini (un par pierre, entre la roche et le cadran)."
        )

    def vers_dict(self) -> dict:
        return {
            "index": self.index,
            "implemente": False,
            "etiquette": "EXTENSION_PREVUE",
        }


def emplacements_cristaux(nombre_positions: int) -> list[EmplacementCristalVibration]:
    """Un emplacement par position. Sur la grille idéale, cela fait 30."""
    return [
        EmplacementCristalVibration(index, nombre_positions)
        for index in range(nombre_positions)
    ]


class LecteurStructures:
    """Interface vide du futur lecteur de structures cachées."""

    identifiant = "lecteur_structures"

    def lire(self, entrees):
        """TODO : aucune logique de décodage."""
        raise NotImplementedError(
            "Lecteur de structures non implémenté. Aucune donnée de pyramide n'est lue."
        )
