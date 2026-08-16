import json
from pathlib import Path

from conftest import MISSION_AAR_DIR, load_module, run_cli

QUERY_PATH = MISSION_AAR_DIR / "query"
query = load_module("query", QUERY_PATH)
filter_events = query.filter_events
parse_round_range = query.parse_round_range
parse_type_list = query.parse_type_list


def run_query(jsonl_path, *args):
    return run_cli(QUERY_PATH, str(jsonl_path), *args)


def test_filter_events_by_single_type():
    events = [
        {"type": "round", "round": 1},
        {"type": "shot", "round": 1},
        {"type": "kill", "round": 1},
    ]

    result = filter_events(events, types={"shot"})

    assert result == [{"type": "shot", "round": 1}]


def test_filter_events_by_multiple_types():
    events = [
        {"type": "round", "round": 1},
        {"type": "shot", "round": 1},
        {"type": "kill", "round": 1},
    ]

    result = filter_events(events, types={"shot", "kill"})

    assert [e["type"] for e in result] == ["shot", "kill"]


def test_filter_events_preserves_file_order_when_no_filters_given():
    events = [{"type": "shot", "round": 1}, {"type": "shot", "round": 2}]

    assert filter_events(events) == events


def test_parse_type_list_splits_comma_separated_values():
    assert parse_type_list(["shot,damage"]) == {"shot", "damage"}


def test_parse_type_list_merges_repeated_flags():
    assert parse_type_list(["shot", "damage,kill"]) == {"shot", "damage", "kill"}


def test_parse_round_range_parses_single_round():
    assert parse_round_range("5") == (5, 5)


def test_parse_round_range_parses_inclusive_range():
    assert parse_round_range("5-8") == (5, 8)


def test_filter_events_by_round_range():
    events = [
        {"type": "kill", "round": 4},
        {"type": "kill", "round": 5},
        {"type": "kill", "round": 6},
        {"type": "kill", "round": 9},
    ]

    result = filter_events(events, round_range=(5, 6))

    assert [e["round"] for e in result] == [5, 6]


def test_filter_events_by_tick_min_and_tick_max():
    events = [
        {"type": "shot", "tick": 100},
        {"type": "shot", "tick": 200},
        {"type": "shot", "tick": 300},
    ]

    result = filter_events(events, tick_min=150, tick_max=250)

    assert [e["tick"] for e in result] == [200]


def test_filter_events_by_tick_uses_start_tick_for_round_events():
    events = [
        {"type": "round", "round": 1, "start_tick": 1, "end_tick": 5437},
        {"type": "round", "round": 2, "start_tick": 5757, "end_tick": 13244},
    ]

    result = filter_events(events, tick_min=5000, tick_max=6000)

    assert [e["round"] for e in result] == [2]


DONK = {"name": "donk", "steamid": "76561198386265483", "team": "Spirit"}
BROKY = {"name": "broky", "steamid": "76561198201620490", "team": "FaZe"}


def test_filter_events_by_player_matches_shot_player_field_by_name():
    events = [
        {"type": "shot", "player": DONK},
        {"type": "shot", "player": BROKY},
    ]

    result = filter_events(events, player="donk")

    assert result == [{"type": "shot", "player": DONK}]


def test_filter_events_by_player_matches_shot_player_field_by_steamid():
    events = [{"type": "shot", "player": DONK}, {"type": "shot", "player": BROKY}]

    result = filter_events(events, player="76561198201620490")

    assert result == [{"type": "shot", "player": BROKY}]


def test_filter_events_by_player_matches_kill_attacker_victim_or_assister():
    kill_as_attacker = {"type": "kill", "attacker": DONK, "victim": BROKY, "assister": None}
    kill_as_victim = {"type": "kill", "attacker": BROKY, "victim": DONK, "assister": None}
    kill_as_assister = {"type": "kill", "attacker": BROKY, "victim": BROKY, "assister": DONK}
    kill_unrelated = {"type": "kill", "attacker": BROKY, "victim": BROKY, "assister": None}

    result = filter_events(
        [kill_as_attacker, kill_as_victim, kill_as_assister, kill_unrelated], player="donk"
    )

    assert result == [kill_as_attacker, kill_as_victim, kill_as_assister]


def test_filter_events_by_player_matches_damage_attacker_or_victim():
    dmg_as_attacker = {"type": "damage", "attacker": DONK, "victim": BROKY}
    dmg_as_victim = {"type": "damage", "attacker": BROKY, "victim": DONK}
    dmg_unrelated = {"type": "damage", "attacker": BROKY, "victim": BROKY}

    result = filter_events([dmg_as_attacker, dmg_as_victim, dmg_unrelated], player="donk")

    assert result == [dmg_as_attacker, dmg_as_victim]


def test_filter_events_by_player_excludes_round_events_with_no_player_fields():
    events = [{"type": "round", "round": 1, "winner": "Spirit"}]

    assert filter_events(events, player="donk") == []


def test_filter_events_by_team_matches_shot_players_team():
    events = [{"type": "shot", "player": DONK}, {"type": "shot", "player": BROKY}]

    result = filter_events(events, team="Spirit")

    assert result == [{"type": "shot", "player": DONK}]


def test_filter_events_by_team_matches_kill_attacker_victim_or_assister():
    kill = {"type": "kill", "attacker": BROKY, "victim": BROKY, "assister": DONK}

    assert filter_events([kill], team="Spirit") == [kill]


def test_filter_events_by_team_excludes_round_events_with_no_team_fields():
    events = [{"type": "round", "round": 1, "winner": "Spirit"}]

    assert filter_events(events, team="Spirit") == []


def test_filter_events_by_site_matches_only_bomb_events_with_that_site():
    bomb_a = {"type": "bomb", "event": "plant", "site": "A"}
    bomb_b = {"type": "bomb", "event": "plant", "site": "B"}
    bomb_no_site = {"type": "bomb", "event": "pickup", "site": None}
    shot = {"type": "shot", "player": DONK}

    result = filter_events([bomb_a, bomb_b, bomb_no_site, shot], site="A")

    assert result == [bomb_a]


def test_cli_outputs_valid_json_array_filtered_by_type_in_file_order(tmp_path):
    jsonl_path = tmp_path / "mission.jsonl"
    events = [
        {"type": "round", "round": 1, "start_tick": 1, "end_tick": 100},
        {"type": "shot", "round": 1, "tick": 10, "player": DONK, "weapon": "ak47", "x": 0, "y": 0, "z": 0},
        {"type": "shot", "round": 1, "tick": 20, "player": BROKY, "weapon": "ak47", "x": 0, "y": 0, "z": 0},
    ]
    jsonl_path.write_text("\n".join(json.dumps(e) for e in events) + "\n")

    result = run_query(jsonl_path, "--type", "shot")

    assert [e["tick"] for e in result] == [10, 20]


def test_cli_combines_multiple_flags():
    jsonl_path = MISSION_AAR_DIR / "mission.jsonl"

    result = run_query(jsonl_path, "--type", "shot", "--player", "donk", "--round", "1")

    assert len(result) > 0
    assert all(e["type"] == "shot" and e["round"] == 1 and e["player"]["name"] == "donk" for e in result)


def test_cli_defaults_to_mission_jsonl_next_to_the_script_when_no_path_given():
    result = run_cli(QUERY_PATH, "--type", "shot", "--player", "donk", "--round", "1")

    assert len(result) > 0
    assert all(e["type"] == "shot" and e["round"] == 1 and e["player"]["name"] == "donk" for e in result)
