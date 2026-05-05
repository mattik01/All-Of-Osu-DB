-- Layer A — Liquipedia tournament mappool sink (SQLite).
--
-- Per README §3 / §12, Layer A holds raw sources as-imported. Wiki/web
-- sources don't have a SQL dump to mirror, so for Liquipedia we sink the
-- scraped + API-verified CSV into this local SQLite file (separate from
-- osu-data's MySQL on port 3308 so it survives the monthly ppy-dump
-- refresh cycle).
--
-- All rows from the verifier land here verbatim — including `mismatch`,
-- `missing` and `no_id` rows. Filtering is the consumer's job at query
-- time (`WHERE verify_status = 'match'`). Curated views belong in a
-- future Layer B `tournament_mappool` projection, not here.
--
-- Source columns (from `data/layerA/liquipedia/owc_mappool_verified.csv`):
--   tournament, tournament_slug, round, slot, slot_category, slot_index,
--   mod_set, beatmap_artist, beatmap_title, beatmap_difficulty,
--   beatmap_id, beatmapset_id, source_url, source_revision,
--   parser_version, scraped_at,
--   verified_status, verified_beatmap_id, verified_beatmapset_id,
--   verified_artist, verified_title, verified_difficulty,
--   verified_ranked_status, verified_at

CREATE TABLE IF NOT EXISTS tournament_pick (
    -- identity (natural key — every scraped row has these three)
    tournament_slug    TEXT    NOT NULL,
    round              TEXT    NOT NULL,
    slot               TEXT    NOT NULL,

    -- semantic
    tournament         TEXT    NOT NULL,
    slot_category      TEXT    NOT NULL,
    slot_index         INTEGER,
    mod_set            TEXT,

    -- Liquipedia-side scrape (preserved verbatim)
    beatmap_id            INTEGER,
    beatmapset_id         INTEGER,
    liquipedia_artist     TEXT,
    liquipedia_title      TEXT,
    liquipedia_difficulty TEXT,

    -- osu! API v2 side (NULL when verifier couldn't resolve the id)
    api_beatmap_id        INTEGER,
    api_beatmapset_id     INTEGER,
    api_artist            TEXT,
    api_title             TEXT,
    api_difficulty        TEXT,
    api_ranked_status     TEXT,

    -- match | mismatch | missing | no_id
    verify_status         TEXT NOT NULL,

    -- provenance
    source_url            TEXT,
    source_revision       INTEGER,
    parser_version        TEXT,
    scraped_at            TEXT,
    verified_at           TEXT,

    PRIMARY KEY (tournament_slug, round, slot)
);

CREATE INDEX IF NOT EXISTS idx_tp_beatmap_id    ON tournament_pick (beatmap_id);
CREATE INDEX IF NOT EXISTS idx_tp_api_bid       ON tournament_pick (api_beatmap_id);
CREATE INDEX IF NOT EXISTS idx_tp_tournament    ON tournament_pick (tournament_slug);
CREATE INDEX IF NOT EXISTS idx_tp_mod           ON tournament_pick (mod_set);
CREATE INDEX IF NOT EXISTS idx_tp_verify_status ON tournament_pick (verify_status);
