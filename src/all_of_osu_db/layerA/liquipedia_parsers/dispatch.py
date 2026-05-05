"""Dispatcher for round-level mappool wikitext.

Parser families are tried in order. The first to return a non-empty list
wins. If none recognise the format, a single warning `MapEntry` is emitted
with `slot="UNKNOWN"` and the raw wikitext attached so an operator can
re-parse manually later.
"""

from __future__ import annotations

from . import plain_bullet
from .types import MapEntry

WARNING_PARSER_VERSION = "warning/v1"


def parse_round_wikitext(
    wikitext: str,
    *,
    tournament: str,
    tournament_slug: str,
    round_name: str,
    source_url: str,
    source_revision: int | None,
) -> list[MapEntry]:
    common_kwargs = dict(
        tournament=tournament,
        tournament_slug=tournament_slug,
        round_name=round_name,
        source_url=source_url,
        source_revision=source_revision,
    )
    for parser in (plain_bullet,):
        rows = parser.parse(wikitext, **common_kwargs)
        if rows:
            return rows

    return [
        MapEntry(
            tournament=tournament,
            tournament_slug=tournament_slug,
            round=round_name,
            slot="UNKNOWN",
            slot_category="UNKNOWN",
            slot_index=None,
            beatmap_artist=None,
            beatmap_title=None,
            beatmap_difficulty=None,
            beatmap_id=None,
            beatmapset_id=None,
            mod_set=None,
            raw_wikitext=wikitext.strip()[:4000],
            source_url=source_url,
            source_revision=source_revision,
            parser_version=WARNING_PARSER_VERSION,
        )
    ]
