# OWC mappool — pool structure

Format reference for the **osu! World Cup** (OWC), the annual country-based 4v4 osu!standard team tournament organised by the osu! community. This file covers what an OWC mappool *is* — pool sizes per round, mod-bracket composition, match flow, and how the format has evolved across editions. Per-slot skill descriptions live in [`slot-guide.md`](./slot-guide.md).

This doc and its sibling exist primarily to support the Liquipedia mappool scraper (`src/all_of_osu_db/layerA/liquipedia.py`) — the scraper extracts these slots and the docs explain what the slots mean.

## What an OWC mappool is

Each OWC match is played from a fixed **mappool** — a list of beatmaps the captains pick from in turn, with bans. The pool is partitioned into **mod brackets** (No Mod, Hidden, Hard Rock, Double Time, Free Mod, Tiebreaker); within each bracket, slot ordinals (`NM1`, `NM2`, …, `HD1`, …) are conventionally assigned by the pool selectors to test specific skillsets — see [`slot-guide.md`](./slot-guide.md).

Mod definitions and bitmasks: see [`../../knowledge-base/game/mods.md`](../../knowledge-base/game/mods.md). The OWC pool uses only the standard mods of those — `NF` (No Fail) and `SD` (Sudden Death) are not bracketed; the `Score V2` ruleset is the scoring system but is not a mod bracket.

## Mod brackets

| Code | Bracket | Forced mod | Player mod choice |
| --- | --- | --- | --- |
| `NM` | No Mod | none (NF allowed) | none |
| `HD` | Hidden | HD on all picked players | none |
| `HR` | Hard Rock | HR on all picked players | none |
| `DT` | Double Time | DT (NC equivalent) on all picked players | none |
| `FM` | Free Mod | each team must field at least 1 HD player and 1 HR (or HDHR) player | other 2 players choose freely from {NM, HD, HR, HDHR} |
| `TB` | Tiebreaker | none | each player chooses freely from {NM, HD, HR, DT, EZ, FL, …} |

Each pick is played by **4 of the 8 players** on each team (the captain chooses which four), with `Score V2` scoring summed across the 4 players.

## Standard pool composition (2022–2024)

Two pool sizes are used depending on stage. The **2022 rebalance** (Azer / pool selectors) moved the speed-focused slot out of No Mod and into Free Mod — `NM5 → FM2` — to encourage less skill-isolated slots. NM shrinks by one, FM grows by one; cascading renames apply (former `NM6 → NM5`, former `FM2 → FM3`, former `FM3 → FM4`). This is the format used in OWC 2022, 2023, and 2024.

| Stage | Total | NM | HD | HR | DT | FM | TB |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Round of 32, Round of 16 | 15 | 4 | 2 | 2 | 3 | 3 | 1 |
| Quarterfinals, Semifinals, Finals, Grand Finals | 20 | 5 | 3 | 3 | 4 | 4 | 1 |

**Slot labels expected** (post-2022):
- NM: `NM1`–`NM4` (RO32/RO16) / `NM1`–`NM5` (QF+)
- HD: `HD1`–`HD2` / `HD1`–`HD3`
- HR: `HR1`–`HR2` / `HR1`–`HR3`
- DT: `DT1`–`DT3` / `DT1`–`DT4`
- FM: `FM1`–`FM3` / `FM1`–`FM4`
- TB: `TB`

## Pre-2022 composition (2019–2021)

The reddit-guide reference format. Same mod brackets, NM is one larger and FM one smaller. `NM5` was specifically the "speed" slot.

| Stage | Total | NM | HD | HR | DT | FM | TB |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Round of 32, Round of 16 | 15 | 5 | 2 | 2 | 3 | 2 | 1 |
| Quarterfinals → Grand Finals | 20 | 6 | 3 | 3 | 4 | 3 | 1 |

## Match flow

