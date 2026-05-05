"""Layer A → Layer B projection tests for `tournament_mappool`.

No live Postgres required: we exercise the *projection* logic by
inserting fixture rows into a temp Layer A SQLite and asserting that
`run_etl` would project the right rows. The Postgres write step is
faked via monkeypatching `psycopg.connect`.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from all_of_osu_db.etl.tournament_mappool import LAYER_A_QUERY, _project_row, run_etl


@pytest.fixture
def layer_a_sqlite(tmp_path: Path) -> Path:
    db = tmp_path / "layerA.sqlite"
    ddl_src = (Path(__file__).resolve().parents[1] / "sql" / "layerA_liquipedia.sql").read_text(encoding="utf-8")
    conn = sqlite3.connect(db)
    conn.executescript(ddl_src)
    rows = [
        # match — should project
        ("Osu_World_Cup/2024", "Grand Finals", "NM1", "osu! World Cup 2024", "NM", 1, "NM",
         100, 50, "Camellia", "Op Zenithfall", "FINAL MISSION",
         100, 50, "Camellia", "Operation: Zenithfall", "FINAL MISSION", "ranked",
         "match",
         "https://liquipedia.net/osu/Osu_World_Cup/2024", 60314, "plain_bullet/v1",
         "2026-05-05T13:01:22+00:00", "2026-05-05T17:30:00+00:00"),
        # mismatch — should also project (id is valid; only metadata diverged)
        ("Osu_World_Cup/2023", "Grand Finals", "TB", "osu! World Cup 2023", "TB", None, "TB",
         200, 75, "IOSYS", "Maths Class", "Streams",
         200, 75, "IOSYS", "Math Class", "Streams", "ranked",
         "mismatch",
         "https://liquipedia.net/osu/Osu_World_Cup/2023", 57000, "plain_bullet/v1",
         "2026-05-05T13:01:30+00:00", "2026-05-05T17:30:01+00:00"),
        # missing — drop
        ("Osu_World_Cup/2020", "Grand Finals", "HD1", "osu! World Cup 2020", "HD", 1, "HD",
         999999999, None, "SEPHID", "CC", "Tourney",
         None, None, None, None, None, None,
         "missing",
         "https://liquipedia.net/osu/Osu_World_Cup/2020", 55000, "plain_bullet/v1",
         "2026-05-05T13:01:31+00:00", "2026-05-05T17:30:02+00:00"),
        # no_id — drop
        ("Osu_World_Cup/2015", "Group Stage", "UNKNOWN", "osu! World Cup 2015", "UNKNOWN", None, None,
         None, None, None, None, None,
         None, None, None, None, None, None,
         "no_id",
         "https://liquipedia.net/osu/Osu_World_Cup/2015", 50000, "warning/v1",
         "2026-05-05T13:01:32+00:00", "2026-05-05T17:30:03+00:00"),
    ]
    conn.executemany(
        """
        INSERT INTO tournament_pick (
            tournament_slug, round, slot, tournament, slot_category, slot_index, mod_set,
            beatmap_id, beatmapset_id,
            liquipedia_artist, liquipedia_title, liquipedia_difficulty,
            api_beatmap_id, api_beatmapset_id,
            api_artist, api_title, api_difficulty, api_ranked_status,
            verify_status,
            source_url, source_revision, parser_version, scraped_at, verified_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    conn.commit()
    conn.close()
    return db


def test_layer_a_query_filters_to_match_and_mismatch_only(layer_a_sqlite: Path):
    conn = sqlite3.connect(layer_a_sqlite)
    conn.row_factory = sqlite3.Row
    rows = list(conn.execute(LAYER_A_QUERY))
    statuses = sorted({r["slot"] for r in rows})
    assert statuses == ["NM1", "TB"]
    assert all(r["api_beatmap_id"] is not None for r in rows)


def test_project_row_renames_api_columns_and_drops_audit_fields():
    src = {
        "tournament_slug": "T/1", "round": "R", "slot": "S",
        "tournament": "T", "slot_category": "NM", "slot_index": 1, "mod_set": "NM",
        "api_beatmap_id": 100, "api_beatmapset_id": 50,
        "api_artist": "A", "api_title": "B", "api_difficulty": "C", "api_ranked_status": "ranked",
        "source_url": "https://x/y",
    }
    from datetime import datetime, timezone
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    out = _project_row(src, last_refreshed=now)
    assert out["beatmap_id"] == 100
    assert out["artist"] == "A"
    assert out["last_refreshed"] is now
    # ensure forensic / Liquipedia-side fields are gone from the projection
    for k in ("liquipedia_artist", "verify_status", "parser_version", "source_revision",
              "scraped_at", "verified_at"):
        assert k not in out


def test_run_etl_projects_two_rows_with_mocked_postgres_writer(
    layer_a_sqlite: Path, monkeypatch: pytest.MonkeyPatch
):
    captured: dict = {}

    def fake_writer(rows, settings):
        captured["rows"] = list(rows)
        captured["settings"] = settings

    import all_of_osu_db.etl.tournament_mappool as mod
    monkeypatch.setattr(mod, "_write_to_postgres", fake_writer)

    from all_of_osu_db.config import Settings
    settings = Settings()
    settings.liquipedia_sqlite_path = layer_a_sqlite

    counts = run_etl(settings=settings)
    assert counts == {"projected": 2, "upserted": 2}
    assert len(captured["rows"]) == 2
    slots = sorted(r["slot"] for r in captured["rows"])
    assert slots == ["NM1", "TB"]
    # spot-check column rename happened
    nm1 = next(r for r in captured["rows"] if r["slot"] == "NM1")
    assert nm1["beatmap_id"] == 100
    assert nm1["title"] == "Operation: Zenithfall"
    assert "liquipedia_artist" not in nm1
    assert "verify_status" not in nm1
