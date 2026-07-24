# -*- coding: utf-8 -*-
"""Première couche conversationnelle locale LinuxIA avec LinuxIA Interprète 4B.

Ce module ne télécharge, ne crée et n'active aucun modèle. Il autorise
uniquement un modèle déjà présent dans Ollama et vérifié par ``ollama list``.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import threading
from dataclasses import dataclass
from typing import List, Sequence, Tuple

MODEL_NAME = "linuxia-interprete:4b"
OLLAMA_THINK_ARGUMENT = "--think=false"
LANGUAGE_MODES = ("court", "normal", "long", "auto")
DEFAULT_LANGUAGE_MODE = "court"
SYSTEM_JOB_STATE = "NOT_CONNECTED"


@dataclass(frozen=True)
class ModelAvailability:
    available: bool
    executable: str
    reason: str


@dataclass(frozen=True)
class ConversationLaunch:
    process: subprocess.Popen[str] | None
    error_line: str
    language_mode: str


_STREAM_BOUNDARY_PUNCTUATION = frozenset(".!?…,:;()[]{}«»\"")


class ProvisionalResponseBuffer:
    """Tampon de flux : les fragments restent provisoires jusqu'à une frontière sûre."""

    def __init__(self) -> None:
        self._committed = ""
        self._pending = ""
        self._lock = threading.Lock()

    @staticmethod
    def _last_boundary(value: str) -> int:
        last = -1
        for index, char in enumerate(value):
            if char.isspace() or char in _STREAM_BOUNDARY_PUNCTUATION:
                last = index
        return last

    def feed(self, chunk: str) -> None:
        text = str(chunk or "")
        if not text:
            return
        with self._lock:
            self._pending += text
            boundary = self._last_boundary(self._pending)
            if boundary >= 0:
                self._committed += self._pending[: boundary + 1]
                self._pending = self._pending[boundary + 1 :]

    def snapshot(self) -> Tuple[str, str]:
        with self._lock:
            return self._committed, self._pending

    def preview(self) -> str:
        committed, pending = self.snapshot()
        return committed + pending

    def finalize(self) -> str:
        with self._lock:
            self._committed += self._pending
            self._pending = ""
            return self._committed


def _creation_flags() -> int:
    return int(getattr(subprocess, "CREATE_NO_WINDOW", 0)) if os.name == "nt" else 0


def parse_model_names(output: str) -> Tuple[str, ...]:
    """Extrait les noms de modèles de la sortie stable de ``ollama list``."""
    names: List[str] = []
    for raw_line in str(output or "").splitlines():
        line = raw_line.strip()
        if not line or line.upper().startswith("NAME "):
            continue
        first = line.split()[0]
        if ":" in first:
            names.append(first.lower())
    return tuple(names)


def _run_text(command: Sequence[str], timeout_seconds: float) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(command),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout_seconds,
        check=False,
        creationflags=_creation_flags(),
    )


def check_model_available(timeout_seconds: float = 8.0) -> ModelAvailability:
    executable = shutil.which("ollama") or shutil.which("ollama.exe") or ""
    if not executable:
        return ModelAvailability(False, "", "OLLAMA_NOT_FOUND")
    try:
        completed = _run_text([executable, "list"], timeout_seconds)
    except (OSError, subprocess.TimeoutExpired):
        return ModelAvailability(False, executable, "OLLAMA_LIST_FAILED")
    if completed.returncode != 0:
        return ModelAvailability(False, executable, "OLLAMA_LIST_FAILED")
    names = parse_model_names(completed.stdout)
    if MODEL_NAME.lower() not in names:
        return ModelAvailability(False, executable, "MODEL_NOT_INSTALLED")

    # LinuxIA refuse d'exposer le raisonnement interne. Une version d'Ollama
    # sans contrôle explicite du mode pensée est donc refusée, sans inférence.
    try:
        help_result = _run_text([executable, "run", "--help"], timeout_seconds)
    except (OSError, subprocess.TimeoutExpired):
        return ModelAvailability(False, executable, "THINK_CONTROL_UNAVAILABLE")
    if help_result.returncode != 0 or "--think" not in help_result.stdout:
        return ModelAvailability(False, executable, "THINK_CONTROL_UNAVAILABLE")
    return ModelAvailability(True, executable, "READY")


