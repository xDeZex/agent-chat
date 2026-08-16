import pandas as pd
import pytest

import math

from extract_mission import is_grenade_weapon, label_bomb_sites, pair_rounds, player_obj, resolve_org, winner_org


def test_resolve_org_returns_spirit_for_spirit_player():
    assert resolve_org("76561198386265483") == "Spirit"  # donk


def test_resolve_org_returns_faze_for_faze_player():
    assert resolve_org("76561197989430253") == "FaZe"  # karrigan


def test_resolve_org_raises_for_unknown_steamid():
    with pytest.raises(ValueError):
        resolve_org("12345")


def test_pair_rounds_assigns_real_round_numbers_and_offsets_end_round_field():
    round_start = pd.DataFrame({"round": [1, 2], "tick": [1, 5757]})
    round_end = pd.DataFrame(
        {"round": [2, 3], "tick": [5437, 13244], "winner": ["CT", "CT"], "reason": ["bomb_defused", "t_killed"]}
    )

    rounds = pair_rounds(round_start, round_end)

    assert [r["round"] for r in rounds] == [1, 2]
    assert [r["start_tick"] for r in rounds] == [1, 5757]
    assert [r["end_tick"] for r in rounds] == [5437, 13244]
    assert [r["winner_side"] for r in rounds] == ["CT", "CT"]
    assert [r["reason"] for r in rounds] == ["bomb_defused", "t_killed"]


def test_winner_org_maps_ct_winner_to_the_org_that_was_ct_this_round():
    assert winner_org(winner_side="CT", ct_org="FaZe") == "FaZe"


def test_winner_org_maps_t_winner_to_the_org_that_was_not_ct_this_round():
    assert winner_org(winner_side="T", ct_org="FaZe") == "Spirit"


def test_label_bomb_sites_labels_the_site_nearest_ct_spawn_as_a():
    ct_spawn = (-1775.0, -1950.0)
    plant_positions = {
        317: [(-370.0, -2020.0)],  # near CT spawn -> A
        318: [(-1950.0, 350.0)],  # far from CT spawn -> B
    }

    labels = label_bomb_sites(ct_spawn, plant_positions)

    assert labels == {317: "A", 318: "B"}


def test_player_obj_represents_a_missing_attacker_as_world():
    assert player_obj(math.nan, math.nan) == {"name": "world", "steamid": None, "team": None}


@pytest.mark.parametrize(
    "weapon",
    ["weapon_flashbang", "weapon_smokegrenade", "weapon_hegrenade", "weapon_incgrenade", "weapon_molotov", "weapon_decoy"],
)
def test_is_grenade_weapon_true_for_grenade_weapons(weapon):
    assert is_grenade_weapon(weapon) is True


@pytest.mark.parametrize("weapon", ["ak47", "usp_silencer", "weapon_knife_stiletto", "hkp2000"])
def test_is_grenade_weapon_false_for_guns_and_knives(weapon):
    assert is_grenade_weapon(weapon) is False
