from pathlib import Path

from conftest import run_cli
from stats import compute_accuracy, compute_kd, compute_round_summary

STATS_PY = Path(__file__).parent.parent / "stats.py"
MISSION_JSONL = Path(__file__).parent.parent.parent / "mission.jsonl"


def run_stats(*args):
    return run_cli(STATS_PY, *args)

DONK = {"name": "donk", "steamid": "76561198386265483", "team": "Spirit"}
BROKY = {"name": "broky", "steamid": "76561198201620490", "team": "FaZe"}


def test_compute_accuracy_counts_all_shots_and_damage_events_with_no_filter():
    events = [
        {"type": "shot", "round": 1, "player": DONK},
        {"type": "shot", "round": 1, "player": BROKY},
        {"type": "damage", "round": 1, "attacker": DONK, "victim": BROKY},
    ]

    result = compute_accuracy(events)

    assert result == {"hits": 1, "shots": 2, "accuracy": 0.5}


def test_compute_accuracy_filters_hits_by_attacker_not_victim():
    events = [
        {"type": "damage", "round": 1, "attacker": DONK, "victim": BROKY},
        {"type": "damage", "round": 1, "attacker": BROKY, "victim": DONK},
    ]

    result = compute_accuracy(events, player="donk")

    assert result["hits"] == 1


def test_compute_accuracy_filters_shots_by_shooter():
    events = [
        {"type": "shot", "round": 1, "player": DONK},
        {"type": "shot", "round": 1, "player": BROKY},
    ]

    result = compute_accuracy(events, player="donk")

    assert result["shots"] == 1


def test_compute_accuracy_filters_by_team():
    events = [
        {"type": "shot", "round": 1, "player": DONK},
        {"type": "shot", "round": 1, "player": BROKY},
        {"type": "damage", "round": 1, "attacker": DONK, "victim": BROKY},
        {"type": "damage", "round": 1, "attacker": BROKY, "victim": DONK},
    ]

    result = compute_accuracy(events, team="Spirit")

    assert result == {"hits": 1, "shots": 1, "accuracy": 1.0}


def test_compute_accuracy_filters_by_round():
    events = [
        {"type": "shot", "round": 1, "player": DONK},
        {"type": "shot", "round": 2, "player": DONK},
    ]

    result = compute_accuracy(events, round_number=1)

    assert result["shots"] == 1


def test_compute_accuracy_returns_none_when_no_shots():
    assert compute_accuracy([])["accuracy"] is None


def test_compute_kd_counts_kills_and_deaths_for_player():
    events = [
        {"type": "kill", "round": 1, "attacker": DONK, "victim": BROKY},
        {"type": "kill", "round": 1, "attacker": BROKY, "victim": DONK},
        {"type": "kill", "round": 1, "attacker": DONK, "victim": BROKY},
    ]

    result = compute_kd(events, player="donk")

    assert result == {"kills": 2, "deaths": 1, "kd": 2.0}


def test_compute_kd_filters_by_round():
    events = [
        {"type": "kill", "round": 1, "attacker": DONK, "victim": BROKY},
        {"type": "kill", "round": 2, "attacker": DONK, "victim": BROKY},
    ]

    result = compute_kd(events, player="donk", round_number=1)

    assert result["kills"] == 1


def test_compute_kd_returns_none_when_no_deaths():
    events = [{"type": "kill", "round": 1, "attacker": DONK, "victim": BROKY}]

    assert compute_kd(events, player="donk")["kd"] is None


def test_compute_round_summary_reports_winner_reason_and_bomb_site():
    events = [
        {"type": "round", "round": 6, "start_tick": 1, "end_tick": 2, "winner": "Spirit", "reason": "bomb_exploded", "bomb_site": "A"},
    ]

    result = compute_round_summary(events, 6)

    assert result["round"] == 6
    assert result["winner"] == "Spirit"
    assert result["reason"] == "bomb_exploded"
    assert result["bomb_site"] == "A"


def test_compute_round_summary_tallies_kills_by_team():
    events = [
        {"type": "round", "round": 1, "start_tick": 1, "end_tick": 2, "winner": "Spirit", "reason": "t_killed", "bomb_site": None},
        {"type": "kill", "round": 1, "attacker": DONK, "victim": BROKY},
        {"type": "kill", "round": 1, "attacker": DONK, "victim": BROKY},
        {"type": "kill", "round": 1, "attacker": BROKY, "victim": DONK},
        {"type": "kill", "round": 2, "attacker": BROKY, "victim": DONK},
    ]

    result = compute_round_summary(events, 1)

    assert result["kills_by_team"] == {"Spirit": 2, "FaZe": 1}


def test_compute_round_summary_reports_who_planted_and_defused():
    events = [
        {"type": "round", "round": 1, "start_tick": 1, "end_tick": 2, "winner": "Spirit", "reason": "bomb_defused", "bomb_site": "B"},
        {"type": "bomb", "round": 1, "event": "pickup", "player": DONK, "site": None},
        {"type": "bomb", "round": 1, "event": "plant", "player": DONK, "site": "B"},
        {"type": "bomb", "round": 1, "event": "defuse", "player": BROKY, "site": "B"},
    ]

    result = compute_round_summary(events, 1)

    assert result["planted_by"] == DONK
    assert result["defused_by"] == BROKY


def test_compute_round_summary_reports_no_plant_or_defuse_when_absent():
    events = [
        {"type": "round", "round": 1, "start_tick": 1, "end_tick": 2, "winner": "Spirit", "reason": "t_killed", "bomb_site": None},
    ]

    result = compute_round_summary(events, 1)

    assert result["planted_by"] is None
    assert result["defused_by"] is None


def test_compute_kd_counts_all_players_with_no_filter():
    events = [
        {"type": "kill", "round": 1, "attacker": DONK, "victim": BROKY},
        {"type": "kill", "round": 1, "attacker": BROKY, "victim": DONK},
    ]

    result = compute_kd(events)

    assert result == {"kills": 2, "deaths": 2, "kd": 1.0}


def test_cli_accuracy_outputs_valid_json_for_a_player():
    result = run_stats(str(MISSION_JSONL), "accuracy", "--player", "donk")

    assert result["shots"] > 0
    assert result["hits"] >= 0
    assert result["accuracy"] == result["hits"] / result["shots"]


def test_cli_kd_outputs_valid_json_for_a_player():
    result = run_stats(str(MISSION_JSONL), "kd", "--player", "donk")

    assert result["kills"] > 0
    assert result["deaths"] > 0


def test_cli_round_summary_for_a_single_round_matches_known_real_round():
    result = run_stats(str(MISSION_JSONL), "round-summary", "--round", "6")

    assert result["round"] == 6
    assert result["winner"] == "Spirit"
    assert result["reason"] == "bomb_exploded"
    assert result["bomb_site"] == "A"


def test_cli_round_summary_without_round_flag_lists_every_round_and_tallies_13_11():
    result = run_stats(str(MISSION_JSONL), "round-summary")

    assert len(result) == 24
    wins = {"Spirit": 0, "FaZe": 0}
    for r in result:
        wins[r["winner"]] += 1
    assert wins == {"Spirit": 13, "FaZe": 11}