def resolve_language_mode(requested: str, user_text: str) -> str:
    mode = str(requested or DEFAULT_LANGUAGE_MODE).lower().strip()
    if mode not in LANGUAGE_MODES:
        mode = DEFAULT_LANGUAGE_MODE
    if mode != "auto":
        return mode
    text = str(user_text or "")
    if len(text) > 280 or any(
        token in text.lower()
        for token in ("explique en détail", "présentation", "architecture", "analyse complète")
    ):
        return "long"
    if len(text) > 100 or text.count("?") > 1:
        return "normal"
    return "court"


def _length_instruction(mode: str) -> str:
    return {
        "court": "Réponds en une ou deux phrases, maximum 30 mots.",
        "normal": "Réponds en deux à cinq phrases, maximum 120 mots.",
        "long": "Réponds clairement et avec structure, maximum 260 mots.",
    }[mode]


def build_prompt(
    user_text: str,
    history: Sequence[Tuple[str, str]],
    requested_language_mode: str,
) -> Tuple[str, str]:
    """Construit un prompt de réception sans outil ni pouvoir d'exécution."""
    mode = resolve_language_mode(requested_language_mode, user_text)
    recent = list(history[-4:])
    context_lines: List[str] = []
    for user_value, assistant_value in recent:
        context_lines.append(f"Gabi: {user_value}")
        context_lines.append(f"LinuxIA Interprète: {assistant_value}")
    context = "\n".join(context_lines) if context_lines else "Aucun échange précédent."

    prompt = f"""/no_think
Réponds au message de Gabi en français naturel.
{_length_instruction(mode)}
Conserve fidèlement les nombres, pourcentages, états et faits présents dans le message et le contexte.
Évite les répétitions, les faux départs et les fragments de mots; relis ta phrase avant de répondre.
Ne prétends jamais avoir utilisé un outil, modifié un fichier ou exécuté une action.
SYSTEM_JOB_NOT_CONNECTED est un état interne; ne le mentionne que si Gabi demande explicitement l’état de System Job.

Contexte récent:
{context}

Message de Gabi: {str(user_text or '').strip()}
/no_think"""
    return prompt, mode


