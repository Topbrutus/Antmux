from __future__ import annotations

import hashlib
import unicodedata
from pathlib import Path

ROOT = Path("tools/linuxia")
CONSOLE = ROOT / "shell/linuxia_ant_console.py"
RENDER = ROOT / "shell/render.py"
VALIDATOR = ROOT / "Test-LinuxIAShell.ps1"
README = ROOT / "README.md"
CHECKSUMS = ROOT / "checksums.sha256"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one match, found {count}")
    return text.replace(old, new, 1)


render = RENDER.read_text(encoding="utf-8")
render = replace_once(
    render,
    '''def _layout_metrics(pack: FramePack, total_rows: int, include_prompt: bool) -> Tuple[int, int, bool]:
    """Réserve d'abord un vrai viewport de journal, puis ancre l'art dans le reste."""
    prompt_rows = 1 if include_prompt else 0
    fixed_rows = 1 + prompt_rows + 3  # en-tête du journal + invite + cadre
    maximum_transcript = max(
        MIN_OUTPUT_ROWS,
        total_rows - fixed_rows - MIN_FRAME_ROWS,
    )
    preferred_transcript = max(PREFERRED_OUTPUT_ROWS_MIN, total_rows // 3)
    target_transcript = max(
        MIN_OUTPUT_ROWS,
        min(PREFERRED_OUTPUT_ROWS_MAX, preferred_transcript, maximum_transcript),
    )

    available_art = total_rows - fixed_rows - target_transcript
    art_rows = max(MIN_FRAME_ROWS, min(pack.height, available_art))
    transcript_rows = total_rows - fixed_rows - art_rows

    roomy = (
        art_rows == pack.height
        and transcript_rows >= target_transcript + 2
    )
    if roomy:
        transcript_rows -= 2
    return art_rows, max(MIN_OUTPUT_ROWS, transcript_rows), roomy
''',
    '''def _effective_prompt_rows(total_rows: int, include_prompt: bool, prompt_rows: int) -> int:
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
    maximum_transcript = max(
        MIN_OUTPUT_ROWS,
        total_rows - fixed_rows - MIN_FRAME_ROWS,
    )
    preferred_transcript = max(PREFERRED_OUTPUT_ROWS_MIN, total_rows // 3)
    target_transcript = max(
        MIN_OUTPUT_ROWS,
        min(PREFERRED_OUTPUT_ROWS_MAX, preferred_transcript, maximum_transcript),
    )

    available_art = total_rows - fixed_rows - target_transcript
    art_rows = max(MIN_FRAME_ROWS, min(pack.height, available_art))
    transcript_rows = total_rows - fixed_rows - art_rows

    roomy = (
        art_rows == pack.height
        and transcript_rows >= target_transcript + 2
    )
    if roomy:
        transcript_rows -= 2
    return art_rows, max(MIN_OUTPUT_ROWS, transcript_rows), roomy
''',
    "render layout metrics",
)
render = replace_once(
    render,
    '''def transcript_scroll_state(
    pack: FramePack,
    transcript: Sequence[str],
    include_prompt: bool = True,
    offset_from_bottom: int = 0,
    columns: int | None = None,
    rows: int | None = None,
) -> Tuple[int, int, int]:
    box_width, total_rows = terminal_layout(pack, columns=columns, rows=rows)
    _, transcript_rows, _ = _layout_metrics(pack, total_rows, include_prompt)
''',
    '''def transcript_scroll_state(
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
''',
    "render transcript scroll signature",
)
render = replace_once(
    render,
    '''    transcript_offset: int = 0,
) -> Tuple[str, int]:
    box_width, total_rows = terminal_layout(pack, columns=columns, rows=rows)
    inner_width = box_width - 2
    art_width = min(pack.width, inner_width - 2)
    art_rows, transcript_rows, roomy = _layout_metrics(pack, total_rows, include_prompt)
''',
    '''    transcript_offset: int = 0,
    prompt_rows: int = 1,
) -> Tuple[str, int]:
    box_width, total_rows = terminal_layout(pack, columns=columns, rows=rows)
    inner_width = box_width - 2
    art_width = min(pack.width, inner_width - 2)
    effective_prompt_rows = _effective_prompt_rows(total_rows, include_prompt, prompt_rows)
    art_rows, transcript_rows, roomy = _layout_metrics(
        pack, total_rows, include_prompt, prompt_rows
    )
''',
    "render compose signature",
)
render = replace_once(
    render,
    '''    normalized_offset, _, maximum_offset = transcript_scroll_state(
        pack, transcript, include_prompt, transcript_offset, columns=columns, rows=rows
    )
''',
    '''    normalized_offset, _, maximum_offset = transcript_scroll_state(
        pack,
        transcript,
        include_prompt,
        transcript_offset,
        columns=columns,
        rows=rows,
        prompt_rows=prompt_rows,
    )
''',
    "render prompt-aware scroll",
)
render = replace_once(
    render,
    '''    prompt_row = min(total_rows, len(output_lines) + 1)
    if include_prompt:
        output_lines.append(_ui(fit_text("linuxia> ", box_width), color))

    output_lines = output_lines[:total_rows]
''',
    '''    prompt_row = min(total_rows, len(output_lines) + 1)
    if include_prompt:
        continuation = " " * len("linuxia> ")
        for index in range(effective_prompt_rows):
            value = "linuxia> " if index == 0 else continuation
            output_lines.append(_ui(fit_text(value, box_width), color))

    output_lines = output_lines[:total_rows]
''',
    "render prompt rows",
)
render = replace_once(
    render,
    '''def draw_fixed_screen(
    pack: FramePack,
    frame_index: int,
    transcript: Sequence[str] = (),
    include_prompt: bool = False,
    color: bool = True,
    transcript_offset: int = 0,
) -> int:
    screen, prompt_row = compose_fixed_screen(
        pack, frame_index, transcript, include_prompt, color, transcript_offset=transcript_offset
    )
''',
    '''def draw_fixed_screen(
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
''',
    "render draw signature",
)
render = replace_once(
    render,
    '''    tall, prompt_tall = compose_fixed_screen(pack, 0, sample, True, False, 72, 80)
    compact_art_rows, compact_transcript_rows, _ = _layout_metrics(pack, 31, True)
    tall_art_rows, _, _ = _layout_metrics(pack, 79, True)
''',
    '''    tall, prompt_tall = compose_fixed_screen(pack, 0, sample, True, False, 72, 80)
    multiline, prompt_multiline = compose_fixed_screen(
        pack, 0, sample, True, False, 72, 32, prompt_rows=3
    )
    compact_art_rows, compact_transcript_rows, _ = _layout_metrics(pack, 31, True)
    multiline_art_rows, multiline_transcript_rows, _ = _layout_metrics(
        pack, 31, True, prompt_rows=3
    )
    tall_art_rows, _, _ = _layout_metrics(pack, 79, True)
''',
    "render multiline self-test setup",
)
render = replace_once(
    render,
    '''            "full_frame_when_tall": len(tall.splitlines()) == 79
            and prompt_tall == 79
            and tall_art_rows == pack.height,
''',
    '''            "full_frame_when_tall": len(tall.splitlines()) == 79
            and prompt_tall == 79
            and tall_art_rows == pack.height,
            "multiline_prompt_rows_reserved": len(multiline.splitlines()) == 31
            and prompt_multiline == 29
            and prompt_multiline < prompt_first,
            "multiline_prompt_preserves_minimum_ui": multiline_transcript_rows >= MIN_OUTPUT_ROWS
            and multiline_art_rows >= MIN_FRAME_ROWS,
''',
    "render multiline self-test checks",
)
RENDER.write_text(render, encoding="utf-8", newline="\n")

