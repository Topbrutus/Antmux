from __future__ import annotations

import hashlib
import hmac
import os
import re
import secrets
import sqlite3
import time
import uuid
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel


ROUTER_PREFIX = "/api/journal"
PUBLIC_KINDS = {
    "JOURNAL": ("🐜📓", "📓🐜", "📓"),
    "MESSAGE": ("🐜✉️", "✉️🐜", "✉️"),
    "JOB": ("🐜💼", "💼🐜", "💼"),
    "PUBLIC_NOTE": ("🐜📣", "📣🐜", "📣"),
}
VISITOR_KINDS = {"MESSAGE", "JOB"}
MAX_POSTS_PER_WINDOW = 3
WINDOW_SECONDS = 24 * 60 * 60
MIN_DELAY_SECONDS = 120
MAX_TITLE_CHARS = 160
MAX_BODY_CHARS = 3000
MAX_NAME_CHARS = 80
MAX_EMAIL_CHARS = 254
MAX_PUBLIC_LIMIT = 100


class VisitorSubmission(BaseModel):
    kind: str = "MESSAGE"
    title: str
    body: str
    name: str = ""
    email: str
    website: str = ""  # honeypot: human visitors leave this empty


class OfficialPost(BaseModel):
    kind: str = "JOURNAL"
    title: str
    body: str
    author_name: str = "ANTMUX"
    emoji_index: str = ""


class ModerationRequest(BaseModel):
    status: str


def utc_iso(timestamp: float) -> str:
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat().replace("+00:00", "Z")


def normalize_text(value: str, max_chars: int, *, required: bool = False) -> str:
    clean = " ".join(str(value or "").replace("\x00", "").split())
    if required and not clean:
        raise HTTPException(status_code=422, detail="required text is empty")
    if len(clean) > max_chars:
        raise HTTPException(status_code=422, detail=f"text exceeds {max_chars} characters")
    return clean


def normalize_body(value: str) -> str:
    clean = str(value or "").replace("\x00", "").replace("\r\n", "\n").replace("\r", "\n").strip()
    if not clean:
        raise HTTPException(status_code=422, detail="message body is empty")
    if len(clean) > MAX_BODY_CHARS:
        raise HTTPException(status_code=422, detail=f"message exceeds {MAX_BODY_CHARS} characters")
    return clean


def normalize_email(value: str) -> str:
    email = normalize_text(value, MAX_EMAIL_CHARS, required=True).lower()
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        raise HTTPException(status_code=422, detail="invalid email")
    return email


def request_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip()[:128]
    real_ip = request.headers.get("x-real-ip", "").strip()
    if real_ip:
        return real_ip[:128]
    return (request.client.host if request.client else "unknown")[:128]


