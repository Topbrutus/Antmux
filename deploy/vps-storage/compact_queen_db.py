from __future__ import annotations

import argparse
import json
import os
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path


def compact(db_path: Path, retain: int) -> dict:
    retain = max(20, int(retain))
    temp = db_path.with_suffix(db_path.suffix + ".compact.tmp")
    previous = db_path.with_suffix(db_path.suffix + ".precompact")
    temp.unlink(missing_ok=True)
    previous.unlink(missing_ok=True)

    with closing(sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)) as src:
        old_count, old_min, old_max = src.execute(
            "SELECT count(*), min(id), max(id) FROM checkpoints"
        ).fetchone()
        schema = src.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='checkpoints'"
        ).fetchone()
        if not schema or not schema[0]:
            raise RuntimeError("checkpoints schema missing")
        rows = src.execute(
            "SELECT id, created_at, state_json, protected_h256, whole_h256 "
            "FROM checkpoints ORDER BY id DESC LIMIT ?",
            (retain,),
        ).fetchall()
    rows.reverse()
    if not rows:
        raise RuntimeError("no checkpoints to retain")

    with closing(sqlite3.connect(temp)) as dst:
        dst.execute(schema[0])
        dst.executemany(
            "INSERT INTO checkpoints(id, created_at, state_json, protected_h256, whole_h256) "
            "VALUES (?, ?, ?, ?, ?)",
            rows,
        )
        dst.commit()
        check = dst.execute("PRAGMA integrity_check").fetchone()[0]
        new_count, new_min, new_max = dst.execute(
            "SELECT count(*), min(id), max(id) FROM checkpoints"
        ).fetchone()
    if check != "ok" or new_count != len(rows) or new_max != old_max:
        temp.unlink(missing_ok=True)
        raise RuntimeError("compact database validation failed")

    result = {
        "schema": "ANTMUX-X72-QUEEN-DB-COMPACTION-v1",
        "compacted_at": datetime.now(timezone.utc).isoformat(),
        "retain": retain,
        "old_count": old_count,
        "old_min_id": old_min,
        "old_max_id": old_max,
        "new_count": new_count,
        "new_min_id": new_min,
        "new_max_id": new_max,
        "old_bytes": db_path.stat().st_size,
        "new_bytes": temp.stat().st_size,
    }
    manifest = db_path.with_name(db_path.name + ".compaction-manifest.json")
    manifest.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    os.replace(db_path, previous)
    os.replace(temp, db_path)
    result["previous_path"] = str(previous)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return result


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("db_path")
    ap.add_argument("--retain", type=int, default=256)
    args = ap.parse_args()
    compact(Path(args.db_path), args.retain)


if __name__ == "__main__":
    main()
