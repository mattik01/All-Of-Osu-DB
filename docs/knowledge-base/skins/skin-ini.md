# `skin.ini` reference

A skin folder's `skin.ini` configures non-asset behaviour: animation framerate, combo colours, cursor options, font prefixes, etc. osu! is case-insensitive on keys; INI-style lines; `//` starts a comment.

Skintool reads it via `LazyLoadingSkinService.parseBasicSkinInfo()`; encoding is tried UTF-8 → ISO-8859-1 → Windows-1252 → stripped-ASCII as a last resort (old skins commonly use Windows-1252).

## `[General]`

| Key | Type | Default | Effect |
| --- | --- | --- | --- |
| `Name` | string | — | Skin display name. |
| `Author` | string | — | Mapper credit. |
| `Version` | string | — | Skin format version (`2.7`, `latest`, etc.). |
| `AnimationFramerate` | int | `-1` | `-1` → play all frames within 1 second. Positive N → fixed N FPS. |
| `AllowSliderBallTint` | bool (0/1) | `false` | If true, tint sliderball with combo colour. |
| `CursorCentre` | bool | `true` | true = render cursor from its centre; false = top-left anchored. |
| `CursorExpand` | bool | `true` | Cursor scales up on click (skintool uses 1.0 → 1.3 over 0.1s then back). |
| `CursorRotate` | bool | `true` | Cursor rotates continuously. |
| `CursorTrailRotate` | bool | `true` | Trail rotates with cursor. (The bundled default skin sets this to `0`.) |
| `HitCircleOverlayAboveNumber` | bool | `true` | true → overlay drawn AFTER (above) the combo number; false → before (under). |
| `SliderBallFlip` | bool | `true` | Horizontally flip sliderball animation frames when slider reverses direction. |
| `SliderBallFrames` | int | varies (10 in bundled default) | Frames available in `sliderb0..N-1`. |
| `SliderStyle` | int | 2 | Slider-rendering style enum (skintool doesn't act on it). |
| `LayeredHitSounds` | bool | `true` | Play multiple hitsounds simultaneously (hitnormal + additions). |
| `SpinnerFadePlayfield` | bool | `false` | Dim the playfield during spinners. |
| `SpinnerFrequencyModulate` | bool | `true` | Pitch-shift `spinnerspin` with rotation speed. |
| `SpinnerNoBlink` | bool | `false` | Disable approach-circle blink. |
| `ComboBurstRandom` | bool | `false` | Randomise which `comboburst-N` plays. |
| `CustomComboBurstSounds` | int list | — | Combo counts that trigger combo bursts (e.g. `50,100,250,500`). |

## `[Colours]`

Colour triples: `R,G,B` (each 0–255).

| Key | Default | Effect |
| --- | --- | --- |
| `Combo1` … `Combo8` | varies | Combo-colour palette. Cycled by `(comboNumber - 1) % N`. |
| `SliderBall` | — | Tint applied to sliderball image (if `AllowSliderBallTint` is true). |
| `SliderBorder` | `255,255,255` | Slider track outline colour. |
| `SliderTrackOverride` | — | Force-override for slider track colour (otherwise it uses the combo colour). |
| `SongSelectActiveText` | `0,0,0` | Text colour for the selected song-select entry. |
| `SongSelectInactiveText` | `255,255,255` | |
| `MenuGlow` | `0,78,155` | Logo / menu-button glow colour. |
| `StarBreakAdditive` | `255,182,193` | Particle tint on "break" sections. |
| `InputOverlayText` | `0,0,0` | Digit colour on input-overlay keys. |
| `SpinnerBackground` | `100,100,100` | Background tint during spinners. |

## `[Fonts]`

| Key | Default | Effect |
| --- | --- | --- |
| `HitCirclePrefix` | `default` | Filename prefix for combo-number digits. `default` → `default-0.png` through `default-9.png`. |
| `HitCircleOverlap` | `-2` | Pixel overlap between consecutive digits. Negative = closer together. |
| `ScorePrefix` | `score` | Score-display digit prefix. |
| `ScoreOverlap` | `0` | |
| `ComboPrefix` | `score` | Combo-counter digit prefix. (Yes, combo counter often re-uses the score prefix.) |
| `ComboOverlap` | `0` | |

## `[CatchTheBeat]` / `[Mania]`

Mode-specific sections. Skintool does **not** parse these. If you need them, the osu! wiki is authoritative.

## Comment syntax

```
// this is a comment
Name: My Skin     // trailing comments work too in most cases
```

## Where combo colours actually come from in skintool

The codebase's skin model has `comboColors` as a field, but `LazyLoadingSkinService.parseBasicSkinInfo()` only reads `Name`, `Author`, `Version` in its lightweight pass. Combo colours are loaded from a pre-built JSON manifest (`ManifestCache`) rather than re-parsed from `skin.ini` at runtime. Worth noting if you're looking at the source and wondering why `[Colours]` parsing seems missing — the manifest pipeline covers it.