class JournalStore:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.data_dir / "public-journal.db"
        self.salt_path = self.data_dir / "journal-hash-salt"
        self.admin_token_path = self.data_dir / "journal-admin-token"
        self.contact_path = self.data_dir / "public-contact-email.txt"
        self._ensure_secret(self.salt_path, 32)
        self._ensure_secret(self.admin_token_path, 32)
        self._init_db()

    @staticmethod
    def _ensure_secret(path: Path, nbytes: int) -> None:
        if path.exists() and path.stat().st_size > 16:
            return
        value = secrets.token_hex(nbytes)
        path.write_text(value + "\n", encoding="utf-8")
        try:
            os.chmod(path, 0o600)
        except OSError:
            pass

    def _secret(self, path: Path) -> str:
        return path.read_text(encoding="utf-8").strip()

    def _hash(self, value: str) -> str:
        salt = self._secret(self.salt_path)
        return hashlib.sha256(f"{salt}|{value}".encode("utf-8")).hexdigest()

    def _init_db(self) -> None:
        with closing(sqlite3.connect(self.db_path)) as db:
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS posts (
                    id TEXT PRIMARY KEY,
                    kind TEXT NOT NULL,
                    title TEXT NOT NULL,
                    body TEXT NOT NULL,
                    author_name TEXT NOT NULL,
                    reply_email TEXT NOT NULL,
                    status TEXT NOT NULL,
                    source TEXT NOT NULL,
                    emoji_open TEXT NOT NULL,
                    emoji_close TEXT NOT NULL,
                    emoji_index TEXT NOT NULL,
                    ip_hash TEXT NOT NULL,
                    email_hash TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    published_at REAL
                )
                """
            )
            db.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_posts_status_time
                ON posts(status, published_at DESC, created_at DESC)
                """
            )
            db.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_posts_ip_time
                ON posts(ip_hash, created_at DESC)
                """
            )
            db.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_posts_email_time
                ON posts(email_hash, created_at DESC)
                """
            )
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS audit (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    post_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    detail TEXT NOT NULL,
                    created_at REAL NOT NULL
                )
                """
            )
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS ants (
                    id TEXT PRIMARY KEY,
                    post_id TEXT NOT NULL UNIQUE,
                    state TEXT NOT NULL,
                    receipt_json TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL
                )
                """
            )
            db.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_ants_state_time
                ON ants(state, updated_at DESC)
                """
            )
            db.commit()

    def public_contact_email(self) -> str:
        env_value = os.environ.get("ANTMUX_PUBLIC_CONTACT_EMAIL", "").strip()
        candidate = env_value
        if not candidate and self.contact_path.exists():
            candidate = self.contact_path.read_text(encoding="utf-8").strip()
        if not candidate:
            return ""
        try:
            return normalize_email(candidate)
        except HTTPException:
            return ""

    def require_admin(self, supplied_authorization: str) -> None:
        expected = self._secret(self.admin_token_path)
        supplied = supplied_authorization.strip()
        if supplied.startswith("Bearer "):
            supplied = supplied[7:].strip()
        if not supplied or not hmac.compare_digest(supplied, expected):
            raise HTTPException(status_code=401, detail="unauthorized")

    def _rate_check(self, db: sqlite3.Connection, ip_hash: str, email_hash: str, now: float) -> int:
        cutoff = now - WINDOW_SECONDS
        ip_rows = db.execute(
            "SELECT created_at FROM posts WHERE ip_hash=? AND created_at>=? ORDER BY created_at DESC",
            (ip_hash, cutoff),
        ).fetchall()
        email_rows = db.execute(
            "SELECT created_at FROM posts WHERE email_hash=? AND created_at>=? ORDER BY created_at DESC",
            (email_hash, cutoff),
        ).fetchall()

        if ip_rows and now - float(ip_rows[0][0]) < MIN_DELAY_SECONDS:
            raise HTTPException(status_code=429, detail=f"wait {MIN_DELAY_SECONDS} seconds between messages")
        if email_rows and now - float(email_rows[0][0]) < MIN_DELAY_SECONDS:
            raise HTTPException(status_code=429, detail=f"wait {MIN_DELAY_SECONDS} seconds between messages")

        used = max(len(ip_rows), len(email_rows))
        if used >= MAX_POSTS_PER_WINDOW:
            raise HTTPException(status_code=429, detail="limit reached: 3 messages per rolling 24 hours")
        return MAX_POSTS_PER_WINDOW - used

    def create_submission(self, payload: VisitorSubmission, ip: str) -> dict[str, Any]:
        if payload.website.strip():
            raise HTTPException(status_code=400, detail="invalid submission")

        kind = payload.kind.strip().upper()
        if kind not in VISITOR_KINDS:
            raise HTTPException(status_code=422, detail="visitor kind must be MESSAGE or JOB")

        title = normalize_text(payload.title, MAX_TITLE_CHARS, required=True)
        body = normalize_body(payload.body)
        name = normalize_text(payload.name, MAX_NAME_CHARS) or "Visiteur"
        email = normalize_email(payload.email)
        now = time.time()
        ip_hash = self._hash(ip)
        email_hash = self._hash(email)
        post_id = f"ANT-{uuid.uuid4().hex[:12].upper()}"
        emoji_open, emoji_close, core = PUBLIC_KINDS[kind]
        emoji_index = f"🐜{core}📚"
        ant_receipt = build_ant_receipt(post_id, title, body, now)
        with closing(sqlite3.connect(self.db_path)) as db:
            # BEGIN IMMEDIATE serializes the quota check + insert, preventing
            # concurrent submissions from racing past the 3-per-window limit.
            db.execute("BEGIN IMMEDIATE")
            remaining_before = self._rate_check(db, ip_hash, email_hash, now)
            db.execute(
                """
                INSERT INTO posts(
                    id, kind, title, body, author_name, reply_email, status, source,
                    emoji_open, emoji_close, emoji_index, ip_hash, email_hash,
                    created_at, published_at
                ) VALUES (?, ?, ?, ?, ?, ?, 'PENDING', 'VISITOR', ?, ?, ?, ?, ?, ?, NULL)
                """,
                (
                    post_id, kind, title, body, name, email,
                    emoji_open, emoji_close, emoji_index, ip_hash, email_hash, now,
                ),
            )
            db.execute(
                """
                INSERT INTO ants(id, post_id, state, receipt_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    post_id,
                    post_id,
                    ant_receipt["state"],
                    json.dumps(ant_receipt, ensure_ascii=False, separators=(",", ":")),
                    now,
                    now,
                ),
            )
            db.execute(
                "INSERT INTO audit(post_id, action, detail, created_at) VALUES (?, 'SUBMITTED', 'visitor pending moderation', ?)",
                (post_id, now),
            )
            db.execute(
                "INSERT INTO audit(post_id, action, detail, created_at) VALUES (?, 'ANT_BORN', 'ant lifecycle created; Life Clock state assigned; Parazone port pending', ?)",
                (post_id, now),
            )
            db.commit()

        return {
            "ok": True,
            "id": post_id,
            "status": "PENDING",
            "emoji_open": emoji_open,
            "emoji_close": emoji_close,
            "remaining_after_this": max(0, remaining_before - 1),
            "ant": ant_receipt,
        }

    def _load_ant(self, ant_id: str) -> dict[str, Any]:
        ant_id = normalize_text(ant_id, 64, required=True)
        with closing(sqlite3.connect(self.db_path)) as db:
            row = db.execute(
                "SELECT receipt_json FROM ants WHERE id=?",
                (ant_id,),
            ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="ant not found")
        return json.loads(str(row[0]))

    def _save_ant(self, ant_id: str, receipt: dict[str, Any], action: str, detail: str) -> dict[str, Any]:
        now = time.time()
        with closing(sqlite3.connect(self.db_path)) as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT id FROM ants WHERE id=?", (ant_id,)).fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="ant not found")
            db.execute(
                "UPDATE ants SET state=?, receipt_json=?, updated_at=? WHERE id=?",
                (
                    receipt["state"],
                    json.dumps(receipt, ensure_ascii=False, separators=(",", ":")),
                    now,
                    ant_id,
                ),
            )
            db.execute(
                "INSERT INTO audit(post_id, action, detail, created_at) VALUES (?, ?, ?, ?)",
                (ant_id, action, detail, now),
            )
            db.commit()
        return receipt

    def confirm_parazone(self, ant_id: str) -> dict[str, Any]:
        current = self._load_ant(ant_id)
        try:
            updated = parazone_complete(current)
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return self._save_ant(
            ant_id,
            updated,
            "PARAZONE_TRANSFER_CONFIRMED",
            "song + language ingress confirmed; ant moved to dormitory egg",
        )

    def crystallize_ant(self, ant_id: str) -> dict[str, Any]:
        current = self._load_ant(ant_id)
        try:
            updated = queen_crystallize(current)
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return self._save_ant(
            ant_id,
            updated,
            "QUEEN_CRYSTALLIZED",
            "dormitory egg crystallized and ready for a new cycle",
        )

    def create_official(self, payload: OfficialPost) -> dict[str, Any]:
        kind = payload.kind.strip().upper()
        if kind not in {"JOURNAL", "PUBLIC_NOTE"}:
            raise HTTPException(status_code=422, detail="official kind must be JOURNAL or PUBLIC_NOTE")
        title = normalize_text(payload.title, MAX_TITLE_CHARS, required=True)
        body = normalize_body(payload.body)
        author = normalize_text(payload.author_name, MAX_NAME_CHARS) or "ANTMUX"
        emoji_index = normalize_text(payload.emoji_index, 96) or ("🐜📓📚" if kind == "JOURNAL" else "🐜📣📚")
        now = time.time()
        post_id = f"ANT-{uuid.uuid4().hex[:12].upper()}"
        emoji_open, emoji_close, _ = PUBLIC_KINDS[kind]
        with closing(sqlite3.connect(self.db_path)) as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute(
                """
                INSERT INTO posts(
                    id, kind, title, body, author_name, reply_email, status, source,
                    emoji_open, emoji_close, emoji_index, ip_hash, email_hash,
                    created_at, published_at
                ) VALUES (?, ?, ?, ?, ?, '', 'PUBLISHED', 'ANTMUX', ?, ?, ?, '', '', ?, ?)
                """,
                (post_id, kind, title, body, author, emoji_open, emoji_close, emoji_index, now, now),
            )
            db.execute(
                "INSERT INTO audit(post_id, action, detail, created_at) VALUES (?, 'PUBLISHED', 'official ANTMUX entry', ?)",
                (post_id, now),
            )
            db.commit()
        return {"ok": True, "id": post_id, "status": "PUBLISHED"}

    def moderate(self, post_id: str, status: str) -> dict[str, Any]:
        post_id = normalize_text(post_id, 64, required=True)
        status = status.strip().upper()
        if status not in {"PUBLISHED", "REJECTED"}:
            raise HTTPException(status_code=422, detail="status must be PUBLISHED or REJECTED")
        now = time.time()
        with closing(sqlite3.connect(self.db_path)) as db:
            row = db.execute("SELECT id FROM posts WHERE id=?", (post_id,)).fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="post not found")
            published_at = now if status == "PUBLISHED" else None
            db.execute(
                "UPDATE posts SET status=?, published_at=? WHERE id=?",
                (status, published_at, post_id),
            )
            db.execute(
                "INSERT INTO audit(post_id, action, detail, created_at) VALUES (?, ?, 'moderation decision', ?)",
                (post_id, status, now),
            )
            db.commit()
        return {"ok": True, "id": post_id, "status": status}

    def public_posts(self, limit: int) -> list[dict[str, Any]]:
        safe_limit = max(1, min(MAX_PUBLIC_LIMIT, int(limit)))
        with closing(sqlite3.connect(self.db_path)) as db:
            rows = db.execute(
                """
                SELECT id, kind, title, body, author_name, source,
                       emoji_open, emoji_close, emoji_index, created_at, published_at
                FROM posts
                WHERE status='PUBLISHED'
                ORDER BY COALESCE(published_at, created_at) DESC
                LIMIT ?
                """,
                (safe_limit,),
            ).fetchall()

        return [
            {
                "id": row[0],
                "kind": row[1],
                "title": row[2],
                "body": row[3],
                "author_name": row[4],
                "source": row[5],
                "emoji_open": row[6],
                "emoji_close": row[7],
                "emoji_index": row[8],
                "created_at": utc_iso(float(row[9])),
                "published_at": utc_iso(float(row[10] or row[9])),
            }
            for row in rows
        ]


