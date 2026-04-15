# Community recommenders & tools

Collected from `documentation/Inital Ideas.md` — prior art for "recommend osu! beatmaps to users" and adjacent tooling. These are references, not dependencies.

## Recommenders

### Tillerino

<https://github.com/Tillerino/Tillerinobot/wiki>

In-IRC-lobby bot. Recommends beatmaps based on the user's top-10 plays. Oldest widely-used recommender.

- **Approach**: collaborative filtering on top-plays.
- **Bias the author flags**: top-plays-driven = strong bias toward farm maps (top plays = highest-PP plays = often farm).
- Still actively used in the osu! IRC community.

### Dynam1cBOT

Skill-fingerprint recommender. For a target user, recommends three maps: easier / match / harder, each ≈80% match quality.

- **Approach**: constructs a multi-dimensional "skill fingerprint" per user (likely along axes similar to RecSys-Study's `aim / speed / strain / approach`), matches to beatmap fingerprints.
- No public code repo documented here; known in the osu! community.

### AlphaOsu!

<https://alphaosu.keytoix.vip/self/pp-recommend>

PP-gain-maximising recommender. Given your current top-100, it suggests maps that would most raise your weighted PP.

- **Approach**: optimiser on expected PP delta.
- **Explicit bias**: farm-first by design. Not a taste-matcher; a goal-optimiser.

### m1tm0 (in-development)

- Reddit threads: [2025-05-12](https://www.reddit.com/r/osugame/comments/1kkj2zr/), [2025-05-21](https://www.reddit.com/r/osugame/comments/1kqjags/osu_recsys_looking_for_alpha_testers/).
- **Approach**: switched to **Bayesian Personalized Ranking** for scalability.
- Discord-bot delivery channel.
- Status as of `Inital Ideas.md`: alpha-testing phase.

### RecSys-Study (the sibling repo itself)

See `analysis/dataset-and-biases.md` for its evaluation numbers. Main contribution: the **engineered `enjoyment` rating + per-user 99th-percentile sensitive-attribute filter** for diversity/constraint-aware recommendation.

## Auto-tagging / map classification

### `osu_oracle`

<https://github.com/token03/osu_oracle>

Automatic beatmap classifier. Produces content tags (stream / jump / tech / alternating / etc.) from beatmap features. Called out as "the most promising auto-tagger" by the author of `Inital Ideas.md`.

- If you need rough content labels per beatmap and don't want to build one from scratch, this is where to look.

### osu! lazer community tagging

The lazer client has a community-driven tagging feature (users add / vote on tags per beatmap). Still young; data surface for this is not documented in the sources.

## Adjacent user-facing tools

### osu!Collector

<https://osucollector.com>

User-collection sharing. 42,300 users / 12,600 collections at time of writing (`Inital Ideas.md`). Users curate themed beatmap collections — an implicit-feedback signal (inclusion in a collection = "I like these together").

If you ever need "ground truth for beatmap similarity," scraping `osuCollector` collection membership is a reasonable starting point.

### Stream / Stamina Map Bot

<https://ost.sombrax79.org/commands>

Community-curated stamina-map list. Narrow taxonomy (stream maps specifically) but human-validated.

### Osufy

<https://osufy.lonke.ro>

Spotify → beatmap mapper. Given a Spotify playlist, finds osu! beatmaps for those songs. More a music-discovery tool than a beatmap recommender.

## Tagging / taxonomy resources

### Spanish osu! wiki — Beatmap Tags page

<https://osu1.roanh.dev/wiki/es/Beatmap/Beatmap_tags>

Extensive technical taxonomy for beatmap content tags. The author of `Inital Ideas.md` considers it the most comprehensive tag reference available.

### Forum / reddit threads on map labeling

- <https://osu.ppy.sh/community/forums/topics/1928067>
- <https://www.reddit.com/r/osugame/comments/1c3uo8s/>
- <https://www.reddit.com/r/osugame/comments/1dcz7ml/>
- <https://www.reddit.com/r/osugame/comments/1kkj2zr/>

Informal but useful — community discussion of how content tags should work, which ones are load-bearing, edge cases.

## Prior-art summary as a table

| Tool | Approach | Signal | Farm-biased? |
| --- | --- | --- | --- |
| Tillerino | top-plays CF | implicit (user's top 10) | Yes |
| Dynam1cBOT | skill fingerprint | derived | Less (by design) |
| AlphaOsu! | PP optimiser | implicit | Very much yes (by design) |
| m1tm0 | BPR | implicit | Unknown |
| RecSys-Study | engineered enjoyment + CF | synthetic rating | Explicitly modelled |
| osu_oracle | content classifier | beatmap features only | N/A (no user) |
| osu!Collector | collections | explicit (via curation) | No (curated) |
