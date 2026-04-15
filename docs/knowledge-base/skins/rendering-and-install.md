# Rendering math & install-path detection

## Playfield coordinate system

- osu! playfield: **512 × 384 osu!pixels** (canonical).
- Origin `(0, 0)` = top-left.
- Hit objects in `.osu` use this coordinate system directly.
- Skintool's preview renders at internal `1366 × 768` and applies `scaleX = canvasWidth/1366`, `scaleY = canvasHeight/768` via JavaFX transform. (Not osu! behaviour — osu! itself scales the playfield into the letterboxed 4:3 area of the screen.)

Skintool's preview-tool selectable preview resolutions (all 16:9): `320×180`, `426×240`, `512×288`, `640×360`, `768×432`, `854×480`, `960×540`, `1024×576`, `1280×720`, `1366×768`.

## Base circle size

Skintool hard-codes `BASE_CIRCLE_SIZE = 80 px` as the circle diameter when no skin element is loaded. **This is not the real CS → diameter formula** — real osu! derives radius from CS and playfield scale. Do NOT use 80 as a canonical value.

## Approach circle scaling

Skintool's formula (preview-only):

```
approachScale(t) = 2.0 - clamp((t - appearTime) / APPROACH_TIME, 0, 1)
```

- Starts at `2.0×`.
- Shrinks linearly to `1.0×` at `hitTime`.
- `APPROACH_TIME = 0.8 s` — **hard-coded, NOT AR-derived**. Real osu! preempt time is AR-dependent; this preview uses one fixed value.

## Fade-in / fade-out

Skintool (preview-only):

- **Fade in**: first 0.1 s after `appearTime` ramps opacity `0 → 1`.
- **Sustain**: full opacity until hit.
- **Fade out**: `opacity = 1.0 - (timeSinceHit × 2)` — reaches zero at 0.5 s post-hit.
- Sliders stay opaque for their full duration, then fade out the same way.

## Hit-burst animation

`HitBurst` class constants:

- `ANIMATION_DURATION = 0.7 s`.
- Frame duration = `1 / animationFramerate` if positive, else `1 / numFrames` (i.e., stretch all frames across 1 s — matches skin.ini's `AnimationFramerate = -1` meaning).
- Rises 20 px over the animation with an ease-out-cubic curve:
  ```
  progress = 1 - (1 - t)^3
  ```
- Fade-out starts at 70% progress:
  ```
  opacity = 1.0 - (progress - 0.7) / 0.3   # for progress ≥ 0.7
  ```
- Lighting effect has `LIGHTING_DURATION = 0.4 s`, scales 0.6 → 0.9.

## Slider track rendering

Stroke build (skintool):

- Outer border stroke width = `BASE_CIRCLE_SIZE + 10 px`, colour = `skin.SliderBorder` (default `255,255,255`), alpha 0.8.
- Inner track stroke width = `BASE_CIRCLE_SIZE`, colour priority:
  1. `skin.SliderTrackOverride` if set.
  2. `comboColors[(comboNumber - 1) % N]`.
  3. Fallback `(180, 180, 200)`.
  Alpha 0.6.
- Stroke `cap = ROUND`, `join = ROUND`.

**Note: skintool uses straight start→end lines.** Real osu! draws a proper curve (Bezier / Catmull / Perfect-Circle). Do not port this preview code to anything that needs accurate slider shapes.

## Reverse arrow

Rotation: `atan2(startY - endY, startX - endX)` — points back toward the start from the reverse endpoint.

## Cursor

- `CursorCentre = true` → draw centred on `(x, y)`.
- `CursorCentre = false` → draw from top-left of the cursor image.
- `CursorExpand = true` → on click, set `scale = 1.3`; decay linearly to `1.0` over `0.1 s`.
- Trail: `MAX_TRAIL_POINTS = 20`; each point's opacity = `1.0 - age × 5` (vanish at ~0.2 s); global trail alpha = 0.5.

## Combo colour cycling

```java
comboIndex = (comboNumber - 1) % comboColors.size();
```

- Combo count resets / advances per the `type & 4` new-combo flag on hit objects.
- `type & 32` / `type & 64` can skip colours (spec feature — skintool doesn't implement the skip, just the increment).

## Score / accuracy display formula (preview only)

```
score += hitValue × max(1, combo / 10)
accuracy% = (h300*300 + h100*100 + h50*50) / (totalHits * 300) * 100
```

Illustrative only; real osu! applies mod multipliers, HP/combo multipliers, and tracks geki/katu separately.

## OS install-path detection

`OsuPathDetector.java` checks paths in order; first existing wins.

### Skins directory (parent of per-skin folders)

**Windows** (in order):
1. `%LOCALAPPDATA%\osu!\Skins`
2. `%USERPROFILE%\AppData\Local\osu!\Skins`
3. `C:\Users\<user.name>\AppData\Local\osu!\Skins` (uses Java's `user.name` system property)
4. `C:\osu!\Skins`
5. `D:\osu!\Skins`

**macOS**:
1. `~/Library/Application Support/osu!/Skins`
2. `~/.local/share/osu!/Skins` (lutris/compatibility layer)

**Linux / other**:
1. `~/.local/share/osu!/Skins`
2. `~/.osu/Skins`
3. `~/osu!/Skins`

### osu! install root

Same paths as above without the trailing `Skins`.

### "Is this a skin folder?" heuristic

A directory is considered a skin folder if it contains any file whose lowercase name:
- equals `skin.ini`, OR
- starts with `hitcircle` / `cursor` / `default-`, OR
- contains `hit` or `score`.

The Skins/ directory is "valid" if any subfolder passes the above test.

OS detection:
```java
osName = System.getProperty("os.name").toLowerCase();
isWindows = osName.contains("win");
isMac     = osName.contains("mac");
// else linux-ish
```

## Songs directory

Skintool doesn't explicitly detect Songs/ (its scope is skins), but by convention `Songs/` is a sibling of `Skins/` inside the osu! root. If you need it, use the same root paths above and append `\Songs`.