DATA_DIR = Path(os.environ.get("ANTMUX_X72_DATA_DIR", "/home/rob/antmux-x72-queen/data"))
store = JournalStore(DATA_DIR)
router = APIRouter(prefix=ROUTER_PREFIX, tags=["public-journal"])


@router.get("/config")
async def journal_config() -> dict[str, Any]:
    return {
        "schema": "ANTMUX-PUBLIC-JOURNAL-v1",
        "title": "🐜 Fourmilière publique",
        "max_posts_per_24h": MAX_POSTS_PER_WINDOW,
        "min_delay_seconds": MIN_DELAY_SECONDS,
        "visitor_types": [
            {"id": "MESSAGE", "open": "🐜✉️", "close": "✉️🐜", "label": "Message"},
            {"id": "JOB", "open": "🐜💼", "close": "💼🐜", "label": "Job / proposition"},
        ],
        "contact_email": store.public_contact_email(),
        "entry_policy": ENTRY_POLICY,
        "launch_phrase": LAUNCH_PHRASE,
        "ant_lifecycle_schema": "ANTMUX-ANT-LIFECYCLE-v1",
        "parazone_port": "READY_TO_CONNECT",
        "privacy": "Les courriels des visiteurs restent privés et ne sont jamais renvoyés par l'API publique.",
    }


