# Dataset characteristics, biases, and pitfalls

Observations and warnings that RecSys-Study surfaced while working with the `top_10000` and `random_10000` osu slices. Use these as sanity anchors when ingesting / validating / analysing new dumps.

## Volume table (from `Points.txt`)

| Metric | In raw dump | Exported CSVs | After processing | In training set |
| --- | --- | --- | --- | --- |
| users_random | 10,000 | 10,000 | 10,000 | 3,991 |
| scores_random | 4,018,988 | 4,018,988 | 2,611,808 (76%) | 509,895 |
| beatmaps_random | 197,513 | 524,496 (= 131,124 × 4) | 257,979 (60,498 ≥10 scores) | 56,704 |
| users_top | 9,999 | 9,999 | 9,999 | 9,643 |
| scores_top | 51,248,991 | 51,248,991 | 37,305,629 (74%) | 6,292,778 |
| beatmaps_top | 197,513 | — | 257,979 (254,833 ≥10 scores) | 233,878 |

Headline facts:
- **Top users have ~12.7× more scores than random users** (51M vs 4M). Top players grind enormously.
- **~24–26% of raw scores are dropped** in processing (mods filter + missing diff attribs).
- **Only ~23% of beatmaps reach the 10-score threshold for random users** (vs. ~99% for top). The long tail is dramatically sparser for casuals.
- **Random-user training retention is 40%** (10,000 → 3,991) after dropping users with <20 interactions on non-zero ratings.
- Beatmap exports: 131,124 unique beatmaps × 4 mods = 524,496 rows — down from 197,513 beatmap IDs total in the dump (the completeness gate drops ~33%).

## Distribution facts

### Long tail (playcount)

`DataAnalysis/analysis.ipynb` cell 15 shows the beatmap playcount distribution is extreme-long-tail — the top ~1% of maps account for a huge fraction of all plays. You need both linear and log-x plots to make sense of it.

### Country distribution

Cell 6 produces bubble plots of `(median hours played × median total_weighted_pp)` keyed by country. Top 10 countries cover most active users. US / JP / KR dominate by user count; Nordic countries skew high on median pp; SE Asia has high playtime but lower weighted pp.

### Playtime density

Cell 4: KDE plot of `total_seconds_played` (clipped 0–4000 hours for readability). Top-10000 distribution is shifted right of random — obvious but useful as a sanity marker.

### Submissions over time

Cell 18: monthly + cumulative upload counts. Confirms the game has grown ~monotonically since release.

### Days after skill stabilization

Cell 13: distribution of `(last_score_date − skill_stabilization_date)`. Most users play well past their stabilization point — validating that the pre-stabilization filter doesn't gut the dataset.

### Farm-factor distributions

Cell 13: both `random_farm_factor` and `top_farm_factor` (`>0` only) are right-skewed. Most maps have low farm factor; a small cluster has extreme.

### Map archetypes (3D plot)

Cell 20: 3D scatter of `(aim, speed, technicality)` coloured by star rating. Hypothesis: visible archetype clusters (aim-heavy / speed-heavy / tech-heavy). Useful for content-based retrieval work.

## Biases, named

1. **Farm bias** — extreme in `top_10000`. Top players grind farm maps. Without an explicit `farm_factor` feature, any popularity-based rating will surface these regardless of taste.

2. **Popularity bias (cold collapse)** — in `RecSys/recommend.py`'s initial SVD pilot, the same 5 item IDs appeared in the top recommendation for every tested user. Classic CF collapse.

3. **Progression bias** — early plays differ radically from current top-100. Mitigated by the `skill_stabilization_date` filter (see `derived-metrics/user-skill.md`).

4. **Mod combinatorial explosion** — raw mods produce too many items. Mitigated by collapsing to `{NM, HR, DT, DTHR}`.

5. **Score table duplication** — `osu_scores` (~34M) vs `osu_scores_high` (~43M). Overlap unresolved. Use `_high` only.

6. **Encoding bias** — non-UTF-8 username/title rows can vanish if imported without a fallback. Use `chardet` + `latin1` fallback.

