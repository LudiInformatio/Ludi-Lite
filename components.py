"""
Context Cards for Ludi Lite — Light Theme
Compact data snapshot cards shown between user input and AI analysis panels.
Design: Intentional minimalism. One card per query. Research note, not betting terminal.
"""

import streamlit as st
import html


def _status_badge(status: str) -> str:
    """Return an inline HTML pill badge for player injury status."""
    s = (status or "Active").upper()
    if s in ("OUT", "SUSPENDED"):
        bg, color = "rgba(196, 30, 58, 0.10)", "#C41E3A"
    elif s in ("GTD", "QUESTIONABLE", "DAY-TO-DAY", "DOUBTFUL"):
        bg, color = "rgba(198, 163, 79, 0.10)", "#8E7022"
    else:  # Active
        bg, color = "rgba(74, 124, 89, 0.10)", "#4A7C59"
    label = s if s in ("OUT", "GTD") else status.title()
    return (
        f'<span style="background:{bg}; color:{color}; padding:3px 10px; '
        f'border-radius:9999px; font-family:Inter,sans-serif; font-size:11px; '
        f'font-weight:600; letter-spacing:0.04em;">{html.escape(label)}</span>'
    )


def render_game_context_card(data: dict) -> None:
    """
    Render a compact game context card with matchup ratings.
    Shown between the user's game selection and the AI analysis panels.
    """
    if not data:
        return

    away = html.escape(str(data.get("away", "")))
    home = html.escape(str(data.get("home", "")))
    if not away or not home:
        return

    time_str = html.escape(str(data.get("time", "")))
    spread = html.escape(str(data.get("spread", "PK")))
    total = data.get("total")
    total_str = f"O/U {total}" if total else ""

    # Matchup ratings
    home_r = data.get("home_rating") or {}
    away_r = data.get("away_rating") or {}

    away_matchup = ""
    if away_r:
        away_matchup = (
            f'<div style="font-family:Inter,sans-serif; font-size:13px; color:#1A1A1A; margin-top:4px;">'
            f'{away} vs {home} DEF &nbsp;{away_r.get("emoji","")} '
            f'<span style="color:#7B7568;">{away_r.get("label","")} (#{away_r.get("rank","")})</span>'
            f'</div>'
        )
    home_matchup = ""
    if home_r:
        home_matchup = (
            f'<div style="font-family:Inter,sans-serif; font-size:13px; color:#1A1A1A; margin-top:2px;">'
            f'{home} vs {away} DEF &nbsp;{home_r.get("emoji","")} '
            f'<span style="color:#7B7568;">{home_r.get("label","")} (#{home_r.get("rank","")})</span>'
            f'</div>'
        )

    # Vacuum section (only if present)
    vacuum_html = ""
    vacuum_text = (data.get("vacuum_text") or "").strip()
    if vacuum_text:
        # Show a brief note, not the full prompt block
        clean = html.escape(vacuum_text.replace("=== USAGE VACUUM ANALYSIS (S.A.V.A.G.E. - calculated from Tank01 stats) ===", "").strip())
        clean = clean.replace("=== USAGE VACUUM ANALYSIS (S.A.V.A.G.E.) ===", "").strip()
        if clean:
            vacuum_html = (
                f'<div style="margin-top:10px; padding-top:8px; border-top:1px solid #E6E4DD;">'
                f'<div style="font-family:Inter,sans-serif; font-size:11px; color:#7B7568; '
                f'text-transform:uppercase; letter-spacing:0.08em; font-weight:600; margin-bottom:4px;">Usage Vacuum</div>'
                f'<div style="font-family:Inter,sans-serif; font-size:12px; color:#1A1A1A; '
                f'white-space:pre-wrap; line-height:1.5;">{clean}</div>'
                f'</div>'
            )

    # Build the time suffix
    time_suffix = f' &middot; {time_str}' if time_str else ''

    st.markdown(f"""
    <div style="
        background: #FFFFFF;
        border: 1px solid rgba(0,0,0,0.03);
        border-top: 2px solid #C6A34F;
        border-radius: 12px;
        padding: 20px 24px;
        margin: 16px 0;
        box-shadow: 0 1px 2px rgba(0,0,0,0.04), 0 4px 8px rgba(0,0,0,0.02), 0 12px 24px rgba(0,0,0,0.02);
    ">
        <div style="font-family:'Libre Baskerville',serif; font-size:16px; color:#1A1A1A; font-weight:700;">
            {away} @ {home}{time_suffix}
        </div>
        <div style="font-family:Inter,sans-serif; font-size:13px; color:#7B7568; margin-top:6px;">
            {home} {spread} &nbsp;&middot;&nbsp; {total_str}
        </div>
        <div style="margin-top:10px;">
            {away_matchup}
            {home_matchup}
        </div>
        {vacuum_html}
    </div>
    """, unsafe_allow_html=True)


