# All-Of-Osu DB

A general-purpose osu! data resource. Not a single-pipeline tool — a **shared
reference database** fed primarily by peppy's monthly data.ppy.sh dump,
designed to absorb additional osu! data sources over time, and served as a
curated Postgres slice that any osu! project (mine or otherwise) can query
without hammering the live osu! API.

> **Status**: scaffolding only. README is complete; no ingest/ETL code yet.
> The implementation order at the bottom of this file is the backlog.

---

## 1. Why this repo exists

I'm building multiple osu!-related projects that all need the same baseline
facts: "which beatmaps exist, which are popular, what metadata do they carry."
The osu! API v2 is rate-limited (~1200 req/min, pagination depth cap is
undocumented) and wasteful to hammer repeatedly for data that barely changes
month-to-month.

peppy publishes monthly MySQL dumps at https://data.ppy.sh that contain almost
everything we'd want. Several community tools already wrap the download +
import (most notably [`Eve-ning/osu-data`][osudata]). But:

- The raw dump is tens of GB, many tables, legacy naming, MySQL-only.
- Most consumers only want a small, clean slice.
- Some consumers want to mix in *other* sources (live API top-ups, osu!track
  history, community mirrors) — the dump alone isn't enough.

So this repo is **one layer to hold raw sources, one layer to serve curated
slices**, and a clean Postgres contract for downstream projects.

---

## 2. Primary consumer

- [`Osu-Replay-To-YT`][yt] — automated pipeline that publishes osu! replay
  videos to YouTube. It queries Layer B (beatmap reference slice) for
  popularity-ranked candidates instead of crawling the osu! API. Contract is
  documented in §11 below.

Any future osu! project of mine that wants read-only access to beatmap / score
/ user data should consume Layer B.

[yt]: https://github.com/mattik01/Osu-Replay-To-YT

---

## 3. Architecture: two layers

```
 ┌─────────────────────────────────────────────────────────────┐
 │  LAYER A — raw sources (MySQL, local, provenance-preserving)│
 │                                                             │
 │   ppy_dump.*           ← Eve-ning/osu-data, monthly         │
 │   osu_api_v2.*         ← (future) targeted top-ups          │
 │   osu_track.*          ← (future) player history snapshots  │
 │   <source>.<table>     ← one schema namespace per source    │
 └──────────────────────────────┬──────────────────────────────┘
                                │  ETL (src/all_of_osu_db/etl/)
                                ▼
 ┌─────────────────────────────────────────────────────────────┐
 │  LAYER B — curated slices (Postgres, local, consumer-facing)│
 │                                                             │
 │   beatmap_reference    ← one row per difficulty (v1)        │
 │   <future projections> ← scores, users, etc. on demand      │
 │   popularity_v / *_v   ← views and materialized views       │
 └─────────────────────────────────────────────────────────────┘
                                │
                                ▼
              downstream projects (plain Postgres URL)
```

### Layer A — raw source mirror (local MySQL)

- Holds each source **as-imported**, with its original table and column
  names. No cleaning, no renames.
- Schema naming convention: `<source>.<table>`. `ppy_dump` is the first; new
  sources go into their own schemas (or table prefixes if multi-schema isn't
  worth the complexity for that source).
- The ppy dump sub-layer is managed by [`osu-data`][osudata], a pip package
  that downloads from data.ppy.sh and imports into a Docker MySQL on port
  **3308** (root user, no password by default). It tunes MySQL for import
  speed, not production (`innodb_doublewrite=0`). We accept that trade-off
  because Layer A is a staging area — Layer B is what we query in anger.
- **Why keep Layer A at all** instead of ETL-on-download:
  1. Re-running ETL is cheap; re-downloading 16 GB is not.
  2. Future consumers may need columns/tables the v1 ETL throws away.
  3. Diffable against Layer B when something downstream looks wrong.

### Layer B — curated slice (local Postgres)

