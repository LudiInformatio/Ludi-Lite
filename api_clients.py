"""
API Clients for Ludi Lite
Handles The-Odds-API (games, props), Claude API, and API key management.
"""

import os
import json
import requests
import streamlit as st
import anthropic
from datetime import datetime
from typing import Optional
import pytz

from team_mapping import normalize_team

# Timezone for game times (Eastern) - used by fetch_todays_games
ET = pytz.timezone('America/New_York')


def get_claude_oauth_token() -> Optional[str]:
    """Get Claude OAuth token from ~/.claude/config.json"""
    try:
        config_path = os.path.expanduser("~/.claude/config.json")
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
                return config.get('oauthToken')
    except Exception:
        pass
    return None


def get_api_key(key_name: str) -> Optional[str]:
    """
    Get API key with priority:
    1. Claude OAuth token (if key is ANTHROPIC_API_KEY)
    2. Streamlit Cloud secrets (st.secrets)
    3. Environment variables
    """
    # Priority 1: For Anthropic, try OAuth token first
    if key_name == "ANTHROPIC_API_KEY":
        oauth_token = get_claude_oauth_token()
        if oauth_token:
            return oauth_token

    # Priority 2: Streamlit Cloud secrets
    try:
        if hasattr(st, 'secrets') and key_name in st.secrets:
            return st.secrets[key_name]
    except Exception:
        pass

    # Priority 3: Environment variable
    key = os.getenv(key_name)
    if key:
        return key

    return None


def fetch_player_props(game_id: str) -> dict:
    """
    Fetch player props for a specific game from The-Odds-API.
    Includes main lines, combo props (PRA, PA, PR, AR), and double/triple-double.

    Args:
        game_id: The-Odds-API game ID

    Returns:
        Dictionary with player props by market type
    """
    api_key = get_api_key("ODDS_API_KEY")
    if not api_key or not game_id:
        return {}

    try:
        url = f"https://api.the-odds-api.com/v4/sports/basketball_nba/events/{game_id}/odds"
        # Include all main prop markets + combos + specials
        # Ludi-Bot uses: player_points, player_rebounds, player_assists, player_threes,
        # player_steals, player_blocks, player_turnovers, player_double_double, player_triple_double
        # Plus combo markets: player_points_rebounds_assists (PRA), player_points_assists (PA),
        # player_points_rebounds (PR), player_assists_rebounds (AR)
        markets = ",".join([
            "player_points",
            "player_rebounds",
            "player_assists",
            "player_threes",
            "player_steals",
            "player_blocks",
            "player_points_rebounds_assists",  # PRA combo
            "player_points_assists",           # PA combo
            "player_points_rebounds",          # PR combo
            "player_assists_rebounds",         # AR combo
            "player_double_double",            # DD
            "player_triple_double"             # TD
        ])
        params = {
            "apiKey": api_key,
            "regions": "us",
            "markets": markets,
            "oddsFormat": "american",
            "bookmakers": "fanduel,draftkings"
        }
        response = requests.get(url, params=params, timeout=15)
        if response.status_code == 200:
            data = response.json()
            props = {
                "points": [], "rebounds": [], "assists": [], "threes": [],
                "steals": [], "blocks": [],
                "pra": [], "pa": [], "pr": [], "ar": [],  # Combos
                "double_double": [], "triple_double": []  # Specials
            }

            # Market key to props dict key mapping
            market_map = {
                "player_points": "points",
                "player_rebounds": "rebounds",
                "player_assists": "assists",
                "player_threes": "threes",
                "player_steals": "steals",
                "player_blocks": "blocks",
                "player_points_rebounds_assists": "pra",
                "player_points_assists": "pa",
                "player_points_rebounds": "pr",
                "player_assists_rebounds": "ar",
                "player_double_double": "double_double",
                "player_triple_double": "triple_double"
            }

            for book in data.get("bookmakers", []):
                book_name = book.get("key", "")
                for market in book.get("markets", []):
                    market_key = market.get("key", "")
                    prop_key = market_map.get(market_key)
                    if not prop_key:
                        continue

                    for outcome in market.get("outcomes", []):
                        prop = {
                            "player": outcome.get("description", ""),
                            "line": outcome.get("point"),
                            "odds": outcome.get("price"),
                            "type": outcome.get("name"),  # Over/Under or Yes/No for DD/TD
                            "book": book_name
                        }
                        # Skip alt lines - main lines typically don't have alternates in standard markets
                        # The-Odds-API separates alt lines into different market keys
                        if prop not in props[prop_key]:
                            props[prop_key].append(prop)

            return props
    except Exception as e:
        st.warning(f"Player props fetch error: {e}")
    return {}


