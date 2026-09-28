from __future__ import annotations

import hashlib
import re
from typing import Any


SCHEMA = "ANTMUX-ANT-BIRTH-v1"
STATE_READY = "READY_TO_SING"

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
    """Deterministic candidate splitter; not a linguistic authority."""
    out: list[str] = []
    for match in WORD_RE.finditer(text):
        word = match.group(0)
        if not word:
            continue

        start = 0
        saw_vowel = False
        for index, char in enumerate(word):
            if char in VOWELS:
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


def build_ant_birth(ant_id: str, title: str, body: str, created_at: float) -> dict[str, Any]:
    source = f"{title}\n{body}"
    fingerprint = hashlib.sha256(source.encode("utf-8")).hexdigest()[:20].upper()
    syllables = candidate_syllables(source)

    return {
        "schema": SCHEMA,
        "ant_id": ant_id,
        "emoji": "🐜",
        "triad_name": triadic_name(f"{ant_id}|{fingerprint}"),
        "state": STATE_READY,
        "role": "SYNAPSE",
        "synapse": {
            "song_channel": "OUTBOUND",
            "gratitude_channel": "INBOUND",
            "meaning": "the ant carries the connection; external systems may listen and return gratitude without owning the ant state",
        },
        "project_soul": {
            "meaning": "software identity + memory + timing + lineage",
            "memory_id": f"MEM-{fingerprint[:12]}",
            "birth_tick_ms": int(created_at * 1000),
            "lineage": [ant_id],
        },
        "baggage": {
            "message_fingerprint": fingerprint,
            "language_triplet": "🔤🎧〰️",
            "syllable_status": "CANDIDATE_V0_1",
            "syllables": syllables,
            "symbolic_song": symbolic_song(syllables),
        },
        "lifecycle": [
            {"step": 1, "state": "ANT_BIRTH", "emoji": "🐜", "status": "DONE"},
            {"step": 2, "state": "CONDITIONAL_ROUTING", "emoji": "🔀", "status": "DONE"},
            {"step": 3, "state": "BAGGAGE_ATTACHED", "emoji": "🎒", "status": "DONE"},
            {"step": 4, "state": "LIFE_CLOCK_ASSIGNMENT", "emoji": "⏱️🧠", "status": "DONE"},
            {"step": 5, "state": "BECOME_SYNAPSE", "emoji": "🐜🧠", "status": "DONE"},
            {"step": 6, "state": "READY_TO_SING", "emoji": "🎶", "status": "ACTIVE"},
        ],
    }
