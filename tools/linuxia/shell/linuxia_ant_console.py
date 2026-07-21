#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Shell local LinuxIA : fourmi fixe, modèle et réseau non activés."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Sequence, Tuple

from frames import FramePack, load_pack
from render import (
    clear_screen,
    draw_fixed_screen,
    enable_ansi,
    hide_cursor,
    move_cursor,
    self_test,
    show_cursor,
    terminal_layout,
)

MODULE_ROOT = Path(__file__).resolve().parent


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


def shell_loop(pack: FramePack, repo: Path, color: bool) -> None:
    launcher = repo / "tools" / "linuxia.ps1"
    if not launcher.is_file():
        raise FileNotFoundError(f"Lanceur LinuxIA introuvable : {launcher}")

    transcript: List[str] = [
        "Commandes : help, status, inspect <chemin>, exit",
        "La fourmi tourne uniquement pendant inspect.",
    ]
    enable_ansi()
    clear_screen()
    hide_cursor()
    try:
        while True:
            prompt_row = draw_fixed_screen(pack, 0, transcript, True, color)
            show_cursor()
            move_cursor(prompt_row, len("linuxia> ") + 1)
            sys.stdout.flush()
            try:
                raw = input().strip()
            finally:
                hide_cursor()

            if not raw:
                continue
            lowered = raw.lower()
            if lowered in {"exit", "quit"}:
                break
            if lowered == "help":
                transcript.extend(
                    [
                        "help                 Affiche les commandes",
                        "status               Affiche l'état du prototype",
                        "inspect <chemin>     Lance la lecture contrôlée",
                        "exit                 Ferme le shell",
                    ]
                )
                continue
            if lowered == "status":
                transcript.extend(
                    [
                        f"REPO: {repo}",
                        f"FRAMES: {len(pack.frames)}",
                        f"FPS: {pack.fps:g}",
                        "MODE: PROTOTYPE_VISUEL_FIXE",
                        "MODEL: NOT_ACTIVATED",
                        "NETWORK: NOT_USED",
                    ]
                )
                continue
            if lowered.startswith("inspect "):
                relative_path = raw[len("inspect ") :].strip().strip('"')
                if not relative_path:
                    transcript.append("ERREUR: chemin manquant.")
                    continue
                transcript.append(f"linuxia> inspect {relative_path}")
                code, output = run_inspect_with_animation(
                    launcher, relative_path, pack, transcript, color
                )
                transcript.extend(output.rstrip().splitlines())
                transcript.append(f"EXIT_CODE: {code}")
                continue
            transcript.append(
                "COMMANDE_INCONNUE: utilise help, status, inspect <chemin> ou exit."
            )
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
        print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
        return 0 if result["ok"] else 1
    raise AssertionError(f"Commande non gérée : {args.command}")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERREUR: {exc}", file=sys.stderr)
        raise SystemExit(1)
