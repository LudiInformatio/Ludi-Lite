# Data Modeling — Ludi-Lite

**Purpose:** SQLite schema design, caching patterns, and database patterns

---

## Our 3 Tables

| Table | Purpose | When to Use |
|-------|---------|-------------|
| `analyses` | Store completed player analyses | Cache expensive Perplexity calls |
| `chat_history` | Conversation history | Multi-turn chats |
| `player_injuries` | Injury/suspension snapshots | DB-first caching for ESPN data |

---

## `snapshot_time` Pattern

Every sync table needs a `snapshot_time` (or `synced_at`) column for staleness detection.

```sql
CREATE TABLE IF NOT EXISTS player_injuries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_name TEXT NOT NULL,
    team TEXT,
    status TEXT,
    injury_type TEXT,
    source TEXT,
    description TEXT,
    snapshot_time TEXT
);
```

**Freshness check:**
```python
def is_cache_fresh(source, ttl_seconds):
    row = conn.execute(
        "SELECT MAX(snapshot_time) FROM player_injuries WHERE source = ?",
        (source,)
    ).fetchone()
    if not row or not row[0]:
        return False
    from datetime import datetime
    age() - datetime.from = (datetime.nowisoformat(row[0])).total_seconds()
    return age < ttl_seconds
```

---

## DB-First Caching Pattern

Use this for injury/suspension data that must survive Streamlit restarts:

```python
def get_suspensions():
    # 1. Check SQLite first
    if is_cache_fresh("ESPN_SUSPENSION", _get_espn_ttl()):
        return read_from_db("ESPN_SUSPENSION")
    
    # 2. If stale, call external API
    data = fetch_espn_suspensions()
    
    # 3. Write to DB with new snapshot_time
    write_to_db(data, source="ESPN_SUSPENSION")
    return data
```

**Steps:**
1. Check `snapshot_time` in SQLite
2. If stale → call external API
3. Write to DB with new `snapshot_time`
4. Return data

---

## When to Use `@st.cache_data` vs SQLite

| Use | Tool | Reason |
|-----|------|--------|
| Computed values (odds formatting, prompt strings) | `@st.cache_data` | Short TTL, session-scoped OK |
| Injury data that must survive restart | SQLite | Cross-session persistence |
| Any data users expect to persist | SQLite | Streamlit restarts clear cache |

---

## CREATE TABLE IF NOT EXISTS

Never DROP tables in production:

```sql
-- ✅ Safe — won't fail if table exists
CREATE TABLE IF NOT EXISTS player_injuries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_name TEXT NOT NULL,
    ...
);

-- ❌ Never in production
DROP TABLE IF EXISTS player_injuries;
CREATE TABLE player_injuries(...);  -- deletes all data
```

---

## Composite Index Pattern

For injury lookups by player + time:

```sql
CREATE INDEX IF NOT EXISTS idx_player_injuries_name_time
ON player_injuries(player_name, snapshot_time);
```

---

## Adding Columns to Existing Tables

```python
def migrate_add_column(conn, table, column, column_type, default=None):
    existing = [row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()]
    if column not in existing:
        default_clause = f" DEFAULT {default}" if default is not None else ""
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_type}{default_clause}")
```

---

## Key Incident

**The-Odds-API quota exhaustion (Feb 2026):**
- Problem: `@st.cache_data` doesn't persist through Streamlit restart
- Fix: Use SQLite `player_injuries` table for data that must survive restarts
- Rule: Any data that must survive restarts → SQLite
