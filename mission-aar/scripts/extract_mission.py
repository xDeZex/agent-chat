import bisect
import json
import sys

import pandas as pd
from demoparser2 import DemoParser

SPIRIT_STEAMIDS = {
    "76561198386265483",  # donk
    "76561198045898864",  # chopper
    "76561198995880877",  # zont1x
    "76561198081484775",  # SH1R0
    "76561199063238565",  # magixx
}
FAZE_STEAMIDS = {
    "76561197989430253",  # karrigan
    "76561197997351207",  # rain
    "76561198068422762",  # frozen
    "76561198201620490",  # broky
    "76561197991272318",  # ropz
}

GRENADE_WEAPONS = {
    "weapon_flashbang",
    "weapon_smokegrenade",
    "weapon_hegrenade",
    "weapon_incgrenade",
    "weapon_molotov",
    "weapon_decoy",
}


def is_grenade_weapon(weapon):
    return weapon in GRENADE_WEAPONS


def resolve_org(steamid):
    steamid = str(steamid)
    if steamid in SPIRIT_STEAMIDS:
        return "Spirit"
    if steamid in FAZE_STEAMIDS:
        return "FaZe"
    raise ValueError(f"unknown steamid: {steamid}")


def pair_rounds(round_start_df, round_end_df):
    starts = round_start_df.sort_values("tick").reset_index(drop=True)
    ends = round_end_df.sort_values("tick").reset_index(drop=True)
    if len(starts) != len(ends):
        raise ValueError(
            f"round_start has {len(starts)} rows but round_end has {len(ends)} rows; "
            "cannot pair them positionally"
        )
    return [
        {
            "round": i + 1,
            "start_tick": int(starts.loc[i, "tick"]),
            "end_tick": int(ends.loc[i, "tick"]),
            "winner_side": ends.loc[i, "winner"],
            "reason": ends.loc[i, "reason"],
        }
        for i in range(len(starts))
    ]


def winner_org(winner_side, ct_org):
    t_org = "Spirit" if ct_org == "FaZe" else "FaZe"
    return ct_org if winner_side == "CT" else t_org


def label_bomb_sites(ct_spawn_xy, plant_positions):
    def centroid(points):
        xs, ys = zip(*points)
        return sum(xs) / len(xs), sum(ys) / len(ys)

    def distance(a, b):
        return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5

    site_ids = list(plant_positions)
    distances = {site_id: distance(ct_spawn_xy, centroid(points)) for site_id, points in plant_positions.items()}
    nearest_site_id = min(site_ids, key=lambda site_id: distances[site_id])
    return {site_id: ("A" if site_id == nearest_site_id else "B") for site_id in site_ids}


TICK_RATE = 64
# Any Spirit player works as the reference for CT/T side resolution per round;
# donk is just the lexicographically-first steamid in the set.
ANCHOR_STEAMID = sorted(SPIRIT_STEAMIDS)[0]


def make_round_lookup(rounds):
    start_ticks = [r["start_tick"] for r in rounds]

    def round_of_tick(tick):
        i = bisect.bisect_right(start_ticks, tick) - 1
        return rounds[max(i, 0)]["round"]

    return round_of_tick


def resolve_ct_org_per_round(parser, rounds):
    sample_ticks = [r["start_tick"] + 10 for r in rounds]
    ticks_df = parser.parse_ticks(["team_num"], ticks=sample_ticks)
    ticks_df["steamid"] = ticks_df["steamid"].astype(str)
    anchor = ticks_df[ticks_df["steamid"] == ANCHOR_STEAMID].set_index("tick")["team_num"]
    anchor_org = resolve_org(ANCHOR_STEAMID)
    ct_org_by_round = {}
    for r, tick in zip(rounds, sample_ticks):
        anchor_is_ct = anchor.loc[tick] == 3
        ct_org_by_round[r["round"]] = anchor_org if anchor_is_ct else other_org(anchor_org)
    return ct_org_by_round


