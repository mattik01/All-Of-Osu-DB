# SQL patterns (verbatim from Osu-RecSys-Study)

These are preserved as-was — proven to work against real ppy dumps. Copy, don't rewrite from memory.

## C.1 Pre-aggregate M:N before join, then compute accuracy

`osu_user_beatmap_playcount` is M:N-ish (multiple rows per `(user, beatmap)`), so joining it raw to `osu_scores_high` duplicates score rows. Aggregate first:

```sql
ALTER TABLE osu_user_beatmap_playcount
ADD INDEX idx_user_beatmap (user_id, beatmap_id);

CREATE TABLE scores_high AS
SELECT
  s.score_id, s.beatmap_id, s.user_id, s.score, s.pp, s.maxcombo, s.rank,
  s.enabled_mods, s.date,
  COALESCE(p.playcount, 0) AS playcount,
  CASE
    WHEN (s.count50 + s.count100 + s.count300 + s.countmiss) = 0 THEN NULL
    ELSE ROUND(
      ((50 * s.count50 + 100 * s.count100 + 300 * s.count300)
       / (300.0 * (s.count50 + s.count100 + s.count300 + s.countmiss))
      ) * 100, 4
    )
  END AS accuracy
FROM osu_scores_high s
LEFT JOIN (
  SELECT user_id, beatmap_id, MAX(playcount) AS playcount
  FROM osu_user_beatmap_playcount
  GROUP BY user_id, beatmap_id
) p ON s.user_id = p.user_id AND s.beatmap_id = p.beatmap_id;
```

Key tricks:
- Pre-aggregate in the subquery, not in the outer join.
- The `(user_id, beatmap_id)` index on the playcount table is mandatory — unindexed it's unusably slow at 75 M rows.
- `LEFT JOIN` + `COALESCE(..., 0)` keeps scores with no recorded playcount (odd but happens).

## C.2 EAV → wide pivot with completeness gate

Pivots `osu_beatmap_difficulty_attribs` by `attrib_id` and filters to beatmaps that have ALL 4 mod combinations with ALL 9 attribs each.

```sql
CREATE TABLE beatmaps AS
SELECT
    d.beatmap_id, b.beatmapset_id, b.user_id AS creator_user_id, d.mods,
    b.playcount, b.passcount, s.favourite_count AS set_favourite_count,
    s.artist, s.title, s.genre_id, s.language_id, s.submit_date, s.approved_date,
    b.bpm, b.hit_length,
    b.countTotal AS count_total, b.countNormal AS count_normal,
    b.countSlider AS count_slider, b.countSpinner AS count_spinner,
    b.diff_drain, b.diff_size, b.diff_overall, b.diff_approach,
    d.diff_unified AS diff_star_rating,
    -- Pivoted difficulty attributes
    MAX(CASE WHEN a.attrib_id = 1  THEN a.value END) AS aim,
    MAX(CASE WHEN a.attrib_id = 3  THEN a.value END) AS speed,
    MAX(CASE WHEN a.attrib_id = 9  THEN a.value END) AS max_combo,
    MAX(CASE WHEN a.attrib_id = 11 THEN a.value END) AS strain,
    MAX(CASE WHEN a.attrib_id = 19 THEN a.value END) AS slider_factor,
    MAX(CASE WHEN a.attrib_id = 21 THEN a.value END) AS speed_note_count,
    MAX(CASE WHEN a.attrib_id = 23 THEN a.value END) AS speed_difficult_strain_count,
    MAX(CASE WHEN a.attrib_id = 25 THEN a.value END) AS aim_difficult_strain_count
FROM osu_beatmap_difficulty d
LEFT JOIN osu_beatmap_difficulty_attribs a
       ON d.beatmap_id = a.beatmap_id AND d.mode = a.mode AND d.mods = a.mods
LEFT JOIN osu_beatmaps b      ON d.beatmap_id = b.beatmap_id
LEFT JOIN osu_beatmapsets s   ON b.beatmapset_id = s.beatmapset_id
WHERE d.mode = 0
  AND d.mods IN (0, 16, 64, 80)
  AND d.beatmap_id IN (
        SELECT beatmap_id FROM (
            SELECT d.beatmap_id, d.mods, COUNT(DISTINCT a.attrib_id) AS attr_count
            FROM osu_beatmap_difficulty d
            JOIN osu_beatmap_difficulty_attribs a
              ON d.beatmap_id = a.beatmap_id AND d.mods = a.mods AND d.mode = a.mode
            WHERE d.mode = 0 AND d.mods IN (0, 16, 64, 80)
            GROUP BY d.beatmap_id, d.mods
            HAVING COUNT(DISTINCT a.attrib_id) = 9
        ) AS complete_mods
        GROUP BY beatmap_id
        HAVING COUNT(DISTINCT mods) = 4
  )
GROUP BY d.beatmap_id, d.mods, d.diff_unified, b.beatmapset_id, b.user_id, b.total_length,
         b.hit_length, b.countTotal, b.countNormal, b.countSlider, b.countSpinner,
         b.diff_drain, b.diff_size, b.diff_overall, b.diff_approach,
         b.difficultyrating, b.playcount, b.passcount, b.bpm,
         s.artist, s.title, s.tags, s.genre_id, s.language_id,
         s.favourite_count, s.track_id, s.submit_date, s.approved_date;
```

