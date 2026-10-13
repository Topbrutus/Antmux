from __future__ import annotations

import argparse
import heapq
import json
from datetime import datetime, timezone
from pathlib import Path


def prune(root: Path, retain: int) -> dict:
    retain = max(20, int(retain))
    root.mkdir(parents=True, exist_ok=True)

    def entries():
        for p in root.glob("*.json"):
            try:
                st = p.stat()
            except FileNotFoundError:
                continue
            yield (st.st_mtime_ns, p.name, st.st_size)

    newest = heapq.nlargest(retain, entries(), key=lambda item: (item[0], item[1]))
    keep = {name for _, name, _ in newest}
    before_count = 0
    before_bytes = 0
    deleted_count = 0
    deleted_bytes = 0
    for p in root.glob("*.json"):
        try:
            st = p.stat()
        except FileNotFoundError:
            continue
        before_count += 1
        before_bytes += st.st_size
        if p.name not in keep:
            p.unlink(missing_ok=True)
            deleted_count += 1
            deleted_bytes += st.st_size

    result = {
        "schema": "BROTOCULATEUR-SNAPSHOT-RETENTION-v1",
        "pruned_at": datetime.now(timezone.utc).isoformat(),
        "root": str(root),
        "retain": retain,
        "before_count": before_count,
        "before_bytes": before_bytes,
        "deleted_count": deleted_count,
        "deleted_bytes": deleted_bytes,
        "remaining_count": before_count - deleted_count,
        "remaining_bytes_estimate": before_bytes - deleted_bytes,
    }
    manifest = root.parent / "snapshot-retention-manifest.json"
    manifest.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return result


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("--retain", type=int, default=512)
    args = ap.parse_args()
    prune(Path(args.root), args.retain)


if __name__ == "__main__":
    main()
