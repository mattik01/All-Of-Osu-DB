# docs/ — domain documentation

Two top-level sections:

- **`knowledge-base/`** — curated osu! domain facts distilled from two sibling repos.
- **`OWC/`** — osu! World Cup tournament reference: mappool structure and slot characterisations. Drives the Liquipedia mappool scraper in `src/all_of_osu_db/layerA/liquipedia.py`.

The `knowledge-base/` content draws from:

- **[`mattik01/Osu-RecSys-Study`](https://github.com/mattik01/Osu-RecSys-Study)** — prior recommender-system work on ppy's monthly MySQL dumps; source of SQL patterns, derived metrics, dataset characteristics.
- **[`mattik01/osu--skintool`](https://github.com/mattik01/osu--skintool)** — skin browsing / hitsound-extraction tool; source of `.osu` file-format details, hitsound rules, skin element registry, rendering math.

See [`sources.md`](./sources.md) for exactly which files each section came from.

## Layout

```
knowledge-base/
├─ game/                    osu! gameplay domain facts
│   ├─ modes-and-status.md        — game modes, ranking status
│   ├─ mods.md                    — full mod bitmask table + ML-practical subset
│   ├─ scoring-and-pp.md          — accuracy, PP, weighted PP, letter ranks
│   └─ difficulty-attributes.md   — SR, AR, CS, OD, HP, aim/speed/strain
│
├─ beatmap-format/          .osu file reference
│   ├─ file-structure.md
│   ├─ timing-points.md
│   ├─ hit-objects-and-sliders.md
│   └─ hitsounds-in-beatmap.md
│
├─ hitsounds/               the hitsound playback model
│   ├─ sample-sets-and-files.md
│   └─ arrangement-json.md        — skintool's per-beatmap hitsound export format
│
├─ skins/                   skin assets & rendering
│   ├─ element-registry.md        — full enumeration of skin element filenames
│   ├─ skin-ini.md                — every key, every default
│   └─ rendering-and-install.md   — preview math + OS install-path detection
│
├─ data-dump/               ppy monthly MySQL dump reference
│   ├─ overview-and-tables.md     — what's in it, every osu_* table we touched
│   ├─ enums-and-gotchas.md       — attrib_id pivot, mod bits, charset pitfalls
│   ├─ sql-patterns.md            — verbatim denormalization queries
│   └─ import-workflow.md         — osu-data CLI, db-import.bat, DuckDB path
│
├─ derived-metrics/         non-trivial features built on top of the dump
│   ├─ user-skill.md              — total_weighted_pp, skill_stabilization_date
│   ├─ beatmap-metrics.md         — popularity rank, farm factor, technicality
│   └─ enjoyment-score.md         — full formula + rationale
│
├─ apis-and-community/      where else osu! data lives
│   ├─ api-and-dumps.md           — osu! API v2, data.ppy.sh, mirrors
│   └─ recommenders-and-tools.md  — Tillerino, AlphaOsu, osu!Collector, osu_oracle, …
│
└─ analysis/
    └─ dataset-and-biases.md      — dump volumes, long tail, farm/popularity bias

OWC/
└─ Mappool/                  osu! World Cup mappool reference
    ├─ pool-structure.md          — pool sizes per stage, era history, match flow
    └─ slot-guide.md              — per-slot skill descriptions + glossary
```

## How this relates to the repo

This knowledge base exists so that ETL, schema, and analysis decisions for `All-Of-Osu-DB` can be made without re-discovering what was already learned in the two source repos. When implementing Layer A ingest (README §16 step 4) or Layer B ETL (step 5), start here.

**Scope discipline:** content in this folder reflects what the two source repos contain. Where a note is the author's opinion/speculation from those repos rather than an objective fact, it is flagged. Official-but-not-in-the-source-repos information (e.g., exact osu! API v2 endpoints, AR→preempt formula) is explicitly called out as *not covered here — go to the osu! wiki*.
