from __future__ import annotations

import cmath
import json
import math
import time
from dataclasses import asdict, dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any, Iterable

SCHEMA = "ANTMUX-X72-RESONANCE-STRUCTURE-v0.1"
MEASUREMENT_SCHEMA = "ANTMUX-X72-RESONANCE-MEASUREMENT-v0.1"
ROUTE_SCHEMA = "ANTMUX-X72-BRUTUS-ROUTE-A-v0.1"
CHANNELS = ("REF", "C1", "C2", "C3", "C4", "C5", "C6", "C7")
ZONES = CHANNELS[1:]

SEVEN_POW_FOUR = 7**4
LCM_3_7_13 = math.lcm(3, 7, 13)
THIRTEEN_SEVEN_SEVEN = 13 * 7 * 7
FOUNDATION_NUMBER = 3 * (6 + 1) * 7 * 7 * 9 * 10 * 13
ACTIVITY_MEAN_EXACT = Fraction(2852, 1000) / 7


def research_constants() -> dict[str, Any]:
    return {
        "seven_pow_four": {"value": SEVEN_POW_FOUR, "authority": "CALCULATED"},
        "lcm_3_7_13": {"value": LCM_3_7_13, "authority": "CALCULATED"},
        "thirteen_times_seven_times_seven": {
            "value": THIRTEEN_SEVEN_SEVEN,
            "authority": "CALCULATED",
        },
        "foundation_number": {"value": FOUNDATION_NUMBER, "authority": "CALCULATED"},
        "activity_mean_2_852_over_7": {
            "fraction": f"{ACTIVITY_MEAN_EXACT.numerator}/{ACTIVITY_MEAN_EXACT.denominator}",
            "value": float(ACTIVITY_MEAN_EXACT),
            "authority": "CALCULATED",
        },
        "residue_formula": {
            "expression": "(91*t + 39*b + 21*o) mod 273",
            "authority": "CALCULATED",
        },
        "theta_formula": {
            "expression": "2*pi*R/273",
            "authority": "CALCULATED",
        },
        "usage": "REFERENCE_ONLY_DO_NOT_FORCE",
    }


def brutus_residue(t: int, b: int, o: int) -> int:
    return (91 * int(t) + 39 * int(b) + 21 * int(o)) % 273


def brutus_theta(t: int, b: int, o: int) -> float:
    return 2.0 * math.pi * brutus_residue(t, b, o) / 273.0


ROUTE_A_NODES = (
    "BOTTOM",
    "MAUVE_A1",
    "YELLOW",
    "RED_1",
    "GREEN_1",
    "GROUND_ECHO",
    "A2",
    "RED_2",
    "BLUE",
    "C3",
    "YELLOW_RETURN",
    "MAUVE_RETURN",
    "BOTTOM_RETURN",
)

ROUTE_A_EDGES = (
    ("BOTTOM", "MAUVE_A1"),
    ("MAUVE_A1", "YELLOW"),
    ("MAUVE_A1", "RED_1"),
    ("MAUVE_A1", "GREEN_1"),
    ("MAUVE_A1", "GROUND_ECHO"),
    ("RED_1", "GREEN_1"),
    ("GREEN_1", "A2"),
    ("RED_1", "RED_2"),
    ("RED_2", "BLUE"),
    ("BLUE", "C3"),
    ("C3", "YELLOW_RETURN"),
    ("C3", "MAUVE_RETURN"),
    ("C3", "BOTTOM_RETURN"),
    ("YELLOW_RETURN", "BOTTOM"),
    ("MAUVE_RETURN", "MAUVE_A1"),
    ("BOTTOM_RETURN", "BOTTOM"),
    ("GROUND_ECHO", "MAUVE_A1"),
)


def route_a_payload() -> dict[str, Any]:
    return {
        "schema": ROUTE_SCHEMA,
        "status": "HYPOTHESIS",
        "physical_claim": False,
        "first_accumulation": "MAUVE_A1",
        "second_accumulation": "A2",
        "third_accumulation": "C3",
        "mirror_pair": ["RED_1", "GREEN_1"],
        "mirror_orientation": ["FORWARD", "REVERSED"],
        "nodes": list(ROUTE_A_NODES),
        "edges": [list(edge) for edge in ROUTE_A_EDGES],
        "descent_targets": ["YELLOW_RETURN", "MAUVE_RETURN", "BOTTOM_RETURN"],
        "ground_echo": "GROUND_ECHO",
        "notes": (
            "Route A follows the current Brutus test order. "
            "Node names are software labels, not physical or biological claims."
        ),
    }


