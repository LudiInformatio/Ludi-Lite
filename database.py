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
