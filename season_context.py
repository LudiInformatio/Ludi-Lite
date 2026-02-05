"""
Season Context for 2025-26 NBA Season
This file grounds AI analysis in the CURRENT season, not training data.
Updated: February 5, 2026

Now uses LIVE data from Tank01 API with static fallbacks.
"""

CURRENT_SEASON = "2025-26"
SEASON_START_DATE = "2025-10-22"

# Known suspensions/removals not reflected in Tank01 rosters
# Tank01 completely removes suspended players from roster data
# Update this list as suspensions are announced/lifted
KNOWN_SUSPENSIONS = [
    {"name": "Paul George", "team": "PHI", "status": "SUSPENDED", "description": "NBA suspension - not on active roster"},
]

# Defense scheme assignments for 2025-26
DEFENSE_SCHEMES_2025_26 = {
    "PAINT_PACK": ["OKC", "BOS", "DET", "MIN", "SAS", "ORL"],
    "BLITZ": ["HOU", "TOR", "MIA", "PHX"],
    "PERIMETER": ["GSW", "DAL", "NYK"],
    "SWITCH_HEAVY": ["CLE", "LAC", "MEM"],
    "FUNNEL": ["WAS", "ATL", "CHI", "UTA", "SAC"],
    "NEUTRAL": ["LAL", "DEN", "MIL", "BKN", "IND", "POR", "CHA", "NOP"]
}

# Offensive classifications for 2025-26
OFFENSE_SCHEMES_2025_26 = {
    "THREE_POINT_CENTRIC": ["BOS", "GSW", "IND", "ATL", "UTA"],
    "MOTION_OFFENSE": ["DEN", "MIA", "SAS"],
    "PACE_PUSH": ["SAC", "IND", "ATL", "CHA"],
    "PAINT_ATTACK": ["MIL", "NOP", "CLE", "ORL"],
    "ISOLATION_HEAVY": ["PHX", "DAL", "LAL", "BKN"],
    "BALANCED": ["OKC", "NYK", "MIN", "LAC", "MEM", "HOU", "TOR", "POR", "DET", "WAS", "CHI"]
}


def get_defense_scheme(team_abbr: str) -> str:
    """Get a team's defensive scheme for 2025-26"""
    for scheme, teams in DEFENSE_SCHEMES_2025_26.items():
        if team_abbr.upper() in teams:
            return scheme
    return "NEUTRAL"


def get_offense_scheme(team_abbr: str) -> str:
    """Get a team's offensive classification for 2025-26"""
    for scheme, teams in OFFENSE_SCHEMES_2025_26.items():
        if team_abbr.upper() in teams:
            return scheme
    return "BALANCED"


def get_live_roster_context() -> str:
    """
    Get live roster context from Tank01 API.
    Uses ROSTER endpoint per team (not the broken league-wide injury list).

    Why roster endpoint: getNBAInjuryList only returns playerID (no team/name).
    getNBATeamRoster includes injury data per player WITH name and team.
    """
    try:
        from tank01_client import get_todays_games, get_team_roster

        # Get tonight's teams from today's schedule
        games = get_todays_games()
        if not games:
            return "\n=== INJURY REPORT ===\nNo games scheduled today.\n"

        # Collect teams playing tonight
        teams_tonight = set()
        for game in games:
            teams_tonight.add(game.get("hTeam", game.get("home", "")))
            teams_tonight.add(game.get("aTeam", game.get("away", "")))
        teams_tonight.discard("")

        not_playing = []
        game_time_decisions = []
        teams_checked = 0

        # Add known suspensions for tonight's teams (Tank01 removes these from rosters)
        for susp in KNOWN_SUSPENSIONS:
            if susp["team"] in teams_tonight:
                not_playing.append(f"- {susp['name']} ({susp['team']}): {susp['status']} - {susp['description']}")

        for team in sorted(teams_tonight):
            roster = get_team_roster(team)
            if not roster:
                continue
            teams_checked += 1

            for player in roster:
                injury = player.get("injury", {})
                designation = (injury.get("designation") or "").upper()
                if not designation:
                    continue

                desc = injury.get("description", "")
                # Extract short description (first sentence or 80 chars)
                short_desc = desc.split(".")[0][:80] if desc else ""
                player_line = f"- {player['name']} ({team}): {injury.get('designation', '')}"
                if short_desc:
                    player_line += f" - {short_desc}"

                # NOT PLAYING: Out, Suspended, Doubtful, Inactive
                if any(s in designation for s in ["OUT", "SUSPENDED", "DOUBTFUL", "INACTIVE"]):
                    not_playing.append(player_line)
                # GAME-TIME DECISION: Day-To-Day, Questionable, Probable
                elif any(s in designation for s in ["DAY-TO-DAY", "QUESTIONABLE", "PROBABLE", "DAY TO DAY"]):
                    game_time_decisions.append(player_line)

        injury_report = "\n=== TONIGHT'S INJURY REPORT (Tank01 Rosters - Live) ===\n"
        injury_report += f"[{teams_checked} teams checked | {len(not_playing)} out | {len(game_time_decisions)} GTD]\n\n"

        if not_playing:
            injury_report += "**NOT PLAYING (DO NOT ANALYZE THESE PLAYERS):**\n"
            injury_report += "\n".join(not_playing[:25]) + "\n"

        if game_time_decisions:
            injury_report += "\n**GAME-TIME DECISIONS (verify before analysis):**\n"
            injury_report += "\n".join(game_time_decisions[:15]) + "\n"

        if not not_playing and not game_time_decisions:
            injury_report += "No injuries reported for tonight's teams.\n"

        return injury_report

    except Exception as e:
        import traceback
        return f"\n=== INJURY REPORT ===\n⚠️ Tank01 API Error: {str(e)}\nCheck TANK01_KEY in Streamlit secrets.\n"


