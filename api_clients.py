"""
API Clients for Ludi Lite
Handles The-Odds-API (games, props), Claude API, and API key management.
With 3-tier fallback chain: The-Odds-API → BallDontLie (BDL) → Tank01
"""

import os
import json
import requests
import streamlit as st
import anthropic
from datetime import datetime
from typing import Optional, Dict, List, Any
import pytz

from team_mapping import normalize_team
import bdl_client
import tank01_client

# Timezone for game times (Eastern) - used by fetch_todays_games
ET = pytz.timezone('America/New_York')


def get_line_movement_context(games: List[Dict]) -> str:
    """
    Compute line movement from session_state.
    Caches first-seen spread/total with timestamp.
    On re-fetch, computes delta and formats: "Opened -5.0 → Now -4.5 (↑ 0.5)"
    
    Args:
        games: List of current game dicts with spread/total
        
    Returns:
        Formatted string with line movement info for all games
    """
    if not games:
        return ""
    
    if "line_history" not in st.session_state:
        st.session_state.line_history = {}
    
    movement_lines = []
    
    for game in games:
        game_id = game.get("id") or f"{game.get('away')}-{game.get('home')}"
        current_spread = game.get("spread")
        current_total = game.get("total")
        
        if game_id in st.session_state.line_history:
            prev = st.session_state.line_history[game_id]
            prev_spread = prev.get("spread")
            prev_total = prev.get("total")
            prev_time = prev.get("timestamp", "")
            
            if current_spread is not None and prev_spread is not None:
                spread_delta = round(current_spread - prev_spread, 1)
                if spread_delta != 0:
                    direction = "↑" if spread_delta > 0 else "↓"
                    movement_lines.append(
                        f"{game.get('away')} @ {game.get('home')}: "
                        f"Spread opened {prev_spread:+.1f} → Now {current_spread:+.1f} ({direction} {abs(spread_delta):.1f})"
                    )
            
            if current_total is not None and prev_total is not None:
                total_delta = round(current_total - prev_total, 1)
                if total_delta != 0:
                    direction = "↑" if total_delta > 0 else "↓"
                    movement_lines.append(
                        f"{game.get('away')} @ {game.get('home')}: "
                        f"Total opened {prev_total:.1f} → Now {current_total:.1f} ({direction} {abs(total_delta):.1f})"
                    )
        
        st.session_state.line_history[game_id] = {
            "spread": current_spread,
            "total": current_total,
            "timestamp": datetime.now(ET).strftime("%I:%M %p")
        }
    
    if movement_lines:
        return f"\n=== LINE MOVEMENT ===\n" + "\n".join(movement_lines[:5]) + "\n"
    return ""


def _parse_odds_api_games(games: List[Dict]) -> List[Dict]:
    """Parse The-Odds-API response into normalized game dicts."""
    parsed = []
    for game in games:
        away_full = game.get("away_team", "")
        home_full = game.get("home_team", "")
        away = normalize_team(away_full)
        home = normalize_team(home_full)

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

        commence = game.get("commence_time", "")
        try:
            dt = datetime.fromisoformat(commence.replace("Z", "+00:00"))
            dt_et = dt.astimezone(ET)
            time_str = dt_et.strftime("%I:%M %p")
        except Exception:
            time_str = "TBD"

        parsed.append({
            "id": game.get("id"),
            "away": away,
            "home": home,
            "away_full": away_full or "Away",
            "home_full": home_full or "Home",
            "spread": spread,
            "total": total,
            "home_ml": home_ml,
            "away_ml": away_ml,
            "time": time_str,
            "commence_time": commence
        })

    parsed.sort(key=lambda g: g.get('commence_time', '9999-12-31T23:59:59Z'))
    return parsed


def _parse_bdl_odds(bdl_odds: List[Dict]) -> List[Dict]:
    """Parse BDL odds response into normalized game dicts."""
    parsed = []
    for odd in bdl_odds:
        game = odd.get("game", {})
        home_team = game.get("home_team", {})
        away_team = game.get("away_team", {})
        
        home_full = home_team.get("full_name", "")
        away_full = away_team.get("full_name", "")
        home = home_team.get("abbreviation", "")
        away = away_team.get("abbreviation", "")
        
        if not home or not away:
            continue

        spread = None
        total = None
        home_ml = None
        away_ml = None
        
        bookmaker = odd.get("bookmaker", {})
        for market in bookmaker.get("markets", []):
            if market.get("key") == "spread":
                for outcome in market.get("outcomes", []):
                    if outcome.get("name") == home_full:
                        spread = outcome.get("point")
            elif market.get("key") == "total":
                for outcome in market.get("outcomes", []):
                    if outcome.get("name") == "Over":
                        total = outcome.get("point")
            elif market.get("key") == "h2h":
                for outcome in market.get("outcomes", []):
                    if outcome.get("name") == home_full:
                        home_ml = outcome.get("price")
                    elif outcome.get("name") == away_full:
                        away_ml = outcome.get("price")

        game_time = game.get("datetime", "")
        try:
            dt = datetime.fromisoformat(game_time.replace("Z", "+00:00"))
            dt_et = dt.astimezone(ET)
            time_str = dt_et.strftime("%I:%M %p")
        except Exception:
            time_str = "TBD"

        parsed.append({
            "id": f"bdl_{game.get('id')}",
            "away": away,
            "home": home,
            "away_full": away_full or "Away",
            "home_full": home_full or "Home",
            "spread": spread,
            "total": total,
            "home_ml": home_ml,
            "away_ml": away_ml,
            "time": time_str,
            "commence_time": game_time,
            "bdl_game_id": game.get("id")
        })

    parsed.sort(key=lambda g: g.get('commence_time', '9999-12-31T23:59:59Z'))
    return parsed


