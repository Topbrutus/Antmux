"""Composants enregistrés du moteur v0.1.

Chacun expose identifiant, ordre, au_tic et instantane.
Le noyau ne les importe pas : `tous()` les assemble.
"""

from __future__ import annotations

from moteur.calculs import (
    alertes_grille,
    alignees,
    decomposer_base7,
    echo_roche,
    ensemble_roches,
    etages_en_sept,
    familles_k,
    fibonacci,
    index_temple,
    intensite,
    ligne_colonne,
    observer_cristal,
    position_roche,
    position_roue,
    premier,
    premier_tic_convergence,
    projection_polybrutus,
    somme_k,
)
from moteur.constantes import (
    FREQUENCE_CANAL_HZ,
    FREQUENCE_FOURMI_BRUTUS_HZ,
    ROLES_COLONIE,
)
from moteur.extensions import LecteurStructures, emplacements_cristaux


class Horloge:
    identifiant = "horloge"
    ordre = 10

    def au_tic(self, etat, config) -> None:
        from moteur.calculs import avancer_horloge

        bloc = config["horloge"]
        phase, reste, pas = avancer_horloge(
            etat.phase,
            etat.reste,
            bloc["phases_par_tour"],
            bloc["frequence_logique_hz"],
            1,
        )
        etat.phase = phase
        etat.reste = reste
        etat.dernier_pas = pas[0]

    def instantane(self, etat, config) -> dict:
        bloc = config["horloge"]
        chiffres = None
        if 0 <= etat.phase < bloc["phases_par_tour"] and bloc["phases_par_tour"] >= 343:
            try:
                chiffres = decomposer_base7(etat.phase, bloc["phases_par_tour"])
            except ValueError:
                chiffres = None
        return {
            "etiquette_frequence": "DOCUMENTÉ",
            "etiquette_phases": "CALCUL EXACT",
            "frequence_logique_hz": bloc["frequence_logique_hz"],
            "phases_par_tour": bloc["phases_par_tour"],
            "phase": etat.phase,
            "reste": etat.reste,
            "dernier_pas": etat.dernier_pas,
            "coup": etat.tic,
            "chiffres_base7": None if chiffres is None else list(chiffres),
            "note": "37 Hz est une fréquence logique. 2401 phases ne sont pas le canal 2400 Hz.",
        }


class RouesABZ:
    identifiant = "roues_abz"
    ordre = 20

    def au_tic(self, etat, config) -> None:
        return None

    def instantane(self, etat, config) -> dict:
        lignes = []
        for graine in config["roues_abz"]["graines"]:
            lignes.append({
                "graine": graine,
                "a": fibonacci(graine),
                "b": premier(graine),
            })
        return {
            "convention_fibonacci": "F(0)=0, F(1)=1, graine n → F(n)",
            "convention_premiers": "n-ième premier, p(1)=2",
            "etiquette": "DOCUMENTÉ",
            "table": lignes,
            "etages_z": list(etages_en_sept()),
            "etiquette_etages": "CALCUL EXACT",
            "note_hz": "Lus comme des hertz, ces étages sont la cible V1.2, non une cadence mesurée.",
            "listes_v01_non_substituees": {
                "a": [1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233],
                "b": [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37],
                "etiquette": "DOCUMENTÉ",
            },
        }


class SixRoues:
    identifiant = "six_roues"
    ordre = 30

    def au_tic(self, etat, config) -> None:
        return None

    def instantane(self, etat, config) -> dict:
        bloc = config["six_roues"]
        roues = []
        for roue in bloc["roues"]:
            roues.append({
                "id": roue["id"],
                "vitesse": roue["vitesse"],
                "depart": roue["depart"],
                "actif": roue["actif"],
                "position": position_roue(roue, etat.tic, bloc["anneau"]),
            })
        convergence = premier_tic_convergence(bloc["roues"], bloc["anneau"])
        return {
            "etiquette_anneau": "CANDIDAT",
            "note": "L'anneau de 273 est une modélisation à confirmer par le propriétaire.",
            "anneau": bloc["anneau"],
            "roues": roues,
            "quorum": alignees(bloc["roues"], etat.tic, bloc["anneau"]),
            "convergence": convergence,
            "convergence_atteinte": convergence is not None and etat.tic > 0 and etat.tic % convergence == 0,
        }


