# User skill: derived features

Two features RecSys-Study computes on top of raw dump columns to characterise users for ML. Both live in the final `users.csv`.

## `total_weighted_pp`

The canonical osu! "total PP" that shows on a user's profile. Computed per-user from score rows.

```python
scores.sort_values(['user_id', 'pp'], ascending=[True, False], inplace=True)
scores['rank']        = scores.groupby('user_id').cumcount()      # 0 = best
scores = scores[scores['rank'] < 100]
scores['weight']      = 0.95 ** scores['rank']
scores['weighted_pp'] = scores['pp'] * scores['weight']
user_total_pp = scores.groupby('user_id')['weighted_pp'].sum()
```

Why recompute instead of using `osu_user_stats.rank_score`?
- Dump vintage can lag the live value.
- The score population you computed against matters — if you've already filtered scores (mod filter, stabilization filter, etc.), recomputing weighted PP against the filtered population gives you a number consistent with the rest of your pipeline.

## `skill_stabilization_date`

Problem: early plays don't reflect current taste / skill. A player's first month on the game has very different maps in it than their current top 100. Training on pre-stabilization data adds noise.

**Definition**: the timestamp at which the user had achieved **10 of their current top 15 plays**. Before that date, they were still bootstrapping their top scores; after, top-100 composition stabilises.

Implementation (conceptual):

```python
# Per user:
top_15 = user_scores.nlargest(15, 'pp')
# sort those 15 by date ascending
top_15_by_date = top_15.sort_values('date')
# the 10th one chronologically IS the stabilization date
skill_stabilization_date = top_15_by_date.iloc[9]['date']
```

After computing, filter all score rows: `date >= skill_stabilization_date`. Verbatim from `data_split.py` and `recommend.py`:

```python
users = pd.read_csv(
    users_path,
    usecols=['user_id', 'skill_stabilization_date'],
    parse_dates=['skill_stabilization_date']
).set_index('user_id')

scores = scores.join(users, on='user_id', how='inner')
scores = scores[scores['date'] >= scores['skill_stabilization_date']]
```

Post-stabilization coverage: the `DataAnalysis/analysis.ipynb` cell 13 confirms most users play substantially past their stabilization point (median "days after stabilization" is large), so this filter doesn't decimate the data.

## Skill-ceiling progression (per-user, chronological)

Not in the final features, but worth preserving — RecSys-Study's notebook tracks how a user's skill ceiling evolves over time:

```python
n_chunks = 15
chunks   = np.array_split(user_df.sort_values('date'), n_chunks)
features = ['diff_star_rating', 'diff_approach', 'aim', 'speed']

# Per chunk: for each feature, compute avg of top 2.5% across all plays up to that point
for i, chunk in enumerate(chunks):
    prior_and_current = df[df['date'] <= chunk['date'].max()]
    for f in features:
        vals   = prior_and_current[f].values
        top_k  = max(1, int(len(vals) * 0.025))
        ceiling = np.mean(sorted(vals, reverse=True)[:top_k])
        # store (user, chunk_idx, feature, ceiling)
```

Output is a per-user GIF in `DataAnalysis/user_<id>_progression.gif` — a pedagogical visual of skill-axis growth across SR / AR / aim / speed. Underpins the "recommendations must respect per-user physical constraints" research idea.

## Min-interactions filter

Before training, drop users with fewer than 20 interactions in the post-filter dataset:

```python
df = df[df['rating'] > 0.0]
df = df.groupby("user_id").filter(lambda x: len(x) >= 20)
```

Retention: `top_10000` → 9,643 users; `random_10000` → 3,991 users. The random set loses 60% because those users have few scores and most enjoyment values collapse to zero after stabilization filtering.

## Per-user rating normalization

Raw engineered enjoyment scores have a wide range (observed −4.875 to +10.311 after the baseline/variance adjustment). Before feeding to Surprise's `Reader(rating_scale=(0.0, 1.0))`, min-max normalize **per user**:

```python
# per-user min-max to [0, 1]
df['rating'] = df.groupby('user_id')['rating'].transform(
    lambda x: (x - x.min()) / (x.max() - x.min() + 1e-9)
)
```

This matters because Surprise silently clips out-of-range ratings.
