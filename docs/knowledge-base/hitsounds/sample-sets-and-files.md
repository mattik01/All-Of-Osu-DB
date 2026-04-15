# Sample sets & hitsound file conventions

## The three sample sets

osu! has **three** built-in sample set families:

| Name | File prefix |
| --- | --- |
| Normal | `normal-` |
| Soft | `soft-` |
| Drum | `drum-` |

In the `.osu` per-object encoding, these map to integers `1`, `2`, `3`. `0` means "inherit from the timing point" (which itself resolves eventually to one of the three).

## Sound types per sample set

Every sample set provides this full suite of filenames (skintool's `ElementGroup.HITSOUNDS`):

| Filename | Played when |
| --- | --- |
| `<set>-hitnormal` | Always, on any hit object (circle / slider head / slider edges). |
| `<set>-hitwhistle` | Bit `2` in hitsound bitfield. Additions (use addition set). |
| `<set>-hitfinish` | Bit `4`. Additions. |
| `<set>-hitclap` | Bit `8`. Additions. |
| `<set>-slidertick` | Per tick on sliders, at tick's active timing point's sample set. |
| `<set>-sliderslide` | Continuous, looped, for slider body duration. |
| `<set>-sliderwhistle` | If slider's own hitSound has whistle; continuous looped, overlaid with sliderslide. |

### Taiko variants

Skintool additionally enumerates `taiko-normal-hitnormal`, `taiko-normal-hitwhistle`, `taiko-normal-hitfinish`, `taiko-normal-hitclap` and their `taiko-soft-*` / `taiko-drum-*` counterparts. These are only used when the beatmap is taiko-mode; the skin applies the `taiko-`-prefixed variant if present, falling back to the mode-agnostic name if not.

## Custom sample indexes

`.osu` hit objects and timing points can reference a **custom index N ≥ 1**. The expected filename is `<set>-<sound><N>.<ext>` — e.g. `normal-hitnormal3.wav`, `soft-hitclap7.ogg`.

- `N = 0` means "no custom" → use the base filename `<set>-<sound>.<ext>`.
- Mappers use this to attach map-specific sound variants while still respecting sample-set semantics.

## File extensions & search order

Skintool's `HitsoundRenderer.load_skin_hitsounds` tries extensions in this order:

```
.wav → .ogg → .mp3 → .flac
```

osu! traditionally prefers `.wav`/`.ogg`; `.mp3` works but has encoding latency. Beatmap-local hitsounds override skin hitsounds.

## Fallback chain (miss resolution)

If the exact `<set>-<sound>{N?}.<ext>` isn't found, skintool's `get_sound_file` tries:

```
<set>-<sound>
→ normal-<sound>
→ soft-<sound>
→ drum-<sound>
→ <sound>        (bare, no set prefix — rare)
```

The bare-`<sound>` fallback exists for custom/malformed skins that drop the sample-set prefix.

## Layered hitsounds

Controlled by `skin.ini [General] LayeredHitSounds`:

- `1` (default) — additions layer on top of hitnormal; multiple sounds play simultaneously on a circle with `hitSound & (2|4|8)`.
- `0` — only one sound plays (the "highest priority" addition). Rare.

Skintool's extractor defaults to `layered_hitsounds = True`.

## Spinner-specific sounds

Not strictly sample-set files — they live at the top level:

| File | Role |
| --- | --- |
| `spinnerspin.<ext>` | Continuous, looped during spinner. Pitch modulates with spin speed unless `SpinnerFrequencyModulate=0`. |
| `spinnerbonus.<ext>` | Per-1000-bonus-score chime. |
| `spinnerbonus-max.<ext>` | lazer-specific "max bonus reached" one-shot. |
| `spinnerfall.<ext>` | Failed-spinner sound (didn't reach threshold). |

## Game-state / UI sounds (for completeness)

Defined in skintool's `SkinElementRegistry` but not beatmap-driven: `combobreak`, `failsound`, `applause`, `sectionpass`, `sectionfail`, `pause-loop`, `menuhit`, `menuclick`, `heartbeat`, `welcome`, `seeya`, etc.

## Nightcore mod auto-mixed hitsounds

Per skintool's `OSU_SKIN_RENDERING.md`, the Nightcore mod layers additional samples regardless of beatmap:
- `nightcore-kick` — beats 1 & 3 of every measure.
- `nightcore-clap` — beats 2 & 4 of every measure.
- `nightcore-hat` — every odd quaver when tick rate is a multiple of 2.
- `nightcore-finish` — first beat of every 4 measures, unless the measure has `omit-barline` flag set.

These are skin files, not beatmap files. Drawing them into a hitsound export requires knowing tempo + meter + bar indices from timing points.
