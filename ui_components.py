import re
import textwrap
import streamlit as st
from datetime import datetime, timedelta
import pytz
from season_context import CURRENT_SEASON
from time_utils import get_time_context
import ui_icons

# Timezone constant
ET = pytz.timezone('America/New_York')


def clean_ai_response(response: str) -> str:
    """
    Remove leaked system instructions from AI output.
    """
    if not response:
        return response

    leak_patterns = [
        r"=== CRITICAL: ROSTER VERIFICATION ===.*?(?=\n\n|\n##|\n\*\*[A-Z]|\Z)",
        r"\*\*BEFORE listing any player.*?(?=\n\n|\n-|\Z)",
        r"- If a player is listed as OUT.*?\n",
        r"- NEVER put injured/suspended players.*?\n",
        r"- Only include players who are ACTIVE.*?\n",
        r"- If unsure, say \"status unclear\".*?\n",
        r"\[INTERNAL.*?\].*?\n",
        r"\[DO NOT OUTPUT\].*?\n",
        r"(?i)always name.*?top.*?players.*?\n",
        r"(?i)check the injury report above.*?\n",
        r"(?i)use ONLY the rosters/injuries from.*?\n",
        r"\(ONLY include players NOT on injury list\)",
        r"\(ONLY ACTIVE players - check injury list!\)",
        r"\(only include.*?active.*?\)",
        r"\(check.*?injury.*?list.*?\)",
    ]

    cleaned = response
    for pattern in leak_patterns:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE | re.DOTALL)

    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    cleaned = re.sub(r'^\s*\n', '', cleaned)

    return cleaned.strip()


def render_header():
    """Render app header with Lo-Fi Premium SVG Logo."""
    logo_svg = ui_icons.get_icon("logo_main", size=48, color="#383531")
    
    st.markdown(textwrap.dedent(f"""
    <div style="text-align: center; padding: 40px 0 30px 0;">
        <div style="display: inline-flex; align-items: center; gap: 16px; margin-bottom: 12px;">
            {logo_svg}
            <div>
                <h1 style="color: #383531; margin: 0; font-size: 32px; font-weight: 700; letter-spacing: -0.5px; line-height: 1;">
                    Ludi Lite
                </h1>
                <p style="color: #C6A34F; margin: 0; font-size: 11px; text-transform: uppercase; letter-spacing: 2px; font-weight: 600; margin-top: 4px;">
                    Sanctuary from the Noise
                </p>
            </div>
        </div>
    </div>
    """), unsafe_allow_html=True)


def render_game_cards(games: list):
    """
    Render clickable game cards using Streamlit buttons styled via CSS.
    """
    if not games:
        st.info("📭 No games scheduled.")
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

    if today_games:
        st.markdown("#### TODAY")
        selected = _render_game_section(today_games, "today")
        if selected: selected_game = selected

    if tomorrow_games:
        st.markdown("#### TOMORROW")
        selected = _render_game_section(tomorrow_games, "tomorrow")
        if selected: selected_game = selected

    if other_games and not today_games and not tomorrow_games:
        st.markdown("#### UPCOMING")
        selected = _render_game_section(other_games, "other")
        if selected: selected_game = selected

    return selected_game


def _render_game_section(games: list, prefix: str):
    """
    Render grid of game buttons.
    """
    num_cols = min(4, max(2, len(games)))
    # For very few games, don't stretch them too wide
    cols = st.columns(num_cols)
    selected = None
    
    # We want a max width for cards
    
    for i, game in enumerate(games):
        col = cols[i % num_cols]
        with col:
            # Format spread
            spread = game.get('spread')
            if spread is not None:
                try:
                    spread_str = f"{float(spread):+.1f}"
                    # Add team context
                    if float(spread) < 0:
                        spread_display = f"{game['home']} {spread_str}"
                    else:
                        spread_display = f"{game['away']} {float(spread)*-1:+.1f}"
                except (ValueError, TypeError):
                    spread_display = "PK"
            else:
                spread_display = "PK"

            total = f"O/U {game.get('total')}" if game.get('total') else ""
            time_str = game.get('time', 'TBD').replace(" PM", "p").replace(" AM", "a")

            # Clean button text (Visuals handled by CSS)
            # Standard Format:
            # AWAY @ HOME
            # TIME  |  SPREAD
            current_label = f"{game['away']} @ {game['home']}\n{time_str}  ·  {spread_display}"

            if st.button(
                current_label,
                key=f"game_{prefix}_{i}_{game.get('id', i)}",
                use_container_width=True
            ):
                selected = game

    return selected


