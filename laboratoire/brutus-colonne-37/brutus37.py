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
Z_STAMP_SCHEMA = "BRUTUS-Z-STAMP-v1"


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


@dataclass(frozen=True)
class ZStamp:
    """Brutus seal placed after C1 and before C2.

    z_id is canonical for the matter itself, so identical matter from different
    paths keeps one identity. Provenance and parent lineage remain separate.
    """

    z_id: str
    normalized_value: int
    formula_id: str
    level: str
    constant_reference: str
    cortex_version: str
    parent_z: str | None
    provenance_digest: str
    route37: int

    def canonical_identity(self) -> dict[str, Any]:
        return {
            "schema": Z_STAMP_SCHEMA,
            "z_id": self.z_id,
            "normalized_value": self.normalized_value,
            "formula_id": self.formula_id,
            "level": self.level,
            "constant_reference": self.constant_reference,
            "cortex_version": self.cortex_version,
        }

    def lineage_view(self) -> dict[str, Any]:
        return {
            "parent_z": self.parent_z,
            "provenance_digest": self.provenance_digest,
            "route37": self.route37,
        }

    def as_dict(self) -> dict[str, Any]:
        return {**self.canonical_identity(), **self.lineage_view()}


class BrutusCortex:
    """Master organ inserted between C1 Entrada and C2 Empreinte."""

    VERSION = "BRUTUS-CORTEX-PINEALE-v1"

    @staticmethod
    def normalize(value: int) -> int:
        # C1: explicit, deterministic normalization. No hidden mutation.
        return int(value)

    def stamp(
        self,
        normalized_value: int,
        *,
        formula_id: str,
        level: str,
        path: str,
        parent_z: str | None = None,
    ) -> ZStamp:
        identity_payload = {
            "schema": Z_STAMP_SCHEMA,
            "normalized_value": int(normalized_value),
            "formula_id": str(formula_id),
            "level": str(level),
            "brutus_constant": BRUTUS_CONSTANT_TEXT,
            "cortex_version": self.VERSION,
        }
        digest = sha256_text(canonical(identity_payload))
        z_id = "Z-" + digest[:32]
        provenance_digest = sha256_text(
            canonical({"z_id": z_id, "path": str(path), "parent_z": parent_z})
        )
        return ZStamp(
            z_id=z_id,
            normalized_value=int(normalized_value),
            formula_id=str(formula_id),
            level=str(level),
            constant_reference=BRUTUS_CONSTANT_TEXT,
            cortex_version=self.VERSION,
            parent_z=parent_z,
            provenance_digest=provenance_digest,
            route37=int(digest[32:48], 16) % 37,
        )

    @staticmethod
    def fingerprint(stamp: ZStamp) -> str:
        """C2 technical fingerprint of matter that is already Z-stamped."""
        return sha256_text(canonical(stamp.canonical_identity()))


