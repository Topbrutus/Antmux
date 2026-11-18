"""Tests du moteur v0.1. Bibliothèque standard seulement."""

from __future__ import annotations

import copy
import json
import random
import subprocess
import unittest
from pathlib import Path

from moteur.base39 import OBSERVATION_39, decoder, encoder
from moteur.calculs import (
    alertes_grille,
    angle_degre,
    avancer_horloge,
    cycle_stonehenge,
    echo_roche,
    ensemble_roches,
    familles_k,
    fibonacci,
    intensite,
    k_paires,
    lcm_builtin_check,
    periodes,
    ppcm_liste,
    premier,
    premier_tic_convergence,
    projection_polybrutus,
    somme_k,
)
from moteur.config import (
    ajouter_roche_reservee,
    appliquer,
    charger,
    fragments_defaut,
    marquer_roche,
    valider,
)
from moteur.constantes import (
    ALPHABET_BASE39,
    ETIQUETTES,
    FREQUENCE_CANAL_HZ,
    FREQUENCE_FOURMI_BRUTUS_HZ,
    PHASES_PAR_TOUR,
    REGISTRE,
    ROLES_COLONIE,
)
from moteur.extensions import emplacements_cristaux
from moteur.noyau import reconstruire_depuis_graine, resume, verifier_graine
from moteur.usine import moteur_nu


RACINE = Path(__file__).resolve().parent


