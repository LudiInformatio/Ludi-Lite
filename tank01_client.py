"""
Tank01 Fantasy Stats API Client for Ludi Lite
Provides live NBA roster, injury, and game data.
Source: https://rapidapi.com/tank01/api/tank01-fantasy-stats
"""

import requests
import streamlit as st
from typing import Optional, List, Dict, Any
from datetime import datetime

# API Configuration
TANK01_HOST = "tank01-fantasy-stats.p.rapidapi.com"
TANK01_BASE_URL = f"https://{TANK01_HOST}"

# Tank01 uses non-standard abbreviations for 5 teams
# Our system uses standard NBA abbreviations (PHX, GSW, SAS, NOP, NYK)
# Tank01 expects: PHO, GS, SA, NO, NY
STANDARD_TO_TANK01 = {
    "PHX": "PHO",
    "GSW": "GS",
    "SAS": "SA",
    "NOP": "NO",
    "NYK": "NY",
}
TANK01_TO_STANDARD = {v: k for k, v in STANDARD_TO_TANK01.items()}


def _to_tank01_abbr(team_abbr: str) -> str:
    """Convert standard NBA abbreviation to Tank01 format."""
    return STANDARD_TO_TANK01.get(team_abbr.upper(), team_abbr.upper())


def _to_standard_abbr(tank01_abbr: str) -> str:
    """Convert Tank01 abbreviation to standard NBA format."""
    return TANK01_TO_STANDARD.get(tank01_abbr.upper(), tank01_abbr.upper())


def _get_api_key() -> Optional[str]:
    """Get Tank01 API key from Streamlit secrets or environment"""
    try:
        return st.secrets.get("TANK01_KEY")
    except Exception:
        import os
        return os.getenv("TANK01_KEY")


