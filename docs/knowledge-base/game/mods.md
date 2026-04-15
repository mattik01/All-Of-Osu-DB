# Mods (bitmask reference)

Scores in the ppy dump carry `enabled_mods` as a **packed bitmask** (`osu_scores_high.enabled_mods`, also `osu_beatmap_difficulty.mods`). Each mod is a single bit; active mods OR together.

## Full bitmask table

| Bit | Code | Name | Gameplay effect |
| --- | --- | --- | --- |
| `1` | NF | No Fail | HP can't drop below 1. |
| `2` | EZ | Easy | Halves overall difficulty — larger circles, lower AR/HP drain. |
| `4` | TD | Touch Device | Mobile/touchscreen — no miss penalty, auto-spinners. |
| `8` | HD | Hidden | Notes fade after appearing; reading test. |
| `16` | HR | Hard Rock | Smaller circles, faster SR, higher HP drain, flipped playfield vertically. |
| `32` | SD | Sudden Death | One miss / 50 / 100 ends the play. |
| `64` | DT | Double Time | +50% speed, ~×1.12 AR & CS. |
| `128` | RX | Relax | Auto-clicks; you only move the cursor. |
| `256` | HT | Half Time | −25% speed, ~×0.88 AR/CS. |
| `512` | NC | Nightcore | DT + pitch-shifted audio. **Always co-occurs with the DT bit.** |
| `1024` | FL | Flashlight | Visibility limited to a small spotlight. |
| `2048` | AU | Auto | Game plays itself (100% / FC). |
| `4096` | SO | Spun Out | Auto-spinner. |
| `8192` | AP | Auto Pilot | Auto cursor; manual click. |
| `16384` | PF | Perfect | Stricter SD — every note must be a 300. |
| `32768` | K4 | Key4 | mania-only. |
| `65536` | K5 | Key5 | mania-only. |
| `131072` | K6 | Key6 | mania-only. |
| `262144` | K7 | Key7 | mania-only. |
| `524288` | K8 | Key8 | mania-only. |
| `1048576` | FI | Fade In | mania-style: invisible until AR distance. |
| `2097152` | RN | Random | mania-only — shuffles columns. |

Source: verbatim from Osu-RecSys-Study's `documentation/schema-info.md` / `README.md`.

## Practical mod subset used by RecSys-Study

The raw mod space has 2²² combinations. The project collapsed it to **four categories only**:

```
NM (0)  HR (16)  DT (64)  DTHR (80 = 16 | 64)
```

Any score whose `enabled_mods` contained a mod outside this set was dropped. Rationale:

- **NF/SD/PF/AU/RX/AP/SO** don't change difficulty in a meaningful, measurable way; they're either auto-play variants or meta flags.
- **EZ / HT / FL** change difficulty but are rare in the top-play distribution.
- **HD** *does* matter (visibility challenge) but has a small, roughly constant pp multiplier; RecSys-Study collapsed duplicates by keeping the **max-pp** score, accepting minor information loss.
- **NC** always co-occurs with DT; treat NC scores as DT for aggregation.
- **Key mods / FI / RN** are mania-only.

This collapse produces a tractable `(beatmap_id, mods_string) → mod_beatmap_id` item space (see `knowledge-base/derived-metrics/user-skill.md`).

SQL filter literal used in the denormalization query:
```sql
WHERE d.mode = 0
  AND d.mods IN (0, 16, 64, 80)
```

## Per-mod-combination difficulty attributes

`osu_beatmap_difficulty` is keyed `(beatmap_id, mode, mods)`. A given beatmap has a **different star rating per mod combination** — HR/DT each re-compute SR from the hit-object layout under the modded parameters. The companion EAV table `osu_beatmap_difficulty_attribs` has separate `aim`, `speed`, `strain`, etc. per `(beatmap_id, mode, mods)` tuple. See `knowledge-base/data-dump/enums-and-gotchas.md` for the attrib pivot.

## Gotchas

- `enabled_mods` from `osu_scores_high` is a raw **integer bitmask**; the "mods string" (`NM`/`DT`/…) is a derived column you compute in Python/SQL after bitwise-decoding.
- `osu_beatmap_difficulty.mods` is not bitmask-packed in the same way the scores table is — it's one row per discrete mod combination actually computed; values for stable mods are 0, 16, 64, 80 in the project's slice.
- **`LayeredHitSounds`** (skin.ini flag) is unrelated to gameplay mods despite the shared "mod-like" appearance.
