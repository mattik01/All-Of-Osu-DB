"""Loader test: verified-CSV → Layer A SQLite tournament_pick.

No network. Builds a 4-row fixture covering all four verify_status values
and asserts that every row lands, columns are mapped correctly, and the
load is idempotent.
"""

from __future__ import annotations

import csv
import sqlite3
from pathlib import Path

import pytest

from all_of_osu_db.layerA.liquipedia_load import load_to_sqlite

FIXTURE_HEADER = [
    "tournament", "tournament_slug", "round", "slot", "slot_category", "slot_index",
    "mod_set", "beatmap_artist", "beatmap_title", "beatmap_difficulty", "beatmap_id",
    "beatmapset_id", "source_url", "source_revision", "parser_version", "scraped_at",
    "verified_status", "verified_beatmap_id", "verified_beatmapset_id", "verified_artist",
    "verified_title", "verified_difficulty", "verified_ranked_status", "verified_at",
]

FIXTURE_ROWS = [
    # match — Liquipedia ID resolves and metadata agrees
    ["osu! World Cup 2024", "Osu_World_Cup/2024", "Grand Finals", "NM1",
     "NM", "1", "NM", "Camellia", "Operation Zenithfall", "FINAL MISSION",
     "100", "50", "https://liquipedia.net/osu/Osu_World_Cup/2024", "60314",
     "plain_bullet/v1", "2026-05-05T13:01:22+00:00",
     "match", "100", "50", "Camellia", "Operation: Zenithfall", "FINAL MISSION",
     "ranked", "2026-05-05T17:30:00+00:00"],
    # mismatch — id resolves but metadata diverged (typical post-tournament rename)
    ["osu! World Cup 2023", "Osu_World_Cup/2023", "Grand Finals", "TB",
     "TB", "", "TB", "IOSYS", "Cirno's Perfect Maths Class", "Streams",
     "200", "75", "https://liquipedia.net/osu/Osu_World_Cup/2023", "57000",
     "plain_bullet/v1", "2026-05-05T13:01:30+00:00",
     "mismatch", "200", "75", "IOSYS", "Cirno's Perfect Math Class", "Streams",
     "ranked", "2026-05-05T17:30:01+00:00"],
    # missing — id was advertised but API returned nothing
    ["osu! World Cup 2020", "Osu_World_Cup/2020", "Grand Finals", "HD1",
     "HD", "1", "HD", "SEPHID", "Critical Cannonball", "Limit Break (Tourney Ver.)",
     "999999999", "", "https://liquipedia.net/osu/Osu_World_Cup/2020", "55000",
     "plain_bullet/v1", "2026-05-05T13:01:31+00:00",
     "missing", "", "", "", "", "", "", "2026-05-05T17:30:02+00:00"],
    # no_id — parser couldn't capture an id (e.g. UNKNOWN warning row)
    ["osu! World Cup 2015", "Osu_World_Cup/2015", "Group Stage", "UNKNOWN",
     "UNKNOWN", "", "", "", "", "",
     "", "", "https://liquipedia.net/osu/Osu_World_Cup/2015", "50000",
     "warning/v1", "2026-05-05T13:01:32+00:00",
     "no_id", "", "", "", "", "", "", "2026-05-05T17:30:03+00:00"],
]


@pytest.fixture
def fixture_csv(tmp_path: Path) -> Path:
    csv_path = tmp_path / "verified.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(FIXTURE_HEADER)
        writer.writerows(FIXTURE_ROWS)
    return csv_path


def _connect(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def test_all_four_rows_land_with_correct_verify_status(fixture_csv: Path, tmp_path: Path):
    db_path = tmp_path / "x.sqlite"
    counts = load_to_sqlite(input_path=fixture_csv, output_path=db_path)
    assert counts["total"] == 4
    assert counts["match"] == 1
    assert counts["mismatch"] == 1
    assert counts["missing"] == 1
    assert counts["no_id"] == 1

    with _connect(db_path) as conn:
        rows = list(conn.execute("SELECT * FROM tournament_pick"))
    assert len(rows) == 4
    statuses = sorted(r["verify_status"] for r in rows)
    assert statuses == ["match", "mismatch", "missing", "no_id"]


def test_liquipedia_columns_preserved_verbatim(fixture_csv: Path, tmp_path: Path):
    db_path = tmp_path / "x.sqlite"
    load_to_sqlite(input_path=fixture_csv, output_path=db_path)
    with _connect(db_path) as conn:
        match_row = conn.execute(
            "SELECT * FROM tournament_pick WHERE verify_status = 'match'"
        ).fetchone()
    assert match_row["liquipedia_artist"] == "Camellia"
    assert match_row["liquipedia_title"] == "Operation Zenithfall"
    assert match_row["liquipedia_difficulty"] == "FINAL MISSION"
    assert match_row["api_title"] == "Operation: Zenithfall"
    assert match_row["beatmap_id"] == 100
    assert match_row["api_beatmap_id"] == 100


def test_missing_and_no_id_rows_have_null_api_columns(fixture_csv: Path, tmp_path: Path):
    db_path = tmp_path / "x.sqlite"
    load_to_sqlite(input_path=fixture_csv, output_path=db_path)
    with _connect(db_path) as conn:
        for status in ("missing", "no_id"):
            row = conn.execute(
                "SELECT * FROM tournament_pick WHERE verify_status = ?", (status,)
            ).fetchone()
            assert row["api_beatmap_id"] is None
            assert row["api_artist"] is None
            assert row["api_ranked_status"] is None


def test_load_is_idempotent(fixture_csv: Path, tmp_path: Path):
    db_path = tmp_path / "x.sqlite"
    load_to_sqlite(input_path=fixture_csv, output_path=db_path)
    load_to_sqlite(input_path=fixture_csv, output_path=db_path)
    with _connect(db_path) as conn:
        n = conn.execute("SELECT count(*) FROM tournament_pick").fetchone()[0]
    assert n == 4


def test_query_time_filter_for_valid_only(fixture_csv: Path, tmp_path: Path):
    db_path = tmp_path / "x.sqlite"
    load_to_sqlite(input_path=fixture_csv, output_path=db_path)
    with _connect(db_path) as conn:
        n_valid = conn.execute(
            "SELECT count(*) FROM tournament_pick WHERE verify_status IN ('match', 'mismatch')"
        ).fetchone()[0]
    assert n_valid == 2


def test_indexes_exist(fixture_csv: Path, tmp_path: Path):
    db_path = tmp_path / "x.sqlite"
    load_to_sqlite(input_path=fixture_csv, output_path=db_path)
    with _connect(db_path) as conn:
        idx = {r["name"] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='tournament_pick'"
        )}
    expected = {
        "idx_tp_beatmap_id", "idx_tp_api_bid", "idx_tp_tournament",
        "idx_tp_mod", "idx_tp_verify_status",
    }
    assert expected <= idx
