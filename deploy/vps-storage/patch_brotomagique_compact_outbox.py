from __future__ import annotations

import argparse
import shutil
from datetime import datetime, timezone
from pathlib import Path

MARKER = "BRUTOMAGIQUE-COMPACT-OUTBOX-v1"
OLD_VARIANTS = (
    '''        with outbox_path.open("a", encoding="utf-8") as handle:\n            handle.write(_canonical_json(crystal) + "\\n")\n''',
    '''        with self.outbox_path.open("a", encoding="utf-8") as handle:\n            handle.write(_canonical_json(crystal) + "\\n")\n''',
)
NEW_TEMPLATE = '''        # BRUTOMAGIQUE-COMPACT-OUTBOX-v1: the full crystal remains in the crystal file;\n        # the append-only feed carries only the fields consumed by downstream readers.\n        feed_record = {\n            key: crystal.get(key)\n            for key in (\n                "SCHEMA",\n                "CRYSTAL_ID",\n                "CRYSTAL_H256",\n                "FORMULA_ID",\n                "LEVEL",\n                "COVERAGE",\n                "CREATED_AT",\n                "PURE_ROUTE",\n            )\n            if key in crystal\n        }\n        with __OUTBOX__.open("a", encoding="utf-8") as handle:\n            handle.write(_canonical_json(feed_record) + "\\n")\n'''


def patch(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if MARKER in text:
        print(f"ALREADY_PATCHED={path}")
        return
    matched = None
    outbox_expr = None
    for candidate in OLD_VARIANTS:
        if candidate in text:
            matched = candidate
            outbox_expr = "self.outbox_path" if "self.outbox_path" in candidate else "outbox_path"
            break
    if matched is None or outbox_expr is None:
        raise RuntimeError("expected outbox writer block not found; refusing blind patch")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = path.with_name(path.name + f".storagefix-{stamp}.bak")
    shutil.copy2(path, backup)
    replacement = NEW_TEMPLATE.replace("__OUTBOX__", outbox_expr)
    path.write_text(text.replace(matched, replacement, 1), encoding="utf-8", newline="\n")
    print(f"PATCHED={path}")
    print(f"BACKUP={backup}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    args = ap.parse_args()
    patch(Path(args.path))


if __name__ == "__main__":
    main()
