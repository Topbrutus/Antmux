from __future__ import annotations

import os
import tempfile
from pathlib import Path

from fastapi import HTTPException


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="antmux-journal-test-") as tmp:
        os.environ["ANTMUX_X72_DATA_DIR"] = tmp

        from app import public_journal as journal

        store = journal.JournalStore(Path(tmp))
        base = 1_800_000_000.0
        original_time = journal.time.time

        try:
            payload = journal.VisitorSubmission(
                kind="MESSAGE",
                title="Bonjour ANTMUX",
                body="Petite fourmi, chante ta symphonie.",
                name="Visiteur test",
                email="visitor@example.test",
                website="",
            )

            journal.time.time = lambda: base
            first = store.create_submission(payload, "203.0.113.10")
            assert first["status"] == "PENDING"
            assert first["emoji_open"] == "🐜✉️"
            assert first["emoji_close"] == "✉️🐜"
            assert first["remaining_after_this"] == 2

            ant = first["ant"]
            assert ant["ant_id"] == first["id"]
            assert ant["schema"] == "ANTMUX-ANT-LIFECYCLE-v1"
            assert ant["state"] == "LIFE_CLOCK_ASSIGNED"
            assert ant["entry_policy"] == "OPEN_TO_ALL"
            assert ant["launch_phrase"] == "Christ ou pas Christ, j’y vais."
            assert ant["project_soul"]["meaning"] == "software identity + memory + timing + lineage"
            assert ant["baggage"]["language_triplet"] == "🔤🎧〰️"
            assert ant["baggage"]["symbolic_song"].startswith("◉→")
            assert ant["baggage"]["symbolic_song"].endswith("→♡")
            assert "email" not in ant["baggage"]
            assert ant["parazone_port"] == "READY_TO_CONNECT"

            # Queen cannot crystallize an ant before Parazone has completed
            # the song + central language transfer and the ant is an egg.
            try:
                store.crystallize_ant(first["id"])
            except HTTPException as exc:
                assert exc.status_code == 409
            else:
                raise AssertionError("premature crystallization must be rejected")

            journal.time.time = lambda: base + 10
            egg = store.confirm_parazone(first["id"])
            assert egg["state"] == "DORMITORY_EGG"
            assert egg["parazone_port"] == "TRANSFER_CONFIRMED"
            assert next(p for p in egg["lifecycle"] if p["state"] == "ANT_SONG")["status"] == "DONE"
            assert next(p for p in egg["lifecycle"] if p["state"] == "DORMITORY_EGG")["status"] == "ACTIVE"

            journal.time.time = lambda: base + 20
            crystal = store.crystallize_ant(first["id"])
            assert crystal["state"] == "CRYSTALLIZED_READY"
            assert crystal["crystal"]["status"] == "READY"
            assert crystal["crystal"]["resume"] == "🥚→👑→💎→🐜"

            # Pending submissions must never leak to the public feed.
            assert store.public_posts(40) == []

            journal.time.time = lambda: base + 121
            second = store.create_submission(payload, "203.0.113.10")
            assert second["remaining_after_this"] == 1

            journal.time.time = lambda: base + 242
            third = store.create_submission(payload, "203.0.113.10")
            assert third["remaining_after_this"] == 0

            journal.time.time = lambda: base + 363
            try:
                store.create_submission(payload, "203.0.113.10")
            except HTTPException as exc:
                assert exc.status_code == 429
                assert "3 messages" in str(exc.detail)
            else:
                raise AssertionError("fourth submission should be rate-limited")

            # Publishing a moderated entry exposes only public-safe fields.
            journal.time.time = lambda: base + 500
            moderated = store.moderate(first["id"], "PUBLISHED")
            assert moderated["status"] == "PUBLISHED"
            public = store.public_posts(40)
            assert len(public) == 1
            assert public[0]["id"] == first["id"]
            assert "reply_email" not in public[0]
            assert "email_hash" not in public[0]
            assert "ip_hash" not in public[0]

            # Admin secret is enforced without ever printing it.
            try:
                store.require_admin("Bearer wrong-token")
            except HTTPException as exc:
                assert exc.status_code == 401
            else:
                raise AssertionError("wrong admin token must fail")
            token = store.admin_token_path.read_text(encoding="utf-8").strip()
            store.require_admin("Bearer " + token)

            # Honeypot must reject bot-like submissions.
            bot = journal.VisitorSubmission(
                kind="JOB",
                title="Bot",
                body="Should not pass",
                name="bot",
                email="bot@example.test",
                website="https://spam.invalid",
            )
            journal.time.time = lambda: base + 700
            try:
                store.create_submission(bot, "203.0.113.55")
            except HTTPException as exc:
                assert exc.status_code == 400
            else:
                raise AssertionError("honeypot submission should fail")

            # Official journal entries publish immediately.
            official = journal.OfficialPost(
                kind="JOURNAL",
                title="Journal système",
                body="🐜📓 Test officiel. 📓🐜",
                author_name="ANTMUX",
                emoji_index="🐜📓🧾📚",
            )
            journal.time.time = lambda: base + 800
            result = store.create_official(official)
            assert result["status"] == "PUBLISHED"
            assert len(store.public_posts(40)) == 2

            print("PUBLIC_JOURNAL_RATE_LIMIT=PASS")
            print("PUBLIC_JOURNAL_PRIVACY=PASS")
            print("PUBLIC_JOURNAL_MODERATION=PASS")
            print("PUBLIC_JOURNAL_ADMIN_GATE=PASS")
            print("PUBLIC_JOURNAL_EMOJI_FRAMING=PASS")
            print("PUBLIC_JOURNAL_ANT_LIFECYCLE=PASS")
            print("PUBLIC_JOURNAL_PARAZONE_GATE=PASS")
            print("PUBLIC_JOURNAL_QUEEN_CRYSTALLIZATION=PASS")
        finally:
            journal.time.time = original_time


if __name__ == "__main__":
    main()
