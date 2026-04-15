# Hitsound resolution per hit object

This file explains how a single hit object translates into actual sample playback — the merge of beatmap-level bitfields with timing-point defaults with per-object overrides.

## Terminology recap

- **Sample set** = which sample family is used for `hitnormal`. One of `normal`, `soft`, `drum`.
- **Addition set** = which sample family is used for `hitwhistle` / `hitfinish` / `hitclap`. Same enum; defaults to the sample set.
- **Custom sample index** = integer N; files `<set>-<sound><N>.wav` override the default `<set>-<sound>.wav`. `N=0` means "no custom" (use the base file).
- **Volume** = 0–100, applied as a multiplier.

## Resolution order (per object)

For a circle or slider head, the values applied are:

1. Start with **timing-point defaults** at `object.time` (sampleSet / sampleIndex / volume).
2. Override any fields provided by the object's trailing `hitSample` group (`[0]` = sampleSet, `[1]` = additionSet, `[2]` = customIndex, `[3]` = volume).
3. Expand the `hitSound` bitfield into concrete sounds:
   - Always: `hitnormal` at the resolved sample set.
   - If `& 2`: `hitwhistle` at the resolved addition set.
   - If `& 4`: `hitfinish` at the resolved addition set.
   - If `& 8`: `hitclap` at the resolved addition set.

All of these play **simultaneously** if `LayeredHitSounds=1` in skin.ini (default). Otherwise only one plays (unusual).

## For sliders

Slider additionally produces:

- **`sliderslide`** — continuous; loops for the slider's full duration. Resolved sample set = object's main sample set.
- **`sliderwhistle`** — only if the slider's own `hitSound & 2`; looped like sliderslide.
- **`slidertick`** — at each computed tick position. Resolved sample set = active timing-point sample set at that tick's absolute time (not the object's sample set — important!). Skintool's parser confirms this by re-evaluating the timing point per tick.
- **Edge sounds** (at repeat points + tail):
  - Always `hitnormal` at that edge's sample set.
  - Additions per edge's own hitsound bitfield (from `edgeHitsounds[i]`), at that edge's addition set (from `edgeSamplesets[i]`).

## Sample file lookup

Given resolved `(sampleSet, soundName, customIndex, volume)`:

1. If `customIndex > 0`, try `{sampleSet}-{soundName}{customIndex}.{wav|ogg|mp3|flac}` in the beatmap folder first, then the skin folder.
2. Otherwise (or on miss), try `{sampleSet}-{soundName}.{ext}` in beatmap folder first, then skin.
3. Fallback chain (per skintool's `HitsoundRenderer.get_sound_file`):
   ```
   <set>-<sound> → normal-<sound> → soft-<sound> → drum-<sound> → <sound>
   ```
4. Beatmap-provided files override the skin's. This is how **map-local custom hitsounds** (explicit artistic use) work.

Extensions tried, in order: `.wav`, `.ogg`, `.mp3`, `.flac`.

## Volume application

Applied per-sample at playback: `final_amplitude = sample_amplitude × (volume / 100.0)`. Timing-point volume is the default; object-level volume overrides for that object only.

## Concrete example

Given:
- Uninherited timing point at t=0: `sampleSet=1 (normal)`, `sampleIndex=0`, `volume=100`.
- Inherited timing point at t=5000: `sampleSet=2 (soft)`, `volume=60`.
- Circle at `t=6000`, `hitSound = 0|2|4 = 6` (whistle + finish), trailing `hitSample = 3:3:2:80:`.

Resolution:
- Start: `sampleSet=soft`, `additionSet=soft`, `sampleIndex=0`, `volume=60` (from inherited TP).
- Override from `hitSample`: `sampleSet=drum`, `additionSet=drum`, `sampleIndex=2`, `volume=80`.
- Play simultaneously at volume 0.8:
  - `drum-hitnormal2.wav` (sample set = drum, index 2).
  - `drum-hitwhistle2.wav` (addition set = drum, index 2).
  - `drum-hitfinish2.wav` (addition set = drum, index 2).

## Gotchas

- **Slider ticks don't inherit the slider's object-level sample set** — each tick re-evaluates the timing point at its own time. Mappers use this to produce "sweeping" tick sound changes across a slider.
- **Missing `hitSample` → inherit everything from timing point**, not "use defaults" — the timing point's `sampleIndex` still applies.
- **Sample index `0` and missing are equivalent** (both mean "use the non-indexed file").
- The parser stores mapped set names as strings (`"normal"`/`"soft"`/`"drum"`) internally; when building output filenames you concatenate them directly.
- `LayeredHitSounds=0` in the skin's `skin.ini` disables the additions-layering (only hitnormal plays). Default is on.
