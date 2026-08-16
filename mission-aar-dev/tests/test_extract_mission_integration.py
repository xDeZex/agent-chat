import json
from collections import Counter
from pathlib import Path

import pytest

from extract_mission import main

DEMO_PATH = Path(__file__).parent.parent.parent / "mission-aar" / "raw" / "spirit-vs-faze-mirage.dem"

pytestmark = pytest.mark.skipif(not DEMO_PATH.exists(), reason="real demo file not present")


@pytest.fixture(scope="module")
def mission_records(tmp_path_factory):
    output_path = tmp_path_factory.mktemp("mission") / "mission.jsonl"
    main(str(DEMO_PATH), str(output_path))
    with open(output_path) as f:
        return [json.loads(line) for line in f]


def test_covers_all_24_rounds_with_the_real_13_11_scoreline(mission_records):
    rounds = [r for r in mission_records if r["type"] == "round"]

    assert len(rounds) == 24
    assert [r["round"] for r in rounds] == list(range(1, 25))
    wins = Counter(r["winner"] for r in rounds)
    assert wins == {"Spirit": 13, "FaZe": 11}


def test_all_six_event_types_present(mission_records):
    types = {r["type"] for r in mission_records}
    assert types == {"position", "shot", "damage", "kill", "round", "bomb"}


def test_round_records_have_the_expected_shape(mission_records):
    rounds = [r for r in mission_records if r["type"] == "round"]
    for r in rounds:
        assert set(r) == {"type", "round", "start_tick", "end_tick", "winner", "reason", "bomb_site"}
        assert r["winner"] in {"Spirit", "FaZe"}
        assert r["bomb_site"] in {"A", "B", None}


def test_kill_and_damage_records_stay_unmerged(mission_records):
    kills = [r for r in mission_records if r["type"] == "kill"]
    damages = [r for r in mission_records if r["type"] == "damage"]

    assert len(kills) == 164
    assert len(damages) == 632


def test_shot_records_exclude_grenade_throws(mission_records):
    shots = [r for r in mission_records if r["type"] == "shot"]
    grenade_weapons = {
        "weapon_flashbang",
        "weapon_smokegrenade",
        "weapon_hegrenade",
        "weapon_incgrenade",
        "weapon_molotov",
        "weapon_decoy",
    }

    assert not any(s["weapon"] in grenade_weapons for s in shots)


def test_position_data_is_downsampled_to_roughly_one_snapshot_per_second(mission_records):
    positions = [r for r in mission_records if r["type"] == "position"]
    rounds = [r for r in mission_records if r["type"] == "round"]
    match_duration_ticks = rounds[-1]["end_tick"] - rounds[0]["start_tick"]
    match_duration_seconds = match_duration_ticks / 64

    # ~1 snapshot per player per second, not full per-tick volume (10 players).
    assert match_duration_seconds * 5 < len(positions) < match_duration_seconds * 15
