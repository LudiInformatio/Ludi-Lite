"""
Canonical Player/Team ID Resolution for Ludi-Lite
Maps BDL IDs ↔ Tank01 IDs ↔ SportsDataIO IDs with name normalization.
"""

import json
import os
import re
import sqlite3
import time
import unicodedata
from datetime import datetime
from typing import Optional, Dict, List

import streamlit as st

DB_PATH = "ludi_lite.db"
CACHE_TTL = 86400

TEAM_MAPPING = [
    ("ATL", "ATL", "ATL", 1,  "Atlanta Hawks"),
    ("BOS", "BOS", "BOS", 2,  "Boston Celtics"),
    ("NOP", "NO",  "NO",  3,  "New Orleans Pelicans"),
    ("CHA", "CHA", "CHA", 4,  "Charlotte Hornets"),
    ("CHI", "CHI", "CHI", 5,  "Chicago Bulls"),
    ("CLE", "CLE", "CLE", 6,  "Cleveland Cavaliers"),
    ("DAL", "DAL", "DAL", 7,  "Dallas Mavericks"),
    ("DEN", "DEN", "DEN", 8,  "Denver Nuggets"),
    ("DET", "DET", "DET", 9,  "Detroit Pistons"),
    ("GSW", "GS",  "GS",  10, "Golden State Warriors"),
    ("HOU", "HOU", "HOU", 11, "Houston Rockets"),
    ("IND", "IND", "IND", 12, "Indiana Pacers"),
    ("LAC", "LAC", "LAC", 13, "LA Clippers"),
    ("LAL", "LAL", "LAL", 14, "Los Angeles Lakers"),
    ("MEM", "MEM", "MEM", 15, "Memphis Grizzlies"),
    ("MIA", "MIA", "MIA", 16, "Miami Heat"),
    ("MIL", "MIL", "MIL", 17, "Milwaukee Bucks"),
    ("MIN", "MIN", "MIN", 18, "Minnesota Timberwolves"),
    ("BKN", "BKN", "BKN", 19, "Brooklyn Nets"),
    ("NYK", "NY",  "NY",  20, "New York Knicks"),
    ("ORL", "ORL", "ORL", 21, "Orlando Magic"),
    ("PHI", "PHI", "PHI", 22, "Philadelphia 76ers"),
    ("PHX", "PHO", "PHO", 23, "Phoenix Suns"),
    ("POR", "POR", "POR", 24, "Portland Trail Blazers"),
    ("SAC", "SAC", "SAC", 25, "Sacramento Kings"),
    ("SAS", "SA",  "SA",  26, "San Antonio Spurs"),
    ("OKC", "OKC", "OKC", 27, "Oklahoma City Thunder"),
    ("UTA", "UTA", "UTA", 28, "Utah Jazz"),
    ("WAS", "WAS", "WAS", 29, "Washington Wizards"),
    ("TOR", "TOR", "TOR", 30, "Toronto Raptors"),
]

STANDARD_TO_BDL = {
    "ATL": "ATL", "BOS": "BOS", "BKN": "BKN", "CHA": "CHA",
    "CHI": "CHI", "CLE": "CLE", "DAL": "DAL", "DEN": "DEN",
    "DET": "DET", "GSW": "GS", "HOU": "HOU", "IND": "IND",
    "LAC": "LAC", "LAL": "LAL", "MEM": "MEM", "MIA": "MIA",
    "MIL": "MIL", "MIN": "MIN", "NOP": "NO", "NYK": "NY",
    "OKC": "OKC", "ORL": "ORL", "PHI": "PHI", "PHX": "PHO",
    "POR": "POR", "SAC": "SAC", "SAS": "SA", "TOR": "TOR",
    "UTA": "UTA", "WAS": "WAS",
}

BDL_TO_STANDARD = {v: k for k, v in STANDARD_TO_BDL.items()}


def normalize_name(name: str) -> str:
    """
    NFKD + lowercase + strip suffixes. Preserves hyphens/apostrophes.
    Ported from Ludi-Bot's PlayerIDResolver.normalize_name()
    """
    if not name:
        return ""

    name = unicodedata.normalize('NFKD', name)
    name = name.encode('ASCII', 'ignore').decode('ASCII')
    name = name.lower().strip()

    for suffix in [' jr.', ' jr', ' sr.', ' sr', ' iii', ' ii', ' iv', ' v']:
        name = name.replace(suffix, '')

    name = ' '.join(name.split())
    return name


