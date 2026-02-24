"""
Database module for Ludi Lite
SQLite storage for analysis history.
"""

import sqlite3

DB_PATH = "ludi_lite.db"


def init_db():
    """Initialize SQLite database for tracking"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            game_date TEXT,
            matchup TEXT,
            spread REAL,
            total REAL,
            freestyle_analysis TEXT,
            methodology_analysis TEXT,
            user_notes TEXT,
            query_type TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            query TEXT,
            freestyle_response TEXT,
            methodology_response TEXT
        )
    """)

    c.execute("""
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

    c.execute("""
        CREATE TABLE IF NOT EXISTS canonical_teams (
            standard_abbr TEXT PRIMARY KEY,
            bdl_abbr TEXT,
            tank01_abbr TEXT,
            espn_id INTEGER,
            full_name TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS canonical_players (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            name_normalized TEXT NOT NULL,
            name_crosswalk TEXT NOT NULL,
            bdl_id INTEGER,
            tank01_id TEXT,
            tank01_aliases TEXT DEFAULT '[]',
            sportsdata_id TEXT,
            dk_player_id TEXT,
            fd_player_id TEXT,
            current_team TEXT,
            is_active INTEGER DEFAULT 1,
            synced_at TEXT
        )
    """)

    c.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_canonical_players_bdl ON canonical_players(bdl_id) WHERE bdl_id IS NOT NULL
    """)
    c.execute("""
        CREATE INDEX IF NOT EXISTS idx_canonical_players_norm ON canonical_players(name_normalized)
    """)
    c.execute("""
        CREATE INDEX IF NOT EXISTS idx_canonical_players_crosswalk ON canonical_players(name_crosswalk)
    """)

    conn.commit()
    conn.close()


def save_analysis(query: str, freestyle: str, methodology: str):
    """Save analysis to database"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO chat_history (query, freestyle_response, methodology_response)
        VALUES (?, ?, ?)
    """, (query, freestyle, methodology))
    conn.commit()
    conn.close()
