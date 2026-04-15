-- Layer B v1 schema: beatmap_reference (README §8)
-- One row per beatmap difficulty. Filtered to status IN (1, 2, 4) at ETL time.

CREATE TABLE IF NOT EXISTS beatmap_reference (
    md5              CHAR(32)    PRIMARY KEY,
    beatmap_id       BIGINT      NOT NULL,
    set_id           BIGINT      NOT NULL,
    mode             SMALLINT    NOT NULL,
    status           SMALLINT    NOT NULL,
    artist           TEXT,
    title            TEXT,
    creator          TEXT,
    version          TEXT,
    length_s         INTEGER,
    bpm              REAL,
    star_rating      REAL,
    playcount        BIGINT,
    passcount        BIGINT,
    favourites       BIGINT,
    approved_date    TIMESTAMPTZ,
    popularity_rank  INTEGER,
    last_refreshed   TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS beatmap_reference_mode_popularity_idx
    ON beatmap_reference (mode, popularity_rank);
CREATE INDEX IF NOT EXISTS beatmap_reference_set_id_idx
    ON beatmap_reference (set_id);
CREATE INDEX IF NOT EXISTS beatmap_reference_beatmap_id_idx
    ON beatmap_reference (beatmap_id);
