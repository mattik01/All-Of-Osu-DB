# `.osu` file structure

A `.osu` beatmap file is **plain text, UTF-8**, section-oriented. Sections start with a bracketed header on its own line; content between headers is either key-value pairs (INI-like) or comma-separated rows. The skintool parser treats any unrecognised bracketed header as "stop section-specific parsing."

Skintool opens files with `encoding='utf-8', errors='ignore'` (tolerates malformed bytes; some old maps have non-UTF-8 bytes).

## Section order (conventional)

```
osu file format v14                    ← format version header
[General]
[Editor]
[Metadata]
[Difficulty]
[Events]
[TimingPoints]
[Colours]
[HitObjects]
```

The skintool parser only reads `[General]`, `[Difficulty]`, `[TimingPoints]`, `[HitObjects]`. Everything else it skips.

## `[General]` keys used

| Key | Meaning | Default used by parser |
| --- | --- | --- |
| `AudioFilename:` | Filename of the audio track (relative to .osu) | — |
| `SampleSet:` | Default hitsound sample set (`Normal`/`Soft`/`Drum`, case-insensitive) | `"normal"` if missing |

Other `[General]` keys that exist in the spec but the skintool ignores: `AudioLeadIn`, `PreviewTime`, `Countdown`, `StackLeniency`, `Mode`, `LetterboxInBreaks`, `WidescreenStoryboard`, `EpilepsyWarning`, `SamplesMatchPlaybackRate`.

## `[Metadata]` keys

Not parsed by the skintool's extractor, but the shape is:

```
Title:<romanised title>
TitleUnicode:<native title>
Artist:<romanised artist>
ArtistUnicode:<native artist>
Creator:<mapper username>
Version:<difficulty name>
Source:<album/game/show>
Tags:<space-separated tags>
BeatmapID:<id>
BeatmapSetID:<set id>
```

The dump's `osu_beatmapsets` table is the canonical source for these values — no reason to parse them from `.osu` when the dump is available. Use the dump; use `.osu` only for timing/hitobject data.

## `[Difficulty]` keys used

| Key | Meaning | Default used by parser |
| --- | --- | --- |
| `SliderMultiplier:` | Base slider-velocity scalar (px / beat). Combines with SV multipliers from inherited timing points. | `1.4` |
| `SliderTickRate:` | Ticks per beat at base SV. | `1.0` |

Other `[Difficulty]` keys: `HPDrainRate` (HP/drain), `CircleSize` (CS), `OverallDifficulty` (OD), `ApproachRate` (AR). These are in the dump as `diff_drain/size/overall/approach` — no need to parse.

## `[TimingPoints]`

Comma-separated rows with **8 fields**. See [`timing-points.md`](./timing-points.md).

## `[HitObjects]`

Comma-separated rows with **at least 5 fields**. See [`hit-objects-and-sliders.md`](./hit-objects-and-sliders.md).

## `[Events]`

Background image, video, breaks, storyboard. Not touched by either source repo.

## `[Colours]`

Combo colours override. Fields: `Combo1 : 255,128,0` through `Combo8`, plus `SliderBorder`, `SliderTrackOverride`, `SliderBall`, etc. See `knowledge-base/skins/skin-ini.md` for the skin-level counterparts (beatmap `[Colours]` overrides skin `[Colours]` for that specific beatmap if the skin has `AllowSliderTint` style behavior — nuanced).

Skintool's `Skin.java` reads `[Colours]` from `skin.ini`, not from `.osu` files.

## Comment syntax

Lines starting with `//` are comments (skintool's ini parser recognises them; whether mainline osu! `.osu` parser does is conventionally yes, but the skintool's `.osu` parser just processes line-by-line and would ignore unmatched lines in active sections).

## What NOT to trust from `.osu` files vs the dump

- Playcount / passcount / favourites — **not in `.osu` at all**. These live on the dump.
- Star rating — **not in `.osu`**. Computed externally; in the dump as `difficultyrating` / `diff_unified`.
- MD5 — **not in `.osu`** (it IS the hash of the `.osu` file content). In the dump as `osu_beatmaps.checksum`. Computing it from the file is straightforward if needed.