@dataclass(frozen=True)
class ResonanceConfig:
    sample_rate_hz: float = 240.0
    breathing_hz: float = 0.1
    carrier_hz: float = 7.0
    phase_step_rad: float = math.pi / 7.0
    max_delay_seconds: float = 0.25

    def validate(self) -> None:
        if not math.isfinite(self.sample_rate_hz) or self.sample_rate_hz <= 0:
            raise ValueError("sample_rate_hz must be finite and > 0")
        if not math.isfinite(self.breathing_hz) or self.breathing_hz <= 0:
            raise ValueError("breathing_hz must be finite and > 0")
        if not math.isfinite(self.carrier_hz) or self.carrier_hz <= 0:
            raise ValueError("carrier_hz must be finite and > 0")
        if self.carrier_hz >= self.sample_rate_hz / 2:
            raise ValueError("carrier_hz must be below Nyquist")
        if not math.isfinite(self.phase_step_rad):
            raise ValueError("phase_step_rad must be finite")
        if not math.isfinite(self.max_delay_seconds) or self.max_delay_seconds < 0:
            raise ValueError("max_delay_seconds must be finite and >= 0")


@dataclass
class ChannelMeasurement:
    channel: str
    amplitude_rms: float
    peak_amplitude: float
    dominant_frequency_hz: float | None
    gain: float | None
    delay_seconds: float | None
    phase_delta_rad: float | None
    coherence: float | None
    bandwidth_low_hz: float | None
    bandwidth_high_hz: float | None
    bandwidth_hz: float | None
    authority: str = "CALCULATED"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RouteSensor:
    node: str
    count: int = 0
    sum_value: float = 0.0
    sum_sq: float = 0.0
    peak_abs: float = 0.0
    last_value: float = 0.0

    def add(self, value: float) -> None:
        v = float(value)
        if not math.isfinite(v):
            raise ValueError("route sensor value must be finite")
        self.count += 1
        self.sum_value += v
        self.sum_sq += v * v
        self.peak_abs = max(self.peak_abs, abs(v))
        self.last_value = v

    @property
    def mean(self) -> float:
        return self.sum_value / self.count if self.count else 0.0

    @property
    def rms(self) -> float:
        return math.sqrt(self.sum_sq / self.count) if self.count else 0.0

    def payload(self) -> dict[str, Any]:
        return {
            "node": self.node,
            "count": self.count,
            "mean": self.mean,
            "rms": self.rms,
            "peak_abs": self.peak_abs,
            "last_value": self.last_value,
            "authority": "MEASURED" if self.count else "NOT_RUN",
        }


class ExperimentJournal:
    def __init__(self, path: str | Path | None = None):
        self.path = Path(path) if path is not None else None
        self.records: list[dict[str, Any]] = []

    def append(self, record: dict[str, Any]) -> None:
        clone = json.loads(json.dumps(record, sort_keys=True, allow_nan=False))
        self.records.append(clone)
        if self.path is not None:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(clone, sort_keys=True, allow_nan=False) + "\n")


