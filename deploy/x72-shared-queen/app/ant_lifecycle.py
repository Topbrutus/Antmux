from __future__ import annotations

import hashlib
import re
from typing import Any


SCHEMA = "ANTMUX-ANT-LIFECYCLE-v1"
ENTRY_POLICY = "OPEN_TO_ALL"
LAUNCH_PHRASE = "Christ ou pas Christ, j’y vais."

NAME_A = ("🟦", "🟥", "🟩", "🟨", "🟪", "⬜", "⬛")
NAME_B = ("🥚", "💎", "🌱", "🌙", "☀️", "🍄", "🪶")
NAME_C = ("⚾", "🎵", "🧭", "🔧", "📚", "🌀", "🪁")

SYMBOLS = ("◇", "┬", "⊕", "⊖", "↗", "↘", "◎", "↺")
WORD_RE = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿŒœ]+")
VOWELS = set("aeiouyàâäéèêëïîôöùûüÿœAEIOUYÀÂÄÉÈÊËÏÎÔÖÙÛÜŸŒ")


def _digest(value: str) -> bytes:
    return hashlib.sha256(value.encode("utf-8")).digest()


def triadic_name(seed: str) -> str:
    digest = _digest(seed)
    return NAME_A[digest[0] % len(NAME_A)] + NAME_B[digest[1] % len(NAME_B)] + NAME_C[digest[2] % len(NAME_C)]


def candidate_syllables(text: str, limit: int = 24) -> list[str]:
    """Small deterministic v0.1 syllable candidate splitter.

    This is intentionally labelled CANDIDATE: it is a software segmentation
    heuristic, not a linguistic authority for French pronunciation.
    """
    out: list[str] = []
    for match in WORD_RE.finditer(text):
        word = match.group(0)
        if not word:
            continue

        start = 0
        saw_vowel = False
        for index, char in enumerate(word):
            is_vowel = char in VOWELS
            if is_vowel:
                saw_vowel = True
                continue

            if saw_vowel and index + 1 < len(word) and word[index + 1] in VOWELS:
                piece = word[start:index]
                if piece:
                    out.append(piece.lower())
                start = index
                saw_vowel = False
                if len(out) >= limit:
                    return out[:limit]

        tail = word[start:]
        if tail:
            out.append(tail.lower())
        if len(out) >= limit:
            break

    return out[:limit]


def symbolic_song(syllables: list[str]) -> str:
    if not syllables:
        return "◉→♡"
    tokens: list[str] = []
    for syllable in syllables:
        digest = _digest(syllable)
        symbol = SYMBOLS[digest[0] % len(SYMBOLS)]
        direction = "↗" if digest[1] % 2 == 0 else "↘"
        tokens.append(f"⟦{symbol}{direction}⟧")
    return "◉→" + "→".join(tokens) + "→♡"


def _phase(step: int, state: str, emoji: str, status: str) -> dict[str, Any]:
    return {"step": step, "state": state, "emoji": emoji, "status": status}


def build_ant_receipt(ant_id: str, title: str, body: str, created_at: float) -> dict[str, Any]:
    source = f"{title}\n{body}"
    fingerprint = hashlib.sha256(source.encode("utf-8")).hexdigest()[:20].upper()
    syllables = candidate_syllables(source)
    song = symbolic_song(syllables)
    name = triadic_name(f"{ant_id}|{fingerprint}")
    birth_tick_ms = int(created_at * 1000)

    return {
        "schema": SCHEMA,
        "ant_id": ant_id,
        "triad_name": name,
        "entry_policy": ENTRY_POLICY,
        "launch_phrase": LAUNCH_PHRASE,
        "state": "LIFE_CLOCK_ASSIGNED",
        "parazone_port": "READY_TO_CONNECT",
        "project_soul": {
            "meaning": "software identity + memory + timing + lineage",
            "memory_id": f"MEM-{fingerprint[:12]}",
            "birth_tick_ms": birth_tick_ms,
            "lineage": [ant_id],
        },
        "baggage": {
            "message_fingerprint": fingerprint,
            "syllable_status": "CANDIDATE_V0_1",
            "syllable_count": len(syllables),
            "syllables": syllables,
            "symbolic_song": song,
            "language_triplet": "🔤🎧〰️",
        },
        "lifecycle": [
            _phase(1, "ANT_BIRTH", "🐜", "DONE"),
            _phase(2, "CONDITIONAL_ROUTING", "🔀", "DONE"),
            _phase(3, "BAGGAGE_ATTACHED", "🎒", "DONE"),
            _phase(4, "LIFE_CLOCK_ASSIGNMENT", "⏱️🧠", "DONE"),
            _phase(5, "TURN_TO_PARAZONE", "↻", "READY"),
            _phase(6, "ANT_SONG", "🎶", "READY"),
            _phase(7, "PARAZONE_GRATITUDE", "🙏", "WAITING_PORT"),
            _phase(8, "CENTRAL_LANGUAGE_INGRESS", "◐│◑", "WAITING_PORT"),
            _phase(9, "DORMITORY_EGG", "🥚", "WAITING"),
            _phase(10, "QUEEN_CRYSTALLIZATION", "👑💎", "WAITING"),
        ],
    }


def parazone_complete(receipt: dict[str, Any]) -> dict[str, Any]:
    if receipt.get("state") not in {"LIFE_CLOCK_ASSIGNED", "PARAZONE_TRANSFER"}:
        raise ValueError("ant is not waiting for Parazone transfer")

    updated = dict(receipt)
    updated["state"] = "DORMITORY_EGG"
    updated["parazone_port"] = "TRANSFER_CONFIRMED"
    phases = [dict(item) for item in receipt.get("lifecycle", [])]
    for phase in phases:
        if phase["state"] in {"TURN_TO_PARAZONE", "ANT_SONG", "PARAZONE_GRATITUDE", "CENTRAL_LANGUAGE_INGRESS"}:
            phase["status"] = "DONE"
        elif phase["state"] == "DORMITORY_EGG":
            phase["status"] = "ACTIVE"
    updated["lifecycle"] = phases
    return updated


def queen_crystallize(receipt: dict[str, Any]) -> dict[str, Any]:
    if receipt.get("state") != "DORMITORY_EGG":
        raise ValueError("only a dormitory egg can be crystallized")

    updated = dict(receipt)
    updated["state"] = "CRYSTALLIZED_READY"
    phases = [dict(item) for item in receipt.get("lifecycle", [])]
    for phase in phases:
        if phase["state"] == "DORMITORY_EGG":
            phase["status"] = "DONE"
        elif phase["state"] == "QUEEN_CRYSTALLIZATION":
            phase["status"] = "DONE"
    updated["lifecycle"] = phases
    updated["crystal"] = {
        "status": "READY",
        "emoji": "💎",
        "resume": "🥚→👑→💎→🐜",
    }
    return updated