console = CONSOLE.read_text(encoding="utf-8")
console = replace_once(
    console,
    '''    hide_cursor,
    move_cursor,
    self_test,
''',
    '''    hide_cursor,
    maximum_prompt_rows,
    move_cursor,
    self_test,
''',
    "console render import",
)
console = replace_once(
    console,
    '''def _paint_input_line(
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
    sys.stdout.write("\\x1b[2K")
    sys.stdout.write(prefix + visible)
    move_cursor(prompt_row, len(prefix) + cursor_index - start + 1)
    sys.stdout.flush()
''',
    '''def _input_block_layout(
    box_width: int,
    value: Sequence[str],
    cursor_index: int,
) -> Tuple[List[str], int, int]:
    """Compose toutes les lignes physiques de saisie et la position exacte du curseur."""
    prefix = "linuxia> "
    continuation = " " * len(prefix)
    width = max(len(prefix) + 1, int(box_width))
    text = "".join(value)
    cursor = min(max(0, int(cursor_index)), len(text))
    lines = [prefix]
    row = 0
    column = len(prefix)
    cursor_row = 0
    cursor_column = column

    for index, raw_char in enumerate(text):
        char = "\\n" if raw_char == "\\r" else raw_char
        if char != "\\n" and column >= width:
            lines.append(continuation)
            row += 1
            column = len(continuation)
        if index == cursor:
            cursor_row = row
            cursor_column = column
        if char == "\\n":
            lines.append(continuation)
            row += 1
            column = len(continuation)
        else:
            lines[row] += char
            column += 1

    if cursor == len(text):
        if column >= width:
            lines.append(continuation)
            row += 1
            column = len(continuation)
        cursor_row = row
        cursor_column = column
    return lines, cursor_row, cursor_column


def _paint_input_block(
    prompt_row: int,
    lines: Sequence[str],
    cursor_row: int,
    cursor_column: int,
    prompt_rows: int,
    visible_start: int,
) -> None:
    visible = list(lines[visible_start : visible_start + prompt_rows])
    for offset in range(prompt_rows):
        move_cursor(prompt_row + offset, 1)
        sys.stdout.write("\\x1b[2K")
        if offset < len(visible):
            sys.stdout.write(visible[offset])
    move_cursor(prompt_row + cursor_row - visible_start, cursor_column + 1)
    sys.stdout.flush()
''',
    "console multiline painter",
)
start = console.index("def _read_shell_input(\n")
end = console.index("\n\ndef play_loop", start)
new_reader = '''def _read_shell_input(
    pack: FramePack,
    transcript: Sequence[str],
    color: bool,
    scroll_offset: int,
    command_history: Sequence[str],
) -> Tuple[str, int]:
    """Lit une commande, conserve les collages multilignes et gère le journal."""
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
        box_width, _ = terminal_layout(pack)
        input_lines, cursor_row, cursor_column = _input_block_layout(
            box_width, value, cursor_index
        )
        prompt_rows = min(len(input_lines), maximum_prompt_rows(pack))
        visible_start = max(
            0,
            min(
                cursor_row - prompt_rows + 1,
                len(input_lines) - prompt_rows,
            ),
        )
        scroll_offset, page_size, maximum = transcript_scroll_state(
            pack,
            transcript,
            True,
            scroll_offset,
            prompt_rows=prompt_rows,
        )
        prompt_row = draw_fixed_screen(
            pack,
            0,
            transcript,
            True,
            color,
            scroll_offset,
            prompt_rows=prompt_rows,
        )
        show_cursor()
        _paint_input_block(
            prompt_row,
            input_lines,
            cursor_row,
            cursor_column,
            prompt_rows,
            visible_start,
        )
        return prompt_row, page_size, maximum

    def read_key_burst() -> List[str]:
        """Regroupe un collage afin de distinguer ses retours internes de l'envoi final."""
        result = [msvcrt.getwch()]
        quiet_until = time.monotonic() + 0.040
        while time.monotonic() < quiet_until:
            drained = False
            while msvcrt.kbhit():
                result.append(msvcrt.getwch())
                drained = True
            if drained:
                quiet_until = time.monotonic() + 0.012
            time.sleep(0.001)
        return result

    prompt_row, page_size, maximum = redraw()
    try:
        while True:
            burst = read_key_burst()
            redraw_needed = False
            submit = False
            index = 0

            while index < len(burst):
                char = burst[index]
                if char in ("\\r", "\\n"):
                    next_index = index + 1
                    if (
                        next_index < len(burst)
                        and burst[next_index] in ("\\r", "\\n")
                        and burst[next_index] != char
                    ):
                        next_index += 1
                    if next_index < len(burst):
                        value.insert(cursor_index, "\\n")
                        cursor_index += 1
                        redraw_needed = True
                        index = next_index
                        continue
                    submit = True
                    break
                if char == "\\x03":
                    raise KeyboardInterrupt
                if char == "\\x08":
                    if cursor_index:
                        del value[cursor_index - 1]
                        cursor_index -= 1
                        redraw_needed = True
                    index += 1
                    continue
                if char in ("\\x00", "\\xe0"):
                    if index + 1 < len(burst):
                        key = burst[index + 1]
                        index += 2
                    else:
                        key = msvcrt.getwch()
                        index += 1
                    if key == "I":  # Page précédente
                        scroll_offset = min(maximum, scroll_offset + max(1, page_size - 1))
                        redraw_needed = True
                    elif key == "Q":  # Page suivante
                        scroll_offset = max(0, scroll_offset - max(1, page_size - 1))
                        redraw_needed = True
                    elif key == "K" and cursor_index:
                        cursor_index -= 1
                        redraw_needed = True
                    elif key == "M" and cursor_index < len(value):
                        cursor_index += 1
                        redraw_needed = True
                    elif key == "G":
                        cursor_index = 0
                        redraw_needed = True
                    elif key == "O":
                        cursor_index = len(value)
                        redraw_needed = True
                    elif key == "S" and cursor_index < len(value):
                        del value[cursor_index]
                        redraw_needed = True
                    elif key == "H" and command_history:
                        history_index = max(0, history_index - 1)
                        value[:] = list(command_history[history_index])
                        cursor_index = len(value)
                        redraw_needed = True
                    elif key == "P" and command_history:
                        history_index = min(len(command_history), history_index + 1)
                        value[:] = [] if history_index == len(command_history) else list(command_history[history_index])
                        cursor_index = len(value)
                        redraw_needed = True
                    continue
                if char == "\\t":
                    value[cursor_index:cursor_index] = list("    ")
                    cursor_index += 4
                    redraw_needed = True
                elif char.isprintable():
                    value.insert(cursor_index, char)
                    cursor_index += 1
                    redraw_needed = True
                index += 1

            if submit:
                return "".join(value).strip(), scroll_offset
            if redraw_needed:
                prompt_row, page_size, maximum = redraw()
    finally:
        hide_cursor()
'''
console = console[:start] + new_reader + console[end:]
console = replace_once(
    console,
    '''        result["checks"]["transcript_buffer_4000"] = (
            len(transcript_probe) == TRANSCRIPT_LINE_LIMIT
            and transcript_probe[0] == "5"
        )
        result["ok"] = all(result["checks"].values())
''',
    '''        result["checks"]["transcript_buffer_4000"] = (
            len(transcript_probe) == TRANSCRIPT_LINE_LIMIT
            and transcript_probe[0] == "5"
        )
        input_probe = list("abc\\ndef")
        input_lines, input_cursor_row, input_cursor_column = _input_block_layout(
            20, input_probe, len(input_probe)
        )
        wrapped_lines, wrapped_cursor_row, _ = _input_block_layout(
            14, list("123456789012"), 12
        )
        result["checks"]["multiline_input_newline_preserved"] = (
            input_lines == ["linuxia> abc", "         def"]
            and input_cursor_row == 1
            and input_cursor_column == 12
        )
        result["checks"]["multiline_input_wraps_upward"] = (
            len(wrapped_lines) == 3 and wrapped_cursor_row == 2
        )
        result["ok"] = all(result["checks"].values())
''',
    "console input self-tests",
)
CONSOLE.write_text(console, encoding="utf-8", newline="\n")

