"""Layer A SQLite sink for the verified Liquipedia mappool CSV.

Reads `owc_mappool_verified.csv` and bulk-loads every row into a local
SQLite file at `Settings.liquipedia_sqlite_path`. **No row filtering** —
`match`, `mismatch`, `missing`, and `no_id` rows all land. Curation /
filtering happens at Layer B and at consumer query time.

The schema lives in `sql/layerA_liquipedia.sql` (idempotent DDL with
`IF NOT EXISTS`). Each load fully replaces the table contents
(`DELETE FROM tournament_pick`) so the SQLite stays a faithful mirror of
the latest verifier output rather than accumulating drift.
"""

from __future__ import annotations

import csv
import logging
import sqlite3
from collections import Counter
from pathlib import Path

from ..config import Settings

log = logging.getLogger(__name__)

DDL_PATH = Path(__file__).resolve().parents[3] / "sql" / "layerA_liquipedia.sql"

INSERT_SQL = """
INSERT INTO tournament_pick (
    tournament_slug, round, slot,
    tournament, slot_category, slot_index, mod_set,
    beatmap_id, beatmapset_id,
    liquipedia_artist, liquipedia_title, liquipedia_difficulty,
    api_beatmap_id, api_beatmapset_id,
    api_artist, api_title, api_difficulty, api_ranked_status,
    verify_status,
    source_url, source_revision, parser_version, scraped_at, verified_at
) VALUES (
    :tournament_slug, :round, :slot,
    :tournament, :slot_category, :slot_index, :mod_set,
    :beatmap_id, :beatmapset_id,
    :liquipedia_artist, :liquipedia_title, :liquipedia_difficulty,
    :api_beatmap_id, :api_beatmapset_id,
    :api_artist, :api_title, :api_difficulty, :api_ranked_status,
    :verify_status,
    :source_url, :source_revision, :parser_version, :scraped_at, :verified_at
)
"""


def _empty_to_none(value: str | None) -> str | None:
    if value is None or value == "":
        return None
    return value


def _to_int(value: str | None) -> int | None:
    v = _empty_to_none(value)
    if v is None:
        return None
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def _csv_to_row(r: dict) -> dict:
    """Map a verified-CSV row to the SQLite parameter dict.

    Liquipedia-side columns from the original scrape become `liquipedia_*`;
    verifier-side `verified_*` columns become `api_*`. Empty strings → NULL.
    """
    return {
        "tournament_slug": r.get("tournament_slug"),
        "round": r.get("round"),
        "slot": r.get("slot"),
        "tournament": r.get("tournament"),
        "slot_category": r.get("slot_category"),
        "slot_index": _to_int(r.get("slot_index")),
        "mod_set": _empty_to_none(r.get("mod_set")),
        "beatmap_id": _to_int(r.get("beatmap_id")),
        "beatmapset_id": _to_int(r.get("beatmapset_id")),
        "liquipedia_artist": _empty_to_none(r.get("beatmap_artist")),
        "liquipedia_title": _empty_to_none(r.get("beatmap_title")),
        "liquipedia_difficulty": _empty_to_none(r.get("beatmap_difficulty")),
        "api_beatmap_id": _to_int(r.get("verified_beatmap_id")),
        "api_beatmapset_id": _to_int(r.get("verified_beatmapset_id")),
        "api_artist": _empty_to_none(r.get("verified_artist")),
        "api_title": _empty_to_none(r.get("verified_title")),
        "api_difficulty": _empty_to_none(r.get("verified_difficulty")),
        "api_ranked_status": _empty_to_none(r.get("verified_ranked_status")),
        "verify_status": r.get("verified_status") or "no_id",
        "source_url": _empty_to_none(r.get("source_url")),
        "source_revision": _to_int(r.get("source_revision")),
        "parser_version": _empty_to_none(r.get("parser_version")),
        "scraped_at": _empty_to_none(r.get("scraped_at")),
        "verified_at": _empty_to_none(r.get("verified_at")),
    }


def load_to_sqlite(
    *,
    settings: Settings | None = None,
    input_path: Path | None = None,
    output_path: Path | None = None,
    ddl_path: Path | None = None,
) -> dict[str, int]:
    """Read the verified CSV, recreate the Layer A SQLite table, return counts.

    Returns a dict with `total` and one key per `verify_status` value.
    """
    settings = settings or Settings()
    in_path = input_path or (Path(settings.liquipedia_output_dir) / "owc_mappool_verified.csv")
    out_path = output_path or Path(settings.liquipedia_sqlite_path)
    ddl = (ddl_path or DDL_PATH).read_text(encoding="utf-8")

    out_path.parent.mkdir(parents=True, exist_ok=True)

    with in_path.open(encoding="utf-8") as fh:
        rows = [_csv_to_row(r) for r in csv.DictReader(fh)]

    if not rows:
        raise RuntimeError(f"No rows in {in_path}")

    conn = sqlite3.connect(out_path)
    try:
        conn.executescript(ddl)
        conn.execute("DELETE FROM tournament_pick")
        conn.executemany(INSERT_SQL, rows)
        conn.commit()
    finally:
        conn.close()

    counts = Counter(r["verify_status"] for r in rows)
    counts["total"] = len(rows)
    log.info("Loaded %d rows into %s; status: %s", len(rows), out_path, dict(counts))
    return dict(counts)