def normalize_for_crosswalk(name: str) -> str:
    """
    NFD + strip apostrophes/hyphens/periods + lowercase.
    More aggressive: "De'Aaron Fox" → "deaaron fox", "Karl-Anthony" → "karlanthony"
    Ported from build_sportsdata_crosswalk.py _normalize_name()
    """
    if not name:
        return ""
    nfd = unicodedata.normalize("NFD", name)
    ascii_name = nfd.encode("ascii", "ignore").decode("ascii")
    clean = re.sub(r"['\-\.]", "", ascii_name).lower().strip()
    clean = re.sub(r"\s+", " ", clean)
    return clean


def _get_sportsdata_api_key() -> Optional[str]:
    """Get SportsDataIO API key from Streamlit secrets or environment."""
    try:
        if hasattr(st, 'secrets') and "SPORTSDATA_API_KEY" in st.secrets:
            return st.secrets["SPORTSDATA_API_KEY"]
    except Exception:
        pass
    return os.getenv("SPORTSDATA_API_KEY")


def _get_bdl_api_key() -> Optional[str]:
    """Get BDL API key from Streamlit secrets or environment."""
    try:
        if hasattr(st, 'secrets') and "BALLDONTLIE_KEY" in st.secrets:
            return st.secrets["BALLDONTLIE_KEY"]
    except Exception:
        pass
    return os.getenv("BALLDONTLIE_KEY")


def _get_tank01_api_key() -> Optional[str]:
    """Get Tank01 API key from Streamlit secrets or environment."""
    try:
        if hasattr(st, 'secrets') and "TANK01_KEY" in st.secrets:
            return st.secrets["TANK01_KEY"]
    except Exception:
        pass
    return os.getenv("TANK01_KEY")