class Stonehenge:
    identifiant = "stonehenge"
    ordre = 40

    def au_tic(self, etat, config) -> None:
        return None

    def instantane(self, etat, config) -> dict:
        bloc = config["stonehenge"]
        canal = config["canal"]
        roches = []
        for roche in bloc["roches"]:
            roches.append({
                "index": roche["index"],
                "etat": roche["etat"],
                "gain": roche["gain"],
                "delai": roche["delai"],
                "timbre": roche["timbre"],
                "echo": echo_roche(roche["gain"], bloc["courant_amplificateur"], roche["etat"]),
                "etiquette_profil": "CANDIDAT",
            })
        nombre = len(roches)
        active = etat.tic % nombre
        emplacements = [item.vers_dict() for item in emplacements_cristaux(nombre)]
        return {
            "concept": (
                "Récit du propriétaire, sans affirmation scientifique ni archéologique : "
                "le cercle émettait des vibrations basses ; le moteur les remplace par sa fréquence, "
                "qui passe à travers les pierres. But : changer les fréquences, pas reconstruire le site."
            ),
            "ancienne_frequence": {
                "etiquette": "ancienne fréquence",
                "aspect": "basse, sourde, terne, lente",
                "etat": "remplacee_progressivement",
            },
            "canal_hz": canal["frequence_hz"],
            "etiquette_canal": FREQUENCE_CANAL_HZ.etiquette,
            "fourmi_brutus_hz": canal["frequence_fourmi_brutus_hz"],
            "etiquette_fourmi": FREQUENCE_FOURMI_BRUTUS_HZ.etiquette,
            "courant_amplificateur": bloc["courant_amplificateur"],
            "etiquette_courant": "CANDIDAT",
            "roches": roches,
            "nombre": nombre,
            "active": active,
            "grille_30": nombre == 30,
            "alertes": alertes_grille(nombre),
            "resonance": "dissonant" if not etat.sain() else "harmonieux",
            "cycles_sains": etat.cycles_sains,
            "intensite": intensite(bloc["roches"], bloc["courant_amplificateur"]),
            "emplacements_cristaux": emplacements,
            "note_cristaux": (
                "Trente emplacements prévus sur la grille idéale, un par pierre, "
                "entre la roche et le cadran. Interface vide."
            ),
        }


class Cadran:
    """Voisin du pipeline, juste après Stonehenge. Les cristaux s'insèrent entre les deux."""

    identifiant = "cadran"
    ordre = 50

    def au_tic(self, etat, config) -> None:
        return None

    def instantane(self, etat, config) -> dict:
        return {
            "visible": config["cadran"]["visible"],
            "tic": etat.tic,
            "phase": etat.phase,
            "canal_hz": config["canal"]["frequence_hz"],
            "fourmi_brutus_hz": config["canal"]["frequence_fourmi_brutus_hz"],
            "note": "Le cadran affiche l'état. Il ne calcule pas une vibration propre.",
        }


class Polybrutus:
    identifiant = "polybrutus"
    ordre = 60

    def au_tic(self, etat, config) -> None:
        return None

    def instantane(self, etat, config) -> dict:
        rotation = (etat.tic + config["polybrutus"]["rotation_depart"]) % 30
        points = projection_polybrutus(rotation)
        familles = familles_k()
        return {
            "rotation": rotation,
            "points": points,
            "ensemble": sorted(ensemble_roches(rotation)),
            "familles": familles,
            "somme_k": somme_k(),
            "rapport": "12/21 = 4/7",
            "centroide": "(0, 0, R/14)",
            "grille_compatible": len(config["stonehenge"]["roches"]) == 30,
            "note": (
                "Un heptagone régulier ne s'emboîte pas dans 30 (pgcd(7, 30) = 1). "
                "C'est la forme du Polybrutus qui s'emboîte. "
                "Coïncidence géométrique exacte, pas une preuve physique."
            ),
        }


