# Sources

Every fact in `knowledge-base/` traces back to one of two sibling repos (unless explicitly marked as canonical osu! knowledge outside them). Facts in `OWC/Mappool/` trace to a third group of public web sources, listed at the bottom.

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

## Liquipedia + Reddit + osu! wiki (for `OWC/Mappool/`)

Public web sources used to compose `docs/OWC/Mappool/pool-structure.md` and `docs/OWC/Mappool/slot-guide.md`. These are also the page families the Liquipedia scraper (`src/all_of_osu_db/layerA/liquipedia.py`) targets.

| Source | What it gave us |
| --- | --- |
| [Reddit /r/osugame, "OWC Mappool Viewer's Guide" (Cytusine + OP, 2022)](https://www.reddit.com/r/osugame/) | Spine of the slot characterisations and example maps; statement of the 2022 `NM5 → FM2` rebalance and Azer's "less skill-isolated slots" framing. |
| [Liquipedia `Osu_World_Cup` root + per-edition pages](https://liquipedia.net/osu/Osu_World_Cup) | Per-edition pool sizes, slot labels, tiebreaker songs, edition-page slug pattern (`/1`, `/2`, `/3`, `/<year>`). Verified format-stability of the `* '''SLOT''' : [URL ...]` plain-bullet wikitext from 2020 onward. |
| [Liquipedia MediaWiki API (`/osu/api.php`)](https://liquipedia.net/osu/api.php) | Wikitext source for all per-edition pages; structured page-revision IDs for deterministic re-scraping. |
| [osu! wiki `Tournaments/OWC/<edition>` pages](https://osu.ppy.sh/wiki/en/Tournaments/OWC) | Authoritative per-edition format announcements and rule changes; cross-reference for Liquipedia data. |
| [osu! World Cup 2022 announcement / forum thread](https://osu.ppy.sh/community/forums) | Source for the explicit "less isolated skillsets" rebalance statement quoted in the reddit guide. |
| Bandcamp / YouTube — Yooh "RPG", Camellia "OOPARTS", Camellia "Operation: Zenithfall" | Confirmation that specific OWC tiebreaker songs were commissioned originals released around tournament time. |

The reddit guide reflects the 2022 OWC framing; pool composition / slot identity for editions 2011–2014 (pre-bracket era) and 2025 (group-stage rebalance) was reconstructed from Liquipedia per-edition pages and the corresponding osu! wiki entries.

## Not in this knowledge base (on purpose)

- Exact osu! API v2 endpoints, auth flow, rate-limit numbers → not authoritatively present in either source repo. Go to <https://osu.ppy.sh/docs/>.
- Canonical AR → preempt-time formula, CS → diameter formula, OD → hit-window formula → skintool hard-codes preview values rather than the real formulas. Go to the osu! wiki.
- Lazer-specific scoring changes, catch/mania/taiko-specific mechanics beyond what's touched by the two repos.
