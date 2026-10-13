from __future__ import annotations

import json
import sqlite3
from pathlib import Path


class FakeQueen:
    def __init__(self) -> None:
        self.value = 0

    def to_checkpoint(self) -> dict[str, object]:
        return {"schema": "TEST-CHECKPOINT", "value": self.value, "payload": "x" * 1024}

    def protected_h256(self) -> str:
        return f"protected-{self.value}"

    def whole_h256(self) -> str:
        return f"whole-{self.value}"


def test_checkpoint_retention_is_bounded(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("ANTMUX_X72_DATA_DIR", str(tmp_path / "runtime"))

    from app.server import Persistence

    db_path = tmp_path / "retention.db"
    persistence = Persistence(db_path, max_checkpoints=32)
    queen = FakeQueen()

    for value in range(100):
        queen.value = value
        persistence.save(queen)  # type: ignore[arg-type]

    with sqlite3.connect(db_path) as db:
        count, min_id, max_id = db.execute(
            "SELECT count(*), min(id), max(id) FROM checkpoints"
        ).fetchone()
        first_json = db.execute(
            "SELECT state_json FROM checkpoints ORDER BY id ASC LIMIT 1"
        ).fetchone()[0]
        last_json = db.execute(
            "SELECT state_json FROM checkpoints ORDER BY id DESC LIMIT 1"
        ).fetchone()[0]

    assert count == 32
    assert min_id == 69
    assert max_id == 100
    assert json.loads(first_json)["value"] == 68
    assert json.loads(last_json)["value"] == 99


def test_checkpoint_retention_never_drops_below_recovery_window(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("ANTMUX_X72_DATA_DIR", str(tmp_path / "runtime2"))

    from app.server import Persistence

    persistence = Persistence(tmp_path / "minimum.db", max_checkpoints=1)
    assert persistence.max_checkpoints == 20
