from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


SLOT_CATEGORIES = ("NM", "HD", "HR", "DT", "FM", "EZ", "FL", "TB")


@dataclass
class MapEntry:
    tournament: str
    tournament_slug: str
    round: str
    slot: str
    slot_category: str
    slot_index: int | None
    beatmap_artist: str | None
    beatmap_title: str | None
    beatmap_difficulty: str | None
    beatmap_id: int | None
    beatmapset_id: int | None
    mod_set: str | None
    raw_wikitext: str
    source_url: str
    source_revision: int | None
    parser_version: str
    scraped_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds")
    )

    def to_dict(self) -> dict:
        return {
            "tournament": self.tournament,
            "tournament_slug": self.tournament_slug,
            "round": self.round,
            "slot": self.slot,
            "slot_category": self.slot_category,
            "slot_index": self.slot_index,
            "beatmap_artist": self.beatmap_artist,
            "beatmap_title": self.beatmap_title,
            "beatmap_difficulty": self.beatmap_difficulty,
            "beatmap_id": self.beatmap_id,
            "beatmapset_id": self.beatmapset_id,
            "mod_set": self.mod_set,
            "raw_wikitext": self.raw_wikitext,
            "source_url": self.source_url,
            "source_revision": self.source_revision,
            "parser_version": self.parser_version,
            "scraped_at": self.scraped_at,
        }