def _parse_tank01_games(tank01_games: List[Dict]) -> List[Dict]:
    """Parse Tank01 games into normalized game dicts."""
    parsed = []
    for game in tank01_games:
        home_abbr = tank01_client._to_standard_abbr(game.get("homeTeamAbv", ""))
        away_abbr = tank01_client._to_standard_abbr(game.get("awayTeamAbv", ""))
        
        game_time = game.get("startTime", "")
        try:
            dt = datetime.fromisoformat(game_time.replace("Z", "+00:00"))
            dt_et = dt.astimezone(ET)
            time_str = dt_et.strftime("%I:%M %p")
        except Exception:
            time_str = "TBD"

        parsed.append({
            "id": f"tank01_{game.get('gameID', '')}",
            "away": away_abbr,
            "home": home_abbr,
            "away_full": away_abbr,
            "home_full": home_abbr,
            "spread": None,
            "total": None,
            "home_ml": None,
            "away_ml": None,
            "time": time_str,
            "commence_time": game_time,
            "tank01_game_id": game.get("gameID")
        })

    parsed.sort(key=lambda g: g.get('commence_time', '9999-12-31T23:59:59Z'))
    return parsed


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


@st.cache_data(ttl=300)
def fetch_player_props(game_id: str) -> dict:
    """
    Fetch player props for a specific game with 3-tier fallback:
    1. The-Odds-API (primary)
    2. BallDontLie (BDL) get_player_props()
    3. Tank01 fetch_betting_odds()
    
    Returns normalized props dict: {points: [], rebounds: [], assists: [], ...}
    """
    api_key = get_api_key("ODDS_API_KEY")
    
    # Tier 1: The-Odds-API
    if api_key and game_id:
        try:
            url = f"https://api.the-odds-api.com/v4/sports/basketball_nba/events/{game_id}/odds"
            markets = ",".join([
                "player_points", "player_rebounds", "player_assists", "player_threes",
                "player_steals", "player_blocks", "player_points_rebounds_assists",
                "player_points_assists", "player_points_rebounds", "player_assists_rebounds",
                "player_double_double", "player_triple_double"
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
                props = _parse_odds_api_props(data)
                if props and any(props.values()):
                    return props
            elif response.status_code in (401, 429):
                st.warning("The-Odds-API exhausted (401/429). Trying BDL...")
            else:
                st.warning(f"The-Odds-API error: {response.status_code}")
        except Exception as e:
            st.warning(f"The-Odds-API props error: {e}")
    
    # Tier 2: BallDontLie (BDL)
    # Need to map Odds-API game_id to BDL game_id
    if bdl_client.is_available() and game_id:
        try:
            # First, get games for today to find the matching BDL game
            from datetime import date
            today = date.today().isoformat()
            games = bdl_client.get_games_for_date(today)
            
            # Find the matching game by date/teams
            bdl_game_id = _find_bdl_game_id(games, game_id)
            
            if bdl_game_id:
                bdl_props = bdl_client.get_player_props(bdl_game_id)
                if bdl_props:
                    props = _parse_bdl_props(bdl_props)
                    if props and any(props.values()):
                        return props
        except Exception as e:
            st.warning(f"BDL props error: {e}")
    
    # Tier 3: Tank01
    try:
        # Need to map Odds-API game_id to Tank01 game_id
        tank01_game_id = _find_tank01_game_id(game_id)
        
        if tank01_game_id:
            tank01_props = tank01_client.fetch_betting_odds(tank01_game_id)
            if tank01_props and any(tank01_props.values()):
                return tank01_props
    except Exception as e:
        st.warning(f"Tank01 props error: {e}")
    
    return {}


def _find_bdl_game_id(bdl_games: List[Dict], odds_game_id: str) -> Optional[int]:
    """Find BDL game ID by matching games list from Odds-API."""
    # Get games from Odds-API to match teams
    odds_games = fetch_todays_games()
    target_game = None
    for g in odds_games:
        if g.get("id") == odds_game_id:
            target_game = g
            break
    
    if not target_game:
        return None
    
    home = target_game.get("home")
    away = target_game.get("away")
    
    # Find matching BDL game by date + teams
    for bdl_game in bdl_games:
        home_team = bdl_game.get("home_team", {})
        away_team = bdl_game.get("away_team", {})
        
        bdl_home = home_team.get("abbreviation", "")
        bdl_away = away_team.get("abbreviation", "")
        
        if bdl_home == home and bdl_away == away:
            return bdl_game.get("id")
    
    return None


def _find_tank01_game_id(odds_game_id: str) -> Optional[str]:
    """Find Tank01 game ID from current games list."""
    odds_games = fetch_todays_games()
    target_game = None
    for g in odds_games:
        if g.get("id") == odds_game_id:
            target_game = g
            break
    
    if not target_game:
        return None
    
    return target_game.get("tank01_game_id")


def _parse_odds_api_props(data: Dict) -> dict:
    """Parse The-Odds-API props response."""
    props = {
        "points": [], "rebounds": [], "assists": [], "threes": [],
        "steals": [], "blocks": [],
        "pra": [], "pa": [], "pr": [], "ar": [],
        "double_double": [], "triple_double": []
    }

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
                    "type": outcome.get("name"),
                    "book": book_name
                }
                if prop not in props[prop_key]:
                    props[prop_key].append(prop)

    return props


def _parse_bdl_props(bdl_props: List[Dict]) -> dict:
    """Parse BDL player props into normalized format."""
    props = {
        "points": [], "rebounds": [], "assists": [], "threes": [],
        "steals": [], "blocks": [],
        "pra": [], "pa": [], "pr": [], "ar": [],
        "double_double": [], "triple_double": []
    }
    
    stat_key_map = {
        "points": "points",
        "rebounds": "rebounds", 
        "assists": "assists",
        "three_pointers": "threes",
        "steals": "steals",
        "blocks": "blocks"
    }
    
    for prop in bdl_props:
        player = prop.get("player", {})
        player_name = f"{player.get('first_name', '')} {player.get('last_name', '')}".strip()
        
        stat_type = prop.get("stat_type", "").lower()
        prop_key = stat_key_map.get(stat_type)
        
        if not prop_key:
            continue
        
        line = prop.get("line", 0)
        over_odds = prop.get("odds", {}).get("over", {}).get("price")
        under_odds = prop.get("odds", {}).get("under", {}).get("price")
        
        if over_odds:
            props[prop_key].append({
                "player": player_name,
                "line": line,
                "odds": over_odds,
                "type": "Over",
                "book": "bdl"
            })
        
        if under_odds:
            props[prop_key].append({
                "player": player_name,
                "line": line,
                "odds": under_odds,
                "type": "Under",
                "book": "bdl"
            })
    
    return props


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


@st.cache_data(ttl=300)
def fetch_todays_games() -> list:
    """
    Fetch today's NBA games with 3-tier fallback chain:
    1. The-Odds-API (primary)
    2. BallDontLie (BDL) get_odds()
    3. Tank01 get_todays_games()
    
    All outputs normalized to same dict format:
    {id, away, home, spread, total, time, commence_time, away_ml, home_ml, away_full, home_full}
    """
    api_key = get_api_key("ODDS_API_KEY")
    
    # Tier 1: The-Odds-API
    if api_key:
        try:
            url = "https://api.the-odds-api.com/v4/sports/basketball_nba/odds/"
            params = {
                "apiKey": api_key,
                "regions": "us",
                "markets": "spreads,totals,h2h",
                "oddsFormat": "american",
                "bookmakers": "fanduel,draftkings"
            }
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                games = response.json()
                parsed = _parse_odds_api_games(games)
                if parsed:
                    return parsed
            elif response.status_code in (401, 429):
                st.warning("The-Odds-API exhausted (401/429). Trying BDL...")
            else:
                st.warning(f"The-Odds-API error: {response.status_code}")
        except Exception as e:
            st.warning(f"The-Odds-API error: {e}")
    
    # Tier 2: BallDontLie (BDL)
    if bdl_client.is_available():
        try:
            from datetime import date
            today = date.today().isoformat()
            bdl_odds = bdl_client.get_odds(today)
            if bdl_odds:
                parsed = _parse_bdl_odds(bdl_odds)
                if parsed:
                    return parsed
        except Exception as e:
            st.warning(f"BDL error: {e}")
    
    # Tier 3: Tank01
    try:
        tank01_games = tank01_client.get_todays_games()
        if tank01_games:
            return _parse_tank01_games(tank01_games)
    except Exception as e:
        st.warning(f"Tank01 error: {e}")
    
    return []


def get_claude_analysis(prompt: str, user_input: str, model: str = "claude-sonnet-4-20250514", temperature: float = 0.3) -> str:
    """
    Get analysis from Claude API

    Args:
        prompt: System prompt with context
        user_input: User query to analyze
        model: Claude model to use
        temperature: Controls randomness (0.1=deterministic, 0.3=balanced, 0.5=creative)
                     Recommended: Freestyle=0.3, Methodology/SAVAGE=0.1, Player Spotlight=0.2
    """
    api_key = get_api_key("ANTHROPIC_API_KEY")
    if not api_key:
        return "Error: ANTHROPIC_API_KEY not found."

    try:
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=model,
            max_tokens=2500,
            temperature=temperature,
            messages=[
                {"role": "user", "content": f"{prompt}\n\n---\n\nANALYZE:\n{user_input}"}
            ]
        )
        return response.content[0].text
    except Exception as e:
        return f"Error: {str(e)}"