class Temple:
    identifiant = "temple"
    ordre = 70

    def au_tic(self, etat, config) -> None:
        return None

    def instantane(self, etat, config) -> dict:
        cote = config["temple"]["cote"]
        cellules = cote * cote
        index = etat.tic % cellules
        ligne, colonne = ligne_colonne(index, cote)
        return {
            "cote": cote,
            "cellules": cellules,
            "index0": index,
            "ligne": ligne,
            "colonne": colonne,
            "formule": "index0 = cote×(ligne−1)+(colonne−1)",
            "etiquette_formule": "CALCUL EXACT",
            "etiquette_couplage": "CANDIDAT",
            "note_couplage": "index0 = tic mod (cote²) est la convention v0.1 qui réalise la période annoncée.",
            "grille": [index_temple(lig, col, cote) for lig in range(1, cote + 1) for col in range(1, cote + 1)],
        }


class Colonie:
    identifiant = "colonie"
    ordre = 80

    def au_tic(self, etat, config) -> None:
        return None

    def instantane(self, etat, config) -> dict:
        bloc_roues = config["six_roues"]
        canal = config["canal"]
        nombre = len(config["stonehenge"]["roches"])
        roche = etat.tic % nombre
        precedente = (etat.tic - 1) % nombre if etat.tic else 0
        anneau = bloc_roues["anneau"]
        anomalies = []
        if etat.force_anomalie:
            anomalies.append("anomalie forcée")
        if etat.graine_corrompue:
            anomalies.append("graine corrompue")
        if not 0 <= etat.phase < config["horloge"]["phases_par_tour"]:
            anomalies.append("phase hors tour")
        quorum = alignees(bloc_roues["roues"], etat.tic, anneau)
        roles = []
        textes = dict(ROLES_COLONIE)
        activites = {
            "fourmi": {
                "activite": "mémorise et route l'état",
                "frequence_hz": canal["frequence_fourmi_brutus_hz"],
                "route": {"phase": etat.phase, "roche": roche, "tic": etat.tic},
            },
            "abeille": {
                "activite": "vérifie le consensus des six roues",
                "quorum": quorum,
            },
            "scarabee": {
                "activite": "transporte l'onde d'une pierre à l'autre",
                "frequence_hz": canal["frequence_hz"],
                "de": precedente,
                "vers": roche,
            },
            "papillon": {
                "activite": "trace la lemniscate des phases de l'anneau",
                "r": etat.tic % anneau,
                "q": etat.tic // anneau,
                "formule": "x = sin(2π r / N), y = ½ sin(4π r / N), z = alpha × q",
                "alpha": "INCONNU",
            },
            "mante": {
                "activite": "inhibe les états invalides",
                "inhibe": bool(anomalies),
            },
            "libellule": {
                "activite": "signale les anomalies",
                "anomalies": anomalies,
            },
            "termite": {
                "activite": "persiste le compteur d'évolution",
                "evolution": etat.tic // anneau,
            },
        }
        for cle, phrase in ROLES_COLONIE:
            roles.append({
                "id": cle,
                "phrase": textes[cle],
                "etiquette_branchement": "CANDIDAT",
                **activites[cle],
            })
        return {
            "porteur": "une même Fourmi",
            "note": "Sept régimes, pas nécessairement sept machines. Brutus n'est pas un insecte.",
            "brutus": "nom du moteur",
            "regimes": roles,
        }


class Cristallisation:
    identifiant = "cristallisation"
    ordre = 90

    def au_tic(self, etat, config) -> None:
        regle = config["cristallisation"]
        cle = "sain" if etat.sain() else "anomalie"
        observer_cristal(etat, cle, regle["seuil"], regle["promus"], regle["niveau_max"])

    def instantane(self, etat, config) -> dict:
        regle = config["cristallisation"]
        return {
            "etiquette_regle": "DOCUMENTÉ",
            "etiquette_accumulation": "CANDIDAT",
            "seuil": regle["seuil"],
            "promus": regle["promus"],
            "libre": regle["libre"],
            "niveau_max": regle["niveau_max"],
            "cristaux": list(etat.cristaux),
            "en_attente": [len(pile) for pile in etat.piles],
            "note": "8 observations → 7 promues + 1 libre. L'enrichissement cycle après cycle est CANDIDAT.",
        }


