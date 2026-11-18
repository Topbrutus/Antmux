"""État partagé. Les composants lisent cet objet ; ils ne se possèdent pas."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Etat:
    tic: int = 0
    phase: int = 0
    reste: int = 0
    dernier_pas: int | None = None
    cycles_sains: int = 0
    force_anomalie: bool = False
    graine_corrompue: bool = False
    piles: list[list[str]] = field(default_factory=list)
    cristaux: list[dict] = field(default_factory=list)

    def sain(self) -> bool:
        return not self.force_anomalie and not self.graine_corrompue
