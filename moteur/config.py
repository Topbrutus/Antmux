"""Configuration : valeurs par défaut, schéma, validation.

Une configuration invalide est refusée. L'appelant garde la précédente.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path


FICHIER_DEFAUT = Path(__file__).with_name("moteur.config.json")


def _entier(label: str, minimum: int, maximum: int, **extra) -> dict:
    regle = {"type": "int", "min": minimum, "max": maximum, "label": label}
    regle.update(extra)
    return regle


def _bool(label: str) -> dict:
    return {"type": "bool", "label": label}


def _str(label: str, min_len: int = 1, max_len: int = 80) -> dict:
    return {"type": "str", "min_len": min_len, "max_len": max_len, "label": label}


def fragments_defaut() -> dict:
    roches = []
    for index in range(30):
        roches.append({
            "index": index,
            "etat": "installee",
            "gain": 100 + index,
            "delai": index,
            "timbre": 17 + index * 3,
        })
    roues = []
    for vitesse in (2, 3, 4, 5, 6, 7):
        roues.append({
            "id": f"r{vitesse}",
            "vitesse": vitesse,
            "depart": 0,
            "actif": True,
        })
    return {
        "version": "0.1.0",
        "horloge": {
            "frequence_logique_hz": 37,
            "phases_par_tour": 2401,
            "phase_depart": 0,
            "reste_depart": 0,
        },
        "roues_abz": {"graines": [4, 7, 9, 12, 13, 16]},
        "six_roues": {"anneau": 273, "roues": roues},
        "stonehenge": {
            "courant_amplificateur": 40,
            "roches": roches,
        },
        "cadran": {"visible": True},
        "polybrutus": {"rotation_depart": 0},
        "temple": {"cote": 12},
        "colonie": {"actif": True},
        "cristallisation": {
            "seuil": 8,
            "promus": 7,
            "libre": 1,
            "niveau_max": 7,
        },
        "capsule": {"visible": True},
        "pyramide": {"visible": True},
        "epitagores": {"contenus": [None] * 12},
        "lecteur_structures": {"actif": False},
        "canal": {
            "frequence_hz": 2400,
            "frequence_fourmi_brutus_hz": 2401,
        },
    }


def schema_defaut() -> dict:
    return {
        "type": "objet",
        "label": "Moteur",
        "champs": {
            "version": {"type": "str", "enum": ["0.1.0"], "label": "Version"},
            "horloge": {
                "type": "objet",
                "label": "Horloge",
                "champs": {
                    "frequence_logique_hz": _entier("Fréquence logique (Hz)", 1, 100000),
                    "phases_par_tour": _entier("Phases par tour", 1, 1000000),
                    "phase_depart": _entier("Phase de départ", 0, 1000000),
                    "reste_depart": _entier("Reste de départ", 0, 1000000),
                },
                "regles": [
                    {"type": "inferieur", "champ": "phase_depart", "borne": "phases_par_tour"},
                    {"type": "inferieur", "champ": "reste_depart", "borne": "frequence_logique_hz"},
                ],
            },
            "roues_abz": {
                "type": "objet",
                "label": "Roues A et B",
                "champs": {
                    "graines": {
                        "type": "liste",
                        "label": "Graines",
                        "min": 1,
                        "max": 12,
                        "item": _entier("Graine", 1, 80),
                    },
                },
            },
            "six_roues": {
                "type": "objet",
                "label": "Six roues",
                "champs": {
                    "anneau": _entier("Taille de l'anneau", 2, 100000),
                    "roues": {
                        "type": "liste",
                        "label": "Roues",
                        "min": 1,
                        "max": 12,
                        "cle_unique": "id",
                        "item": {
                            "type": "objet",
                            "champs": {
                                "id": _str("Identifiant"),
                                "vitesse": _entier("Vitesse", 1, 100000),
                                "depart": _entier("Position de départ", 0, 1000000),
                                "actif": _bool("Active"),
                            },
                        },
                    },
                },
                "regles": [
                    {"type": "depart_dans_anneau", "liste": "roues", "anneau": "anneau"},
                ],
            },
            "stonehenge": {
                "type": "objet",
                "label": "Stonehenge",
                "champs": {
                    "courant_amplificateur": _entier("Courant amplificateur", 0, 100),
                    "roches": {
                        "type": "liste",
                        "label": "Roches",
                        "min": 1,
                        "max": 60,
                        "item": {
                            "type": "objet",
                            "champs": {
                                "index": _entier("Index", 0, 59),
                                "etat": {
                                    "type": "str",
                                    "enum": ["installee", "reservee"],
                                    "label": "État",
                                },
                                "gain": _entier("Gain", 0, 10000),
                                "delai": _entier("Délai", 0, 10000),
                                "timbre": _entier("Timbre", 0, 10000),
                            },
                        },
                    },
                },
                "regles": [{"type": "indices_ordonnes", "liste": "roches"}],
            },
            "cadran": {
                "type": "objet",
                "label": "Cadran",
                "champs": {"visible": _bool("Visible")},
            },
            "polybrutus": {
                "type": "objet",
                "label": "Polybrutus",
                "champs": {
                    "rotation_depart": _entier("Rotation de départ (pas de 12°)", 0, 29),
                },
            },
            "temple": {
                "type": "objet",
                "label": "Temple Z144",
                "champs": {"cote": _entier("Côté de la grille", 1, 24)},
            },
            "colonie": {
                "type": "objet",
                "label": "Colonie",
                "champs": {"actif": _bool("Active")},
            },
            "cristallisation": {
                "type": "objet",
                "label": "Cristallisation",
                "champs": {
                    "seuil": _entier("Seuil d'observations", 2, 64),
                    "promus": _entier("Promus", 1, 63),
                    "libre": _entier("Libre", 1, 63),
                    "niveau_max": _entier("Niveau maximum", 1, 7),
                },
                "regles": [{"type": "somme", "a": "promus", "b": "libre", "egal": "seuil"}],
            },
            "capsule": {
                "type": "objet",
                "label": "Capsule",
                "champs": {"visible": _bool("Visible")},
            },
            "pyramide": {
                "type": "objet",
                "label": "Pyramide de quartz",
                "champs": {"visible": _bool("Visible")},
            },
            "epitagores": {
                "type": "objet",
                "label": "Épitagores",
                "champs": {
                    "contenus": {
                        "type": "liste",
                        "label": "Contenus",
                        "min": 12,
                        "max": 12,
                        "item": {
                            "type": "null_ou_str",
                            "max_len": 200,
                            "label": "Contenu",
                        },
                    },
                },
            },
            "lecteur_structures": {
                "type": "objet",
                "label": "Lecteur de structures",
                "champs": {"actif": _bool("Actif")},
            },
            "canal": {
                "type": "objet",
                "label": "Fréquences",
                "champs": {
                    "frequence_hz": _entier("Canal des pierres (Hz)", 1, 20000),
                    "frequence_fourmi_brutus_hz": _entier("Fourmi et Brutus (Hz)", 1, 20000),
                },
            },
        },
    }


def schema_avec(schema: dict, identifiant: str, fragment_schema: dict) -> dict:
    """Ajoute le schéma d'un composant enregistré après coup."""
    sortie = copy.deepcopy(schema)
    sortie["champs"][identifiant] = fragment_schema
    return sortie