class Capsule:
    identifiant = "capsule"
    ordre = 100

    def au_tic(self, etat, config) -> None:
        return None

    def instantane(self, etat, config) -> dict:
        cote = config["temple"]["cote"]
        index = etat.tic % (cote * cote)
        ligne, colonne = ligne_colonne(index, cote)
        return {
            "etiquette": "CANDIDAT",
            "definition_trouvee": False,
            "visible": config["capsule"]["visible"],
            "phase": etat.phase,
            "coup": etat.tic,
            "index_temple": index,
            "ligne": ligne,
            "colonne": colonne,
            "note": (
                "Le mot « capsule » n'apparaît ni dans le README, ni dans la spec, ni dans le dépôt. "
                "Écrin d'affichage seulement. Le propriétaire doit préciser sa fonction, "
                "son contenu et sa place."
            ),
        }


class Pyramide:
    identifiant = "pyramide"
    ordre = 110

    def au_tic(self, etat, config) -> None:
        return None

    def instantane(self, etat, config) -> dict:
        return {
            "visible": config["pyramide"]["visible"],
            "motif": "pyramide de quartz",
            "etiquette": "CANDIDAT",
            "note": "Motif visuel. Aucune propriété physique du quartz n'est affirmée.",
        }


class Epitagores:
    identifiant = "epitagores"
    ordre = 120

    def au_tic(self, etat, config) -> None:
        return None

    def instantane(self, etat, config) -> dict:
        contenus = config["epitagores"]["contenus"]
        return {
            "etiquette": "CANDIDAT",
            "definition_trouvee": False,
            "dimension_depart": 6,
            "dimension_arrivee": 7,
            "enonce": (
                "Les 12 Épitagores permettent de passer avec le Polybrutus "
                "de la sixième dimension à la dimension suivante."
            ),
            "emplacements": [
                {
                    "index": index + 1,
                    "contenu": contenu,
                    "etiquette": "INCONNU" if contenu is None else "CANDIDAT",
                }
                for index, contenu in enumerate(contenus)
            ],
            "correspondances": [
                {
                    "nom": "grille Z144",
                    "etiquette": "CANDIDAT",
                    "note": "Le nombre 12 coïncide. L'identité n'est pas établie.",
                },
                {
                    "nom": "12 paires nord-sud",
                    "etiquette": "CANDIDAT",
                    "note": "Autre douze. La famille k = 12 compte 6 paires.",
                },
                {
                    "nom": "triplets de Pythagore",
                    "etiquette": "CANDIDAT",
                    "note": "Le sens des « 12 de Pythagore » reste indéterminé dans la spec.",
                },
            ],
        }


class Lecteur:
    identifiant = "lecteur_structures"
    ordre = 130

    def __init__(self) -> None:
        self._interface = LecteurStructures()

    def au_tic(self, etat, config) -> None:
        return None

    def instantane(self, etat, config) -> dict:
        return {
            "statut": "NON_IMPLEMENTE",
            "etiquette": "EXTENSION_PREVUE",
            "actif": config["lecteur_structures"]["actif"],
            "entrees_attendues": ["relevés", "plans", "mesures", "modèles"],
            "note": "Interface vide. Aucune lecture et aucune donnée de pyramide.",
        }

    def lire(self, entrees):
        return self._interface.lire(entrees)


def tous() -> list:
    return [
        Horloge(),
        RouesABZ(),
        SixRoues(),
        Stonehenge(),
        Cadran(),
        Polybrutus(),
        Temple(),
        Colonie(),
        Cristallisation(),
        Capsule(),
        Pyramide(),
        Epitagores(),
        Lecteur(),
    ]
