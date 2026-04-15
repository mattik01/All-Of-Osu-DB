# `arrangement.json` — skintool's per-beatmap hitsound export

`beatmap-hitsound-extractor/process_all_beatmaps.py` produces, for each beatmap it processes, an `arrangement.json` alongside an exported audio track. The JSON is a fully-resolved "play this sample at this time" script — every layer of hitsound resolution (timing points, additions, sample index, volume, slider ticks) is flattened into explicit entries.

This is a useful **reference target**: if you ever build a hitsound/rhythm exporter for `All-Of-Osu-DB`, this schema is proven and already compatible with the sample files it ships with.

## Top-level schema

```json
{
  "beatmap_folder": "41823 The Quick Brown Fox - The Big Black",
  "difficulty_name": "... [WHO'S AFRAID OF THE BIG BLACK]",
  "start_time":  6966,                // ms within the original audio
  "end_time":   16966,                // ms (window = exactly 10 000 ms)
  "hit_objects": [ /* see below */ ],
  "unique_sounds":   ["hitnormal","whistle","clap","finish","slidertick","sliderslide"],
  "samplesets_used": ["soft","normal","drum"],
  "variety_score": 118,
  "audio_file": "beatmaps/<folder>/audio.mp3"
}
```

## Per-hit-object entry

```json
{
  "time": 9991,
  "sounds": [
    { "sound":"hitnormal",   "sampleset":"soft", "sample_index":0, "volume":100, "time_offset":0 },
    { "sound":"sliderslide", "sampleset":"soft", "sample_index":0, "volume":100, "time_offset":0, "duration":83 },
    { "sound":"hitnormal",   "sampleset":"soft", "sample_index":0, "volume":100, "time_offset":83 }
  ],
  "sampleset": "soft",
  "additions": "soft",
  "sample_index": 0,
  "volume": 100
}
```

Rules:

- Times on the object level are absolute ms relative to the beatmap start; times on the nested `sounds` entries are `time_offset` **relative to the parent object's `time`** (so the slider tail above is `9991 + 83 = 10074`).
- `sound` ∈ `hitnormal | whistle | finish | clap | slidertick | sliderslide` (and `sliderwhistle` in some maps).
- `sampleset` and `additions` on the object level describe the resolved sets used for that object. Individual nested `sounds` carry the set actually used (usually matches, but slider ticks reach out to their tick-time's timing point).
- `sample_index = 0` means "use the default file" (no numeric suffix).
- `duration` is present only on continuous sounds (`sliderslide`, `sliderwhistle`) — the runtime loops the sample for that many ms.

## How the JSON is produced

1. Parse `.osu` → `BeatmapParser.parse()` → typed `TimingPoint` and `HitObject` structs.
2. For each hit object, call `get_hitsounds_with_timing()` → list of `(sound_name, sampleset, sample_index, volume, time_offset[, duration])`.
3. The object's `sampleset`/`additions` are resolved from (timing point at `object.time` ← overridden by object's `hitSample` group).
4. Slider edges are expanded: one `hitnormal` per edge at `time_offset = edge_idx * single_slide_duration`, plus additions per `edgeHitsounds[i]` bitfield.
5. Slider ticks expanded: one `slidertick` per tick; tick's sample set re-read from the timing point at the tick's absolute time, not from the slider's object sample set.
6. Slider body: one `sliderslide` entry with `duration = end_time - start_time`. If `hitSound & 2`, add a parallel `sliderwhistle` entry.

## "variety_score" — beatmap interestingness heuristic

```
variety_score = unique_sounds_count   * 10
              + samplesets_used_count * 5
              + custom_samples_count  * 15
              + volume_levels_count   * 3
density_score = min(window_objects_count, 50)
total_score   = variety_score + density_score
```

- Window length: 10 000 ms.
- Sliding step: 5 000 ms.
- Window must contain ≥10 hit objects to be considered.

The top window by `total_score` becomes the exported 10-second clip (`start_time` / `end_time` / `audio_file`).

This is a rough "which 10 seconds of this beatmap best showcase hitsound variety" heuristic — useful for preview generation but not for research-grade sampling.

## Sample files in the extractor

Each exported folder under `beatmap-hitsound-extractor/samples/<name>/` contains:
- `arrangement.json` — the above schema.
- `audio.mp3` — the original 10-second window.
- `hitsounds.mp3` — just the synthesised hitsound track.
- `combined.mp3` — audio + hitsounds mixed.

These are artifacts, not runtime data. Useful as a reference when building a similar exporter.
