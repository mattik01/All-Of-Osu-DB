# Official data sources: API v2 & data dumps

## Primary: `data.ppy.sh` monthly MySQL dumps

The canonical, bulk source for osu! data. See `../data-dump/overview-and-tables.md` for full schema coverage.

- URL: <https://data.ppy.sh/>
- Cadence: monthly, usually published a few days into each month (sometimes delayed).
- Slices: `top_1000`, `top_10000`, `random_10000` × 4 modes. **No "all beatmaps" option.**
- Format: MySQL dump, multi-GB per slice.
- Reference generator: [`ppy/osu-performance-datasets-generator`](https://github.com/ppy/osu-performance-datasets-generator) — read its README and `dump_all.sh` for authoritative contents.

**Legal**: dump redistribution is restricted. Private/personal use accepted; **public SQL endpoints or mirrored dumps require permission from contact@ppy.sh**. `All-Of-Osu-DB`'s Layer B is local-only for this reason — see the main README §14.

## Recommended wrapper: `Eve-ning/osu-data`

[`osu-data`](https://github.com/Eve-ning/osu-data) — pip package that downloads + imports dumps into a local Docker MySQL on **port 3308**. Handles the boring parts. This is what `All-Of-Osu-DB` builds on.

CLI flags (re-stated because they matter):
- `-m/--mode`: `osu / taiko / fruits / mania`.
- `-v/--version`: `top_1000 / top_10000 / random_10000`.
- `-y/--ymd`: dump date `YYYY_MM_DD`; leave blank for latest.
- Port 3308 is hardcoded by the tool.
- Persists data across runs by default — remove the compose project to force refresh.

Image redistribution of its built Docker images is not allowed per its README.

## Official osu! API v2

The live API. `https://osu.ppy.sh/api/v2/...` with OAuth2 client-credentials / authorization-code.

**Neither source repo encodes its endpoints, auth flow, or rate limits authoritatively.** RecSys-Study's `schema-info.md` mentions only:

- Rate limit is strict enough that a scraping campaign risked getting banned — the author explicitly marked their scraping folder `(inactive)` and pivoted to dumps.
- The common community-cited ceiling is ~1,200 req/min (unofficial / anecdotal; not confirmed).
- Pagination depth is undocumented and likely has a hard cap.

For exact usage go to:
- <https://osu.ppy.sh/docs/> — official API docs.
- `osu-api` Discord / <https://github.com/ppy/osu-api>.

In `All-Of-Osu-DB`'s architecture, API v2 is a **future Layer A source** for targeted top-ups between monthly dumps (see main README §12) — not yet implemented.

## osu! API v1

Legacy, key-based API. Smaller surface, still functional but deprecated for new work. Not used in either source repo.

## Hugging Face: `lekdan/osu`

Mentioned in `All-Of-Osu-DB`'s main README §4 as an optional cross-check / Parquet offline dataset. **Neither source repo actually uses it** — included here for completeness.

- URL pattern: `https://huggingface.co/datasets/lekdan/osu`
- Use case: Parquet mirror for faster offline analytical queries.

## Other osu! data APIs (unofficial)

### osu!track

<https://osutrack-api.ameo.dev> — third-party service tracking osu! player rank/PP history over time. Covers the "how did this player progress" dimension that the dumps don't (dumps are point-in-time, not longitudinal).

- Referenced in `All-Of-Osu-DB` main README §4 as a future Layer A source.
- RecSys-Study doesn't use it but mentions it as a potential feature for the progression-aware research direction.

### Beatmap mirrors

- **catboy.best** — beatmap audio/asset mirror. <https://catboy.best/>
- **osu.direct** — same role.

These mirror `.osu` files + audio for offline use. Relevant when you want beatmap content, not just metadata. `All-Of-Osu-DB` main README §4 lists these as a future on-demand Layer A source.

## Rate limit & auth summary (what we know)

| Source | Auth | Rate limit |
| --- | --- | --- |
| `data.ppy.sh` dump | None (just HTTP download) | — |
| osu! API v2 | OAuth2 | Strict (~1200/min unofficial); go read the docs |
| osu!track | None per-request key needed per community convention | Not documented here |
| catboy/osu.direct | None, direct download | Be polite; no documented limit here |

## What's NOT here

Anything beyond what the two source repos mention. For endpoint paths, response schemas, OAuth flow — read the osu! wiki and the official API docs.
