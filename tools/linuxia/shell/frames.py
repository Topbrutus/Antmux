# -*- coding: utf-8 -*-
"""Chargement local et déterministe des 100 images ASCII LinuxIA."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import List

SCHEMA_VERSION = "linuxia-ant-frames-v1"
CHUNK_NAMES = tuple(f"frames-{index:02d}.json" for index in range(10))


@dataclass(frozen=True)
class FramePack:
    frames: List[str]
    width: int
    height: int
    fps: float
    metadata: dict


def load_pack(module_root: Path) -> FramePack:
    asset_root = module_root / "assets"
    manifest = json.loads((asset_root / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("Schéma des images LinuxIA incompatible.")

    frames: List[str] = []
    for name in CHUNK_NAMES:
        chunk = json.loads((asset_root / name).read_text(encoding="utf-8"))
        frames.extend(str(frame) for frame in chunk)

    expected = int(manifest.get("frame_count", 0))
    if expected != 100 or len(frames) != 100:
        raise ValueError(
            f"Le paquet doit contenir exactement 100 images; reçu : {len(frames)}."
        )

    return FramePack(
        frames=frames,
        width=int(manifest["width"]),
        height=int(manifest["height"]),
        fps=float(manifest.get("fps", 20.0)),
        metadata=dict(manifest.get("metadata") or {}),
    )
