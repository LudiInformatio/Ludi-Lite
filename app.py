"""
Ludi Lite - AI Sports Research Lab
Dashboard with Game Cards + Chat Interface
Side-by-side: Claude Freestyle vs Claude + Ludi Methodology

Run with: streamlit run app.py
Mobile: Access via http://YOUR-IP:8501 on same WiFi
"""

import streamlit as st
from datetime import datetime

from api_clients import (
    get_api_key,
    fetch_todays_games,
    fetch_player_props,
    format_props_context,
    get_claude_analysis,
)

# Use dynamic prompts for fresh injury data on each request
from prompts import get_dynamic_prompt
from season_context import (
    get_defense_scheme,
    get_offense_scheme,
    get_game_specific_context,
    get_player_specific_context,
)
from query_parser import parse_chat_query, match_player_to_game
# Optional Perplexity integration for Freestyle
try:
    from perplexity_client import search_game_context, search_player_context, search_late_news, is_perplexity_available
    PERPLEXITY_ENABLED = is_perplexity_available()
except ImportError:
    PERPLEXITY_ENABLED = False
    def search_game_context(*args, **kwargs): return ""
    def search_player_context(*args, **kwargs): return ""
    def search_late_news(*args): return ""

# Team name normalization (handles Odds-API vs Tank01 naming differences)
from team_mapping import normalize_team, get_full_name

# S.A.V.A.G.E. usage calculator (data-driven stat bumps when players are OUT)
from usage_calculator import get_usage_vacuum_analysis, format_usage_vacuum_for_prompt
from tank01_client import get_team_roster

# Extracted modules
from database import init_db, save_analysis
from time_utils import get_time_context, build_time_aware_prompt, ET
import ui_icons
from ui_components import render_header, render_game_cards, render_chat_interface, render_analysis_output

# =============================================================================
# Configuration
# =============================================================================

st.set_page_config(
    page_title="Ludi Lite",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed"  # Better for mobile
)

