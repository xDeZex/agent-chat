import argparse
import json
import sys


def read_events(path):
    with open(path) as f:
        return [json.loads(line) for line in f]


def parse_type_list(values):
    types = set()
    for value in values:
        types.update(value.split(","))
    return types


def parse_round_range(value):
    if "-" in value:
        lo, hi = value.split("-", 1)
        return int(lo), int(hi)
    return int(value), int(value)


def event_tick(event):
    return event["tick"] if "tick" in event else event["start_tick"]


PLAYER_FIELDS_BY_TYPE = {
    "kill": ("attacker", "victim", "assister"),
    "damage": ("attacker", "victim"),
    "shot": ("player",),
    "bomb": ("player",),
    "position": ("player",),
}


def event_players(event):
    fields = PLAYER_FIELDS_BY_TYPE.get(event["type"], ())
    return [event[f] for f in fields if event.get(f) is not None]


def matches_player(event, player):
    return any(p["name"] == player or p["steamid"] == player for p in event_players(event))


def matches_team(event, team):
    return any(p["team"] == team for p in event_players(event))


def filter_events(
    events,
    *,
    types=None,
    round_range=None,
    tick_min=None,
    tick_max=None,
    player=None,
    team=None,
    site=None,
):
    if types is not None:
        events = [e for e in events if e["type"] in types]
    if round_range is not None:
        lo, hi = round_range
        events = [e for e in events if lo <= e["round"] <= hi]
    if tick_min is not None:
        events = [e for e in events if event_tick(e) >= tick_min]
    if tick_max is not None:
        events = [e for e in events if event_tick(e) <= tick_max]
    if player is not None:
        events = [e for e in events if matches_player(e, player)]
    if team is not None:
        events = [e for e in events if matches_team(e, team)]
    if site is not None:
        events = [e for e in events if e["type"] == "bomb" and e.get("site") == site]
    return events


def build_arg_parser():
    parser = argparse.ArgumentParser(description="Filter mission.jsonl events.")
    parser.add_argument("jsonl_path")
    parser.add_argument("--type", action="append", default=None)
    parser.add_argument("--player")
    parser.add_argument("--team")
    parser.add_argument("--round")
    parser.add_argument("--tick-min", type=int)
    parser.add_argument("--tick-max", type=int)
    parser.add_argument("--site", choices=["A", "B"])
    return parser


def main(argv):
    args = build_arg_parser().parse_args(argv)
    events = read_events(args.jsonl_path)
    result = filter_events(
        events,
        types=parse_type_list(args.type) if args.type is not None else None,
        round_range=parse_round_range(args.round) if args.round is not None else None,
        tick_min=args.tick_min,
        tick_max=args.tick_max,
        player=args.player,
        team=args.team,
        site=args.site,
    )
    json.dump(result, sys.stdout)


if __name__ == "__main__":
    main(sys.argv[1:])
