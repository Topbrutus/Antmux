from __future__ import annotations

import hashlib
import unicodedata
from pathlib import Path

ROOT = Path("tools/linuxia")
RENDER = ROOT / "shell/render.py"
CONSOLE = ROOT / "shell/linuxia_ant_console.py"
CHECKSUMS = ROOT / "checksums.sha256"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one match, found {count}")
    return text.replace(old, new, 1)


render = RENDER.read_text(encoding="utf-8")
render = replace_once(
    render,
    '''    effective_prompt_rows = _effective_prompt_rows(total_rows, include_prompt, prompt_rows)
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
''',
    '''    effective_prompt_rows = _effective_prompt_rows(total_rows, include_prompt, prompt_rows)
    fixed_rows = 1 + effective_prompt_rows + 3  # en-tête du journal + invite + cadre
    preferred_transcript = max(PREFERRED_OUTPUT_ROWS_MIN, total_rows // 3)
    baseline_fixed_rows = 1 + (1 if include_prompt else 0) + 3
    baseline_art_rows = max(
        MIN_FRAME_ROWS,
        min(
            pack.height,
            total_rows - baseline_fixed_rows - preferred_transcript,
        ),
    )
    available_content = total_rows - fixed_rows
    transcript_rows = max(
        MIN_OUTPUT_ROWS,
        min(preferred_transcript, available_content - baseline_art_rows),
    )
    art_rows = max(
        MIN_FRAME_ROWS,
        min(pack.height, available_content - transcript_rows),
    )
''',
    "prefer shrinking log before art",
)
render = replace_once(
    render,
    '''            "multiline_prompt_preserves_minimum_ui": multiline_transcript_rows >= MIN_OUTPUT_ROWS
            and multiline_art_rows >= MIN_FRAME_ROWS,
''',
    '''            "multiline_prompt_preserves_minimum_ui": multiline_transcript_rows >= MIN_OUTPUT_ROWS
            and multiline_art_rows >= MIN_FRAME_ROWS,
            "multiline_prompt_shrinks_log_before_art": multiline_art_rows == compact_art_rows
            and multiline_transcript_rows == compact_transcript_rows - 2,
''',
    "render refinement self-test",
)
RENDER.write_text(render, encoding="utf-8", newline="\n")

console = CONSOLE.read_text(encoding="utf-8")
console = replace_once(
    console,
    '''        result = [msvcrt.getwch()]
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
''',
    '''        result = [msvcrt.getwch()]
        time.sleep(0.002)
        if not msvcrt.kbhit():
            return result
        quiet_until = time.monotonic() + 0.012
        while time.monotonic() < quiet_until:
            drained = False
            while msvcrt.kbhit():
                result.append(msvcrt.getwch())
                drained = True
            if drained:
                quiet_until = time.monotonic() + 0.006
            time.sleep(0.001)
        return result
''',
    "fast normal typing burst detection",
)
CONSOLE.write_text(console, encoding="utf-8", newline="\n")

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