# Custom CSS - Lo-Fi Premium Palette
st.markdown("""
<style>
    /* -------------------------------------------------------------------------
       LUDI LITE - MILLION DOLLAR MINIMALIST
       "The Private Study" Aesthetic
       ------------------------------------------------------------------------- */
       
    /* 1. TYPOGRAPHY (Google Fonts) */
    @import url('https://fonts.googleapis.com/css2?family=Libre+Baskerville:wght@400;700&family=Inter:wght@300;400;500;600&display=swap');

    /* 2. THEME VARIABLES */
    :root {
        /* Palette - Warm Editorial */
        --paper: #F9F8F6;       /* Slightly brighter, cleaner cream */
        --ink: #1A1A1A;         /* Richer charcoal (almost black) */
        --stone: #7B7568;       /* Muted secondary text */
        --subtle: #E6E4DD;      /* Very subtle borders */
        --gold: #C6A34F;        /* Muted gold accent */
        --success: #4A7C59;     /* Deep verified green */
        
        /* Typography */
        --font-heading: 'Libre Baskerville', serif;
        --font-body: 'Inter', sans-serif;
        
        /* Depth (Apple/Linear Style) */
        --shadow-card: 
            0 1px 2px rgba(0,0,0,0.04), 
            0 4px 8px rgba(0,0,0,0.02),
            0 12px 24px rgba(0,0,0,0.02);
            
        --shadow-hover:
            0 2px 4px rgba(0,0,0,0.04), 
            0 12px 24px rgba(0,0,0,0.04),
            0 32px 64px rgba(0,0,0,0.04);
            
        --radius: 12px;
    }

    /* 3. GLOBAL RESET */
    .stApp {
        background-color: var(--paper);
        /* Subtle noise texture for tactile feel (very low opacity) */
        background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.8' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)' opacity='0.03'/%3E%3C/svg%3E");
        color: var(--ink);
        font-family: var(--font-body);
    }
    
    h1, h2, h3, h4 {
        font-family: var(--font-heading) !important;
        font-weight: 700 !important;
        color: var(--ink) !important;
        letter-spacing: -0.02em !important;
        line-height: 1.1 !important;
    }
    
    p, div, label, span {
        font-family: var(--font-body);
        color: var(--ink);
        line-height: 1.5;
    }

    /* 4. ANIMATIONS */
    @keyframes fade-in {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .fade-in { animation: fade-in 0.6s cubic-bezier(0.2, 0.8, 0.2, 1) forwards; }

    /* 5. HERO SECTION */
    .hero-container {
        text-align: center;
        padding: 60px 20px 40px;
        margin-bottom: 40px;
        /* No background gradient - purely whitespace */
    }

    .cta-button {
        display: inline-block;
        padding: 14px 32px;
        background-color: var(--ink);
        color: #FFFFFF !important;
        border-radius: 9999px; /* Pill shape */
        font-weight: 600;
        font-size: 13px;
        letter-spacing: 0.5px;
        text-decoration: none;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    
    .cta-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(0,0,0,0.15);
        background-color: #000000;
    }

    /* 6. COMPONENT OVERRIDES */
    
    /* Buttons as Cards (Game Cards) */
    div.row-widget.stButton > button {
        background: #FFFFFF;
        border: 1px solid rgba(0,0,0,0.03); /* Almost invisible border */
        box-shadow: var(--shadow-card);
        border-radius: var(--radius);
        padding: 20px 24px;
        text-align: left;
        color: var(--ink);
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
        height: auto;
        min-height: 90px;
    }
    
    div.row-widget.stButton > button:hover {
        transform: translateY(-4px);
        box-shadow: var(--shadow-hover);
        border-color: var(--gold);
        background: #FFFFFF;
        z-index: 10;
        position: relative;
    }
    
    div.row-widget.stButton > button:active, 
    div.row-widget.stButton > button:focus {
        border-color: var(--gold);
        box-shadow: 0 0 0 2px rgba(198, 163, 79, 0.2);
    }

    /* Inputs (Text, Select, Number) */
    /* Remove default gray borders and shadows */
    .stTextInput input, .stSelectbox div[data-baseweb="select"] > div, .stNumberInput input {
        background-color: #FFFFFF !important;
        border: 1px solid var(--subtle) !important;
        border-radius: 8px !important;
        box-shadow: none !important;
        color: var(--ink) !important;
        font-family: var(--font-body) !important;
        padding: 10px 14px !important;
        transition: border-color 0.2s, box-shadow 0.2s;
    }
    
    .stTextInput input:focus, .stNumberInput input:focus, .stSelectbox div[data-baseweb="select"] > div:focus-within {
        border-color: var(--gold) !important;
        box-shadow: 0 0 0 3px rgba(198, 163, 79, 0.15) !important;
    }
    
    /* Analysis Panels */
    .sanctuary-panel {
        background: #FFFFFF;
        border: 1px solid rgba(0,0,0,0.03);
        border-radius: var(--radius);
        padding: 32px; /* More whitespace */
        margin-bottom: 32px;
        box-shadow: var(--shadow-card);
        animation: fade-in 0.5s ease-out;
    }
    
    .panel-header {
        font-family: var(--font-heading);
        font-size: 20px;
        margin-bottom: 16px;
        display: flex;
        align-items: center;
        gap: 12px;
        border-bottom: 1px solid var(--subtle);
        padding-bottom: 16px;
    }

    /* Badges & Tags */
    .badge-amber {
        background-color: rgba(198, 163, 79, 0.1);
        color: #8E7022;
        padding: 4px 10px;
        border-radius: 4px;
        font-size: 10px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em; /* Wide tracking */
    }

    /* Utility Helpers */
    .text-stone { color: var(--stone) !important; }
    .text-sm { font-size: 13px !important; }
    .uppercase { text-transform: uppercase; letter-spacing: 0.08em; font-weight: 600; font-size: 11px; }

    /* Hide Default UI Gunk */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
</style>
""", unsafe_allow_html=True)

# Initialize database at module level
init_db()