def render_player_context_card(data: dict) -> None:
    """
    Render a compact player context card with stats and matchup rating.
    Shown between the user's player query and the AI analysis panels.
    """
    if not data:
        return

    name = html.escape(str(data.get("name", "")))
    if not name:
        return

    team = html.escape(str(data.get("team", "")))
    opponent = html.escape(str(data.get("opponent", "")))
    status = data.get("status", "Active")
    badge = _status_badge(status)

    # Matchup line
    opp_r = data.get("opp_rating") or {}
    matchup_html = ""
    if opp_r and opponent:
        matchup_html = (
            f'<div style="font-family:Inter,sans-serif; font-size:13px; color:#1A1A1A; margin-top:8px;">'
            f'vs {opponent} DEF &nbsp;{opp_r.get("emoji","")} '
            f'<span style="color:#7B7568;">{opp_r.get("label","")} (#{opp_r.get("rank","")})</span>'
            f'</div>'
        )

    # Total line
    total = data.get("total")
    total_html = ""
    if total:
        total_html = (
            f'<div style="font-family:Inter,sans-serif; font-size:13px; color:#7B7568; margin-top:2px;">'
            f'O/U {total}</div>'
        )

    # Stats line
    stats = data.get("stats") or {}
    stats_html = ""
    if stats:
        parts = []
        if stats.get("pts"):
            parts.append(f'{stats["pts"]} PPG')
        if stats.get("ast"):
            parts.append(f'{stats["ast"]} APG')
        if stats.get("reb"):
            parts.append(f'{stats["reb"]} RPG')
        if parts:
            stats_html = (
                f'<div style="font-family:Inter,sans-serif; font-size:13px; color:#7B7568; margin-top:8px;">'
                f'{" &nbsp;&middot;&nbsp; ".join(parts)}'
                f'</div>'
            )

    # Vacuum section
    vacuum_html = ""
    vacuum_text = (data.get("vacuum_text") or "").strip()
    if vacuum_text:
        clean = html.escape(vacuum_text.replace("=== USAGE VACUUM ANALYSIS (S.A.V.A.G.E.) ===", "").strip())
        clean = clean.replace("=== USAGE VACUUM ANALYSIS (S.A.V.A.G.E. - calculated from Tank01 stats) ===", "").strip()
        if clean:
            vacuum_html = (
                f'<div style="margin-top:10px; padding-top:8px; border-top:1px solid #E6E4DD;">'
                f'<div style="font-family:Inter,sans-serif; font-size:11px; color:#7B7568; '
                f'text-transform:uppercase; letter-spacing:0.08em; font-weight:600; margin-bottom:4px;">Usage Vacuum</div>'
                f'<div style="font-family:Inter,sans-serif; font-size:12px; color:#1A1A1A; '
                f'white-space:pre-wrap; line-height:1.5;">{clean}</div>'
                f'</div>'
            )

    # Build matchup suffix for header
    matchup_suffix = f' &middot; {team} vs {opponent}' if team and opponent else (f' &middot; {team}' if team else '')

    st.markdown(f"""
    <div style="
        background: #FFFFFF;
        border: 1px solid rgba(0,0,0,0.03);
        border-top: 2px solid #C6A34F;
        border-radius: 12px;
        padding: 20px 24px;
        margin: 16px 0;
        box-shadow: 0 1px 2px rgba(0,0,0,0.04), 0 4px 8px rgba(0,0,0,0.02), 0 12px 24px rgba(0,0,0,0.02);
    ">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div style="font-family:'Libre Baskerville',serif; font-size:16px; color:#1A1A1A; font-weight:700;">
                {name.upper()}{matchup_suffix}
            </div>
            {badge}
        </div>
        {stats_html}
        {matchup_html}
        {total_html}
        {vacuum_html}
    </div>
    """, unsafe_allow_html=True)
