#!/usr/bin/env python3
import argparse
import asyncio
import json
import threading
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import websockets


STAGES = ["ENTREE", "TRIADE_A", "NONUPLE_A", "MATRICE_36", "NONUPLE_B", "TRIADE_B", "SORTIE"]
COUNTS = [1, 3, 9, 36, 9, 3, 1]

FAKE_AUDIO_LOCK = threading.Lock()
FAKE_AUDIO_BASELINE_SEEN = threading.Event()
FAKE_AUDIO_SEQUENCE = 40
FAKE_AUDIO_EVENTS: list[dict] = []


class FakeGamezelAudioHandler(BaseHTTPRequestHandler):
    def log_message(self, _format: str, *_args: object) -> None:
        return

    def _send_json(self, payload: dict) -> None:
        raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/public/audio/state":
            FAKE_AUDIO_BASELINE_SEEN.set()
            with FAKE_AUDIO_LOCK:
                sequence = FAKE_AUDIO_SEQUENCE
            self._send_json({
                "mode": "PUBLIC_SAFE",
                "read_only": True,
                "sequence": sequence,
            })
            return

        if parsed.path == "/api/public/audio/events":
            query = urllib.parse.parse_qs(parsed.query)
            try:
                since = int(query.get("sinceSequence", ["0"])[0])
            except (TypeError, ValueError):
                since = 0
            with FAKE_AUDIO_LOCK:
                events = [dict(cue) for cue in FAKE_AUDIO_EVENTS if int(cue["SEQUENCE"]) > since]
                sequence = FAKE_AUDIO_SEQUENCE
            self._send_json({
                "mode": "PUBLIC_SAFE",
                "read_only": True,
                "sequence": sequence,
                "count": len(events),
                "events": events,
            })
            return

        self.send_error(404)


