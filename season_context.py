"""
Season Context for 2025-26 NBA Season
This file grounds AI analysis in the CURRENT season, not training data.
Updated: February 5, 2026

Now uses LIVE data from Tank01 API with static fallbacks.
"""

CURRENT_SEASON = "2025-26"
SEASON_START_DATE = "2025-10-22"

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
    Returns formatted string with key roster moves and injuries.
    """
    try:
        from tank01_client import get_injury_list

        injuries = get_injury_list()
        key_injuries = [inj for inj in injuries if inj.get("designation") in ["Out", "Doubtful"]]

        injury_report = "\n=== CURRENT INJURY REPORT (LIVE from Tank01) ===\n"
        if key_injuries:
            for inj in key_injuries[:15]:
                injury_report += f"- {inj['name']} ({inj['team']}): {inj['designation']}"
                if inj.get('description'):
                    injury_report += f" - {inj['description']}"
                injury_report += "\n"
        else:
            injury_report += "No major injuries reported.\n"

        return injury_report

    except Exception as e:
        return f"\n(Live injury data unavailable)\n"


def get_static_roster_context() -> str:
    """
    Static roster context as fallback when API is unavailable.
    Updated: February 5, 2026 (Trade Deadline Day)
    """
    return """
=== KEY 2025-26 ROSTER CHANGES (VERIFIED) ===

TRADE DEADLINE MOVES (Feb 4-5, 2026):
- Anthony Davis: NOW ON WASHINGTON WIZARDS (from Dallas)
- Luka Doncic: NOW ON LA LAKERS
- Trae Young: NOW ON WASHINGTON WIZARDS
- James Harden: NOW ON CLEVELAND (from LA Clippers)
- Darius Garland: NOW ON LA CLIPPERS (from Cleveland)
- Nikola Vucevic: NOW ON BOSTON (from Chicago)
- Coby White: NOW ON CHARLOTTE (from Chicago)
- Ayo Dosunmu: NOW ON MINNESOTA (from Chicago)
- Deandre Ayton: NOW ON LA LAKERS

2024 OFFSEASON (STILL IN EFFECT):
- Klay Thompson: ON DALLAS (not Golden State)
- Paul George: ON PHILADELPHIA (not LA Clippers)
- DeMar DeRozan: ON SACRAMENTO
- Isaiah Hartenstein: ON OKLAHOMA CITY
- Dejounte Murray: ON NEW ORLEANS

IMPORTANT: Use THIS roster data, not your training data.
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

    return f"""
=== CURRENT SEASON: {CURRENT_SEASON} NBA SEASON ===
Today: February 5, 2026
Season Status: Regular season (started {SEASON_START_DATE})
TRADE DEADLINE: TODAY at 3:00 PM ET

{get_static_roster_context()}

{live_injuries}

DEFENSE SCHEME ASSIGNMENTS (2025-26):
{defense_list}

CONTEXT NOTES:
- Newly traded players may need 2-3 games to integrate with new team
- Check injury status before projecting minutes/usage
- Back-to-back games typically reduce production by 3-5%

IMPORTANT: If your training data conflicts with the above, USE THE ABOVE.
These are the CURRENT facts for the 2025-26 season.
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
