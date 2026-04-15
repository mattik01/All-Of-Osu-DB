# Sources

Every fact in `knowledge-base/` traces back to one of these two repos (unless explicitly marked as canonical osu! knowledge outside them).

## `mattik01/Osu-RecSys-Study`

Files mined for this knowledge base:

| Path | What it gave us |
| --- | --- |
| `README.md` / `documentation/schema-info.md` (identical) | mod bitmask table, score/accuracy columns, engineered enjoyment formula, research framing |
| `documentation/Inital Ideas.md` | prior-art recommender landscape (Tillerino, AlphaOsu, etc.), community resources |
| `Points.txt` | dataset volume table, processing-step list, author self-grading |
| `sql_dump_import_and_modification/sql-processing-queries.txt` | verbatim SQL for `USERS`, `scores_high`, `beatmaps` denormalization |
| `sql_dump_import_and_modification/db-import.bat` | MySQL dump import pattern, folder naming convention |
| `data scraping (inactive)/import-sql-processor.py` | MySQL → DuckDB syntax cleanup regexes, encoding fallback |
| `data/database_export.py` | streaming non-buffered cursor pattern for MySQL → CSV |
| `data/processed/print_farm.py` | canonical farm-map sanity-check list |
| `RecSys/recommend.py` | initial SVD pilot, observed popularity collapse |
| `RecSys/pipeline/data_split.py` | pre-stabilization filter, rating-scale normalization |
| `RecSys/pipeline/evaluator.py` | sensitive-attribute 99th-percentile ceiling filter |
| `RecSys/pipeline/model_trainer.py` | Surprise library model recipes, min-interactions filter |
| `RecSys/pipeline/summary_pretty_table.txt` | observed evaluation numbers |
| `RecSys/second_dataset/*` | Instacart constraint experiments (diversity caps, recent-item suppression) |
| `DataAnalysis/analysis.ipynb` | total_weighted_pp recipe, technicality prototype, per-bin correlations, skill-ceiling tracking |

## `mattik01/osu--skintool`

| Path | What it gave us |
| --- | --- |
| `beatmap-hitsound-extractor/process_all_beatmaps.py` | `.osu` parser reference: sections, timing-point fields, hit-object bitfields, slider params, hitsound resolution |
| `beatmap-hitsound-extractor/generate_hitsounds.py`, `regenerate_single.py` | sample-set / addition mapping, filename conventions |
| `beatmap-hitsound-extractor/samples/*/arrangement.json` | concrete example of the per-beatmap hitsound export schema |
| `src/main/java/com/osuskin/tool/model/SkinElementRegistry.java` | full enumeration of every skin element filename, by category |
| `src/main/java/com/osuskin/tool/model/Skin.java`, `LazyLoadingSkinService.java` | `skin.ini` keys parsed, defaults used |
| `src/main/java/com/osuskin/tool/view/gameplay/*` | preview-level rendering math: approach-circle scaling, fades, slider-track width, cursor expand |
| `src/main/java/com/osuskin/tool/util/OsuPathDetector.java` | per-OS default install paths, "is this a skin folder?" heuristic |
| `src/main/resources/default-skin/skin.ini`, `!README.txt` | bundled default skin values |
| `docs/OSU_SKIN_RENDERING.md`, `docs/ARCHITECTURE.md` | playfield size, curve type names, nightcore-mod audio rules |
| `CLAUDE.md`, root `README.md` | project-level context |

## Not in this knowledge base (on purpose)

- Exact osu! API v2 endpoints, auth flow, rate-limit numbers → not authoritatively present in either source repo. Go to <https://osu.ppy.sh/docs/>.
- Canonical AR → preempt-time formula, CS → diameter formula, OD → hit-window formula → skintool hard-codes preview values rather than the real formulas. Go to the osu! wiki.
- Lazer-specific scoring changes, catch/mania/taiko-specific mechanics beyond what's touched by the two repos.
