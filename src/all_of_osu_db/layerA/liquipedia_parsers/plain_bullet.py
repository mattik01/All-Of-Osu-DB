"""Parser for the plain-wiki-bullet mappool format used by Liquipedia OWC pages
from at least 2020 onward, and (in NM-only form) by OWC #1 in 2011.

Recognises lines shaped like:
    * '''NM1''' : [https://osu.ppy.sh/beatmapsets/<sid>#osu/<bid> <nowiki>Artist - Title (Mapper) [Diff]</nowiki>]

Bold variants (`**bold**` instead of `'''bold'''`), trailing whitespace, missing
`<nowiki>` wrappers, and bare `osu.ppy.sh/beatmaps/<bid>` URLs all parse.
Unparseable lines are skipped silently — `dispatch.parse_round_wikitext` is
responsible for emitting a single warning row per round if no maps were
recovered.
"""

from __future__ import annotations

import re

from .types import SLOT_CATEGORIES, MapEntry

PARSER_VERSION = "plain_bullet/v1"

_SLOT_RE = re.compile(
    r"""^\s*\*+\s*                              # bullet marker(s)
        (?:'''|\*\*)\s*                         # bold opener
        ([A-Z]{2}\d?|TB\d?)                     # slot label, e.g. NM1 or TB
        \s*(?:'''|\*\*)\s*                      # bold closer
        :?\s*                                   # optional colon
        \[(\S+)\s+(.+?)\]\s*$                   # [URL display-text]
    """,
    re.VERBOSE,
)

_SLOT_LABEL_RE = re.compile(r"^([A-Z]{2})(\d+)?$")

_BMS_URL_RE = re.compile(
    r"https?://osu\.ppy\.sh/beatmapsets/(\d+)(?:#\w+/(\d+))?"
)
_BM_URL_RE = re.compile(r"https?://osu\.ppy\.sh/beatmaps/(\d+)")
_B_URL_RE = re.compile(r"https?://osu\.ppy\.sh/b/(\d+)")

_TITLE_RE = re.compile(
    r"""^\s*
        (.+?)\s+-\s+                            # artist -
        (.+?)                                   # title
        (?:\s+\(([^)]+)\))?                     # optional (mapper)
        \s*\[([^\]]+)\]                         # [diff]
        \s*$""",
    re.VERBOSE,
)


def _strip_nowiki(text: str) -> str:
    return re.sub(r"</?nowiki\s*/?>", "", text).strip()


def _parse_slot(slot: str) -> tuple[str, int | None] | None:
    match = _SLOT_LABEL_RE.match(slot)
    if not match:
        return None
    cat, idx = match.group(1), match.group(2)
    if cat not in SLOT_CATEGORIES:
        return None
    return cat, int(idx) if idx is not None else None


def _parse_url(url: str) -> tuple[int | None, int | None]:
    if m := _BMS_URL_RE.search(url):
        sid = int(m.group(1))
        bid = int(m.group(2)) if m.group(2) else None
        return sid, bid
    if m := _BM_URL_RE.search(url):
        return None, int(m.group(1))
    if m := _B_URL_RE.search(url):
        return None, int(m.group(1))
    return None, None


def _parse_display(display: str) -> tuple[str | None, str | None, str | None]:
    cleaned = _strip_nowiki(display)
    m = _TITLE_RE.match(cleaned)
    if not m:
        return None, None, None
    artist = m.group(1).strip()
    title = m.group(2).strip()
    diff = m.group(4).strip()
    return artist, title, diff


def parse(
    wikitext: str,
    *,
    tournament: str,
    tournament_slug: str,
    round_name: str,
    source_url: str,
    source_revision: int | None,
) -> list[MapEntry]:
    """Parse a single round's wikitext into a list of MapEntry rows.

    Returns an empty list if no slot lines are recognised; the dispatcher
    decides whether to emit a warning row.
    """
    entries: list[MapEntry] = []
    for line in wikitext.splitlines():
        match = _SLOT_RE.match(line)
        if not match:
            continue
        slot_label, url, display = match.group(1), match.group(2), match.group(3)
        parsed_slot = _parse_slot(slot_label)
        if parsed_slot is None:
            continue
        slot_category, slot_index = parsed_slot
        sid, bid = _parse_url(url)
        artist, title, diff = _parse_display(display)
        entries.append(
            MapEntry(
                tournament=tournament,
                tournament_slug=tournament_slug,
                round=round_name,
                slot=slot_label,
                slot_category=slot_category,
                slot_index=slot_index,
                beatmap_artist=artist,
                beatmap_title=title,
                beatmap_difficulty=diff,
                beatmap_id=bid,
                beatmapset_id=sid,
                mod_set=slot_category,
                raw_wikitext=line.strip(),
                source_url=source_url,
                source_revision=source_revision,
                parser_version=PARSER_VERSION,
            )
        )
    return entries