@router.get("/public")
async def journal_public(limit: int = 40) -> dict[str, Any]:
    return {
        "schema": "ANTMUX-PUBLIC-JOURNAL-v1",
        "posts": store.public_posts(limit),
    }


@router.post("/submit")
async def journal_submit(payload: VisitorSubmission, request: Request) -> dict[str, Any]:
    return store.create_submission(payload, request_ip(request))


@router.post("/admin/publish")
async def journal_admin_publish(payload: OfficialPost, request: Request) -> dict[str, Any]:
    store.require_admin(request.headers.get("authorization", ""))
    return store.create_official(payload)


@router.post("/admin/moderate/{post_id}")
async def journal_admin_moderate(post_id: str, payload: ModerationRequest, request: Request) -> dict[str, Any]:
    store.require_admin(request.headers.get("authorization", ""))
    return store.moderate(post_id, payload.status)


@router.post("/admin/ant/{ant_id}/parazone-complete")
async def journal_admin_parazone_complete(ant_id: str, request: Request) -> dict[str, Any]:
    store.require_admin(request.headers.get("authorization", ""))
    return {"ok": True, "ant": store.confirm_parazone(ant_id)}


@router.post("/admin/ant/{ant_id}/crystallize")
async def journal_admin_crystallize_ant(ant_id: str, request: Request) -> dict[str, Any]:
    store.require_admin(request.headers.get("authorization", ""))
    return {"ok": True, "ant": store.crystallize_ant(ant_id)}
