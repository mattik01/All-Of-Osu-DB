"""Fixture-driven tests for the Liquipedia mappool parser dispatcher.

No network. The dispatcher and its sub-parsers are pure functions over
wikitext strings; these tests pin the modern (2020+) plain-bullet format,
the older bare-beatmap URL form, and the warning-row fallback for unknown
layouts.
"""

from __future__ import annotations

import re

import pytest

from all_of_osu_db.layerA.liquipedia_parsers import parse_round_wikitext


SLOT_RE = re.compile(r"^(NM[1-9]|HD[1-9]|HR[1-9]|DT[1-9]|FM[1-9]|TB)$")

COMMON_KWARGS = dict(
    tournament="osu! World Cup 2023",
    tournament_slug="Osu_World_Cup/2023",
    round_name="Grand Finals",
    source_url="https://liquipedia.net/osu/Osu_World_Cup/2023",
    source_revision=12345,
)


MODERN_FIXTURE = """\
===Grand Finals===
* '''NM1''' : [https://osu.ppy.sh/beatmapsets/2078743#osu/4352819 <nowiki>Kominami Yasuha - 3355411 [1122411]</nowiki>]
* '''NM2''' : [https://osu.ppy.sh/beatmapsets/2078744#osu/4352820 <nowiki>Marmalade butcher - Amanita (DeviousPanda) [Collab Extreme]</nowiki>]
* '''HD1''' : [https://osu.ppy.sh/beatmapsets/2078745#osu/4352821 <nowiki>artist - title [diff]</nowiki>]
* '''DT1''' : [https://osu.ppy.sh/beatmapsets/2078730#osu/4352790 <nowiki>senya - Koborezu no Negaigoto [Satellite]</nowiki>]
* '''TB''' : [https://osu.ppy.sh/beatmapsets/2078750#osu/4352830 <nowiki>Camellia - Operation: Zenithfall [TB]</nowiki>]
"""


LEGACY_FIXTURE_NM_ONLY = """\
===Grand Finals===
* '''NM1''' : [https://osu.ppy.sh/beatmaps/11091 <nowiki>BeForU - Love Shine [Hard]</nowiki>]
* '''NM2''' : [https://osu.ppy.sh/beatmaps/21422 <nowiki>BRANDY - The Festival of Ghost 2 [DaRRi MiX]</nowiki>]
* '''TB''' : [https://osu.ppy.sh/beatmaps/20019 <nowiki>Hyadain - Battle with the Four Fiends [Sinistro]</nowiki>]
"""


UNKNOWN_FIXTURE = """\
This page has only post-match templates, no actual mappool definitions.
{{Map|map=|score1=|score2=|winner=}}
{{Map|map=|score1=|score2=|winner=}}
"""


def test_modern_plain_bullet_extracts_all_slots() -> None:
    entries = parse_round_wikitext(MODERN_FIXTURE, **COMMON_KWARGS)
    assert len(entries) == 5
    slots = [e.slot for e in entries]
    assert slots == ["NM1", "NM2", "HD1", "DT1", "TB"]
    for e in entries:
        assert SLOT_RE.match(e.slot), f"slot {e.slot!r} fails the slot regex"


def test_modern_plain_bullet_parses_artist_title_diff() -> None:
    [nm1, _, _, dt1, tb] = parse_round_wikitext(MODERN_FIXTURE, **COMMON_KWARGS)
    assert nm1.beatmap_artist == "Kominami Yasuha"
    assert nm1.beatmap_title == "3355411"
    assert nm1.beatmap_difficulty == "1122411"
    assert nm1.beatmapset_id == 2078743
    assert nm1.beatmap_id == 4352819
    assert dt1.beatmap_artist == "senya"
    assert dt1.beatmap_title == "Koborezu no Negaigoto"
    assert dt1.beatmap_difficulty == "Satellite"
    assert tb.slot_category == "TB"
    assert tb.slot_index is None


def test_modern_plain_bullet_records_provenance() -> None:
    [nm1, *_] = parse_round_wikitext(MODERN_FIXTURE, **COMMON_KWARGS)
    assert nm1.tournament == "osu! World Cup 2023"
    assert nm1.tournament_slug == "Osu_World_Cup/2023"
    assert nm1.round == "Grand Finals"
    assert nm1.source_url.startswith("https://liquipedia.net/osu/")
    assert nm1.source_revision == 12345
    assert nm1.parser_version.startswith("plain_bullet/")
    assert nm1.raw_wikitext.startswith("* '''NM1'''")


def test_legacy_bare_beatmap_url_only_returns_beatmap_id() -> None:
    entries = parse_round_wikitext(LEGACY_FIXTURE_NM_ONLY, **COMMON_KWARGS)
    assert len(entries) == 3
    nm1 = entries[0]
    assert nm1.beatmap_id == 11091
    assert nm1.beatmapset_id is None
    assert nm1.beatmap_artist == "BeForU"
    assert nm1.beatmap_title == "Love Shine"
    assert nm1.beatmap_difficulty == "Hard"


def test_bold_wrapped_tiebreaker_link_parses() -> None:
    fixture = (
        "* '''TB''' : '''[https://osu.ppy.sh/beatmaps/4881796 "
        "<nowiki>Camellia - Operation: Zenithfall (Mir) [FINAL MISSION]</nowiki>]'''\n"
    )
    entries = parse_round_wikitext(fixture, **COMMON_KWARGS)
    assert len(entries) == 1
    tb = entries[0]
    assert tb.slot == "TB"
    assert tb.beatmap_id == 4881796
    assert tb.beatmap_artist == "Camellia"
    assert tb.beatmap_title == "Operation: Zenithfall"
    assert tb.beatmap_difficulty == "FINAL MISSION"


def test_unknown_layout_emits_single_warning_row() -> None:
    entries = parse_round_wikitext(UNKNOWN_FIXTURE, **COMMON_KWARGS)
    assert len(entries) == 1
    warning = entries[0]
    assert warning.slot == "UNKNOWN"
    assert warning.slot_category == "UNKNOWN"
    assert warning.parser_version.startswith("warning/")
    assert "{{Map" in warning.raw_wikitext


def test_empty_input_emits_warning_row_not_crash() -> None:
    entries = parse_round_wikitext("", **COMMON_KWARGS)
    assert len(entries) == 1
    assert entries[0].slot == "UNKNOWN"


@pytest.mark.parametrize("bad_line", [
    "* NM1 : [https://osu.ppy.sh/beatmaps/11091 <nowiki>X - Y [Z]</nowiki>]",
    "  '''NM1''' [https://osu.ppy.sh/beatmaps/11091 X - Y [Z]]",
    "* '''XX1''' : [https://osu.ppy.sh/beatmaps/11091 <nowiki>X - Y [Z]</nowiki>]",
])
def test_unrecognised_line_does_not_yield_entry(bad_line: str) -> None:
    fixture = MODERN_FIXTURE + bad_line + "\n"
    entries = parse_round_wikitext(fixture, **COMMON_KWARGS)
    assert len(entries) == 5