validator = VALIDATOR.read_text(encoding="utf-8")
validator = replace_once(
    validator,
    '''    Add-ShellTestResult 'STATIC-LOG-VIEWPORT' `
        ($scriptText -match 'PREFERRED_OUTPUT_ROWS_MIN\\s*=\\s*8' -and `
         $scriptText -match 'visible_log_rows_at_least_10') `
        'A standard terminal reserves at least ten visible rows for the log'
''',
    '''    Add-ShellTestResult 'STATIC-LOG-VIEWPORT' `
        ($scriptText -match 'PREFERRED_OUTPUT_ROWS_MIN\\s*=\\s*8' -and `
         $scriptText -match 'visible_log_rows_at_least_10') `
        'A standard terminal reserves at least ten visible rows for the log'
    Add-ShellTestResult 'STATIC-MULTILINE-INPUT' `
        ($consoleText -match '_input_block_layout' -and `
         $consoleText -match 'read_key_burst' -and `
         $consoleText -match 'maximum_prompt_rows' -and `
         $consoleText -match 'prompt_rows=prompt_rows' -and `
         $consoleText.Contains('value.insert(cursor_index, "\\n")')) `
        'Pasted text keeps internal line breaks and expands the input block upward'
''',
    "validator multiline static check",
)
VALIDATOR.write_text(validator, encoding="utf-8", newline="\n")