def fusionner_fragment(config: dict, identifiant: str, fragment: dict) -> dict:
    sortie = copy.deepcopy(config)
    sortie.setdefault(identifiant, copy.deepcopy(fragment))
    return sortie


def valider(config: dict, schema: dict | None = None) -> list[str]:
    if schema is None:
        schema = schema_defaut()
    return _valider_valeur(config, schema, "config")


def _valider_valeur(valeur, regle: dict, chemin: str) -> list[str]:
    type_attendu = regle["type"]
    if type_attendu == "int":
        if type(valeur) is not int or isinstance(valeur, bool):
            return [f"{chemin} : entier attendu"]
        if valeur < regle["min"] or valeur > regle["max"]:
            return [f"{chemin} : entier hors bornes ({regle['min']}..{regle['max']}), reçu {valeur}"]
        return []
    if type_attendu == "bool":
        if type(valeur) is not bool:
            return [f"{chemin} : booléen attendu"]
        return []
    if type_attendu == "str":
        if type(valeur) is not str:
            return [f"{chemin} : texte attendu"]
        if "enum" in regle and valeur not in regle["enum"]:
            return [f"{chemin} : valeur non autorisée {valeur!r}"]
        if len(valeur) < regle.get("min_len", 0) or len(valeur) > regle.get("max_len", 10**6):
            return [f"{chemin} : longueur de texte hors bornes"]
        return []
    if type_attendu == "null_ou_str":
        if valeur is None:
            return []
        if type(valeur) is not str:
            return [f"{chemin} : texte ou vide attendu"]
        if len(valeur) > regle.get("max_len", 200):
            return [f"{chemin} : texte trop long"]
        return []
    if type_attendu == "liste":
        if not isinstance(valeur, list):
            return [f"{chemin} : liste attendue"]
        erreurs = []
        if len(valeur) < regle["min"] or len(valeur) > regle["max"]:
            erreurs.append(
                f"{chemin} : nombre d'éléments hors bornes ({regle['min']}..{regle['max']}), reçu {len(valeur)}"
            )
        for index, element in enumerate(valeur):
            erreurs.extend(_valider_valeur(element, regle["item"], f"{chemin}[{index}]"))
        cle = regle.get("cle_unique")
        if cle and not erreurs:
            vus = []
            for element in valeur:
                if isinstance(element, dict):
                    vus.append(element.get(cle))
            if len(vus) != len(set(vus)):
                erreurs.append(f"{chemin} : identifiants en double")
        return erreurs
    if type_attendu == "objet":
        return _valider_objet(valeur, regle, chemin)
    return [f"{chemin} : type de schéma inconnu"]


