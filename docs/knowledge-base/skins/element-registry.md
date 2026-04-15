# Skin element registry

Full enumeration of skin image & audio element base-names recognised by skintool's `SkinElementRegistry.java`. These are the filenames osu! skins ship (without extension; extensions tried: `.png` / `.wav` / `.ogg` / `.mp3`).

## Naming conventions

- **All filenames are compared lowercase.** osu! itself is case-insensitive on skin files.
- **Animated elements** use a `-N` suffix starting at `-0`: `hit300-0.png`, `hit300-1.png`, … Loader scans frames until first missing.
- **HD / `@2x`** variant: append `@2x` before the extension: `hitcircle@2x.png`. Used on high-DPI displays.
- **Canonicalisation regex** for categorisation (skintool's `getDefinition`):
  1. lowercase
  2. strip extension after final `.`
  3. strip `-N` frame suffix matching `.*-\d+$`
  4. strip `@2x`

## Hit circles & approach

| Name | Animated | Notes |
| --- | --- | --- |
| `hitcircle` | no | Base circle. |
| `hitcircleoverlay` | yes | Drawn over the number (or under — see `HitCircleOverlayAboveNumber`). |
| `hitcircleselect` | no | Editor-only selection highlight. |
| `approachcircle` | no | Shrinking ring. |

## Hit bursts (animated)

| Name | Meaning |
| --- | --- |
| `hit0` | Miss. |
| `hit50` | 50 judgment. |
| `hit100` | 100. |
| `hit100k` | Katu 100 (slider-tail all-ticks-hit 100). |
| `hit300` | 300. |
| `hit300g` | Geki 300 (all-combo or spinner-perfect). |
| `hit300k` | Katu 300. |

## Lighting & particles

`lighting`, `particle50`, `particle100`, `particle300`.

## Sliders

| Name | Notes |
| --- | --- |
| `sliderb` | Slider ball — animated `sliderb0..sliderb9` (count from `SliderBallFrames`). |
| `sliderball-spec` | Specular overlay for ball. |
| `sliderfollowcircle` | Animated follow circle around the ball. |
| `sliderscorepoint` | Tick-score indicator. |
| `sliderpoint10`, `sliderpoint30` | Legacy score-point variants. |
| `reversearrow` | Rotated to point backward at repeat edges. |
| `slidertrack`, `slidertrackoverride` | Track body (can be tinted). |
| `sliderstartcircle`, `sliderstartcircleoverlay` | Head of slider. |
| `sliderendcircle`, `sliderendcircleoverlay` | Tail. |
| `sliderb-nd` | Background (referenced in skin README only). |
| `sliderb-spec` | Overlay / highlight pass. |

## Follow points

`followpoint` — animated `followpoint-0..7`. Drawn on a dotted line between successive combo objects.

## Spinner

`spinner-background`, `spinner-circle`, `spinner-metre`, `spinner-osu`, `spinner-clear`, `spinner-spin`, `spinner-approachcircle`, `spinner-rpm`, `spinner-top`, `spinner-bottom`, `spinner-glow`, `spinner-middle`, `spinner-middle2`.

## Cursor

`cursor`, `cursortrail`, `cursormiddle`, `cursor-smoke`. See `rendering-and-install.md` for CursorCentre / CursorExpand / CursorRotate behaviour.

## Numbers

| Base prefix | What it renders |
| --- | --- |
| `default-0` … `default-9` | Combo numbers inside hit circles. Prefix overridable via `skin.ini [Fonts] HitCirclePrefix`. |
| `score-0` … `score-9` | Score display digits. `score-comma`, `score-dot`, `score-percent`, `score-x`. |
| `combo-0` … `combo-9` | Combo counter. `combo-comma`, `combo-x`. |

## Health / Score bar

`scorebar-bg`, `scorebar-colour` (animated — skintool caps loading at 10 frames for perf), `scorebar-ki`, `scorebar-kidanger`, `scorebar-kidanger2`, `scorebar-marker`.

## Pause / fail / ranking

Pause: `pause-overlay`, `pause-back`, `pause-continue`, `pause-retry`.

Fail: `fail-background`.

Ranking screen: `ranking-panel`, `ranking-perfect`, `ranking-S`, `ranking-S-small`, `ranking-SH`, `ranking-SH-small`, `ranking-X`, `ranking-X-small`, `ranking-XH`, `ranking-XH-small`, `ranking-A` / `-A-small`, `ranking-B` / `-B-small`, `ranking-C` / `-C-small`, `ranking-D` / `-D-small`.

## Mod icons

Prefix `selection-mod-`, then: `easy`, `nofail`, `halftime`, `hardrock`, `suddendeath`, `perfect`, `doubletime`, `nightcore`, `hidden`, `flashlight`, `relax`, `autopilot`, `spunout`, `autoplay`, `cinema`.

## Menu / misc

`menu-background`, `menu-snow`, `welcome_text`, `inputoverlay-background`, `inputoverlay-key`, `play-skip` (animated), `play-unranked`, `arrow-pause`, `arrow-warning`, `multi-skipped`, `section-pass`, `section-fail`, `ready`, `count1`, `count2`, `count3`, `go`, `comboburst` (base) + `comboburst-0..9`, `star`, `star2`, `menu-back`, `menu-button-background`, `selection-mode`, `selection-mods`, `selection-random`, `selection-options`, `mode-osu`, `mode-taiko`, `mode-fruits`, `mode-mania`.

## Audio

### Gameplay hit sounds

For every sampleset `normal / soft / drum` (and taiko variants `taiko-normal-*`, `taiko-soft-*`, `taiko-drum-*`):

- `<set>-hitnormal`, `<set>-hitwhistle`, `<set>-hitfinish`, `<set>-hitclap`
- `<set>-slidertick`, `<set>-sliderslide`, `<set>-sliderwhistle`

Custom-indexed variants: `<set>-<sound>N` for any positive integer N.

### Spinner

`spinnerspin`, `spinnerbonus`, `spinnerbonus-max`, `spinnerfall`.

### Game state

`combobreak`, `failsound`, `applause`, `sectionpass`, `sectionfail`, `pause-loop`, `pause-back-click`, `pause-continue-click`, `pause-retry-click`, `pause-hover`.

### Countdown / ready

`count1s`, `count2s`, `count3s`, `gos`, `readys`.

### Menu

`heartbeat`, `seeya`, `welcome`, `menuback`, `menuhit`, `menuclick`, `click-short`, `click-short-confirm`, `click-close`, `back-button-click`, `back-button-hover`, `menu-direct-click`, `menu-edit-click`, `menu-exit-click`, `menu-freeplay-click`, `menu-multiplayer-click`, `menu-options-click`, `menu-play-click`, `menu-charts-click`, `menu-char-select`, `shutter`.

### Input

`key-confirm`, `key-delete`, `key-movement`, `key-press-1..4`, `check-on`, `check-off`, `select-expand`, `select-difficulty`.

### Multiplayer

`match-confirm`, `match-join`, `match-leave`, `match-notready`, `match-ready`, `match-start`.

### Nightcore mod overlays

`nightcore-kick`, `nightcore-clap`, `nightcore-hat`, `nightcore-finish` — layered beat-pattern sounds active only under the Nightcore mod.

### Editor / catch

`metronomelow` — editor metronome / catch banana.

## Categories (skintool's `ElementGroup`)

The registry categorises every element into one of:

```
HIT_CIRCLES, SLIDERS, SPINNER, CURSOR, APPROACH_CIRCLES,
HIT_BURSTS, FOLLOW_POINTS, HIT_SOUNDS, SLIDER_SOUNDS, SPINNER_SOUNDS,
UI_SOUNDS, MISC_SOUNDS, NUMBERS, HEALTH_BAR, SCORE_BAR,
MOD_ICONS, RANKING_SCREEN, PAUSE_OVERLAY, MENU_ELEMENTS,
PARTICLES, LIGHTING, MISC_IMAGES
```

This is useful for building a "skin completeness" checker — group-by category, count how many base-names have assets present.

## Known gaps

- **Mania column-specific skin elements** (`mania-key1`, `mania-stage-*`, `mania-note1`, etc.) are **not enumerated** in skintool's registry. If you need them, consult the osu! wiki's skin docs directly.
- **Combo-colour parsing** from `[Colours]` is not implemented in `LazyLoadingSkinService.parseBasicSkinInfo`; skintool pulls combo colours from a pre-built JSON manifest instead.