readme = README.read_text(encoding="utf-8")
readme = replace_once(
    readme,
    '''Le lancement du modèle résident utilise explicitement `--think=false`. Si la version locale d'Ollama ne fournit pas ce contrôle, LinuxIA refuse l'inférence plutôt que d'afficher le raisonnement interne. Un filtre défensif retire aussi les balises ou préfixes de raisonnement résiduels.
''',
    '''Le lancement du modèle résident utilise explicitement `--think=false`. Si la version locale d'Ollama ne fournit pas ce contrôle, LinuxIA refuse l'inférence plutôt que d'afficher le raisonnement interne. Un filtre défensif retire aussi les balises ou préfixes de raisonnement résiduels.

Sous Windows, la saisie se développe maintenant sur plusieurs lignes. Un collage conserve ses retours internes, toutes les lignes disponibles restent visibles et le cadre remonte automatiquement à mesure que le bloc de saisie grandit; seul le dernier retour du collage, ou la touche Entrée pressée séparément, envoie le message.
''',
    "README multiline input",
)
README.write_text(readme, encoding="utf-8", newline="\n")

entries: list[tuple[str, str]] = []
for line in CHECKSUMS.read_text(encoding="utf-8").splitlines():
    if line.strip():
        digest, relative = line.split("  ", 1)
        entries.append((digest, relative))

updated: list[str] = []
for _, relative in entries:
    raw = (ROOT / relative).read_bytes()
    text = raw.decode("utf-8-sig")
    canonical = unicodedata.normalize(
        "NFC",
        text.replace("\r\n", "\n").replace("\r", "\n"),
    )
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    updated.append(f"{digest}  {relative}")
CHECKSUMS.write_text("\n".join(updated) + "\n", encoding="utf-8", newline="\n")
