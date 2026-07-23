# -*- coding: utf-8 -*-
"""Rendu ANSI fixe : aucune image ni saisie ne pollue le tampon du terminal."""

from __future__ import annotations

import ctypes
import os
import shutil
import sys
import textwrap
from typing import List, Sequence, Tuple

from frames import FramePack

ANSI_RESET = "\x1b[0m"
ANSI_PURPLE = "\x1b[38;5;141m"
MIN_OUTPUT_ROWS = 3


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
    value = value.replace("\r", " ").replace("\n", " ").replace("\t", "    ")
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
    safe_rows = max(1, detected_rows - 1)
    box_width = min(safe_columns, max(pack.width + 6, 42))
    if box_width < pack.width + 4:
        raise RuntimeError(
            f"Terminal trop étroit : {detected_columns} colonnes; "
            f"au moins {pack.width + 5} sont nécessaires."
        )
    minimum_rows = pack.height + 8
    if safe_rows < minimum_rows:
        raise RuntimeError(
            f"Terminal trop bas : {detected_rows} lignes; "
            f"au moins {minimum_rows + 1} sont nécessaires."
        )
    return box_width, safe_rows


def frame_lines(frame: str, width: int, height: int) -> List[str]:
    source = frame.splitlines()[:height]
    source.extend([""] * (height - len(source)))
    return [center_text(line[:width].rstrip(), width) for line in source]


def _continuation_indent(value: str) -> str:
    for prefix in ("Reine> ", "linuxia> ", "ERREUR: ", "EXIT_CODE: "):
        if value.startswith(prefix):
            return " " * len(prefix)
    return ""


def wrap_transcript_line(value: str, width: int) -> List[str]:
    """Retourne des lignes physiques sans couper un mot à la marge droite."""
    normalized = str(value or "").replace("\r", " ").replace("\n", " ").replace("\t", "    ")
    normalized = " ".join(normalized.split())
    if not normalized:
        return [""]
    wrapped = textwrap.wrap(
        normalized,
        width=max(8, width),
        subsequent_indent=_continuation_indent(normalized),
        break_long_words=True,
        break_on_hyphens=False,
        replace_whitespace=True,
        drop_whitespace=True,
    )
    return wrapped or [""]


def physical_transcript_lines(transcript: Sequence[str], width: int) -> List[str]:
    """Déplie le journal logique en lignes physiques prêtes à défiler."""
    result: List[str] = []
    for logical in transcript:
        result.extend(wrap_transcript_line(logical, width))
    return result


def visible_transcript_lines(
    transcript: Sequence[str],
    width: int,
    row_limit: int,
    offset_from_bottom: int = 0,
) -> List[str]:
    """Retourne une fenêtre du journal; zéro suit automatiquement la fin."""
    if row_limit <= 0:
        return []
    physical = physical_transcript_lines(transcript, width)
    max_offset = max(0, len(physical) - row_limit)
    offset = min(max(0, int(offset_from_bottom)), max_offset)
    end = max(0, len(physical) - offset)
    start = max(0, end - row_limit)
    return physical[start:end]


def transcript_scroll_state(
    pack: FramePack,
    transcript: Sequence[str],
    include_prompt: bool = True,
    offset_from_bottom: int = 0,
    columns: int | None = None,
    rows: int | None = None,
) -> Tuple[int, int, int]:
    """Normalise le défilement et retourne (offset, taille_page, maximum)."""
    box_width, total_rows = terminal_layout(pack, columns=columns, rows=rows)
    normal_box_rows = pack.height + 5
    reserved_rows = 1 + (1 if include_prompt else 0) + MIN_OUTPUT_ROWS
    compact = total_rows < normal_box_rows + reserved_rows
    box_rows = pack.height + (3 if compact else 5)
    transcript_rows = max(0, total_rows - box_rows - 1 - (1 if include_prompt else 0))
    physical_count = len(physical_transcript_lines(transcript, box_width))
    maximum = max(0, physical_count - transcript_rows)
    offset = min(max(0, int(offset_from_bottom)), maximum)
    return offset, max(1, transcript_rows), maximum


