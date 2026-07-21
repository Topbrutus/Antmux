# -*- coding: utf-8 -*-
"""Rendu ANSI fixe : aucune image ne pousse le tampon du terminal."""

from __future__ import annotations

import ctypes
import os
import shutil
import sys
from typing import List, Sequence, Tuple

from frames import FramePack

ANSI_RESET = "\x1b[0m"
ANSI_PURPLE = "\x1b[38;5;141m"


def enable_ansi() -> None:
    if os.name != "nt":
        return
    try:
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)
        mode = ctypes.c_uint32()
        if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            kernel32.SetConsoleMode(handle, mode.value | 0x0004)
    except Exception:
        pass


def clear_screen() -> None:
    """Efface une fois au démarrage, jamais entre les images."""
    sys.stdout.write("\x1b[2J\x1b[H")
    sys.stdout.flush()


def cursor_home() -> None:
    sys.stdout.write("\x1b[H")


def move_cursor(row: int, column: int = 1) -> None:
    sys.stdout.write(f"\x1b[{max(1, row)};{max(1, column)}H")


def hide_cursor() -> None:
    sys.stdout.write("\x1b[?25l")
    sys.stdout.flush()


def show_cursor() -> None:
    sys.stdout.write("\x1b[?25h")
    sys.stdout.flush()


def fit_text(value: str, width: int) -> str:
    value = value.replace("\r", " ").replace("\n", " ")
    if len(value) > width:
        return value[: max(0, width - 1)] + ("…" if width else "")
    return value + (" " * (width - len(value)))


def center_text(value: str, width: int) -> str:
    value = value[:width]
    left = max(0, (width - len(value)) // 2)
    return (" " * left) + value + (" " * (width - len(value) - left))


def terminal_layout(
    pack: FramePack,
    columns: int | None = None,
    rows: int | None = None,
) -> Tuple[int, int]:
    terminal = shutil.get_terminal_size(fallback=(100, 32))
    detected_columns = terminal.columns if columns is None else columns
    detected_rows = terminal.lines if rows is None else rows
    safe_columns = max(36, detected_columns - 1)
    safe_rows = max(pack.height + 8, detected_rows - 1)
    box_width = min(safe_columns, max(pack.width + 6, 42))
    if box_width < pack.width + 4:
        raise RuntimeError(
            f"Terminal trop étroit : {detected_columns} colonnes; "
            f"au moins {pack.width + 5} sont nécessaires."
        )
    return box_width, safe_rows


def frame_lines(frame: str, width: int, height: int) -> List[str]:
    source = frame.splitlines()[:height]
    source.extend([""] * (height - len(source)))
    return [center_text(line[:width].rstrip(), width) for line in source]


def compose_fixed_screen(
    pack: FramePack,
    frame_index: int,
    transcript: Sequence[str] = (),
    include_prompt: bool = False,
    color: bool = True,
    columns: int | None = None,
    rows: int | None = None,
) -> Tuple[str, int]:
    box_width, total_rows = terminal_layout(pack, columns=columns, rows=rows)
    inner_width = box_width - 2
    art_width = min(pack.width, inner_width - 2)
    art = frame_lines(
        pack.frames[frame_index % len(pack.frames)], art_width, pack.height
    )

    title = " LINUXIA CLI "
    fill = max(0, box_width - len(title) - 2)
    left = fill // 2
    lines: List[str] = [
        "╭" + ("─" * left) + title + ("─" * (fill - left)) + "╮",
        "│" + center_text("LOCAL · AUDITABLE · PRÊTE", inner_width) + "│",
        "│" + (" " * inner_width) + "│",
    ]
    lines.extend("│" + center_text(line, inner_width) + "│" for line in art)

    # Référence visuelle v3 : aucun texte mouvant sous la fourmi.
    lines.extend(
        [
            "│" + (" " * inner_width) + "│",
            "╰" + ("─" * (box_width - 2)) + "╯",
        ]
    )

    transcript_rows = max(0, total_rows - len(lines) - (2 if include_prompt else 1))
    if transcript_rows:
        lines.append(fit_text(" SORTIE", box_width))
        visible = list(transcript[-transcript_rows:])
        visible.extend([""] * (transcript_rows - len(visible)))
        lines.extend(fit_text(line, box_width) for line in visible)

    prompt_row = min(total_rows, len(lines) + 1)
    if include_prompt:
        lines.append(fit_text("linuxia> ", box_width))

    lines = [fit_text(line, box_width) for line in lines[:total_rows]]
    screen = "\n".join(lines)
    if color:
        screen = f"{ANSI_PURPLE}{screen}{ANSI_RESET}"
    return screen, prompt_row


def draw_fixed_screen(
    pack: FramePack,
    frame_index: int,
    transcript: Sequence[str] = (),
    include_prompt: bool = False,
    color: bool = True,
) -> int:
    screen, prompt_row = compose_fixed_screen(
        pack, frame_index, transcript, include_prompt, color
    )
    cursor_home()
    sys.stdout.write(screen)
    sys.stdout.flush()
    return prompt_row


def self_test(pack: FramePack) -> dict:
    checks = {
        "frame_count_100": len(pack.frames) == 100,
        "positive_dimensions": pack.width > 0 and pack.height > 0,
        "frame_height_exact": all(
            len(frame.splitlines()) == pack.height for frame in pack.frames
        ),
        "frame_width_bounded": all(
            len(line) <= pack.width
            for frame in pack.frames
            for line in frame.splitlines()
        ),
    }
    distinct = next(
        (i for i, frame in enumerate(pack.frames[1:], 1) if frame != pack.frames[0]),
        0,
    )
    first, prompt_first = compose_fixed_screen(
        pack, 0, ["test"], True, False, 80, 40
    )
    second, prompt_second = compose_fixed_screen(
        pack, distinct, ["test"], True, False, 80, 40
    )
    first_lines, second_lines = first.splitlines(), second.splitlines()
    checks.update(
        {
            "distinct_animation_frame": distinct > 0 and first != second,
            "fixed_line_count": len(first_lines) == len(second_lines),
            "fixed_line_width": len({len(x) for x in first_lines}) == 1
            and len({len(x) for x in second_lines}) == 1,
            "fixed_prompt_row": prompt_first == prompt_second,
            "no_trailing_newline": not first.endswith("\n") and not second.endswith("\n"),
            "no_clear_sequence_in_frame": "\x1b[2J" not in first
            and "\x1b[2J" not in second,
            "no_flashing_status": "LINUXIA TRAVAILLE" not in first
            and "·  ·  ·" not in first
            and "LINUXIA TRAVAILLE" not in second
            and "·  ·  ·" not in second,
        }
    )
    return {
        "schema_version": "linuxia-ant-shell-self-test-v1",
        "ok": all(checks.values()),
        "frame_count": len(pack.frames),
        "checks": checks,
    }
