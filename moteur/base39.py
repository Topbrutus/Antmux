"""Encodeur base 39 sans perte.

Aucun alphabet base 39 n'a été trouvé dans le dépôt. Les chaînes
commençant par « b39 » dans les journaux sont des empreintes
hexadécimales, pas un codage en base 39.

L'alphabet par défaut est étiqueté CANDIDAT : à confirmer par le
propriétaire. Observation, sans conclusion : 39 = 3 × 13.
"""

from __future__ import annotations

from moteur.constantes import ALPHABET_BASE39


OBSERVATION_39 = "39 = 3 × 13. Observation arithmétique, sans conclusion."


def alphabet_par_defaut() -> str:
    alphabet = ALPHABET_BASE39.valeur
    if len(alphabet) != 39 or len(set(alphabet)) != 39:
        raise RuntimeError("l'alphabet base 39 doit avoir 39 symboles distincts")
    return alphabet


def encoder(donnees: bytes, alphabet: str | None = None) -> str:
    """Encode des octets. Les octets nuls de tête sont conservés."""
    symboles = alphabet if alphabet is not None else alphabet_par_defaut()
    _verifier_alphabet(symboles)
    if not donnees:
        return ""
    zeros = 0
    for octet in donnees:
        if octet == 0:
            zeros += 1
        else:
            break
    reste = donnees[zeros:]
    if not reste:
        return symboles[0] * zeros
    valeur = int.from_bytes(reste, "big")
    chiffres: list[str] = []
    while valeur:
        valeur, reste_div = divmod(valeur, 39)
        chiffres.append(symboles[reste_div])
    return symboles[0] * zeros + "".join(reversed(chiffres))


def decoder(texte: str, alphabet: str | None = None) -> bytes:
    symboles = alphabet if alphabet is not None else alphabet_par_defaut()
    _verifier_alphabet(symboles)
    if texte == "":
        return b""
    index = {symbole: i for i, symbole in enumerate(symboles)}
    zeros = 0
    for symbole in texte:
        if symbole not in index:
            raise ValueError(f"symbole hors alphabet base 39: {symbole!r}")
        if symbole == symboles[0]:
            zeros += 1
        else:
            break
    corps = texte[zeros:]
    if not corps:
        return bytes(zeros)
    valeur = 0
    for symbole in corps:
        valeur = valeur * 39 + index[symbole]
    brut = valeur.to_bytes((valeur.bit_length() + 7) // 8, "big")
    return bytes(zeros) + brut


def _verifier_alphabet(alphabet: str) -> None:
    if len(alphabet) != 39 or len(set(alphabet)) != 39:
        raise ValueError("alphabet base 39 invalide")
