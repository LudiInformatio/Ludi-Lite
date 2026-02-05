"""
UI Components for Ludi Lite
Streamlit rendering functions for the dashboard.
"""

import streamlit as st
from season_context import CURRENT_SEASON
from time_utils import get_time_context


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
