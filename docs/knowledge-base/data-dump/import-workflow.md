# Import workflow

Two proven paths for getting a ppy dump into a queryable local database.

## Path A — `Eve-ning/osu-data` (what `All-Of-Osu-DB` uses)

The [`osu-data`](https://github.com/Eve-ning/osu-data) pip package wraps download + import into a local Docker MySQL on **port 3308**. This is what `All-Of-Osu-DB`'s Layer A is built on.

Key facts (from osu-data's README, captured here so future agents don't have to re-research):

- Default MySQL port: **3308** (not 3306 — intentional, so it doesn't collide with a user's existing MySQL).
- Default root user, no password.
- Runs its own docker-compose project; persists data in its volume across runs.
- **Does NOT overwrite on refresh by default** — to replace last month's dump with this month's, you must remove its compose project first.
- Tunes MySQL for import speed, not production (`innodb_doublewrite=0` etc.) — fine for a staging DB you rebuild monthly; never run prod on this.
- CLI flags:
  - `-m/--mode` — one of `osu / taiko / fruits / mania`.
  - `-v/--version` — one of `top_1000 / top_10000 / random_10000`. **There is no "all maps" option.** `top_10000` is the default pick for popularity-weighted work.
  - `-y/--ymd` — dump date in `YYYY_MM_DD` format (matches ppy's folder naming). Leave blank for latest.

`All-Of-Osu-DB` wraps this in `src/all_of_osu_db/layerA/ppy_dump.py` (planned — see main README §16 step 4).

## Path B — direct MySQL import (Osu-RecSys-Study's legacy path)

RecSys-Study used a bespoke `db-import.bat` batch script that:

1. Locates a dump folder like `2025_05_01_performance_osu_top_10000/`.
2. Uses the folder name as the MySQL schema name.
3. Pipes each `.sql` file in the folder through `pv | mysql` for progress visibility:

   ```bat
   pv "<dump_folder>\<file>.sql" | mysql -u root <schema_name>
   ```

4. Repeats for every `.sql` file (one per table or per table chunk).

Useful because:
- No Docker overhead.
- `pv` shows live MB/s progress — important when importing multi-GB files.
- Folder-name-as-schema lets multiple dump versions coexist in one MySQL instance.

The downside is manual download + no refresh automation. Use Path A unless you have a specific reason.

## Path C — DuckDB (RecSys-Study's experimental alternative)

Not recommended for `All-Of-Osu-DB` but captured for reference. RecSys-Study's `import-sql-processor.py` rewrites MySQL dump syntax into DuckDB-compatible syntax before loading, handling:

- Backticks → stripped.
- `AUTO_INCREMENT` / `UNSIGNED` → stripped.
- `ENGINE=`, `DEFAULT CHARSET=`, `COLLATE`, `CHARACTER SET` → stripped.
- Encoding detection with `chardet` (fallback to `latin1`) for rows containing non-UTF-8 usernames/titles.

DuckDB is attractive for analytical workloads but not a drop-in MySQL replacement; MySQL charset / enum edge cases cost more than the analytical speed gain.

## Cross-cutting import gotchas

### Encoding

Dumps contain non-UTF-8 bytes (Japanese usernames, song titles in legacy charsets). Two options:

1. Let MySQL handle it — it's tolerant if the dump declares charset correctly.
2. Pre-process with `chardet` + `latin1` fallback (RecSys-Study's approach for DuckDB path).

### Mixed-case columns

`countTotal`, `countNormal`, `countSlider`, `countSpinner` need quoting on Postgres. RecSys-Study alias-renames to snake_case in the `CREATE TABLE AS SELECT` (see [`sql-patterns.md`](./sql-patterns.md) §C.2).

### Mandatory indexes

After import, **before** running any derived query:

```sql
ALTER TABLE osu_user_beatmap_playcount
ADD INDEX idx_user_beatmap (user_id, beatmap_id);
```

Add this for any large join table. `osu-data` creates the dump's original indexes but not ones specific to downstream queries.

### Import timing

For `top_10000 osu` on a local disk + osu-data tuning: ~15–30 minutes end-to-end (download + import), dominated by download. `random_10000` is similar. `top_1000` is much smaller, mostly useful for quick smoke tests.

## Monthly refresh cadence

ppy publishes new dumps a few days into each month, sometimes delayed. `All-Of-Osu-DB`'s runbook (main README §10) codifies the flow:

1. Check data.ppy.sh for a new dump for the target month.
2. `osu-data` downloads + imports (replacing prior by removing compose project).
3. ETL into Layer B Postgres.
4. Run validation checks (`knowledge-base/analysis/dataset-and-biases.md` has the sanity metrics to compare month-over-month).

### Expected drift

Monthly deltas in row counts: **±10%** is normal. Anything larger → investigate (could be a dump-generation bug upstream, a new slice policy, or an on-disk corruption).
