# Enjoyment score

RecSys-Study's engineered rating. Used as the target column when training the recommender — a proxy for implicit preference, since osu! provides no explicit "liked this" per-beatmap signal.

## The formula

Verbatim from `documentation/schema-info.md`:

```
enjoyment =
    0.2 * playcount_component +
    0.3 * favourite_component +
    0.2 * accuracy_component    * (1 - farm_factor) +
    0.3 * pp_contribution_component * farm_factor
```

Followed by a **per-user zero-mean / unit-variance adjustment** — each user's enjoyment scores are standardised within their own distribution.

## Components

### `playcount_component`

```
playcount_component(user, beatmap, mods) =
    1 - exp(-user_playcount_on_beatmap / average_global_playcount)
```

- Exponential saturation curve. Saturation point near the global mean playcount.
- Then **min-max normalized per user** into `[0, 1]` so that the curve is comparable across users with very different absolute playcounts.

### `favourite_component`

```
favourite_component(beatmapset) = favourite_count / total_playcount_of_set
```

Global, per-set. Measures explicit positive feedback density. Same value for every difficulty in the set.

### `accuracy_component`

```
accuracy_component(score) = 1 - (accuracy - 0.95)^2
```

- Peaks at `accuracy = 0.95`.
- Triangular-ish bump. Assumes ~95% is the "in the zone, enjoying it" acc range.
- Below 95% → player was struggling. Above 95% → player was potentially under-challenged.

### `pp_contribution_component`

```
pp_contribution_component(score, user) = score.pp / user.total_weighted_pp
```

How much this single score contributes to the user's total weighted PP. Captures "this is one of the scores that actually matters for my rank."

## The farm-factor gate

The weighting between `accuracy_component` and `pp_contribution_component` is controlled by `farm_factor`:

- **On farmy maps** (`farm_factor` high): weight `pp_contribution_component` more. Because on a farm map, actually gaining PP is the signal that the play mattered — accuracy is cheap.
- **On non-farmy maps** (`farm_factor` low): weight `accuracy_component` more. Because on these, the player doesn't play for PP; how well they performed is the signal of enjoyment.

```
weighted_acc = accuracy_component    * (1 - farm_factor)     # 0..0.2
weighted_pp  = pp_contribution_comp  * farm_factor            # 0..0.3
```

See [`beatmap-metrics.md`](./beatmap-metrics.md) for `farm_factor` definition.

## Observed range

After per-user baseline/variance adjustment: **−4.875 to +10.311** (from `recommend.py` output comments). Most values cluster in `0.1–0.5` before the adjustment.

**Critical**: Surprise's `Reader(rating_scale=(0.0, 1.0))` silently clips out-of-range values. You MUST min-max normalize per user after the formula + adjustment, before feeding to Surprise:

```python
df['rating'] = df.groupby('user_id')['rating'].transform(
    lambda x: (x - x.min()) / (x.max() - x.min() + 1e-9)
)
```

## The author's honest caveat

From `Points.txt` / `schema-info.md`: the formula is **"necessarily somewhat arbitrary"**. It's designed from experience / inspection, not from ground-truth liking data (which isn't available at scale). The weights `0.2 / 0.3 / 0.2 / 0.3` are intuitive, not optimised.

Ways it could go wrong:
- A player who grinds a farm map they hate gets a high `playcount_component` and a high `pp_contribution_component` → high enjoyment score despite disliking the map.
- A player who plays a map once with 99% acc gets a high `accuracy_component` → high enjoyment despite nearly-no interaction.
- The per-user variance adjustment mutes users with uniform enjoyment (someone who only plays maps they love) — their rating variance collapses.

The `Reddit` / `favourite_count` data is the closest thing to ground-truth liking; author speculates that incorporating favourite-set membership per user (if ever scrapable) would be a better rating target.

## Alternative: `playcount` rating

Trained in parallel as a baseline. Simply `log(playcount + 1)` per `(user, beatmap, mod)`, normalized. Results in `RecSys/pipeline/summary_pretty_table.txt` show `enjoyment` rating beats `playcount` rating by ~80× on `true_avg` — most of the recommender's signal really does come from the engineered formula, not raw playcount.

## Full derivation, for a single score row

```python
# Inputs
user_pc_on_map         = playcount[user, beatmap]           # user_playcount
global_pc_avg          = mean(playcount across all plays)   # constant
favourite_count        = beatmap_set.favourite_count
total_pc_of_set        = sum(playcount) across set
accuracy               = score.accuracy / 100.0             # 0..1 domain
user_total_pp          = user.total_weighted_pp
score_pp               = score.pp
farm                   = beatmap.farm_factor                # 0..1

# Components
playcount_c    = 1 - np.exp(-user_pc_on_map / global_pc_avg)
# then per-user minmax to [0,1]
favourite_c    = favourite_count / total_pc_of_set
accuracy_c     = 1 - (accuracy - 0.95) ** 2
pp_contrib_c   = score_pp / user_total_pp

# Aggregate
enjoyment = (
    0.2 * playcount_c +
    0.3 * favourite_c +
    0.2 * accuracy_c  * (1 - farm) +
    0.3 * pp_contrib_c * farm
)

# Then per-user standardize, then per-user min-max to [0,1].
```

## Notes for `All-Of-Osu-DB`

This project's `beatmap_reference` **does not** include `enjoyment` — it's a score-level + score-set-statistics-level metric, not a beatmap-level one. If you ever add a Layer B score projection, enjoyment belongs there, not in `beatmap_reference`.
