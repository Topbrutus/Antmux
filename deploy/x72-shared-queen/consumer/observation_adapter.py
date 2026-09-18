from __future__ import annotations

import asyncio
import hashlib
import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, AsyncIterator, Iterable

AUTHORITY = "QUEEN_SERVER_V0_2"
OBSERVABILITY_SCHEMA = "ANTMUX-X72-OBSERVABILITY-v1"


class ObservationError(RuntimeError):
    """Base error for read-only X72 observation failures."""


class TransportError(ObservationError):
    """HTTP/WebSocket transport failed."""


class InvalidJSON(ObservationError):
    """A source returned non-JSON or non-object JSON."""


class SchemaMismatch(ObservationError):
    """A payload did not match the expected authority/schema/entity."""


@dataclass(frozen=True)
class ObservationEnvelope:
    observed_at_utc: str
    entity_id: str
    source_schema: str
    source_endpoint: str
    freshness_ms: int
    status: str
    payload: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "observed_at_utc": self.observed_at_utc,
            "entity_id": self.entity_id,
            "source_schema": self.source_schema,
            "source_endpoint": self.source_endpoint,
            "freshness_ms": self.freshness_ms,
            "status": self.status,
            "payload": self.payload,
        }


class X72ObservationAdapter:
    """Read-only consumer for the authoritative shared X72 Queen.

    This adapter never calls mutation endpoints and never synthesizes Queen values.
    Unknown additive fields are preserved in the original payload.
    """

    def __init__(
        self,
        base_url: str,
        ws_url: str | None = None,
        *,
        timeout: float = 5.0,
        reconnect_delay: float = 0.1,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.ws_url = ws_url or self._derive_ws_url(self.base_url)
        self.timeout = float(timeout)
        self.reconnect_delay = float(reconnect_delay)
        self._entity_id: str | None = None

    @staticmethod
    def _derive_ws_url(base_url: str) -> str:
        if base_url.startswith("https://"):
            return "wss://" + base_url[len("https://") :] + "/ws"
        if base_url.startswith("http://"):
            return "ws://" + base_url[len("http://") :] + "/ws"
        raise ValueError("base_url must start with http:// or https://")

    @staticmethod
    def _utc_now() -> str:
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    def _bind_entity(self, entity_id: Any, endpoint: str) -> str:
        if not isinstance(entity_id, str) or not entity_id:
            raise SchemaMismatch(f"{endpoint}: missing/invalid entity_id")
        if self._entity_id is None:
            self._entity_id = entity_id
        elif entity_id != self._entity_id:
            raise SchemaMismatch(
                f"{endpoint}: entity_id changed from {self._entity_id} to {entity_id}"
            )
        return entity_id

    def _request_json(self, path: str) -> dict[str, Any]:
        url = self.base_url + path
        request = urllib.request.Request(
            url,
            method="GET",
            headers={"Accept": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                raw = response.read()
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
            raise TransportError(f"GET {path} failed: {exc}") from exc

        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise InvalidJSON(f"GET {path} returned invalid JSON") from exc
        if not isinstance(payload, dict):
            raise InvalidJSON(f"GET {path} returned non-object JSON")
        return payload

    def _envelope(
        self,
        payload: dict[str, Any],
        endpoint: str,
        source_schema: str,
        entity_id: str,
    ) -> ObservationEnvelope:
        return ObservationEnvelope(
            observed_at_utc=self._utc_now(),
            entity_id=entity_id,
            source_schema=source_schema,
            source_endpoint=endpoint,
            freshness_ms=0,
            status="FRESH",
            payload=dict(payload),
        )

    def read_health(self) -> ObservationEnvelope:
        payload = self._request_json("/api/health")
        if payload.get("ok") is not True or payload.get("source") != AUTHORITY:
            raise SchemaMismatch("/api/health: authority/liveness mismatch")
        entity_id = self._bind_entity(payload.get("entity_id"), "/api/health")
        return self._envelope(payload, "/api/health", AUTHORITY, entity_id)

    def read_telemetry(self) -> ObservationEnvelope:
        payload = self._request_json("/api/telemetry")
        if (
            payload.get("schema") != OBSERVABILITY_SCHEMA
            or payload.get("authority") != AUTHORITY
            or payload.get("scope") != "operational_read_only"
        ):
            raise SchemaMismatch("/api/telemetry: observability contract mismatch")
        entity_id = self._bind_entity(payload.get("entity_id"), "/api/telemetry")
        return self._envelope(
            payload,
            "/api/telemetry",
            OBSERVABILITY_SCHEMA,
            entity_id,
        )

    def read_state(self) -> ObservationEnvelope:
        payload = self._request_json("/api/state")
        if payload.get("source") != AUTHORITY:
            raise SchemaMismatch("/api/state: authority mismatch")
        entity_id = self._bind_entity(payload.get("entity_id"), "/api/state")
        return self._envelope(payload, "/api/state", AUTHORITY, entity_id)

    def _ensure_entity(self) -> str:
        if self._entity_id is None:
            self.read_health()
        assert self._entity_id is not None
        return self._entity_id

    def read_events(self) -> ObservationEnvelope:
        entity_id = self._ensure_entity()
        payload = self._request_json("/api/events")
        events = payload.get("events")
        if not isinstance(events, list):
            raise SchemaMismatch("/api/events: events must be a list")
        mismatches = [
            event.get("entity_id")
            for event in events
            if isinstance(event, dict)
            and event.get("entity_id") not in (None, entity_id)
        ]
        if mismatches:
            raise SchemaMismatch("/api/events: event entity_id mismatch")
        return self._envelope(payload, "/api/events", AUTHORITY, entity_id)

    def read_report(self) -> ObservationEnvelope:
        entity_id = self._ensure_entity()
        payload = self._request_json("/api/report")
        if not isinstance(payload.get("verdict"), str):
            raise SchemaMismatch("/api/report: missing verdict")
        return self._envelope(payload, "/api/report", AUTHORITY, entity_id)

    async def stream_state(
        self,
        *,
        max_messages: int | None = None,
        reconnect: bool = True,
        max_reconnects: int = 3,
    ) -> AsyncIterator[ObservationEnvelope]:
        if max_messages is not None and max_messages <= 0:
            return
        if max_reconnects < 0:
            raise ValueError("max_reconnects must be >= 0")

        try:
            import websockets
        except ImportError as exc:
            raise TransportError("websockets package is required for stream_state") from exc

        delivered = 0
        reconnects = 0
        last_error: Exception | None = None

        while True:
            try:
                async with websockets.connect(
                    self.ws_url,
                    open_timeout=self.timeout,
                    close_timeout=self.timeout,
                ) as websocket:
                    while True:
                        raw = await asyncio.wait_for(websocket.recv(), timeout=self.timeout)
                        try:
                            payload = json.loads(raw)
                        except json.JSONDecodeError as exc:
                            raise InvalidJSON("WebSocket returned invalid JSON") from exc
                        if not isinstance(payload, dict):
                            raise InvalidJSON("WebSocket returned non-object JSON")
                        if payload.get("source") != AUTHORITY:
                            raise SchemaMismatch("WebSocket authority mismatch")
                        entity_id = self._bind_entity(payload.get("entity_id"), "WS /ws")
                        yield self._envelope(payload, "WS /ws", AUTHORITY, entity_id)
                        delivered += 1
                        if max_messages is not None and delivered >= max_messages:
                            return
            except (InvalidJSON, SchemaMismatch):
                raise
            except Exception as exc:
                last_error = exc

            if not reconnect:
                raise TransportError(f"WebSocket disconnected: {last_error}") from last_error
            if reconnects >= max_reconnects:
                raise TransportError(
                    f"WebSocket reconnect budget exhausted after {reconnects} attempts: {last_error}"
                ) from last_error
            reconnects += 1
            await asyncio.sleep(self.reconnect_delay)


def deterministic_report(
    observations: Iterable[ObservationEnvelope],
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    entity_id: str | None = None
    for observation in observations:
        if entity_id is None:
            entity_id = observation.entity_id
        elif observation.entity_id != entity_id:
            raise SchemaMismatch("deterministic_report: mixed entity_id values")
        canonical_payload = json.dumps(
            observation.payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
        rows.append(
            {
                "source_endpoint": observation.source_endpoint,
                "source_schema": observation.source_schema,
                "status": observation.status,
                "payload_h256": hashlib.sha256(canonical_payload).hexdigest(),
            }
        )

    rows.sort(key=lambda row: (row["source_endpoint"], row["source_schema"], row["payload_h256"]))
    core = {
        "schema": "ANTMUX-X72-OBSERVATION-REPORT-v1",
        "entity_id": entity_id or "",
        "records": rows,
    }
    canonical_core = json.dumps(
        core,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return {
        **core,
        "report_h256": hashlib.sha256(canonical_core).hexdigest(),
    }
