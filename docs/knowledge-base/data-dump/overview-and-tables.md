# ppy MySQL dump: overview & raw tables

## What it is

The canonical public osu! data source is [`data.ppy.sh`](https://data.ppy.sh/) — **monthly MySQL dumps** published by peppy. Each dump is a snapshot of a slice of production data at dump time. Multiple **slices** are published per month:

- `osu_top_1000` — top 1,000 ranked players' scores + associated beatmaps.
- `osu_top_10000` — top 10,000 ranked players'.
- `osu_random_10000` — 10,000 randomly-sampled active players.

Plus per-mode variants (`taiko_*`, `fruits_*`, `mania_*`).

Files arrive as a folder `YYYY_MM_DD_performance_<mode>_<slice>/` containing many `.sql` files (one per table, sometimes split into chunks). Sizes: ~1–2 GB compressed for `top_10000 osu`; tens of GB for the largest slices.

The `Eve-ning/osu-data` pip package automates download + import into a local Docker MySQL on port 3308. See [`import-workflow.md`](./import-workflow.md).

## Table map (the ones RecSys-Study uses)

### User-side

#### `osu_user_stats`
Per-user career aggregates (one row per user).

| Column | Type | Notes |
| --- | --- | --- |
| `user_id` | bigint | Primary key; matches `osu_user_beatmap_playcount.user_id`, `osu_scores_high.user_id`. |
| `accuracy` | float | Legacy career-accuracy metric (hit-vs-miss only, lower). |
| `accuracy_new` | float | Weighted version (definition partially unknown). |
| `playcount` | bigint | Total plays lifetime. |
| `rank` / `rank_score` | bigint / float | Global rank and weighted-PP score. |
| `fail_count` | bigint | Lifetime fails. |
| `exit_count` | bigint | Lifetime mid-play exits. |
| `max_combo` | int | Personal best combo. |
| `country_acronym` | char(2) | ISO-style. |
| `last_played` | datetime | |
| `total_seconds_played` | bigint | |
| plus many more not used by RecSys-Study |

#### `sample_users` (per-slice)
RecSys-Study convention — NOT a ppy table; it's whatever population of `user_id`s the slice covers, materialised as a convenience table. For `top_10000` that's 10,000 rows.

### Score-side

#### `osu_scores_high` (~43 M rows for `top_10000 osu`)
One row per user's **top** score on each beatmap+mod-bitmask. Actual high-score leaderboard data.

| Column | Type | Notes |
| --- | --- | --- |
| `score_id` | bigint | PK. |
| `beatmap_id` | bigint | → `osu_beatmaps.beatmap_id`. |
| `user_id` | bigint | → `osu_user_stats.user_id`. |
| `score` | bigint | In-game score value. |
| `pp` | float | Nullable — older scores / RX / AP have NULL. |
| `maxcombo` | int | Max combo within this score (vs. beatmap.max_combo → detect FC). |
| `rank` | enum | Letter rank `D/C/B/A/S/X/SH/XH`. |
| `enabled_mods` | int | **Mod bitmask** (see `game/mods.md`). |
| `date` | datetime | When the score was set. |
| `count50`, `count100`, `count300`, `countmiss` | int | Judgment counts. |
| `countgeki`, `countkatu` | int | Present but unused by RecSys-Study. |
| `pass` | tinyint | Passed the map? |

#### `osu_scores` (sibling, partial; ~34 M rows, ~65% of `_high`)
Older / legacy-mode score table. Possibly overlaps `_high`. **Author never resolved the overlap** — flagged as an open question. Safest default: use `_high` only.

#### `osu_user_beatmap_playcount` (~75 M rows)
`(user_id, beatmap_id, playcount)`. Per-user per-beatmap play count (**not** per-mod). Needs aggregation before joining: `SELECT user_id, beatmap_id, MAX(playcount) GROUP BY user_id, beatmap_id` — there can be multiple rows per pair.

Without an index on `(user_id, beatmap_id)` this table is effectively unqueryable at scale; RecSys-Study adds one explicitly.

### Beatmap-side

#### `osu_beatmaps`
One row per **difficulty** (per-difficulty metadata).

| Column | Type | Notes |
| --- | --- | --- |
| `beatmap_id` | bigint | PK. |
| `beatmapset_id` | bigint | → `osu_beatmapsets`. |
| `user_id` | bigint | **Creator** (not player). |
| `checksum` | char(32) | **MD5 of the .osu file** — used as canonical identifier in-game. |
| `version` | varchar | Difficulty name (e.g. `"Insane"`). |
| `playmode` | tinyint | 0=std, 1=taiko, 2=catch, 3=mania. |
| `approved` | tinyint | Status (-2 graveyard … 4 loved). |
| `approved_date` | datetime | Nullable (unranked maps). |
| `total_length` | int | Song length in seconds. |
| `hit_length` | int | Playable seconds (first hit → last hit). |
| `bpm` | float | Dominant BPM. |
| `playcount` | bigint | Total plays on this difficulty. |
| `passcount` | bigint | Plays that didn't fail. |
| `countTotal` | int | Total hit objects (mixed-case!). |
| `countNormal` | int | Circles. |
| `countSlider` | int | Sliders. |
| `countSpinner` | int | Spinners. |
| `diff_drain` | float | HP. |
| `diff_size` | float | CS. |
| `diff_overall` | float | OD. |
| `diff_approach` | float | AR. |
| `difficultyrating` | float | Legacy nomod star rating. |

**Watch out:** `countTotal`, `countNormal`, `countSlider`, `countSpinner` are mixed-case identifiers. Keep backticks on MySQL, quote on Postgres, or rename on import.

#### `osu_beatmapsets`
One row per beatmap **set** (one upload).

| Column | Notes |
| --- | --- |
| `beatmapset_id` | PK. |
| `artist`, `title` | Romanised. |
| `creator` | Creator username (redundant with `osu_beatmaps.user_id` join to `osu_user_stats`). |
| `favourite_count` | Set-level favourites count. Same for every difficulty in the set. |
| `tags` | Space-separated. |
| `genre_id`, `language_id` | Enum IDs (small tables — look up in the dump). |
| `track_id` | Optional FeaturedArtist link. |
| `submit_date`, `approved_date` | |

#### `osu_beatmap_difficulty` (~7 M rows; `d`)
One row per `(beatmap_id, mode, mods)` combination.

| Column | Notes |
| --- | --- |
| `beatmap_id`, `mode`, `mods` | Composite key. `mods` in this table is one of the discrete combinations actually computed (0, 16, 64, 80 for std-mode ML). |
| `diff_unified` | **Mod-specific star rating** (renamed to `diff_star_rating` in processed CSVs). |

#### `osu_beatmap_difficulty_attribs` (~64 M rows; `a`) — EAV
| Column | Notes |
| --- | --- |
| `beatmap_id`, `mode`, `mods`, `attrib_id` | Composite key. |
| `value` | Float. |

Pivot map (see [`enums-and-gotchas.md`](./enums-and-gotchas.md)):
- 1 = aim, 3 = speed, 9 = max_combo, 11 = strain, 19 = slider_factor, 21 = speed_note_count, 23 = speed_difficult_strain_count, 25 = aim_difficult_strain_count.

## Tables in the dump but NOT used by RecSys-Study

Called out in `schema-info.md` as "exists but not pulled":

- **Per-100-chunks fail/exit masks** (table name not captured) — ~4 M rows, partial mod coverage. Could produce per-section difficulty heatmaps. Wishlist.
- **Genre / language lookup tables** — small dimension tables; IDs joined to `osu_beatmapsets`. You can inline them if you want human-readable genre labels.

## Tables / data explicitly NOT in any ppy dump

Per RecSys-Study's `schema-info.md` wishlist:
- **Max PP per `(beatmap, mod)`** — third-party might have it; ppy doesn't expose.
- **User favourited beatmapsets** — would be the gold-standard explicit feedback; author flagged as "seems impossible" to fetch at scale.
- **Per-beatmap exit / fail rate** — the per-chunk table above is the rawest form; no aggregate exists.
- **Live-API-only data** (lazer-specific stats, current rank, very recent scores).

## Relationship to the `osu-performance-datasets-generator` repo

ppy maintains [`ppy/osu-performance-datasets-generator`](https://github.com/ppy/osu-performance-datasets-generator) which documents what each slice contains and how it's built. Reference that repo (README + `dump_all.sh`) for authoritative slice contents. Not mirrored here; go read it when in doubt.
