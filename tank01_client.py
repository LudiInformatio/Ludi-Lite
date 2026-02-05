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
    params = {"teamAbv": team_abbr.upper()}
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
    Get current NBA injury list.

    Returns:
        List of injury dictionaries with player name, team, status, description
    """
    data = _make_request("getNBAInjuryList")
    if not data or "body" not in data:
        return []

    injuries = data["body"]
    return [
        {
            "name": inj.get("longName", inj.get("playerName", "Unknown")),
            "team": inj.get("team", ""),
            "designation": inj.get("designation", ""),
            "description": inj.get("injDesc", inj.get("description", "")),
            "return_date": inj.get("injReturnDate", "")
        }
        for inj in injuries
    ]


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
        abbr = team.get("teamAbv", "")
        roster = team.get("Roster", [])
        teams[abbr] = [p.get("longName", p.get("espnName", "")) for p in roster]

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
    data = _make_request("getNBADepthCharts", {"teamAbv": team_abbr.upper()})
    if not data or "body" not in data:
        return {}

    return data["body"]


def find_player_team(player_name: str) -> Optional[str]:
    """
    Find which team a player is currently on.

    Args:
        player_name: Player name (partial match supported)

    Returns:
        Team abbreviation or None if not found
    """
    teams = get_all_teams_with_rosters()
    player_lower = player_name.lower()

    for team_abbr, roster in teams.items():
        for player in roster:
            if player_lower in player.lower():
                return team_abbr

    return None


def get_team_injuries(team_abbr: str) -> List[Dict[str, Any]]:
    """
    Get injuries for a specific team.

    Args:
        team_abbr: Team abbreviation

    Returns:
        List of injuries for that team
    """
    all_injuries = get_injury_list()
    return [inj for inj in all_injuries if inj["team"].upper() == team_abbr.upper()]


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


def format_player_context(player_name: str) -> str:
    """
    Format player-specific context for prop analysis.

    Args:
        player_name: Player name

    Returns:
        Formatted player context string
    """
    team = find_player_team(player_name)
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
    out_teammates = [inj["name"] for inj in injuries if inj["designation"] in ["Out", "Doubtful"]]
    if out_teammates:
        context += f"Teammates OUT: {', '.join(out_teammates)} (potential usage boost)\n"

    return context