def launch_response(
    user_text: str,
    history: Sequence[Tuple[str, str]],
    language_mode: str,
) -> ConversationLaunch:
    """Lance uniquement le modèle local déjà installé; jamais de téléchargement."""
    availability = check_model_available()
    resolved_mode = resolve_language_mode(language_mode, user_text)
    if not availability.available:
        messages = {
            "OLLAMA_NOT_FOUND": "LinuxIA Interprète> Ollama n'est pas disponible sur cet ordinateur.",
            "MODEL_NOT_INSTALLED": (
                "LinuxIA Interprète> LinuxIA Interprète 4B n'est pas installé. Je refuse de le télécharger automatiquement."
            ),
            "OLLAMA_LIST_FAILED": (
                "LinuxIA Interprète> Ollama ne répond pas. Aucun modèle n'a été lancé."
            ),
            "THINK_CONTROL_UNAVAILABLE": (
                "LinuxIA Interprète> Cette version d'Ollama ne peut pas masquer le raisonnement interne. "
                "Je refuse donc de lancer LinuxIA Interprète dans cette interface."
            ),
        }
        return ConversationLaunch(
            None,
            messages.get(availability.reason, "LinuxIA Interprète> LinuxIA Interprète n'est pas disponible."),
            resolved_mode,
        )

    prompt, resolved_mode = build_prompt(user_text, history, language_mode)
    process = subprocess.Popen(
        [
            availability.executable,
            "run",
            MODEL_NAME,
            OLLAMA_THINK_ARGUMENT,
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        encoding="utf-8",
        errors="replace",
        creationflags=_creation_flags(),
    )
    assert process.stdin is not None
    process.stdin.write(prompt)
    process.stdin.close()
    return ConversationLaunch(process, "", resolved_mode)


def _remove_plain_thinking(value: str) -> str:
    """Filtre défensif pour les anciennes sorties CLI non structurées."""
    marker = re.search(r"(?is)(?:final answer|answer|réponse finale|réponse)\s*:\s*", value)
    if marker:
        value = value[marker.end() :]

    kept: List[str] = []
    trace_line = re.compile(
        r"(?i)^\s*(?:thinking(?:\.{3}|…|:)?|analysis\s*:|"
        r"okay,?\s+the\s+user|the\s+user\s+is|we\s+need|we\s+should|"
        r"let(?:'|’)s|i\s+need\s+to)"
    )
    for line in value.splitlines():
        if trace_line.match(line):
            continue
        kept.append(line)
    return "\n".join(kept)


def _apply_backspaces(value: str) -> str:
    """Applique les retours arrière comme un terminal au lieu de les supprimer seuls."""
    result: List[str] = []
    for char in str(value or ""):
        if char == "\b":
            if result:
                result.pop()
        else:
            result.append(char)
    return "".join(result)


def _remove_adjacent_word_stutter(value: str) -> str:
    """Retire les répétitions exactes et les faux départs adjacents."""
    exact_duplicate = re.compile(r"(?iu)\b([^\W\d_]{2,})\s+\1\b")
    prefix_pair = re.compile(
        r"(?iu)(?=\b([^\W\d_]{4,})\s+([^\W\d_]{4,})\b)"
    )
    current = value
    while True:
        collapsed = exact_duplicate.sub(r"\1", current)
        if collapsed != current:
            current = collapsed
            continue

        replacement = None
        for match in prefix_pair.finditer(current):
            first, second = match.group(1), match.group(2)
            left, right = first.casefold(), second.casefold()
            if left != right and len(right) > len(left) and right.startswith(left):
                replacement = (match.start(1), match.end(2), second)
                break
        if replacement is None:
            return current
        start, end, second = replacement
        current = current[:start] + second + current[end:]


def sanitize_preview_response(output: str) -> str:
    """Nettoie un aperçu provisoire sans le transformer en entrée d'historique."""
    value = _apply_backspaces(str(output or ""))
    value = re.sub(r"(?is)<think>.*?</think>", "", value)
    value = re.sub(r"(?is)<think>.*$", "", value)
    value = re.sub(r"\x1b\[[0-9;?]*[ -/]*[@-~]", "", value)
    value = value.replace("\r\n", "\n").replace("\r", "\n")
    value = _remove_plain_thinking(value)
    lines = [line.strip() for line in value.splitlines() if line.strip()]
    value = " ".join(lines)
    value = re.sub(r"\s+", " ", value).strip()
    value = _remove_adjacent_word_stutter(value)
    for prefix in ("linuxia interprète:", "linuxia interprete:", "interprète:", "interprete:", "reine:"):
        if value.lower().startswith(prefix):
            value = value[len(prefix) :].strip()
            break
    return value


def sanitize_response(output: str, mode: str) -> str:
    """Retire tout raisonnement interne, applique les corrections terminales et borne la réponse."""
    value = _apply_backspaces(str(output or ""))
    value = re.sub(r"(?is)<think>.*?</think>", "", value)
    value = re.sub(r"(?is)<think>.*$", "", value)
    value = re.sub(r"\x1b\[[0-9;?]*[ -/]*[@-~]", "", value)
    value = value.replace("\r\n", "\n").replace("\r", "\n")
    value = _remove_plain_thinking(value)
    lines = [line.strip() for line in value.splitlines() if line.strip()]
    value = " ".join(lines)
    value = re.sub(r"\s+", " ", value).strip()
    value = _remove_adjacent_word_stutter(value)
    for prefix in ("linuxia interprète:", "linuxia interprete:", "interprète:", "interprete:", "reine:"):
        if value.lower().startswith(prefix):
            value = value[len(prefix) :].strip()
            break
    if not value:
        return "Je t'écoute."

    limit = {"court": 220, "normal": 900, "long": 1900}.get(mode, 220)
    if len(value) > limit:
        value = value[: limit - 1].rstrip() + "…"
    return value


def conversation_self_test() -> dict:
    prompt, mode = build_prompt("Comment ça va?", [], "court")
    prompt_auto, auto_mode = build_prompt(
        "Fais une présentation détaillée de notre architecture LinuxIA.", [], "auto"
    )
    provisional = ProvisionalResponseBuffer()
    provisional.feed("fonc")
    before_boundary = provisional.snapshot()
    provisional.feed("tion ")
    after_boundary = provisional.snapshot()
    provisional.feed("provis")
    before_final = provisional.snapshot()
    finalized = provisional.finalize()

    checks = {
        "model_exact": MODEL_NAME == "linuxia-interprete:4b",
        "think_disabled_exact": OLLAMA_THINK_ARGUMENT == "--think=false",
        "list_parser_exact": parse_model_names(
            "NAME ID SIZE MODIFIED\nlinuxia-interprete:4b abc 523 MB now\nother:latest def 1 GB now\n"
        )
        == ("linuxia-interprete:4b", "other:latest"),
        "short_mode": mode == "court" and "maximum 30 mots" in prompt,
        "auto_long": auto_mode == "long" and "maximum 260 mots" in prompt_auto,
        "no_think": prompt.startswith("/no_think") and prompt.endswith("/no_think"),
        "no_tool_claim": "Ne prétends jamais" in prompt,
        "anti_stutter_prompt": "Évite les répétitions" in prompt,
        "provisional_not_committed_before_boundary": before_boundary == ("", "fonc"),
        "provisional_commits_on_boundary": after_boundary == ("fonction ", ""),
        "provisional_final_flush": before_final == ("fonction ", "provis")
        and finalized == "fonction provis",
        "sanitize_think": sanitize_response(
            "<think>raisonnement</think> Reine: Ça va bien, merci!", "court"
        )
        == "Ça va bien, merci!",
        "sanitize_plain_thinking": sanitize_response(
            "Thinking... Okay, the user is asking a question.", "court"
        )
        == "Je t'écoute.",
        "sanitize_final_marker": sanitize_response(
            "Thinking...\nAnswer: Ça va bien, merci!", "court"
        )
        == "Ça va bien, merci!",
        "sanitize_terminal_backspaces": sanitize_response(
            "Je dois anal\b\b\b\banalyser cela.", "court"
        )
        == "Je dois analyser cela.",
        "sanitize_prefix_stutter": sanitize_response(
            "Je n’ai pas de fonction ni d’études person personnelles.", "court"
        )
        == "Je n’ai pas de fonction ni d’études personnelles.",
        "sanitize_short_duplicate_stutter": sanitize_response(
            "Je Je ne peux pas agir.", "court"
        )
        == "Je ne peux pas agir.",
        "preview_short_duplicate_stutter": sanitize_preview_response(
            "Je Je ne peux pas agir."
        )
        == "Je ne peux pas agir.",
        "no_canned_greeting": "Bonjour Gabi." not in prompt and "Je suis prête." not in prompt,
        "system_job_honest": SYSTEM_JOB_STATE == "NOT_CONNECTED" and "SYSTEM_JOB_NOT_CONNECTED" in prompt,
    }
    return {"ok": all(checks.values()), "checks": checks}
