"""
UI Components for Ludi Lite
Streamlit rendering functions for the dashboard.
"""

import re
import streamlit as st
from datetime import datetime, timedelta
import pytz
from season_context import CURRENT_SEASON
from time_utils import get_time_context

# Timezone constant
ET = pytz.timezone('America/New_York')


def clean_ai_response(response: str) -> str:
    """
    Remove leaked system instructions from AI output.
    These patterns come from ROSTER_RULES in prompts.py that sometimes
    echo back in Claude's response.
    """
    if not response:
        return response

    leak_patterns = [
        # Full ROSTER_RULES block
        r"=== CRITICAL: ROSTER VERIFICATION ===.*?(?=\n\n|\n##|\n\*\*[A-Z]|\Z)",
        # Individual instruction lines
        r"\*\*BEFORE listing any player.*?(?=\n\n|\n-|\Z)",
        r"- If a player is listed as OUT.*?\n",
        r"- NEVER put injured/suspended players.*?\n",
        r"- Only include players who are ACTIVE.*?\n",
        r"- If unsure, say \"status unclear\".*?\n",
        # Internal markers
        r"\[INTERNAL.*?\].*?\n",
        r"\[DO NOT OUTPUT\].*?\n",
        # Common instruction echoes
        r"(?i)always name.*?top.*?players.*?\n",
        r"(?i)check the injury report above.*?\n",
        r"(?i)use ONLY the rosters/injuries from.*?\n",
    ]

    cleaned = response
    for pattern in leak_patterns:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE | re.DOTALL)

    # Clean up resulting extra whitespace
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    cleaned = re.sub(r'^\s*\n', '', cleaned)  # Leading blank lines

    return cleaned.strip()


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
    """
    Render clickable game cards grouped by date.
    Shows TODAY and TOMORROW sections with games sorted chronologically.
    """
    if not games:
        st.info("📭 No games scheduled. Check back later!")
        return None

    # Group games by date
    today = datetime.now(ET).date()
    tomorrow = today + timedelta(days=1)

    today_games = []
    tomorrow_games = []
    other_games = []

    for game in games:
        try:
            commence = game.get('commence_time', '')
            if commence:
                game_dt = datetime.fromisoformat(
                    commence.replace('Z', '+00:00')
                ).astimezone(ET).date()

                if game_dt == today:
                    today_games.append(game)
                elif game_dt == tomorrow:
                    tomorrow_games.append(game)
                else:
                    other_games.append(game)
            else:
                other_games.append(game)
        except Exception:
            other_games.append(game)

    selected_game = None

    # Render TODAY section
    if today_games:
        st.markdown("#### 🏀 TODAY")
        selected = _render_game_section(today_games, "today")
        if selected:
            selected_game = selected

    # Render TOMORROW section
    if tomorrow_games:
        st.markdown("#### 📆 TOMORROW")
        selected = _render_game_section(tomorrow_games, "tomorrow")
        if selected:
            selected_game = selected

    # Render OTHER section (future games beyond tomorrow)
    if other_games and not today_games and not tomorrow_games:
        st.markdown("#### 📅 UPCOMING")
        selected = _render_game_section(other_games, "other")
        if selected:
            selected_game = selected

    return selected_game


def _render_game_section(games: list, prefix: str):
    """
    Render a section of game cards in a responsive grid.
    Returns the selected game if user clicks one.
    """
    # Responsive columns: max 4 on desktop, wraps on mobile
    num_cols = min(len(games), 4)
    cols = st.columns(num_cols)
    selected = None

    for i, game in enumerate(games):
        col = cols[i % num_cols]
        with col:
            # Format spread
            spread = game.get('spread')
            if spread is not None:
                try:
                    spread_str = f"{game['home']} {float(spread):+.1f}"
                except (ValueError, TypeError):
                    spread_str = "PK"
            else:
                spread_str = "PK"

            # Format total
            total = game.get('total')
            total_str = f"O/U {total}" if total else ""

            # Create button with game info
            button_text = f"**{game['away']} @ {game['home']}**\n{spread_str} | {total_str}\n🕐 {game.get('time', 'TBD')}"

            if st.button(
                button_text,
                key=f"game_{prefix}_{i}_{game.get('id', i)}",
                use_container_width=True
            ):
                selected = game

    return selected


def render_chat_interface():
    """Render chat input for natural language queries"""
    st.markdown("### 💬 Ask Ludi")

    query = st.text_input(
        "Ask about a player, prop, or game...",
        placeholder="Examples: 'Luka assists tonight', 'DEN vs NYK', 'Trae Young PTS 28.5' (Press Enter)",
        key="chat_input",
        label_visibility="collapsed"
    )

    # Auto-analyze when query is entered (press Enter)
    # Query submission automatically shows BOTH analyses
    analyze_both = bool(query)  # Auto-trigger on query
    analyze_method = False  # Not used - always show both

    return query, analyze_both, analyze_method


def render_analysis_output(freestyle: str, methodology: str, show_both: bool = True, perplexity_used: bool = False):
    """Render analysis results side by side"""
    # Clean responses before rendering
    freestyle_cleaned = clean_ai_response(freestyle) if freestyle else ""
    methodology_cleaned = clean_ai_response(methodology) if methodology else ""

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
            st.markdown(freestyle_cleaned)

        with col2:
            st.markdown("""
            <div style="background: #10B98120; border: 2px solid #10B981; border-radius: 8px; padding: 5px 15px; margin-bottom: 10px;">
                <h3 style="color: #10B981; margin: 0;">🎯 Ludi Method</h3>
                <p style="color: #94A3B8; margin: 0; font-size: 11px;">Claude + S.A.V.A.G.E. + Tank01</p>
            </div>
            """, unsafe_allow_html=True)
            st.markdown(methodology_cleaned)
    else:
        st.markdown("""
        <div style="background: #10B98120; border: 2px solid #10B981; border-radius: 8px; padding: 5px 15px; margin-bottom: 10px;">
            <h3 style="color: #10B981; margin: 0;">🎯 Ludi Method Analysis</h3>
        </div>
        """, unsafe_allow_html=True)
        st.markdown(methodology_cleaned)


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
