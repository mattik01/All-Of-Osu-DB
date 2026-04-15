from datetime import datetime, timezone

import psycopg
from sqlalchemy import create_engine, text
from tqdm import tqdm

from .config import Settings

BATCH_LOG_INTERVAL = 10_000

SOURCE_SQL = """
SELECT
    b.checksum          AS md5,
    b.beatmap_id        AS beatmap_id,
    b.beatmapset_id     AS set_id,
    b.playmode          AS mode,
    b.approved          AS status,
    s.artist,
    s.title,
    s.creator,
    b.version,
    b.total_length      AS length_s,
    b.bpm,
    b.difficultyrating  AS star_rating,
    b.playcount,
    b.passcount,
    s.favourite_count   AS favourites,
    s.approved_date     AS approved_date
FROM osu_beatmaps b
JOIN osu_beatmapsets s ON s.beatmapset_id = b.beatmapset_id
WHERE b.approved IN (1, 2, 4)
  AND b.checksum IS NOT NULL
  AND b.deleted_at IS NULL
  AND s.deleted_at IS NULL
"""

STAGING_DDL = """
CREATE TEMP TABLE staging (
    md5            CHAR(32),
    beatmap_id     BIGINT,
    set_id         BIGINT,
    mode           SMALLINT,
    status         SMALLINT,
    artist         TEXT,
    title          TEXT,
    creator        TEXT,
    version        TEXT,
    length_s       INTEGER,
    bpm            REAL,
    star_rating    REAL,
    playcount      BIGINT,
    passcount      BIGINT,
    favourites     BIGINT,
    approved_date  TIMESTAMP
) ON COMMIT DROP;
"""

UPSERT_SQL = """
INSERT INTO beatmap_reference (
    md5, beatmap_id, set_id, mode, status,
    artist, title, creator, version,
    length_s, bpm, star_rating,
    playcount, passcount, favourites,
    approved_date, popularity_rank, last_refreshed
)
SELECT
    md5, beatmap_id, set_id, mode, status,
    artist, title, creator, version,
    length_s, bpm, star_rating,
    playcount, passcount, favourites,
    approved_date AT TIME ZONE 'UTC',
    NULL,
    %s
FROM staging
ON CONFLICT (md5) DO UPDATE SET
    beatmap_id     = EXCLUDED.beatmap_id,
    set_id         = EXCLUDED.set_id,
    mode           = EXCLUDED.mode,
    status         = EXCLUDED.status,
    artist         = EXCLUDED.artist,
    title          = EXCLUDED.title,
    creator        = EXCLUDED.creator,
    version        = EXCLUDED.version,
    length_s       = EXCLUDED.length_s,
    bpm            = EXCLUDED.bpm,
    star_rating    = EXCLUDED.star_rating,
    playcount      = EXCLUDED.playcount,
    passcount      = EXCLUDED.passcount,
    favourites     = EXCLUDED.favourites,
    approved_date  = EXCLUDED.approved_date,
    last_refreshed = EXCLUDED.last_refreshed
"""

RANK_SQL = """
UPDATE beatmap_reference br
SET popularity_rank = r.rnk
FROM (
    SELECT md5,
           rank() OVER (PARTITION BY mode ORDER BY playcount DESC) AS rnk
    FROM beatmap_reference
) r
WHERE br.md5 = r.md5;
"""


def run_etl() -> None:
    s = Settings()
    src = create_engine(s.layer_a_url)
    now = datetime.now(timezone.utc)

    print(f"Layer A: {s.layer_a_mysql_host}:{s.layer_a_mysql_port}/{s.layer_a_mysql_db}")
    print(f"Layer B: {s.layer_b_pg_host}:{s.layer_b_pg_port}/{s.layer_b_pg_db}")

    with psycopg.connect(s.layer_b_url) as pg_conn:
        with pg_conn.cursor() as cur:
            cur.execute(STAGING_DDL)

            with src.connect().execution_options(stream_results=True) as mysql_conn:
                result = mysql_conn.execute(text(SOURCE_SQL))

                pbar = tqdm(desc="  streaming", unit=" rows", mininterval=0.5)
                with cur.copy(
                    "COPY staging ("
                    "md5, beatmap_id, set_id, mode, status, "
                    "artist, title, creator, version, "
                    "length_s, bpm, star_rating, "
                    "playcount, passcount, favourites, approved_date"
                    ") FROM STDIN"
                ) as copy:
                    n = 0
                    for row in result:
                        copy.write_row(row)
                        n += 1
                        if n % BATCH_LOG_INTERVAL == 0:
                            pbar.update(BATCH_LOG_INTERVAL)
                    pbar.update(n % BATCH_LOG_INTERVAL)
                pbar.close()
                print(f"  staged {n:,} rows")

            print("  upserting into beatmap_reference …")
            cur.execute(UPSERT_SQL, (now,))
            print(f"  upsert affected {cur.rowcount:,} rows")

            print("  computing popularity_rank …")
            cur.execute(RANK_SQL)
            print(f"  ranked {cur.rowcount:,} rows")

        pg_conn.commit()

    print("ETL complete.")