- Derived from Layer A by ETL scripts. Clean schema, sensible names, sensible
  types, precomputed derived columns, indexes sized for real queries.
- Postgres 16 in Docker (see `docker-compose.yml.example`). Portable schema —
  the same dump/restore works against a managed Postgres (Supabase, Neon,
  VPS) when we're ready to host remotely.
- v1 projection: **`beatmap_reference`** (§8). Other projections (scores,
  users, recsys-style enrichments) are added when a consumer needs them.

[osudata]: https://github.com/Eve-ning/osu-data

---

## 4. Data sources

| Source                   | Role                                | Cadence   | Status       |
| ------------------------ | ----------------------------------- | --------- | ------------ |
| data.ppy.sh MySQL dump   | Primary: beatmaps, scores, users    | Monthly   | v1 target    |
| Liquipedia (osu! wiki)   | Tournament mappools (OWC first)     | On demand | Layer A SQLite + Layer B `tournament_mappool` |
| osu! API v2              | Incremental top-ups between dumps   | On demand | Future       |
| osu!track API            | Player rank/performance history     | On demand | Future       |
| catboy.best / osu.direct | Beatmap audio/asset mirror          | On demand | Future       |
| HuggingFace `lekdan/osu` | Cross-check / Parquet offline views | Static    | Optional     |

Only the ppy dump is in scope for v1. The table above sets direction —
subsequent sources land in their own Layer A namespace per §12.

