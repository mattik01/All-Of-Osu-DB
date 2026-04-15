# Timing points

`[TimingPoints]` rows define the beat grid and slider-velocity modulation. **Every hit object is evaluated against the active timing point(s) at its time.** Misparsing timing points = wrong slider durations, wrong ticks, wrong hitsounds.

## Row format (8 fields, comma-separated)

```
time, beatLength, meter, sampleSet, sampleIndex, volume, uninherited, effects
```

| Field | Type | Meaning |
| --- | --- | --- |
| `time` | int (ms) | Start time — parsed via `int(float(...))` to tolerate decimals. |
| `beatLength` | float | **Positive** → uninherited (defines BPM). **Negative** → inherited (defines SV multiplier). |
| `meter` | int | Time-signature numerator (beats per measure). Default `4`. |
| `sampleSet` | int | Default sample set at this point: `0` = beatmap default, `1` = normal, `2` = soft, `3` = drum. |
| `sampleIndex` | int | Custom sample index (`0` = no custom). |
| `volume` | int 0–100 | Volume percentage applied to hitsounds from this point forward. |
| `uninherited` | 0/1 | Redundant with sign of `beatLength` but authoritative; cast to bool. |
| `effects` | int bitfield | `& 1` = kiai, `& 8` = omit first-bar-line. **Not parsed by the skintool** — flagged as a gap if you need kiai timing. |

## Uninherited vs inherited

### Uninherited (timing point proper)

`beatLength > 0`, measured in ms-per-beat.

```
BPM = 60000 / beatLength
```

Example: `beatLength = 400` → `BPM = 150`.

### Inherited (greenline / SV change)

`beatLength < 0`. The negative value encodes an SV multiplier:

```
velocity_multiplier = -100 / beatLength
```

Examples:
- `beatLength = -100` → 1.0× velocity (neutral).
- `beatLength = -50`  → 2.0× velocity.
- `beatLength = -200` → 0.5× velocity.

Inherited points also carry their own `sampleSet`, `sampleIndex`, `volume` — **each overrides the uninherited point** for the time window it covers. This is how mappers modulate volume in kiai sections and swap sample sets mid-song.

## "Active timing point at time T"

The timing point in effect at time `T` is the latest point with `point.time <= T`. If multiple points share the exact same time (rare but legal), later-in-file wins.

For slider math you need **both**:
- The most recent **inherited** point at-or-before `T` (defines SV).
- The most recent **uninherited** point at-or-before `T` (defines base beat length / BPM).

If an inherited point is active, use its `velocity_multiplier`. If only uninherited points exist at that time, `velocity_multiplier = 1.0`.

## Slider-velocity math

```
base_sv    = (SliderMultiplier × 100) / uninherited.beatLength     # px per ms
actual_sv  = base_sv × velocity_multiplier                         # px per ms, modulated
slider_duration_ms = (pixelLength / actual_sv) × repeats           # total hold time
tick_distance_px   = (SliderMultiplier × 100) / SliderTickRate     # px between ticks
```

Where `SliderMultiplier` and `SliderTickRate` come from `[Difficulty]`.

Ticks are placed per repeat-segment; odd repeats reverse direction (ping-pong). Ticks are skipped if `tick_distance >= length` (too short for any tick to fit).

## Kiai

`effects & 1 = kiai`. Turns on visual flashing + sample-set emphasis. Parser does not currently expose this; the dump doesn't either. If you need kiai windows, parse `.osu` yourself.

## Per-object hitsound fields inherited from timing points

When a hit object doesn't override them, it inherits:
- `sampleSet` — used for `hitnormal` sound.
- `additionSet` — per-object override (default 0 = match sampleSet).
- `sampleIndex` — 0 = default, N = `normal-hitnormal{N}.wav` variant.
- `volume` — 0–100, applied as a `volume / 100.0` multiplier.

See [`hitsounds-in-beatmap.md`](./hitsounds-in-beatmap.md) for the resolution logic.
