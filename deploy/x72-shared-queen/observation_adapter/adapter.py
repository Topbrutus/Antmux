from __future__ import annotations

import asyncio
import hashlib
import json
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, AsyncIterator, Callable, Iterable
from urllib.parse import urlparse, urlunparse

import websockets


QUEEN_SOURCE = "QUEEN_SERVER_V0_2"
OBSERVABILITY_SCHEMA = "ANTMUX-X72-OBSERVABILITY-v1"
OBSERVATION_REPORT_SCHEMA = "ANTMUX-X72-OBSERVATION-REPORT-v1"


@dataclass(frozen=True)
class ObservationEnvelope:
    observed_at_utc: str
    entity_id: str | None
    source_schema: str
    source_endpoint: str
    freshness_ms: int
    status: str
    condition: str
    payload: dict[str, Any] | None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _payload_h256(payload: dict[str, Any] | None) -> str | None:
    if payload is None:
        return None
    return hashlib.sha256(_canonical_json(payload)).hexdigest()


def deterministic_report(records: Iterable[ObservationEnvelope]) -> dict[str, Any]:
    stable_records: list[dict[str, Any]] = []
    entity_ids: set[str] = set()

    for record in records:
        if record.entity_id:
            entity_ids.add(record.entity_id)
        stable_records.append(
            {
                "entity_id": record.entity_id,
                "source_schema": record.source_schema,
                "source_endpoint": record.source_endpoint,
                "status": record.status,
                "condition": record.condition,
                "payload_h256": _payload_h256(record.payload),
            }
        )

    stable_records.sort(
        key=lambda item: (
            str(item["entity_id"]),
            str(item["source_schema"]),
            str(item["source_endpoint"]),
            str(item["status"]),
            str(item["condition"]),
            str(item["payload_h256"]),
        )
    )
    body = {
        "schema": OBSERVATION_REPORT_SCHEMA,
        "entity_ids": sorted(entity_ids),
        "record_count": len(stable_records),
        "records": stable_records,
    }
    return {
        **body,
        "report_h256": hashlib.sha256(_canonical_json(body)).hexdigest(),
    }


