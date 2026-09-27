#!/usr/bin/env python3
import argparse
import asyncio
import json
import urllib.request

import websockets


STAGES = ["ENTREE", "TRIADE_A", "NONUPLE_A", "MATRICE_36", "NONUPLE_B", "TRIADE_B", "SORTIE"]
COUNTS = [1, 3, 9, 36, 9, 3, 1]


def publish(base: str, token: str, index: int) -> dict:
    payload = {
        "mode": "PUBLIC_SAFE",
        "read_only": True,
        "status": "LIVE",
        "stage_index": index,
        "stage": STAGES[index],
        "channels": COUNTS[index],
        "trace_points": index + 1,
        "trace_total": 62,
        "stage_exec_us": 100.0 + index,
        "stage_work_ratio": round(index / 6, 6),
        "public_values": [],
        "public_values_total": COUNTS[index],
        "global_error": {"exact": "0", "decimal": 0.0},
        "f1": {
            "formula_id": "F1",
            "k": 3,
            "value": "1764",
            "formula": "z_P(21^k)=4*21^(k-1)",
            "source_commit_short": "runner-test",
        },
        "events": [],
        "event_seq": index + 1,
    }
    req = urllib.request.Request(
        base.rstrip("/") + "/api/zelstereos/ingest",
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        },
    )
    with urllib.request.urlopen(req, timeout=5) as response:
        result = json.loads(response.read().decode("utf-8"))
    if result.get("ok") is not True:
        raise AssertionError(f"ingest failed at stage {index}: {result}")
    return result


async def run(base: str, ws_url: str, token: str) -> None:
    received = []
    async with websockets.connect(ws_url, open_timeout=5) as ws:
        for index in range(7):
            publish(base, token, index)

        while len(received) < 7:
            raw = await asyncio.wait_for(ws.recv(), timeout=5)
            message = json.loads(raw)
            if message.get("transport_replay") is True:
                continue
            received.append(message)

    indexes = [item.get("stage_index") for item in received]
    if indexes != list(range(7)):
        raise AssertionError(f"stage order mismatch: {indexes}")

    versions = [item.get("transport_event_version") for item in received]
    if not all(isinstance(v, int) for v in versions):
        raise AssertionError(f"missing integer transport versions: {versions}")
    if versions != sorted(versions) or len(set(versions)) != 7:
        raise AssertionError(f"transport versions not strictly ordered: {versions}")

    channels = [item.get("channels") for item in received]
    if channels != COUNTS:
        raise AssertionError(f"channel sequence mismatch: {channels}")

    for index, item in enumerate(received):
        if item.get("transport_replay") is not False:
            raise AssertionError(f"live event marked as replay at stage {index}")
        if float(item.get("stage_exec_us", -1)) != 100.0 + index:
            raise AssertionError(f"stage_exec_us mismatch at stage {index}: {item}")
        expected_ratio = round(index / 6, 6)
        if float(item.get("stage_work_ratio", -1)) != expected_ratio:
            raise AssertionError(f"stage_work_ratio mismatch at stage {index}: {item}")

    print(
        "ZELSTEREOS_WS_ORDER=PASS "
        f"stages={indexes} channels={channels} versions={versions}"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1:8720")
    parser.add_argument("--ws", default="ws://127.0.0.1:8720/ws?channel=zelstereos")
    parser.add_argument("--token", required=True)
    args = parser.parse_args()
    asyncio.run(run(args.base, args.ws, args.token))


if __name__ == "__main__":
    main()
