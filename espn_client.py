"""
ESPN Client for Ludi Lite
Fetches suspensions and injuries from ESPN API with SQLite caching.

No API key needed. Rate limited to 0.4s between team calls.
"""

import sqlite3
import requests
import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

DB_PATH = "ludi_lite.db"

ESPN_TEAM_IDS = {
    "ATL": 1, "BOS": 2, "NOP": 3, "CHA": 4, "CHI": 5, "CLE": 6,
    "DAL": 7, "DEN": 8, "DET": 9, "GS": 10, "HOU": 11,
    "IND": 12, "LAC": 13, "LAL": 14, "MEM": 15, "MIA": 16,
    "MIL": 17, "MIN": 18, "BKN": 19, "NYK": 20, "ORL": 21,
    "PHI": 22, "PHX": 23, "POR": 24, "SAC": 25, "SA": 26,
    "OKC": 27, "UTA": 28, "WAS": 29, "TOR": 30
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept": "application/json",
}
TIMEOUT = 10
RATE_LIMIT_SLEEP = 0.4

STATUS_MAP = {
    "Out": "OUT",
    "Questionable": "GTD",
    "Doubtful": "DOUBTFUL",
    "Day-To-Day": "GTD",
    "Probable": "PROBABLE",
}


def _get(url: str) -> dict:
    """Safe GET with timeout and error handling."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        logger.error(f"ESPN request error: {e}")
    return {}


def _get_espn_ttl() -> int:
    """Map time context mode to TTL in seconds."""
    try:
        from time_utils import get_time_context
        mode = get_time_context()["mode"]
        ttl_map = {
            "EARLY_LOOK": 14400,
            "AFTERNOON": 7200,
            "PRE_GAME": 1800,
            "LOCK_TIME": 1200,
        }
        return ttl_map.get(mode, 7200)
    except Exception:
        return 7200


def _init_db():
    """Ensure player_injuries table exists."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS player_injuries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_name TEXT NOT NULL,
            team TEXT,
            status TEXT,
            injury_type TEXT,
            source TEXT,
            description TEXT,
            snapshot_time TEXT
        )
    """)
    conn.commit()
    conn.close()


def is_cache_fresh(source: str = "espn") -> bool:
    """Check if cached data is fresh based on TTL."""
    _init_db()
    ttl = _get_espn_ttl()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT snapshot_time FROM player_injuries
        WHERE source = ?
        ORDER BY snapshot_time DESC
        LIMIT 1
    """, (source,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return False

    try:
        snapshot_time = datetime.fromisoformat(row[0])
        age = (datetime.now() - snapshot_time).total_seconds()
        return age < ttl
    except Exception:
        return False


def fetch_espn_suspensions() -> List[Dict]:
    """Fetch suspensions (type_id==17) from ESPN for all 30 teams."""
    suspensions = []

    for team_abbr, team_id in ESPN_TEAM_IDS.items():
        url = f"https://sports.core.api.espn.com/v2/sports/basketball/leagues/nba/teams/{team_id}/injuries"
        data = _get(url)
        items = data.get("items", [])

        for item in items:
            ref = item.get("$ref", "")
            if not ref:
                continue

            injury = _get(ref)
            if not injury:
                continue

            inj_type = injury.get("type", {})
            if inj_type.get("id") not in ("17", 17):
                continue

            athlete_ref = injury.get("athlete", {}).get("$ref", "")
            player_name = None
            if athlete_ref:
                athlete = _get(athlete_ref)
                player_name = athlete.get("displayName") or athlete.get("fullName")

            if not player_name:
                continue

            details = injury.get("details", {})
            description = injury.get("shortComment") or injury.get("longComment", "")[:200] or "Suspended"

            suspensions.append({
                "player_name": player_name,
                "team": team_abbr,
                "status": "OUT",
                "injury_type": "SUSPENSION",
                "source": "espn",
                "description": description,
                "snapshot_time": datetime.now().isoformat(),
            })

        time.sleep(RATE_LIMIT_SLEEP)

    return suspensions


def fetch_espn_injuries() -> List[Dict]:
    """Fetch non-suspension injuries from ESPN for all 30 teams."""
    injuries = []

    for team_abbr, team_id in ESPN_TEAM_IDS.items():
        url = f"https://sports.core.api.espn.com/v2/sports/basketball/leagues/nba/teams/{team_id}/injuries"
        data = _get(url)
        items = data.get("items", [])

        for item in items:
            ref = item.get("$ref", "")
            if not ref:
                continue

            injury = _get(ref)
            if not injury:
                continue

            inj_type = injury.get("type", {})
            if inj_type.get("id") in ("17", 17):
                continue

            espn_status = injury.get("status", "")
            our_status = STATUS_MAP.get(espn_status)
            if not our_status:
                continue

            athlete_ref = injury.get("athlete", {}).get("$ref", "")
            player_name = None
            if athlete_ref:
                athlete = _get(athlete_ref)
                player_name = athlete.get("displayName") or athlete.get("fullName")

            if not player_name:
                continue

            details = injury.get("details", {})
            description = injury.get("shortComment") or injury.get("longComment", "")[:200] or inj_type.get("name", "Injury")
            injury_type = inj_type.get("name", "") or details.get("type", "Injury")

            injuries.append({
                "player_name": player_name,
                "team": team_abbr,
                "status": our_status,
                "injury_type": injury_type,
                "source": "espn",
                "description": description,
                "snapshot_time": datetime.now().isoformat(),
            })

        time.sleep(RATE_LIMIT_SLEEP)

    return injuries


def _write_to_db(records: List[Dict], source: str):
    """Write records to player_injuries table."""
    if not records:
        return

    _init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    for rec in records:
        cursor.execute("""
            INSERT INTO player_injuries (player_name, team, status, injury_type, source, description, snapshot_time)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            rec["player_name"],
            rec.get("team", ""),
            rec["status"],
            rec.get("injury_type", ""),
            source,
            rec.get("description", ""),
            rec["snapshot_time"],
        ))

    conn.commit()
    conn.close()


def get_suspensions() -> List[Dict]:
    """Get suspensions - DB-first with ESPN fallback."""
    if is_cache_fresh("espn"):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT player_name, team, status, injury_type, description, snapshot_time
            FROM player_injuries
            WHERE source = 'espn' AND status = 'OUT' AND injury_type = 'SUSPENSION'
        """)
        rows = cursor.fetchall()
        conn.close()

        if rows:
            return [
                {
                    "player_name": r[0],
                    "team": r[1],
                    "status": r[2],
                    "injury_type": r[3],
                    "description": r[4],
                    "snapshot_time": r[5],
                }
                for r in rows
            ]

    suspensions = fetch_espn_suspensions()
    if suspensions:
        _write_to_db(suspensions, "espn")

    return suspensions


def get_injuries() -> List[Dict]:
    """Get injuries - DB-first with ESPN fallback."""
    if is_cache_fresh("espn"):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT player_name, team, status, injury_type, description, snapshot_time
            FROM player_injuries
            WHERE source = 'espn' AND status != 'OUT'
        """)
        rows = cursor.fetchall()
        conn.close()

        if rows:
            return [
                {
                    "player_name": r[0],
                    "team": r[1],
                    "status": r[2],
                    "injury_type": r[3],
                    "description": r[4],
                    "snapshot_time": r[5],
                }
                for r in rows
            ]

    injuries = fetch_espn_injuries()
    if injuries:
        _write_to_db(injuries, "espn")

    return injuries


def is_available() -> bool:
    """Check if ESPN API is reachable."""
    try:
        url = f"https://sports.core.api.espn.com/v2/sports/basketball/leagues/nba/teams/1/injuries"
        return _get(url) is not None
    except Exception:
        return False
