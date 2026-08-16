# Survey: candidate games/datasets for mission event data

Research for [#2 "Survey candidate games/datasets for mission event data"](https://github.com/xDeZex/agent-chat/issues/2), part of the Wayfinder plan in #1. This is a **survey producing a shortlist for human sign-off, not a final decision**. The actual dataset choice is a separate follow-up ticket, [#3 "Choose the mission dataset"](https://github.com/xDeZex/agent-chat/issues/3).

## What we're looking for

The prototype needs a single flat data file representing one recorded "military training mission," sourced from a recorded competitive/esports shooter match, that a Claude Code session can query to answer questions like "what went wrong" and "did we fulfill our mission objectives." That requires:

- **Event-level data**, not just aggregate/summary stats: positions over time, shots fired, hits/kills (who shot/killed whom), and objective/round state.
- A structure that maps onto military framing: objectives, squads/teams (callsigns), and a clear win/loss or objective-completion outcome.
- Bonus: an accompanying recorded video of the same match.
- Preference for a **professional/competitive** recorded match over a casual/pickup match, since curated event data is more likely to exist for those.

## Candidates evaluated

### Counter-Strike 2 (and CS:GO) — shortlisted, top pick

**Event-level data, exactly how.** [`awpy`](https://github.com/pnxenopoulos/awpy) ([PyPI](https://pypi.org/project/awpy/), [docs](https://awpy.readthedocs.io/)) is a Python library (Rust core, `pip install awpy`) that parses CS2 `.dem` files and returns Polars dataframes: `dem.kills` (attacker + victim + weapon), `dem.damages`, `dem.shots` (individual fire events), `dem.ticks` (tick-by-tick player position/state), `dem.rounds`, `dem.bomb` (plant/defuse — the objective state), and `dem.grenades`. It wraps [`demoparser2`](https://github.com/LaihoE/demoparser) (also usable standalone) as its Rust parsing backend. This is the most complete event-level dataset of any candidate surveyed: continuous positions, discrete shot events, kill attribution, and objective (bomb) state all in one file.

**Video of the same match.** Yes. HLTV match pages link both the `.dem` download and the Twitch broadcast VOD for the same match side by side (confirmed via HLTV's own demo/VOD workflow description).

**Mapping to mission framing.** Strong. 5v5 teams (map to squads), round-based objective (plant/defuse the bomb, or defend the site — maps directly to "did we fulfill our mission objectives"), clear round win/loss and match win/loss.

**Professional match data.** Yes, and this is the strongest point: HLTV.org hosts free, permanent `.dem` downloads for effectively every pro match — Majors, ESL, BLAST, etc. (pro demos, unlike matchmaking demos, don't expire). No partner/API-key gate required to obtain a specific named pro match.

Sources: [awpy GitHub](https://github.com/pnxenopoulos/awpy), [awpy on PyPI](https://pypi.org/project/awpy/), [awpy docs](https://awpy.readthedocs.io/), [demoparser2 GitHub](https://github.com/LaihoE/demoparser), [demoinfocs-golang](https://github.com/markus-wa/demoinfocs-golang) (alternate Go parser, kills/shots/round events/grenade trajectories), [HLTV demo/VOD download guidance](https://community.skin.club/en/articles/how-to-watch-demo-in-cs2).

### Rainbow Six Siege — shortlisted, second place

**Event-level data, exactly how.** Ubisoft officially publishes `.rec` "Match Replay" files for its own pro events — confirmed for Six Invitational 2023, BLAST R6 Regional Leagues, and BLAST R6 Majors, distributed as day-bundled zip downloads via an official Ubisoft blog post ([dotesports coverage](https://dotesports.com/rainbow-6/news/how-to-download-match-replays-from-the-six-invitational), [Liquipedia's replay file index](https://liquipedia.net/rainbowsix/R6_Match_Replay_Files)). The main open community parser, [`r6-dissect`](https://github.com/redraskal/r6-dissect) (Go, CLI + library, JSON/Excel output), reads the Dissect `.rec` format and exposes match/team/player metadata plus "match feedback" events: kills, headshots, objective locates, defuser plants/disables, bans, disconnects. **Important gap:** per its own README, `r6-dissect` does **not** currently expose continuous player positions or individual shot/bullet events — those are listed as unimplemented/planned. A second, more exploratory community project ([`draguve/R6-Replays`](https://github.com/draguve/R6-Replays)) is attempting to reverse-engineer the remaining binary payload but by its own admission hasn't decoded positions or shots either. There's a separate hosted service, [R6Data](https://r6data.com/api-docs) (redirects to [r6.arenyze.com](https://r6.arenyze.com/api-docs)), whose docs reference `locationUpdates`/`positions` arrays in its normalized payload, which suggests it goes further than `r6-dissect`, but the public docs don't confirm the granularity (per-tick vs per-event) and it's a closed hosted API rather than an inspectable open parser.

**Video of the same match.** Yes — R6 esports VODs are readily available (official Ubisoft esports site, Twitch/YouTube archives of BLAST/Six Invitational broadcasts) for the same events the `.rec` files come from.

**Mapping to mission framing.** Good structurally (attacker/defender teams, round-based site objectives, plant/defuse mirrors CS2's bomb objective) but weaker in practice today because the freely-available open-source parsing stops short of positions/shots.

**Professional match data.** Yes, and notably this is *official, Ubisoft-published* pro replay data (not scraped), which is unusually strong provenance. The [official R6 Data Portal](https://grid.gg/get-rainbow-six/) (via GRID) offers deeper event-level scrim/tournament data but is partner/application-gated, not publicly self-serve.

Sources: [r6-dissect GitHub](https://github.com/redraskal/r6-dissect), [dotesports: downloading Six Invitational replays](https://dotesports.com/rainbow-6/news/how-to-download-match-replays-from-the-six-invitational), [Liquipedia R6 Match Replay Files](https://liquipedia.net/rainbowsix/R6_Match_Replay_Files), [draguve/R6-Replays GitHub](https://github.com/draguve/R6-Replays), [R6Data/Arenyze API docs](https://r6.arenyze.com/api-docs), [GRID R6 Siege Data Portal](https://grid.gg/get-rainbow-six/).

### Arma 3 (and milsim-adjacent titles) — evaluated, not shortlisted

**Event-level data, exactly how.** [OCAP2](https://github.com/OCAP2/OCAP) is a real, actively-maintained Arma 3 server-side addon that captures unit/vehicle positions throughout an operation plus shots, kills, hits, connects/disconnects, markers, and (with ACE3) mine/explosive events, played back on a web-based interactive map. This is exactly the kind of event granularity the criteria ask for, so the "milsim ecosystem produces good data" assumption is largely borne out — **with one large caveat**: OCAP only records missions where the server operator installed the addon and was actively recording *at the time the mission was played*. There is no equivalent to a `.dem`/`.rec` file that exists independently of the mission having been run through OCAP — you cannot retroactively extract this data from an arbitrary already-played Arma mission. So the candidate pool is restricted to whichever specific communities happened to record with OCAP (or similar tools like [After Action Review 3](https://forums.bohemia.net/forums/topic/234176-after-action-review-3-%E2%80%94-battle-replays-in-arma-3/) or [tS_AARViewer](https://github.com/10Dozen/tS_AARViewer)) and published the result.

**Video of the same match.** Not systematically — depends entirely on whether the specific community also streamed/recorded video, which is inconsistent across milsim units.

**Mapping to mission framing.** Excellent narratively (it *is* literally a military mission briefing/objectives/AAR structure) — but that's exactly the "thematically on-the-nose" assumption the task asked us not to lean on uncritically.

**Professional match data.** Weak. Arma 3 does have a competitive PvP scene — Electronic Sports Masters (ESM) runs Arma 3 PvP competitions, and Bohemia Interactive ran an "End Game Tournament" — but it's small and niche compared to CS2/R6, and there's no confirmed public case of a competitive Arma 3 match having been both OCAP-recorded and published as a downloadable dataset. Most published OCAP-style recordings come from cooperative milsim unit operations (players vs. AI), not competitive PvP with a clean win/loss outcome.

**Verdict:** ruled out for this round — the data model is right, but "actually obtainable for a specific, already-recorded competitive match" fails in practice, which is exactly the risk the ticket asked us to check for rather than assume away.

Sources: [OCAP2/OCAP GitHub](https://github.com/OCAP2/OCAP), [OCAP forum thread](https://forums.bohemia.net/forums/topic/194164-ocap-op-capture-and-playback-aarreplay/), [After Action Review 3 forum thread](https://forums.bohemia.net/forums/topic/234176-after-action-review-3-%E2%80%94-battle-replays-in-arma-3/), [tS_AARViewer GitHub](https://github.com/10Dozen/tS_AARViewer), [Electronic Sports Masters (Arma 3)](https://www.esportsmasters.org/), [Arma 3 End Game Tournament](https://arma3.com/end-game-tournament).

### Squad — evaluated, not shortlisted

Squad is UE5-based and does have a parser project, [`Codycody31/squad-replay`](https://github.com/Codycody31/squad-replay) (Rust, converts Squad UE5 `.replay` files to JSON/binary bundles), plus server-log-derived tools like [`JkSchrack/squadLogs`](https://github.com/JkSchrack/squadLogs). However: `squad-replay`'s README does not document its output schema in enough detail to confirm positions/shots/kills/objective-flag events are actually captured (only that a "Bundle" of parsed data exists), and `squadLogs` derives only session-level metrics (map, duration, average player count) from RCON logs rather than per-kill/per-objective events. Squad does have a competitive scene (Squad World Championship, run via Toornament), but no evidence was found of pro SWC matches having been captured with either tool and published as a dataset. This is a genuine wildcard worth revisiting if `squad-replay`'s schema turns out to be richer than its docs currently show, but as surveyed it doesn't clear the "actually obtainable, verified" bar.

Sources: [Codycody31/squad-replay GitHub](https://github.com/Codycody31/squad-replay), [JkSchrack/squadLogs GitHub](https://github.com/JkSchrack/squadLogs), [SWC Open League on Toornament](https://play.toornament.com/en_US/tournaments/1343458918973554688/).

### Other titles considered

- **Valorant.** The official Riot developer API's [`/val/match/v1/matches/{matchId}`](https://valapidocs.techchrism.me/endpoint/match-details) endpoint is unusually rich for an official API: kill events include `killer`/`victim`, `victimLocation`, and a `playerLocations` array (x/y + view angle for every player) at the moment of each kill, plus round results that should include spike plant/defuse (the objective event). Structurally this maps well to mission framing (5v5, attack/defend, spike objective). But two access problems keep it out of the shortlist: (1) personal Riot developer API keys are scoped to the key holder's own match history — there's no public "look up any pro match by ID" browsing endpoint, so getting a *specific* named pro match requires already knowing its match ID or going through the partner-gated [VALORANT Data Portal](https://grid.gg/get-valorant/) (same GRID program as R6's portal); (2) positions are only snapshotted at kill events, not continuously tracked like CS2's tick data. Worth a second look in #3 if a matchId can be sourced, but not verified obtainable in this survey.
- **Overwatch / Overwatch 2.** The (unofficial, reverse-engineered) Overwatch League API and community projects like [`overwatcher`](https://github.com/qiushiyan/overwatcher) expose team/player/match-level stats, and paid vendors (Data Sports Group, GameScorekeeper) cover the league — but everything found was aggregate per-match/per-season statistics, not event-level positions/shots/kill-attribution data. No evidence of a replay-file parser analogous to `awpy` or `demoparser2`. Ruled out.
- **PUBG.** The official [PUBG Developer API](https://documentation.pubg.com/en/telemetry-events.html) is genuinely strong on event granularity — telemetry JSON includes `LogPlayerPosition`, `LogPlayerKillV2` (attacker, victim, weapon, assists), damage events, etc., and there are mature wrappers (e.g. [`pubg-python`](https://pypi.org/project/pubg-python/)). But PUBG is battle-royale: there's no discrete "objective" to complete or fail beyond survival placement, and while 4-player squads exist, the "did we fulfill our mission objectives" framing has nothing concrete to bind to. Ruled out on structural fit, not data availability.
- **Insurgency: Sandstorm.** Has a built-in in-game replay system (replay IDs, viewable via the main menu / [support docs](https://support.saber.games/hc/en/insurgency-sandstorm/articles/understanding-the-replay-system-12)), and does have an objective-based (Push/Firefight) structure that maps well to mission framing narratively. No evidence found of any community parser or API that extracts structured event data (positions/shots/kills) from these in-game replays — it appears to be a watch-only replay viewer, not an exportable dataset. Ruled out for lack of a verified extraction path.

## Ranked shortlist (for human sign-off — not a decision)

| Rank | Candidate | Event-level data | Video available | Mission-framing fit | Pro match data |
|---|---|---|---|---|---|
| 1 | **CS2 / CS:GO** | Strong — positions, shots, kills, objective (bomb) state, all via `awpy`/`demoparser2` | Yes, linked from HLTV alongside the demo | Strong (teams, round objective, win/loss) | Yes, freely downloadable, no gate |
| 2 | **Rainbow Six Siege** | Partial — kills/objective events confirmed via `r6-dissect`; positions/shots not yet exposed by open tooling | Yes, esports VODs widely available | Strong (attack/defend, site objective) | Yes, official Ubisoft-published `.rec` files |
| 3 | **Arma 3 (OCAP2)** | Strong in principle, but only for missions actually recorded with OCAP/equivalent at the time | Inconsistent, depends on community | Excellent narratively, but weak competitive scene | Weak — little PvP esports, no confirmed OCAP+competitive overlap |
| 4 | **Squad** | Unverified — parser exists but schema undocumented | Unknown | Good (squads, objectives/flags) | Unverified — competitive scene exists (SWC) but no confirmed captured data |

Valorant, Overwatch, PUBG, and Insurgency: Sandstorm were evaluated and are not included in the ranked shortlist above (Valorant for unresolved pro-match-ID access, the others for weaker fit or unverified extraction paths); see write-ups above if a different tradeoff becomes relevant in #3.

## Recommendation (for #3 to confirm or override)

**CS2 is the recommended starting point for #3.** It's the only candidate where all four criteria are independently verified with concrete, named tools: `awpy`/`demoparser2` for parsing, HLTV for sourcing a specific professional match's `.dem` file *and* its VOD with no access gate, and a round/bomb-objective structure that maps directly onto "did we fulfill our mission objectives." Rainbow Six Siege is a credible second choice with a genuine edge in provenance (official Ubisoft-published pro replays) but currently loses on positions/shots granularity through open tooling — worth re-checking R6Data/Arenyze's actual field-level output before ruling it out fully. Arma 3 and Squad remain interesting but are blocked on "was this specific competitive match actually captured with a working tool," which is the exact failure mode this ticket was scoped to catch rather than assume away.

This is a recommendation, not a final decision — #3 should confirm (or revisit) the pick, including spot-checking the actual field contents of an `awpy`-parsed demo before committing.
