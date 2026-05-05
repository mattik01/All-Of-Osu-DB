"""Match-classifier tests for verify_mappool.classify (no network)."""

from __future__ import annotations

import pytest

from all_of_osu_db.layerA.verify_mappool import classify, _normalise


@pytest.mark.parametrize(
    "a,b",
    [
        ("Camellia", "camellia"),
        ("Operation: Zenithfall", "Operation Zenithfall"),
        ("FINAL MISSION", "final-mission"),
        ("TK from Ling tosite sigure", "TK  from   Ling   tosite sigure"),
        ("BlackY feat. Risa Yuzuki", "BlackY  feat Risa Yuzuki"),
        ("naïve", "naive"),
    ],
)
def test_normalise_collapses_case_punct_whitespace_diacritics(a, b):
    assert _normalise(a) == _normalise(b)


def test_match_when_all_three_fields_match():
    api = {
        "id": 100,
        "version": "Extra",
        "beatmapset": {"id": 50, "artist": "Camellia", "title": "Operation: Zenithfall", "status": "ranked"},
    }
    status, fields = classify(
        liquipedia_id=100,
        api_response=api,
        liq_artist="Camellia",
        liq_title="Operation Zenithfall",
        liq_difficulty="extra",
    )
    assert status == "match"
    assert fields["verified_beatmapset_id"] == 50
    assert fields["verified_ranked_status"] == "ranked"


def test_mismatch_when_difficulty_differs():
    api = {
        "id": 100,
        "version": "Insane",
        "beatmapset": {"id": 50, "artist": "Camellia", "title": "Zenithfall"},
    }
    status, _ = classify(
        liquipedia_id=100,
        api_response=api,
        liq_artist="Camellia",
        liq_title="Zenithfall",
        liq_difficulty="Extra",
    )
    assert status == "mismatch"


def test_missing_when_api_returned_none_for_a_given_id():
    status, fields = classify(
        liquipedia_id=999999999,
        api_response=None,
        liq_artist="A", liq_title="B", liq_difficulty="C",
    )
    assert status == "missing"
    assert fields == {}


def test_no_id_when_liquipedia_did_not_capture_one():
    status, fields = classify(
        liquipedia_id=None,
        api_response=None,
        liq_artist="A", liq_title="B", liq_difficulty="C",
    )
    assert status == "no_id"
    assert fields == {}


def test_artist_title_can_come_from_either_top_level_or_beatmapset_block():
    api_topflat = {"id": 1, "artist": "X", "title": "Y", "version": "Z", "beatmapset_id": 9}
    status, fields = classify(
        liquipedia_id=1, api_response=api_topflat,
        liq_artist="X", liq_title="Y", liq_difficulty="Z",
    )
    assert status == "match"
    assert fields["verified_beatmapset_id"] == 9