def get_static_roster_context() -> str:
    """
    Static roster context as fallback when API is unavailable.
    Only includes 2025-26 season moves (offseason + in-season trades).
    """
    return """
=== 2025-26 SEASON ROSTER CHANGES ===

OFFSEASON MOVES (Summer 2025):
- Klay Thompson → DALLAS (from Golden State)
- Paul George → PHILADELPHIA (from LA Clippers) — currently SUSPENDED
- DeMar DeRozan → SACRAMENTO (from Chicago)
- Isaiah Hartenstein → OKLAHOMA CITY (from New York)
- Dejounte Murray → NEW ORLEANS (from Atlanta)

TRADE DEADLINE (Feb 4-5, 2026):
- Luka Doncic → LA LAKERS (from Dallas)
- Deandre Ayton → LA LAKERS (from Portland)
- Anthony Davis → WASHINGTON (from Dallas)
- Trae Young → WASHINGTON (from Atlanta)
- James Harden → CLEVELAND (from LA Clippers)
- Darius Garland → LA CLIPPERS (from Cleveland)
- Nikola Vucevic → BOSTON (from Chicago)
- Kristaps Porzingis → GOLDEN STATE (from Boston)
- Coby White → CHARLOTTE (from Chicago)
- Ayo Dosunmu → MINNESOTA (from Chicago)
- Anfernee Simons → CHICAGO (from Portland)
- Jimmy Butler → GOLDEN STATE (from Miami) — OUT with torn ACL

NOTE: Tank01 API rosters reflect these changes in real-time.
Use LIVE roster data above when available, this list as fallback only.
"""


def get_full_season_context() -> str:
    """
    Return complete season context for AI prompts.
    Combines live data (when available) with static context.
    """
    defense_list = "\n".join([
        f"  - {scheme}: {', '.join(teams)}"
        for scheme, teams in DEFENSE_SCHEMES_2025_26.items()
    ])

    # Try to get live injury data
    try:
        live_injuries = get_live_roster_context()
    except Exception:
        live_injuries = ""

    # Dynamic date
    from datetime import datetime
    import pytz
    today_str = datetime.now(pytz.timezone('America/New_York')).strftime('%B %d, %Y')

    return f"""
=== CURRENT SEASON: {CURRENT_SEASON} NBA SEASON ===
Today: {today_str}
Season Status: Regular season (started {SEASON_START_DATE})
Trade Deadline: PASSED (Feb 5, 2026 at 3:00 PM ET)

{get_static_roster_context()}

{live_injuries}

DEFENSE SCHEME ASSIGNMENTS (2025-26):
{defense_list}

CONTEXT NOTES:
- This is the 2025-26 NBA season. Do NOT reference prior seasons' rosters.
- Newly traded players may need 2-3 games to integrate with new team
- Check injury status before projecting minutes/usage
- Back-to-back games typically reduce production by 3-5%
- Suspended players are NOT on Tank01 rosters - check KNOWN_SUSPENSIONS above

CRITICAL: Only reference 2025-26 season data.
- Do NOT mention where players were last season as "news"
- Treat offseason moves as established facts, not breaking changes
- If your training data conflicts with the above, USE THE ABOVE.
"""


def get_game_specific_context(home_team: str, away_team: str) -> str:
    """
    Get context specific to a game matchup.
    Includes rosters, injuries, and scheme matchups.
    """
    try:
        from tank01_client import format_game_context
        live_context = format_game_context(home_team, away_team)
    except Exception:
        live_context = ""

    home_def = get_defense_scheme(home_team)
    away_def = get_defense_scheme(away_team)
    home_off = get_offense_scheme(home_team)
    away_off = get_offense_scheme(away_team)

    scheme_context = f"""
SCHEME MATCHUP:
- {away_team} Offense ({away_off}) vs {home_team} Defense ({home_def})
- {home_team} Offense ({home_off}) vs {away_team} Defense ({away_def})
"""

    return live_context + scheme_context


def get_player_specific_context(player_name: str) -> str:
    """
    Get context specific to a player for prop analysis.
    """
    try:
        from tank01_client import format_player_context
        return format_player_context(player_name)
    except Exception:
        return f"\nPlayer context for '{player_name}' unavailable.\n"
