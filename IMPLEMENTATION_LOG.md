# OWC Mappool — implementation log

Session date: **2026-05-05**. This file records what was built, what was considered and ruled out, and what remains for follow-up sessions. Source-of-truth approved plan: `~/.claude/plans/we-have-an-extremely-shiny-hamming.md`.

## What we did (Phase 1 — shipped)

### Documentation

Two files under `docs/OWC/Mappool/` (sibling of `docs/knowledge-base/`, not nested inside it — the user explicitly placed it under `docs/OWC/`):

- [`pool-structure.md`](./pool-structure.md) — what an OWC mappool is, mod brackets, pool composition tables for 2022–2024 (15 = 4/2/2/3/3/1, 20 = 5/3/3/4/4/1) and pre-2022 (15 = 5/2/2/3/2/1, 20 = 6/3/3/4/3/1), match flow, era history (OWC #1 2011 NM-only → 2013–14 introduction of brackets → 2015–18 emergence of slot conventions → 2019–21 peak specialisation → 2022 `NM5 → FM2` rebalance → 2023–24 steady state → 2025 group-stage + double-elimination), tiebreaker tradition (Camellia OOPARTS 2020, Yooh RPG 2021, Camellia Operation: Zenithfall 2024), Liquipedia page-structure notes for the scraper.
- [`slot-guide.md`](./slot-guide.md) — H2 per category (NM, HD, HR, DT, FM, TB), H3 per slot ordinal with intent / typical BPM-SR-AR ranges / 2–3 archetypal examples / era evolution notes, glossary inlined at the bottom (alt, antimod, AR change, burst, finger control, flow aim, gimmick, HDHR, jump map, low-AR, precision, reading, rhythm control, snap aim, stamina speed, stream, SV, swing, tech).

Style matches `docs/knowledge-base/`: no frontmatter, H1 + H2/H3, pipe tables, code blocks for wikitext, cross-refs into `knowledge-base/game/mods.md` and `difficulty-attributes.md` for canonical definitions.

Index/citation updates:
- `docs/README.md` — reframed as "two top-level sections" (`knowledge-base/` + `OWC/`), added `OWC/Mappool/` to the layout tree.
- `docs/sources.md` — new "Liquipedia + Reddit + osu! wiki" section listing the reddit guide, Liquipedia API, per-edition pages, osu! wiki, OWC 2022 announcement, and Bandcamp/YouTube tiebreaker confirmations.

### Liquipedia scraper

Code under `src/all_of_osu_db/layerA/`:

- `liquipedia.py` — `LiquipediaClient` (httpx-based MediaWiki API client with 30 s rate limit per ToS, on-disk wikitext cache keyed by page slug, retries with exponential backoff, redirects followed); `iter_owc_editions(through_year)` discovery (`/1`, `/2`, `/3`, then `/2013`–`/2025`); `_find_mappool_section` + `_split_into_rounds` using `mwparserfromhell` for section navigation; `scrape_edition` + `scrape_owc` orchestrators that write JSON per `(edition, round)` and a top-level `index.json` manifest.
- `liquipedia_parsers/types.py` — `MapEntry` dataclass with the full Phase-1 schema (`tournament`, `tournament_slug`, `round`, `slot`, `slot_category`, `slot_index`, `beatmap_artist`, `beatmap_title`, `beatmap_difficulty`, `beatmap_id`, `beatmapset_id`, `mod_set`, `raw_wikitext`, `source_url`, `source_revision`, `parser_version`, `scraped_at`).
- `liquipedia_parsers/plain_bullet.py` — primary parser for `* '''SLOT''' : [URL <nowiki>Artist - Title (Mapper) [Diff]</nowiki>]` (the format actually used across OWC 2011 + 2020–2025 per direct API inspection).
- `liquipedia_parsers/dispatch.py` — try parsers in order; emit a single `slot="UNKNOWN"` warning row per round if nothing matches, so older / template-only editions don't crash the run.
- CLI in `src/all_of_osu_db/cli.py` — `layerA` Typer sub-app with `liquipedia owc [--year N] [--include-qualifier/--no-qualifier] [--refresh-cache] [--dry-run] [--through-year N]`.

### Configuration & plumbing

- `src/all_of_osu_db/config.py` — added `liquipedia_user_agent`, `liquipedia_cache_dir`, `liquipedia_output_dir`, `liquipedia_min_request_interval_s` (default 30 s).
- `.env.example` — same four keys mirrored with comments on the ToS rate limit.
- `environment.yml` — added `httpx` + `mwparserfromhell` (conda-forge).
- `pyproject.toml` — added `httpx` + `mwparserfromhell` to `[project] dependencies`; added `[tool.pytest.ini_options]` with `pythonpath = ["src"]` so tests can import the package without an editable install.
- `README.md` — §4 source table (Liquipedia row), §6 layout (`layerA/liquipedia.py`, `layerA/liquipedia_parsers/`, `docs/OWC/Mappool/`), §7 CLI surface (`all-of-osu layerA liquipedia owc ...`), §12 footnote on wiki/web sources deviating from the SQL-dump-per-source pattern.
- `.gitignore` — no change needed; existing `data/` rule already gitignores everything the scraper writes.

### Tests

`tests/test_liquipedia_parser.py` — 9 fixture-driven tests, no network. Cover: modern plain-bullet extraction, artist/title/difficulty parsing, provenance fields populated, legacy bare-URL form (`osu.ppy.sh/beatmaps/<bid>` without set ID), unknown-layout warning row, empty input, slot-regex compliance, three parametrised "unrecognised line is skipped" cases. **All 9 tests pass** (`pytest tests/test_liquipedia_parser.py`).

## What we considered and ruled out

| Option | Why rejected |
| --- | --- |
| Single monolithic `OWC/Mappool/README.md` | User chose two-file split for navigability; matches knowledge-base 1–4-file-per-folder norm. |
| Four files (`README` + `pool-structure` + `slot-guide` + `glossary`) | User trimmed to two; glossary inlined into `slot-guide.md`. |
| MySQL Layer A schema `liquipedia.*` for v1 | README §12 wants one MySQL schema per source, but Liquipedia is wikitext, not a SQL dump. Inventing a schema before seeing edition variation is premature. JSON cache lets us iterate, then commit to a schema in Phase 3. |
| Direct Postgres `tournament_mappool` table for v1 | Same reason — locks in a Layer B contract before we've seen the wikitext variation. Deferred to Phase 3 once name → beatmap_id resolution is also tackled. |
| Scope: only 2022–2024 (modern era) for Phase 1 | User chose all editions 2011–2024 (and the parser tolerates 2025 too). The dispatcher's warning-row fallback handles edition formats the parser doesn't know yet. |
| Scope: just transcribe the reddit guide | User chose "deep multi-era history" — `pool-structure.md` covers OWC #1 NM-only era through 2025 group-stage rebalance. |
| `{{Map|...}}` template parser as a primary code path | Direct API inspection showed `{{Map|...}}` is a *match-result* template (score1/score2/winner), not a mappool definition. Plain wiki bullets are what mappool sections actually use. The originally-planned `map_template.py` module was renamed to `plain_bullet.py` to match reality; `dispatch.py` keeps the multi-parser shape so additional parsers can be added in Phase 2 without re-architecting. |
| Auto-detect latest revision via `action=query` before re-fetching | Adds complexity for marginal benefit on pages that change infrequently. v1 caches by slug only; `--refresh-cache` forces re-fetch. Worth revisiting if Phase 2 surfaces frequently-edited tournaments. |
| Bundle scraper output into the git repo | `data/` is gitignored. Output files are reproducible from the cache; users run the scraper locally. |

## How to run

```bash
conda env create -f environment.yml      # first time only
conda activate all-of-osu-db
pip install -e .                         # so all-of-osu CLI is on PATH

all-of-osu layerA liquipedia owc --dry-run            # see what would happen, no writes
all-of-osu layerA liquipedia owc --year 2024          # one edition (≈2 API calls = 1 minute)
all-of-osu layerA liquipedia owc                      # all editions (≈25 calls × 30 s ≈ 13 min cold)
all-of-osu layerA liquipedia owc --refresh-cache      # bypass on-disk cache
```

Output lands at `data/layerA/liquipedia/osu_world_cup/<edition>/<round>.json` (gitignored), with a top-level `data/layerA/liquipedia/index.json` manifest summarising the run.

## Verification checklist (per the approved plan)

When you do the first real scrape:

1. **Single-edition manual diff** — scrape `Osu_World_Cup/2023`; open the Liquipedia page in a browser; assert every Grand Finals slot in the JSON matches the page (count, slot order, beatmap titles).
2. **Slot regex** — every emitted `slot` matches `^(NM[1-9]|HD[1-9]|HR[1-9]|DT[1-9]|FM[1-9]|TB)$`. Anything else means a parser miss; track it.
3. **Pool-size invariants** — RO32 / RO16 → 15 maps; QF → GF → 20 maps. Warn (don't fail) on mismatches: older editions (2011–2014) and 2025 group-stage will violate this legitimately.
4. **Determinism** — two consecutive runs with cache enabled produce byte-identical JSON.
5. **Rate-limit conformance** — log every API call with timestamp; assert no two `parse` calls within 30 s.
6. **Doc cross-link audit** — every `[…](../../knowledge-base/…)` link in the new docs resolves.

The unit tests already cover (1)/(2) for the parser; the rest are integration checks against real Liquipedia data.

## What's next

### Phase 2 — expand scraper to all S-Tier osu!standard tournaments

- Iterate `https://liquipedia.net/osu/S-Tier_Tournaments`; filter out tournament names matching `(?i)taiko|catch|mania`.
- Reuse `LiquipediaClient` and the dispatcher; expect new wikitext template variants to surface — add new parsers as siblings under `liquipedia_parsers/`.
- Extend the JSON output layout: `data/layerA/liquipedia/<tournament_slug>/<round>.json`. The current `osu_world_cup/<edition>/...` layout is OWC-specific and should be generalised when Phase 2 starts.
- Track unknown-layout warning rows centrally to drive parser additions.

### Phase 3 — Layer B `tournament_mappool` projection

- Resolve `(beatmap_artist, beatmap_title, beatmap_difficulty)` → `beatmap_id` via `osu_beatmaps` from the ppy dump (Layer A `ppy_dump.*`), with osu! API v2 fallback for misses.
- New `sql/layerB_tournament_mappool.sql` (DDL), `src/all_of_osu_db/etl/tournament_mappool.py` (Layer A JSON + ppy dump → Layer B Postgres), §8-style contract block in README.
- Decide schema: flat `(tournament, round, slot, beatmap_id, …)` per pick, or normalised `tournaments` / `rounds` / `picks` 3-table schema. Likely flat for v1 since downstream queries will be `WHERE tournament = 'OWC 2024' AND round = 'Grand Finals'`.
- Capture which Liquipedia-supplied beatmap_ids matched the dump cleanly vs. which required API fallback vs. which we couldn't resolve — useful for spotting Liquipedia data quality issues.

### Phase 1.5 — incremental polish (when Phase 2 starts)

- Refresh the docs (`pool-structure.md`, `slot-guide.md`) with anything surprising that surfaces in real wikitext (e.g., undocumented slot conventions in pre-2018 editions).
- Add a per-edition pool-size invariants table to the verifier so off-format editions warn predictably instead of being noisy.
- Consider an optional `--latest-revision-check` flag that does a cheap `action=query&prop=info` before each `parse` to skip cached pages whose revid is unchanged — only worth it if Phase 2 surfaces frequently-edited tournament pages.