- **Bo-X** scaling per stage: typically Bo7 in early rounds, growing to Bo11 / Bo13 in Finals and Grand Finals.
- **Roll** for first ban / pick (osu!'s `!roll` command).
- **Bans**: each captain bans 1–2 maps (varies by edition).
- **Picks alternate** until one team reaches the score threshold (e.g., 6 wins in a Bo11). At that point the **Tiebreaker** is forced.
- The Tiebreaker is `TB`-slot only; mods are free per player. The Tiebreaker map is published *with* the pool, so it is not a surprise — it is the deciding pick if the score is even at the penultimate point.
- **Player rotation**: the captain selects which 4 of 8 players play each map. Free Mod requires at least one HD and one HR (or HDHR) on each team for that pick.

## Era history of pool philosophy

OWC's pool format has shifted substantially across 14+ editions. Slot conventions described in [`slot-guide.md`](./slot-guide.md) crystallised gradually; older editions do **not** follow them and the scraper's parser must tolerate that.

### OWC #1 to #3 (2011–2012): pre-bracket era

Editions used ordinal names (`Osu_World_Cup/1`, `/2`, `/3`) before the year-based slug took over in 2013. **All maps in the pool were No Mod.** Slots were just `NM1`, `NM2`, …, with the only modded pick being the Tiebreaker (where players could choose mods individually).

OWC #1 pool sizes by stage:

| Stage | Maps |
| --- | --- |
| Round of 32, Round of 16, Quarterfinals | 15 NM + 1 TB |
| Semifinals, Third Place Playoff | 6 NM + 1 TB |
| Finals | 8 NM + 1 TB |

There was no `HD`/`HR`/`DT`/`FM` bracket. The reddit-guide framing of "what NM3 means" does not apply to this era.

### 2013–2014: introduction of mod brackets

Year-based slugs begin. The `HD`/`HR`/`DT`/`FM` brackets enter the format, but slot identities (e.g., "NM1 = aim consistency") are not yet codified. Pool selectors compose the pool by general difficulty band rather than by skill slot.

### 2015–2018: emergence of slot conventions

Slot-by-slot skill conventions begin to firm up. `NM1` as a "comfy aim consistency" opener, `NM2` as "streams", `HR2` as "precision", and so on become *expectations* rather than *announcements*. Pool sizes converge on 15-and-20-by-stage. Liquipedia coverage is uneven for this era — some pages are populated only with match-result templates and not the pool itself.

### 2019–2021: peak specialisation

The "reddit-guide era". Slot identities are at their most explicit and most isolated. NM5 is unambiguously the speed slot; HD2 is the low-AR reading slot; FM2 is the antimod slot. Pool sizes are 15 (RO32/RO16) and 20 (QF–GF). Tiebreakers shift toward **commissioned originals** at the top end:

- OWC 2020 Grand Finals tiebreaker: **Camellia — OOPARTS [Zenith]** (commissioned).
- OWC 2021 Grand Finals tiebreaker: **Yooh — RPG [Divinity]** (commissioned).

### 2022: deliberate rebalance

OWC 2022 announces (via Azer / pool selectors) a move toward **less skill-isolated slots** — pool selectors are no longer constrained to one-skill-per-slot, and may mix skillsets within a single map. The most concrete structural change is:

- **`NM5` (speed) is moved to `FM2`** in Free Mod; cascading renames (`NM6 → NM5`, `FM2 → FM3`, `FM3 → FM4`).
- Stated rationale (paraphrased from OWC 2022 announcement): "The maps will still dominantly feature their intended skillsets, but there is no longer a restriction on what else they may have."

Tiebreakers in 2022 were a mix of community-mapped picks per round, without a single commissioned headline song.

### 2023–2024: post-rebalance steady state

The 2022 format carries forward. Pool composition tables above (15/20 with 4/2/2/3/3/1 and 5/3/3/4/4/1) describe both years. **Qualifier** stages use 4 brackets (NM/HD/HR/DT) with no FM or TB. OWC 2024 returns to commissioned tiebreakers at the top end:

- OWC 2024 Finals and Grand Finals tiebreaker: **Camellia — Operation: Zenithfall** (commissioned; reused across both rounds).

### 2025: structural change

OWC 2025 introduced a **Group Stage** preceding the bracket — a 16-map pool (5/2/2/3/3/1) with NM bumped back up to 5 — and switched the bracket to **double elimination**. Tiebreakers in 2025 used community-mapped picks rather than commissioned originals.

## Tiebreaker tradition

The Grand Finals tiebreaker has, in some editions, been a **commissioned original** — a song written specifically for OWC and mapped to fit. This is not a hard rule across all editions and not all years have a commissioned headline:

| Edition | GF tiebreaker artist / song | Commissioned? |
| --- | --- | --- |
| OWC 2020 | Camellia — OOPARTS [Zenith] | yes |
| OWC 2021 | Yooh — RPG [Divinity] | yes |
| OWC 2022 | community map (varies) | no |
| OWC 2024 | Camellia — Operation: Zenithfall | yes |
| OWC 2025 | community map | no |

When commissioned, the song is typically released publicly on the artist's Bandcamp / YouTube around the start of the Grand Finals weekend.

## Qualifier stages

In addition to the bracket-stage pools, recent editions (2018+) include a **Qualifier**: every team plays the same Qualifier mappool to seed into the bracket. Qualifier pools are smaller than bracket pools (typically 8–10 maps), use 4 brackets (NM/HD/HR/DT), and have no FM or TB slot. The Liquipedia subpage for the Qualifier is `<edition>/Qualifier` (e.g., `Osu_World_Cup/2024/Qualifier`); older editions either embed the Qualifier in the main edition page or omit it entirely.

## Liquipedia page structure

The scraper's discovery flow walks the per-edition pages on Liquipedia:

| Slug pattern | Editions |
| --- | --- |
| `Osu_World_Cup/1`, `/2`, `/3` | OWC #1 (2011), #2 (2012), #3 (late 2012) |
| `Osu_World_Cup/<year>` | from 2013 onward |
| `Osu_World_Cup/<edition>/Qualifier` | optional subpage; scraper probes and tolerates 404 |

Each per-edition page typically contains an `==Mappool==` section. Within it, modern editions (2020+) use a **plain wiki bullet** format:

```
* '''NM1''' : [https://osu.ppy.sh/beatmapsets/<sid>#osu/<bid> <nowiki>Artist - Title (Mapper) [Difficulty]</nowiki>]
```

Older editions (pre-2020) use varied formats including bare bullets and inconsistent slot labelling. Some Liquipedia pages — notably 2014–2017 — are populated only with the post-match `{{Map|map=…|score1=…}}` *result* templates and have no mappool definition; the scraper logs these as warning rows rather than crashing.

## Sources

Citations resolve in [`../../sources.md`](../../sources.md). Primary references for this file:

- Reddit, /r/osugame, "OWC Mappool Viewer's Guide" (Cytusine + OP, 2022) — pool sizes and the `NM5 → FM2` rebalance announcement.
- Liquipedia: `Osu_World_Cup/1`, `/2020`, `/2022`, `/2023`, `/2024`, `/2025` — pool sizes per edition, slot labelling, and tiebreaker songs.
- osu! wiki: `wiki/en/Tournaments/OWC/<edition>` — per-edition official format documentation.
- Bandcamp / YouTube — confirmation of commissioned-tiebreaker releases (Yooh "RPG", Camellia "Operation: Zenithfall").
