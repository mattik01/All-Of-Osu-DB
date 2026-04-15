# Hit objects & sliders

`[HitObjects]` rows are comma-separated with **at least 5 mandatory fields**; the rest depend on the object type.

## Row format

```
x, y, time, type, hitSound[, objectParams][, hitSample]
```

| Field | Type | Meaning |
| --- | --- | --- |
| `x` | int | X coordinate in osu!pixels, **0–512**. |
| `y` | int | Y coordinate in osu!pixels, **0–384**. |
| `time` | int (ms) | Object start time. |
| `type` | int bitfield | See type bits below. |
| `hitSound` | int bitfield | See hitsound bits below. |
| `objectParams` | string | Type-dependent extras (slider curve, spinner end time, etc.). |
| `hitSample` | `A:B:C[:D:E]` | Optional trailing group: `sampleSet:additionSet:customIndex[:volume:filename]`. |

## `type` bitfield

| Bit | Meaning |
| --- | --- |
| `1` | Hit circle |
| `2` | Slider |
| `4` | New combo (visual-only — increments combo number, cycles combo colour) |
| `8` | Spinner |
| `16` | osu!mania hold note |
| `32,64` | Combo colour skip count (advances colour by N when new-combo is set) |
| `128` | osu!mania hold note variant marker |

Skintool parser detects type via:
```python
is_circle  = bool(type & 1)
is_slider  = bool(type & 2)
is_spinner = bool(type & 8)
```

## `hitSound` bitfield (additions)

| Bit | Sound |
| --- | --- |
| `0` (implicit) | `hitnormal` — always plays. |
| `2` | `hitwhistle` |
| `4` | `hitfinish` |
| `8` | `hitclap` |

Multiple additions stack. See [`hitsounds-in-beatmap.md`](./hitsounds-in-beatmap.md) for resolution rules.

## Coordinate system

Playfield is **512 × 384 osu!pixels**. `(0,0)` = top-left. Hit Rock (HR mod) flips the Y coordinate; Easy does not. Coordinates in `.osu` are pre-mod — mods apply at render time.

## Hit circle (type & 1)

Mandatory fields only; no objectParams. May carry a trailing `hitSample`.

## Spinner (type & 8)

One extra objectParam: `endTime` (int ms).

```
256,192,5432,12,0,8000,0:0:0:0:
```
(512/2, 384/2 centre; active 5432 → 8000 ms; hitsound 0; hitSample trailing.)

## Slider (type & 2) — the complex one

Full form:
```
x,y,time,type,hitSound,curveData,repeats,pixelLength,edgeHitsounds,edgeSamplesets,hitSample
```

Skintool's parser flow:
1. Split the tail on `,` → up to 5 parts: `[curveData, repeats, pixelLength, edgeHitsounds, edgeSamplesets]`.
2. Within `curveData`, split on `|` → `[curveType, "x:y", "x:y", ...]`.
3. Recognise trailing `hitSample` by the presence of `:` in what came after the comma-split.

### Curve types

Single-letter codes on the first `|`-token of `curveData`:

| Code | Name | Notes |
| --- | --- | --- |
| `L` | Linear | Polyline through anchor points. |
| `B` | Bezier | One or more Bezier segments, separated by duplicated anchor points. |
| `C` | Catmull | Legacy Catmull-Rom. Rare in modern maps. |
| `P` | PerfectCircle | Exactly 3 anchor points (start, waypoint, end); defines a circumscribed arc. |

### Anchor points

`x:y` pairs separated by `|`. The object's `(x,y)` is implicit as the first anchor — `.osu` lists only the **post-start** anchors.

### Other slider fields

- `repeats` — integer ≥ 1. `1` = no repeat (one pass). `2` = one bounce back (two passes). Edge count = `repeats + 1`.
- `pixelLength` — float, arc length in osu!pixels.
- `edgeHitsounds` — `|`-separated ints, **one per edge** (`repeats + 1` entries). Each entry is a hitsound bitfield (same meaning as the object's `hitSound`). Index 0 = head (redundant with the object's own hitSound), 1..N = each reversal point and the final tail.
- `edgeSamplesets` — `|`-separated `A:B` pairs, one per edge: `sampleSet:additionSet` (same numeric enum). Default `0:0` if missing.

### Slider timing math

See [`timing-points.md`](./timing-points.md) for the SV resolution:

```
single_slide_duration = total_duration / repeats
edge_time(i) = object.time + single_slide_duration * i   # i in [0, repeats]
```

Tick times are computed per-segment; direction alternates on odd repeats. Ticks skipped if `tick_distance_px >= pixelLength`.

### Slider ball interpolation

Real osu! follows the curve (Bezier/Catmull/Perfect-Circle math). Skintool's preview approximates with a straight `start → end` lerp and ping-pong on `isRepeating` — **this repo does NOT implement real curve interpolation**.

## Trailing `hitSample` (`:`-separated group)

```
sampleSet:additionSet:customIndex[:volume:filename]
```

| Index | Meaning |
| --- | --- |
| `[0]` | Sample set for `hitnormal`. `0` = inherit from timing point, `1` = normal, `2` = soft, `3` = drum. |
| `[1]` | Addition set for whistle/finish/clap. Same enum. |
| `[2]` | Custom sample index (overrides the timing point's). |
| `[3]` | Volume 0–100 (overrides). |
| `[4]` | Explicit filename (replaces the whole lookup — rare). |

## osu!mania hold note (type & 128)

Appears only in mania mode maps. `objectParams` encodes end time in the hitSample position with a different delimiter: `endTime:sampleSet:additionSet:customIndex:volume:filename`. Not relevant for `All-Of-Osu-DB`'s mode=0 scope.

## New-combo flag

`type & 4` means "this is the start of a new combo." Increments the visible combo number, advances the combo colour index. The parser in skintool's renderer uses:

```java
comboIndex = (comboNumber - 1) % comboColors.size();
```
