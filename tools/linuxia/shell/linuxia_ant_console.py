#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Shell local LinuxIA : fourmi fixe et première couche LinuxIA Interprète 4B."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import List, Sequence, Tuple

from conversation import (
    DEFAULT_LANGUAGE_MODE,
    LANGUAGE_MODES,
    MODEL_NAME,
    check_model_available,
    conversation_self_test,
    launch_response,
    sanitize_response,
)
from frames import FramePack, load_pack
from greetings import canned_greetings_removed
from render import (
    clear_screen,
    draw_fixed_screen,
    enable_ansi,
    hide_cursor,
    move_cursor,
    self_test,
    show_cursor,
    terminal_layout,
    transcript_scroll_state,
)

MODULE_ROOT = Path(__file__).resolve().parent


def _paint_input_line(
    prompt_row: int,
    box_width: int,
    value: Sequence[str],
    cursor_index: int,
) -> None:
    prefix = "linuxia> "
    available = max(1, box_width - len(prefix))
    text = "".join(value)
    start = max(0, cursor_index - available + 1)
    visible = text[start : start + available]
    move_cursor(prompt_row, 1)
    sys.stdout.write("\x1b[2K")
    sys.stdout.write(prefix + visible)
    move_cursor(prompt_row, len(prefix) + cursor_index - start + 1)
    sys.stdout.flush()


def _read_shell_input(
    pack: FramePack,
    transcript: Sequence[str],
    color: bool,
    scroll_offset: int,
    command_history: Sequence[str],
) -> Tuple[str, int]:
    """Lit une commande et gère PgUp/PgDn dans le journal sous Windows."""
    if os.name != "nt":
        normalized, _, _ = transcript_scroll_state(
            pack, transcript, True, scroll_offset
        )
        prompt_row = draw_fixed_screen(
            pack, 0, transcript, True, color, normalized
        )
        show_cursor()
        move_cursor(prompt_row, len("linuxia> ") + 1)
        try:
            return input().strip(), normalized
        finally:
            hide_cursor()

    import msvcrt

    value: List[str] = []
    cursor_index = 0
    history_index = len(command_history)

    def redraw() -> Tuple[int, int, int]:
        nonlocal scroll_offset
        scroll_offset, page_size, maximum = transcript_scroll_state(
            pack, transcript, True, scroll_offset
        )
        prompt_row = draw_fixed_screen(
            pack, 0, transcript, True, color, scroll_offset
        )
        show_cursor()
        box_width, _ = terminal_layout(pack)
        _paint_input_line(prompt_row, box_width, value, cursor_index)
        return prompt_row, page_size, maximum

    prompt_row, page_size, maximum = redraw()
    try:
        while True:
            char = msvcrt.getwch()
            if char in ("\r", "\n"):
                return "".join(value).strip(), scroll_offset
            if char == "\x03":
                raise KeyboardInterrupt
            if char == "\x08":
                if cursor_index:
                    del value[cursor_index - 1]
                    cursor_index -= 1
                    box_width, _ = terminal_layout(pack)
                    _paint_input_line(prompt_row, box_width, value, cursor_index)
                continue
            if char in ("\x00", "\xe0"):
                key = msvcrt.getwch()
                if key == "I":  # Page précédente
                    scroll_offset = min(maximum, scroll_offset + max(1, page_size - 1))
                    prompt_row, page_size, maximum = redraw()
                elif key == "Q":  # Page suivante
                    scroll_offset = max(0, scroll_offset - max(1, page_size - 1))
                    prompt_row, page_size, maximum = redraw()
                elif key == "K" and cursor_index:
                    cursor_index -= 1
                    box_width, _ = terminal_layout(pack)
                    _paint_input_line(prompt_row, box_width, value, cursor_index)
                elif key == "M" and cursor_index < len(value):
                    cursor_index += 1
                    box_width, _ = terminal_layout(pack)
                    _paint_input_line(prompt_row, box_width, value, cursor_index)
                elif key == "G":
                    cursor_index = 0
                    box_width, _ = terminal_layout(pack)
                    _paint_input_line(prompt_row, box_width, value, cursor_index)
                elif key == "O":
                    cursor_index = len(value)
                    box_width, _ = terminal_layout(pack)
                    _paint_input_line(prompt_row, box_width, value, cursor_index)
                elif key == "S" and cursor_index < len(value):
                    del value[cursor_index]
                    box_width, _ = terminal_layout(pack)
                    _paint_input_line(prompt_row, box_width, value, cursor_index)
                elif key == "H" and command_history:
                    history_index = max(0, history_index - 1)
                    value[:] = list(command_history[history_index])
                    cursor_index = len(value)
                    box_width, _ = terminal_layout(pack)
                    _paint_input_line(prompt_row, box_width, value, cursor_index)
                elif key == "P" and command_history:
                    history_index = min(len(command_history), history_index + 1)
                    value[:] = [] if history_index == len(command_history) else list(command_history[history_index])
                    cursor_index = len(value)
                    box_width, _ = terminal_layout(pack)
                    _paint_input_line(prompt_row, box_width, value, cursor_index)
                continue
            if char.isprintable():
                value.insert(cursor_index, char)
                cursor_index += 1
                box_width, _ = terminal_layout(pack)
                _paint_input_line(prompt_row, box_width, value, cursor_index)
    finally:
        hide_cursor()


