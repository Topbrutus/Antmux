# -*- coding: utf-8 -*-
"""Rendu ANSI fixe : journal en haut, animation centrée et ancrée en bas."""

from __future__ import annotations

import ctypes
import os
import re
import shutil
import sys
import textwrap
from typing import List, Sequence, Tuple

from frames import FramePack

ANSI_RESET = "\x1b[0m"
ANSI_PURPLE = "\x1b[38;5;141m"
ANSI_SGR_RE = re.compile(r"\x1b\[[0-9;]*m")
MIN_OUTPUT_ROWS = 3
PREFERRED_OUTPUT_ROWS_MIN = 8
PREFERRED_OUTPUT_ROWS_MAX = 12
MIN_FRAME_ROWS = 8


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


def strip_ansi(value: str) -> str:
    return ANSI_SGR_RE.sub("", value)


def visible_width(value: str) -> int:
    return len(strip_ansi(value))


def fit_text(value: str, width: int) -> str:
    value = value.replace("\r", " ").replace("\n", " ").replace("\t", "    ")
    if len(value) > width:
        return value[: max(0, width - 1)] + ("…" if width else "")
    return value + (" " * (width - len(value)))


def center_text(value: str, width: int) -> str:
    value = value[:width]
    left = max(0, (width - len(value)) // 2)
    return (" " * left) + value + (" " * (width - len(value) - left))


def center_ansi(value: str, width: int, color: bool) -> str:
    rendered = value if color else strip_ansi(value)
    current = visible_width(rendered)
    if current > width:
        raise RuntimeError(
            f"Image LinuxIA trop large : {current} colonnes visibles pour une zone de {width}."
        )
    left = (width - current) // 2
    right = width - current - left
    return (" " * left) + rendered + (" " * right)


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
    minimum_rows = 1 + MIN_OUTPUT_ROWS + 1 + 3 + MIN_FRAME_ROWS
    if safe_rows < minimum_rows:
        raise RuntimeError(
            f"Terminal trop bas : {detected_rows} lignes; "
            f"au moins {minimum_rows + 1} sont nécessaires."
        )
    return box_width, safe_rows


def _effective_prompt_rows(total_rows: int, include_prompt: bool, prompt_rows: int) -> int:
    if not include_prompt:
        return 0
    maximum = max(
        1,
        total_rows - (1 + MIN_OUTPUT_ROWS + 3 + MIN_FRAME_ROWS),
    )
    return min(max(1, int(prompt_rows)), maximum)


def maximum_prompt_rows(
    pack: FramePack,
    columns: int | None = None,
    rows: int | None = None,
) -> int:
    """Nombre maximal de lignes de saisie sans masquer le journal ni l'animation minimale."""
    _, total_rows = terminal_layout(pack, columns=columns, rows=rows)
    return _effective_prompt_rows(total_rows, True, total_rows)


def _layout_metrics(
    pack: FramePack,
    total_rows: int,
    include_prompt: bool,
    prompt_rows: int = 1,
) -> Tuple[int, int, bool]:
    """Réserve d'abord un vrai viewport de journal, puis ancre l'art dans le reste."""
    effective_prompt_rows = _effective_prompt_rows(total_rows, include_prompt, prompt_rows)
    fixed_rows = 1 + effective_prompt_rows + 3  # en-tête du journal + invite + cadre

    baseline_prompt_rows = 1 if include_prompt else 0
    baseline_fixed_rows = 1 + baseline_prompt_rows + 3
    maximum_transcript = max(
        MIN_OUTPUT_ROWS,
        total_rows - baseline_fixed_rows - MIN_FRAME_ROWS,
    )
    preferred_transcript = max(PREFERRED_OUTPUT_ROWS_MIN, total_rows // 3)
    target_transcript = max(
        MIN_OUTPUT_ROWS,
        min(PREFERRED_OUTPUT_ROWS_MAX, preferred_transcript, maximum_transcript),
    )
    baseline_art_rows = max(
        MIN_FRAME_ROWS,
        min(
            pack.height,
            total_rows - baseline_fixed_rows - target_transcript,
        ),
    )

    available_content = total_rows - fixed_rows
    roomy = (
        baseline_art_rows == pack.height
        and available_content >= baseline_art_rows + target_transcript + 2
    )
    art_rows = baseline_art_rows
    transcript_rows = available_content - art_rows - (2 if roomy else 0)
    if transcript_rows < MIN_OUTPUT_ROWS:
        roomy = False
        art_rows = max(
            MIN_FRAME_ROWS,
            min(baseline_art_rows, available_content - MIN_OUTPUT_ROWS),
        )
        transcript_rows = available_content - art_rows
    return art_rows, max(MIN_OUTPUT_ROWS, transcript_rows), roomy


def _sample_rows(lines: Sequence[str], target_height: int) -> List[str]:
    if target_height >= len(lines):
        return list(lines)
    if target_height <= 1:
        return [lines[len(lines) // 2]]
    last = len(lines) - 1
    return [lines[round(index * last / (target_height - 1))] for index in range(target_height)]


def frame_lines(frame: str, width: int, height: int, color: bool = True) -> List[str]:
    """Rend une image à sa hauteur native, centrée sans toucher aux codes ANSI."""
    source = frame.splitlines()
    if len(source) != height:
        raise ValueError(f"Image LinuxIA invalide : {len(source)} lignes au lieu de {height}.")
    return [center_ansi(line, width, color) for line in source]


def scaled_frame_lines(
    frame: str,
    width: int,
    source_height: int,
    target_height: int,
    color: bool,
) -> List[str]:
    source = frame.splitlines()
    if len(source) != source_height:
        raise ValueError(
            f"Image LinuxIA invalide : {len(source)} lignes au lieu de {source_height}."
        )
    return [center_ansi(line, width, color) for line in _sample_rows(source, target_height)]


def _continuation_indent(value: str) -> str:
    for prefix in ("LinuxIA Interprète> ", "Reine> ", "linuxia> ", "ERREUR: ", "EXIT_CODE: "):
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
    prompt_rows: int = 1,
) -> Tuple[int, int, int]:
    box_width, total_rows = terminal_layout(pack, columns=columns, rows=rows)
    _, transcript_rows, _ = _layout_metrics(
        pack, total_rows, include_prompt, prompt_rows
    )
    physical_count = len(physical_transcript_lines(transcript, box_width))
    maximum = max(0, physical_count - transcript_rows)
    offset = min(max(0, int(offset_from_bottom)), maximum)
    return offset, max(1, transcript_rows), maximum


def _ui(value: str, color: bool) -> str:
    return f"{ANSI_PURPLE}{value}{ANSI_RESET}" if color else value


def compose_fixed_screen(
    pack: FramePack,
    frame_index: int,
    transcript: Sequence[str] = (),
    include_prompt: bool = False,
    color: bool = True,
    columns: int | None = None,
    rows: int | None = None,
    transcript_offset: int = 0,
    prompt_rows: int = 1,
) -> Tuple[str, int]:
    box_width, total_rows = terminal_layout(pack, columns=columns, rows=rows)
    inner_width = box_width - 2
    art_width = min(pack.width, inner_width - 2)
    effective_prompt_rows = _effective_prompt_rows(total_rows, include_prompt, prompt_rows)
    art_rows, transcript_rows, roomy = _layout_metrics(
        pack, total_rows, include_prompt, prompt_rows
    )
    art = scaled_frame_lines(
        pack.frames[frame_index % len(pack.frames)],
        art_width,
        pack.height,
        art_rows,
        color,
    )

    title = " LINUXIA CLI "
    fill = max(0, box_width - len(title) - 2)
    left = fill // 2
    plain_box: List[Tuple[str, bool]] = [
        ("╭" + ("─" * left) + title + ("─" * (fill - left)) + "╮", False),
        ("│" + center_text("LOCAL · AUDITABLE · PRÊTE", inner_width) + "│", False),
    ]
    if roomy:
        plain_box.append(("│" + (" " * inner_width) + "│", False))
    plain_box.extend((line, True) for line in art)
    if roomy:
        plain_box.append(("│" + (" " * inner_width) + "│", False))
    plain_box.append(("╰" + ("─" * (box_width - 2)) + "╯", False))

    normalized_offset, _, maximum_offset = transcript_scroll_state(
        pack,
        transcript,
        include_prompt,
        transcript_offset,
        columns=columns,
        rows=rows,
        prompt_rows=prompt_rows,
    )
    if normalized_offset:
        label = f" HISTORIQUE · PgDn vers récent · +{normalized_offset}/{maximum_offset} "
    elif maximum_offset:
        label = " HISTORIQUE · PgUp pour remonter "
    else:
        label = " HISTORIQUE "

    output_lines: List[str] = [_ui(fit_text(label + ("─" * max(0, box_width - len(label))), box_width), color)]
    visible = visible_transcript_lines(transcript, box_width, transcript_rows, normalized_offset)
    output_lines.extend(_ui(" " * box_width, color) for _ in range(transcript_rows - len(visible)))
    output_lines.extend(_ui(fit_text(line, box_width), color) for line in visible)

    for value, is_art in plain_box:
        if not is_art:
            output_lines.append(_ui(fit_text(value, box_width), color))
        else:
            # L'image garde ses vraies couleurs; les bordures restent violettes.
            output_lines.append(_ui("│", color) + center_ansi(value, inner_width, color) + _ui("│", color))

    prompt_row = min(total_rows, len(output_lines) + 1)
    if include_prompt:
        continuation = " " * len("linuxia> ")
        for index in range(effective_prompt_rows):
            value = "linuxia> " if index == 0 else continuation
            output_lines.append(_ui(fit_text(value, box_width), color))

    output_lines = output_lines[:total_rows]
    return "\n".join(output_lines), prompt_row


def draw_fixed_screen(
    pack: FramePack,
    frame_index: int,
    transcript: Sequence[str] = (),
    include_prompt: bool = False,
    color: bool = True,
    transcript_offset: int = 0,
    prompt_rows: int = 1,
) -> int:
    screen, prompt_row = compose_fixed_screen(
        pack,
        frame_index,
        transcript,
        include_prompt,
        color,
        transcript_offset=transcript_offset,
        prompt_rows=prompt_rows,
    )
    cursor_home()
    rendered = screen.split("\n")
    for index, line in enumerate(rendered):
        sys.stdout.write("\x1b[2K")
        sys.stdout.write(line)
        if index + 1 < len(rendered):
            sys.stdout.write("\n")
    sys.stdout.write("\x1b[J")
    sys.stdout.flush()
    return prompt_row


def self_test(pack: FramePack) -> dict:
    plain_frames = [strip_ansi(frame) for frame in pack.frames]
    checks = {
        "frame_count_36": len(pack.frames) == 36,
        "positive_dimensions": pack.width == 60 and pack.height == 55,
        "source_dimensions_60x70": pack.metadata.get("source_width") == 60
        and pack.metadata.get("source_height") == 70,
        "truecolor_frames": all("\x1b[38;2;" in frame for frame in pack.frames),
        "frame_height_exact": all(len(frame.splitlines()) == pack.height for frame in pack.frames),
        "frame_width_exact": all(
            len(line) == pack.width
            for frame in plain_frames
            for line in frame.splitlines()
        ),
    }
    distinct = next((i for i, frame in enumerate(pack.frames[1:], 1) if frame != pack.frames[0]), 0)
    sample = [
        "linuxia> première question",
        "LinuxIA Interprète> première réponse",
        "linuxia> deuxième question",
        "LinuxIA Interprète> Une réponse assez longue qui doit revenir proprement à la ligne sans disparaître à droite.",
    ]
    first, prompt_first = compose_fixed_screen(pack, 0, sample, True, False, 72, 32)
    second, prompt_second = compose_fixed_screen(pack, distinct, sample, True, False, 72, 32)
    scrolled, _ = compose_fixed_screen(pack, 0, sample * 4, True, False, 72, 32, transcript_offset=4)
    color_screen, _ = compose_fixed_screen(pack, 0, sample, True, True, 72, 32)
    tall, prompt_tall = compose_fixed_screen(pack, 0, sample, True, False, 72, 80)
    multiline, prompt_multiline = compose_fixed_screen(
        pack, 0, sample, True, False, 72, 32, prompt_rows=3
    )
    compact_art_rows, compact_transcript_rows, _ = _layout_metrics(pack, 31, True)
    multiline_art_rows, multiline_transcript_rows, _ = _layout_metrics(
        pack, 31, True, prompt_rows=3
    )
    tall_art_rows, _, _ = _layout_metrics(pack, 79, True)
    first_lines, second_lines = first.splitlines(), second.splitlines()
    wrapped = visible_transcript_lines(
        ["LinuxIA Interprète> Une réponse assez longue qui doit revenir proprement à la ligne."], 32, 3
    )
    checks.update(
        {
            "distinct_animation_frame": distinct > 0 and first != second,
            "fixed_line_count": len(first_lines) == len(second_lines),
            "fixed_line_width": len({len(x) for x in first_lines}) == 1
            and len({len(x) for x in second_lines}) == 1,
            "fixed_prompt_row": prompt_first == prompt_second,
            "no_trailing_newline": not first.endswith("\n") and not second.endswith("\n"),
            "no_clear_sequence_in_frame": "\x1b[2J" not in first and "\x1b[2J" not in second,
            "no_flashing_status": "LINUXIA TRAVAILLE" not in first and "·  ·  ·" not in first,
            "compact_output_rows": len(first_lines) == 31 and prompt_first == 31,
            "visible_log_rows_at_least_10": compact_transcript_rows >= 10
            and compact_art_rows >= MIN_FRAME_ROWS,
            "transcript_word_wrap": len(wrapped) >= 2 and all(len(line) <= 32 for line in wrapped),
            "latest_message_end_visible": bool(wrapped) and wrapped[-1].endswith("ligne."),
            "transcript_above_title": first.find("HISTORIQUE") < first.find("LINUXIA CLI"),
            "scroll_offset_changes_window": scrolled != first and "PgDn vers récent" in scrolled,
            "animation_anchor_stable": first.find("LINUXIA CLI") == second.find("LINUXIA CLI")
            and prompt_first == prompt_second,
            "ansi_truecolor_preserved": "\x1b[38;2;" in color_screen,
            "full_frame_when_tall": len(tall.splitlines()) == 79
            and prompt_tall == 79
            and tall_art_rows == pack.height,
            "multiline_prompt_rows_reserved": len(multiline.splitlines()) == 31
            and prompt_multiline == 29
            and prompt_multiline < prompt_first,
            "multiline_prompt_preserves_minimum_ui": multiline_transcript_rows >= MIN_OUTPUT_ROWS
            and multiline_art_rows >= MIN_FRAME_ROWS,
            "multiline_prompt_shrinks_log_before_art": multiline_art_rows == compact_art_rows
            and multiline_transcript_rows == compact_transcript_rows - 2,
        }
    )
    return {
        "schema_version": "linuxia-ant-shell-self-test-v2",
        "ok": all(checks.values()),
        "frame_count": len(pack.frames),
        "checks": checks,
    }