Key techniques:
- **Conditional MAX pivot** on an EAV table.
- **Double-gate subquery**: inner HAVING filters `(beatmap, mods)` with all 9 attribs; outer HAVING filters beatmaps that pass the inner for all 4 mod combinations.
- `LEFT JOIN` + explicit GROUP BY on all non-aggregated columns (required for strict SQL modes).

Resulting row count: `131,124 beatmaps × 4 mods = 524,496` rows for `top_10000 osu` — down from the raw 197,513 beatmaps in the dump.

## C.3 User join

Simple but worth pinning:

```sql
CREATE TABLE USERS AS
SELECT su.user_id, su.username, ous.accuracy, ous.accuracy_new,
       ous.playcount, ous.rank, ous.fail_count, ous.exit_count,
       ous.max_combo, ous.country_acronym, ous.last_played,
       ous.total_seconds_played
FROM sample_users su
JOIN osu_user_stats ous ON su.user_id = ous.user_id;
```

`total_weighted_pp` and `skill_stabilization_date` are computed later in Python (see `derived-metrics/user-skill.md`); they don't fit naturally into a single SQL statement.

## C.4 Accuracy formula template

```sql
CASE
  WHEN (count50 + count100 + count300 + countmiss) = 0 THEN NULL
  ELSE ROUND(
    ((50 * count50 + 100 * count100 + 300 * count300)
     / (300.0 * (count50 + count100 + count300 + countmiss))
    ) * 100, 4
  )
END
```

## C.5 Popularity rank (deferred to Postgres in `All-Of-Osu-DB`)

Not in RecSys-Study directly, but specified in `All-Of-Osu-DB` README §8 — compute after load:

```sql
UPDATE beatmap_reference br SET popularity_rank = sub.r
FROM (
  SELECT md5,
         rank() OVER (PARTITION BY mode ORDER BY playcount DESC) AS r
    FROM beatmap_reference
) sub
WHERE br.md5 = sub.md5;
```

Or inline as a generated column / materialised view via `layerB_views.sql`.

## C.6 Streaming export (MySQL → CSV)

From `data/database_export.py`:

```python
cursor = conn.cursor(buffered=False)   # non-buffered for streaming
cursor.execute(f"USE `{schema}`")
cursor.execute(f"SELECT * FROM `{table}`")
headers = [desc[0] for desc in cursor.description]
with open(filepath, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(headers)
    for row in tqdm(cursor):
        writer.writerow(row)
```

Key: `buffered=False` and iterate, rather than `fetchall()`. Without this, a 50M-row table OOMs Python.

For `All-Of-Osu-DB`'s Postgres side, prefer `COPY ... FROM STDIN` batches over row-by-row inserts — see `src/all_of_osu_db/etl/` when implemented.

## C.7 Aggregate sanity queries

Useful for post-load spot-checking (per `All-Of-Osu-DB` README §13):

```sql
-- Row count
SELECT mode, status, count(*)
  FROM beatmap_reference
  GROUP BY mode, status
  ORDER BY mode, status;

-- Top-100 popularity sanity
SELECT md5, artist, title, version, playcount
  FROM beatmap_reference
 WHERE mode = 0
   AND status IN (1, 2, 4)
 ORDER BY playcount DESC
 LIMIT 100;

-- MD5 round-trip (grab a known map's MD5 from osu! client first)
SELECT *
  FROM beatmap_reference
 WHERE md5 = 'abcd1234...';
```