def other_org(org):
    return "FaZe" if org == "Spirit" else "Spirit"


def build_bomb_site_labels(parser, rounds):
    ct_spawn_tick = rounds[0]["start_tick"] + 30
    spawn_df = parser.parse_ticks(["X", "Y", "team_num"], ticks=[ct_spawn_tick])
    ct_rows = spawn_df[spawn_df["team_num"] == 3]
    ct_spawn_xy = (ct_rows["X"].mean(), ct_rows["Y"].mean())

    planted = parser.parse_event("bomb_planted")
    if planted.empty:
        return {}
    planted["user_steamid"] = planted["user_steamid"].astype("uint64")
    pos_df = parser.parse_ticks(["X", "Y"], ticks=planted["tick"].tolist())
    merged = pos_df.merge(planted, left_on=["tick", "steamid"], right_on=["tick", "user_steamid"])

    plant_positions = {}
    for site_id, group in merged.groupby("site"):
        plant_positions[int(site_id)] = list(zip(group["X"], group["Y"]))

    return label_bomb_sites(ct_spawn_xy, plant_positions)


def player_obj(name, steamid):
    if pd.isna(steamid) or pd.isna(name):
        return {"name": "world", "steamid": None, "team": None}
    return {"name": name, "steamid": str(steamid), "team": resolve_org(steamid)}


def build_round_records(rounds, ct_org_by_round, planted, site_labels, round_of_tick):
    planted_site_by_round = {}
    if not planted.empty:
        for _, row in planted.iterrows():
            planted_site_by_round[round_of_tick(row["tick"])] = site_labels[int(row["site"])]

    records = []
    for r in rounds:
        winner = winner_org(r["winner_side"], ct_org_by_round[r["round"]])
        records.append(
            {
                "type": "round",
                "round": r["round"],
                "start_tick": r["start_tick"],
                "end_tick": r["end_tick"],
                "winner": winner,
                "reason": r["reason"],
                "bomb_site": planted_site_by_round.get(r["round"]),
            }
        )
    return records


def build_kill_records(parser, round_of_tick):
    deaths = parser.parse_event("player_death")
    records = []
    for _, row in deaths.iterrows():
        assister = None
        if isinstance(row["assister_name"], str):
            assister = player_obj(row["assister_name"], row["assister_steamid"])
        records.append(
            {
                "type": "kill",
                "round": round_of_tick(row["tick"]),
                "tick": int(row["tick"]),
                "attacker": player_obj(row["attacker_name"], row["attacker_steamid"]),
                "victim": player_obj(row["user_name"], row["user_steamid"]),
                "weapon": row["weapon"],
                "headshot": bool(row["headshot"]),
                "assister": assister,
            }
        )
    return records


def build_damage_records(parser, round_of_tick):
    hurts = parser.parse_event("player_hurt")
    records = []
    for _, row in hurts.iterrows():
        records.append(
            {
                "type": "damage",
                "round": round_of_tick(row["tick"]),
                "tick": int(row["tick"]),
                "attacker": player_obj(row["attacker_name"], row["attacker_steamid"]),
                "victim": player_obj(row["user_name"], row["user_steamid"]),
                "weapon": row["weapon"],
                "damage": int(row["dmg_health"]),
                "headshot": row["hitgroup"] == "head",
            }
        )
    return records


def build_shot_records(parser, round_of_tick):
    fires = parser.parse_event("weapon_fire")
    fires = fires[~fires["weapon"].apply(is_grenade_weapon)].copy()
    fires["user_steamid"] = fires["user_steamid"].astype("uint64")
    pos_df = parser.parse_ticks(["X", "Y", "Z"], ticks=fires["tick"].tolist())
    merged = fires.merge(pos_df, left_on=["tick", "user_steamid"], right_on=["tick", "steamid"])
    if len(merged) != len(fires):
        raise ValueError(
            f"{len(fires) - len(merged)} weapon_fire event(s) had no matching position sample; "
            "the shot record count would silently undercount"
        )

    records = []
    for _, row in merged.iterrows():
        records.append(
            {
                "type": "shot",
                "round": round_of_tick(row["tick"]),
                "tick": int(row["tick"]),
                "player": player_obj(row["user_name"], row["user_steamid"]),
                "weapon": row["weapon"],
                "x": float(row["X"]),
                "y": float(row["Y"]),
                "z": float(row["Z"]),
            }
        )
    return records


