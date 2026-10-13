from __future__ import annotations

import argparse
import shutil
from datetime import datetime, timezone
from pathlib import Path

MARKER = "BRUTOMAGIQUE-GZIP-CRYSTALS-v1"
IMPORT_OLD = "import json\nimport os\nimport shutil\n"
IMPORT_NEW = "import gzip\nimport json\nimport os\nimport shutil\n"

LOOKUP_OLD = '''                for crystal_root in (self.crystal_dir, self.overflow_crystal_dir):\n                    candidate = crystal_root / f"{cid}.json"\n                    if candidate.exists():\n                        path = candidate\n                        break\n'''
LOOKUP_NEW = '''                for crystal_root in (self.crystal_dir, self.overflow_crystal_dir):\n                    candidate = crystal_root / f"{cid}.json"\n                    if candidate.exists():\n                        path = candidate\n                        break\n                    candidate_gz = crystal_root / f"{cid}.json.gz"\n                    if candidate_gz.exists():\n                        path = candidate_gz\n                        break\n'''
READ_OLD = '''                if path is None:\n                    return\n                child = json.loads(path.read_text(encoding="utf-8"))\n'''
READ_NEW = '''                if path is None:\n                    return\n                # BRUTOMAGIQUE-GZIP-CRYSTALS-v1: legacy JSON and lossless gzip coexist.\n                if path.name.endswith(".json.gz"):\n                    with gzip.open(path, "rt", encoding="utf-8") as handle:\n                        child = json.load(handle)\n                else:\n                    child = json.loads(path.read_text(encoding="utf-8"))\n'''
WRITER_OLD = '''        path = crystal_dir / f"{crystal['CRYSTAL_ID']}.json"\n        path.write_text(json.dumps(crystal, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")\n'''
WRITER_NEW = '''        # BRUTOMAGIQUE-GZIP-CRYSTALS-v1: full crystals remain lossless but compressed on disk.\n        path = crystal_dir / f"{crystal['CRYSTAL_ID']}.json.gz"\n        temp = path.with_suffix(path.suffix + ".tmp")\n        with temp.open("wb") as raw_handle:\n            with gzip.GzipFile(fileobj=raw_handle, mode="wb", compresslevel=6, mtime=0) as gzip_handle:\n                gzip_handle.write(\n                    json.dumps(crystal, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8")\n                )\n        temp.replace(path)\n'''


def patch(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if MARKER in text:
        print(f"ALREADY_PATCHED={path}")
        return
    for label, needle in (("imports", IMPORT_OLD), ("lookup", LOOKUP_OLD), ("reader", READ_OLD), ("writer", WRITER_OLD)):
        if needle not in text:
            raise RuntimeError(f"expected {label} block not found; refusing blind patch")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = path.with_name(path.name + f".gzipfix-{stamp}.bak")
    shutil.copy2(path, backup)
    text = text.replace(IMPORT_OLD, IMPORT_NEW, 1)
    text = text.replace(LOOKUP_OLD, LOOKUP_NEW, 1)
    text = text.replace(READ_OLD, READ_NEW, 1)
    text = text.replace(WRITER_OLD, WRITER_NEW, 1)
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