7. **Star rating / PP formula drift** — osu! has changed SR and PP formulas over its history; old scores were computed under the formula in effect at the time. Mixing dump vintages in aggregations can produce artifacts. Flagged as a TODO in the notebook (cell 26); not quantified.

8. **Letter ranks are not informative** — they're a coarse coating over accuracy/combo. Don't use as features for ML.

9. **Two accuracy columns on users** — `accuracy` vs `accuracy_new`. Definitions partially unknown. `accuracy_new` is higher. Pick one and document.

10. **`playcount` in the score CSV is not mod-specific** — gotcha called out in the README. It's the total user playcount on the beatmap regardless of mods.

## Evaluation patterns worth keeping

### Filtered vs unfiltered top-K

Per-user eval flow from `RecSys/pipeline/evaluator.py`:

1. Predict rating for every item the user has in the validation set.
2. Sort predictions descending; take top-K=100.
3. Produce a **filtered** top-K by dropping items exceeding the user's 99th-percentile on any sensitive attribute (`diff_approach, diff_star_rating, aim, speed`).
4. Compute per-user metrics: `true_avg`, `true_top`, `true_min`, `mse`.
5. Aggregate per-fold (3-fold CV), per configuration.
6. Compare filtered vs unfiltered via deltas.

Result shape (from `summary_pretty_table.txt`):

| Dataset | true_avg | true_top | true_min | mse | Δ(filtered-unfiltered) |
| --- | --- | --- | --- | --- | --- |
| enjoyment / random | ~0.405 | ~0.563 | ~0.27 | 0.006–0.009 | true_min +0.0075, true_avg -0.0006 |
| enjoyment / top | ~0.35 | ~0.54 | similar | similar | similar |
| playcount / random | ~0.005 | — | — | 0.0001–0.002 | trivially low |
| playcount / top | ~0.001 | — | — | similar | trivially low |

Takeaway: filter reliably **raises the worst-case recommendation quality** (true_min) at tiny cost to average. `enjoyment` rating beats `playcount` rating by ~80× on `true_avg`.

SVD / KNN / BaselineOnly produce near-identical metrics in every cell — author's own grade on evaluation is "lackluster."

### Diversity caps (from Instacart cross-domain test)

```python
seen_depts, seen_aisles = {}, {}
for p in sorted(predictions, key=lambda p: -p.est):
    if p.is_recent_to_user: continue
    if seen_depts.get(p.dept, 0)   >= MAX_DEPT:  continue
    if seen_aisles.get(p.aisle, 0) >= MAX_AISLE: continue
    filtered.append(p)
    seen_depts[p.dept]   += 1
    seen_aisles[p.aisle] += 1
    if len(filtered) >= k: break
```

Pattern: greedy top-K with per-category caps. Transfers to osu: replace `dept/aisle` with `(genre, sr-bin)` or `(creator_user_id, sr-bin)` to prevent a single mapper or narrow SR range from dominating a recommendation list.

## Sanity checks for a fresh ingest

From RecSys-Study's experience, run these immediately after any dump ingest:

1. **Volume within ±10% of the prior month.** Larger deltas = upstream change or corruption.
2. **Top-100 popularity spot check.** Known popular maps should appear at the top of `ORDER BY playcount DESC`.
3. **MD5 round-trip.** Grab a known-map MD5 from the osu! client; it should return exactly one row.
4. **Idempotency.** Running the ETL twice on the same dump produces byte-identical row counts and per-column hashes.
5. **Farm-factor sanity.** `top_farm_factor` should rank the known-farm-map list (Blue Zenith, Big Black, etc.) highly. If it doesn't, your pivot or aggregation is wrong.

The `All-Of-Osu-DB` main README §13 codifies most of these as the `validate` command's job.

## Author self-grade (`Points.txt`)

For honesty: RecSys-Study's author rates the work as follows:
- Proposal: 7/8
- Data analysis: 6/6 ("a lot of cool stuff... barely shown")
- RecSys: 12/16 ("passable pipeline")
- Evaluation: 5/10 ("lackluster")

Total 30/40. Treat the engineered-enjoyment formula and SQL patterns as load-bearing; treat the evaluation numbers as directional, not authoritative.