**Dump slicing (important):** `osu-data` does not expose "all beatmaps ever."
Its `-v/--version` flag is one of `top_1000`, `top_10000`, `random_10000`
(scores/coverage slices of ppy's dump). For `Osu-Replay-To-YT` the `top_10000`
slice of mode `osu` is expected to be sufficient — it covers the popular maps
a YouTube upload pipeline would care about. Verify at first ingest.

---

## 5. Stack

| Concern       | Choice                         | Why                                                      |
| ------------- | ------------------------------ | -------------------------------------------------------- |
| Language      | Python 3.11+                   | Matches sibling repos, rich ecosystem for SQL/ETL.       |
| Environment   | conda (Miniconda / Miniforge)  | `environment.yml` at repo root; one isolated env per repo. |
| Config        | `pydantic-settings` + `.env`   | One schema, one source of truth.                         |
| Layer A DB    | MySQL 8 (in Docker)            | Native to ppy's dump — zero conversion risk on import.   |
| Layer A ingest| `osu-data` (pip)               | Already solves download + import + monthly cadence.      |
| Layer B DB    | Postgres 16 (in Docker)        | Better tooling; PostgREST path to SQL-over-HTTP later.   |
| ETL           | Python + SQLAlchemy or raw SQL | TBD — raw SQL is fine if transforms stay simple.         |
| Test runner   | `pytest`                       | Standard.                                                |
| Lint/format   | `ruff`                         | Standard.                                                |

Explicit non-choices:
- **pgloader / DuckDB as Layer A**: rejected. MySQL-native avoids conversion
  edge cases (enums, bitfields, charsets). Can be revisited later.
- **Managed cloud DB for Layer B**: deferred until a remote consumer needs it.

---

## 6. Planned repo layout

```
All-Of-Osu-DB/
├─ README.md                       ← this file
├─ LICENSE                         ← MIT (code only; ppy marks excluded)
├─ .gitignore
├─ .env.example
├─ docker-compose.yml.example      ← Postgres service for Layer B
├─ environment.yml                 ← conda env `all-of-osu-db`, Python 3.11+
├─ pyproject.toml                  ← package metadata + CLI entry (not yet created)
├─ docs/
│   ├─ knowledge-base/             ← osu! domain facts (mods, dump schema, etc.)
│   ├─ OWC/Mappool/                ← osu! World Cup mappool reference
│   ├─ schema.md                   ← Layer B columns + Layer A provenance
│   └─ runbook.md                  ← monthly refresh playbook
├─ sql/
│   ├─ layerA_liquipedia.sql       ← SQLite DDL for tournament_pick (Liquipedia mirror)
│   ├─ layerB_schema.sql           ← Postgres DDL for Layer B tables
│   ├─ layerB_tournament_mappool.sql ← Postgres DDL for the OWC mappool projection
│   └─ layerB_views.sql            ← popularity_v + convenience views
├─ src/all_of_osu_db/
│   ├─ __init__.py
│   ├─ config.py                   ← pydantic-settings
│   ├─ cli.py                      ← `refresh | etl | validate | export-parquet`
│   ├─ layerA/
│   │   ├─ __init__.py
│   │   ├─ ppy_dump.py             ← thin wrapper around `osu-data` CLI
│   │   ├─ liquipedia.py           ← OWC mappool scraper (JSON output)
│   │   ├─ liquipedia_parsers/     ← wikitext dispatcher + per-format parsers
│   │   ├─ verify_mappool.py       ← osu! API v2 verification of scraped beatmap_ids
│   │   ├─ liquipedia_load.py      ← verified CSV → Layer A SQLite (tournament_pick)
│   │   ├─ osu_api_v2.py           ← OAuth2 client + batched /beatmaps lookup
│   │   └─ (future) osu_track.py
│   ├─ etl/
│   │   ├─ __init__.py
│   │   ├─ beatmap_reference.py    ← MySQL(ppy_dump) → Postgres(Layer B)
│   │   └─ tournament_mappool.py   ← SQLite(liquipedia) → Postgres(Layer B)
│   └─ validate.py                 ← post-ETL sanity checks
└─ tests/
    └─ test_etl_shape.py           ← fixtures + ETL transform tests
```

---

## 7. CLI surface (planned)

```
all-of-osu refresh                # full cycle: pull dump → import A → ETL → validate
all-of-osu refresh --skip-download   # re-use last downloaded dump
all-of-osu etl                    # re-run ETL only (iterate on Layer B shape)
all-of-osu validate               # row counts, spot checks
all-of-osu export-parquet         # optional Parquet artifact from Layer B
all-of-osu layerA ppy-dump \
    --mode osu --version top_10000 --ymd 2026_04_01

# Liquipedia tournament mappools (Layer A scrape → Layer B projection)
all-of-osu layerA liquipedia owc                       # all OWC editions, scrape JSONs
all-of-osu layerA liquipedia owc --year 2024
all-of-osu layerA liquipedia owc --year 2024 --no-qualifier
all-of-osu layerA liquipedia owc --refresh-cache
all-of-osu layerA liquipedia owc --dry-run
all-of-osu layerA liquipedia export-csv                # flatten JSONs to one CSV
all-of-osu layerA liquipedia verify-mappool            # API-verify + CSV + Layer A SQLite
all-of-osu layerA liquipedia load-sqlite               # load verified CSV into SQLite (standalone)
all-of-osu etl tournament-mappool                      # Layer A SQLite → Layer B Postgres
```

Implement with `typer` or `click`; exact choice when coding begins.

---

## 8. Layer B v1 schema — `beatmap_reference`

The contract that `Osu-Replay-To-YT` will depend on. One row per difficulty.
Filtered to `status ∈ {ranked, loved}` unless a consumer needs more.

| Column             | Type           | Source (Layer A `ppy_dump.*`)        | Notes                                           |
| ------------------ | -------------- | ------------------------------------ | ----------------------------------------------- |
| `md5`              | `char(32) PK`  | `osu_beatmaps.checksum`              | In-game hash; primary key.                      |
| `beatmap_id`       | `bigint`       | `osu_beatmaps.beatmap_id`            | Per-difficulty ID. Indexed.                     |
| `set_id`           | `bigint`       | `osu_beatmaps.beatmapset_id`         | Indexed.                                        |
| `mode`             | `smallint`     | `osu_beatmaps.playmode`              | 0=std, 1=taiko, 2=catch, 3=mania.               |
| `status`           | `smallint`     | `osu_beatmaps.approved`              | -2 graveyard … 4 loved. Filter in views.        |
| `artist`           | `text`         | `osu_beatmapsets.artist`             |                                                 |
| `title`            | `text`         | `osu_beatmapsets.title`              |                                                 |
| `creator`          | `text`         | `osu_beatmapsets.creator`            |                                                 |
| `version`          | `text`         | `osu_beatmaps.version`               | Difficulty name (e.g. "Insane").                |
| `length_s`         | `integer`      | `osu_beatmaps.total_length`          | Seconds.                                        |
| `bpm`              | `real`         | `osu_beatmaps.bpm`                   |                                                 |
| `star_rating`      | `real`         | `osu_beatmaps.difficultyrating`      | NM stars; mod-adjusted SR deferred.             |
| `playcount`        | `bigint`       | `osu_beatmaps.playcount`             |                                                 |
| `passcount`        | `bigint`       | `osu_beatmaps.passcount`             |                                                 |
| `favourites`       | `bigint`       | `osu_beatmapsets.favourite_count`    | Set-level fav count; replicated per diff.       |
| `approved_date`    | `timestamptz`  | `osu_beatmapsets.approved_date`      | Nullable. Set-level field; `osu_beatmaps` has no approved_date in the dump. Stored UTC-naive in MySQL; coerced via `AT TIME ZONE 'UTC'` on insert. |
| `popularity_rank`  | `integer`      | derived                              | `rank() over (partition by mode order by playcount desc)`. |
| `last_refreshed`   | `timestamptz`  | ETL clock                            | When this row was last rewritten.               |

Indexes:
- PK on `md5`.
- `(mode, popularity_rank)` — primary query shape for downstream.
- `(set_id)`, `(beatmap_id)`.
- Full-text on `(artist, title, version, creator)` — optional, Phase 2.

**Provenance disclaimer**: exact ppy column names above are derived from
community reference (Osu-RecSys-Study schema notes) and the standard osu!
schema. Confirm against a live dump on first import; adjust the ETL and this
table as needed. Any deviation from what's written here must update *this
README* in the same PR.

Views (`sql/layerB_views.sql`):
- `ranked_std_popular_v` — `beatmap_reference` filtered to `mode=0` and
  `status IN (1,2,4)`, ordered by `popularity_rank`.
- `by_md5_v` — convenience single-row lookup shape.

---

## 8.1 Layer B — `tournament_mappool` (Liquipedia projection)

Curated slice of the Liquipedia OWC scraper output. One row per pick
(unique by `(tournament_slug, round, slot)`). Filtered to picks where the
osu! API v2 verifier resolved the beatmap — `missing` and `no_id` rows
from Layer A are excluded; `mismatch` rows are kept (the beatmap_id is
still valid, only post-tournament metadata renames diverged).

| Column            | Type          | Source (Layer A `tournament_pick`) | Notes                                          |
| ----------------- | ------------- | ---------------------------------- | ---------------------------------------------- |
| `tournament_slug` | `text PK`     | `tournament_slug`                  | Stable id e.g. `Osu_World_Cup/2024`.           |
| `round`           | `text PK`     | `round`                            | E.g. `Grand Finals`, `Round of 32`, `Mappool`. |
| `slot`            | `text PK`     | `slot`                             | E.g. `NM1`, `HD2`, `TB`.                       |
| `tournament`      | `text`        | `tournament`                       | Display name, e.g. `osu! World Cup 2024`.     |
| `slot_category`   | `text`        | `slot_category`                    | `NM \| HD \| HR \| DT \| FM \| TB`.            |
| `slot_index`      | `smallint`    | `slot_index`                       | 1, 2, 3, … or `NULL` for `TB`.                 |
| `mod_set`         | `text`        | `mod_set`                          | Usually equals `slot_category`.                |
| `beatmap_id`      | `bigint NN`   | `api_beatmap_id`                   | osu! API verified to exist.                    |
| `beatmapset_id`   | `bigint`      | `api_beatmapset_id`                |                                                |
| `artist`          | `text`        | `api_artist`                       | osu!-side metadata (authoritative).            |
| `title`           | `text`        | `api_title`                        |                                                |
| `difficulty`      | `text`        | `api_difficulty`                   |                                                |
| `ranked_status`   | `text`        | `api_ranked_status`                | `ranked \| loved \| qualified \| graveyard \| …`. |
| `source_url`      | `text`        | `source_url`                       | Liquipedia page back-reference.                |
| `last_refreshed`  | `timestamptz` | ETL clock                          | Set on each `etl tournament-mappool` run.      |

Indexes: PK; `(beatmap_id)`; `(tournament_slug)`; `(mod_set)`.

Layer A columns *not* included in this projection (kept in the SQLite
mirror for forensic queries): `liquipedia_artist/title/difficulty`,
`parser_version`, `source_revision`, `scraped_at`, `verified_at`,
`verify_status`. To inspect mismatches or unresolved picks, query the
SQLite directly.

Provenance: see `data/layerA/liquipedia/liquipedia.sqlite::tournament_pick`
and `docs/OWC/Mappool/`.

---

## 9. Setup / first run

### Prerequisites (install these yourself before running any step below)

The repo assumes **nothing** beyond a working shell. Install each tool once:

| Tool                       | Why                                                          | Install                                                                    |
| -------------------------- | ------------------------------------------------------------ | -------------------------------------------------------------------------- |
| Miniconda / Miniforge      | Drives the Python env from `environment.yml`.                | https://docs.conda.io/projects/miniconda/ or https://conda-forge.org/miniforge/ |
| Docker Desktop (or Engine) | Runs Layer B Postgres and `osu-data`'s Layer A MySQL.        | https://docs.docker.com/desktop/                                           |
| `psql` client (optional)   | Applying `sql/*.sql` by hand; also useful for spot queries.  | Bundled with any Postgres install, or install `postgresql-client`.         |
| `git`                      | Cloning this repo.                                           | https://git-scm.com/downloads                                              |

Python itself is provided by the conda env — don't install it separately.
All Python packages (`typer`, `osu-data`, `sqlalchemy`, etc.) are declared in
`environment.yml`; `conda env create` handles them.

### Steps

```bash
# 1. Clone and create the conda env
git clone <this repo>
cd All-Of-Osu-DB
conda env create -f environment.yml
conda activate all-of-osu-db

# 2. Configure
cp .env.example .env
# edit .env — at minimum set LAYER_B_PG_PASSWORD

# 3. Start Layer B Postgres
cp docker-compose.yml.example docker-compose.yml
docker compose up -d postgres

# 4. Apply Layer B schema
psql "$LAYER_B_PG_URL" -f sql/layerB_schema.sql
psql "$LAYER_B_PG_URL" -f sql/layerB_views.sql

# 5. Bootstrap Layer A (downloads ~GB of dump, takes a while)
all-of-osu layerA ppy-dump --mode osu --version top_10000

# 6. Run ETL into Layer B
all-of-osu etl
all-of-osu validate
```

To re-run after opening a new shell: `conda activate all-of-osu-db`.
To update deps after editing `environment.yml`: `conda env update -f environment.yml --prune`.

`osu-data` manages its own Docker container for MySQL on port 3308. Don't
publish a conflicting MySQL on that port.

---

## 10. Monthly refresh runbook (`docs/runbook.md` should expand this)

1. Check data.ppy.sh has a new dump for the target month (usually a few days
   into each month; sometimes delayed).
2. `all-of-osu refresh --mode osu --version top_10000 --ymd YYYY_MM_DD` (env must be activated)
   - Downloads the new dump into `osu-data`'s Docker volume.
   - `osu-data` preserves previous data by default; to replace, you must
     remove the compose project. Decision: replace on each refresh. The
     wrapper in `layerA/ppy_dump.py` automates this.
   - Runs the ETL into Layer B.
   - Runs `validate`.
3. Sanity-check the output: top-100 playcount matches osu.ppy.sh spot check,
   row counts within ±10% of the previous month.
4. If a consumer repo has a pinned date, bump its `.env` accordingly.

---

## 11. Downstream consumption contract

Consumers speak plain Postgres. No awareness of Layer A, `osu-data`, or the
ETL is required. `Osu-Replay-To-YT` uses:

```ini
# in Osu-Replay-To-YT .env
BEATMAP_DB_URL=postgresql://osu:<password>@127.0.0.1:5432/all_of_osu
```

Canonical query shape:

```sql
SELECT md5, beatmap_id, set_id, artist, title, version, star_rating,
       playcount, favourites
  FROM beatmap_reference
 WHERE mode = 0
   AND status IN (1, 2, 4)
 ORDER BY popularity_rank
 LIMIT :n;
```

Or use the `ranked_std_popular_v` view.

**Breaking changes to `beatmap_reference` require a version bump** (ADR or
explicit note in release notes, plus a search of consumer repos). Add columns
freely; don't rename or drop.

### 11.1 Inspecting Layer B locally

Same connection for anything: consumer app, `psql`, DBeaver, HeidiSQL,
pgAdmin, VS Code SQLTools, etc. Pull credentials from your local `.env`:

```
Host:     127.0.0.1
Port:     $LAYER_B_PG_PORT   # default 5432; see note below
User:     $LAYER_B_PG_USER   # default osu
Password: $LAYER_B_PG_PASSWORD
Database: $LAYER_B_PG_DB     # default all_of_osu
```

**Port conflict with a native Postgres install:** if you already run a
Windows/macOS/Linux-packaged Postgres (e.g. `postgresql-x64-*` service),
it will hold `127.0.0.1:5432` before the Docker container can publish on
it. Symptom: password auth fails from the host but works via `docker exec`.
Either stop the native service, or bump `LAYER_B_PG_PORT` in `.env` (e.g.
`5433`) and `docker compose up -d postgres` — the compose file reads the
port from the env.

**psql one-liner (Docker container, no host client needed):**

```bash
docker exec -it all-of-osu-postgres psql -U "$LAYER_B_PG_USER" -d "$LAYER_B_PG_DB"
```

**From the host with a local `psql`:**

```bash
psql "postgresql://$LAYER_B_PG_USER:$LAYER_B_PG_PASSWORD@127.0.0.1:$LAYER_B_PG_PORT/$LAYER_B_PG_DB"
```

**Quick spot-check query** (top 5 most-played std difficulties):

```sql
SELECT popularity_rank, artist, title, version, playcount
FROM beatmap_reference
WHERE mode = 0 AND status IN (1, 2, 4)
ORDER BY popularity_rank
LIMIT 5;
```

Or run `all-of-osu validate` for the canned counts + spot check.

---

## 12. Extending Layer A with a new source

When a second source needs to land in Layer A:

1. Pick a **schema namespace** (e.g., `osu_api_v2`, `osu_track`) — use a
   Postgres-style `CREATE SCHEMA` on MySQL (via database naming) or a table
   prefix. Prefer one MySQL database per source where practical.
2. Create `src/all_of_osu_db/layerA/<source>.py` exposing a `refresh()`
   entrypoint and any helpers.
3. Document the source in the §4 table (role, cadence, status).
4. Decide if this source feeds a Layer B projection:
   - **Enriches an existing projection** (e.g., fresher playcount from API
     v2 overriding ppy dump): update `etl/beatmap_reference.py` to prefer the
     new source where applicable, document the precedence rule in
     `docs/schema.md`.
   - **Introduces a new projection** (e.g., `player_history`): add
     `sql/layerB_<projection>.sql`, `src/all_of_osu_db/etl/<projection>.py`,
     and a §8-style contract table for consumers.

Keep each source isolated enough that removing it is a one-file deletion.

**Wiki / web sources** (e.g. Liquipedia for tournament mappools) deviate from
the "MySQL schema per source" pattern: they have no SQL dump to mirror.
- v1: sink to a JSON file cache under `data/layerA/<source>/` while the shape stabilises across real data.
- v2: once stable, promote to a local **SQLite** sink (still Layer A; lives in
  the same `data/layerA/<source>/` directory). SQLite is preferred over the
  osu-data MySQL container because the wiki source has its own cadence and
  shouldn't get nuked when the monthly ppy-dump refresh wipes the MySQL
  container. Schema lives in `sql/layerA_<source>.sql`.

The OWC scraper (`src/all_of_osu_db/layerA/liquipedia.py` + `liquipedia_load.py`
+ `verify_mappool.py`) is the first instance of this pattern. Layer A artifact
is `data/layerA/liquipedia/liquipedia.sqlite` with one table `tournament_pick`
(every scraped row preserved, including audit rows). The corresponding Layer B
projection (`tournament_mappool`) is documented in §8.1.

---

## 13. Verification / sanity checks

- **Top-100 spot check**: Layer B `ORDER BY popularity_rank LIMIT 100` for
  `mode=0` matches popular maps listed on osu.ppy.sh (accepting the dump's
  staleness vs the live site).
- **MD5 round-trip**: known-map MD5 (e.g., Big Black [WHO'S AFRAID OF THE BIG
  BLACK?] — grab MD5 from osu! client) returns exactly one row with correct
  artist/title.
- **Idempotency**: running `refresh` twice on the same dump produces
  byte-identical Layer B row counts and per-column hashes.
- **Monthly rollover**: after replacing the dump, `validate` reports row
  counts within ±10% of the previous month (larger deltas = investigate).
- **Downstream smoke**: `psql $BEATMAP_DB_URL -c "SELECT count(*) FROM
  beatmap_reference"` from a consumer repo succeeds and returns >0.

---

## 14. Legal / ToS

- **Code**: MIT (see `LICENSE`). osu! and ppy trademarks are excluded.
- **ppy dumps**: redistribution is restricted. Consuming the dumps for
  personal / private use is accepted; **public SQL endpoints or mirrored
  dumps require emailing contact@ppy.sh for permission**. This repo never
  republishes ppy dump bytes — only derived columns in Layer B.
- **`osu-data` images**: per its README, do not redistribute the built
  Docker images.

While Layer B is local-only, none of the above is a concern. Revisit §14
before exposing any public endpoint.

---

## 15. Out of scope (for now)

- Public / remote hosting of Layer B (VPS, Supabase, Neon). Schema is
  portable; we'll push it when there's a reason to.
- Publicly-queryable SQL-over-HTTP (PostgREST etc.). Stub in the compose
  example, disabled.
- Score / user Layer B projections. Add when a consumer asks.
- Mod-bitmask collapse / farm-factor derived columns (see Osu-RecSys-Study
  for prior art). Relevant for score-level work, not for beatmap reference.
- Live API v2 top-ups between monthly dumps. Revisit if staleness bites.

---

## 16. Implementation order (the backlog)

If you're a fresh Claude session opening this repo, work in this order. Each
step is small enough to verify before moving to the next.

1. **Bootstrap Python project**
   - `environment.yml` at repo root defining a conda env `all-of-osu-db`
     (Python 3.11+, deps: `typer`, `pydantic-settings`, `sqlalchemy`,
     `pymysql`, `psycopg`/`psycopg-binary`, `ruff`, `pytest`, plus
     `osu-data` from pip).
   - Optional `pyproject.toml` for the `src/all_of_osu_db` package metadata
     + CLI entry point + `ruff` / `pytest` configs (installed into the conda
     env via `pip install -e .`).
2. **Config**
   - `src/all_of_osu_db/config.py` — pydantic-settings model loading `.env`,
     with the keys listed in `.env.example`.
3. **Layer B schema**
   - `sql/layerB_schema.sql` — `beatmap_reference` table per §8.
   - `sql/layerB_views.sql` — `ranked_std_popular_v`, `by_md5_v`.
   - Apply against the Postgres from `docker-compose.yml`.
4. **Layer A ingest wrapper**
   - `src/all_of_osu_db/layerA/ppy_dump.py` — shell out to `osu-data` with
     args from config, capture logs, handle the "preserves previous data"
     behavior by replacing the compose project when doing a refresh.
   - Verify a `top_10000` `mode=osu` ingest lands in MySQL on port 3308.
     Inspect the resulting tables against the column assumptions in §8 and
     **update §8 to match reality** before writing the ETL.
5. **ETL**
   - `src/all_of_osu_db/etl/beatmap_reference.py` — read from MySQL
     (`LAYER_A_MYSQL_*`), write to Postgres (`LAYER_B_PG_*`). Use
     server-side cursors on the MySQL side; batched `COPY` on the Postgres
     side. Upsert on `md5`. Compute `popularity_rank` in Postgres after
     load.
6. **Validate**
   - `src/all_of_osu_db/validate.py` — row counts, null checks on key
     columns, the §13 spot checks.
7. **CLI**
   - `src/all_of_osu_db/cli.py` — wire commands from §7.
8. **Tests**
   - `tests/test_etl_shape.py` — synthetic MySQL fixtures, assert ETL
     produces the expected Postgres rows for a handful of hand-picked cases
     (happy path, null bpm, graveyarded map filtered out, etc.).
9. **Docs**
   - `docs/schema.md` — expand §8 with per-column notes and provenance
     gotchas discovered in step 4.
   - `docs/runbook.md` — expand §10 with real commands and failure modes
     seen in practice.
10. **First monthly rollover**
    - Run the whole flow end-to-end against a fresh dump for a different
      month. Fix anything that breaks. Only after this is green should you
      treat the pipeline as trustworthy.

---

## 17. Resources / read first

Before implementing, skim:

- [`ppy/osu-performance-datasets-generator`](https://github.com/ppy/osu-performance-datasets-generator)
  — authoritative on what the monthly dump contains. README + `dump_all.sh`.
- [`Eve-ning/osu-data`][osudata] — README for CLI flags, ports, refresh
  semantics. Note `-p 3308` default MySQL port, `-v {top_1000,top_10000,
  random_10000}`, and that data persists across runs unless compose project
  is removed.
- [`mattik01/Osu-RecSys-Study`](https://github.com/mattik01/Osu-RecSys-Study)
  — prior work using the same dumps:
  - `documentation/schema-info.md` — useful for column selection.
  - `sql_dump_import_and_modification/sql-processing-queries.txt` —
    reusable SQL patterns (denormalization, aggregation, indexing).
- [osu! API v2 docs](https://osu.ppy.sh/docs/) — for any future API-based
  Layer A source.
- Sibling project [`Osu-Replay-To-YT`][yt] — in particular its `PLAN.md` to
  understand what the v1 consumer expects.

---

## 18. Open questions left for the implementer

Flagged in-line above; pulled together here for convenience:

- §4: confirm `top_10000` slice covers enough popular maps for the YT
  pipeline. If not, consider running `random_10000` alongside or moving up
  to a broader source.
- §8: validate exact ppy column names against a real imported dump; update
  this README in the same PR as any correction.
- §10: choose whether `refresh` replaces or appends Layer A data on each
  run. Default in this README: **replace**, but benchmark import time —
  append may be cheaper if `osu-data` grows incremental support.
- §11: pin the `beatmap_reference` contract version (v1) and decide a
  bump policy before a second consumer arrives.

---

*Not affiliated with or endorsed by ppy Pty Ltd. osu! is a trademark of ppy.*
