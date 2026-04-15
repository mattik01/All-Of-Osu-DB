# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository status

**Scaffolding only.** README.md is the spec; no Python code, SQL, or `pyproject.toml` exists yet. The implementation backlog is in README §16 — work in that order. `src/`, `sql/`, `tests/` are empty placeholders.

## Where the domain knowledge lives

**`docs/knowledge-base/` is populated** with osu! domain facts distilled from two sibling repos — [`mattik01/Osu-RecSys-Study`](https://github.com/mattik01/Osu-RecSys-Study) (ppy dump SQL patterns, derived metrics, dataset characteristics) and [`mattik01/osu--skintool`](https://github.com/mattik01/osu--skintool) (`.osu` file format, hitsound rules, skin registry). Start there before re-researching anything. Top-level sections: `game/`, `beatmap-format/`, `hitsounds/`, `skins/`, `data-dump/`, `derived-metrics/`, `apis-and-community/`, `analysis/`. Index at `docs/README.md`; source citation at `docs/sources.md`.

Particularly load-bearing for ETL work: `docs/knowledge-base/data-dump/sql-patterns.md` (verbatim denormalization queries), `docs/knowledge-base/data-dump/enums-and-gotchas.md` (mod bits, EAV attrib_id pivot map, charset pitfalls).

When implementing, follow the planned layout in README §6 (`src/all_of_osu_db/{config,cli,layerA,etl,validate}.py`).

## Architecture: two-layer database

This is **not** a single ETL pipeline — it is a shared reference DB built from multiple sources.

- **Layer A — raw mirror (MySQL on port 3308):** Each source imported as-is, original names preserved, one schema namespace per source (`ppy_dump.*`, future `osu_api_v2.*`, etc.). Managed by the third-party [`Eve-ning/osu-data`](https://github.com/Eve-ning/osu-data) pip package, which runs its own Docker MySQL — **do not run a competing MySQL on 3308**. Layer A is staging; never queried by downstream consumers.
- **Layer B — curated slice (Postgres 16 on 5432):** Clean schema derived from Layer A by ETL. v1 projection is `beatmap_reference` (one row per difficulty). Schema in README §8 — that table is the consumer contract and any deviation found during real ingest **must update README §8 in the same PR** (see §8 "Provenance disclaimer" and §16 step 4).

Downstream projects (notably [`Osu-Replay-To-YT`](https://github.com/mattik01/Osu-Replay-To-YT)) connect to Layer B via plain `BEATMAP_DB_URL` Postgres URL — they have no awareness of Layer A or `osu-data`.

### Adding a new Layer A source
Follow README §12: new schema namespace, new `src/all_of_osu_db/layerA/<source>.py` with a `refresh()` entrypoint, document in §4 table, decide whether it enriches an existing Layer B projection or introduces a new one (with its own §8-style contract).

### Breaking-change policy
`beatmap_reference` columns may be **added** freely; **renames or drops require a version bump** and a search of consumer repos (README §11).

## Stack & tooling (planned)

- Python 3.11+ via a **conda env** named `all-of-osu-db`, defined in
  `environment.yml` at the repo root. Create with
  `conda env create -f environment.yml`, enter with
  `conda activate all-of-osu-db`. Do **not** use `uv` / `poetry` / raw venv —
  user prefers conda.
- `typer` CLI, `pydantic-settings` for config from `.env`
- `sqlalchemy` + `pymysql` (Layer A), `psycopg` + `psycopg-binary` (Layer B)
- `ruff` (lint/format), `pytest` (tests)
- `osu-data` is pip-only — declared under the `pip:` section of `environment.yml`.
- Layer B DB started via `docker compose up -d postgres` (copy `docker-compose.yml.example` first)

### External prerequisites (user installs; do not assume installed)
The repo does not bundle or auto-install system tooling. Before scaffolding or
running anything, these must already be on the user's machine:
Miniconda/Miniforge, Docker Desktop (or engine + compose), `git`, optionally
`psql` for applying DDL by hand. If unsure whether they're installed, check
with `where.exe <tool>` and surface any missing pieces to the user — do not
try to work around missing prereqs silently.

## Planned CLI (README §7)

```
all-of-osu refresh [--skip-download]    # full cycle: dump → Layer A → ETL → validate
all-of-osu etl                          # ETL only (iterate on Layer B shape)
all-of-osu validate                     # row counts + §13 spot checks
all-of-osu export-parquet
all-of-osu layerA ppy-dump --mode osu --version top_10000 --ymd YYYY_MM_DD
```

`osu-data`'s slice flag is constrained to `top_1000 | top_10000 | random_10000` — there is no "all beatmaps" option. Default is `top_10000` of mode `osu`.

## ETL implementation notes (README §16 step 5)

- Read MySQL with **server-side cursors**; write Postgres with batched **`COPY`**.
- **Upsert on `md5`** (the in-game hash, primary key of `beatmap_reference`).
- Compute `popularity_rank` in Postgres after load: `rank() over (partition by mode order by playcount desc)`.
- `refresh` **replaces** Layer A on each run by default (osu-data otherwise preserves prior data) — automate via removing the compose project in the wrapper.

## Verification (README §13)

Idempotency matters: running `refresh` twice on the same dump must produce byte-identical Layer B row counts and per-column hashes. Monthly rollover tolerance: row counts within ±10% of previous month.

## Legal

Never republish ppy dump bytes (only derived columns in Layer B). Public SQL endpoints / mirrored dumps require permission from contact@ppy.sh — current scope is local-only, revisit README §14 before exposing anything publicly.
