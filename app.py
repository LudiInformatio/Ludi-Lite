"""
Ludi Lite - AI Sports Research Lab
Dashboard with Game Cards + Chat Interface
Side-by-side: Claude Freestyle vs Claude + Ludi Methodology

Run with: streamlit run app.py
Mobile: Access via http://YOUR-IP:8501 on same WiFi
"""

import streamlit as st
import anthropic
import sqlite3
import json
import os
from datetime import datetime, date
from typing import Optional, Tuple
import requests
import pytz

from prompts import FREESTYLE_PROMPT, LUDI_METHOD_PROMPT, PLAYER_SPOTLIGHT_PROMPT
from season_context import (
    get_defense_scheme,
    get_offense_scheme,
    get_game_specific_context,
    get_player_specific_context,
    get_full_season_context,
    CURRENT_SEASON
)
# Optional Perplexity integration for Freestyle
try:
    from perplexity_client import search_game_context, search_player_context, is_perplexity_available
    PERPLEXITY_ENABLED = is_perplexity_available()
except ImportError:
    PERPLEXITY_ENABLED = False
    def search_game_context(*args): return ""
    def search_player_context(*args): return ""

# Team name normalization (handles Odds-API vs Tank01 naming differences)
from team_mapping import normalize_team, get_full_name

# Timezone for game times (Eastern)
ET = pytz.timezone('America/New_York')

# =============================================================================
# Configuration
# =============================================================================

st.set_page_config(
    page_title="Ludi Lite",
    page_icon="🏀",
    layout="wide",
    initial_sidebar_state="collapsed"  # Better for mobile
)