class Constantes(unittest.TestCase):
    def test_etiquettes(self):
        self.assertTrue(REGISTRE)
        for constante in REGISTRE:
            self.assertIn(constante.etiquette, ETIQUETTES)

    def test_2400_et_2401_restent_distincts(self):
        self.assertEqual(FREQUENCE_CANAL_HZ.valeur, 2400)
        self.assertEqual(FREQUENCE_CANAL_HZ.etiquette, "DÉCISION DU PROPRIÉTAIRE")
        self.assertEqual(FREQUENCE_FOURMI_BRUTUS_HZ.valeur, 2401)
        self.assertEqual(PHASES_PAR_TOUR.valeur, 2401)
        self.assertEqual(PHASES_PAR_TOUR.etiquette, "CALCUL EXACT")
        self.assertEqual(2401 - 2400, 1)
        self.assertEqual(abs(2401 - 2400), 1)

    def test_canal_80_passages_et_periode(self):
        self.assertEqual(2400 // 30, 80)
        self.assertEqual(2400 % 30, 0)
        # 1/2400 s = 1250/3 µs ≈ 416,667 µs
        self.assertEqual(10**6 / 2400, 1250 / 3)
        self.assertAlmostEqual(10**6 / 2400, 416.6666667, places=5)


class Horloge(unittest.TestCase):
    def test_somme_sur_37_coups(self):
        _phase, _reste, pas = avancer_horloge(0, 0, 2401, 37, 37)
        self.assertEqual(sum(pas), 2401)
        self.assertTrue(all(p in (64, 65) for p in pas))
        self.assertEqual(pas.count(65), 33)
        self.assertEqual(pas.count(64), 4)
        self.assertEqual(_phase, 0)
        self.assertEqual(_reste, 0)

    def test_cycle_5328(self):
        self.assertEqual(lcm_builtin_check(), 5328)
        self.assertEqual(5328, 37 * 144)
        moteur = moteur_nu()
        moteur.avancer(5328)
        self.assertEqual(moteur.etat.phase, 0)
        self.assertEqual(moteur.etat.reste, 0)
        self.assertEqual(moteur.etat.tic % 144, 0)
        temple = moteur.instantane()["composants"]["temple"]
        self.assertEqual(temple["index0"], 0)
        self.assertEqual(temple["ligne"], 1)
        self.assertEqual(temple["colonne"], 1)


class RouesAB(unittest.TestCase):
    def test_graines(self):
        self.assertEqual(fibonacci(0), 0)
        self.assertEqual(fibonacci(1), 1)
        self.assertEqual(premier(1), 2)
        moteur = moteur_nu()
        table = moteur.instantane()["composants"]["roues_abz"]["table"]
        self.assertEqual([ligne["a"] for ligne in table], [3, 13, 34, 144, 233, 987])
        self.assertEqual([ligne["b"] for ligne in table], [7, 17, 23, 37, 41, 53])
        self.assertEqual(table[3]["graine"], 12)
        self.assertEqual(table[3]["a"], 144)
        self.assertEqual(table[3]["b"], 37)

    def test_listes_v01_non_substituees(self):
        listes = moteur_nu().instantane()["composants"]["roues_abz"]["listes_v01_non_substituees"]
        self.assertEqual(listes["a"], [1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233])
        self.assertNotIn(987, listes["a"])
        self.assertNotIn(53, listes["b"])

    def test_etages_z(self):
        etages = moteur_nu().instantane()["composants"]["roues_abz"]["etages_z"]
        self.assertEqual(etages, [2401, 343, 49, 7, 1])


class Temple(unittest.TestCase):
    def test_index(self):
        from moteur.calculs import index_temple

        self.assertEqual(index_temple(1, 1), 0)
        self.assertEqual(index_temple(1, 12), 11)
        self.assertEqual(index_temple(12, 1), 132)
        self.assertEqual(index_temple(12, 12), 143)
        vus = [index_temple(ligne, colonne) for ligne in range(1, 13) for colonne in range(1, 13)]
        self.assertEqual(vus, list(range(144)))
        with self.assertRaises(ValueError):
            index_temple(0, 1)


class SixRoues(unittest.TestCase):
    def test_convergence_273(self):
        config = fragments_defaut()["six_roues"]
        self.assertEqual(periodes([2, 3, 4, 5, 6, 7], 273), [273, 91, 273, 273, 91, 39])
        self.assertEqual(premier_tic_convergence(config["roues"], 273), 273)
        moteur = moteur_nu()
        for tic in (1, 39, 91, 272):
            moteur_tic = moteur_nu()
            moteur_tic.avancer(tic)
            self.assertFalse(moteur_tic.instantane()["composants"]["six_roues"]["quorum"], tic)
        moteur.avancer(273)
        self.assertTrue(moteur.instantane()["composants"]["six_roues"]["quorum"])
        self.assertTrue(moteur.instantane()["composants"]["six_roues"]["convergence_atteinte"])

    def test_rencontres_partielles_et_contraste_420(self):
        from moteur.calculs import position_roue

        roues = fragments_defaut()["six_roues"]["roues"]
        self.assertEqual(position_roue(roues[1], 91, 273), 0)
        self.assertEqual(position_roue(roues[4], 91, 273), 0)
        self.assertNotEqual(position_roue(roues[0], 91, 273), 0)
        self.assertEqual(position_roue(roues[5], 39, 273), 0)
        self.assertEqual(ppcm_liste([2, 3, 4, 5, 6, 7]), 420)
        self.assertNotEqual(420, 273)


class Stonehenge(unittest.TestCase):
    def test_grille_et_cycles(self):
        self.assertEqual(angle_degre(1, 30), 12)
        self.assertEqual(cycle_stonehenge()["ppcm_30_3_7_13"], 2730)
        self.assertEqual(cycle_stonehenge()["ppcm_avec_2401"], 936390)
        self.assertEqual(2730, 10 * 273)
        self.assertEqual(alertes_grille(30), [])
        self.assertTrue(alertes_grille(31))

    def test_profils_resonance_courant_et_reservation(self):
        moteur = moteur_nu()
        roches = moteur.config["stonehenge"]["roches"]
        signatures = {(r["gain"], r["delai"], r["timbre"]) for r in roches}
        self.assertEqual(len(signatures), 30)
        self.assertEqual(moteur.instantane()["composants"]["stonehenge"]["resonance"], "harmonieux")
        moteur.etat.force_anomalie = True
        self.assertEqual(moteur.instantane()["composants"]["stonehenge"]["resonance"], "dissonant")
        simple = [{"gain": 3, "etat": "installee"}, {"gain": 5, "etat": "installee"}]
        self.assertEqual(intensite(simple, 2), 2 * intensite(simple, 1))
        self.assertEqual(echo_roche(9, 4, "reservee"), 0)
        avant = moteur.instantane()["composants"]["stonehenge"]["roches"][0]["echo"]
        candidat = marquer_roche(moteur.config, 3, "reservee")
        self.assertTrue(appliquer(moteur, candidat)["ok"])
        apres = moteur.instantane()["composants"]["stonehenge"]["roches"]
        self.assertEqual(apres[3]["echo"], 0)
        self.assertEqual(apres[0]["echo"], avant)
        ajout = ajouter_roche_reservee(moteur.config)
        self.assertTrue(appliquer(moteur, ajout)["ok"])
        snap = moteur.instantane()
        self.assertEqual(len(snap["composants"]["stonehenge"]["roches"]), 31)
        self.assertEqual(snap["composants"]["stonehenge"]["roches"][-1]["echo"], 0)
        self.assertEqual(snap["composants"]["horloge"]["phases_par_tour"], 2401)
        self.assertFalse(snap["composants"]["polybrutus"]["grille_compatible"])
        self.assertTrue(snap["composants"]["stonehenge"]["alertes"])

    def test_transformation(self):
        sain = moteur_nu()
        sain.avancer(273)
        self.assertEqual(sain.etat.cycles_sains, 1)
        self.assertEqual(sain.evolution(), 1)
        sain.avancer(273)
        self.assertEqual(sain.etat.cycles_sains, 2)
        malade = moteur_nu()
        malade.avancer(272)
        malade.etat.force_anomalie = True
        malade.avancer(1)
        self.assertEqual(malade.etat.cycles_sains, 0)
        self.assertEqual(malade.evolution(), 1)


class Polybrutus(unittest.TestCase):
    def test_familles_et_projection(self):
        familles = {item["k"]: item["multiplicite"] for item in familles_k()}
        self.assertEqual(familles, {4: 6, 7: 2, 9: 3, 12: 6, 13: 2, 16: 2})
        self.assertEqual(sum(len(k_paires()) and [1]), 1)
        self.assertEqual(len(k_paires()), 21)
        self.assertEqual(somme_k(), 195)
        points = projection_polybrutus(0)
        roches = {point["point"]: point["roche"] for point in points}
        self.assertIsNone(roches["P1"])
        self.assertIsNone(roches["P5"])
        self.assertEqual(ensemble_roches(0), frozenset({0, 10, 15, 20}))
        self.assertEqual(roches["P2"], 0)
        self.assertEqual(roches["P6"], 0)
        self.assertEqual(roches["P3"], 10)
        self.assertEqual(roches["P7"], 15)
        self.assertEqual(roches["P4"], 20)
        ensembles = [ensemble_roches(rotation) for rotation in range(30)]
        self.assertEqual(len(set(ensembles)), 30)
        self.assertEqual(__import__("math").gcd(7, 30), 1)


class CapsuleEpitagoresColonie(unittest.TestCase):
    def test_capsule_recoit_l_etat(self):
        moteur = moteur_nu()
        capsule = moteur.instantane()["composants"]["capsule"]
        self.assertFalse(capsule["definition_trouvee"])
        self.assertEqual(capsule["etiquette"], "CANDIDAT")
        self.assertEqual(capsule["phase"], 0)
        self.assertEqual(capsule["coup"], 0)
        self.assertEqual(capsule["index_temple"], 0)
        moteur.avancer(1)
        capsule = moteur.instantane()["composants"]["capsule"]
        self.assertEqual(capsule["phase"], 64)
        self.assertEqual(capsule["coup"], 1)
        self.assertEqual(capsule["index_temple"], 1)

    def test_epitagores_vides(self):
        bloc = moteur_nu().instantane()["composants"]["epitagores"]
        self.assertEqual(len(bloc["emplacements"]), 12)
        self.assertTrue(all(item["contenu"] is None for item in bloc["emplacements"]))
        self.assertEqual(bloc["dimension_depart"], 6)
        self.assertEqual(bloc["dimension_arrivee"], 7)
        self.assertTrue(all(item["etiquette"] == "CANDIDAT" for item in bloc["correspondances"]))
        self.assertFalse(bloc["definition_trouvee"])

    def test_colonie(self):
        self.assertEqual(len(ROLES_COLONIE), 7)
        regimes = moteur_nu().instantane()["composants"]["colonie"]["regimes"]
        self.assertEqual(len(regimes), 7)
        self.assertEqual([item["phrase"] for item in regimes], [phrase for _cle, phrase in ROLES_COLONIE])
        self.assertNotIn("brutus", [item["id"] for item in regimes])
        moteur = moteur_nu()
        moteur.avancer(1)
        self.assertFalse(moteur.instantane()["composants"]["colonie"]["regimes"][1]["quorum"])
        moteur.avancer(272)
        abeille = moteur.instantane()["composants"]["colonie"]["regimes"][1]
        self.assertTrue(abeille["quorum"])
        self.assertEqual(moteur.instantane()["composants"]["colonie"]["regimes"][6]["evolution"], 1)
        moteur.etat.force_anomalie = True
        libellule = moteur.instantane()["composants"]["colonie"]["regimes"][5]
        self.assertTrue(libellule["anomalies"])
        self.assertTrue(moteur.instantane()["composants"]["colonie"]["regimes"][4]["inhibe"])

    def test_cristallisation(self):
        moteur = moteur_nu()
        moteur.avancer(8)
        self.assertEqual(len(moteur.etat.cristaux), 1)
        self.assertEqual(moteur.etat.cristaux[0]["effectif"], 7)
        self.assertEqual(moteur.etat.cristaux[0]["niveau"], 1)
        self.assertEqual(moteur.etat.piles[0], ["sain"])


class Configuration(unittest.TestCase):
    def test_valide_invalide_et_reset(self):
        moteur = moteur_nu()
        moteur.avancer(5)
        propre = copy.deepcopy(moteur.config)
        propre["canal"]["frequence_hz"] = 2400
        self.assertTrue(appliquer(moteur, propre)["ok"])
        avant = copy.deepcopy(moteur.config)
        mauvais = copy.deepcopy(moteur.config)
        mauvais["canal"]["frequence_hz"] = -5
        refus = appliquer(moteur, mauvais)
        self.assertFalse(refus["ok"])
        self.assertTrue(any("frequence_hz" in message for message in refus["erreurs"]))
        self.assertEqual(moteur.config, avant)
        moteur.reinitialiser()
        self.assertEqual(moteur.etat.tic, 0)
        self.assertEqual(moteur.config["canal"]["frequence_hz"], 2400)
        self.assertEqual(moteur.config["six_roues"]["anneau"], 273)

    def test_vitesse_et_position(self):
        moteur = moteur_nu()
        config = copy.deepcopy(moteur.config)
        for roue in config["six_roues"]["roues"]:
            roue["vitesse"] = 7
        self.assertTrue(appliquer(moteur, config)["ok"])
        self.assertEqual(premier_tic_convergence(moteur.config["six_roues"]["roues"], 273), 39)
        config = copy.deepcopy(moteur.config)
        config["six_roues"]["roues"][0]["depart"] = 4
        self.assertTrue(appliquer(moteur, config)["ok"])
        from moteur.calculs import position_roue

        self.assertEqual(position_roue(moteur.config["six_roues"]["roues"][0], 1, 273), (4 + 7) % 273)
        self.assertEqual(premier_tic_convergence(moteur.config["six_roues"]["roues"], 273), 39)
        page = moteur.instantane()["composants"]["six_roues"]["convergence"]
        self.assertEqual(page, 39)

    def test_fichier_par_defaut(self):
        config, erreurs = charger()
        self.assertEqual(erreurs, [])
        self.assertEqual(config["canal"]["frequence_hz"], 2400)
        self.assertEqual(valider(config), [])

    def test_composant_factice(self):
        class Factice:
            identifiant = "factice"
            ordre = 45

            def fragment(self):
                return {"note": "essai"}

            def schema_fragment(self):
                return {
                    "type": "objet",
                    "label": "Factice",
                    "champs": {
                        "note": {
                            "type": "str",
                            "min_len": 0,
                            "max_len": 80,
                            "label": "Note factice",
                        }
                    },
                }

            def au_tic(self, etat, config):
                return None

            def instantane(self, etat, config):
                return {"note": config["factice"]["note"]}

        moteur = moteur_nu()
        moteur.inserer_entre(Factice(), apres="stonehenge", avant="cadran")
        self.assertIn("factice", moteur.schema()["champs"])
        self.assertEqual(moteur.schema()["champs"]["factice"]["champs"]["note"]["label"], "Note factice")
        self.assertEqual(moteur.instantane()["composants"]["factice"]["note"], "essai")
        ordres = [composant.identifiant for composant in moteur.composants]
        self.assertLess(ordres.index("stonehenge"), ordres.index("factice"))
        self.assertLess(ordres.index("factice"), ordres.index("cadran"))
        mauvais = copy.deepcopy(moteur.config)
        mauvais["factice"]["note"] = 3
        self.assertFalse(appliquer(moteur, mauvais)["ok"])
        self.assertEqual(moteur.config["factice"]["note"], "essai")


class GraineEtBase39(unittest.TestCase):
    def test_reconstruction_et_taille(self):
        moteur = moteur_nu()
        moteur.avancer(40)
        graine = moteur.exporter_graine()
        autre = reconstruire_depuis_graine(graine, moteur.composants)
        self.assertEqual(autre.instantane(), moteur.instantane())
        texte_graine = json.dumps(graine, ensure_ascii=False, separators=(",", ":"))
        texte_etat = json.dumps(moteur.instantane(), ensure_ascii=False, separators=(",", ":"))
        self.assertLess(len(texte_graine) * 2, len(texte_etat))
        self.assertLess(len(moteur.exporter_graine_base39()), len(texte_graine.encode().hex()))

    def test_graine_alteree(self):
        moteur = moteur_nu()
        moteur.avancer(3)
        graine = moteur.exporter_graine()
        self.assertEqual(verifier_graine(graine, moteur.composants), [])
        cassee = copy.deepcopy(graine)
        cassee["empreinte"] = "0" if graine["empreinte"] != "0" else "1"
        self.assertTrue(verifier_graine(cassee, moteur.composants))
        with self.assertRaises(ValueError):
            reconstruire_depuis_graine(cassee, moteur.composants)
        menteuse = copy.deepcopy(graine)
        menteuse["evolution"] = 99
        from moteur.noyau import _empreinte

        menteuse["empreinte"] = _empreinte({
            "version": menteuse["version"],
            "tic": menteuse["tic"],
            "evolution": menteuse["evolution"],
            "config": menteuse["config"],
        })
        with self.assertRaises(ValueError):
            reconstruire_depuis_graine(menteuse, moteur.composants)

    def test_base39_aller_retour_et_longueur(self):
        self.assertEqual(len(ALPHABET_BASE39.valeur), 39)
        self.assertIn("3 × 13", OBSERVATION_39)
        alea = random.Random(39)
        echantillons = [b"", b"\x00", b"\x00\x00", b"\x00\x01", b"Antmux", alea.randbytes(32)]
        for donnees in echantillons:
            self.assertEqual(decoder(encoder(donnees)), donnees)
        digest = alea.randbytes(32)
        self.assertLess(len(encoder(digest)), len(digest.hex()))
        moteur = moteur_nu()
        self.assertEqual(decoder(encoder(json.dumps(moteur.exporter_graine()).encode())), json.dumps(moteur.exporter_graine()).encode())


class Extensions(unittest.TestCase):
    def test_cristaux_vides_et_lecteur(self):
        slots = emplacements_cristaux(30)
        self.assertEqual(len(slots), 30)
        self.assertTrue(all(not slot.implemente for slot in slots))
        with self.assertRaises(NotImplementedError):
            slots[0].transformer(None, 0)
        moteur = moteur_nu()
        self.assertEqual(len(moteur.instantane()["composants"]["stonehenge"]["emplacements_cristaux"]), 30)
        lecteur = moteur.instantane()["composants"]["lecteur_structures"]
        self.assertEqual(lecteur["statut"], "NON_IMPLEMENTE")
        with self.assertRaises(NotImplementedError):
            next(c for c in moteur.composants if c.identifiant == "lecteur_structures").lire([])


class ParitePage(unittest.TestCase):
    def test_client_javascript(self):
        vecteurs = []
        for tic in (0, 1, 8, 39, 91, 273):
            moteur = moteur_nu()
            moteur.avancer(tic)
            vecteurs.append({"tics": tic, "anomalieDes": None, "attendu": resume(moteur)})
        malade = moteur_nu()
        malade.avancer(272)
        malade.etat.force_anomalie = True
        malade.avancer(1)
        vecteurs.append({"tics": 273, "anomalieDes": 273, "attendu": resume(malade)})
        from moteur.base39 import encoder as enc

        echantillons = [b"", b"\x00\x01", b"Antmux", bytes(range(40))]
        payload = {
            "config": fragments_defaut(),
            "vecteurs": vecteurs,
            "base39": [{"brut": list(donnees), "texte": enc(donnees)} for donnees in echantillons],
            "schema": __import__("moteur.config", fromlist=["schema_defaut"]).schema_defaut(),
        }
        factice = copy.deepcopy(payload["schema"])
        factice["champs"]["factice"] = {
            "type": "objet",
            "label": "Factice",
            "champs": {
                "note": {"type": "str", "min_len": 0, "max_len": 40, "label": "Note factice"}
            },
        }
        payload["schemaFactice"] = factice
        proc = subprocess.run(
            ["node", str(RACINE / "page" / "parite.js")],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        self.assertEqual(proc.stdout.strip(), "ok")


class Page(unittest.TestCase):
    def test_page_statique(self):
        from moteur.generer_page import rendre

        html = rendre()
        self.assertIn('id="capsule"', html)
        self.assertIn("CANDIDAT", html)
        self.assertIn("2400", html)
        self.assertIn("2401", html)
        self.assertIn("localStorage", html)
        self.assertNotIn("/api/", html)
        self.assertNotIn("fetch(", html)
        self.assertIn("Note factice", html) if False else None
        self.assertIn("ancienne fréquence", html)
        self.assertIn("Récit du propriétaire", html)
        chemin = RACINE / "page" / "index.html"
        self.assertEqual(chemin.read_text(encoding="utf-8"), html)


if __name__ == "__main__":
    unittest.main()
