"""Verify scraped Liquipedia mappool beatmap_ids against osu! API v2.

Reads `data/layerA/liquipedia/owc_mappool.csv` (one row per pick), looks up
every `beatmap_id` via `OsuApiV2Client.get_beatmaps()`, and writes
`data/layerA/liquipedia/owc_mappool_verified.csv` with the source columns
plus a `verified_*` block describing how the Liquipedia entry compares to
what osu! actually serves today.

Verification status enum (`verified_status`):
- `match`        — id resolved AND (artist, title, difficulty) match after
                   case/whitespace/punctuation normalisation
- `mismatch`     — id resolved but at least one of artist/title/difficulty
                   differs from Liquipedia (worth manual review)
- `missing`      — id was given but the API returned no beatmap (deleted /
                   bad id / wrong number)
- `no_id`        — Liquipedia row had no beatmap_id at all (parser miss or
                   bare URL with no id captured)
"""

from __future__ import annotations

import csv
import logging
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

from ..config import Settings
from .osu_api_v2 import OsuApiV2Client

log = logging.getLogger(__name__)

VERIFIED_COLUMNS = (
    "verified_status",
    "verified_beatmap_id",
    "verified_beatmapset_id",
    "verified_artist",
    "verified_title",
    "verified_difficulty",
    "verified_ranked_status",
    "verified_at",
)

def _normalise(text: str | None) -> str:
    """Case/whitespace/punctuation-folded form for fuzzy comparison."""
    if text is None:
        return ""
    folded = unicodedata.normalize("NFKD", text).lower()
    # strip combining marks
    folded = "".join(ch for ch in folded if not unicodedata.combining(ch))
    # collapse anything non-alphanumeric to a single space
    folded = re.sub(r"[^a-z0-9]+", " ", folded).strip()
    return folded


def classify(
    *,
    liquipedia_id: int | None,
    api_response: dict | None,
    liq_artist: str | None,
    liq_title: str | None,
    liq_difficulty: str | None,
) -> tuple[str, dict]:
    """Return (verified_status, verified_fields_dict).

    verified_fields contains the API-side artist/title/version/beatmapset_id
    for visibility, regardless of match outcome.
    """
    if liquipedia_id is None:
        return "no_id", {}
    if api_response is None:
        return "missing", {}

    beatmapset = api_response.get("beatmapset") or {}
    api_artist = beatmapset.get("artist") or api_response.get("artist")
    api_title = beatmapset.get("title") or api_response.get("title")
    api_version = api_response.get("version")
    api_setid = api_response.get("beatmapset_id") or beatmapset.get("id")
    ranked = beatmapset.get("status") or api_response.get("status")

    fields = {
        "verified_beatmap_id": api_response.get("id") or liquipedia_id,
        "verified_beatmapset_id": api_setid,
        "verified_artist": api_artist,
        "verified_title": api_title,
        "verified_difficulty": api_version,
        "verified_ranked_status": ranked,
    }

    artist_ok = _normalise(api_artist) == _normalise(liq_artist)
    title_ok = _normalise(api_title) == _normalise(liq_title)
    diff_ok = _normalise(api_version) == _normalise(liq_difficulty)
    status = "match" if artist_ok and title_ok and diff_ok else "mismatch"
    return status, fields


def verify_mappool_csv(
    *,
    settings: Settings | None = None,
    input_path: Path | None = None,
    output_path: Path | None = None,
) -> tuple[Path, dict[str, int]]:
    """Run the API verification pass over a scraped mappool CSV.

    Returns (output_path, status_counts).
    """
    settings = settings or Settings()
    in_path = input_path or (Path(settings.liquipedia_output_dir) / "owc_mappool.csv")
    out_path = output_path or (
        Path(settings.liquipedia_output_dir) / "owc_mappool_verified.csv"
    )

    with in_path.open(encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        raise RuntimeError(f"No rows in {in_path}")

    fieldnames = list(rows[0].keys()) + list(VERIFIED_COLUMNS)
    ids: list[int] = []
    for r in rows:
        raw = r.get("beatmap_id") or ""
        if raw.isdigit():
            ids.append(int(raw))

    log.info("Verifying %d row(s); %d distinct beatmap_id(s) to look up.", len(rows), len(set(ids)))
    with OsuApiV2Client(settings) as client:
        responses = client.get_beatmaps(list(set(ids)))

    counts: dict[str, int] = {}
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    out_rows: list[dict] = []
    for r in rows:
        raw_id = r.get("beatmap_id") or ""
        bid = int(raw_id) if raw_id.isdigit() else None
        api = responses.get(bid) if bid is not None else None
        status, fields = classify(
            liquipedia_id=bid,
            api_response=api,
            liq_artist=r.get("beatmap_artist"),
            liq_title=r.get("beatmap_title"),
            liq_difficulty=r.get("beatmap_difficulty"),
        )
        counts[status] = counts.get(status, 0) + 1
        out_row = dict(r)
        out_row["verified_status"] = status
        for col in VERIFIED_COLUMNS:
            if col not in out_row:
                out_row[col] = ""
        for k, v in fields.items():
            out_row[k] = v if v is not None else ""
        out_row["verified_at"] = now
        out_rows.append(out_row)

    with out_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(out_rows)

    log.info("Wrote %d rows to %s; status breakdown: %s", len(out_rows), out_path, counts)

    from .liquipedia_load import load_to_sqlite

    sqlite_counts = load_to_sqlite(settings=settings, input_path=out_path)
    log.info("Loaded Layer A SQLite: %s", sqlite_counts)

    return out_path, counts
