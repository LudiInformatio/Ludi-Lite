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
    """Render app header with Lo-Fi Premium styling."""
    st.markdown("""
    <div style="text-align: center; padding: 20px 0 30px 0;">
        <div style="display: inline-flex; align-items: center; gap: 12px;">
            <span style="font-size: 32px;">🏀</span>
            <div>
                <h1 style="color: #f5f3ed; margin: 0; font-size: 28px; font-weight: 700; letter-spacing: -1px;">
                    Ludi Lite
                </h1>
                <p style="color: #C6A34F; margin: 0; font-size: 12px; text-transform: uppercase; letter-spacing: 2px;">
                    AI Sports Research Lab
                </p>
            </div>
        </div>
        <p style="color: #8A867F; font-size: 13px; margin-top: 12px; font-style: italic;">
            "A Sanctuary from the Noise"
        </p>
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
    """
    Render analysis output with Lo-Fi Premium styling.
    Brief, scannable format inspired by PropsMadness.
    """
    # Clean leaked instructions
    freestyle = clean_ai_response(freestyle) if freestyle else ""
    methodology = clean_ai_response(methodology) if methodology else ""

    if show_both and freestyle and methodology:
        # Section header
        st.markdown("""
        <div style="text-align: center; margin-bottom: 20px;">
            <span style="color: #8A867F; font-size: 12px; text-transform: uppercase; letter-spacing: 2px;">
                Analysis Comparison
            </span>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        with col1:
            # Freestyle Header
            st.markdown("""
            <div style="background: linear-gradient(135deg, #2A3441 0%, #344152 100%);
                        border: 2px solid #5B7C99; border-radius: 12px; padding: 16px; margin-bottom: 8px;">
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px;">
                    <span style="font-size: 20px;">🔍</span>
                    <div>
                        <div style="color: #f5f3ed; font-weight: 600;">FREESTYLE</div>
                        <div style="color: #5B7C99; font-size: 11px;">Raw AI Research</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Perplexity badge if used
            if perplexity_used:
                st.markdown("""
                <div style="background: rgba(139, 92, 246, 0.1); border: 1px solid #8B5CF6;
                            border-radius: 6px; padding: 6px 10px; margin-bottom: 12px; display: inline-block;">
                    <span style="color: #A78BFA; font-size: 11px;">⚡ + Perplexity Real-Time</span>
                </div>
                """, unsafe_allow_html=True)

            st.markdown(freestyle)

        with col2:
            # S.A.V.A.G.E. Header
            st.markdown("""
            <div style="background: linear-gradient(135deg, #2A3D2E 0%, #344D3A 100%);
                        border: 2px solid #4A7C59; border-radius: 12px; padding: 16px; margin-bottom: 8px;">
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px;">
                    <span style="font-size: 20px;">🎯</span>
                    <div>
                        <div style="color: #f5f3ed; font-weight: 600;">S.A.V.A.G.E.</div>
                        <div style="color: #4A7C59; font-size: 11px;">Ludi Methodology</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Methodology badges
            st.markdown("""
            <div style="display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 12px;">
                <span style="background: rgba(198, 163, 79, 0.15); border: 1px solid #C6A34F;
                            border-radius: 4px; padding: 3px 8px; font-size: 10px; color: #C6A34F;">Usage Vacuum</span>
                <span style="background: rgba(198, 163, 79, 0.15); border: 1px solid #C6A34F;
                            border-radius: 4px; padding: 3px 8px; font-size: 10px; color: #C6A34F;">Archetype</span>
                <span style="background: rgba(198, 163, 79, 0.15); border: 1px solid #C6A34F;
                            border-radius: 4px; padding: 3px 8px; font-size: 10px; color: #C6A34F;">Pace</span>
            </div>
            """, unsafe_allow_html=True)

            st.markdown(methodology)

        # Comparison legend
        st.markdown("""
        <div style="background: #2D2A26; border-radius: 8px; padding: 12px; margin-top: 16px;">
            <div style="color: #8A867F; font-size: 11px; text-align: center;">
                <strong style="color: #5B7C99;">Freestyle</strong> = General AI research |
                <strong style="color: #4A7C59;">S.A.V.A.G.E.</strong> = Usage Vacuum • Archetype vs Scheme • Pace • Blowout Tax • B2B Fatigue
            </div>
        </div>
        """, unsafe_allow_html=True)

    elif methodology:
        # Single panel (Ludi Method only)
        st.markdown("""
        <div style="background: linear-gradient(135deg, #2A3D2E 0%, #344D3A 100%);
                    border: 2px solid #4A7C59; border-radius: 12px; padding: 20px;">
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 16px;">
                <span style="font-size: 24px;">🎯</span>
                <div>
                    <div style="color: #f5f3ed; font-weight: 600; font-size: 18px;">S.A.V.A.G.E. Analysis</div>
                    <div style="color: #4A7C59; font-size: 12px;">Ludi Methodology Applied</div>
                </div>
            </div>
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


def render_prop_analysis_card(player: str, stat: str, line: float, analysis: dict) -> None:
    """
    Render a PropsMadness-style prop analysis card.

    Args:
        player: Player name
        stat: Stat type (PTS, AST, REB, etc.)
        line: The betting line
        analysis: Dict with hit_rate, l15_avg, h2h_record, defense_rank, verdict
    """
    st.markdown(f"""
    <div style="background: #2D2A26; border-radius: 12px; padding: 20px; border: 1px solid #8A867F;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
            <div>
                <h3 style="color: #f5f3ed; margin: 0;">{player}</h3>
                <span style="color: #8A867F; font-size: 12px;">{stat} | Line: {line}</span>
            </div>
            <div class="time-badge">{analysis.get('verdict', 'LEAN OVER')}</div>
        </div>

        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 16px;">
            <div class="stat-card">
                <div class="label">L15 Avg</div>
                <div class="value">{analysis.get('l15_avg', 'N/A')}</div>
                <div class="subtext">{analysis.get('l15_min', 'N/A')} min</div>
            </div>
            <div class="stat-card">
                <div class="label">Hit Rate</div>
                <div class="value">{analysis.get('hit_rate', 'N/A')}</div>
                <div class="subtext">{analysis.get('hit_games', '0')}/15 games</div>
            </div>
            <div class="stat-card">
                <div class="label">vs Opp</div>
                <div class="value">{analysis.get('h2h_rate', 'N/A')}</div>
                <div class="subtext">{analysis.get('h2h_games', '0')} games</div>
            </div>
            <div class="stat-card">
                <div class="label">Def Rank</div>
                <div class="value">#{analysis.get('defense_rank', 'N/A')}</div>
                <div class="subtext">vs {stat}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_hit_rate_dots(hits: int, total: int = 15) -> str:
    """Generate HTML for hit rate dot visualization."""
    dots = ""
    for i in range(total):
        if i < hits:
            dots += '<span class="dot active"></span>'
        else:
            dots += '<span class="dot"></span>'
    return f'<div class="hit-rate">{dots}</div>'
