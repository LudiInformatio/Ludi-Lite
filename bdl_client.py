"""
Ball Don't Lie API Client for Ludi Lite
GOAT tier ($39.99/mo) — 600 req/min
Docs: https://docs.balldontlie.io/

Ported from Ludi-Bot, adapted for Streamlit with @st.cache_data decorators.
"""

import os
import time
import logging
import requests
import streamlit as st
from typing import Optional, Dict, List, Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# BDLClient class
# ---------------------------------------------------------------------------
class BDLClient:
    """
    Ball Don't Lie API Client

    Tier: GOAT ($39.99/mo)
    Rate Limit: 600 requests/minute
    Docs: https://docs.balldontlie.io/
    """

    BASE_URL_V1 = "https://api.balldontlie.io/nba/v1"
    BASE_URL_V2 = "https://api.balldontlie.io/nba/v2"

    def __init__(self, api_key: str = None):
        self.api_key = api_key or self._get_api_key()
        if not self.api_key:
            logger.warning("BALLDONTLIE_KEY not found in environment variables.")

        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": self.api_key or "",
            "Content-Type": "application/json",
        })

        self.last_request_time = 0
        self.min_interval = 0.11

    def _get_api_key(self) -> Optional[str]:
        """Get API key from Streamlit secrets or environment."""
        try:
            if hasattr(st, 'secrets') and "BALLDONTLIE_KEY" in st.secrets:
                return st.secrets["BALLDONTLIE_KEY"]
        except Exception:
            pass
        return os.getenv("BALLDONTLIE_KEY")

    def _wait_for_rate_limit(self):
        """Enforce rate limits between calls."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self.last_request_time = time.time()

    def _get(self, url: str, params: Dict = None) -> Dict:
        """Single-page GET with error handling and rate limiting."""
        self._wait_for_rate_limit()
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                logger.error("BDL Rate Limit Exceeded (429).")
            elif e.response.status_code == 401:
                logger.error("BDL Unauthorized (401). Check API Key.")
            else:
                logger.error(f"BDL HTTP Error: {e}")
            return {}
        except requests.exceptions.RequestException as e:
            logger.error(f"BDL Connection Error: {e}")
            return {}

    def _get_all_pages(self, url: str, params: Dict = None) -> List[Dict]:
        """Paginated GET — follows cursor until exhausted."""
        params = dict(params or {})
        all_data: List[Dict] = []
        while True:
            resp = self._get(url, params)
            data = resp.get("data")
            if data is None:
                break
            if isinstance(data, list):
                all_data.extend(data)
            else:
                all_data.append(data)

            meta = resp.get("meta", {})
            next_cursor = meta.get("next_cursor")
            if not next_cursor:
                break
            params["cursor"] = next_cursor
        return all_data

    def get_all_players(self, search: str = None, page: int = 1, per_page: int = 100) -> Dict:
        """Fetch players with optional search."""
        params: Dict[str, Any] = {"per_page": per_page}
        if search:
            params["search"] = search
        if page > 1:
            params["cursor"] = page
        return self._get(f"{self.BASE_URL_V1}/players", params)

    def get_player_by_id(self, player_id: int) -> Dict:
        """Fetch single player details by ID."""
        data = self._get(f"{self.BASE_URL_V1}/players/{player_id}")
        return data.get("data", {}) if data else {}

    def get_all_teams(self) -> List[Dict]:
        """Fetch all NBA teams."""
        data = self._get(f"{self.BASE_URL_V1}/teams")
        return data.get("data", []) if data else []

    def get_team_by_id(self, team_id: int) -> Dict:
        """Fetch team details by ID."""
        data = self._get(f"{self.BASE_URL_V1}/teams/{team_id}")
        return data.get("data", {}) if data else {}

    def get_games(self, date: str = None, season: int = None,
                  team_ids: List[int] = None, per_page: int = 100) -> Dict:
        """Fetch games based on filters. Returns raw response dict."""
        params: Dict[str, Any] = {"per_page": per_page}
        if date:
            params["dates[]"] = date
        if season:
            params["seasons[]"] = season
        if team_ids:
            params["team_ids[]"] = team_ids
        return self._get(f"{self.BASE_URL_V1}/games", params)

    def get_game_by_id(self, game_id: int) -> Dict:
        """Fetch single game details."""
        data = self._get(f"{self.BASE_URL_V1}/games/{game_id}")
        return data.get("data", {}) if data else {}

    def get_games_for_date(self, date: str) -> List[Dict]:
        """
        Get games for a specific date.
        
        Args:
            date: Date in YYYY-MM-DD format
            
        Returns:
            List of game dictionaries
        """
        if not self.api_key:
            return []
        
        data = self.get_games(date=date)
        return data.get("data", []) if data else []

    def get_stats(self, game_ids: List[int] = None,
                  player_ids: List[int] = None,
                  season: int = None, date: str = None) -> Dict:
        """Fetch box score stats."""
        params: Dict[str, Any] = {"per_page": 100}
        if game_ids:
            params["game_ids[]"] = game_ids
        if player_ids:
            params["player_ids[]"] = player_ids
        if season:
            params["seasons[]"] = season
        if date:
            params["dates[]"] = date
        return self._get(f"{self.BASE_URL_V1}/stats", params)

    @st.cache_data(ttl=86400)
    def get_season_averages(_self, player_ids: List[int] = None,
                            season: int = 2025,
                            category: str = "general",
                            season_type: str = "regular") -> List[Dict]:
        """
        Fetch season averages.
        TTL: 24 hours (86400s)
        
        Categories: general, advanced, scoring, usage, per_36, per_48,
                    opponent, defense
        season_type: regular, playoffs
        """
        params: Dict[str, Any] = {"season": season, "type": season_type}
        if player_ids:
            params["player_ids[]"] = player_ids

        data = _self._get(f"{_self.BASE_URL_V1}/season_averages/{category}", params)
        return data.get("data", []) if data else []

    def get_team_season_averages(self, team_ids: List[int] = None,
                                  season: int = 2025,
                                  category: str = "general") -> List[Dict]:
        """Fetch team season averages."""
        params: Dict[str, Any] = {"season": season}
        if team_ids:
            params["team_ids[]"] = team_ids

        data = self._get(f"{self.BASE_URL_V1}/team_season_averages/{category}", params)
        return data.get("data", []) if data else []

    def get_stats_for_game(self, game_id: int) -> List[Dict]:
        """Helper to get all stats for a specific game."""
        data = self.get_stats(game_ids=[game_id])
        return data.get("data", [])

    @st.cache_data(ttl=3600)
    def get_recent_game_logs(_self, player_id: int, last_n: int = 10) -> List[Dict]:
        """
        Fetch recent game logs for a player.
        TTL: 1 hour (3600s)
        
        Args:
            player_id: BDL player ID
            last_n: Number of recent games to fetch (default 10)
            
        Returns:
            List of game logs with date, opponent, PTS, REB, AST, 3PM, MIN
        """
        if not player_id:
            return []
        
        data = _self.get_stats(player_ids=[player_id])
        games = data.get("data", [])
        if not games:
            return []
        
        logs = []
        for game in games[:last_n]:
            team = game.get("team", {})
            game_info = game.get("game", {})
            
            log_entry = {
                "date": game_info.get("date", "")[:10] if game_info.get("date") else "",
                "opponent": game.get("opponent_team", {}).get("abbreviation", ""),
                "pts": game.get("pts", 0),
                "reb": game.get("reb", 0),
                "ast": game.get("ast", 0),
                "three_pm": game.get("fg3m", 0),
                "min": game.get("min", 0),
                "game_id": game_info.get("id"),
                "result": game.get("team", {}).get("score", 0),
                "opp_score": game.get("opponent_team", {}).get("score", 0)
            }
            logs.append(log_entry)
        
        return logs

    @st.cache_data(ttl=900)
    def get_active_injuries(_self) -> List[Dict]:
        """
        Fetch current injury list.
        TTL: 15 minutes (900s)
        """
        data = _self._get(f"{_self.BASE_URL_V1}/player_injuries")
        return data.get("data", []) if data else []

    def get_box_scores(self, date: str = None, live: bool = False) -> List[Dict]:
        """Fetch box scores."""
        if live:
            url = f"{self.BASE_URL_V1}/box_scores/live"
            params = {}
        else:
            url = f"{self.BASE_URL_V1}/box_scores"
            params = {"date": date} if date else {}

        data = self._get(url, params)
        return data.get("data", []) if data else []

    @st.cache_data(ttl=300)
    def get_player_props(_self, game_id: int) -> List[Dict]:
        """
        Fetch player props from BDL v2 Odds API.
        TTL: 5 minutes (300s)
        """
        if not _self.api_key:
            return []

        _self._wait_for_rate_limit()
        try:
            url = f"{_self.BASE_URL_V2}/odds/player_props"
            response = _self.session.get(url, params={"game_id": game_id}, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data.get("data", [])
        except Exception as e:
            logger.error(f"BDL Props Error: {e}")
            return []

    @st.cache_data(ttl=600)
    def get_odds(_self, date: str = None) -> List[Dict]:
        """
        Fetch game odds from BDL v2.
        TTL: 10 minutes (600s)
        """
        params: Dict[str, Any] = {}
        if date:
            params["dates[]"] = date

        if not _self.api_key:
            return []

        _self._wait_for_rate_limit()
        try:
            url = f"{_self.BASE_URL_V2}/odds"
            response = _self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data.get("data", [])
        except Exception as e:
            logger.error(f"BDL Odds Error: {e}")
            return []

    def get_advanced_stats(self, player_ids: List[int] = None,
                           game_ids: List[int] = None,
                           season: int = None) -> List[Dict]:
        """Fetch advanced stats from BDL v2."""
        params: Dict[str, Any] = {"per_page": 100}
        if player_ids:
            params["player_ids[]"] = player_ids
        if game_ids:
            params["game_ids[]"] = game_ids
        if season:
            params["seasons[]"] = season

        return self._get_all_pages(f"{self.BASE_URL_V2}/stats/advanced", params)

    def search_player(self, name: str) -> List[Dict]:
        """Search for a player by name string."""
        data = self.get_all_players(search=name)
        return data.get("data", [])

    def map_player_id(self, name: str) -> Optional[int]:
        """Resolve player name to BDL ID."""
        candidates = self.search_player(name)
        for p in candidates:
            full = f"{p['first_name']} {p['last_name']}"
            if full.lower() == name.lower():
                return p["id"]
        return None

    def check_api_status(self) -> bool:
        """Simple health check of the API connection."""
        try:
            teams = self.get_all_teams()
            return len(teams) > 0
        except Exception:
            return False


# ---------------------------------------------------------------------------
# Module-level singleton + convenience functions
# ---------------------------------------------------------------------------
_client: Optional[BDLClient] = None


def _get_client() -> BDLClient:
    """Lazy singleton for module-level functions."""
    global _client
    if _client is None:
        _client = BDLClient()
    return _client


def is_available() -> bool:
    """Check if BDL API key is configured."""
    return bool(_get_client().api_key)


def get_games_for_date(date: str) -> List[Dict]:
    """Get games for a specific date."""
    return _get_client().get_games_for_date(date=date)


def get_odds(date: str = None) -> List[Dict]:
    """Fetch game odds from BDL v2."""
    return _get_client().get_odds(date=date)


def get_player_props(game_id: int) -> List[Dict]:
    """Fetch player props from BDL v2."""
    return _get_client().get_player_props(game_id)


def get_injuries() -> List[Dict]:
    """Fetch current injury list."""
    return _get_client().get_active_injuries()


def get_box_scores(date: str = None, live: bool = False) -> List[Dict]:
    """Fetch box scores."""
    return _get_client().get_box_scores(date=date, live=live)


def get_advanced_stats(player_ids: List[int] = None,
                      game_ids: List[int] = None,
                      season: int = None) -> List[Dict]:
    """Fetch advanced stats."""
    return _get_client().get_advanced_stats(
        player_ids=player_ids, game_ids=game_ids, season=season
    )


def get_season_averages(player_ids: List[int] = None,
                        season: int = 2025,
                        category: str = "general",
                        season_type: str = "regular") -> List[Dict]:
    """Fetch season averages."""
    return _get_client().get_season_averages(
        player_ids=player_ids, season=season,
        category=category, season_type=season_type
    )


def get_team_season_averages(team_ids: List[int] = None,
                             season: int = 2025,
                             category: str = "general") -> List[Dict]:
    """Fetch team season averages."""
    return _get_client().get_team_season_averages(
        team_ids=team_ids, season=season, category=category
    )


def get_player_stats(game_ids: List[int] = None,
                     player_ids: List[int] = None,
                     season: int = None, date: str = None) -> Dict:
    """Fetch player stats."""
    return _get_client().get_stats(
        game_ids=game_ids, player_ids=player_ids,
        season=season, date=date
    )


def get_recent_game_logs(player_id: int, last_n: int = 10) -> List[Dict]:
    """Fetch recent game logs for a player."""
    return _get_client().get_recent_game_logs(player_id=player_id, last_n=last_n)
