# Beatmap-level derived metrics

Features computed on top of raw dump columns to characterise beatmaps for ML and filtering. All are defined per `(beatmap_id, mods)` unless noted.

## `popularity_rank`

Used by `All-Of-Osu-DB`'s `beatmap_reference` as the primary consumer query axis.

```sql
rank() OVER (PARTITION BY mode ORDER BY playcount DESC)
```

- Per-mode rank.
- Ties broken arbitrarily by Postgres (use `dense_rank()` if you care; `rank` is fine if you don't).
- Compute after ETL load, not in the source MySQL — Postgres window functions are friendlier here.

## `favourite_factor`

Explicit-positive-feedback ratio at the beatmap-set level.

```
favourite_factor = osu_beatmapsets.favourite_count / total_playcount_of_set
```

Where `total_playcount_of_set = sum(osu_beatmaps.playcount) over the set`. Replicated per difficulty (every row in the set has the same value — confirmed by notebook sanity check).

Interpretation: higher = more users hit "favourite" per play. A proxy for "people who tried this, loved it." Orthogonal to raw playcount popularity.

## Farm factor

Captures how much a beatmap is played **for PP farming** rather than for genuine enjoyment / skill-match.

### Components

```
compactness(beatmap) = mean(pp of top scores) / max(pp of top scores)
```
High when most players on the map reach near-max pp — indicating the map has a narrow "ceiling" that's easy to approach.

```
true_pp(score)       = score.pp * 0.95^rank_of_score_within_beatmap
pp_contribution_g(b) = sum(true_pp for all top scores on b) / total_playcount_of_b
```
High when each play on this beatmap contributes a lot to players' total weighted PP globally.

### Composite

```
farm_factor = 0.2 * compactness + 0.8 * pp_contribution_global
```

Two parallel variants computed:
- `random_farm_factor` — computed against the `random_10000` score population.
- `top_farm_factor` — computed against the `top_10000` score population.

The `top_farm_factor` is consistently higher for known farm maps, since top players grind them.

### Sanity-check map list

From `data/processed/print_farm.py` — names that must rank high on `top_farm_factor` for the metric to be correct:

```
Blue Zenith, (can you) understand me?, KARMANATIONS, AaAaAaAAaAaAAa,
Freedom Dive, Bass Slut (Original Mix), The Big Black, No Title,
Santa-san, PADORU / PADORU, Renai Circulation, Epitaph,
Overkill, Crab Rave
```

If any of these DON'T rank in the top ~500 by `top_farm_factor`, your pivot or aggregation is wrong.

## Relevance flags

Used to filter the long tail:

```
relevant_random = (count of scores from random_10000 users on this beatmap >= 10)
relevant_top    = (count of scores from top_10000 users on this beatmap >= 10)
```

Coverage:
- Random users: only ~23% of beatmaps reach the ≥10 threshold.
- Top users: ~99% — because they grind broadly.

Use these to drop rare-map rows before training to avoid cold-start noise.

## `technicality` (prototype)

```python
technicality = slider_factor * (1 - passcount / playcount)
```

Combines slider density (from the `attrib_id=19` pivot) with inferred difficulty (low pass rate → harder). Not validated against a ground-truth "technical map" label; treat as exploratory.

## `pp_per_star` (prototype)

```python
# per beatmap-mod, on scores with accuracy >= 98%
pp_per_star = max(pp_of_high_acc_scores) / diff_star_rating
```

Exposes farm bias by SR bin. High `pp_per_star` at low SR = that map gives more PP than its star rating suggests → farmable.

## Per-SR-bin correlations

Pattern for exposing where farm dominates discovery:

```python
bins = np.arange(2.0, 10.25, 0.25)
ratio_df['star_bin'] = pd.cut(ratio_df['diff_star_rating'], bins)
for bin_range, group in ratio_df.groupby('star_bin'):
    pp_corr   = group['max_pp'].corr(group['playcount'])
    star_corr = group['diff_star_rating'].corr(group['playcount'])
```

Then plot `pp_corr` and `star_corr` per bin. In RecSys-Study's output, both show large variance across bins — the relationship between SR/PP and playcount isn't monotonic.

## Per-user 99th-percentile ceiling (for filtered recommendation)

Computed per user from their prior plays; used to exclude recommendations that would overstep any of the player's physical / reading caps.

```python
SENSITIVE_ATTRS = ["diff_approach", "diff_star_rating", "aim", "speed"]
PERCENTILE = 99

# user_prior_plays: DataFrame of this user's scores joined to beatmap features
ceilings = user_prior_plays[SENSITIVE_ATTRS].quantile(PERCENTILE / 100.0)

# when recommending:
def is_out_of_range(candidate_beatmap):
    return any(candidate_beatmap[a] > ceilings[a] for a in SENSITIVE_ATTRS)
```

Applied as a post-recommendation filter (`top_filtered = [p for p in predictions if not p.is_out_of_range][:k]`). Reliably raises `true_min` (worst-case recommendation quality) at small cost to `true_avg`.

## Column name reference (processed `beatmaps.csv`)

```
mod_beatmap_id        — synthetic int; unique (beatmap_id, mods_string) → int
beatmap_id            — ppy ID
mods_string           — one of "NM" / "HR" / "DT" / "DTHR"
beatmapset_id
creator_user_id
playcount / passcount
set_favourite_count
artist / title / submit_date / approved_date
bpm / hit_length
count_total / count_normal / count_slider / count_spinner
diff_drain / diff_size / diff_overall / diff_approach / diff_star_rating
aim / speed / max_combo / strain / slider_factor / speed_note_count
genre
favourite_factor
relevant_random / relevant_top
random_farm_factor / top_farm_factor
```
