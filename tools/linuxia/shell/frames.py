# -*- coding: utf-8 -*-
"""Chargement local et déterministe des 36 images ANSI LinuxIA championnes."""

from __future__ import annotations

import base64
import json
import re
import zlib
from dataclasses import dataclass
from pathlib import Path
from typing import List

SCHEMA_VERSION = "linuxia-ant-frames-v2"
ANSI_SGR_RE = re.compile(r"\x1b\[[0-9;]*m")


@dataclass(frozen=True)
class FramePack:
    frames: List[str]
    width: int
    height: int
    fps: float
    metadata: dict


def _visible_width(value: str) -> int:
    return len(ANSI_SGR_RE.sub("", value))


def load_pack(module_root: Path) -> FramePack:
    asset_root = module_root / "assets"
    manifest = json.loads((asset_root / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("Schéma des images LinuxIA incompatible.")

    chunk_names = tuple(str(name) for name in manifest.get("chunks") or ())
    if not chunk_names:
        raise ValueError("Le manifeste LinuxIA ne contient aucune ressource d'animation.")

    raw_frames: List[str] = []
    for name in chunk_names:
        chunk = json.loads((asset_root / name).read_text(encoding="utf-8"))
        if isinstance(chunk, dict) and chunk.get("encoding") == "zlib-base64-json":
            compressed = base64.b64decode(str(chunk["data"]).encode("ascii"), validate=True)
            decoded = zlib.decompress(compressed).decode("utf-8")
            values = json.loads(decoded)
        else:
            values = chunk
        raw_frames.extend(str(frame) for frame in values)

    expected = int(manifest.get("frame_count", 0))
    if expected != 36 or len(raw_frames) != 36:
        raise ValueError(
            f"Le paquet champion doit contenir exactement 36 images; reçu : {len(raw_frames)}."
        )

    source_width = int(manifest["width"])
    source_height = int(manifest["height"])
    crop = dict(manifest.get("display_crop") or {})
    top = int(crop.get("top", 0))
    bottom = int(crop.get("bottom", source_height))
    if not (0 <= top < bottom <= source_height):
        raise ValueError("Fenêtre de cadrage LinuxIA invalide.")

    frames: List[str] = []
    for index, frame in enumerate(raw_frames):
        lines = frame.splitlines()
        if len(lines) != source_height:
            raise ValueError(
                f"Image LinuxIA {index} : {len(lines)} lignes au lieu de {source_height}."
            )
        if any(_visible_width(line) != source_width for line in lines):
            raise ValueError(f"Image LinuxIA {index} : largeur visible non conforme.")
        frames.append("\n".join(lines[top:bottom]))

    metadata = dict(manifest.get("metadata") or {})
    metadata.update(
        {
            "source_width": source_width,
            "source_height": source_height,
            "display_crop_top": top,
            "display_crop_bottom": bottom,
        }
    )
    return FramePack(
        frames=frames,
        width=source_width,
        height=bottom - top,
        fps=float(manifest.get("fps", 5.0)),
        metadata=metadata,
    )
