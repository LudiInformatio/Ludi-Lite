"""
Context Cards for Ludi Lite — Private Study Theme
Compact data snapshot cards shown between user input and AI analysis panels.
Design: PropsMadness-inspired editorial layout with gold left-border accent.
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


def _matchup_pill(rating: dict) -> str:
    """Return an inline HTML pill badge for a matchup rating (traffic-light style).

    Args:
        rating: Dict with keys "emoji", "label", "rank".
                label determines color: Favorable=green, Neutral=gold, Tough=red.
    Returns:
        HTML string for the pill, or empty string if rating is falsy/empty.
    """
    if not rating:
        return ""

    emoji = rating.get("emoji", "")
    label = rating.get("label", "")
    rank = rating.get("rank", "")

    if not label:
        return ""

    # Pick color scheme based on label text
    label_lower = label.lower()
    if label_lower == "favorable":
        bg, color = "rgba(74, 124, 89, 0.10)", "#4A7C59"
    elif label_lower == "tough":
        bg, color = "rgba(196, 30, 58, 0.10)", "#C41E3A"
    else:  # Neutral or anything else
        bg, color = "rgba(198, 163, 79, 0.10)", "#8E7022"

    # Build content: "{emoji} {label} #{rank}"
    content_parts = []
    if emoji:
        content_parts.append(emoji)
    content_parts.append(html.escape(str(label)))
    if rank != "" and rank is not None:
        content_parts.append(f"#{html.escape(str(rank))}")
    content = " ".join(content_parts)

    return (
        f'<span style="background:{bg}; color:{color}; padding:3px 10px; '
        f'border-radius:9999px; font-family:Inter,sans-serif; font-size:11px; '
        f'font-weight:600; display:inline-block;">{content}</span>'
    )


def _prop_row(prop: dict) -> str:
    """Return an inline HTML flex row for a single prop line.

    Args:
        prop: Dict with keys "player", "stat", "line", and optionally
              "fd_odds" and "dk_odds".
    Returns:
        HTML string for the prop row.
    """
    if not prop:
        return ""

    player = html.escape(str(prop.get("player", "")))
    stat = html.escape(str(prop.get("stat", "")))
    line = prop.get("line", "")
    fd_odds = prop.get("fd_odds")
    dk_odds = prop.get("dk_odds")

    if not player:
        return ""

    # Left side: "Player STAT Line"
    # stat rendered in stone color, player and line in ink
    line_str = html.escape(str(line)) if line != "" and line is not None else ""
    left = f'{player} <span style="color:#7B7568;">{stat}</span>'
    if line_str:
        left += f' {line_str}'

    # Right side: odds from available books
    odds_parts = []
    if fd_odds is not None:
        # Format with explicit +/- sign if integer
        try:
            fd_display = f"{int(fd_odds):+d}"
        except (ValueError, TypeError):
            fd_display = html.escape(str(fd_odds))
        odds_parts.append(f"FD {fd_display}")
    if dk_odds is not None:
        try:
            dk_display = f"{int(dk_odds):+d}"
        except (ValueError, TypeError):
            dk_display = html.escape(str(dk_odds))
        odds_parts.append(f"DK {dk_display}")

    right_html = ""
    if odds_parts:
        right_text = " / ".join(odds_parts)
        right_html = (
            f'<span style="font-family:Inter,sans-serif; font-size:12px; '
            f'color:#7B7568; white-space:nowrap;">{right_text}</span>'
        )

    return (
        f'<div style="display:flex; justify-content:space-between; align-items:baseline; '
        f'padding:4px 0; font-family:Inter,sans-serif; font-size:13px; color:#1A1A1A;">'
        f'<span>{left}</span>{right_html}</div>'
    )


# ---------------------------------------------------------------------------
# Shared constants for card container style and section label style
# ---------------------------------------------------------------------------

_CARD_STYLE = (
    "background:#FFFFFF; "
    "border-left:4px solid #C6A34F; "
    "border-radius:0 12px 12px 0; "
    "padding:20px 24px; "
    "margin:16px 0; "
    "box-shadow:0 1px 2px rgba(0,0,0,0.04), 0 4px 8px rgba(0,0,0,0.02), 0 12px 24px rgba(0,0,0,0.02);"
)

_SECTION_LABEL = (
    "font-family:Inter,sans-serif; font-size:11px; color:#7B7568; "
    "text-transform:uppercase; letter-spacing:0.08em; font-weight:600;"
)

_DIVIDER = (
    '<div style="border-top:1px solid #E6E4DD; margin:10px 0;"></div>'
)


def _clean_vacuum_text(raw: str) -> str:
    """Strip the S.A.V.A.G.E. header banners and whitespace from vacuum text,
    then html-escape the remainder. Returns empty string if nothing useful."""
    text = (raw or "").strip()
    if not text:
        return ""
    # Remove known header banners
    for banner in (
        "=== USAGE VACUUM ANALYSIS (S.A.V.A.G.E. - calculated from Tank01 stats) ===",
        "=== USAGE VACUUM ANALYSIS (S.A.V.A.G.E.) ===",
    ):
        text = text.replace(banner, "")
    text = text.strip()
    return html.escape(text) if text else ""


def _build_vacuum_section(vacuum_text: str) -> str:
    """Return USAGE VACUUM section HTML (with leading divider), or empty string."""
    clean = _clean_vacuum_text(vacuum_text)
    if not clean:
        return ""
    return (
        f'{_DIVIDER}'
        f'<div style="{_SECTION_LABEL} margin-bottom:4px;">Usage Vacuum</div>'
        f'<div style="font-family:Inter,sans-serif; font-size:12px; color:#1A1A1A; '
        f'white-space:pre-wrap; line-height:1.5;">{clean}</div>'
    )


# ---------------------------------------------------------------------------
# Main render functions
# ---------------------------------------------------------------------------

def render_game_context_card(data: dict) -> None:
    """Render a PropsMadness-inspired game context card.

    Sections (shown conditionally):
        MATCHUP SNAPSHOT header · teams · lines · matchup ratings ·
        TOP PROPS · USAGE VACUUM
    """
    if not data:
        return

    away = html.escape(str(data.get("away", "")))
    home = html.escape(str(data.get("home", "")))
    if not away or not home:
        return

    away_full = html.escape(str(data.get("away_full", "")))
    home_full = html.escape(str(data.get("home_full", "")))
    time_str = html.escape(str(data.get("time", "")))
    spread = html.escape(str(data.get("spread", "PK")))
    total = data.get("total")
    home_ml = data.get("home_ml")
    away_ml = data.get("away_ml")

    # -- Header row: section label left, time right --------------------------
    time_html = (
        f'<span style="font-family:Inter,sans-serif; font-size:12px; '
        f'color:#7B7568;">{time_str}</span>'
    ) if time_str else ""

    header = (
        f'<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">'
        f'<span style="{_SECTION_LABEL}">Matchup Snapshot</span>'
        f'{time_html}'
        f'</div>'
    )

    # -- Teams ---------------------------------------------------------------
    teams = (
        f'<div style="font-family:\'Libre Baskerville\',serif; font-size:18px; '
        f'color:#1A1A1A; font-weight:700;">{away} @ {home}</div>'
    )
    # Full names line (only if at least one is provided)
    full_names = ""
    if away_full or home_full:
        full_names = (
            f'<div style="font-family:Inter,sans-serif; font-size:12px; '
            f'color:#7B7568; margin-top:2px;">{away_full} at {home_full}</div>'
        )

    # -- Lines ---------------------------------------------------------------
    total_str = f"O/U {total}" if total else ""
    spread_line_parts = [p for p in [f"{home} {spread}", total_str] if p]
    spread_line = " &middot; ".join(spread_line_parts)
    lines_html = (
        f'<div style="font-family:Inter,sans-serif; font-size:13px; '
        f'color:#7B7568; margin-top:6px;">{spread_line}</div>'
    ) if spread_line else ""

    # Moneyline row
    ml_html = ""
    if away_ml is not None or home_ml is not None:
        ml_parts = []
        if away_ml is not None:
            try:
                ml_parts.append(f"{away} {int(away_ml):+d}")
            except (ValueError, TypeError):
                ml_parts.append(f"{away} {html.escape(str(away_ml))}")
        if home_ml is not None:
            try:
                ml_parts.append(f"{home} {int(home_ml):+d}")
            except (ValueError, TypeError):
                ml_parts.append(f"{home} {html.escape(str(home_ml))}")
        ml_html = (
            f'<div style="font-family:Inter,sans-serif; font-size:13px; '
            f'color:#7B7568; margin-top:2px;">ML: {" / ".join(ml_parts)}</div>'
        )

    # -- Matchup Ratings (always show divider before if any rating exists) ---
    home_r = data.get("home_rating") or {}
    away_r = data.get("away_rating") or {}
    ratings_html = ""
    if away_r or home_r:
        ratings_html = _DIVIDER
        if away_r:
            pill = _matchup_pill(away_r)
            ratings_html += (
                f'<div style="font-family:Inter,sans-serif; font-size:13px; '
                f'color:#1A1A1A; margin-bottom:4px;">'
                f'{away} offense vs {home} DEF &nbsp;{pill}</div>'
            )
        if home_r:
            pill = _matchup_pill(home_r)
            ratings_html += (
                f'<div style="font-family:Inter,sans-serif; font-size:13px; '
                f'color:#1A1A1A;">'
                f'{home} offense vs {away} DEF &nbsp;{pill}</div>'
            )

    # -- Top Props -----------------------------------------------------------
    top_props = data.get("top_props") or []
    props_html = ""
    if top_props:
        rows = "".join(_prop_row(p) for p in top_props)
        props_html = (
            f'{_DIVIDER}'
            f'<div style="{_SECTION_LABEL} margin-bottom:4px;">Top Props</div>'
            f'{rows}'
        )

    # -- Usage Vacuum --------------------------------------------------------
    vacuum_html = _build_vacuum_section(data.get("vacuum_text", ""))

    # -- Assemble card -------------------------------------------------------
    st.markdown(
        f'<div style="{_CARD_STYLE}">'
        f'{header}'
        f'{teams}'
        f'{full_names}'
        f'{lines_html}'
        f'{ml_html}'
        f'{ratings_html}'
        f'{props_html}'
        f'{vacuum_html}'
        f'</div>',
        unsafe_allow_html=True,
    )


def render_player_context_card(data: dict) -> None:
    """Render a PropsMadness-inspired player context card.

    Sections (shown conditionally):
        PROP CHECK header · player name · context · season stats ·
        PROP LINE · matchup · USAGE VACUUM
    """
    if not data:
        return

    name = html.escape(str(data.get("name", "")))
    if not name:
        return

    team = html.escape(str(data.get("team", "")))
    opponent = html.escape(str(data.get("opponent", "")))
    time_str = html.escape(str(data.get("time", "")))
    status = data.get("status", "Active")
    badge = _status_badge(status)

    # -- Header row: label left, status badge right --------------------------
    header = (
        f'<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">'
        f'<span style="{_SECTION_LABEL}">Prop Check</span>'
        f'{badge}'
        f'</div>'
    )

    # -- Player name (uppercased, Libre Baskerville) -------------------------
    name_html = (
        f'<div style="font-family:\'Libre Baskerville\',serif; font-size:18px; '
        f'color:#1A1A1A; font-weight:700;">{name.upper()}</div>'
    )

    # -- Context line: "TEAM vs OPP · 7:30 PM" ------------------------------
    ctx_parts = []
    if team and opponent:
        ctx_parts.append(f"{team} vs {opponent}")
    elif team:
        ctx_parts.append(team)
    if time_str:
        ctx_parts.append(time_str)
    context_html = ""
    if ctx_parts:
        context_html = (
            f'<div style="font-family:Inter,sans-serif; font-size:13px; '
            f'color:#7B7568; margin-top:2px;">'
            f'{" &middot; ".join(ctx_parts)}</div>'
        )

    # -- Season stats: "26.8 PPG · 12.4 RPG · 9.1 APG" ---------------------
    stats = data.get("stats") or {}
    stats_html = ""
    if stats:
        # Order: PTS, REB, AST (standard box-score order)
        stat_map = [("pts", "PPG"), ("reb", "RPG"), ("ast", "APG")]
        parts = [
            f"{html.escape(str(stats[k]))} {label}"
            for k, label in stat_map
            if stats.get(k)
        ]
        if parts:
            stats_html = (
                f'<div style="font-family:Inter,sans-serif; font-size:13px; '
                f'color:#7B7568; margin-top:4px;">'
                f'{" &middot; ".join(parts)}</div>'
            )

    # -- Divider before prop line / matchup ----------------------------------
    # Always show if there is any content below the stats block
    opp_r = data.get("opp_rating") or {}
    stat_focus = data.get("stat_focus", "")
    line = data.get("line")
    spread = data.get("spread")
    total = data.get("total")
    vacuum_text = data.get("vacuum_text", "")

    has_below = stat_focus or line or opp_r or spread or total or vacuum_text
    first_divider = _DIVIDER if has_below else ""

    # -- Prop line section: "Points Over 26.5" + matchup pill ----------------
    prop_line_html = ""
    if stat_focus and line is not None and str(line):
        safe_focus = html.escape(str(stat_focus))
        safe_line = html.escape(str(line))
        pill = _matchup_pill(opp_r)
        pill_part = f" &nbsp;{pill}" if pill else ""
        prop_line_html = (
            f'<div style="{_SECTION_LABEL} margin-bottom:4px;">Prop Line</div>'
            f'<div style="font-family:Inter,sans-serif; font-size:14px; '
            f'color:#1A1A1A; margin-bottom:2px;">'
            f'{safe_focus} Over {safe_line}{pill_part}</div>'
        )

    # -- Matchup section (only when no prop line already showed pill) --------
    matchup_html = ""
    if opponent and (opp_r or spread is not None or total is not None):
        # If prop line section already exists, add a divider before matchup
        matchup_divider = _DIVIDER if prop_line_html else ""
        matchup_html = matchup_divider
        if opp_r and not prop_line_html:
            # Only show standalone matchup pill if prop line didn't render it
            pill = _matchup_pill(opp_r)
            matchup_html += (
                f'<div style="font-family:Inter,sans-serif; font-size:13px; '
                f'color:#1A1A1A; margin-bottom:2px;">'
                f'vs {opponent} DEF &nbsp;{pill}</div>'
            )
        elif opp_r and prop_line_html:
            # Prop line showed the pill already; show a simpler matchup ref
            pass
        # Spread + total line
        game_parts = []
        if spread is not None:
            game_parts.append(html.escape(str(spread)))
        if total is not None:
            game_parts.append(f"O/U {html.escape(str(total))}")
        if game_parts:
            matchup_html += (
                f'<div style="font-family:Inter,sans-serif; font-size:13px; '
                f'color:#7B7568; margin-top:2px;">'
                f'{" &middot; ".join(game_parts)}</div>'
            )

    # -- Usage Vacuum --------------------------------------------------------
    vacuum_html = _build_vacuum_section(vacuum_text)

    # -- Assemble card -------------------------------------------------------
    st.markdown(
        f'<div style="{_CARD_STYLE}">'
        f'{header}'
        f'{name_html}'
        f'{context_html}'
        f'{stats_html}'
        f'{first_divider}'
        f'{prop_line_html}'
        f'{matchup_html}'
        f'{vacuum_html}'
        f'</div>',
        unsafe_allow_html=True,
    )
