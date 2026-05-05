-- Layer B — `tournament_mappool` projection (Postgres).
--
-- Curated slice of the Layer A `tournament_pick` SQLite mirror.
-- Consumer-facing per README §11. Columns trimmed to the minimum a
-- downstream app cares about (which beatmap got picked, in which slot,
-- with what mod, in which tournament round). Liquipedia-side scraped
-- text fields and parser-internal audit columns are dropped — they
-- live in Layer A for forensic queries.
--
-- Source: Layer A `data/layerA/liquipedia/liquipedia.sqlite::tournament_pick`,
--   filtered to `verify_status IN ('match', 'mismatch')`. `missing` and
--   `no_id` rows are excluded (no resolvable beatmap_id, no value to a
--   downstream consumer).
--
-- Column policy per README §11: add columns freely; renames or drops
-- require a contract version bump. v1 schema below.

CREATE TABLE IF NOT EXISTS tournament_mappool (
    -- identity
    tournament_slug   text          NOT NULL,
    round             text          NOT NULL,
    slot              text          NOT NULL,

    -- semantic
    tournament        text          NOT NULL,
    slot_category     text          NOT NULL,
    slot_index        smallint,
    mod_set           text,

    -- the actual map (osu! API v2 verified existence)
    beatmap_id        bigint        NOT NULL,
    beatmapset_id     bigint,
    artist            text,
    title             text,
    difficulty        text,
    ranked_status     text,

    -- back-reference into the Liquipedia page that authored the pick
    source_url        text,

    last_refreshed    timestamptz   NOT NULL,

    PRIMARY KEY (tournament_slug, round, slot)
);

CREATE INDEX IF NOT EXISTS idx_tm_beatmap_id  ON tournament_mappool (beatmap_id);
CREATE INDEX IF NOT EXISTS idx_tm_tournament  ON tournament_mappool (tournament_slug);
CREATE INDEX IF NOT EXISTS idx_tm_mod         ON tournament_mappool (mod_set);