def _valider_objet(valeur, regle: dict, chemin: str) -> list[str]:
    if not isinstance(valeur, dict):
        return [f"{chemin} : objet attendu"]
    erreurs = []
    champs = regle["champs"]
    for cle in valeur:
        if cle not in champs:
            erreurs.append(f"{chemin}.{cle} : champ inconnu")
    for cle, sous in champs.items():
        if cle not in valeur:
            erreurs.append(f"{chemin}.{cle} : champ manquant")
        else:
            erreurs.extend(_valider_valeur(valeur[cle], sous, f"{chemin}.{cle}"))
    if erreurs:
        return erreurs
    for spec in regle.get("regles", []):
        erreurs.extend(_regle(spec, valeur, chemin))
    return erreurs


def _regle(spec: dict, objet: dict, chemin: str) -> list[str]:
    genre = spec["type"]
    if genre == "inferieur":
        if objet[spec["champ"]] >= objet[spec["borne"]]:
            return [f"{chemin}.{spec['champ']} : doit être strictement inférieur à {spec['borne']}"]
        return []
    if genre == "somme":
        if objet[spec["a"]] + objet[spec["b"]] != objet[spec["egal"]]:
            return [f"{chemin} : {spec['a']} + {spec['b']} doit égaler {spec['egal']}"]
        return []
    if genre == "depart_dans_anneau":
        anneau = objet[spec["anneau"]]
        erreurs = []
        for index, roue in enumerate(objet[spec["liste"]]):
            if roue["depart"] >= anneau:
                erreurs.append(
                    f"{chemin}.{spec['liste']}[{index}].depart : doit être < {anneau} (taille de l'anneau)"
                )
        return erreurs
    if genre == "indices_ordonnes":
        erreurs = []
        for index, roche in enumerate(objet[spec["liste"]]):
            if roche["index"] != index:
                erreurs.append(f"{chemin}.{spec['liste']}[{index}].index : doit valoir {index}")
        return erreurs
    return [f"{chemin} : règle inconnue"]


def appliquer(moteur, candidat: dict) -> dict:
    erreurs = valider(candidat, moteur.schema())
    if erreurs:
        return {"ok": False, "erreurs": erreurs}
    moteur.config = copy.deepcopy(candidat)
    return {"ok": True, "erreurs": []}


def charger(chemin: Path | None = None) -> tuple[dict, list[str]]:
    """Charge le fichier. S'il est illisible ou invalide, rend les défauts."""
    fichier = chemin or FICHIER_DEFAUT
    defaut = fragments_defaut()
    try:
        texte = fichier.read_text(encoding="utf-8")
        donnees = json.loads(texte)
    except (OSError, json.JSONDecodeError) as exc:
        return defaut, [f"fichier de configuration inutilisable ({exc}). Défauts conservés."]
    erreurs = valider(donnees)
    if erreurs:
        return defaut, erreurs
    return donnees, []


def enregistrer(config: dict, chemin: Path | None = None) -> None:
    fichier = chemin or FICHIER_DEFAUT
    fichier.write_text(
        json.dumps(config, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def marquer_roche(config: dict, index: int, etat: str) -> dict:
    sortie = copy.deepcopy(config)
    sortie["stonehenge"]["roches"][index]["etat"] = etat
    return sortie


def ajouter_roche_reservee(config: dict) -> dict:
    sortie = copy.deepcopy(config)
    roches = sortie["stonehenge"]["roches"]
    index = len(roches)
    roches.append({
        "index": index,
        "etat": "reservee",
        "gain": 100 + index,
        "delai": index,
        "timbre": 17 + index * 3,
    })
    return sortie