def format_props_context(props: dict, max_players: int = 5) -> str:
    """
    Format player props into context string for AI analysis.
    Includes main lines, combos (PRA, PA, etc.), and DD/TD.

    Args:
        props: Dictionary from fetch_player_props()
        max_players: Maximum players to include per category

    Returns:
        Formatted string with prop lines
    """
    if not props:
        return ""

    context = "\n=== PLAYER PROP LINES (The-Odds-API) ===\n"

    # Main stat categories
    main_categories = [
        ("points", "PTS"),
        ("rebounds", "REB"),
        ("assists", "AST"),
        ("threes", "3PM"),
        ("steals", "STL"),
        ("blocks", "BLK")
    ]

    # Combo categories
    combo_categories = [
        ("pra", "PTS+REB+AST"),
        ("pa", "PTS+AST"),
        ("pr", "PTS+REB"),
        ("ar", "AST+REB")
    ]

    # Special categories (Yes/No instead of Over/Under)
    special_categories = [
        ("double_double", "Double-Double"),
        ("triple_double", "Triple-Double")
    ]

    # Process main stats
    context += "\n**Main Lines:**\n"
    for category, label in main_categories:
        players_seen = set()
        lines = []
        for prop in props.get(category, []):
            player = prop.get("player", "")
            if player and player not in players_seen and prop.get("type") == "Over":
                players_seen.add(player)
                line = prop.get("line", "N/A")
                odds = prop.get("odds", "N/A")
                lines.append(f"{player}: {line} ({odds:+d})" if isinstance(odds, int) else f"{player}: {line}")

        if lines:
            context += f"  {label}: " + " | ".join(lines[:max_players]) + "\n"

    # Process combos (compact format)
    combo_lines = []
    for category, label in combo_categories:
        for prop in props.get(category, []):
            player = prop.get("player", "")
            if player and prop.get("type") == "Over":
                line = prop.get("line", "N/A")
                combo_lines.append(f"{player} {label}: {line}")
                break  # Just first player per combo for brevity

    if combo_lines:
        context += f"\n**Combos:** " + " | ".join(combo_lines[:4]) + "\n"

    # Process DD/TD (compact)
    special_lines = []
    for category, label in special_categories:
        for prop in props.get(category, []):
            player = prop.get("player", "")
            if player and prop.get("type") == "Yes":
                odds = prop.get("odds", "N/A")
                special_lines.append(f"{player} {label} ({odds:+d})" if isinstance(odds, int) else f"{player} {label}")

    if special_lines:
        context += f"**Specials:** " + " | ".join(special_lines[:3]) + "\n"

    return context


def fetch_todays_games() -> list:
    """Fetch today's NBA games from The-Odds-API"""
    api_key = get_api_key("ODDS_API_KEY")
    if not api_key:
        return []

    try:
        url = "https://api.the-odds-api.com/v4/sports/basketball_nba/odds/"
        params = {
            "apiKey": api_key,
            "regions": "us",
            "markets": "spreads,totals,h2h",  # Added h2h (moneyline)
            "oddsFormat": "american",
            "bookmakers": "fanduel,draftkings"
        }
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            games = response.json()
            # Parse into simpler format
            parsed = []
            for game in games:
                # Use proper team name normalization (handles Odds-API full names)
                away_full = game.get("away_team", "")
                home_full = game.get("home_team", "")
                away = normalize_team(away_full)
                home = normalize_team(home_full)

                # Get spread, total, and moneyline from first bookmaker
                spread = None
                total = None
                home_ml = None
                away_ml = None
                for book in game.get("bookmakers", []):
                    for market in book.get("markets", []):
                        if market["key"] == "spreads" and not spread:
                            for outcome in market["outcomes"]:
                                if outcome["name"] == home_full:
                                    spread = outcome["point"]
                        if market["key"] == "totals" and not total:
                            for outcome in market["outcomes"]:
                                if outcome["name"] == "Over":
                                    total = outcome["point"]
                        if market["key"] == "h2h" and not home_ml:
                            for outcome in market["outcomes"]:
                                if outcome["name"] == home_full:
                                    home_ml = outcome["price"]
                                elif outcome["name"] == away_full:
                                    away_ml = outcome["price"]

                # Parse time
                commence = game.get("commence_time", "")
                try:
                    dt = datetime.fromisoformat(commence.replace("Z", "+00:00"))
                    dt_et = dt.astimezone(ET)
                    time_str = dt_et.strftime("%I:%M %p")
                except Exception:
                    time_str = "TBD"

                parsed.append({
                    "id": game.get("id"),
                    "away": away,  # Now properly normalized (e.g., "LAL" not "LAK")
                    "home": home,  # Now properly normalized (e.g., "NYK" not "KNI")
                    "away_full": away_full or "Away",
                    "home_full": home_full or "Home",
                    "spread": spread,
                    "total": total,
                    "home_ml": home_ml,  # Moneyline
                    "away_ml": away_ml,  # Moneyline
                    "time": time_str
                })
            return parsed
    except Exception as e:
        st.error(f"Error fetching games: {e}")
    return []


def get_claude_analysis(prompt: str, user_input: str, model: str = "claude-sonnet-4-20250514") -> str:
    """Get analysis from Claude API"""
    api_key = get_api_key("ANTHROPIC_API_KEY")
    if not api_key:
        return "Error: ANTHROPIC_API_KEY not found."

    try:
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=model,
            max_tokens=2500,
            messages=[
                {"role": "user", "content": f"{prompt}\n\n---\n\nANALYZE:\n{user_input}"}
            ]
        )
        return response.content[0].text
    except Exception as e:
        return f"Error: {str(e)}"
