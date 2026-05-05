"""Round-splitter tests for the Liquipedia OWC scraper.

The Mappool section on modern OWC pages does not use wiki sub-headings —
rounds are encoded with `{{Tabs dynamic}}` + `{{Tabs dynamic/tab|N}}`
markers. These tests pin both the tab-walker path and the legacy
sub-heading fallback path of `_split_into_rounds`.
"""

from __future__ import annotations

import mwparserfromhell

from all_of_osu_db.layerA.liquipedia import _split_into_rounds


TABS_DYNAMIC_FIXTURE = """\
==Mappools==
{{Tabs dynamic
|name1=Round of 32
|name2=Round of 16
|name3=Quarterfinals
|This=1
}}
{{Tabs dynamic/tab|1}}
{{box|start|padding=1em}}
{{Tabs dynamic
|name1=No Mod
|name2=Tiebreaker
|This=1
}}
{{Tabs dynamic/tab|1}}
* '''NM1''' : [https://osu.ppy.sh/beatmaps/100 <nowiki>A - B [C]</nowiki>]
{{Tabs dynamic/tab|2}}
* '''TB''' : [https://osu.ppy.sh/beatmaps/101 <nowiki>D - E [F]</nowiki>]
{{Tabs dynamic/end}}
{{box|end}}
{{Tabs dynamic/tab|2}}
{{box|start|padding=1em}}
* '''NM1''' : [https://osu.ppy.sh/beatmaps/200 <nowiki>R16-A - R16-B [R16-C]</nowiki>]
{{box|end}}
{{Tabs dynamic/tab|3}}
{{box|start|padding=1em}}
* '''NM1''' : [https://osu.ppy.sh/beatmaps/300 <nowiki>QF-A - QF-B [QF-C]</nowiki>]
{{box|end}}
{{Tabs dynamic/end}}
"""


SUBHEADING_FIXTURE = """\
==Mappool==
===Round of 16===
* '''NM1''' : [https://osu.ppy.sh/beatmaps/100 <nowiki>A - B [C]</nowiki>]
===Quarterfinals===
* '''NM1''' : [https://osu.ppy.sh/beatmaps/200 <nowiki>D - E [F]</nowiki>]
"""


FLAT_FIXTURE = """\
==Mappool==
* '''NM1''' : [https://osu.ppy.sh/beatmaps/100 <nowiki>A - B [C]</nowiki>]
* '''TB''' : [https://osu.ppy.sh/beatmaps/200 <nowiki>D - E [F]</nowiki>]
"""


def _section(wikitext: str):
    code = mwparserfromhell.parse(wikitext)
    sections = code.get_sections(levels=[2], include_lead=False)
    return sections[0]


def test_tabs_dynamic_splits_into_named_rounds() -> None:
    rounds = _split_into_rounds(_section(TABS_DYNAMIC_FIXTURE))
    names = [name for name, _ in rounds]
    assert names == ["Round of 32", "Round of 16", "Quarterfinals"]


def test_tabs_dynamic_round_bodies_contain_their_own_bullets() -> None:
    rounds = dict(_split_into_rounds(_section(TABS_DYNAMIC_FIXTURE)))
    assert "/beatmaps/200" in rounds["Round of 16"]
    assert "/beatmaps/300" in rounds["Quarterfinals"]
    # Round of 32 keeps its inner mod-bracket Tabs block — bullets are still there.
    assert "/beatmaps/100" in rounds["Round of 32"]
    assert "/beatmaps/101" in rounds["Round of 32"]


def test_tabs_dynamic_does_not_leak_other_rounds_into_a_round() -> None:
    rounds = dict(_split_into_rounds(_section(TABS_DYNAMIC_FIXTURE)))
    assert "/beatmaps/200" not in rounds["Round of 32"]
    assert "/beatmaps/300" not in rounds["Round of 16"]


def test_subheading_fallback_when_no_tabs_dynamic() -> None:
    rounds = _split_into_rounds(_section(SUBHEADING_FIXTURE))
    names = [name for name, _ in rounds]
    assert names == ["Round of 16", "Quarterfinals"]


def test_flat_section_returns_single_mappool_round() -> None:
    rounds = _split_into_rounds(_section(FLAT_FIXTURE))
    assert len(rounds) == 1
    name, body = rounds[0]
    assert name == "Mappool"
    assert "/beatmaps/100" in body and "/beatmaps/200" in body
