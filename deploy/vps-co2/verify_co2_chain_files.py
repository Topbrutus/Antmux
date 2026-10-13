from __future__ import annotations

import json
import sys
from pathlib import Path

from co2_proof_chain import verify_chain_files


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: verify_co2_chain_files.py <co1-archive.jsonl> <co2-chain.jsonl>")
    archive = Path(sys.argv[1]).expanduser()
    chain = Path(sys.argv[2]).expanduser()
    result = verify_chain_files(archive, chain)
    print("CO2_FILE_VERIFY=" + json.dumps(result, sort_keys=True, separators=(",", ":")))
    if result["missing_links"] != 0:
        raise SystemExit(2)
    if result["archive_records"] != result["chain_links"]:
        raise SystemExit(3)
    print("CO2_FILE_VERIFY=PASS")


if __name__ == "__main__":
    main()