def build_bomb_records(parser, round_of_tick, site_labels):
    event_names = {
        "bomb_pickup": "pickup",
        "bomb_dropped": "drop",
        "bomb_planted": "plant",
        "bomb_defused": "defuse",
    }
    frames = []
    for name, event_label in event_names.items():
        df = parser.parse_event(name)
        if df.empty:
            continue
        df = df.copy()
        df["event"] = event_label
        frames.append(df)

    all_ticks = [int(t) for df in frames for t in df["tick"].tolist()]
    pos_df = parser.parse_ticks(["X", "Y", "Z"], ticks=all_ticks)

    records = []
    for df in frames:
        df = df.copy()
        df["user_steamid"] = df["user_steamid"].astype("uint64")
        merged = df.merge(pos_df, left_on=["tick", "user_steamid"], right_on=["tick", "steamid"])
        if len(merged) != len(df):
            raise ValueError(
                f"{len(df) - len(merged)} {df['event'].iloc[0]} event(s) had no matching position sample; "
                "the bomb record count would silently undercount"
            )
        for _, row in merged.iterrows():
            has_site = "site" in row and pd.notna(row["site"])
            site = site_labels.get(int(row["site"])) if has_site else None
            records.append(
                {
                    "type": "bomb",
                    "round": round_of_tick(row["tick"]),
                    "tick": int(row["tick"]),
                    "event": row["event"],
                    "player": player_obj(row["user_name"], row["user_steamid"]),
                    "site": site,
                    "x": float(row["X"]),
                    "y": float(row["Y"]),
                    "z": float(row["Z"]),
                }
            )
    return records


def build_position_records(parser, rounds, round_of_tick):
    first_tick = rounds[0]["start_tick"]
    last_tick = rounds[-1]["end_tick"]
    sample_ticks = list(range(first_tick, last_tick + 1, TICK_RATE))
    pos_df = parser.parse_ticks(["X", "Y", "Z", "health"], ticks=sample_ticks)
    # A player not yet spawned/connected at a sampled tick has no health value; skip those snapshots.
    pos_df = pos_df.dropna(subset=["health"])

    records = []
    for _, row in pos_df.iterrows():
        records.append(
            {
                "type": "position",
                "round": round_of_tick(row["tick"]),
                "tick": int(row["tick"]),
                "player": player_obj(row["name"], row["steamid"]),
                "x": float(row["X"]),
                "y": float(row["Y"]),
                "z": float(row["Z"]),
                "health": int(row["health"]),
            }
        )
    return records


def main(demo_path, output_path):
    parser = DemoParser(demo_path)

    round_start = parser.parse_event("round_start")
    round_end = parser.parse_event("round_end")
    rounds = pair_rounds(round_start, round_end)
    round_of_tick = make_round_lookup(rounds)

    ct_org_by_round = resolve_ct_org_per_round(parser, rounds)
    site_labels = build_bomb_site_labels(parser, rounds)
    planted = parser.parse_event("bomb_planted")

    records = []
    records += build_round_records(rounds, ct_org_by_round, planted, site_labels, round_of_tick)
    records += build_kill_records(parser, round_of_tick)
    records += build_damage_records(parser, round_of_tick)
    records += build_shot_records(parser, round_of_tick)
    records += build_bomb_records(parser, round_of_tick, site_labels)
    records += build_position_records(parser, rounds, round_of_tick)

    with open(output_path, "w") as f:
        for record in records:
            f.write(json.dumps(record) + "\n")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
