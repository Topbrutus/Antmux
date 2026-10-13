from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

FIELDS = (
    "SCHEMA",
    "CRYSTAL_ID",
    "CRYSTAL_H256",
    "FORMULA_ID",
    "LEVEL",
    "COVERAGE",
    "CREATED_AT",
    "PURE_ROUTE",
)


def canonical(obj: dict) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def compact(path: Path) -> dict:
    if not path.exists():
        return {"path": str(path), "status": "MISSING"}
    tmp = path.with_suffix(path.suffix + ".compact.tmp")
    manifest = path.with_name(path.name + ".compaction-manifest.json")
    source_hash = hashlib.sha256()
    output_hash = hashlib.sha256()
    source_bytes = 0
    output_bytes = 0
    lines = 0
    errors = 0
    progress_step = 512 * 1024 * 1024
    next_progress = progress_step
    tmp.unlink(missing_ok=True)
    with path.open("rb") as src, tmp.open("wb") as dst:
        for raw in src:
            source_hash.update(raw)
            source_bytes += len(raw)
            if source_bytes >= next_progress:
                print(f"OUTBOX_COMPACT_PROGRESS path={path} source_bytes={source_bytes} lines={lines}", flush=True)
                next_progress += progress_step
            if not raw.strip():
                continue
            try:
                obj = json.loads(raw)
                record = {key: obj.get(key) for key in FIELDS if key in obj}
                if not record.get("CRYSTAL_ID") or not record.get("CRYSTAL_H256"):
                    raise ValueError("missing crystal identity")
                encoded = (canonical(record) + "\n").encode("utf-8")
            except Exception:
                errors += 1
                continue
            dst.write(encoded)
            output_hash.update(encoded)
            output_bytes += len(encoded)
            lines += 1
        dst.flush()
        os.fsync(dst.fileno())
    if errors:
        tmp.unlink(missing_ok=True)
        raise RuntimeError(f"refusing compaction: {errors} invalid lines")
    result = {
        "schema": "BRUTOMAGIQUE-OUTBOX-COMPACTION-v1",
        "compacted_at": datetime.now(timezone.utc).isoformat(),
        "path": str(path),
        "lines": lines,
        "source_bytes": source_bytes,
        "compact_bytes": output_bytes,
        "freed_bytes": source_bytes - output_bytes,
        "source_sha256": source_hash.hexdigest(),
        "compact_sha256": output_hash.hexdigest(),
        "fields": list(FIELDS),
        "full_payload_source": "individual crystal files remain authoritative",
    }
    manifest.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)
    return result


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="+")
    args = ap.parse_args()
    for raw in args.paths:
        result = compact(Path(raw))
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