def start_fake_gamezel_audio_runtime(port: int = 9321) -> tuple[ThreadingHTTPServer, threading.Thread]:
    global FAKE_AUDIO_SEQUENCE
    with FAKE_AUDIO_LOCK:
        FAKE_AUDIO_SEQUENCE = 40
        FAKE_AUDIO_EVENTS.clear()
    FAKE_AUDIO_BASELINE_SEEN.clear()
    server = ThreadingHTTPServer(("127.0.0.1", port), FakeGamezelAudioHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


def publish_fake_audio_cue() -> dict:
    global FAKE_AUDIO_SEQUENCE
    cue = {
        "TYPE": "AUDIO_CUE",
        "EVENT_ID": "GZ-AUD-000041",
        "SEQUENCE": 41,
        "sequence": 41,
        "SOUND_ID": "SFX78",
        "FILE": "assets/sfx/gamezel/SFX078_ROUND_STARTED_L3.mp3",
        "PLAYER_ID": "P1",
        "PLAYER_NAME": "ASTRA",
        "AUDIO_MASTER": "PANEL_1",
        "STARTED_AT": 1791228000041,
        "REPLAY": False,
    }
    with FAKE_AUDIO_LOCK:
        FAKE_AUDIO_SEQUENCE = 41
        FAKE_AUDIO_EVENTS.append(dict(cue))
    return cue


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


def public_draw(base: str, player_id: str = "P1") -> dict:
    req = urllib.request.Request(
        base.rstrip("/") + "/api/gamezel/draw",
        data=json.dumps({"player_id": player_id}).encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=5) as response:
        result = json.loads(response.read().decode("utf-8"))
    if result.get("ok") is not True:
        raise AssertionError(f"GAMEZEL public draw failed: {result}")
    return result


async def run(base: str, ws_url: str, token: str) -> None:
    received = []
    audio_event = None
    draw_event = None
    draw_result = None
    fake_server, fake_thread = start_fake_gamezel_audio_runtime()
    try:
        async with websockets.connect(ws_url, open_timeout=5) as ws:
            if not await asyncio.to_thread(FAKE_AUDIO_BASELINE_SEEN.wait, 5):
                raise AssertionError("X72 did not baseline GAMEZEL audio sequence")

            for index in range(7):
                publish(base, token, index)

            while len(received) < 7:
                raw = await asyncio.wait_for(ws.recv(), timeout=5)
                message = json.loads(raw)
                if message.get("transport_replay") is True:
                    continue
                if message.get("type") == "GAMEZEL_AUDIO_CUE":
                    raise AssertionError(f"baseline audio was replayed unexpectedly: {message}")
                received.append(message)

            expected_audio_cue = publish_fake_audio_cue()
            while audio_event is None:
                raw = await asyncio.wait_for(ws.recv(), timeout=5)
                message = json.loads(raw)
                if message.get("type") == "GAMEZEL_AUDIO_CUE":
                    audio_event = message

            draw_result = public_draw(base, "P1")
            while draw_event is None:
                raw = await asyncio.wait_for(ws.recv(), timeout=5)
                message = json.loads(raw)
                if message.get("transport_replay") is True:
                    continue
                if message.get("type") == "GAMEZEL_PUBLIC_DRAW":
                    draw_event = message
    finally:
        fake_server.shutdown()
        fake_server.server_close()
        fake_thread.join(timeout=2)

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

    if not isinstance(audio_event, dict):
        raise AssertionError("missing GAMEZEL_AUDIO_CUE from X72 WebSocket relay")
    if audio_event.get("mode") != "PUBLIC_SAFE" or audio_event.get("read_only") is not True:
        raise AssertionError(f"unsafe GAMEZEL audio envelope: {audio_event}")
    cue = audio_event.get("cue") if isinstance(audio_event.get("cue"), dict) else {}
    if cue.get("EVENT_ID") != expected_audio_cue["EVENT_ID"] or cue.get("SEQUENCE") != 41:
        raise AssertionError(f"wrong GAMEZEL audio cue: {audio_event}")
    if cue.get("SOUND_ID") != "SFX78" or cue.get("FILE") != expected_audio_cue["FILE"]:
        raise AssertionError(f"wrong GAMEZEL audio payload: {audio_event}")

    if not isinstance(draw_result, dict) or not isinstance(draw_event, dict):
        raise AssertionError("missing GAMEZEL public draw result/event")
    if draw_result.get("execution") != "NONE" or draw_result.get("persisted") is not False:
        raise AssertionError(f"unsafe GAMEZEL draw result: {draw_result}")
    if draw_result.get("player_id") != "P1" or draw_result.get("audio_ref") != "SFX86":
        raise AssertionError(f"wrong ASTRA public draw identity: {draw_result}")
    if draw_event.get("player_id") != "P1" or draw_event.get("player_name") != "ASTRA":
        raise AssertionError(f"wrong ASTRA WebSocket event: {draw_event}")
    if draw_event.get("audio_ref") != "SFX86":
        raise AssertionError(f"wrong ASTRA audio ref: {draw_event}")
    if draw_event.get("transport_replay") is not False:
        raise AssertionError(f"live GAMEZEL draw marked as replay: {draw_event}")
    if draw_event.get("card", {}).get("card_id") != draw_result.get("card", {}).get("card_id"):
        raise AssertionError("GAMEZEL draw card mismatch between HTTP result and WebSocket event")
    draw_version = draw_event.get("transport_event_version")
    if not isinstance(draw_version, int) or draw_version <= versions[-1]:
        raise AssertionError(f"GAMEZEL draw transport version not monotonic: {draw_version}")

    print(
        "ZELSTEREOS_WS_ORDER=PASS "
        f"stages={indexes} channels={channels} versions={versions} "
        f"gamezel_draw_version={draw_version} gamezel_player=P1 "
        f"gamezel_audio_event={cue.get('EVENT_ID')} gamezel_audio_sequence={cue.get('SEQUENCE')}"
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
