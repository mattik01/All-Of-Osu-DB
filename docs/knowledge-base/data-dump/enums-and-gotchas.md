# Enums, bitfields & gotchas

## Enum: `osu_beatmaps.playmode` (`mode`)

```
0 = osu! standard (default)
1 = osu!taiko
2 = osu!catch ("fruits")
3 = osu!mania
```

## Enum: `osu_beatmaps.approved` (ranking status)

```
-2  = graveyard
-1  = WIP
 0  = pending
 1  = ranked
 2  = approved
 3  = qualified
 4  = loved
```

RecSys-Study keeps `{1, 2, 4}` (ranked + approved + loved). `All-Of-Osu-DB` uses the same filter in `ranked_std_popular_v`.

## Bitfield: `osu_scores_high.enabled_mods` / `osu_beatmap_difficulty.mods`

See `game/mods.md` for the full 22-bit table. Key points for SQL:

- In `osu_beatmap_difficulty`, the column is **one of the actual combinations computed** (for osu-std pp system: 0, 16, 64, 80). It is NOT a full bitmask — it's a subset of bitmasks the PP system materialised rows for.
- In `osu_scores_high`, the column **is** the raw mod bitmask exactly as played. Contains things like HD|DT|HR (72 + 8 = 88), EZ|DT (66), etc.
- **NC always co-occurs with DT**: if bit 512 is set, bit 64 is also set. Treat NC as DT for aggregation.
- **HD is a visibility mod**: non-difficulty-changing in the sense used here; RecSys-Study collapses `HD|X` down to `X` by keeping the max-pp row of duplicates.

## EAV pivot: `osu_beatmap_difficulty_attribs.attrib_id`

Map (std mode):

| `attrib_id` | Feature | Meaning |
| --- | --- | --- |
| `1` | `aim` | Aim-component strain/score. |
| `3` | `speed` | Speed-component strain/score. |
| `9` | `max_combo` | Mod-specific max combo. |
| `11` | `strain` | Combined strain metric. |
| `19` | `slider_factor` | Slider density / normalizer. |
| `21` | `speed_note_count` | Count of note-pairs under ~200ms. |
| `23` | `speed_difficult_strain_count` | High-speed-strain windows. |
| `25` | `aim_difficult_strain_count` | High-aim-strain windows. |

Completeness gate used in RecSys-Study's SQL: `COUNT(DISTINCT attrib_id) = 9`. That's 9 attribs per `(beatmap_id, mode, mods)` row — the 9th attrib (not pivoted above) is presumed an overall difficulty scalar. The gate drops a beatmap entirely if any of the 4 mod combinations is missing any of the 9 attribs.

Other modes (taiko / catch / mania) use different `attrib_id` numbers — unknown here since RecSys-Study is std-only.

## Charset & encoding gotchas

### MySQL-side

- Dumps contain rows that aren't valid UTF-8 — usernames and song titles in Shift-JIS, Windows-1252, mixed. RecSys-Study's `import-sql-processor.py` uses `chardet` for detection with a `latin1` fallback.
- Folder-name convention includes the dump date but not the encoding: `2025_05_01_performance_osu_top_10000`.

### DuckDB migration (RecSys-Study's experimental path)

When running the MySQL dump through DuckDB, the import script had to strip MySQL-specific syntax:

```python
sql = re.sub(r"`([^`]*)`",               r"\1", sql)         # backticks
sql = re.sub(r"AUTO_INCREMENT",          "", sql, flags=re.I)
sql = re.sub(r"UNSIGNED",                "", sql, flags=re.I)
sql = re.sub(r"ENGINE\s*=\s*\w+",        "", sql, flags=re.I)
sql = re.sub(r"DEFAULT CHARSET=\w+",     "", sql, flags=re.I)
sql = re.sub(r"COLLATE\s+\w+",           "", sql, flags=re.I)
sql = re.sub(r"CHARACTER SET\s+\w+",     "", sql, flags=re.I)
```

For MySQL→Postgres (the `All-Of-Osu-DB` path), similar rewrites apply, plus: `tinyint` → `smallint`/`boolean`, mixed-case column names quoted with `"`, `datetime` → `timestamptz`, etc.

## Mixed-case identifiers

The ppy dump uses camelCase for some columns:

- `osu_beatmaps.countTotal`
- `osu_beatmaps.countNormal`
- `osu_beatmaps.countSlider`
- `osu_beatmaps.countSpinner`

MySQL preserves case on Windows/Linux dumps; Postgres folds unquoted identifiers to lowercase. Three options when importing:
1. Always quote: `"countTotal"`. Tedious but exact.
2. Rename in ETL to snake_case: `count_total`. Cleaner consumer-side.
3. Let Postgres fold and live with lowercase only.

`All-Of-Osu-DB`'s `beatmap_reference` uses option 2 (snake_case).

## Two accuracy columns

`osu_user_stats.accuracy` vs `accuracy_new` — both exist. Definitions not documented in source repos. `accuracy_new` is consistently higher. Treat as "two different definitions, pick one and stick with it; document which."

## `osu_scores_high` vs `osu_scores`

`_high` = ~43 M rows, confident. Sibling `osu_scores` = ~34 M rows (partial, ~65%). Overlap unresolved. **Use `_high` only unless you have a specific reason otherwise.**

## Nullables & empty counts

- `pp` can be NULL on old scores or mod-excluded rows (RX/AP/etc.).
- `approved_date` is NULL for unranked maps.
- `count50+100+300+miss = 0` produces divide-by-zero in accuracy calc — always wrap in `CASE WHEN ... = 0 THEN NULL ELSE ... END`.
- `osu_beatmaps.bpm` is 0 for malformed maps — rare, but check before filtering.

## Timestamps

- All date columns are MySQL `datetime` (no timezone). RecSys-Study assumes UTC (reasonable). When importing to Postgres, convert to `timestamptz` with a literal `'UTC'` timezone.

## Score-count math gotchas

- `maxcombo == beatmap.max_combo` → FC (or auto-slider-break FC). Not sufficient alone to detect perfect 100% plays; need `countmiss == 0` AND `count50 == 0` AND `count100 == 0`.
- Max combo in `osu_beatmaps` column is wrong/stale for some older maps; prefer `attrib_id = 9` on the difficulty-attribs pivot.