def render_chat_interface():
    """Render chat input with minimalist styling"""
    
    # Icon + Label
    search_icon = ui_icons.get_icon("search", size=18, color="#8A867F")
    st.markdown(textwrap.dedent(f"""
    <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px; margin-top: 20px;">
        {search_icon}
        <span style="font-size: 14px; color: #8A867F; font-weight: 500;">ASK LUDI</span>
    </div>
    """), unsafe_allow_html=True)

    query = st.text_input(
        "Chat Input",
        placeholder="E.g. 'Luka assists tonight' or 'Nuggets Sixers analysis'",
        key="chat_input",
        label_visibility="collapsed"
    )

    analyze_both = bool(query)
    analyze_method = False

    return query, analyze_both, analyze_method


def render_analysis_output(freestyle: str, methodology: str, show_both: bool = True, perplexity_used: bool = False):
    """
    Render analysis output in side-by-side 'Sanctuary' panels.
    """
    freestyle = clean_ai_response(freestyle) if freestyle else ""
    methodology = clean_ai_response(methodology) if methodology else ""

    if show_both and freestyle and methodology:
        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)

        with col1:
            # FREESTYLE PANEL
            icon = ui_icons.get_icon("freestyle", color="#5B7089")
            st.markdown(textwrap.dedent(f"""
            <div class="sanctuary-panel" style="border-top: 3px solid #7B94AB;">
                <div class="panel-header">
                    {icon}
                    <span style="color: #383531;">Freestyle</span>
                </div>
                <div style="font-size: 14px; line-height: 1.6; color: #383531;">
            """), unsafe_allow_html=True)
            
            if perplexity_used:
                st.markdown(textwrap.dedent("""<div class="badge-amber" style="background:#F3E8FF; color:#7B5FA6; display:inline-block; margin-bottom:12px;">⚡ Live Search</div>"""), unsafe_allow_html=True)
                
            st.markdown(freestyle)
            st.markdown("</div></div>", unsafe_allow_html=True)

        with col2:
            # METHODOLOGY PANEL
            icon = ui_icons.get_icon("methodology", color="#4A7C59")
            st.markdown(textwrap.dedent(f"""
            <div class="sanctuary-panel" style="border-top: 3px solid #4A7C59;">
                <div class="panel-header">
                    {icon}
                    <span style="color: #383531;">S.A.V.A.G.E.</span>
                </div>
                <div style="font-size: 14px; line-height: 1.6; color: #383531;">
            """), unsafe_allow_html=True)
            
            # Badges
            st.markdown(textwrap.dedent("""
            <div style="display: flex; gap: 6px; margin-bottom: 12px; flex-wrap: wrap;">
                <span class="badge-amber">Usage Vacuum</span>
                <span class="badge-amber">Archetypes</span>
                <span class="badge-amber">Pace</span>
            </div>
            """), unsafe_allow_html=True)
            
            st.markdown(methodology)
            st.markdown("</div></div>", unsafe_allow_html=True)
    
    elif methodology:
        # SINGLE PANEL
        icon = ui_icons.get_icon("methodology", color="#4A7C59")
        st.markdown(textwrap.dedent(f"""
        <div class="sanctuary-panel" style="border-top: 3px solid #4A7C59;">
            <div class="panel-header">
                {icon}
                <span style="color: #383531;">S.A.V.A.G.E. Analysis</span>
            </div>
            <div style="font-size: 14px; line-height: 1.6;">
        """), unsafe_allow_html=True)
        st.markdown(methodology)
        st.markdown("</div></div>", unsafe_allow_html=True)

    # Footer Legend
    st.markdown(textwrap.dedent("""
    <div style="text-align: center; margin-top: 30px; margin-bottom: 50px;">
        <p class="text-stone text-sm uppercase">Ludi Lite Research Lab</p>
    </div>
    """), unsafe_allow_html=True)


def render_manual_input():
    # Only keeping this as a stub since it's removed from main workflow in app.py
    # but might be imported
    return None, None


def render_prop_analysis_card(player: str, stat: str, line: float, analysis: dict) -> None:
    # Deprecated for now, moving to text-based AI output
    pass


def render_hit_rate_dots(hits: int, total: int = 15) -> str:
    return ""
