"""Noyau du moteur.

Il ne connaît aucun composant précis : il reçoit une liste d'objets
qui exposent identifiant, ordre, fragment, schema, au_tic et instantane.
Le point d'insertion entre Stonehenge et le cadran est un ordre libre
(40 < ordre < 50), prévu pour les trente cristaux de vibration.
"""

from __future__ import annotations

import copy
import hashlib
import json

from moteur.base39 import encoder
from moteur.config import appliquer, fragments_defaut, schema_avec, schema_defaut, valider
from moteur.constantes import VERSION
from moteur.etat import Etat


TIC_MAX_GRAINE = 100_000


def canonique(objet) -> bytes:
    return json.dumps(objet, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


class Moteur:
    def __init__(self, config: dict, composants: list, avertissements: list[str] | None = None) -> None:
        erreurs = valider(config, schema_depuis(composants, config))
        if erreurs:
            raise ValueError(" ; ".join(erreurs))
        self.config = copy.deepcopy(config)
        self.composants = sorted(composants, key=lambda c: c.ordre)
        self.avertissements = list(avertissements or [])
        self.etat = Etat(
            phase=self.config["horloge"]["phase_depart"],
            reste=self.config["horloge"]["reste_depart"],
        )

    def schema(self) -> dict:
        return schema_depuis(self.composants, self.config)

    def enregistrer(self, composant) -> None:
        """Enregistre un composant sans modifier les autres."""
        if any(item.identifiant == composant.identifiant for item in self.composants):
            raise ValueError(f"composant déjà présent : {composant.identifiant}")
        config = fusion_fragment(self.config, composant)
        self.composants.append(composant)
        self.composants.sort(key=lambda c: c.ordre)
        self.config = config

    def inserer_entre(self, composant, apres: str, avant: str) -> None:
        """Place un composant dans le pipeline, entre deux identifiants."""
        ordre_apres = self._ordre(apres)
        ordre_avant = self._ordre(avant)
        if not ordre_apres < ordre_avant:
            raise ValueError("le point d'insertion exige apres < avant")
        composant.ordre = (ordre_apres + ordre_avant) / 2
        self.enregistrer(composant)

    def _ordre(self, identifiant: str) -> int:
        for composant in self.composants:
            if composant.identifiant == identifiant:
                return composant.ordre
        raise KeyError(identifiant)

    def evolution(self) -> int:
        anneau = int(self.config["six_roues"]["anneau"])
        return self.etat.tic // anneau

    def avancer(self, n: int = 1) -> None:
        if n < 0:
            raise ValueError("tic négatif")
        for _ in range(n):
            self.etat.tic += 1
            for composant in self.composants:
                composant.au_tic(self.etat, self.config)
            anneau = int(self.config["six_roues"]["anneau"])
            if anneau > 0 and self.etat.tic % anneau == 0 and self.etat.sain():
                self.etat.cycles_sains += 1

    def instantane(self) -> dict:
        return {
            "version": VERSION,
            "tic": self.etat.tic,
            "evolution": self.evolution(),
            "cycles_sains": self.etat.cycles_sains,
            "sain": self.etat.sain(),
            "avertissements": list(self.avertissements),
            "composants": {
                composant.identifiant: composant.instantane(self.etat, self.config)
                for composant in self.composants
            },
        }

    def reinitialiser(self) -> None:
        neuf = fragments_defaut()
        for composant in self.composants:
            if composant.identifiant not in neuf and hasattr(composant, "fragment"):
                neuf[composant.identifiant] = copy.deepcopy(composant.fragment())
        self.config = neuf
        self.etat = Etat(
            phase=self.config["horloge"]["phase_depart"],
            reste=self.config["horloge"]["reste_depart"],
        )

    def exporter_graine(self) -> dict:
        payload = {
            "version": VERSION,
            "tic": self.etat.tic,
            "evolution": self.evolution(),
            "config": self.config,
        }
        graine = dict(payload)
        graine["empreinte"] = _empreinte(payload)
        return graine

    def exporter_graine_base39(self) -> str:
        return encoder(canonique(self.exporter_graine()))


def schema_depuis(composants: list, config: dict | None = None) -> dict:
    schema = schema_defaut()
    for composant in composants:
        if composant.identifiant in schema["champs"]:
            continue
        if hasattr(composant, "schema_fragment"):
            schema = schema_avec(schema, composant.identifiant, composant.schema_fragment())
    return schema


def fusion_fragment(config: dict, composant) -> dict:
    if composant.identifiant in config or not hasattr(composant, "fragment"):
        return config
    sortie = copy.deepcopy(config)
    sortie[composant.identifiant] = copy.deepcopy(composant.fragment())
    erreurs = valider(sortie, schema_depuis([composant], sortie))
    # schema_depuis starts from default and adds unknown components only.
    # Validate the new key with a targeted schema if the full one fails
    # because other keys exist. The default schema plus the new fragment
    # accepts the merged document when the fragment is valid.
    if erreurs:
        raise ValueError(" ; ".join(erreurs))
    return sortie


def _empreinte(payload: dict) -> str:
    digest = hashlib.sha256(canonique(payload)).digest()
    return encoder(digest)


def verifier_graine(graine: dict, composants: list) -> list[str]:
    """Retourne les anomalies. Liste vide si la graine est intacte."""
    try:
        _controler_graine(graine, composants)
    except ValueError as exc:
        return [str(exc)]
    return []


def reconstruire_depuis_graine(graine: dict, composants: list) -> Moteur:
    _controler_graine(graine, composants)
    moteur = Moteur(graine["config"], composants)
    moteur.avancer(int(graine["tic"]))
    if moteur.evolution() != graine["evolution"]:
        raise ValueError("graine corrompue : l'évolution ne correspond pas au tic")
    return moteur


def _controler_graine(graine: dict, composants: list) -> None:
    if not isinstance(graine, dict):
        raise ValueError("graine corrompue : objet attendu")
    for cle in ("version", "tic", "evolution", "config", "empreinte"):
        if cle not in graine:
            raise ValueError(f"graine corrompue : champ manquant ({cle})")
    if type(graine["tic"]) is not int or not 0 <= graine["tic"] <= TIC_MAX_GRAINE:
        raise ValueError("graine corrompue : tic hors bornes")
    if type(graine["evolution"]) is not int or graine["evolution"] < 0:
        raise ValueError("graine corrompue : évolution invalide")
    payload = {
        "version": graine["version"],
        "tic": graine["tic"],
        "evolution": graine["evolution"],
        "config": graine["config"],
    }
    if graine["empreinte"] != _empreinte(payload):
        raise ValueError("graine corrompue : empreinte invalide")
    erreurs = valider(graine["config"], schema_depuis(composants, graine["config"]))
    if erreurs:
        raise ValueError("graine corrompue : " + " ; ".join(erreurs))


def appliquer_config(moteur: Moteur, candidat: dict) -> dict:
    return appliquer(moteur, candidat)


def resume(moteur: Moteur) -> dict:
    """Résumé stable, partagé avec le client de la page pour la parité."""
    from moteur.calculs import (
        alignees,
        echo_roche,
        position_roche,
        position_roue,
        premier_tic_convergence,
    )

    config = moteur.config
    etat = moteur.etat
    roues = config["six_roues"]["roues"]
    anneau = config["six_roues"]["anneau"]
    roches = config["stonehenge"]["roches"]
    courant = config["stonehenge"]["courant_amplificateur"]
    cote = config["temple"]["cote"]
    return {
        "tic": etat.tic,
        "phase": etat.phase,
        "reste": etat.reste,
        "evolution": moteur.evolution(),
        "cycles_sains": etat.cycles_sains,
        "quorum": alignees(roues, etat.tic, anneau),
        "convergence": premier_tic_convergence(roues, anneau),
        "roche": position_roche(etat.tic, len(roches)),
        "pos0": position_roue(roues[0], etat.tic, anneau),
        "cristaux": len(etat.cristaux),
        "resonance": "dissonant" if not etat.sain() else "harmonieux",
        "echo0": echo_roche(roches[0]["gain"], courant, roches[0]["etat"]),
        "index_temple": etat.tic % (cote * cote),
        "canal": config["canal"]["frequence_hz"],
        "fourmi": config["canal"]["frequence_fourmi_brutus_hz"],
    }
