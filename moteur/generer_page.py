"""Écrit la page statique à partir du moteur. Aucun serveur."""

from __future__ import annotations

import json
from pathlib import Path

from moteur.config import fragments_defaut, schema_defaut
from moteur.constantes import ROLES_COLONIE
from moteur.usine import moteur_nu


RACINE = Path(__file__).resolve().parent
GABARIT = RACINE / "page" / "gabarit.html"
SORTIE = RACINE / "page" / "index.html"


def rendre() -> str:
    moteur = moteur_nu()
    gabarit = GABARIT.read_text(encoding="utf-8")
    remplacements = {
        "/*__CONFIG__*/": json.dumps(fragments_defaut(), ensure_ascii=False, separators=(",", ":")),
        "/*__SCHEMA__*/": json.dumps(schema_defaut(), ensure_ascii=False, separators=(",", ":")),
        "/*__GRAINE__*/": json.dumps(moteur.exporter_graine_base39(), ensure_ascii=False),
        "/*__ROLES__*/": json.dumps(
            [{"id": cle, "phrase": phrase} for cle, phrase in ROLES_COLONIE],
            ensure_ascii=False,
            separators=(",", ":"),
        ),
    }
    html = gabarit
    for jeton, valeur in remplacements.items():
        if jeton not in html:
            raise RuntimeError(f"jeton absent du gabarit : {jeton}")
        html = html.replace(jeton, valeur)
    return html


def ecrire() -> Path:
    SORTIE.write_text(rendre(), encoding="utf-8")
    return SORTIE


if __name__ == "__main__":
    print(ecrire())