class X72ObservationAdapter:
    def __init__(
        self,
        base_url: str,
        *,
        timeout_seconds: float = 3.0,
        reconnect_delay_seconds: float = 0.2,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.reconnect_delay_seconds = reconnect_delay_seconds
        self.ws_url = self._derive_ws_url(self.base_url)
        self._entity_id: str | None = None

    @staticmethod
    def _derive_ws_url(base_url: str) -> str:
        parsed = urlparse(base_url)
        scheme = "wss" if parsed.scheme == "https" else "ws"
        path = parsed.path.rstrip("/") + "/ws"
        return urlunparse((scheme, parsed.netloc, path, "", "", ""))

    def _endpoint_url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def _validate_entity(self, entity_id: str | None) -> str:
        if not entity_id:
            raise ValueError("missing entity_id")
        normalized = str(entity_id)
        if self._entity_id is not None and self._entity_id != normalized:
            raise ValueError(
                f"entity_id changed from {self._entity_id} to {normalized}"
            )
        return normalized

    def _remember_entity(self, entity_id: str | None) -> None:
        normalized = self._validate_entity(entity_id)
        if self._entity_id is None:
            self._entity_id = normalized

    def _fresh(
        self,
        *,
        endpoint: str,
        schema: str,
        payload: dict[str, Any],
        started: float,
        condition: str = "OK",
    ) -> ObservationEnvelope:
        entity_id = payload.get("entity_id")
        if entity_id:
            self._remember_entity(str(entity_id))
        return ObservationEnvelope(
            observed_at_utc=_utc_now(),
            entity_id=self._entity_id,
            source_schema=schema,
            source_endpoint=endpoint,
            freshness_ms=max(0, round((time.monotonic() - started) * 1000)),
            status="FRESH",
            condition=condition,
            payload=payload,
            error=None,
        )

    def _failure(
        self,
        *,
        endpoint: str,
        schema: str,
        condition: str,
        error: str,
        payload: dict[str, Any] | None = None,
        status: str = "UNKNOWN",
        freshness_ms: int = 0,
    ) -> ObservationEnvelope:
        return ObservationEnvelope(
            observed_at_utc=_utc_now(),
            entity_id=self._entity_id,
            source_schema=schema,
            source_endpoint=endpoint,
            freshness_ms=max(0, freshness_ms),
            status=status,
            condition=condition,
            payload=payload,
            error=error,
        )

    def _request_json(self, path: str) -> tuple[str, dict[str, Any] | None, str | None]:
        request = urllib.request.Request(
            self._endpoint_url(path),
            method="GET",
            headers={"Accept": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                raw_bytes = response.read()
        except urllib.error.HTTPError as exc:
            return "HTTP_ERROR", None, f"HTTP {exc.code}"
        except urllib.error.URLError as exc:
            return "HTTP_CONNECT_ERROR", None, str(exc.reason)
        except TimeoutError as exc:
            return "HTTP_TIMEOUT", None, str(exc)
        except OSError as exc:
            return "HTTP_IO_ERROR", None, str(exc)

        try:
            raw = raw_bytes.decode("utf-8")
            payload = json.loads(raw)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            return "INVALID_JSON", None, str(exc)

        if not isinstance(payload, dict):
            return "SCHEMA_MISMATCH", None, "top-level JSON must be an object"
        return "OK", payload, None

    def _read_validated(
        self,
        *,
        endpoint: str,
        schema: str,
        validator: Callable[[dict[str, Any]], None],
    ) -> ObservationEnvelope:
        started = time.monotonic()
        condition, payload, error = self._request_json(endpoint)
        if condition != "OK" or payload is None:
            return self._failure(
                endpoint=endpoint,
                schema=schema,
                condition=condition,
                error=error or condition,
            )
        try:
            validator(payload)
            return self._fresh(
                endpoint=endpoint,
                schema=schema,
                payload=payload,
                started=started,
            )
        except Exception as exc:
            return self._failure(
                endpoint=endpoint,
                schema=schema,
                condition="SCHEMA_MISMATCH",
                error=str(exc),
                payload=payload,
            )

    def read_health(self) -> ObservationEnvelope:
        def validate(payload: dict[str, Any]) -> None:
            if payload.get("ok") is not True:
                raise ValueError("health ok is not true")
            if payload.get("source") != QUEEN_SOURCE:
                raise ValueError("unexpected health source")
            self._validate_entity(payload.get("entity_id"))

        return self._read_validated(
            endpoint="/api/health",
            schema=f"{QUEEN_SOURCE}/health",
            validator=validate,
        )

    def read_telemetry(self) -> ObservationEnvelope:
        def validate(payload: dict[str, Any]) -> None:
            if payload.get("schema") != OBSERVABILITY_SCHEMA:
                raise ValueError("unexpected observability schema")
            if payload.get("authority") != QUEEN_SOURCE:
                raise ValueError("unexpected observability authority")
            if payload.get("scope") != "operational_read_only":
                raise ValueError("unexpected observability scope")
            self._validate_entity(payload.get("entity_id"))

        return self._read_validated(
            endpoint="/api/telemetry",
            schema=OBSERVABILITY_SCHEMA,
            validator=validate,
        )

    def read_state(self) -> ObservationEnvelope:
        def validate(payload: dict[str, Any]) -> None:
            if payload.get("source") != QUEEN_SOURCE:
                raise ValueError("unexpected state source")
            self._validate_entity(payload.get("entity_id"))
            if "tick_count" not in payload:
                raise ValueError("missing tick_count")
            if "reference_h256" not in payload:
                raise ValueError("missing reference_h256")

        return self._read_validated(
            endpoint="/api/state",
            schema=QUEEN_SOURCE,
            validator=validate,
        )

    def read_events(self) -> ObservationEnvelope:
        def validate(payload: dict[str, Any]) -> None:
            events = payload.get("events")
            if not isinstance(events, list):
                raise ValueError("events must be a list")
            event_entities = {
                str(event.get("entity_id"))
                for event in events
                if isinstance(event, dict) and event.get("entity_id")
            }
            if len(event_entities) > 1:
                raise ValueError("event window contains multiple entity_id values")
            if event_entities:
                self._remember_entity(next(iter(event_entities)))
            elif self._entity_id is None:
                raise ValueError("cannot correlate empty event window without entity_id")

        return self._read_validated(
            endpoint="/api/events",
            schema=f"{QUEEN_SOURCE}/events",
            validator=validate,
        )

    def read_report(self) -> ObservationEnvelope:
        if self._entity_id is None:
            health = self.read_health()
            if health.status != "FRESH":
                return self._failure(
                    endpoint="/api/report",
                    schema=f"{QUEEN_SOURCE}/repair-report",
                    condition="IDENTITY_UNAVAILABLE",
                    error="cannot correlate report without Queen identity",
                )

        def validate(payload: dict[str, Any]) -> None:
            if "verdict" not in payload:
                raise ValueError("missing verdict")
            if "reference_protected_h256" not in payload:
                raise ValueError("missing reference_protected_h256")

        return self._read_validated(
            endpoint="/api/report",
            schema=f"{QUEEN_SOURCE}/repair-report",
            validator=validate,
        )

    async def stream_state(self) -> AsyncIterator[ObservationEnvelope]:
        last_payload: dict[str, Any] | None = None
        last_real_monotonic: float | None = None
        disconnected_emitted = False
        has_connected_once = False

        while True:
            try:
                async with websockets.connect(
                    self.ws_url,
                    open_timeout=self.timeout_seconds,
                    close_timeout=1,
                ) as websocket:
                    reconnect = has_connected_once
                    has_connected_once = True
                    disconnected_emitted = False

                    async for raw in websocket:
                        started = time.monotonic()
                        try:
                            payload = json.loads(raw)
                            if not isinstance(payload, dict):
                                raise ValueError("top-level WebSocket JSON must be an object")
                            if payload.get("source") != QUEEN_SOURCE:
                                raise ValueError("unexpected WebSocket state source")
                            self._validate_entity(payload.get("entity_id"))
                            if "tick_count" not in payload or "reference_h256" not in payload:
                                raise ValueError("incomplete WebSocket VisualState")
                        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                            yield self._failure(
                                endpoint="/ws",
                                schema=QUEEN_SOURCE,
                                condition="WEBSOCKET_INVALID_JSON",
                                error=str(exc),
                                payload=last_payload,
                                status="STALE" if last_payload is not None else "UNKNOWN",
                                freshness_ms=0
                                if last_real_monotonic is None
                                else round((time.monotonic() - last_real_monotonic) * 1000),
                            )
                            continue
                        except Exception as exc:
                            yield self._failure(
                                endpoint="/ws",
                                schema=QUEEN_SOURCE,
                                condition="WEBSOCKET_SCHEMA_MISMATCH",
                                error=str(exc),
                                payload=last_payload,
                                status="STALE" if last_payload is not None else "UNKNOWN",
                                freshness_ms=0
                                if last_real_monotonic is None
                                else round((time.monotonic() - last_real_monotonic) * 1000),
                            )
                            continue

                        last_payload = payload
                        last_real_monotonic = time.monotonic()
                        yield self._fresh(
                            endpoint="/ws",
                            schema=QUEEN_SOURCE,
                            payload=payload,
                            started=started,
                            condition="RECONNECTED" if reconnect else "STREAM_STATE",
                        )
                        reconnect = False

                    if not disconnected_emitted:
                        disconnected_emitted = True
                        freshness_ms = 0
                        if last_real_monotonic is not None:
                            freshness_ms = round(
                                (time.monotonic() - last_real_monotonic) * 1000
                            )
                        yield self._failure(
                            endpoint="/ws",
                            schema=QUEEN_SOURCE,
                            condition="WEBSOCKET_DISCONNECT",
                            error="normal WebSocket close",
                            payload=last_payload,
                            status="STALE" if last_payload is not None else "UNKNOWN",
                            freshness_ms=freshness_ms,
                        )
                    await asyncio.sleep(self.reconnect_delay_seconds)

            except asyncio.CancelledError:
                raise
            except Exception as exc:
                if not disconnected_emitted:
                    disconnected_emitted = True
                    freshness_ms = 0
                    if last_real_monotonic is not None:
                        freshness_ms = round(
                            (time.monotonic() - last_real_monotonic) * 1000
                        )
                    yield self._failure(
                        endpoint="/ws",
                        schema=QUEEN_SOURCE,
                        condition=(
                            "WEBSOCKET_DISCONNECT"
                            if last_payload is not None
                            else "WEBSOCKET_CONNECT_ERROR"
                        ),
                        error=type(exc).__name__,
                        payload=last_payload,
                        status="STALE" if last_payload is not None else "UNKNOWN",
                        freshness_ms=freshness_ms,
                    )
                await asyncio.sleep(self.reconnect_delay_seconds)
