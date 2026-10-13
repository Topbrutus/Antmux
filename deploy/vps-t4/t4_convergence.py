from __future__ import annotations

import os
from collections import deque
from dataclasses import dataclass, field
from hashlib import blake2b
from typing import Any

SCHEMA = "BRUTUS_T4_CONVERGENCE_V1"
RECENT_LIMIT = 37
DEFAULT_MAX_TARGETS = 16_384
DEFAULT_SIGS_PER_TARGET = 16


def _env_int(name: str, default: int, minimum: int, maximum: int) -> int:
    try:
        value = int(os.getenv(name, str(default)).strip())
    except (TypeError, ValueError):
        value = default
    return max(minimum, min(maximum, value))


def _sig(text: str | None, size: int = 12) -> bytes:
    raw = "" if text is None else str(text)
    return blake2b(raw.encode("utf-8"), digest_size=size).digest()


@dataclass
class TargetRecord:
    c2_sigs: set[bytes] = field(default_factory=set)
    families: set[str] = field(default_factory=set)
    origin_sigs: set[bytes] = field(default_factory=set)
    parent_sigs: set[bytes] = field(default_factory=set)
    observations: int = 0


class T4Convergence:
    """Bounded shadow convergence tracker keyed by canonical Z target.

    T2 owns exact duplicates. T3 owns semantic neighborhood. T4 counts a
    convergence only when a target Z receives a C2 fingerprint that is distinct
    from the C2 fingerprints already retained for that same target.
    """

    T3_CLASSES = ("EXACT_REFERENCE", "NEAR", "ADJACENT", "DISTANT", "ISOLATED")

    def __init__(
        self,
        max_targets: int | None = None,
        sigs_per_target: int | None = None,
    ) -> None:
        self.max_targets = max_targets if max_targets is not None else _env_int(
            "BROTO_T4_MAX_TARGETS", DEFAULT_MAX_TARGETS, 37, 131_072
        )
        self.sigs_per_target = sigs_per_target if sigs_per_target is not None else _env_int(
            "BROTO_T4_SIGS_PER_TARGET", DEFAULT_SIGS_PER_TARGET, 2, 64
        )
        self._targets: dict[str, TargetRecord] = {}
        self.observations = 0
        self.retained_observations = 0
        self.missing_z = 0
        self.untracked_capacity = 0
        self.signature_capacity_events = 0
        self.exact_repeat_observations = 0
        self.distinct_structure_observations = 0
        self.structural_convergence_events = 0
        self.convergent_targets = 0
        self.cross_family_convergence_events = 0
        self.cross_family_targets = 0
        self.multi_origin_convergence_events = 0
        self.multi_origin_targets = 0
        self.multi_parent_convergence_events = 0
        self.multi_parent_targets = 0
        self.max_distinct_c2_per_target = 0
        self.t2_consistency_conflicts = 0
        self.t3_consistency_conflicts = 0
        self.convergence_by_t3_class = {name: 0 for name in self.T3_CLASSES}
        self.last_event: str | None = None
        self._recent: deque[dict[str, Any]] = deque(maxlen=RECENT_LIMIT)

    def observe(
        self,
        packet: Any,
        fingerprint: str,
        *,
        family: str,
        t2_event: str,
        t3_class: str,
    ) -> str:
        if not isinstance(fingerprint, str) or not fingerprint.startswith("C2-"):
            raise ValueError("T4 requires a C2- fingerprint")
        self.observations += 1
        family = str(family or "OTHER")
        t2_event = str(t2_event or "")
        t3_class = str(t3_class or "ISOLATED")
        z_id = getattr(packet, "z_id", None)
        if not isinstance(z_id, str) or not z_id.startswith("Z-"):
            self.missing_z += 1
            self.last_event = "MISSING_Z"
            return self.last_event

        rec = self._targets.get(z_id)
        if rec is None:
            if len(self._targets) >= self.max_targets:
                self.untracked_capacity += 1
                self.last_event = "UNTRACKED_TARGET_CAPACITY"
                return self.last_event
            rec = TargetRecord()
            self._targets[z_id] = rec

        rec.observations += 1
        self.retained_observations += 1
        c2sig = _sig(fingerprint, 16)
        origin_sig = _sig(getattr(packet, "z_origin_id", None), 8)
        parent_sig = _sig(getattr(packet, "z_parent_id", None), 8)
        already = c2sig in rec.c2_sigs
        t2_says_duplicate = t2_event.startswith("EXACT_DUPLICATE")
        t3_says_exact = t3_class == "EXACT_REFERENCE"

        if already:
            self.exact_repeat_observations += 1
            if not t2_says_duplicate:
                self.t2_consistency_conflicts += 1
            if not t3_says_exact:
                self.t3_consistency_conflicts += 1
            event = "EXACT_REPEAT_NOT_CONVERGENCE"
        else:
            if len(rec.c2_sigs) >= self.sigs_per_target:
                # Once a target reaches its signature cap we cannot safely tell a
                # never-retained C2 from a repeat of a never-retained C2. Record
                # capacity pressure, but do not manufacture a consistency conflict.
                self.signature_capacity_events += 1
                event = "DISTINCT_UNTRACKED_SIGNATURE_CAP"
            else:
                if t2_says_duplicate:
                    self.t2_consistency_conflicts += 1
                if t3_says_exact:
                    self.t3_consistency_conflicts += 1
                previous_count = len(rec.c2_sigs)
                previous_families = set(rec.families)
                previous_origins = set(rec.origin_sigs)
                previous_parents = set(rec.parent_sigs)
                rec.c2_sigs.add(c2sig)
                rec.families.add(family)
                rec.origin_sigs.add(origin_sig)
                rec.parent_sigs.add(parent_sig)
                self.distinct_structure_observations += 1
                self.max_distinct_c2_per_target = max(
                    self.max_distinct_c2_per_target, len(rec.c2_sigs)
                )
                if previous_count == 0:
                    event = "FIRST_STRUCTURE"
                else:
                    self.structural_convergence_events += 1
                    if previous_count == 1:
                        self.convergent_targets += 1
                    if t3_class in self.convergence_by_t3_class:
                        self.convergence_by_t3_class[t3_class] += 1
                    cross_family = bool(previous_families and family not in previous_families)
                    multi_origin = bool(previous_origins and origin_sig not in previous_origins)
                    multi_parent = bool(previous_parents and parent_sig not in previous_parents)
                    if cross_family:
                        self.cross_family_convergence_events += 1
                        if len(rec.families) == 2:
                            self.cross_family_targets += 1
                    if multi_origin:
                        self.multi_origin_convergence_events += 1
                        if len(rec.origin_sigs) == 2:
                            self.multi_origin_targets += 1
                    if multi_parent:
                        self.multi_parent_convergence_events += 1
                        if len(rec.parent_sigs) == 2:
                            self.multi_parent_targets += 1
                    qualifiers = []
                    if cross_family:
                        qualifiers.append("CROSS_FAMILY")
                    if multi_origin:
                        qualifiers.append("MULTI_ORIGIN")
                    if multi_parent:
                        qualifiers.append("MULTI_PARENT")
                    event = "STRUCTURAL_CONVERGENCE"
                    if qualifiers:
                        event += ":" + "+".join(qualifiers)

        self.last_event = event
        self._recent.append({
            "z_id": z_id,
            "fingerprint": fingerprint,
            "family": family,
            "t2_event": t2_event,
            "t3_class": t3_class,
            "event": event,
            "distinct_c2_for_target": len(rec.c2_sigs),
            "families_for_target": len(rec.families),
            "origins_for_target": len(rec.origin_sigs),
            "parents_for_target": len(rec.parent_sigs),
        })
        return event

    def status(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA,
            "mode": SCHEMA,
            "authority": "SHADOW_ONLY",
            "target_key": "Z_ID_CANONICAL_VALUE_TARGET",
            "observations": self.observations,
            "retained_observations": self.retained_observations,
            "tracked_targets": len(self._targets),
            "max_targets": self.max_targets,
            "sigs_per_target": self.sigs_per_target,
            "missing_z": self.missing_z,
            "untracked_capacity": self.untracked_capacity,
            "signature_capacity_events": self.signature_capacity_events,
            "exact_repeat_observations": self.exact_repeat_observations,
            "distinct_structure_observations": self.distinct_structure_observations,
            "structural_convergence_events": self.structural_convergence_events,
            "convergent_targets": self.convergent_targets,
            "cross_family_convergence_events": self.cross_family_convergence_events,
            "cross_family_targets": self.cross_family_targets,
            "multi_origin_convergence_events": self.multi_origin_convergence_events,
            "multi_origin_targets": self.multi_origin_targets,
            "multi_parent_convergence_events": self.multi_parent_convergence_events,
            "multi_parent_targets": self.multi_parent_targets,
            "max_distinct_c2_per_target": self.max_distinct_c2_per_target,
            "convergence_by_t3_class": dict(self.convergence_by_t3_class),
            "t2_consistency_conflicts": self.t2_consistency_conflicts,
            "t3_consistency_conflicts": self.t3_consistency_conflicts,
            "last_event": self.last_event,
            "recent_limit": RECENT_LIMIT,
            "recent": list(self._recent),
            "exact_duplicate_counts_as_convergence": False,
            "hash_distance_used": False,
            "scientific_convergence_claim": False,
            "deduplication_applied": False,
            "packets_collapsed": 0,
            "controls_routing": False,
            "controls_scheduling": False,
            "compute_skips": 0,
            "value_mutated": False,
            "proof_promotion": False,
            "persistent": False,
        }