def _get_vacuum_context(team_abbr: str, game_total=None) -> str:
    """
    Get S.A.V.A.G.E. usage vacuum analysis for a team.
    Returns formatted text to inject into Claude's prompt, or empty string.
    """
    try:
        roster = get_team_roster(team_abbr, include_stats=True)
        if not roster:
            return ""
        injured = [
            p["name"] for p in roster
            if p.get("injury", {}).get("designation", "").upper()
            in ("OUT", "DOUBTFUL", "SUSPENDED")
        ]
        if not injured:
            return ""
        total = float(game_total) if game_total else None
        analysis = get_usage_vacuum_analysis(team_abbr, injured, game_total=total)
        return format_usage_vacuum_for_prompt(analysis)
    except Exception:
        return ""

def render_sidebar():
    with st.sidebar:
        st.markdown("""
        <div style="padding: 20px 0;">
            <p style="font-family: var(--font-heading); font-size: 14px; color: var(--ink); font-weight: 700;">Ludi Lite</p>
            <p style="font-size: 11px; color: var(--stone);">v0.4 &middot; Research Lab</p>
        </div>
        """, unsafe_allow_html=True)


# =============================================================================
# Main App
# =============================================================================

def main():
    render_sidebar()
    
    # 2. Hero Section (Simplified - Logo Only)
    logo_svg = ui_icons.get_icon("logo_main", size=80, color="#383531")
    st.markdown(f"""
    <div class="hero-container fade-in" style="padding: 40px 20px 20px;">
        <div style="margin-bottom: 16px;">
            {logo_svg}
        </div>
        <!-- Ludi Lite Branding -->
        <h1 style="font-family: var(--font-heading); font-size: 32px; margin: 0; color: var(--charcoal);">
            Ludi Lite
        </h1>
        <p style="font-family: var(--font-body); font-size: 14px; color: var(--stone); letter-spacing: 1px; margin-top: 4px;">
            The Smart AI Bet Research Agent
        </p>
    </div>
    """, unsafe_allow_html=True)


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

    # Section 3: Manual Input (REMOVED - use natural language queries)
    # manual_type, manual_params = render_manual_input()

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

        # Fetch player props for this game (The-Odds-API)
        props_context = ""
        game_id = selected_game.get('id')
        if game_id:
            props = fetch_player_props(game_id)
            if props:
                props_context = format_props_context(props, max_players=8)

        # Format moneyline if available
        home_ml = selected_game.get('home_ml')
        away_ml = selected_game.get('away_ml')
        ml_str = ""
        if home_ml and away_ml:
            ml_str = f"\nMONEYLINE: {selected_game['away']} {away_ml:+d} / {selected_game['home']} {home_ml:+d}" if isinstance(home_ml, int) else ""

        # S.A.V.A.G.E. usage vacuum analysis for both teams
        game_total = selected_game.get('total')
        vacuum_text = ""
        home_vacuum = _get_vacuum_context(selected_game['home'], game_total)
        away_vacuum = _get_vacuum_context(selected_game['away'], game_total)
        if home_vacuum or away_vacuum:
            vacuum_text = f"\n=== USAGE VACUUM ANALYSIS (S.A.V.A.G.E. - calculated from Tank01 stats) ===\n{home_vacuum}{away_vacuum}"

        analysis_input = f"""
GAME: {selected_game['away']} @ {selected_game['home']}
SPREAD: {selected_game['home']} {spread_str}
TOTAL: {selected_game.get('total') or 'TBD'}{ml_str}
TIME: {selected_game.get('time') or 'TBD'}

{selected_game['away']} Defense: {get_defense_scheme(selected_game['away'])}
{selected_game['home']} Defense: {get_defense_scheme(selected_game['home'])}
{selected_game['away']} Offense: {get_offense_scheme(selected_game['away'])}
{selected_game['home']} Offense: {get_offense_scheme(selected_game['home'])}

{live_context}
{props_context}
{vacuum_text}
"""

    elif query and (analyze_both or analyze_ludi):
        query_type, params = parse_chat_query(query)

        if query_type == "game":
            live_context = get_game_specific_context(params['home'], params['away'])
            # S.A.V.A.G.E. vacuum for chat-based game queries
            vacuum_text = ""
            home_v = _get_vacuum_context(params['home'])
            away_v = _get_vacuum_context(params['away'])
            if home_v or away_v:
                vacuum_text = f"\n=== USAGE VACUUM ANALYSIS (S.A.V.A.G.E.) ===\n{home_v}{away_v}"

            analysis_input = f"""
GAME: {params['away']} @ {params['home']}
{params['away']} Defense: {get_defense_scheme(params['away'])}
{params['home']} Defense: {get_defense_scheme(params['home'])}
{params['away']} Offense: {get_offense_scheme(params['away'])}
{params['home']} Offense: {get_offense_scheme(params['home'])}

{live_context}
{vacuum_text}
"""

        elif query_type in ["player", "player_prop"]:
            stat_focus = params.get('stat', 'All Stats')
            line_info = f"LINE: {params.get('line', 'N/A')}" if params.get('line') else ""

            # Auto-match player to tonight's game FIRST (so we know team)
            game_match = match_player_to_game(params['name'], games)
            # Pass team to player context to avoid redundant broken lookup
            player_context = get_player_specific_context(params['name'], team_abbr=game_match.get("team"))
            opponent = game_match.get("opponent", params.get('opponent', 'Unknown'))
            game_context = ""

            if game_match.get("game"):
                g = game_match["game"]
                spread_val = g.get('spread')
                spread_str = f"{float(spread_val):+.1f}" if spread_val else "PK"
                total_str = f"O/U {g['total']}" if g.get('total') else ""
                home_ml = g.get('home_ml')
                away_ml = g.get('away_ml')
                ml_str = f"MONEYLINE: {g['away']} {away_ml:+d} / {g['home']} {home_ml:+d}" if isinstance(home_ml, int) else ""

                # Get live matchup context (rosters, injuries, scheme)
                live_matchup = get_game_specific_context(g['home'], g['away'])

                game_context = f"""
TONIGHT'S GAME: {g['away']} @ {g['home']}
SPREAD: {g['home']} {spread_str}  {total_str}
{ml_str}
TIME: {g.get('time', 'TBD')}
{g['away']} Defense: {get_defense_scheme(g['away'])}
{g['home']} Defense: {get_defense_scheme(g['home'])}
{g['away']} Offense: {get_offense_scheme(g['away'])}
{g['home']} Offense: {get_offense_scheme(g['home'])}

{live_matchup}
"""

            # S.A.V.A.G.E. vacuum for player's team (shows if teammates are OUT)
            player_vacuum = ""
            player_team = game_match.get('team')
            if player_team:
                g_total = game_match.get("game", {}).get("total")
                player_vacuum = _get_vacuum_context(player_team, g_total)
                if player_vacuum:
                    player_vacuum = f"\n=== USAGE VACUUM ANALYSIS (S.A.V.A.G.E.) ===\n{player_vacuum}"

            analysis_input = f"""
PLAYER: {params['name']}
TEAM: {game_match.get('team', 'Unknown')}
OPPONENT: {opponent}
STAT FOCUS: {stat_focus}
{line_info}
QUERY: {query}

{game_context}
{player_context}
{player_vacuum}
"""
            query_type = "player"

        else:
            analysis_input = f"QUERY: {query}"
            query_type = "player"

    # Run Analysis
    if analysis_input and (selected_game or analyze_both or analyze_ludi):
        # Get FRESH prompts with current injury data (not stale imports)
        if query_type == "game":
            prompt_freestyle = get_dynamic_prompt("freestyle")
            prompt_method = get_dynamic_prompt("methodology")
        else:
            prompt_freestyle = get_dynamic_prompt("freestyle")
            prompt_method = get_dynamic_prompt("player")

        # Add time context
        prompt_freestyle = build_time_aware_prompt(prompt_freestyle, time_ctx, late_news)
        prompt_method = build_time_aware_prompt(prompt_method, time_ctx, late_news)

        # Determine model
        model = "claude-sonnet-4-20250514"

        # Enhance Freestyle with Perplexity real-time search (if available)
        # Uses time-based recency filtering per industry best practices
        freestyle_input = analysis_input
        perplexity_used = False
        if PERPLEXITY_ENABLED and (analyze_both or selected_game):
            with st.spinner("🔍 Searching real-time data..."):
                # Calculate hours to game for dynamic recency filtering
                hours_to_game = 12  # Default
                if selected_game and selected_game.get('time'):
                    try:
                        game_time_str = selected_game['time']
                        now = datetime.now(ET)
                        game_time = datetime.strptime(game_time_str, "%I:%M %p").replace(
                            year=now.year, month=now.month, day=now.day,
                            tzinfo=ET
                        )
                        hours_to_game = max(0, (game_time - now).total_seconds() / 3600)
                    except Exception:
                        hours_to_game = 12

                if query_type == "game" and selected_game:
                    pplx_context = search_game_context(
                        selected_game.get('away_full', selected_game['away']),
                        selected_game.get('home_full', selected_game['home']),
                        hours_to_game=int(hours_to_game)
                    )
                    # Add late news if close to tipoff
                    if hours_to_game <= 2:
                        late = search_late_news(selected_game['home'])
                        late += search_late_news(selected_game['away'])
                        pplx_context = (pplx_context or "") + late

                    if pplx_context:
                        freestyle_input = analysis_input + pplx_context
                        perplexity_used = True
                elif query_type == "player":
                    # Use parsed player name + auto-matched opponent
                    player_name_search = params.get('name', query.split()[0] if query else "")
                    opp_search = opponent if opponent != 'Unknown' else ''
                    pplx_context = search_player_context(
                        player_name=player_name_search,
                        opponent=opp_search,
                        hours_to_game=int(hours_to_game)
                    )
                    if pplx_context:
                        freestyle_input = analysis_input + pplx_context
                        perplexity_used = True

        if analyze_both or selected_game:
            spinner_text = "Running Freestyle + Perplexity..." if perplexity_used else "Running Freestyle analysis..."
            with st.spinner(spinner_text):
                freestyle = get_claude_analysis(prompt_freestyle, freestyle_input, model)

            with st.spinner("Running Ludi Method analysis..."):
                methodology = get_claude_analysis(prompt_method, analysis_input, model)

            render_analysis_output(freestyle, methodology, show_both=True, perplexity_used=perplexity_used)

            # Save option
            if st.button("💾 Save Analysis"):
                save_analysis(query or "Game Card", freestyle, methodology)
                st.success("Saved!")

        elif analyze_ludi:
            with st.spinner("Running Ludi Method analysis..."):
                methodology = get_claude_analysis(prompt_method, analysis_input, model)

            render_analysis_output("", methodology, show_both=False)

    # Footer with data sources - Lo-Fi Premium Light
    st.markdown("---")

    # Data source badges - Light mode
    st.markdown("""
    <div style="text-align: center; margin-bottom: 12px;">
        <span style="background: rgba(91, 124, 153, 0.08); border: 1px solid #7B94AB; border-radius: 4px;
                    padding: 4px 10px; margin: 3px; font-size: 10px; color: #5B7089; display: inline-block;">Claude AI</span>
        <span style="background: rgba(74, 124, 89, 0.08); border: 1px solid #6B9876; border-radius: 4px;
                    padding: 4px 10px; margin: 3px; font-size: 10px; color: #5B8A69; display: inline-block;">Tank01 API</span>
        <span style="background: rgba(160, 135, 61, 0.08); border: 1px solid #B39443; border-radius: 4px;
                    padding: 4px 10px; margin: 3px; font-size: 10px; color: #806A2F; display: inline-block;">The-Odds-API</span>
        <span style="background: rgba(139, 92, 246, 0.08); border: 1px solid #9B7BC6; border-radius: 4px;
                    padding: 4px 10px; margin: 3px; font-size: 10px; color: #7B5FA6; display: inline-block;">Perplexity AI</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <p style="color: #6B6760; font-size: 11px; text-align: center;">
        Ludi Lite | Research Assistant | Not betting advice<br/>
        <span style="font-size: 9px; color: #8A867F;">We reject "AI Slop" in favor of Human Verification</span>
    </p>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