def compose_fixed_screen(
    pack: FramePack,
    frame_index: int,
    transcript: Sequence[str] = (),
    include_prompt: bool = False,
    color: bool = True,
    columns: int | None = None,
    rows: int | None = None,
    transcript_offset: int = 0,
) -> Tuple[str, int]:
    box_width, total_rows = terminal_layout(pack, columns=columns, rows=rows)
    inner_width = box_width - 2
    art_width = min(pack.width, inner_width - 2)
    art = frame_lines(
        pack.frames[frame_index % len(pack.frames)], art_width, pack.height
    )

    normal_box_rows = pack.height + 5
    reserved_rows = 1 + (1 if include_prompt else 0) + MIN_OUTPUT_ROWS
    compact = total_rows < normal_box_rows + reserved_rows

    title = " LINUXIA CLI "
    fill = max(0, box_width - len(title) - 2)
    left = fill // 2
    box_lines: List[str] = [
        "╭" + ("─" * left) + title + ("─" * (fill - left)) + "╮",
        "│" + center_text("LOCAL · AUDITABLE · PRÊTE", inner_width) + "│",
    ]
    if not compact:
        box_lines.append("│" + (" " * inner_width) + "│")
    box_lines.extend("│" + center_text(line, inner_width) + "│" for line in art)
    if not compact:
        box_lines.append("│" + (" " * inner_width) + "│")
    box_lines.append("╰" + ("─" * (box_width - 2)) + "╯")

    transcript_rows = max(
        0, total_rows - len(box_lines) - 1 - (1 if include_prompt else 0)
    )
    normalized_offset, _, maximum_offset = transcript_scroll_state(
        pack,
        transcript,
        include_prompt,
        transcript_offset,
        columns=columns,
        rows=rows,
    )
    if normalized_offset:
        label = f" HISTORIQUE · PgDn vers récent · +{normalized_offset}/{maximum_offset} "
    elif maximum_offset:
        label = " HISTORIQUE · PgUp pour remonter "
    else:
        label = " HISTORIQUE "
    lines: List[str] = [fit_text(label + ("─" * max(0, box_width - len(label))), box_width)]
    visible = visible_transcript_lines(
        transcript, box_width, transcript_rows, normalized_offset
    )
    lines.extend([""] * (transcript_rows - len(visible)))
    lines.extend(fit_text(line, box_width) for line in visible)
    lines.extend(box_lines)

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
    transcript_offset: int = 0,
) -> int:
    screen, prompt_row = compose_fixed_screen(
        pack,
        frame_index,
        transcript,
        include_prompt,
        color,
        transcript_offset=transcript_offset,
    )
    cursor_home()
    rendered = screen.split("\n")
    for index, line in enumerate(rendered):
        # 2K efface aussi les caractères tapés au-delà de la largeur du cadre.
        sys.stdout.write("\x1b[2K")
        sys.stdout.write(line)
        if index + 1 < len(rendered):
            sys.stdout.write("\n")
    # Efface les anciennes lignes si la fenêtre a été redimensionnée.
    sys.stdout.write("\x1b[J")
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
    sample = [
        "linuxia> première question",
        "LinuxIA Interprète> première réponse",
        "linuxia> deuxième question",
        "LinuxIA Interprète> Une réponse assez longue qui doit revenir proprement à la ligne sans disparaître à droite.",
    ]
    first, prompt_first = compose_fixed_screen(
        pack, 0, sample, True, False, 66, 28
    )
    second, prompt_second = compose_fixed_screen(
        pack, distinct, sample, True, False, 66, 28
    )
    scrolled, _ = compose_fixed_screen(
        pack, 0, sample * 4, True, False, 66, 28, transcript_offset=4
    )
    first_lines, second_lines = first.splitlines(), second.splitlines()
    wrapped = visible_transcript_lines(
        ["LinuxIA Interprète> Une réponse assez longue qui doit revenir proprement à la ligne."],
        32,
        3,
    )
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
            "compact_output_rows": len(first_lines) == 27 and prompt_first == 27,
            "transcript_word_wrap": len(wrapped) >= 2
            and all(len(line) <= 32 for line in wrapped),
            "latest_message_end_visible": bool(wrapped)
            and wrapped[-1].endswith("ligne."),
            "transcript_above_title": first.find("HISTORIQUE")
            < first.find("LINUXIA CLI"),
            "scroll_offset_changes_window": scrolled != first
            and "PgDn vers récent" in scrolled,
        }
    )
    return {
        "schema_version": "linuxia-ant-shell-self-test-v1",
        "ok": all(checks.values()),
        "frame_count": len(pack.frames),
        "checks": checks,
    }