@dataclass
class CrystalRecord:
    key: str
    z_id: str
    c2_fingerprint: str
    value: int
    formula_id: str
    level: str
    bucket37: int
    count: int = 0
    paths: set[str] = field(default_factory=set)
    provenance_digests: set[str] = field(default_factory=set)
    parent_z_ids: set[str] = field(default_factory=set)
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
    """37 hash lanes. Duplicate Z identities update one canonical record."""

    def __init__(self) -> None:
        self._buckets: list[dict[str, CrystalRecord]] = [dict() for _ in range(37)]
        self.observations = 0
        self.unique_crystals = 0
        self.dust_collapsed = 0

    @staticmethod
    def identity(z_id: str) -> str:
        return sha256_text(canonical({"z_id": str(z_id)}))

    @staticmethod
    def lane(key: str) -> int:
        return int(key[:16], 16) % 37

    def get_by_z(self, z_id: str) -> CrystalRecord | None:
        key = self.identity(z_id)
        return self._buckets[self.lane(key)].get(key)

    def get(self, value: int, formula_id: str, level: str = "L1") -> CrystalRecord | None:
        # Compatibility helper: reconstruct canonical Z identity without path.
        cortex = BrutusCortex()
        z = cortex.stamp(int(value), formula_id=formula_id, level=level, path="lookup")
        return self.get_by_z(z.z_id)

    def observe(
        self,
        stamp: ZStamp,
        c2_fingerprint: str,
        path: str,
        *,
        trace_digest: str = "",
        brutus_constant_applied: bool = False,
    ) -> tuple[CrystalRecord, bool]:
        key = self.identity(stamp.z_id)
        lane = self.lane(key)
        rec = self._buckets[lane].get(key)
        created = rec is None
        now = utc_now()
        if created:
            rec = CrystalRecord(
                key=key,
                z_id=stamp.z_id,
                c2_fingerprint=c2_fingerprint,
                value=stamp.normalized_value,
                formula_id=stamp.formula_id,
                level=stamp.level,
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
        rec.paths.add(str(path))
        rec.provenance_digests.add(stamp.provenance_digest)
        if stamp.parent_z:
            rec.parent_z_ids.add(stamp.parent_z)
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
    """33 deterministic instruments. C1 precedes the Brutus Cortex; C2 follows it."""

    NAMES = (
        "C1_NORMALIZE", "C2_EMPREINTE_Z", "C3_LIBRARY", "C4_NOVELTY", "C5_RARITY",
        "C6_PROVENANCE", "C7_ROUTER", "T1_FAMILY", "T2_EXACT_DUPLICATE", "T3_NEIGHBORHOOD",
        "T4_CONVERGENCE", "T5_INDEPENDENCE", "T6_PAPILLON", "T7_CALCUL", "T8_COUNTERTEST",
        "T9_STABILITY", "T10_REPLAY", "T11_BUDGET", "T12_CANDIDATE", "L1_CRYSTAL_SCORE",
        "L2_THRESHOLD", "L3_PRESS", "L4_CANON", "L5_PLACEMENT", "S1_AGGREGATOR",
        "S2_LINEAGE_INDEX", "S3_ROUTE_INDEX", "S4_FORMULA_INDEX", "S5_FAST_INDEX",
        "CO1_ARCHIVE", "CO2_PROOF_CHAIN", "CO3_CHECKPOINT", "CO4_RESUME",
    )

    def evaluate(self, value: int, route_signature: str, z_stamp: ZStamp, c2_fingerprint: str) -> list[dict[str, Any]]:
        n = int(value)
        s = str(abs(n))
        values: list[Any] = [
            n,
            c2_fingerprint,
            z_stamp.route37,
            {"known": False},
            {"initial_replay_budget": 8},
            z_stamp.provenance_digest,
            route_signature,
            {"formula_id": z_stamp.formula_id},
            {"z_id": z_stamp.z_id},
            {"mod37": n % 37},
            {"route37": z_stamp.route37},
            {"parent_z": z_stamp.parent_z},
            route_signature,
            {"value": n, "constant_applied": False},
            {"status": "UNTESTED"},
            {"status": "UNMEASURED"},
            8,
            {"budget_class": "PROTOTYPE"},
            {"candidate": True},
            {"score": None},
            {"threshold": None},
            {"dust_key": z_stamp.z_id},
            {"canonical_z": z_stamp.z_id},
            "HOT",
            {"aggregate_z": z_stamp.z_id},
            {"parent_z": z_stamp.parent_z},
            route_signature,
            z_stamp.formula_id,
            {"bucket37": z_stamp.route37},
            {"archive": False},
            {"trace": sha256_text(z_stamp.z_id + c2_fingerprint)},
            {"checkpoint": None},
            {"resume": None},
        ]
        assert len(values) == 33 == len(self.NAMES)
        return [
            {"index": i + 1, "instrument": name, "measurement": val}
            for i, (name, val) in enumerate(zip(self.NAMES, values))
        ]


class Brutus37Engine:
    """33 vertebrae + 4 master organs = 37-post prototype."""

    ORGANS = ("BRUTUS_CORTEX_PINEALE", "PAPILLON", "FAST_LIBRARY_37", "QUEEN_ANTS")

    def __init__(self) -> None:
        self.cortex = BrutusCortex()
        self.library = FastLibrary37()
        self.spine = Spine33()
        self.vertebra_evaluations = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.z_stamps_issued = 0

    @staticmethod
    def papillon_route(value: int, formula_id: str, path: str, z_id: str) -> dict[str, int]:
        digest = sha256_text(
            canonical({"value": int(value), "formula_id": formula_id, "path": path, "z_id": z_id})
        )
        return {"route144": int(digest[:16], 16) % 144, "lane37": int(digest[16:32], 16) % 37}

    def process(
        self,
        value: int,
        *,
        formula_id: str = "SEED",
        path: str = "root",
        level: str = "L1",
        parent_z: str | None = None,
    ) -> dict[str, Any]:
        # C1 — Entrée / normalization.
        normalized = self.cortex.normalize(value)

        # Master organ — Brutus Cortex / Pineale. Z is sealed BEFORE C2.
        z_stamp = self.cortex.stamp(
            normalized,
            formula_id=formula_id,
            level=level,
            path=path,
            parent_z=parent_z,
        )
        self.z_stamps_issued += 1

        # C2 — technical fingerprint of already stamped matter.
        c2_fingerprint = self.cortex.fingerprint(z_stamp)
        existing = self.library.get_by_z(z_stamp.z_id)
        route = self.papillon_route(normalized, formula_id, path, z_stamp.z_id)
        route_signature = f"P{route['route144']:03d}/V{route['lane37']:02d}"
        sequence = ["C1_ENTREE", "BRUTUS_CORTEX_PINEALE", "Z_STAMP", "C2_EMPREINTE"]

        if existing is not None:
            self.cache_hits += 1
            rec, _ = self.library.observe(
                z_stamp,
                c2_fingerprint,
                path,
                trace_digest=existing.trace_digest,
            )
            return {
                "value": normalized,
                "cache_hit": True,
                "sequence": sequence,
                "z_stamp": z_stamp.as_dict(),
                "c2_fingerprint": c2_fingerprint,
                "route": route,
                "record": self._record_view(rec),
                "vertebrae": None,
                "constant": BRUTUS_CONSTANT_TEXT,
                "constant_applied": False,
            }

        self.cache_misses += 1
        vertebrae = self.spine.evaluate(normalized, route_signature, z_stamp, c2_fingerprint)
        self.vertebra_evaluations += 33
        trace_digest = sha256_text(canonical({"z_stamp": z_stamp.as_dict(), "vertebrae": vertebrae}))
        rec, _ = self.library.observe(
            z_stamp,
            c2_fingerprint,
            path,
            trace_digest=trace_digest,
        )
        return {
            "value": normalized,
            "cache_hit": False,
            "sequence": sequence,
            "z_stamp": z_stamp.as_dict(),
            "c2_fingerprint": c2_fingerprint,
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
            "z_id": rec.z_id,
            "c2_fingerprint": rec.c2_fingerprint,
            "bucket37": rec.bucket37,
            "count": rec.count,
            "independent_paths": rec.independent_paths,
            "provenance_count": len(rec.provenance_digests),
            "parent_z_count": len(rec.parent_z_ids),
            "replay_budget": rec.replay_budget,
            "first_seen": rec.first_seen,
            "last_seen": rec.last_seen,
            "trace_digest": rec.trace_digest,
        }

    def status(self) -> dict[str, Any]:
        return {
            "schema": "BRUTUS-COLONNE-37-PROTOTYPE-v2-ZSTAMP",
            "posts": 37,
            "vertebrae": 33,
            "organs": list(self.ORGANS),
            "brutus_constant": BRUTUS_CONSTANT_TEXT,
            "cortex_version": self.cortex.VERSION,
            "z_stamp_schema": Z_STAMP_SCHEMA,
            "z_stamps_issued": self.z_stamps_issued,
            "library": self.library.stats(),
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "vertebra_evaluations": self.vertebra_evaluations,
        }
