# Game modes & ranking status

## Game modes

osu! has four official modes. In the ppy MySQL dump they appear as integer codes in `osu_beatmaps.playmode` (and the same encoding is re-used throughout dump columns named `mode`):

| Code | Name | Internal slug | In scope for RecSys-Study? |
| --- | --- | --- | --- |
| `0` | osu! standard | `osu` | ✅ (exclusive focus) |
| `1` | osu!taiko | `taiko` | ❌ |
| `2` | osu!catch ("fruits") | `fruits` | ❌ |
| `3` | osu!mania | `mania` | ❌ — explicitly excluded (mania-specific mods K4/K5/…, RN, FI sit in high bits) |

The skintool's `ElementGroup` list confirms the mode slugs: `mode-osu`, `mode-taiko`, `mode-fruits`, `mode-mania`.

`osu-data` slicing is per mode — `--mode osu` in `osu-data`'s CLI narrows the dump download to standard. Its `-v/--version` flag then selects one of `top_1000 | top_10000 | random_10000` user slices (see [`../data-dump/import-workflow.md`](../data-dump/import-workflow.md)).

## Ranking status

Beatmaps carry a status flag that governs whether they count toward PP and whether they are included in "official" datasets. The column is `osu_beatmaps.approved` (int); user-facing names, ordered by unlock level:

| Code | Status | Notes |
| --- | --- | --- |
| `-2` | Graveyard | Pending but inactive. Excluded from RecSys-Study. |
| `-1` | WIP | Pending active work. |
| `0` | Pending | Submitted, unranked. |
| `1` | Ranked | Eligible for PP. |
| `2` | Approved | Legacy "ranked" for certain marathon maps. |
| `3` | Qualified | In queue to be ranked. |
| `4` | Loved | Community-loved; playcount tracked, no PP. |

RecSys-Study used `status IN (1, 2, 4)` — ranked + approved + loved — as the consumer-relevant slice (see `knowledge-base/data-dump/sql-patterns.md`). `All-Of-Osu-DB`'s `beatmap_reference` default filter is the same (README §8, `ranked_std_popular_v`).

## Beatmap vs beatmap set

- A **beatmap set** is a single upload: one `.osz` archive, one shared audio file, shared artist/title/creator.
- A **beatmap** ("difficulty") is one playable chart inside the set. Each has its own difficulty name (`version`), its own MD5 checksum, its own star rating.
- Key joins:
  - `osu_beatmaps.beatmapset_id → osu_beatmapsets.beatmapset_id` for artist/title/tags/favourite_count.
  - `osu_beatmaps.user_id` = **creator**'s user id (NOT the player's).

Set-level `favourite_count` is the same for every difficulty in the set; RecSys-Study's pipeline verified this as a sanity check and replicated it down to beatmap rows to build the `favourite_factor` feature.

## Country / locale

`osu_user_stats.country_acronym` is the ISO-style country code (US, JP, KR, DE, …). `DataAnalysis/analysis.ipynb` cell 6 produces a bubble plot of (median hours played × median weighted PP) keyed by country — top 10 countries cover most of the active population.
