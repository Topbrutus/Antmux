from __future__ import annotations

import argparse
import shutil
from datetime import datetime, timezone
from pathlib import Path

MARKER = "DEFAULT_MAX_CHECKPOINTS = 256"
INIT_OLD = '''class Persistence:\n    def __init__(self, db_path: Path):\n        self.db_path = db_path\n        self.db_path.parent.mkdir(parents=True, exist_ok=True)\n'''
INIT_NEW = '''class Persistence:\n    DEFAULT_MAX_CHECKPOINTS = 256\n\n    def __init__(self, db_path: Path, max_checkpoints: int = DEFAULT_MAX_CHECKPOINTS):\n        self.db_path = db_path\n        self.max_checkpoints = max(20, int(max_checkpoints))\n        self.db_path.parent.mkdir(parents=True, exist_ok=True)\n'''
SAVE_OLD = '''            db.execute(\n                "INSERT INTO checkpoints(created_at, state_json, protected_h256, whole_h256) VALUES (?, ?, ?, ?)",\n                (time.time(), state_json, queen.protected_h256(), queen.whole_h256()),\n            )\n            db.commit()\n'''
SAVE_NEW = '''            cursor = db.execute(\n                "INSERT INTO checkpoints(created_at, state_json, protected_h256, whole_h256) VALUES (?, ?, ?, ?)",\n                (time.time(), state_json, queen.protected_h256(), queen.whole_h256()),\n            )\n            newest_id = int(cursor.lastrowid or 0)\n            cutoff_id = newest_id - self.max_checkpoints\n            if cutoff_id > 0:\n                db.execute(\n                    "DELETE FROM checkpoints WHERE id IN ("\n                    "SELECT id FROM checkpoints WHERE id <= ? ORDER BY id ASC LIMIT 128)",\n                    (cutoff_id,),\n                )\n            db.commit()\n'''


def patch(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if MARKER in text:
        print(f"ALREADY_PATCHED={path}")
        return
    if INIT_OLD not in text:
        raise RuntimeError("expected Persistence init block not found; refusing blind patch")
    if SAVE_OLD not in text:
        raise RuntimeError("expected Persistence save block not found; refusing blind patch")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = path.with_name(path.name + f".retention-{stamp}.bak")
    shutil.copy2(path, backup)
    text = text.replace(INIT_OLD, INIT_NEW, 1)
    text = text.replace(SAVE_OLD, SAVE_NEW, 1)
    path.write_text(text, encoding="utf-8", newline="\n")
    print(f"PATCHED={path}")
    print(f"BACKUP={backup}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    args = ap.parse_args()
    patch(Path(args.path))


if __name__ == "__main__":
    main()
