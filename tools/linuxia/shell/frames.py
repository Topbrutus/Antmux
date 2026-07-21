# -*- coding: utf-8 -*-
"""Chargement local et déterministe des 100 images ASCII LinuxIA."""

from __future__ import annotations

import base64
import json
import zlib
from dataclasses import dataclass
from pathlib import Path
from typing import List

SCHEMA_VERSION = "linuxia-ant-frames-v1"
ASSET_NAMES = (
    "frames-01.b85",
    "frames-02.b85",
    "frames-03.b85",
    "frames-04.b85",
)


@dataclass(frozen=True)
class FramePack:
    frames: List[str]
    width: int
    height: int
    fps: float
    metadata: dict


def load_pack(module_root: Path) -> FramePack:
    asset_root = module_root / "assets"
    encoded = "".join(
        (asset_root / name).read_text(encoding="ascii").strip()
        for name in ASSET_NAMES
    )
    data = json.loads(zlib.decompress(base64.b85decode(encoded)).decode("utf-8"))
    if data.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("Schéma des images LinuxIA incompatible.")

    frames = list(data.get("frames") or [])
    if len(frames) != 100:
        raise ValueError(
            f"Le paquet doit contenir exactement 100 images; reçu : {len(frames)}."
        )

    return FramePack(
        frames=frames,
        width=int(data["width"]),
        height=int(data["height"]),
        fps=float(data.get("fps", 20.0)),
        metadata=dict(data.get("metadata") or {}),
    )