def play_loop(pack: FramePack, color: bool) -> None:
    enable_ansi()
    clear_screen()
    hide_cursor()
    delay = 1.0 / max(1.0, pack.fps)
    frame_index = 0
    try:
        while True:
            draw_fixed_screen(pack, frame_index, color=color)
            frame_index = (frame_index + 1) % len(pack.frames)
            time.sleep(delay)
    except KeyboardInterrupt:
        pass
    finally:
        show_cursor()
        _, safe_rows = terminal_layout(pack)
        move_cursor(safe_rows, 1)
        sys.stdout.write("\n")
        sys.stdout.flush()


def run_inspect_with_animation(
    launcher: Path,
    relative_path: str,
    pack: FramePack,
    transcript: Sequence[str],
    color: bool,
) -> Tuple[int, str]:
    command = [
        "powershell.exe",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(launcher),
        "inspect",
        "--file",
        relative_path,
    ]
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    delay = 1.0 / max(1.0, pack.fps)
    frame_index = 0
    while process.poll() is None:
        draw_fixed_screen(pack, frame_index, transcript, False, color)
        frame_index = (frame_index + 1) % len(pack.frames)
        time.sleep(delay)
    output, _ = process.communicate()
    return process.returncode, output or ""


def run_conversation_with_animation(
    user_text: str,
    history: Sequence[Tuple[str, str]],
    language_mode: str,
    pack: FramePack,
    transcript: Sequence[str],
    color: bool,
) -> Tuple[str, str]:
    """Anime la fourmi pendant l'inférence et draine la sortie sans défilement."""
    launch = launch_response(user_text, history, language_mode)
    if launch.process is None:
        line = launch.error_line
        for prefix in ("LinuxIA Interprète> ", "Reine> "):
            if line.startswith(prefix):
                line = line[len(prefix) :]
                break
        return line, launch.language_mode

    process = launch.process
    chunks: List[str] = []

    def read_output() -> None:
        if process.stdout is None:
            return
        for chunk in iter(lambda: process.stdout.read(256), ""):
            if not chunk:
                break
            chunks.append(chunk)

    reader = threading.Thread(target=read_output, name="linuxia-interprete-reader", daemon=True)
    reader.start()

    delay = 1.0 / max(1.0, pack.fps)
    frame_index = 0
    deadline = time.monotonic() + 75.0
    timed_out = False
    while process.poll() is None:
        draw_fixed_screen(pack, frame_index, transcript, False, color)
        frame_index = (frame_index + 1) % len(pack.frames)
        if time.monotonic() >= deadline:
            timed_out = True
            process.kill()
            break
        time.sleep(delay)

    try:
        process.wait(timeout=5.0)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5.0)
    reader.join(timeout=2.0)

    if timed_out:
        return "LinuxIA Interprète a pris trop de temps. J'ai arrêté cette réponse sans lancer d'action.", launch.language_mode
    if process.returncode != 0:
        return "LinuxIA Interprète n'a pas réussi à répondre. Aucune action n'a été exécutée.", launch.language_mode
    return sanitize_response("".join(chunks), launch.language_mode), launch.language_mode


