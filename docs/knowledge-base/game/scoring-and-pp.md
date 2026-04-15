# Scoring, accuracy, PP, and letter ranks

## Accuracy (standard mode)

The canonical formula, recomputed in RecSys-Study's SQL because the dump's stored accuracy is only on `osu_user_stats` (career-level) and not per-score:

```
accuracy = (50 * count50 + 100 * count100 + 300 * count300)
         / (300 * (count50 + count100 + count300 + countmiss))
         * 100
```

Returns NULL when the denominator is zero (i.e., no hits recorded — dead spinner, aborted play). See `knowledge-base/data-dump/sql-patterns.md` §C.1 for the exact `CASE` wrapping.

## Two user-level accuracy columns

`osu_user_stats` has both:

- **`accuracy`** — legacy column, hit-vs-miss only, lower.
- **`accuracy_new`** — weighted by something (likely top-plays only); consistently higher than `accuracy`. **The exact definition isn't documented in the source repos** — flagged as a known unknown.

Treat both as career-level metrics, not per-score.

## Performance Points (PP)

PP is osu!'s canonical per-score skill metric. Raw column: `osu_scores_high.pp` (float; can be NULL for older scores that predate PP, or for scores under excluded mods like RX/AP).

### Weighted PP ("total_weighted_pp")

User rank/skill is determined by the sum of their **top 100 scores**, each weighted by `0.95^rank`:

```python
scores.sort_values(['user_id', 'pp'], ascending=[True, False])
scores['rank']        = scores.groupby('user_id').cumcount()      # 0 = best score
scores = scores[scores['rank'] < 100]
scores['weight']      = 0.95 ** scores['rank']
scores['weighted_pp'] = scores['pp'] * scores['weight']
user_total_pp = scores.groupby('user_id')['weighted_pp'].sum()
```

(from `DataAnalysis/analysis.ipynb` cell 6)

This is the number shown as "PP" on a user's profile. `osu_user_stats.rank_score` would be the authoritative stored value; RecSys-Study recomputes it into a derived column `total_weighted_pp` rather than trusting the dump.

### true_pp (per-score, for farm-factor math)

Same 0.95-per-rank weighting, applied per-score but globally per-beatmap rather than per-user — used in the farm-factor formula:

```
true_pp(score) = score.pp * 0.95 ** rank_of_score_within_beatmap
```

See `knowledge-base/derived-metrics/beatmap-metrics.md`.

## Score value (the in-game points column)

`osu_scores_high.score` is the classic in-game score value (max ~1,000,000 FC baseline, with multipliers). Not directly used by RecSys-Study's feature engineering — PP dominates.

Preview-only simulation used by skintool (not real osu!):
```
score      += hitValue * max(1, combo / 10)
accuracy%  = (h300*300 + h100*100 + h50*50) / (totalHits*300) * 100
```
This is illustrative, not authoritative — real osu! applies mod multipliers and HP/combo-based multipliers.

## Letter ranks

Awarded per play: `D`, `C`, `B`, `A`, `S`, `X` (SS = full 100%). Hidden-variant shadows: `SH`, `XH` (awarded when HD or FL is active for an otherwise-S/X play). Column: `osu_scores_high.rank`.

Author's note (Osu-RecSys-Study `schema-info.md`): letter ranks "do not really matter" for ML purposes — they're a coarse categorical coating over accuracy/combo.

## Hit counts

`osu_scores_high.count300`, `count100`, `count50`, `countmiss` — integer counts per judgment. `countgeki`, `countkatu` exist in the table but aren't used by RecSys-Study (geki = 300 on a spinner/first-combo, katu = 100 on slider head + all ticks). All four "osu! standard hits" contribute to the accuracy formula; miss reduces the denominator's effective weight.

`maxcombo` — longest combo chain in this score. Compare against `osu_beatmaps.max_combo` (from the `attrib_id=9` pivot in `osu_beatmap_difficulty_attribs`) to detect FC plays: `maxcombo == beatmap.max_combo`.

## Judgment hit windows (preview-only)

Skintool hard-codes preview values:
```
HIT_WINDOW_300 = ±50  ms
HIT_WINDOW_100 = ±100 ms
HIT_WINDOW_50  = ±150 ms
APPROACH_TIME  = 800  ms (constant, not AR-derived)
```

These are wrong for real gameplay — real windows are OD-dependent and approach time is AR-dependent. **This repo does NOT encode the real formulas.** Go to the osu! wiki for them.
