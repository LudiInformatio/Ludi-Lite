"""
UI Components for Ludi Lite
Styled output cards inspired by PropsMadness, betting research tools
"""

import streamlit as st

# Color scheme (matching Ludi brand)
COLORS = {
    "dark_navy": "#0F172A",
    "slate": "#1E293B",
    "gold": "#FBBF24",
    "emerald": "#10B981",
    "red": "#EF4444",
    "blue": "#60A5FA",
    "gray": "#94A3B8",
    "white": "#F8FAFC"
}


def indicator(value, thresholds: dict = None, inverse: bool = False):
    """
    Return colored indicator based on value
    thresholds: {"good": 7, "bad": 20} - below good is green, above bad is red
    inverse: if True, lower is better (like rankings)
    """
    if thresholds is None:
        return "⚪"

    good = thresholds.get("good", 10)
    bad = thresholds.get("bad", 20)

    try:
        val = float(value) if not isinstance(value, (int, float)) else value
    except (ValueError, TypeError):
        return "⚪"

    if inverse:
        if val <= good:
            return "🟢"
        elif val >= bad:
            return "🔴"
        else:
            return "🟡"
    else:
        if val >= good:
            return "🟢"
        elif val <= bad:
            return "🔴"
        else:
            return "🟡"


def render_player_card(data: dict):
    """
    Render a player prop card like PropsMadness

    data = {
        "player_name": "Amen Thompson",
        "team": "HOU",
        "opponent": "BOS",
        "prop": "Assists",
        "line": 5.5,
        "odds": -107,
        "direction": "Over",
        "metrics": {
            "L15 Average": {"value": 6.1, "signal": "good"},
            "L15 Hit Rate": {"value": "9/15", "signal": "good"},
            "H2H": {"value": "1/4", "signal": "bad"},
            ...
        },
        "ludi_analysis": {
            "archetype": "SLASHER/PLAYMAKER",
            "opp_scheme": "PAINT_PACK",
            "matchup_grade": "C+",
            "flags": ["30th pace = grind game", "H2H concerning"],
            "verdict": "LEAN UNDER"
        }
    }
    """
    st.markdown(f"""
    <div style="background: {COLORS['slate']}; border-radius: 12px; padding: 20px; margin: 10px 0;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
            <div>
                <h3 style="color: {COLORS['white']}; margin: 0;">{data.get('player_name', 'Player')}</h3>
                <p style="color: {COLORS['gray']}; margin: 5px 0;">{data.get('team', '')} vs {data.get('opponent', '')}</p>
            </div>
            <div style="text-align: right;">
                <span style="background: {COLORS['gold']}; color: {COLORS['dark_navy']}; padding: 5px 12px; border-radius: 20px; font-weight: bold;">
                    {data.get('direction', 'Over')} {data.get('line', '')} {data.get('prop', '')}
                </span>
                <p style="color: {COLORS['emerald']}; margin: 5px 0; font-weight: bold;">{data.get('odds', '')}</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Metrics table
    if "metrics" in data:
        cols = st.columns(2)
        metrics = list(data["metrics"].items())

        for i, (metric_name, metric_data) in enumerate(metrics):
            col = cols[i % 2]
            value = metric_data.get("value", "N/A")
            signal = metric_data.get("signal", "neutral")

            if signal == "good":
                color = COLORS["emerald"]
                icon = "🟢"
            elif signal == "bad":
                color = COLORS["red"]
                icon = "🔴"
            else:
                color = COLORS["gray"]
                icon = "⚪"

            col.markdown(f"""
            <div style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid {COLORS['dark_navy']};">
                <span style="color: {COLORS['gray']};">{metric_name}</span>
                <span style="color: {color}; font-weight: bold;">{icon} {value}</span>
            </div>
            """, unsafe_allow_html=True)

    # Ludi Analysis section
    if "ludi_analysis" in data:
        la = data["ludi_analysis"]
        st.markdown(f"""
        <div style="background: {COLORS['dark_navy']}; border-radius: 8px; padding: 15px; margin-top: 15px;">
            <h4 style="color: {COLORS['gold']}; margin: 0 0 10px 0;">🎯 LUDI ANALYSIS</h4>
            <p style="color: {COLORS['gray']}; margin: 5px 0;"><strong>Archetype:</strong> {la.get('archetype', 'N/A')}</p>
            <p style="color: {COLORS['gray']}; margin: 5px 0;"><strong>vs Scheme:</strong> {la.get('opp_scheme', 'N/A')}</p>
            <p style="color: {COLORS['gray']}; margin: 5px 0;"><strong>Matchup Grade:</strong> {la.get('matchup_grade', 'N/A')}</p>
        </div>
        """, unsafe_allow_html=True)

        # Flags
        if la.get("flags"):
            st.markdown(f"<p style='color: {COLORS['gold']}; font-weight: bold; margin-top: 10px;'>⚠️ FLAGS:</p>", unsafe_allow_html=True)
            for flag in la["flags"]:
                st.markdown(f"<p style='color: {COLORS['gray']}; margin: 2px 0 2px 15px;'>• {flag}</p>", unsafe_allow_html=True)

        # Verdict
        verdict = la.get("verdict", "")
        if verdict:
            verdict_color = COLORS["emerald"] if "OVER" in verdict.upper() else COLORS["red"] if "UNDER" in verdict.upper() else COLORS["gray"]
            st.markdown(f"""
            <div style="margin-top: 15px; padding: 10px; background: {verdict_color}20; border-left: 4px solid {verdict_color}; border-radius: 4px;">
                <p style="color: {verdict_color}; font-weight: bold; margin: 0;">VERDICT: {verdict}</p>
            </div>
            """, unsafe_allow_html=True)


def render_game_matchup_card(data: dict):
    """
    Render a game matchup card with playtype breakdown

    data = {
        "away_team": "DEN",
        "home_team": "NYK",
        "spread": -4.5,
        "total": 221.5,
        "away_record": "5-5 L10",
        "home_record": "7-3 L10",
        "playtype_matchup": [
            {"playtype": "Post Up", "off_rank": 1, "def_rank": 22, "edge": "away"},
            {"playtype": "PnR Ball Handler", "off_rank": 10, "def_rank": 26, "edge": "away"},
            ...
        ],
        "key_advantages": {
            "away": ["Post Up (#1 vs #22)", "PnR Handler (#10 vs #26)"],
            "home": ["Transition (#9 vs #24)", "Spot Up (#1 vs #16)"]
        },
        "ludi_notes": {
            "pace_context": "Both teams 25th-26th pace - SLOW GAME",
            "scheme_matchup": "NYK PERIMETER vs DEN MOTION",
            "flags": ["Jokic post-up dominance", "NYK elite defense L10"],
            "players_to_watch": ["Jokic (post + assists)", "Murray (PnR)", "Brunson (needs ISO)"]
        }
    }
    """
    away = data.get("away_team", "AWAY")
    home = data.get("home_team", "HOME")
    spread = data.get("spread", 0)
    total = data.get("total", 0)

    # Header
    spread_display = f"{home} {spread:+.1f}" if spread != 0 else "PICK"

    st.markdown(f"""
    <div style="background: {COLORS['slate']}; border-radius: 12px; padding: 20px; margin: 10px 0;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div style="text-align: center;">
                <h2 style="color: {COLORS['white']}; margin: 0;">{away}</h2>
                <p style="color: {COLORS['gray']}; margin: 5px 0;">{data.get('away_record', '')}</p>
            </div>
            <div style="text-align: center;">
                <p style="color: {COLORS['gold']}; font-weight: bold; margin: 0;">{spread_display}</p>
                <p style="color: {COLORS['gray']}; margin: 5px 0;">O/U {total}</p>
            </div>
            <div style="text-align: center;">
                <h2 style="color: {COLORS['white']}; margin: 0;">{home}</h2>
                <p style="color: {COLORS['gray']}; margin: 5px 0;">{data.get('home_record', '')}</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Playtype matchup table
    if "playtype_matchup" in data:
        st.markdown(f"<h4 style='color: {COLORS['gold']}; margin-top: 20px;'>PLAYTYPE MATCHUP</h4>", unsafe_allow_html=True)

        st.markdown(f"""
        <div style="display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 2px solid {COLORS['gray']};">
            <span style="color: {COLORS['blue']}; font-weight: bold; width: 80px;">{away} OFF</span>
            <span style="color: {COLORS['gray']}; font-weight: bold; flex: 1; text-align: center;">Playtype</span>
            <span style="color: {COLORS['emerald']}; font-weight: bold; width: 80px; text-align: right;">{home} DEF</span>
        </div>
        """, unsafe_allow_html=True)

        for pt in data["playtype_matchup"]:
            playtype = pt.get("playtype", "")
            off_rank = pt.get("off_rank", "-")
            def_rank = pt.get("def_rank", "-")
            edge = pt.get("edge", "neutral")

            if edge == "away":
                edge_indicator = f"<span style='color: {COLORS['emerald']};'>🟢 EDGE</span>"
            elif edge == "home":
                edge_indicator = f"<span style='color: {COLORS['red']};'>🔴 TOUGH</span>"
            else:
                edge_indicator = f"<span style='color: {COLORS['gray']};'>⚪</span>"

            st.markdown(f"""
            <div style="display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid {COLORS['dark_navy']};">
                <span style="color: {COLORS['blue']}; width: 80px;">#{off_rank}</span>
                <span style="color: {COLORS['white']}; flex: 1; text-align: center;">{playtype}</span>
                <span style="color: {COLORS['emerald']}; width: 50px; text-align: center;">#{def_rank}</span>
                <span style="width: 80px; text-align: right;">{edge_indicator}</span>
            </div>
            """, unsafe_allow_html=True)

    # Key advantages
    if "key_advantages" in data:
        col1, col2 = st.columns(2)

        with col1:
            st.markdown(f"<h5 style='color: {COLORS['blue']};'>{away} ADVANTAGES</h5>", unsafe_allow_html=True)
            for adv in data["key_advantages"].get("away", []):
                st.markdown(f"<p style='color: {COLORS['gray']}; margin: 2px 0;'>• {adv}</p>", unsafe_allow_html=True)

        with col2:
            st.markdown(f"<h5 style='color: {COLORS['emerald']};'>{home} ADVANTAGES</h5>", unsafe_allow_html=True)
            for adv in data["key_advantages"].get("home", []):
                st.markdown(f"<p style='color: {COLORS['gray']}; margin: 2px 0;'>• {adv}</p>", unsafe_allow_html=True)

    # Ludi notes
    if "ludi_notes" in data:
        ln = data["ludi_notes"]
        st.markdown(f"""
        <div style="background: {COLORS['dark_navy']}; border-radius: 8px; padding: 15px; margin-top: 20px;">
            <h4 style="color: {COLORS['gold']}; margin: 0 0 10px 0;">🎯 LUDI GAME NOTES</h4>
        </div>
        """, unsafe_allow_html=True)

        if ln.get("pace_context"):
            st.markdown(f"<p style='color: {COLORS['gray']};'><strong>Pace:</strong> {ln['pace_context']}</p>", unsafe_allow_html=True)

        if ln.get("scheme_matchup"):
            st.markdown(f"<p style='color: {COLORS['gray']};'><strong>Schemes:</strong> {ln['scheme_matchup']}</p>", unsafe_allow_html=True)

        if ln.get("flags"):
            st.markdown(f"<p style='color: {COLORS['gold']}; font-weight: bold;'>⚠️ FLAGS:</p>", unsafe_allow_html=True)
            for flag in ln["flags"]:
                st.markdown(f"<p style='color: {COLORS['gray']}; margin: 2px 0 2px 15px;'>• {flag}</p>", unsafe_allow_html=True)

        if ln.get("players_to_watch"):
            st.markdown(f"<p style='color: {COLORS['emerald']}; font-weight: bold;'>👀 PLAYERS TO WATCH:</p>", unsafe_allow_html=True)
            for player in ln["players_to_watch"]:
                st.markdown(f"<p style='color: {COLORS['gray']}; margin: 2px 0 2px 15px;'>• {player}</p>", unsafe_allow_html=True)


def render_comparison_header():
    """Render the side-by-side comparison header"""
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"""
        <div style="background: {COLORS['blue']}20; border: 2px solid {COLORS['blue']}; border-radius: 8px; padding: 10px; text-align: center;">
            <h3 style="color: {COLORS['blue']}; margin: 0;">🤖 FREESTYLE</h3>
            <p style="color: {COLORS['gray']}; margin: 5px 0 0 0; font-size: 12px;">Raw AI - No methodology</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div style="background: {COLORS['emerald']}20; border: 2px solid {COLORS['emerald']}; border-radius: 8px; padding: 10px; text-align: center;">
            <h3 style="color: {COLORS['emerald']}; margin: 0;">🎯 LUDI METHOD</h3>
            <p style="color: {COLORS['gray']}; margin: 5px 0 0 0; font-size: 12px;">S.A.V.A.G.E. framework applied</p>
        </div>
        """, unsafe_allow_html=True)