class SignalGenerator:
    def __init__(self, config: ResonanceConfig):
        config.validate()
        self.config = config

    def _times(self, samples: int) -> list[float]:
        if samples < 1:
            raise ValueError("samples must be >= 1")
        sr = self.config.sample_rate_hz
        return [i / sr for i in range(samples)]

    def breathing_envelope(self, samples: int, *, frequency_hz: float | None = None) -> list[float]:
        frequency_hz = self.config.breathing_hz if frequency_hz is None else float(frequency_hz)
        if frequency_hz <= 0:
            raise ValueError("frequency_hz must be > 0")
        return [
            (1.0 + math.sin(2.0 * math.pi * frequency_hz * t)) / 2.0
            for t in self._times(samples)
        ]

    def sine(
        self,
        samples: int,
        *,
        frequency_hz: float | None = None,
        amplitude: float = 1.0,
        phase_rad: float = 0.0,
        breathing: bool = False,
    ) -> list[float]:
        f = self.config.carrier_hz if frequency_hz is None else float(frequency_hz)
        if f <= 0 or f >= self.config.sample_rate_hz / 2:
            raise ValueError("frequency_hz must be inside (0, Nyquist)")
        env = self.breathing_envelope(samples) if breathing else [1.0] * samples
        return [
            float(amplitude) * env[i] * math.sin(2.0 * math.pi * f * t + phase_rad)
            for i, t in enumerate(self._times(samples))
        ]

    def impulse(self, samples: int, *, index: int = 1, amplitude: float = 1.0) -> list[float]:
        if not 0 <= index < samples:
            raise ValueError("impulse index is outside sample range")
        out = [0.0] * samples
        out[index] = float(amplitude)
        return out

    def chirp(
        self,
        samples: int,
        *,
        start_hz: float = 1.0,
        end_hz: float = 40.0,
        amplitude: float = 1.0,
    ) -> list[float]:
        if not (0 < start_hz < end_hz < self.config.sample_rate_hz / 2):
            raise ValueError("chirp frequencies must satisfy 0 < start < end < Nyquist")
        duration = max((samples - 1) / self.config.sample_rate_hz, 1.0 / self.config.sample_rate_hz)
        k = (end_hz - start_hz) / duration
        out: list[float] = []
        for t in self._times(samples):
            phase = 2.0 * math.pi * (start_hz * t + 0.5 * k * t * t)
            out.append(float(amplitude) * math.sin(phase))
        return out


def _next_pow2(value: int) -> int:
    n = 1
    while n < value:
        n <<= 1
    return n