def _append_interpreter_response(transcript: List[str], response: str) -> None:
    lines = [line.strip() for line in str(response or "").splitlines() if line.strip()]
    if not lines:
        lines = ["Je t'écoute."]
    transcript.append(f"LinuxIA Interprète> {lines[0]}")
    transcript.extend(f"       {line}" for line in lines[1:])


def shell_loop(pack: FramePack, repo: Path, color: bool) -> None:
    launcher = repo / "tools" / "linuxia.ps1"
    if not launcher.is_file():
        raise FileNotFoundError(f"Lanceur LinuxIA introuvable : {launcher}")

    transcript: List[str] = [
        "Commandes : /help, /status, /langage, /inspect, /exit",
        f"Conversation locale : {MODEL_NAME} déjà installé seulement",
        "La fourmi tourne pendant une réponse ou une inspection.",
    ]
    history: List[Tuple[str, str]] = []
    command_history: List[str] = []
    language_mode = DEFAULT_LANGUAGE_MODE
    scroll_offset = 0

    enable_ansi()
    clear_screen()
    hide_cursor()
    try:
        while True:
            raw, scroll_offset = _read_shell_input(
                pack, transcript, color, scroll_offset, command_history
            )

            if not raw:
                continue
            command_history.append(raw)
            command_history = command_history[-50:]
            lowered = raw.lower()

            _, page_size, maximum_offset = transcript_scroll_state(
                pack, transcript, True, scroll_offset
            )
            if lowered in {"/haut", "haut"}:
                scroll_offset = min(
                    maximum_offset, scroll_offset + max(1, page_size - 1)
                )
                continue
            if lowered in {"/bas", "bas"}:
                scroll_offset = max(0, scroll_offset - max(1, page_size - 1))
                continue
            if lowered in {"/fin", "fin"}:
                scroll_offset = 0
                continue

            scroll_offset = 0

            if lowered in {"exit", "quit", "/exit", "/quit"}:
                break

            if lowered in {"help", "/help"}:
                transcript.extend(
                    [
                        "/help                       Affiche les commandes",
                        "/status                     Affiche l'état local",
                        "/langage                    Affiche le mode actuel",
                        "/langage court|normal|long|auto",
                        "/inspect <chemin>           Lance la lecture contrôlée",
                        "/haut, /bas, /fin            Parcourt le journal",
                        "PgUp / PgDn                  Défile sans quitter la saisie",
                        "/exit                       Ferme le shell",
                        "Toute autre phrase est envoyée à LinuxIA Interprète 4B.",
                    ]
                )
                continue

            if lowered in {"status", "/status"}:
                availability = check_model_available()
                transcript.extend(
                    [
                        f"REPO: {repo}",
                        f"FRAMES: {len(pack.frames)}",
                        f"FPS: {pack.fps:g}",
                        "MODE: CONVERSATION_LOCALE_CONTROLEE",
                        f"MODEL: {MODEL_NAME}",
                        f"MODEL_READY: {availability.available}",
                        f"LANGAGE: {language_mode.upper()}",
                        "SYSTEM_JOB: NOT_CONNECTED",
                        "HERMES: NOT_CONNECTED",
                    ]
                )
                continue

            if lowered == "/langage" or lowered == "langage":
                transcript.append(f"LinuxIA Interprète> Mode de langage : {language_mode.upper()}.")
                continue

            if lowered.startswith("/langage ") or lowered.startswith("langage "):
                selected = lowered.split(None, 1)[1].strip()
                if selected not in LANGUAGE_MODES:
                    transcript.append(
                        "LinuxIA Interprète> Modes disponibles : court, normal, long ou auto."
                    )
                else:
                    language_mode = selected
                    transcript.append(f"LinuxIA Interprète> Mode de langage : {language_mode.upper()}.")
                continue

            inspect_prefix = None
            if lowered.startswith("/inspect "):
                inspect_prefix = "/inspect "
            elif lowered.startswith("inspect "):
                inspect_prefix = "inspect "
            if inspect_prefix is not None:
                relative_path = raw[len(inspect_prefix) :].strip().strip('"')
                if not relative_path:
                    transcript.append("ERREUR: chemin manquant.")
                    continue
                transcript.append(f"linuxia> /inspect {relative_path}")
                code, output = run_inspect_with_animation(
                    launcher, relative_path, pack, transcript, color
                )
                transcript.extend(output.rstrip().splitlines())
                transcript.append(f"EXIT_CODE: {code}")
                continue

            # Toute phrase ordinaire, y compris « bonjour » et « comment ça va »,
            # est générée par LinuxIA Interprète. Il n'existe plus de réponse de salutation préparée.
            transcript.append(f"linuxia> {raw}")
            response, resolved_mode = run_conversation_with_animation(
                raw,
                history,
                language_mode,
                pack,
                transcript,
                color,
            )
            _append_interpreter_response(transcript, response)
            history.append((raw, response))
            history = history[-6:]
            if language_mode == "auto":
                transcript.append(f"[LANGAGE AUTO: {resolved_mode.upper()}]")
    finally:
        show_cursor()
        clear_screen()
        print("LinuxIA CLI fermée.")


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Console ASCII fixe de LinuxIA.")
    commands = result.add_subparsers(dest="command", required=True)
    demo = commands.add_parser("demo", help="Joue la rotation jusqu'à Ctrl+C.")
    demo.add_argument("--fps", type=float)
    demo.add_argument("--no-color", action="store_true")
    shell = commands.add_parser("shell", help="Ouvre le shell LinuxIA animé.")
    shell.add_argument("--repo", required=True, type=Path)
    shell.add_argument("--fps", type=float)
    shell.add_argument("--no-color", action="store_true")
    commands.add_parser("self-test", help="Valide le rendu sans l'afficher.")
    return result


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    pack = load_pack(MODULE_ROOT)
    if getattr(args, "fps", None) is not None:
        if args.fps <= 0:
            raise ValueError("--fps doit être supérieur à zéro.")
        pack = FramePack(pack.frames, pack.width, pack.height, args.fps, pack.metadata)
    if args.command == "demo":
        play_loop(pack, not args.no_color)
        return 0
    if args.command == "shell":
        shell_loop(pack, args.repo.resolve(), not args.no_color)
        return 0
    if args.command == "self-test":
        result = self_test(pack)
        conversation_result = conversation_self_test()
        result["conversation_ok"] = conversation_result["ok"]
        result["conversation_checks"] = conversation_result["checks"]
        result["canned_greetings_removed"] = canned_greetings_removed()
        for name, passed in conversation_result["checks"].items():
            result["checks"][f"conversation_{name}"] = passed
        result["checks"]["canned_greetings_removed"] = canned_greetings_removed()
        result["ok"] = all(result["checks"].values())
        print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
        return 0 if result["ok"] else 1
    raise AssertionError(f"Commande non gérée : {args.command}")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERREUR: {exc}", file=sys.stderr)
        raise SystemExit(1)
