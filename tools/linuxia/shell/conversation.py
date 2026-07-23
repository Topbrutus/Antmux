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


def sanitize_response(output: str, mode: str) -> str:
    """Retire tout raisonnement interne et borne une réponse imprévisible."""
    value = str(output or "")
    value = re.sub(r"(?is)<think>.*?</think>", "", value)
    value = re.sub(r"(?is)<think>.*$", "", value)
    value = re.sub(r"\x1b\[[0-9;?]*[ -/]*[@-~]", "", value)
    value = value.replace("\b", "").replace("\r", "\n")
    value = _remove_plain_thinking(value)
    lines = [line.strip() for line in value.splitlines() if line.strip()]
    value = " ".join(lines)
    value = re.sub(r"\s+", " ", value).strip()
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
        "no_canned_greeting": "Bonjour Gabi." not in prompt and "Je suis prête." not in prompt,
        "system_job_honest": SYSTEM_JOB_STATE == "NOT_CONNECTED" and "SYSTEM_JOB_NOT_CONNECTED" in prompt,
    }
    return {"ok": all(checks.values()), "checks": checks}