def _fft(values: list[complex]) -> list[complex]:
    n = len(values)
    if n == 0 or n & (n - 1):
        raise ValueError("FFT length must be a non-zero power of two")
    if n == 1:
        return [values[0]]
    even = _fft(values[0::2])
    odd = _fft(values[1::2])
    out = [0j] * n
    for k in range(n // 2):
        twiddle = cmath.exp(-2j * math.pi * k / n) * odd[k]
        out[k] = even[k] + twiddle
        out[k + n // 2] = even[k] - twiddle
    return out


def _normalize_phase(angle: float) -> float:
    return math.atan2(math.sin(angle), math.cos(angle))


class SignalAnalyzer:
    def __init__(self, sample_rate_hz: float, max_delay_seconds: float = 0.25):
        if sample_rate_hz <= 0:
            raise ValueError("sample_rate_hz must be > 0")
        self.sample_rate_hz = float(sample_rate_hz)
        self.max_delay_seconds = max(0.0, float(max_delay_seconds))

    @staticmethod
    def rms(samples: Iterable[float]) -> float:
        data = [float(v) for v in samples]
        if not data:
            return 0.0
        return math.sqrt(sum(v * v for v in data) / len(data))

    @staticmethod
    def peak(samples: Iterable[float]) -> float:
        data = [abs(float(v)) for v in samples]
        return max(data, default=0.0)

    def spectrum(self, samples: Iterable[float]) -> list[tuple[float, complex]]:
        data = [float(v) for v in samples]
        if not data:
            return []
        n_fft = _next_pow2(len(data))
        padded = [complex(v, 0.0) for v in data] + [0j] * (n_fft - len(data))
        bins = _fft(padded)
        half = n_fft // 2
        return [(k * self.sample_rate_hz / n_fft, bins[k]) for k in range(half + 1)]

    def dominant_frequency(self, samples: Iterable[float]) -> float | None:
        spec = self.spectrum(samples)
        if len(spec) <= 1:
            return None
        return max(spec[1:], key=lambda item: abs(item[1]))[0]

    def coefficient_at(self, samples: Iterable[float], frequency_hz: float) -> complex:
        data = [float(v) for v in samples]
        if not data:
            return 0j
        omega = -2j * math.pi * float(frequency_hz) / self.sample_rate_hz
        return sum(v * cmath.exp(omega * i) for i, v in enumerate(data))

    def estimate_delay_seconds(self, reference: Iterable[float], signal: Iterable[float]) -> float | None:
        ref = [float(v) for v in reference]
        out = [float(v) for v in signal]
        n = min(len(ref), len(out))
        if n < 3:
            return None
        ref = ref[:n]
        out = out[:n]
        max_lag = min(n - 2, int(round(self.max_delay_seconds * self.sample_rate_hz)))
        best_lag = 0
        best_score = -1.0
        for lag in range(-max_lag, max_lag + 1):
            if lag >= 0:
                xs = ref[: n - lag]
                ys = out[lag:n]
            else:
                xs = ref[-lag:n]
                ys = out[: n + lag]
            if len(xs) < 3:
                continue
            mx = sum(xs) / len(xs)
            my = sum(ys) / len(ys)
            dx = [x - mx for x in xs]
            dy = [y - my for y in ys]
            denom = math.sqrt(sum(x * x for x in dx) * sum(y * y for y in dy))
            if denom <= 1e-18:
                continue
            score = abs(sum(x * y for x, y in zip(dx, dy)) / denom)
            if score > best_score:
                best_score = score
                best_lag = lag
        if best_score < 0:
            return None
        return best_lag / self.sample_rate_hz

    def phase_delta_rad(self, reference: Iterable[float], signal: Iterable[float], frequency_hz: float) -> float | None:
        x = self.coefficient_at(reference, frequency_hz)
        y = self.coefficient_at(signal, frequency_hz)
        if abs(x) <= 1e-18 or abs(y) <= 1e-18:
            return None
        return _normalize_phase(cmath.phase(y) - cmath.phase(x))

    def coherence(self, reference: Iterable[float], signal: Iterable[float], frequency_hz: float, *, windows: int = 4) -> float | None:
        ref = [float(v) for v in reference]
        out = [float(v) for v in signal]
        n = min(len(ref), len(out))
        if n < windows * 8:
            return None
        segment = n // windows
        sxx = 0.0
        syy = 0.0
        sxy = 0j
        used = 0
        for w in range(windows):
            start = w * segment
            stop = start + segment
            if stop > n:
                break
            xs = ref[start:stop]
            ys = out[start:stop]
            if len(xs) < 8:
                continue
            win = [0.5 - 0.5 * math.cos(2.0 * math.pi * i / (len(xs) - 1)) for i in range(len(xs))]
            x = self.coefficient_at([a * b for a, b in zip(xs, win)], frequency_hz)
            y = self.coefficient_at([a * b for a, b in zip(ys, win)], frequency_hz)
            sxx += abs(x) ** 2
            syy += abs(y) ** 2
            sxy += x * y.conjugate()
            used += 1
        if not used or sxx <= 1e-18 or syy <= 1e-18:
            return None
        value = abs(sxy) ** 2 / (sxx * syy)
        return max(0.0, min(1.0, float(value)))

    def bandwidth(self, reference: Iterable[float], signal: Iterable[float]) -> tuple[float | None, float | None, float | None]:
        ref_spec = self.spectrum(reference)
        out_spec = self.spectrum(signal)
        if len(ref_spec) != len(out_spec) or len(ref_spec) <= 2:
            return None, None, None
        max_ref = max((abs(v) for _, v in ref_spec[1:]), default=0.0)
        if max_ref <= 1e-18:
            return None, None, None
        response: list[tuple[float, float]] = []
        for (freq, x), (_, y) in zip(ref_spec[1:], out_spec[1:]):
            mag = abs(x)
            if mag < max_ref * 0.03:
                continue
            response.append((freq, abs(y) / mag))
        if not response:
            return None, None, None
        peak_index = max(range(len(response)), key=lambda i: response[i][1])
        peak_gain = response[peak_index][1]
        if peak_gain <= 1e-18:
            return None, None, None
        threshold = peak_gain / math.sqrt(2.0)
        left = peak_index
        right = peak_index
        while left > 0 and response[left - 1][1] >= threshold:
            left -= 1
        while right + 1 < len(response) and response[right + 1][1] >= threshold:
            right += 1
        low = response[left][0]
        high = response[right][0]
        return low, high, max(0.0, high - low)

    def analyze(self, reference: Iterable[float], signal: Iterable[float], channel: str) -> ChannelMeasurement:
        ref = [float(v) for v in reference]
        out = [float(v) for v in signal]
        if not ref or not out:
            return ChannelMeasurement(channel, 0.0, 0.0, None, None, None, None, None, None, None, None)
        n = min(len(ref), len(out))
        ref = ref[:n]
        out = out[:n]
        dominant = self.dominant_frequency(out)
        ref_rms = self.rms(ref)
        out_rms = self.rms(out)
        gain = out_rms / ref_rms if ref_rms > 1e-18 else None
        phase = self.phase_delta_rad(ref, out, dominant) if dominant is not None else None
        coherence = self.coherence(ref, out, dominant) if dominant is not None else None
        low, high, width = self.bandwidth(ref, out)
        return ChannelMeasurement(
            channel=channel,
            amplitude_rms=out_rms,
            peak_amplitude=self.peak(out),
            dominant_frequency_hz=dominant,
            gain=gain,
            delay_seconds=self.estimate_delay_seconds(ref, out),
            phase_delta_rad=phase,
            coherence=coherence,
            bandwidth_low_hz=low,
            bandwidth_high_hz=high,
            bandwidth_hz=width,
        )


class ResonanceStructure:
    """Independent X72 experimental signal/sensor subsystem.

    It does not import or mutate QueenCore/NoyauEngine. Any wheel interaction
    must pass through the separate bridge.
    """

    def __init__(self, config: ResonanceConfig | None = None, *, journal: ExperimentJournal | None = None):
        self.config = config or ResonanceConfig()
        self.config.validate()
        self.generator = SignalGenerator(self.config)
        self.analyzer = SignalAnalyzer(self.config.sample_rate_hz, self.config.max_delay_seconds)
        self.journal = journal or ExperimentJournal()
        self.channels: dict[str, list[float]] = {name: [] for name in CHANNELS}
        self.route_sensors: dict[str, RouteSensor] = {node: RouteSensor(node) for node in ROUTE_A_NODES}
        self.last_report: dict[str, Any] | None = None

    def reset_channels(self) -> None:
        self.channels = {name: [] for name in CHANNELS}

    def record_route_sample(self, node: str, value: float) -> None:
        try:
            sensor = self.route_sensors[node]
        except KeyError as exc:
            raise ValueError(f"unknown Route A node: {node}") from exc
        sensor.add(value)

    def ingest(self, channel: str, samples: Iterable[float]) -> None:
        if channel not in self.channels:
            raise ValueError(f"unknown channel: {channel}")
        values = [float(v) for v in samples]
        if any(not math.isfinite(v) for v in values):
            raise ValueError("samples must be finite")
        self.channels[channel].extend(values)

    def _make_reference(self, test_type: str, samples: int, frequency_hz: float) -> list[float]:
        test_type = test_type.upper()
        if test_type == "FIXED_SINE":
            return self.generator.sine(samples, frequency_hz=frequency_hz)
        if test_type == "IMPULSE":
            return self.generator.impulse(samples, index=min(4, samples - 1))
        if test_type == "CHIRP":
            end = min(self.config.sample_rate_hz * 0.40, max(frequency_hz * 4.0, frequency_hz + 1.0))
            start = max(0.5, min(frequency_hz / 4.0, end / 2.0))
            return self.generator.chirp(samples, start_hz=start, end_hz=end)
        if test_type in {"BREATHING", "SYNCHRONOUS", "ASCENDING", "DESCENDING"}:
            return self.generator.sine(samples, frequency_hz=frequency_hz, breathing=True)
        raise ValueError(f"unsupported test type: {test_type}")

    def run_synthetic_test(
        self,
        test_type: str,
        *,
        source_channel: str = "C1",
        duration_seconds: float = 4.0,
        frequency_hz: float | None = None,
    ) -> dict[str, Any]:
        """Deterministic demo telemetry for software verification only."""
        if source_channel not in ZONES:
            raise ValueError("source_channel must be C1..C7")
        if duration_seconds <= 0:
            raise ValueError("duration_seconds must be > 0")
        frequency_hz = self.config.carrier_hz if frequency_hz is None else float(frequency_hz)
        samples = max(64, int(round(duration_seconds * self.config.sample_rate_hz)))
        reference = self._make_reference(test_type, samples, frequency_hz)
        self.reset_channels()
        self.channels["REF"] = list(reference)
        source_index = ZONES.index(source_channel)
        test_type_upper = test_type.upper()

        for zone_index, zone in enumerate(ZONES):
            distance = abs(zone_index - source_index)
            gain = max(0.55, 1.0 - 0.055 * distance)
            delay = distance
            phase_offset = 0.0
            if test_type_upper == "ASCENDING":
                phase_offset = zone_index * self.config.phase_step_rad
            elif test_type_upper == "DESCENDING":
                phase_offset = -zone_index * self.config.phase_step_rad

            if test_type_upper in {"FIXED_SINE", "BREATHING", "SYNCHRONOUS", "ASCENDING", "DESCENDING"}:
                breathing = test_type_upper in {"BREATHING", "SYNCHRONOUS", "ASCENDING", "DESCENDING"}
                base = self.generator.sine(
                    samples,
                    frequency_hz=frequency_hz,
                    amplitude=gain,
                    phase_rad=phase_offset,
                    breathing=breathing,
                )
                out = [0.0] * delay + base[: samples - delay] if delay else base
            else:
                shifted = [0.0] * delay + reference[: samples - delay] if delay else list(reference)
                out = [gain * v for v in shifted]
            self.channels[zone] = out

        return self.analyze_current(
            test_type=test_type_upper,
            source_channel=source_channel,
            input_parameters={
                "duration_seconds": duration_seconds,
                "frequency_hz": frequency_hz,
                "sample_rate_hz": self.config.sample_rate_hz,
                "synthetic_demo": True,
            },
        )

    def analyze_link(self, left: str, right: str) -> dict[str, Any]:
        if left not in self.channels or right not in self.channels:
            raise ValueError("link endpoints must be REF or C1..C7")
        return self.analyzer.analyze(
            self.channels[left],
            self.channels[right],
            f"{left}<->{right}",
        ).to_dict()

    def analyze_current(
        self,
        *,
        test_type: str,
        source_channel: str | None = None,
        input_parameters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        ref = self.channels["REF"]
        measurements: dict[str, dict[str, Any]] = {}
        for zone in ZONES:
            measurements[zone] = self.analyzer.analyze(ref, self.channels[zone], zone).to_dict()

        links: dict[str, dict[str, Any]] = {}
        for left, right in zip(ZONES, ZONES[1:]):
            key = f"{left}<->{right}"
            links[key] = self.analyze_link(left, right)

        low_sum = sum(measurements[z]["amplitude_rms"] for z in ("C1", "C2", "C3"))
        high_sum = sum(measurements[z]["amplitude_rms"] for z in ("C5", "C6", "C7"))
        upper_lower_ratio = high_sum / low_sum if low_sum > 1e-18 else None

        report = {
            "schema": MEASUREMENT_SCHEMA,
            "timestamp": time.time(),
            "status": "MEASURED" if any(self.channels[z] for z in ZONES) else "NOT_RUN",
            "test_type": test_type,
            "source_channel": source_channel,
            "input_parameters": dict(input_parameters or {}),
            "reference": {
                "samples": len(ref),
                "amplitude_rms": self.analyzer.rms(ref),
                "peak_amplitude": self.analyzer.peak(ref),
                "dominant_frequency_hz": self.analyzer.dominant_frequency(ref),
                "authority": "MEASURED" if ref else "NOT_RUN",
            },
            "measurements": measurements,
            "links": links,
            "upper_lower_ratio_M": {
                "value": upper_lower_ratio,
                "expression": "(C5+C6+C7)/(C1+C2+C3) using RMS amplitude",
                "authority": "CALCULATED" if upper_lower_ratio is not None else "NOT_RUN",
            },
            "route_a": route_a_payload(),
            "route_sensors": {k: v.payload() for k, v in self.route_sensors.items()},
            "research_constants": research_constants(),
            "physical_claim": False,
            "conclusion": "DATA_ONLY",
            "anomalies": [],
        }
        self.last_report = report
        self.journal.append(report)
        return report

    @staticmethod
    def stereo(left: Iterable[float], right: Iterable[float]) -> dict[str, list[float]]:
        l = [float(v) for v in left]
        r = [float(v) for v in right]
        n = min(len(l), len(r))
        l = l[:n]
        r = r[:n]
        return {
            "L": l,
            "R": r,
            "SUM": [a + b for a, b in zip(l, r)],
            "DIFF": [a - b for a, b in zip(l, r)],
        }

    def snapshot(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA,
            "status": "CANDIDATE",
            "authority": "OBSERVATION_ONLY",
            "standalone": True,
            "mutates_wheel": False,
            "physical_claim": False,
            "channels": {name: len(values) for name, values in self.channels.items()},
            "route_a": route_a_payload(),
            "route_sensors": {k: v.payload() for k, v in self.route_sensors.items()},
            "research_constants": research_constants(),
        }
