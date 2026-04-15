# Difficulty attributes

osu! exposes two tiers of "how hard is this beatmap" data:

1. **Base difficulty parameters** — author-chosen settings: AR, CS, OD, HP. Live on `osu_beatmaps`.
2. **Computed difficulty attributes** — PP-system outputs per `(beatmap, mode, mods)`. Live on `osu_beatmap_difficulty` + `osu_beatmap_difficulty_attribs` (EAV).

## Base parameters (`osu_beatmaps.*`, per-beatmap)

| Column | Meaning | Typical range |
| --- | --- | --- |
| `diff_drain` | HP drain rate | 0–10 |
| `diff_size` | CS — hit-circle size (higher = smaller circles) | 0–10 |
| `diff_overall` | OD — judgment strictness | 0–10 |
| `diff_approach` | AR — how long notes are visible | 0–10 (higher = shorter preempt) |
| `difficultyrating` | Legacy nomod star rating; also exposed as `diff_unified` in `osu_beatmap_difficulty` | ~0–10+ |
| `bpm` | Dominant BPM | ~60–300 |
| `total_length` | Total song length (seconds) | |
| `hit_length` | Playable time from first to last hit object (seconds) | |
| `max_combo` | Theoretical max chain (also recoverable via attrib_id=9) | |

Hit-object counts: `countTotal = countNormal + countSlider + countSpinner`. **MySQL mixed-case identifiers** — watch for `countTotal` vs `count_total` when dumping to Postgres.

## Star rating (SR)

`osu_beatmap_difficulty.diff_unified` — **per mod combination**. RecSys-Study renames this to `diff_star_rating` in processed CSVs. HR and DT each re-compute SR with modded parameters, so each `(beatmap_id, mods)` tuple has its own value. The `osu_beatmaps.difficultyrating` column is the nomod-equivalent convenience value.

Caveat called out by the author: **star rating and PP formulas have changed over osu!'s history**. Old scores were computed under the formula active at the time — mixing dump vintages in aggregations can create artifacts. TODO in `DataAnalysis/analysis.ipynb` cell 26 was to quantify this variance; not completed.

## Computed difficulty attributes (EAV pivot)

`osu_beatmap_difficulty_attribs` is a long table: `(beatmap_id, mode, mods, attrib_id, value)`. Each `(beatmap, mode, mods)` tuple has multiple rows, one per attrib. RecSys-Study pivots them:

| `attrib_id` | Feature name | Semantic |
| --- | --- | --- |
| `1` | `aim` | Cumulative / derived distance-between-hit-objects component of PP's aim skill. |
| `3` | `speed` | Tapping-speed component. |
| `9` | `max_combo` | Theoretical max combo for this mod combo. |
| `11` | `strain` | Rolling-difficulty strain metric. |
| `19` | `slider_factor` | Ratio / normalizer involving sliders. |
| `21` | `speed_note_count` | Count of note pairs spaced under ~200 ms (fast tap sections). |
| `23` | `speed_difficult_strain_count` | Number of high-speed-strain windows. |
| `25` | `aim_difficult_strain_count` | Number of high-aim-strain windows. |

RecSys-Study's SQL uses `COUNT(DISTINCT attrib_id) = 9` as a completeness gate — a beatmap-mods row is kept only if all 9 attribs are populated. The gate drops ~30% of beatmaps. (The 9th attrib not pivoted above is implied but its `attrib_id` isn't documented in the source; likely an overall difficulty value.)

See verbatim pivot SQL in `knowledge-base/data-dump/sql-patterns.md` §C.2.

## Hit-object composition

The three counts together describe map shape:
- **Circle-heavy** maps: stream / stamina tests.
- **Slider-heavy** maps: flow / slider-velocity control.
- **Spinner-heavy** maps: rare; usually a marathon-style breakpoint.

RecSys-Study uses `slider_factor` + pass rate to build a prototype **technicality** feature (see `knowledge-base/derived-metrics/beatmap-metrics.md`).

## Not in this knowledge base

- Exact AR → **preempt / fade-in time** formula (AR uses tiered linear segments with a DT/HR multiplier).
- Exact OD → **hit window** formula.
- Exact CS → **circle radius** formula.
- How `aim` / `speed` / `strain` are computed internally.

These exist in the osu! wiki and the `ppy/osu-performance` repo. Neither source repo here encodes them; the skintool hard-codes preview constants (`APPROACH_TIME = 0.8s`, `BASE_CIRCLE_SIZE = 80`) that should **not** be relied on as real values.
