"""Layer A SQLite → Layer B Postgres ETL for `tournament_mappool`.

Reads the Layer A `tournament_pick` table (one row per scraped pick,
including audit rows for unresolved IDs), keeps only the rows where the
osu! API v2 verifier resolved the beatmap (`verify_status IN ('match',
'mismatch')`), and upserts them into Layer B `tournament_mappool` —
the consumer-facing curated table per README §11.

Drops the following Layer A columns at projection time (they live only
in Layer A, for forensic / audit use):
    liquipedia_artist, liquipedia_title, liquipedia_difficulty,
    parser_version, source_revision, scraped_at, verified_at,
    verify_status, missing/no_id rows themselves.

Renames the `api_*` columns from Layer A to bare names in Layer B
(`api_artist` → `artist`, etc.) since after the v_status filter the
osu!-side metadata IS the metadata.

The DDL in `sql/layerB_tournament_mappool.sql` is idempotent and is
applied at the start of every run.
"""

from __future__ import annotations

import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from ..config import Settings

log = logging.getLogger(__name__)

DDL_PATH = Path(__file__).resolve().parents[3] / "sql" / "layerB_tournament_mappool.sql"

LAYER_A_QUERY = """
SELECT
    tournament_slug, round, slot,
    tournament, slot_category, slot_index, mod_set,
    api_beatmap_id, api_beatmapset_id,
    api_artist, api_title, api_difficulty, api_ranked_status,
    source_url
FROM tournament_pick
WHERE verify_status IN ('match', 'mismatch')
  AND api_beatmap_id IS NOT NULL
"""


UPSERT_SQL = """
INSERT INTO tournament_mappool (
    tournament_slug, round, slot,
    tournament, slot_category, slot_index, mod_set,
    beatmap_id, beatmapset_id, artist, title, difficulty, ranked_status,
    source_url, last_refreshed
) VALUES (
    %(tournament_slug)s, %(round)s, %(slot)s,
    %(tournament)s, %(slot_category)s, %(slot_index)s, %(mod_set)s,
    %(beatmap_id)s, %(beatmapset_id)s, %(artist)s, %(title)s,
    %(difficulty)s, %(ranked_status)s,
    %(source_url)s, %(last_refreshed)s
)
ON CONFLICT (tournament_slug, round, slot) DO UPDATE SET
    tournament    = EXCLUDED.tournament,
    slot_category = EXCLUDED.slot_category,
    slot_index    = EXCLUDED.slot_index,
    mod_set       = EXCLUDED.mod_set,
    beatmap_id    = EXCLUDED.beatmap_id,
    beatmapset_id = EXCLUDED.beatmapset_id,
    artist        = EXCLUDED.artist,
    title         = EXCLUDED.title,
    difficulty    = EXCLUDED.difficulty,
    ranked_status = EXCLUDED.ranked_status,
    source_url    = EXCLUDED.source_url,
    last_refreshed = EXCLUDED.last_refreshed
"""


def _project_row(row: sqlite3.Row, *, last_refreshed: datetime) -> dict:
    return {
        "tournament_slug": row["tournament_slug"],
        "round": row["round"],
        "slot": row["slot"],
        "tournament": row["tournament"],
        "slot_category": row["slot_category"],
        "slot_index": row["slot_index"],
        "mod_set": row["mod_set"],
        "beatmap_id": row["api_beatmap_id"],
        "beatmapset_id": row["api_beatmapset_id"],
        "artist": row["api_artist"],
        "title": row["api_title"],
        "difficulty": row["api_difficulty"],
        "ranked_status": row["api_ranked_status"],
        "source_url": row["source_url"],
        "last_refreshed": last_refreshed,
    }


def run_etl(*, settings: Settings | None = None) -> dict[str, int]:
    """Project Layer A tournament_pick → Layer B tournament_mappool.

    Returns {'projected': N, 'upserted': N}. Raises if Postgres is
    unreachable or the Layer A SQLite is missing.
    """
    settings = settings or Settings()
    sqlite_path = Path(settings.liquipedia_sqlite_path)
    if not sqlite_path.exists():
        raise FileNotFoundError(
            f"Layer A SQLite not found: {sqlite_path}. "
            "Run `all-of-osu layerA liquipedia verify-mappool` first."
        )

    # Layer A read
    conn_a = sqlite3.connect(sqlite_path)
    conn_a.row_factory = sqlite3.Row
    try:
        rows_a = conn_a.execute(LAYER_A_QUERY).fetchall()
    finally:
        conn_a.close()

    last_refreshed = datetime.now(timezone.utc)
    projected = [_project_row(r, last_refreshed=last_refreshed) for r in rows_a]
    log.info("Projected %d row(s) from Layer A.", len(projected))

    _write_to_postgres(projected, settings)

    log.info("Upserted %d row(s) into Layer B tournament_mappool.", len(projected))
    return {"projected": len(projected), "upserted": len(projected)}


def _write_to_postgres(rows: list[dict], settings: Settings) -> None:
    """Apply DDL + upsert rows. Isolated so tests can monkeypatch."""
    import psycopg  # imported lazily so the rest of the module works without it

    ddl = DDL_PATH.read_text(encoding="utf-8")
    with psycopg.connect(settings.layer_b_url) as conn:
        with conn.cursor() as cur:
            cur.execute(ddl)
            cur.executemany(UPSERT_SQL, rows)
        conn.commit()
