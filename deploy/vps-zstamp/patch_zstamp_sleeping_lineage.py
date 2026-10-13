from __future__ import annotations

import hashlib
import sys
from pathlib import Path

EXPECTED_ORCH = "8f644bbfe8bdef4a9f5ebec66b1d540fa762c8ff8524f967e523967fd78b2662"
EXPECTED_SLEEP = "8618020e2bb773d640a08d7840140fd9cbd87707abb06a525ca1ac9327ca623d"
MARKER = "exact_z_lineage_preserved"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected 1 replacement, found {count}")
    return text.replace(old, new, 1)


def patch(root: Path) -> None:
    pkg = root / "src" / "brotoculateur"
    orch_path = pkg / "orchestrator.py"
    sleep_path = pkg / "sleeping_pool.py"
    if MARKER in sleep_path.read_text(encoding="utf-8"):
        print("ZSTAMP_SLEEPING_LINEAGE=ALREADY_APPLIED")
        print(f"ORCHESTRATOR_SHA256={sha(orch_path)}")
        print(f"SLEEPING_POOL_SHA256={sha(sleep_path)}")
        return
    if sha(orch_path) != EXPECTED_ORCH:
        raise RuntimeError(f"orchestrator hash drift: {sha(orch_path)} != {EXPECTED_ORCH}")
    if sha(sleep_path) != EXPECTED_SLEEP:
        raise RuntimeError(f"sleeping_pool hash drift: {sha(sleep_path)} != {EXPECTED_SLEEP}")

    orch = orch_path.read_text(encoding="utf-8")
    orch = replace_once(
        orch,
        '        digest = sha256(f"ZSTAMP-V1|{int(value)}".encode("utf-8")).digest()\n',
        '        digest = sha256(f"BRUTUS-Z-ROLLOUT-V1-28|{int(value)}".encode("utf-8")).digest()\n',
        "rollout salt",
    )
    orch = replace_once(
        orch,
        '            "rollout_percent": self.zstamp_percent,\n',
        '            "rollout_percent": self.zstamp_percent,\n            "rollout_law": "sha256(\'BRUTUS-Z-ROLLOUT-V1-28|\' + integer_value) % 100",\n',
        "rollout status",
    )
    orch_path.write_bytes(orch.replace("\r\n", "\n").encode("utf-8"))

    sleep = sleep_path.read_text(encoding="utf-8")
    sleep = replace_once(
        sleep,
        "class TraceToken(NamedTuple):\n    packet_id: bytes | str\n    parent_id: bytes | str | None\n    branch_bits: int | None\n",
        "class TraceToken(NamedTuple):\n    packet_id: bytes | str\n    parent_id: bytes | str | None\n    z_id: bytes | str | None\n    z_parent_id: bytes | str | None\n    z_origin_id: bytes | str | None\n    branch_bits: int | None\n",
        "trace token z fields",
    )
    sleep = replace_once(
        sleep,
        "def _unpack_hex_id(value: bytes | str | None) -> str | None:\n    if isinstance(value, bytes):\n        return value.hex()\n    return value\n\n\ndef _pack_branch_path",
        "def _unpack_hex_id(value: bytes | str | None) -> str | None:\n    if isinstance(value, bytes):\n        return value.hex()\n    return value\n\n\ndef _pack_z_id(value: str | None) -> bytes | str | None:\n    if value is None:\n        return None\n    if value.startswith('Z-') and len(value) == 34:\n        try:\n            return bytes.fromhex(value[2:])\n        except ValueError:\n            pass\n    return value\n\ndef _unpack_z_id(value: bytes | str | None) -> str | None:\n    if isinstance(value, bytes):\n        return 'Z-' + value.hex()\n    return value\n\n\ndef _pack_branch_path",
        "z pack helpers",
    )
    sleep = replace_once(
        sleep,
        "        self._packed_ids = 0\n        self._raw_ids = 0\n",
        "        self._packed_ids = 0\n        self._raw_ids = 0\n        self._packed_z_ids = 0\n        self._raw_z_ids = 0\n",
        "z stats init",
    )
    sleep = replace_once(
        sleep,
        "        packet_id = _pack_hex_id(packet.packet_id)\n        parent_id = _pack_hex_id(packet.parent_id)\n        self._packed_ids += int(isinstance(packet_id, bytes)) + int(isinstance(parent_id, bytes))\n        self._raw_ids += int(isinstance(packet_id, str)) + int(isinstance(parent_id, str))\n\n        branch_bits",
        "        packet_id = _pack_hex_id(packet.packet_id)\n        parent_id = _pack_hex_id(packet.parent_id)\n        z_id = _pack_z_id(packet.z_id)\n        z_parent_id = _pack_z_id(packet.z_parent_id)\n        z_origin_id = _pack_z_id(packet.z_origin_id)\n        self._packed_ids += int(isinstance(packet_id, bytes)) + int(isinstance(parent_id, bytes))\n        self._raw_ids += int(isinstance(packet_id, str)) + int(isinstance(parent_id, str))\n        self._packed_z_ids += sum(isinstance(v, bytes) for v in (z_id, z_parent_id, z_origin_id))\n        self._raw_z_ids += sum(isinstance(v, str) for v in (z_id, z_parent_id, z_origin_id))\n\n        branch_bits",
        "pack z ids",
    )
    sleep = replace_once(
        sleep,
        "            TraceToken(packet_id, parent_id, branch_bits, branch_len, branch_raw, float(priority))\n",
        "            TraceToken(packet_id, parent_id, z_id, z_parent_id, z_origin_id, branch_bits, branch_len, branch_raw, float(priority))\n",
        "store z ids",
    )
    sleep = replace_once(
        sleep,
        "                    parent_id=_unpack_hex_id(token.parent_id),\n                    branch_path=_unpack_branch_path(token.branch_bits, token.branch_len, token.branch_raw),\n",
        "                    parent_id=_unpack_hex_id(token.parent_id),\n                    branch_path=_unpack_branch_path(token.branch_bits, token.branch_len, token.branch_raw),\n                    z_id=_unpack_z_id(token.z_id),\n                    z_parent_id=_unpack_z_id(token.z_parent_id),\n                    z_origin_id=_unpack_z_id(token.z_origin_id),\n",
        "restore z ids",
    )
    sleep = replace_once(
        sleep,
        "            'raw_ids': self._raw_ids,\n            'exact_packet_identity_preserved': True,\n",
        "            'raw_ids': self._raw_ids,\n            'packed_z_ids': self._packed_z_ids,\n            'raw_z_ids': self._raw_z_ids,\n            'exact_z_lineage_preserved': True,\n            'exact_packet_identity_preserved': True,\n",
        "z status",
    )
    sleep_path.write_bytes(sleep.replace("\r\n", "\n").encode("utf-8"))

    print("ZSTAMP_SLEEPING_LINEAGE=PASS")
    print(f"ORCHESTRATOR_SHA256={sha(orch_path)}")
    print(f"SLEEPING_POOL_SHA256={sha(sleep_path)}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: patch_zstamp_sleeping_lineage.py <brotoculateur-root>")
    patch(Path(sys.argv[1]).resolve())
