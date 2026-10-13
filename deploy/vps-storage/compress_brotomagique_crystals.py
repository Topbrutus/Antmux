from __future__ import annotations

import argparse
import gzip
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path


def compress(root: Path, min_age_seconds: int, max_files: int) -> dict:
    now = time.time()
    considered = 0
    compressed = 0
    raw_bytes = 0
    gzip_bytes = 0
    failures = 0

    for path in root.glob("*.json"):
        if compressed >= max_files:
            break
        try:
            st = path.stat()
        except FileNotFoundError:
            continue
        if now - st.st_mtime < min_age_seconds:
            continue
        considered += 1
        target = path.with_suffix(path.suffix + ".gz")
        temp = target.with_suffix(target.suffix + ".tmp")
        try:
            with path.open("rb") as src, temp.open("wb") as raw_dst:
                with gzip.GzipFile(fileobj=raw_dst, mode="wb", compresslevel=6, mtime=0) as dst:
                    while True:
                        chunk = src.read(1024 * 1024)
                        if not chunk:
                            break
                        dst.write(chunk)
            with gzip.open(temp, "rb") as check:
                while check.read(1024 * 1024):
                    pass
            gz_size = temp.stat().st_size
            os.replace(temp, target)
            path.unlink()
            compressed += 1
            raw_bytes += st.st_size
            gzip_bytes += gz_size
        except Exception:
            failures += 1
            temp.unlink(missing_ok=True)
            continue

    result = {
        "schema": "BRUTOMAGIQUE-CRYSTAL-GZIP-v1",
        "compressed_at": datetime.now(timezone.utc).isoformat(),
        "root": str(root),
        "min_age_seconds": min_age_seconds,
        "max_files": max_files,
        "considered": considered,
        "compressed": compressed,
        "failures": failures,
        "raw_bytes": raw_bytes,
        "gzip_bytes": gzip_bytes,
        "freed_bytes": raw_bytes - gzip_bytes,
        "ratio": (gzip_bytes / raw_bytes) if raw_bytes else None,
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return result


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("--min-age-seconds", type=int, default=900)
    ap.add_argument("--max-files", type=int, default=100000)
    args = ap.parse_args()
    result = compress(Path(args.root), args.min_age_seconds, args.max_files)
    if result["failures"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