# Custom CSS for mobile-friendly cards
st.markdown("""
<style>
    /* Dark theme */
    .stApp {
        background-color: #0F172A;
    }

    /* Game card styling */
    .game-card {
        background: linear-gradient(135deg, #1E293B 0%, #334155 100%);
        border-radius: 12px;
        padding: 15px;
        margin: 8px 0;
        border: 1px solid #475569;
        cursor: pointer;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    .game-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(251, 191, 36, 0.2);
    }
    .game-card h3 {
        color: #F8FAFC;
        margin: 0 0 8px 0;
        font-size: 18px;
    }
    .game-card .line {
        color: #FBBF24;
        font-weight: bold;
        font-size: 14px;
    }
    .game-card .time {
        color: #94A3B8;
        font-size: 12px;
    }

    /* Chat styling */
    .chat-input {
        background: #1E293B;
        border: 1px solid #475569;
        border-radius: 8px;
        color: #F8FAFC;
    }

    /* Analysis panels */
    .freestyle-panel {
        background: #1E3A5F;
        border: 2px solid #60A5FA;
        border-radius: 8px;
        padding: 15px;
    }
    .method-panel {
        background: #1A3D2E;
        border: 2px solid #10B981;
        border-radius: 8px;
        padding: 15px;
    }

    /* Time badge */
    .time-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: bold;
    }

    /* Mobile responsive */
    @media (max-width: 768px) {
        .game-card {
            padding: 12px;
        }
        .game-card h3 {
            font-size: 16px;
        }
    }

    /* Hide Streamlit branding for cleaner look */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# =============================================================================
# Database Setup
# =============================================================================

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

init_db()

# =============================================================================
# Time Context
# =============================================================================

def get_time_context() -> dict:
    """Get current time context for analysis"""
    try:
        now_et = datetime.now(ET)
    except Exception:
        now_et = datetime.now()

    hour = now_et.hour

    if hour < 12:
        mode = "EARLY_LOOK"
        confidence = "LOW - Verify closer to game time"
        color = "#FCD34D"
    elif hour < 17:
        mode = "AFTERNOON"
        confidence = "MEDIUM - Watch for updates"
        color = "#60A5FA"
    elif hour < 19:
        mode = "PRE_GAME"
        confidence = "HIGH - Most lineups confirmed"
        color = "#34D399"
    else:
        mode = "LOCK_TIME"
        confidence = "HIGHEST - Games starting"
        color = "#F87171"

    return {
        "timestamp": now_et.strftime("%I:%M %p ET"),
        "date": now_et.strftime("%b %d, %Y"),
        "mode": mode,
        "confidence": confidence,
        "color": color,
        "hour": hour
    }


def build_time_aware_prompt(base_prompt: str, time_context: dict, late_news: str = "") -> str:
    """Inject time context and season data into prompt"""
    # Get current season context (rosters, injuries, etc.)
    season_context = get_full_season_context()

    time_header = f"""
=== ANALYSIS TIMESTAMP ===
Current Time: {time_context['timestamp']} on {time_context['date']}
Analysis Mode: {time_context['mode']}
Confidence: {time_context['confidence']}

{season_context}
"""
    if late_news.strip():
        time_header += f"""
=== LATE NEWS (User Provided - Prioritize This) ===
{late_news}
"""
    return time_header + "\n" + base_prompt

# =============================================================================
# API Functions
# =============================================================================

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
    4. Local Ludi-Bot .env file (development fallback)
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

    # Priority 4: Local .env file (development only)
    env_path = os.path.expanduser("~/Ludi-Bot/.env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                if line.startswith(f"{key_name}="):
                    return line.strip().split("=", 1)[1].strip('"\'')

    return None


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
            "markets": "spreads,totals",
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

                # Get spread and total from first bookmaker
                spread = None
                total = None
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

# =============================================================================
# Query Parser
# =============================================================================

def parse_chat_query(query: str) -> Tuple[str, dict]:
    """
    Parse natural language query into structured request

    Handles:
    - Games: "DEN vs NYK", "Lakers @ Suns"
    - Players: "Luka", "Doncic", "Luka Doncic"
    - Stats: PTS, AST, REB, 3PM, STL, BLK, TO, MIN, FG, FT, etc.
    - Combos: PRA, PA, PR, RA, PTS+AST, PTS+REB+AST, stocks, etc.
    - Props: "Luka PTS 28.5", "Trae assists over 9.5"

    Returns: (query_type, params)
    """
    import re
    query_lower = query.lower().strip()
    query_original = query.strip()

    # ===================
    # GAME QUERY PATTERNS
    # ===================
    # "DEN vs NYK", "Lakers @ Suns", "Denver versus New York"
    game_patterns = [
        r"(\w+)\s+(?:vs\.?|versus|@|at)\s+(\w+)",
    ]
    for pattern in game_patterns:
        match = re.search(pattern, query_lower)
        if match:
            # Use proper team normalization (handles "Lakers", "LAL", "Los Angeles", etc.)
            away = normalize_team(match.group(1))
            home = normalize_team(match.group(2))
            return "game", {"away": away, "home": home}

    # ===================
    # STAT NORMALIZATION
    # ===================
    stat_aliases = {
        # Points
        "pts": "Points", "points": "Points", "point": "Points", "scoring": "Points",
        # Assists
        "ast": "Assists", "assists": "Assists", "assist": "Assists", "dimes": "Assists",
        # Rebounds
        "reb": "Rebounds", "rebounds": "Rebounds", "rebound": "Rebounds", "boards": "Rebounds",
        "trb": "Rebounds", "total rebounds": "Rebounds",
        # 3-Pointers
        "3pm": "3PM", "3s": "3PM", "threes": "3PM", "three pointers": "3PM",
        "3pt": "3PM", "3 pointers": "3PM", "triples": "3PM",
        # Steals
        "stl": "Steals", "steals": "Steals", "steal": "Steals",
        # Blocks
        "blk": "Blocks", "blocks": "Blocks", "block": "Blocks",
        # Turnovers
        "to": "Turnovers", "turnovers": "Turnovers", "turnover": "Turnovers", "tos": "Turnovers",
        # Minutes
        "min": "Minutes", "mins": "Minutes", "minutes": "Minutes",
        # Field Goals
        "fgm": "FGM", "fg": "FGM", "field goals": "FGM",
        # Free Throws
        "ftm": "FTM", "ft": "FTM", "free throws": "FTM", "fts": "FTM",
        # Fantasy
        "fpts": "Fantasy", "fantasy": "Fantasy", "fantasy points": "Fantasy", "fp": "Fantasy",

        # === COMBO PROPS ===
        # PRA (Points + Rebounds + Assists)
        "pra": "PTS+REB+AST", "pts+reb+ast": "PTS+REB+AST", "pts reb ast": "PTS+REB+AST",
        "points rebounds assists": "PTS+REB+AST", "p+r+a": "PTS+REB+AST",
        # PA (Points + Assists)
        "pa": "PTS+AST", "pts+ast": "PTS+AST", "points assists": "PTS+AST",
        "points and assists": "PTS+AST", "p+a": "PTS+AST", "pts ast": "PTS+AST",
        # PR (Points + Rebounds)
        "pr": "PTS+REB", "pts+reb": "PTS+REB", "points rebounds": "PTS+REB",
        "points and rebounds": "PTS+REB", "p+r": "PTS+REB", "pts reb": "PTS+REB",
        # RA (Rebounds + Assists)
        "ra": "REB+AST", "reb+ast": "REB+AST", "rebounds assists": "REB+AST",
        "rebounds and assists": "REB+AST", "r+a": "REB+AST", "reb ast": "REB+AST",
        # Stocks (Steals + Blocks)
        "stocks": "STL+BLK", "stl+blk": "STL+BLK", "steals blocks": "STL+BLK",
        "steals and blocks": "STL+BLK", "defensive stats": "STL+BLK",
        # Boards + Dimes
        "boards dimes": "REB+AST", "rebounds dimes": "REB+AST",
        # Double-Double
        "dd": "Double-Double", "double double": "Double-Double", "double-double": "Double-Double",
        # Triple-Double
        "td": "Triple-Double", "triple double": "Triple-Double", "triple-double": "Triple-Double",
    }

    # ===================
    # PROP WITH LINE PATTERN
    # ===================
    # "Luka PTS 28.5", "Trae Young assists 9.5", "Jokic PRA over 45.5"
    # Pattern: [name] [stat] [optional: over/under] [number]

    # Build stat pattern from aliases
    stat_keywords = "|".join(sorted(stat_aliases.keys(), key=len, reverse=True))

    # Pattern 1: Name + Stat + Number
    prop_pattern = rf"(.+?)\s+({stat_keywords})\s+(?:over|under|o|u)?\s*(\d+\.?\d*)"
    prop_match = re.search(prop_pattern, query_lower)

    if prop_match:
        name_raw = prop_match.group(1).strip()
        stat_raw = prop_match.group(2).strip()
        line = float(prop_match.group(3))

        # Clean up name (remove common prefixes)
        name = name_raw.replace("give me", "").replace("info on", "").replace("about", "").strip()
        name = name.title()

        # Normalize stat
        stat = stat_aliases.get(stat_raw, stat_raw.upper())

        return "player_prop", {"name": name, "stat": stat, "line": line}

    # ===================
    # PLAYER + STAT (no line)
    # ===================
    # "Luka assists", "Jokic rebounds", "Trae PRA"
    stat_pattern = rf"(.+?)\s+({stat_keywords})(?:\s|$)"
    stat_match = re.search(stat_pattern, query_lower)

    if stat_match:
        name_raw = stat_match.group(1).strip()
        stat_raw = stat_match.group(2).strip()

        # Clean name
        name = name_raw.replace("give me", "").replace("info on", "").replace("about", "").strip()
        name = name.title()

        # Normalize stat
        stat = stat_aliases.get(stat_raw, stat_raw.upper())

        return "player", {"name": name, "stat": stat}

    # ===================
    # PLAYER ONLY (general query)
    # ===================
    # "Luka", "tell me about Jokic", "info on Trae Young"

    # Remove common prefixes
    clean_query = query_lower
    prefixes_to_remove = [
        "give me info on", "give me information on", "tell me about",
        "info on", "information on", "about", "what about",
        "how is", "how's", "analyze", "breakdown", "break down"
    ]
    for prefix in prefixes_to_remove:
        if clean_query.startswith(prefix):
            clean_query = clean_query[len(prefix):].strip()
            break

    # If something remains, treat as player name
    if clean_query and len(clean_query) > 1:
        return "player", {"name": clean_query.title(), "stat": "All Stats"}

    return "unknown", {}

# =============================================================================
# UI Components
# =============================================================================

def render_header():
    """Render dashboard header"""
    time_ctx = get_time_context()

    st.markdown(f"""
    <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px 0; border-bottom: 1px solid #334155; margin-bottom: 20px;">
        <div>
            <h1 style="color: #FBBF24; margin: 0; font-size: 28px;">🏀 Ludi Lite</h1>
            <p style="color: #94A3B8; margin: 5px 0 0 0; font-size: 14px;">AI Research Lab | {CURRENT_SEASON}</p>
        </div>
        <div style="text-align: right;">
            <span class="time-badge" style="background: {time_ctx['color']}20; color: {time_ctx['color']};">
                {time_ctx['mode']}
            </span>
            <p style="color: #94A3B8; margin: 5px 0 0 0; font-size: 12px;">{time_ctx['timestamp']}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_game_cards(games: list):
    """Render clickable game cards"""
    if not games:
        st.info("No games found. Enter a game manually below or check API key.")
        return None

    st.markdown("### 📅 Today's Games")
    st.markdown("<p style='color: #94A3B8; font-size: 12px;'>Click a game to analyze</p>", unsafe_allow_html=True)

    # Create columns for game cards (responsive)
    cols = st.columns(min(len(games), 4))

    selected_game = None

    for i, game in enumerate(games):
        col = cols[i % len(cols)]
        with col:
            spread_str = f"{game['home']} {game['spread']:+.1f}" if game['spread'] else "PK"
            total_str = f"O/U {game['total']}" if game['total'] else ""

            # Create button styled as card
            if st.button(
                f"**{game['away']} @ {game['home']}**\n{spread_str} | {total_str}\n{game['time']}",
                key=f"game_{i}",
                use_container_width=True
            ):
                selected_game = game

    return selected_game


def render_chat_interface():
    """Render chat input for natural language queries"""
    st.markdown("### 💬 Ask Ludi")

    query = st.text_input(
        "Ask about a player, prop, or game...",
        placeholder="Examples: 'Luka assists tonight', 'DEN vs NYK', 'Trae Young PTS 28.5'",
        key="chat_input",
        label_visibility="collapsed"
    )

    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        analyze_both = st.button("🔍 Analyze Both", type="primary", disabled=not query)
    with col2:
        analyze_method = st.button("🎯 Ludi Only", disabled=not query)

    return query, analyze_both, analyze_method


def render_analysis_output(freestyle: str, methodology: str, show_both: bool = True, perplexity_used: bool = False):
    """Render analysis results side by side"""
    if show_both:
        col1, col2 = st.columns(2)

        # Freestyle header - show Perplexity badge if used
        freestyle_subtitle = "Claude + Perplexity Search" if perplexity_used else "Claude AI"
        freestyle_icon = "🤖🔍" if perplexity_used else "🤖"

        with col1:
            st.markdown(f"""
            <div style="background: #60A5FA20; border: 2px solid #60A5FA; border-radius: 8px; padding: 5px 15px; margin-bottom: 10px;">
                <h3 style="color: #60A5FA; margin: 0;">{freestyle_icon} Freestyle</h3>
                <p style="color: #94A3B8; margin: 0; font-size: 11px;">{freestyle_subtitle}</p>
            </div>
            """, unsafe_allow_html=True)
            st.markdown(freestyle)

        with col2:
            st.markdown("""
            <div style="background: #10B98120; border: 2px solid #10B981; border-radius: 8px; padding: 5px 15px; margin-bottom: 10px;">
                <h3 style="color: #10B981; margin: 0;">🎯 Ludi Method</h3>
                <p style="color: #94A3B8; margin: 0; font-size: 11px;">Claude + S.A.V.A.G.E. + Tank01</p>
            </div>
            """, unsafe_allow_html=True)
            st.markdown(methodology)
    else:
        st.markdown("""
        <div style="background: #10B98120; border: 2px solid #10B981; border-radius: 8px; padding: 5px 15px; margin-bottom: 10px;">
            <h3 style="color: #10B981; margin: 0;">🎯 Ludi Method Analysis</h3>
        </div>
        """, unsafe_allow_html=True)
        st.markdown(methodology)


def render_manual_input():
    """Render manual game/player input as fallback"""
    with st.expander("📝 Manual Input", expanded=False):
        input_type = st.radio("Type", ["Game", "Player"], horizontal=True)

        if input_type == "Game":
            col1, col2 = st.columns(2)
            with col1:
                away = st.text_input("Away Team", placeholder="DEN")
                spread = st.number_input("Spread", value=0.0, step=0.5)
            with col2:
                home = st.text_input("Home Team", placeholder="NYK")
                total = st.number_input("Total", value=220.0, step=0.5)

            context = st.text_area("Context (injuries, B2B, etc.)", height=80)
            late_news = st.text_area("🚨 Late News", height=60)

            if away and home:
                return "game", {
                    "away": away.upper(),
                    "home": home.upper(),
                    "spread": spread,
                    "total": total,
                    "context": context,
                    "late_news": late_news
                }
        else:
            col1, col2 = st.columns(2)
            with col1:
                player = st.text_input("Player Name", placeholder="Luka Doncic")
                team = st.text_input("Team", placeholder="DAL")
            with col2:
                opponent = st.text_input("Opponent", placeholder="PHX")
                stat = st.selectbox("Stat Focus", [
                    "All Stats",
                    "--- Single Stats ---",
                    "Points", "Assists", "Rebounds", "3PM",
                    "Steals", "Blocks", "Turnovers", "Minutes",
                    "FGM", "FTM",
                    "--- Combo Props ---",
                    "PTS+REB+AST (PRA)", "PTS+AST (PA)", "PTS+REB (PR)",
                    "REB+AST (RA)", "STL+BLK (Stocks)",
                    "--- Special ---",
                    "Double-Double", "Triple-Double", "Fantasy Points"
                ])

            context = st.text_area("Context", height=60)
            late_news = st.text_area("🚨 Late News", height=60)

            if player and opponent:
                return "player", {
                    "name": player,
                    "team": team,
                    "opponent": opponent,
                    "stat": stat,
                    "context": context,
                    "late_news": late_news
                }

    return None, None


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

# =============================================================================
# Main App
# =============================================================================

def main():
    render_header()

    time_ctx = get_time_context()

    # Initialize session state
    if "analysis_result" not in st.session_state:
        st.session_state.analysis_result = None

    # Section 1: Today's Games (Cards)
    games = fetch_todays_games()
    selected_game = render_game_cards(games)

    st.divider()

    # Section 2: Chat Interface
    query, analyze_both, analyze_ludi = render_chat_interface()

    # Section 3: Manual Input (collapsed)
    manual_type, manual_params = render_manual_input()

    st.divider()

    # Process Analysis
    analysis_input = None
    query_type = None
    late_news = ""

    # Priority: Selected game card > Chat query > Manual input
    if selected_game:
        query_type = "game"
        # Format spread safely
        spread_value = selected_game.get('spread')
        if spread_value is not None and spread_value != '':
            try:
                spread_str = f"{float(spread_value):+.1f}"
            except (ValueError, TypeError):
                spread_str = 'PK'
        else:
            spread_str = 'PK'

        # Get live roster/injury context for BOTH analysis modes
        live_context = get_game_specific_context(selected_game['home'], selected_game['away'])

        analysis_input = f"""
GAME: {selected_game['away']} @ {selected_game['home']}
SPREAD: {selected_game['home']} {spread_str}
TOTAL: {selected_game.get('total') or 'TBD'}
TIME: {selected_game.get('time') or 'TBD'}

{selected_game['away']} Defense: {get_defense_scheme(selected_game['away'])}
{selected_game['home']} Defense: {get_defense_scheme(selected_game['home'])}
{selected_game['away']} Offense: {get_offense_scheme(selected_game['away'])}
{selected_game['home']} Offense: {get_offense_scheme(selected_game['home'])}

{live_context}
"""

    elif query and (analyze_both or analyze_ludi):
        query_type, params = parse_chat_query(query)

        if query_type == "game":
            live_context = get_game_specific_context(params['home'], params['away'])
            analysis_input = f"""
GAME: {params['away']} @ {params['home']}
{params['away']} Defense: {get_defense_scheme(params['away'])}
{params['home']} Defense: {get_defense_scheme(params['home'])}
{params['away']} Offense: {get_offense_scheme(params['away'])}
{params['home']} Offense: {get_offense_scheme(params['home'])}

{live_context}
"""

        elif query_type in ["player", "player_prop"]:
            stat_focus = params.get('stat', 'All Stats')
            line_info = f"LINE: {params.get('line', 'N/A')}" if params.get('line') else ""
            opponent = params.get('opponent', 'Unknown')
            player_context = get_player_specific_context(params['name'])

            analysis_input = f"""
PLAYER: {params['name']}
STAT FOCUS: {stat_focus}
{line_info}
QUERY: {query}

{player_context}
"""
            query_type = "player"

        else:
            analysis_input = f"QUERY: {query}"
            query_type = "player"

    elif manual_type and manual_params:
        query_type = manual_type
        late_news = manual_params.get("late_news", "")

        if manual_type == "game":
            analysis_input = f"""
GAME: {manual_params['away']} @ {manual_params['home']}
SPREAD: {manual_params['home']} {manual_params['spread']:+.1f}
TOTAL: {manual_params['total']}

{manual_params['away']} Defense: {get_defense_scheme(manual_params['away'])}
{manual_params['home']} Defense: {get_defense_scheme(manual_params['home'])}

CONTEXT: {manual_params.get('context', 'None')}
"""
        else:
            analysis_input = f"""
PLAYER: {manual_params['name']} ({manual_params.get('team', '')})
OPPONENT: {manual_params['opponent']}
STAT FOCUS: {manual_params['stat']}
OPPONENT DEFENSE: {get_defense_scheme(manual_params['opponent'])}

CONTEXT: {manual_params.get('context', 'None')}
"""

    # Run Analysis
    if analysis_input and (selected_game or analyze_both or analyze_ludi or manual_params):
        # Select prompts based on query type
        if query_type == "game":
            prompt_freestyle = FREESTYLE_PROMPT
            prompt_method = LUDI_METHOD_PROMPT
        else:
            prompt_freestyle = FREESTYLE_PROMPT
            prompt_method = PLAYER_SPOTLIGHT_PROMPT

        # Add time context
        prompt_freestyle = build_time_aware_prompt(prompt_freestyle, time_ctx, late_news)
        prompt_method = build_time_aware_prompt(prompt_method, time_ctx, late_news)

        # Determine model
        model = "claude-sonnet-4-20250514"

        # Enhance Freestyle with Perplexity real-time search (if available)
        freestyle_input = analysis_input
        perplexity_used = False
        if PERPLEXITY_ENABLED and (analyze_both or selected_game):
            with st.spinner("🔍 Searching real-time data..."):
                if query_type == "game" and selected_game:
                    pplx_context = search_game_context(
                        selected_game.get('away_full', selected_game['away']),
                        selected_game.get('home_full', selected_game['home'])
                    )
                    if pplx_context:
                        freestyle_input = analysis_input + pplx_context
                        perplexity_used = True
                elif query_type == "player":
                    # Extract player name from analysis_input
                    pplx_context = search_player_context(query.split()[0] if query else "")
                    if pplx_context:
                        freestyle_input = analysis_input + pplx_context
                        perplexity_used = True

        if analyze_both or selected_game:
            spinner_text = "🤖🔍 Running Freestyle + Perplexity..." if perplexity_used else "🤖 Running Freestyle analysis..."
            with st.spinner(spinner_text):
                freestyle = get_claude_analysis(prompt_freestyle, freestyle_input, model)

            with st.spinner("🎯 Running Ludi Method analysis..."):
                methodology = get_claude_analysis(prompt_method, analysis_input, model)

            render_analysis_output(freestyle, methodology, show_both=True, perplexity_used=perplexity_used)

            # Save option
            if st.button("💾 Save Analysis"):
                save_analysis(query or "Game Card", freestyle, methodology)
                st.success("Saved!")

        elif analyze_ludi:
            with st.spinner("🎯 Running Ludi Method analysis..."):
                methodology = get_claude_analysis(prompt_method, analysis_input, model)

            render_analysis_output("", methodology, show_both=False)

    # Footer
    st.markdown("---")
    st.markdown("""
    <p style="color: #64748B; font-size: 11px; text-align: center;">
        Ludi Lite | Research Assistant | Not betting advice
    </p>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()