def _make_request(endpoint: str, params: dict = None) -> Optional[dict]:
    """Make authenticated request to Tank01 API"""
    api_key = _get_api_key()
    if not api_key:
        return None

    headers = {
        "x-rapidapi-host": TANK01_HOST,
        "x-rapidapi-key": api_key
    }

    try:
        response = requests.get(
            f"{TANK01_BASE_URL}/{endpoint}",
            headers=headers,
            params=params or {},
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.warning(f"Tank01 API error: {e}")
        return None


@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_team_roster(team_abbr: str, include_stats: bool = False) -> List[Dict[str, Any]]:
    """
    Get current roster for a team.

    Args:
        team_abbr: Team abbreviation (e.g., 'LAL', 'BOS')
        include_stats: Whether to include player season averages

    Returns:
        List of player dictionaries with name, position, injury status, etc.
    """
    tank01_abbr = _to_tank01_abbr(team_abbr)
    params = {"teamAbv": tank01_abbr}
    if include_stats:
        params["statsToGet"] = "averages"

    data = _make_request("getNBATeamRoster", params)
    if not data or "body" not in data:
        return []

    roster = data["body"].get("roster", [])
    return [
        {
            "name": p.get("longName", p.get("espnName", "Unknown")),
            "position": p.get("pos", ""),
            "team": p.get("team", team_abbr),
            "injury": p.get("injury", {}),
            "player_id": p.get("playerID", ""),
            "jersey": p.get("jerseyNum", ""),
            "stats": p.get("stats", {}) if include_stats else {}
        }
        for p in roster
    ]


@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_injury_list() -> List[Dict[str, Any]]:
    """
    DEPRECATED: This endpoint returns INCOMPLETE data (playerID only, no team/name).

    The getNBAInjuryList endpoint is BROKEN - returns only playerID without team/name fields.
    All injury data should be retrieved via get_team_roster() instead, which includes
    embedded injury fields with complete player information.

    DO NOT USE THIS FUNCTION. Use get_team_roster() for injury data.

    Original endpoint: getNBAInjuryList
    Working alternative: getNBATeamRoster (per team, has injury data)

    Returns:
        Empty list (function disabled)
    """
    # DISABLED - Returns incomplete data
    # data = _make_request("getNBAInjuryList")
    # if not data or "body" not in data:
    #     return []
    #
    # injuries = data["body"]
    # return [
    #     {
    #         "name": inj.get("longName", inj.get("playerName", "Unknown")),
    #         "team": inj.get("team", ""),
    #         "designation": inj.get("designation", ""),
    #         "description": inj.get("injDesc", inj.get("description", "")),
    #         "return_date": inj.get("injReturnDate", "")
    #     }
    #     for inj in injuries
    # ]

    print("⚠️ WARNING: get_injury_list() is DEPRECATED. Use get_team_roster() for injury data.")
    return []


@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_all_teams_with_rosters() -> Dict[str, List[str]]:
    """
    Get all NBA teams with their current rosters.

    Returns:
        Dictionary mapping team abbreviation to list of player names
    """
    data = _make_request("getNBATeams", {"rosters": "true"})
    if not data or "body" not in data:
        return {}

    teams = {}
    for team in data["body"]:
        abbr = _to_standard_abbr(team.get("teamAbv", ""))
        roster = team.get("Roster", [])
        # Roster items can be strings (player IDs) or dicts (player objects)
        names = []
        for p in roster:
            if isinstance(p, str):
                names.append(p)
            elif isinstance(p, dict):
                names.append(p.get("longName", p.get("espnName", "")))
        teams[abbr] = names

    return teams


@st.cache_data(ttl=60)  # Cache for 1 minute (games change more frequently)
def get_todays_games() -> List[Dict[str, Any]]:
    """
    Get today's NBA games with details.

    Returns:
        List of game dictionaries
    """
    today = datetime.now().strftime("%Y%m%d")
    data = _make_request("getNBAGamesForDate", {"gameDate": today})
    if not data or "body" not in data:
        return []

    return data["body"]


@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_depth_chart(team_abbr: str) -> Dict[str, List[str]]:
    """
    Get team depth chart (starting lineup and backups by position).

    Args:
        team_abbr: Team abbreviation

    Returns:
        Dictionary mapping position to list of players
    """
    data = _make_request("getNBADepthCharts", {"teamAbv": _to_tank01_abbr(team_abbr)})
    if not data or "body" not in data:
        return {}

    return data["body"]


def find_player_team(player_name: str, search_teams: list = None) -> Optional[str]:
    """
    Find which team a player is currently on by searching live rosters.
    Uses get_team_roster() (per-team endpoint with full player names).

    Args:
        player_name: Player name (partial match supported)
        search_teams: Optional list of team abbreviations to search.
                      If None, searches all 30 teams (cached, so fast after first call).

    Returns:
        Standard team abbreviation or None if not found
    """
    player_lower = player_name.lower().strip()

    # Default: search all 30 NBA teams
    if search_teams is None:
        search_teams = [
            "ATL", "BOS", "BKN", "CHA", "CHI", "CLE", "DAL", "DEN", "DET",
            "GSW", "HOU", "IND", "LAC", "LAL", "MEM", "MIA", "MIL", "MIN",
            "NOP", "NYK", "OKC", "ORL", "PHI", "PHX", "POR", "SAC", "SAS",
            "TOR", "UTA", "WAS"
        ]

    for team_abbr in search_teams:
        roster = get_team_roster(team_abbr)
        if not roster:
            continue
        for player in roster:
            if player_lower in player.get("name", "").lower():
                return team_abbr

    return None


def get_team_injuries(team_abbr: str) -> List[Dict[str, Any]]:
    """
    Get injuries for a specific team from roster data.

    Args:
        team_abbr: Team abbreviation

    Returns:
        List of injuries for that team
    """
    roster = get_team_roster(team_abbr)
    injuries = []

    for player in roster:
        injury = player.get("injury", {})
        designation = injury.get("designation")

        if designation:  # Only include players with injury status
            injuries.append({
                "name": player.get("name", "Unknown"),
                "team": _to_standard_abbr(team_abbr),
                "designation": designation,
                "description": injury.get("description", "")
            })

    return injuries


def format_roster_context(team_abbr: str) -> str:
    """
    Format team roster as context string for AI prompts.

    Args:
        team_abbr: Team abbreviation

    Returns:
        Formatted roster string
    """
    roster = get_team_roster(team_abbr)
    if not roster:
        return f"{team_abbr}: Roster unavailable"

    injuries = get_team_injuries(team_abbr)
    injury_names = {inj["name"].lower() for inj in injuries}

    active = []
    out = []

    for player in roster:
        name = player["name"]
        pos = player["position"]
        inj = player.get("injury", {})
        designation = inj.get("designation", "")

        if name.lower() in injury_names or designation:
            status = designation or "OUT"
            out.append(f"{name} ({pos}) - {status}")
        else:
            active.append(f"{name} ({pos})")

    result = f"\n{team_abbr} ROSTER:\n"
    result += "Active: " + ", ".join(active[:8]) + ("..." if len(active) > 8 else "") + "\n"
    if out:
        result += "Injured/Out: " + ", ".join(out) + "\n"

    return result


def format_game_context(home_team: str, away_team: str) -> str:
    """
    Format full game context including both rosters and injuries.

    Args:
        home_team: Home team abbreviation
        away_team: Away team abbreviation

    Returns:
        Formatted game context string for AI prompts
    """
    context = "\n=== LIVE ROSTER DATA (from Tank01 API) ===\n"
    context += format_roster_context(away_team)
    context += format_roster_context(home_team)

    # Add key injuries summary
    away_injuries = get_team_injuries(away_team)
    home_injuries = get_team_injuries(home_team)

    if away_injuries or home_injuries:
        context += "\nKEY INJURIES TO MONITOR:\n"
        for inj in away_injuries[:3]:
            context += f"- {inj['name']} ({away_team}): {inj['description'] or inj['designation']}\n"
        for inj in home_injuries[:3]:
            context += f"- {inj['name']} ({home_team}): {inj['description'] or inj['designation']}\n"

    return context


@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_box_score(game_id: str) -> Optional[Dict[str, Any]]:
    """
    Get box score for a specific game.

    Args:
        game_id: Tank01 game ID

    Returns:
        Box score dictionary with player stats, or None
    """
    data = _make_request("getNBABoxScore", {"gameID": game_id})
    if not data or "body" not in data:
        return None
    return data["body"]


@st.cache_data(ttl=600)  # Cache for 10 minutes (historical data changes less)
def get_player_recent_games(player_name: str, num_games: int = 5) -> List[Dict[str, Any]]:
    """
    Get a player's recent game stats using box score lookups.

    Args:
        player_name: Player name (partial match supported)
        num_games: Number of recent games to fetch (default 5)

    Returns:
        List of game stat dictionaries with pts, reb, ast, etc.
    """
    # First find the player's team
    team = find_player_team(player_name)
    if not team:
        return []

    # Get recent games for this team
    recent_games = []

    # Check if we can get games from getNBAGamesForDate for past dates
    # For now, return empty - this would need historical date iteration
    # In production, you'd iterate back through dates until you have num_games

    return recent_games


@st.cache_data(ttl=300)
def get_team_recent_record(team_abbr: str, num_games: int = 5) -> Dict[str, Any]:
    """
    Get a team's recent win/loss record.

    Args:
        team_abbr: Team abbreviation
        num_games: Number of recent games to check

    Returns:
        Dictionary with wins, losses, and streak info
    """
    # This would require iterating through recent dates
    # Placeholder for now - in production would use getNBAGamesForDate
    return {
        "team": team_abbr,
        "record": "N/A",
        "streak": "N/A"
    }


@st.cache_data(ttl=3600)  # 1 hour — team stats don't change mid-game
def get_all_team_stats() -> Dict[str, Dict]:
    """
    Fetch team-level stats from Tank01.
    Returns: {"BOS": {"ppg": 112.3, "oppg": 105.1}, ...}
    """
    data = _make_request("getNBATeams", {
        "teamStats": "true",
        "statsToGet": "averages"
    })
    if not data or "body" not in data:
        return {}

    teams = {}
    for team in data["body"]:
        abbr = _to_standard_abbr(team.get("teamAbv", ""))
        if not abbr:
            continue
        try:
            teams[abbr] = {
                "ppg": float(team.get("ppg", 0) or 0),
                "oppg": float(team.get("oppg", 0) or 0),
            }
        except (ValueError, TypeError):
            continue
    return teams


def format_player_context(player_name: str, team_abbr: str = None) -> str:
    """
    Format player-specific context for prop analysis.

    Args:
        player_name: Player name
        team_abbr: Optional team abbreviation (skips lookup if provided)

    Returns:
        Formatted player context string
    """
    team = team_abbr or find_player_team(player_name)
    if not team:
        return f"\nPlayer '{player_name}' not found in current rosters.\n"

    roster = get_team_roster(team, include_stats=True)
    injuries = get_team_injuries(team)

    # Find the player
    player = None
    for p in roster:
        if player_name.lower() in p["name"].lower():
            player = p
            break

    if not player:
        return f"\nPlayer '{player_name}' roster data unavailable.\n"

    context = f"\n=== {player['name'].upper()} - LIVE DATA ===\n"
    context += f"Team: {team}\n"
    context += f"Position: {player['position']}\n"

    # Check if injured
    inj = player.get("injury", {})
    if inj.get("designation"):
        context += f"INJURY STATUS: {inj['designation']} - {inj.get('description', '')}\n"

    # Add stats if available
    stats = player.get("stats", {})
    if stats:
        context += "Season Averages: "
        stat_parts = []
        if "pts" in stats:
            stat_parts.append(f"{stats['pts']} PPG")
        if "reb" in stats:
            stat_parts.append(f"{stats['reb']} RPG")
        if "ast" in stats:
            stat_parts.append(f"{stats['ast']} APG")
        context += ", ".join(stat_parts) + "\n"

    # Teammates who are out (usage vacuum opportunity)
    out_teammates = [inj["name"] for inj in injuries if inj["designation"] in ["Out", "Doubtful", "Suspended"]]
    if out_teammates:
        context += f"Teammates OUT: {', '.join(out_teammates)} (potential usage boost)\n"

    return context
