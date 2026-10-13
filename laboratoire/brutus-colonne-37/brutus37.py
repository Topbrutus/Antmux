from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal, getcontext
from typing import Any

getcontext().prec = 80
BRUTUS_CONSTANT = (Decimal(7) ** 21) / (Decimal(10) ** 17)
BRUTUS_CONSTANT_TEXT = "5.58545864083284007"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def canonical(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def v_p(n: int, p: int) -> int:
    n = abs(int(n))
    if n == 0:
        return 0
    k = 0
    while n % p == 0:
        k += 1
        n //= p
    return k


def digital_root(n: int) -> int:
    n = abs(int(n))
    return 0 if n == 0 else 1 + ((n - 1) % 9)


def is_square(n: int) -> bool:
    if n < 0:
        return False
    r = math.isqrt(n)
    return r * r == n


@dataclass
class CrystalRecord:
    key: str
    value: int
    formula_id: str
    level: str
    bucket37: int
    count: int = 0
    paths: set[str] = field(default_factory=set)
    first_seen: str = ""
    last_seen: str = ""
    trace_digest: str = ""
    brutus_constant_applied: bool = False

    @property
    def independent_paths(self) -> int:
        return len(self.paths)

    @property
    def replay_budget(self) -> int:
        if self.count <= 2:
            return 8
        if self.count <= 4:
            return 6
        if self.count <= 8:
            return 4
        if self.count <= 16:
            return 2
        return 1


class FastLibrary37:
    """37 hash lanes. Duplicate observations update one canonical record."""

    def __init__(self) -> None:
        self._buckets: list[dict[str, CrystalRecord]] = [dict() for _ in range(37)]
        self.observations = 0
        self.unique_crystals = 0
        self.dust_collapsed = 0

    @staticmethod
    def identity(value: int, formula_id: str, level: str) -> str:
        return sha256_text(canonical({"value": int(value), "formula_id": formula_id, "level": level}))

    @staticmethod
    def lane(key: str) -> int:
        return int(key[:16], 16) % 37

    def get(self, value: int, formula_id: str, level: str = "L1") -> CrystalRecord | None:
        key = self.identity(value, formula_id, level)
        return self._buckets[self.lane(key)].get(key)

    def observe(self, value: int, formula_id: str, path: str, *, level: str = "L1", trace_digest: str = "", brutus_constant_applied: bool = False) -> tuple[CrystalRecord, bool]:
        key = self.identity(value, formula_id, level)
        lane = self.lane(key)
        rec = self._buckets[lane].get(key)
        created = rec is None
        now = utc_now()
        if created:
            rec = CrystalRecord(
                key=key,
                value=int(value),
                formula_id=formula_id,
                level=level,
                bucket37=lane,
                first_seen=now,
                trace_digest=trace_digest,
                brutus_constant_applied=bool(brutus_constant_applied),
            )
            self._buckets[lane][key] = rec
            self.unique_crystals += 1
        else:
            self.dust_collapsed += 1
        rec.count += 1
        rec.paths.add(path)
        rec.last_seen = now
        self.observations += 1
        return rec, created

    def stats(self) -> dict[str, int]:
        return {
            "lanes": 37,
            "lanes_used": sum(1 for b in self._buckets if b),
            "observations": self.observations,
            "unique_crystals": self.unique_crystals,
            "dust_collapsed": self.dust_collapsed,
        }


class Spine33:
    """33 deterministic instruments. They measure; they do not silently mutate the integer."""

    NAMES = (
        "NORMALIZE", "SIGN", "ABS", "PARITY", "DIGITS", "DIGIT_SUM", "DIGITAL_ROOT",
        "BIT_LENGTH", "MOD_37", "QUOTIENT_37", "DIVISIBLE_37", "MOD_7", "MOD_13",
        "MOD_3", "MOD_9", "GCD_37", "GCD_7", "GCD_13", "IS_SQUARE", "REVERSED_DECIMAL",
        "IS_PALINDROME", "V2", "V3", "V7", "V13", "POPCOUNT", "MOD_111", "MOD_273",
        "MOD_343", "MOD_637", "MOD_2401", "BRUTUS_CONSTANT_REFERENCE", "ROUTE_SIGNATURE",
    )

    def evaluate(self, value: int, route_signature: str) -> list[dict[str, Any]]:
        n = int(value)
        s = str(abs(n))
        reversed_n = int(s[::-1]) if s else 0
        values: list[Any] = [
            n,
            -1 if n < 0 else (1 if n > 0 else 0),
            abs(n),
            "EVEN" if n % 2 == 0 else "ODD",
            len(s),
            sum(int(ch) for ch in s),
            digital_root(n),
            abs(n).bit_length(),
            n % 37,
            n // 37,
            n % 37 == 0,
            n % 7,
            n % 13,
            n % 3,
            n % 9,
            math.gcd(abs(n), 37),
            math.gcd(abs(n), 7),
            math.gcd(abs(n), 13),
            is_square(n),
            reversed_n,
            s == s[::-1],
            v_p(n, 2),
            v_p(n, 3),
            v_p(n, 7),
            v_p(n, 13),
            abs(n).bit_count(),
            n % 111,
            n % 273,
            n % 343,
            n % 637,
            n % 2401,
            BRUTUS_CONSTANT_TEXT,
            route_signature,
        ]
        assert len(values) == 33 == len(self.NAMES)
        return [{"index": i + 1, "instrument": name, "measurement": val} for i, (name, val) in enumerate(zip(self.NAMES, values))]


class Brutus37Engine:
    """33 vertebrae + 4 master organs = 37-post prototype."""

    ORGANS = ("BRUTUS_CONSTANT", "PAPILLON", "FAST_LIBRARY_37", "QUEEN_ANTS")

    def __init__(self) -> None:
        self.library = FastLibrary37()
        self.spine = Spine33()
        self.vertebra_evaluations = 0
        self.cache_hits = 0
        self.cache_misses = 0

    @staticmethod
    def papillon_route(value: int, formula_id: str, path: str) -> dict[str, int]:
        digest = sha256_text(canonical({"value": int(value), "formula_id": formula_id, "path": path}))
        return {"route144": int(digest[:16], 16) % 144, "lane37": int(digest[16:32], 16) % 37}

    def process(self, value: int, *, formula_id: str = "SEED", path: str = "root", level: str = "L1") -> dict[str, Any]:
        value = int(value)
        existing = self.library.get(value, formula_id, level)
        route = self.papillon_route(value, formula_id, path)
        route_signature = f"P{route['route144']:03d}/V{route['lane37']:02d}"

        if existing is not None:
            self.cache_hits += 1
            rec, _ = self.library.observe(value, formula_id, path, level=level, trace_digest=existing.trace_digest)
            return {
                "value": value,
                "cache_hit": True,
                "route": route,
                "record": self._record_view(rec),
                "vertebrae": None,
                "constant": BRUTUS_CONSTANT_TEXT,
                "constant_applied": False,
            }

        self.cache_misses += 1
        vertebrae = self.spine.evaluate(value, route_signature)
        self.vertebra_evaluations += 33
        trace_digest = sha256_text(canonical(vertebrae))
        rec, _ = self.library.observe(value, formula_id, path, level=level, trace_digest=trace_digest)
        return {
            "value": value,
            "cache_hit": False,
            "route": route,
            "record": self._record_view(rec),
            "vertebrae": vertebrae,
            "constant": BRUTUS_CONSTANT_TEXT,
            "constant_applied": False,
        }

    @staticmethod
    def _record_view(rec: CrystalRecord) -> dict[str, Any]:
        return {
            "key": rec.key,
            "bucket37": rec.bucket37,
            "count": rec.count,
            "independent_paths": rec.independent_paths,
            "replay_budget": rec.replay_budget,
            "first_seen": rec.first_seen,
            "last_seen": rec.last_seen,
            "trace_digest": rec.trace_digest,
        }

    def status(self) -> dict[str, Any]:
        return {
            "schema": "BRUTUS-COLONNE-37-PROTOTYPE-v1",
            "posts": 37,
            "vertebrae": 33,
            "organs": list(self.ORGANS),
            "brutus_constant": BRUTUS_CONSTANT_TEXT,
            "library": self.library.stats(),
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "vertebra_evaluations": self.vertebra_evaluations,
        }