class PlayerResolver:
    """
    Single source of truth for player ID resolution.
    Handles BDL ↔ Tank01 ↔ SportsDataIO ID mapping with dual normalization.
    """

    def __init__(self):
        self._cache: Dict[str, dict] = {}
        self._ensure_teams_seeded()

    def _ensure_teams_seeded(self):
        """Seed canonical_teams table if empty."""
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM canonical_teams")
        if c.fetchone()[0] == 0:
            for standard, bdl, tank01, espn_id, full_name in TEAM_MAPPING:
                c.execute("""
                    INSERT OR REPLACE INTO canonical_teams
                    (standard_abbr, bdl_abbr, tank01_abbr, espn_id, full_name)
                    VALUES (?, ?, ?, ?, ?)
                """, (standard, bdl, tank01, espn_id, full_name))
            conn.commit()
        conn.close()

    def _get_connection(self) -> sqlite3.Connection:
        return sqlite3.connect(DB_PATH)

    def get_player(self, name: str) -> Optional[dict]:
        """Get full player row by normalized name lookup."""
        if name in self._cache:
            return self._cache[name]

        norm = normalize_name(name)
        crosswalk = normalize_for_crosswalk(name)

        conn = self._get_connection()
        c = conn.cursor()

        c.execute("""
            SELECT id, full_name, name_normalized, name_crosswalk, bdl_id,
                   tank01_id, tank01_aliases, sportsdata_id, dk_player_id,
                   fd_player_id, current_team, is_active, synced_at
            FROM canonical_players
            WHERE name_crosswalk = ? OR name_normalized = ?
            ORDER BY
                CASE WHEN name_crosswalk = ? THEN 0 ELSE 1 END,
                CASE WHEN tank01_id IS NOT NULL THEN 0 ELSE 1 END
            LIMIT 1
        """, (crosswalk, norm, crosswalk))

        row = c.fetchone()
        conn.close()

        if row:
            player = {
                "id": row[0],
                "full_name": row[1],
                "name_normalized": row[2],
                "name_crosswalk": row[3],
                "bdl_id": row[4],
                "tank01_id": row[5],
                "tank01_aliases": json.loads(row[6]) if row[6] else [],
                "sportsdata_id": row[7],
                "dk_player_id": row[8],
                "fd_player_id": row[9],
                "current_team": row[10],
                "is_active": row[11],
                "synced_at": row[12],
            }
            self._cache[name] = player
            return player

        return None

    def get_bdl_id(self, name: str) -> Optional[int]:
        """Get BDL player ID by name."""
        player = self.get_player(name)
        return player["bdl_id"] if player else None

    def get_tank01_id(self, name: str) -> Optional[str]:
        """Get Tank01 player ID by name."""
        player = self.get_player(name)
        return player["tank01_id"] if player else None

    def to_standard_abbr(self, abbr: str) -> str:
        """Convert any abbreviation format to standard (GS → GSW, NO → NOP)."""
        return BDL_TO_STANDARD.get(abbr.upper(), abbr.upper())

    def to_bdl_abbr(self, standard: str) -> str:
        """Convert standard abbreviation to BDL format (GSW → GS, NOP → NO)."""
        return STANDARD_TO_BDL.get(standard.upper(), standard.upper())

    def get_espn_id(self, abbr: str) -> Optional[int]:
        """Get ESPN team ID from standard abbreviation."""
        conn = self._get_connection()
        c = conn.cursor()
        c.execute("SELECT espn_id FROM canonical_teams WHERE standard_abbr = ?", (abbr.upper(),))
        row = c.fetchone()
        conn.close()
        return row[0] if row else None

    def sync(self, force: bool = False) -> int:
        """
        Build/refresh canonical_players from 3 sources.
        Returns count of matched rows.
        """
        conn = self._get_connection()
        c = conn.cursor()

        if not force:
            c.execute("SELECT synced_at FROM canonical_players ORDER BY synced_at DESC LIMIT 1")
            row = c.fetchone()
            if row and row[0]:
                last_sync = datetime.fromisoformat(row[0])
                if (datetime.now() - last_sync).total_seconds() < CACHE_TTL:
                    conn.close()
                    return 0

        sd_key = _get_sportsdata_api_key()
        bdl_key = _get_bdl_api_key()
        tank01_key = _get_tank01_api_key()

        sd_players = {}
        if sd_key:
            sd_players = self._fetch_sportsdata_players(sd_key)

        bdl_players = {}
        if bdl_key:
            bdl_players = self._fetch_bdl_players(bdl_key)

        tank01_players = {}
        if tank01_key:
            tank01_players = self._fetch_tank01_rosters(tank01_key)

        matched = 0
        now = datetime.now().isoformat()

        all_names = set(sd_players.keys()) | set(bdl_players.keys())
        for crosswalk_key in all_names:
            sd = sd_players.get(crosswalk_key, {})
            bdl = bdl_players.get(crosswalk_key, {})
            tank01 = tank01_players.get(crosswalk_key, {})

            full_name = sd.get("full_name") or bdl.get("full_name") or ""
            if not full_name:
                continue

            name_norm = normalize_name(full_name)
            name_cross = crosswalk_key

            bdl_id = bdl.get("bdl_id")
            tank01_id = tank01.get("tank01_id")
            if tank01_id and tank01.get("tank01_aliases"):
                aliases = json.dumps(tank01["tank01_aliases"])
            else:
                aliases = "[]"

            c.execute("""
                INSERT OR REPLACE INTO canonical_players
                (full_name, name_normalized, name_crosswalk, bdl_id, tank01_id,
                 tank01_aliases, sportsdata_id, dk_player_id, fd_player_id,
                 current_team, is_active, synced_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
            """, (
                full_name, name_norm, name_cross,
                bdl_id, tank01_id, aliases,
                sd.get("sportsdata_id"), sd.get("dk_player_id"), sd.get("fd_player_id"),
                sd.get("team") or bdl.get("team"),
                now
            ))
            matched += 1

        conn.commit()
        conn.close()
        self._cache.clear()
        return matched

    def _fetch_sportsdata_players(self, api_key: str) -> Dict[str, dict]:
        """Fetch players from SportsDataIO /Players endpoint."""
        import requests

        url = "https://api.sportsdata.io/api/nba/fantasy/json/Players"
        headers = {"Ocp-Apim-Subscription-Key": api_key}

        cache_path = "cache/sportsdata/Players.json"
        if os.path.exists(cache_path):
            age_hours = (time.time() - os.path.getmtime(cache_path)) / 3600
            if age_hours < 1:
                with open(cache_path) as f:
                    data = json.load(f)
            else:
                try:
                    resp = requests.get(url, headers=headers, timeout=15)
                    resp.raise_for_status()
                    data = resp.json()
                    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
                    with open(cache_path, "w") as f:
                        json.dump(data, f)
                except Exception:
                    with open(cache_path) as f:
                        data = json.load(f)
        else:
            try:
                resp = requests.get(url, headers=headers, timeout=15)
                resp.raise_for_status()
                data = resp.json()
                os.makedirs(os.path.dirname(cache_path), exist_ok=True)
                with open(cache_path, "w") as f:
                    json.dump(data, f)
            except Exception:
                data = []

        players = {}
        for p in data:
            first = p.get("FirstName", "") or ""
            last = p.get("LastName", "") or ""
            full = f"{first} {last}".strip()
            if not full:
                continue
            key = normalize_for_crosswalk(full)
            players[key] = {
                "full_name": full,
                "sportsdata_id": p.get("PlayerID"),
                "dk_player_id": p.get("DraftKingsPlayerID"),
                "fd_player_id": p.get("FanDuelPlayerID"),
                "team": self.to_standard_abbr(p.get("Team", "")),
            }
        return players

    def _fetch_bdl_players(self, api_key: str) -> Dict[str, dict]:
        """Fetch all players from BDL API."""
        import requests

        url = "https://api.balldontlie.io/nba/v1/players"
        headers = {"Authorization": api_key}

        players = {}
        cursor = None
        while True:
            params = {"per_page": 100}
            if cursor:
                params["cursor"] = cursor

            try:
                resp = requests.get(url, headers=headers, params=params, timeout=10)
                resp.raise_for_status()
                data = resp.json()
            except Exception:
                break

            for p in data.get("data", []):
                full = f"{p.get('first_name', '')} {p.get('last_name', '')}".strip()
                if not full:
                    continue
                key = normalize_for_crosswalk(full)
                players[key] = {
                    "full_name": full,
                    "bdl_id": p.get("id"),
                    "team": p.get("team", {}).get("abbreviation", ""),
                }

            meta = data.get("meta", {})
            cursor = meta.get("next_cursor")
            if not cursor:
                break

        return players

    def _fetch_tank01_rosters(self, api_key: str) -> Dict[str, dict]:
        """Fetch all 30 team rosters from Tank01."""
        import requests

        headers = {"x-rapidapi-host": "tank01-fantasy-stats.p.rapidapi.com",
                   "x-rapidapi-key": api_key}

        players = {}
        for standard, tank01 in STANDARD_TO_BDL.items():
            try:
                url = "https://tank01-fantasy-stats.p.rapidapi.com/getNBATeamRoster"
                resp = requests.get(url, headers=headers,
                                    params={"teamAbv": tank01}, timeout=10)
                resp.raise_for_status()
                data = resp.json()
            except Exception:
                continue

            for p in data.get("body", {}).get("roster", []):
                full = p.get("longName", p.get("espnName", ""))
                if not full:
                    continue
                key = normalize_for_crosswalk(full)
                if key in players:
                    existing = players[key]["tank01_aliases"]
                    existing.append(p.get("playerID"))
                    players[key]["tank01_aliases"] = existing
                else:
                    players[key] = {
                        "full_name": full,
                        "tank01_id": p.get("playerID"),
                        "tank01_aliases": [p.get("playerID")],
                    }

        return players


_resolver: Optional[PlayerResolver] = None


def get_resolver() -> PlayerResolver:
    """Get singleton resolver instance."""
    global _resolver
    if _resolver is None:
        _resolver = PlayerResolver()
    return _resolver


def get_bdl_id(name: str) -> Optional[int]:
    """Module-level convenience: get BDL ID by name."""
    return get_resolver().get_bdl_id(name)


def get_tank01_id(name: str) -> Optional[str]:
    """Module-level convenience: get Tank01 ID by name."""
    return get_resolver().get_tank01_id(name)


def to_standard_abbr(abbr: str) -> str:
    """Module-level convenience: convert to standard abbreviation."""
    return get_resolver().to_standard_abbr(abbr)


def to_bdl_abbr(standard: str) -> str:
    """Module-level convenience: convert to BDL abbreviation."""
    return get_resolver().to_bdl_abbr(standard)


def get_espn_id(abbr: str) -> Optional[int]:
    """Module-level convenience: get ESPN team ID."""
    return get_resolver().get_espn_id(abbr)


def sync_canonical(force: bool = False) -> int:
    """Module-level convenience: sync canonical players."""
    return get_resolver().sync(force=force)
