"""
Usage Bump Calculator for Ludi Lite
Based on Ludi-Bot's proven S.A.V.A.G.E. methodology (Module E: The Calibrator).

v2 — Smart vacuum detection:
- Uses gamesPlayed ratio to detect long-term injuries (vacuum already absorbed)
- Cross-references TRADE_DEADLINE_OVERRIDES for just-traded players
- Position-aware beneficiary matching
- Partial vacuum scaling (not binary on/off)
"""

from typing import Dict, List, Optional
from datetime import datetime
from tank01_client import get_team_roster


def detect_trade_and_get_stats(player_name: str) -> Dict:
    """
    Detect if player was traded and get stats for their current team.
    
    Uses BDL game logs to detect team changes. If player has played for
    2+ teams in recent games, they were traded. Filters to most recent
    team's games to get accurate post-trade averages.
    
    Returns:
        {
            "traded": True/False,
            "no_data": True/False,
            "teams": ["LAL", "MIL"],  # if traded
            "recent_team": "MIL",       # current team
            "avg_pts": 15.2,           # post-trade average
            "avg_reb": 5.1,
            "avg_ast": 3.4,
            "games_played": 8
        }
    """
    try:
        from bdl_client import _get_client, get_recent_game_logs
        
        client = _get_client()
        if not client.api_key:
            return {"traded": False, "no_data": False}
        
        player_id = client.map_player_id(player_name)
        if not player_id:
            return {"traded": False, "no_data": True}
        
        logs = get_recent_game_logs(player_id, last_n=30)
        if not logs:
            return {"traded": False, "no_data": True}
        
        cutoff_date = "2026-01-15"
        recent_logs = [g for g in logs if g.get("date", "") >= cutoff_date]
        if not recent_logs:
            recent_logs = logs[:10]
        
        teams = list(set(g.get("team", "") for g in recent_logs if g.get("team")))
        teams = [t for t in teams if t]

        if len(teams) < 2:
            # Game logs show one team — but player may have been traded and not played yet.
            # Cross-check BDL player record: if current team differs from log team → traded + injured.
            log_team = teams[0] if teams else ""
            try:
                current_player = client.get_player_by_id(player_id)
                current_team = (current_player.get("team") or {}).get("abbreviation", "")
                if current_team and log_team and current_team != log_team:
                    return {"traded": True, "no_data": True,
                            "teams": [log_team, current_team], "recent_team": current_team,
                            "note": "traded_not_played"}
            except Exception:
                pass
            return {"traded": False, "no_data": False, "teams": teams}

        # Find most recent team by date (logs already sorted newest-first)
        most_recent_team = next(
            (g.get("team") for g in recent_logs if g.get("team")), ""
        )
        if not most_recent_team:
            return {"traded": True, "no_data": True}
        
        team_logs = [g for g in recent_logs if g.get("team") == most_recent_team]
        if not team_logs:
            return {"traded": True, "no_data": True}
        
        def safe_avg(key):
            values = [g.get(key, 0) for g in team_logs if g.get(key) is not None]
            return sum(values) / len(values) if values else 0
        
        return {
            "traded": True,
            "no_data": False,
            "teams": teams,
            "recent_team": most_recent_team,
            "avg_pts": round(safe_avg("pts"), 1),
            "avg_reb": round(safe_avg("reb"), 1),
            "avg_ast": round(safe_avg("ast"), 1),
            "games_played": len(team_logs)
        }
    
    except Exception:
        return {"traded": False, "no_data": False}


# --- Core adjustment factors (from Ludi-Bot Module E) ---
PROMOTION_MINUTES = 8       # Baseline extra minutes when backup becomes starter
HIGH_PACE_BOOST = 1.03      # O/U > 238
LOW_PACE_DECLINE = 0.97     # O/U < 218

# --- Smart vacuum thresholds ---
MIN_GAMES_FOR_VACUUM = 10          # Must have played ≥10 games to create a vacuum
FULL_VACUUM_THRESHOLD = 0.75       # Played >75% of team games → full vacuum
ABSORBED_THRESHOLD = 0.50          # Played <50% of team games → vacuum absorbed
MIN_CONTRIBUTION_MPG = 15          # Player must average ≥15 MPG to create meaningful vacuum
MIN_ROTATION_MPG = 12              # Beneficiary must average ≥12 MPG to absorb vacuum

# Long-term injury keywords — if description matches, more likely absorbed
LONG_TERM_KEYWORDS = [
    "acl", "achilles", "torn", "surgery", "season-ending", "season ending",
    "indefinitely", "fractured", "broken", "out for season", "out for the season",
]


def _get_trade_overrides() -> dict:
    """Load TRADE_DEADLINE_OVERRIDES from season_context (lazy to avoid circular imports)."""
    try:
        from season_context import TRADE_DEADLINE_OVERRIDES
        return TRADE_DEADLINE_OVERRIDES
    except ImportError:
        return {}


def _estimate_team_games(roster: list) -> int:
    """
    Estimate how many games the team has played this season.
    Uses the max gamesPlayed among all roster players as proxy.
    """
    max_gp = 0
    for p in roster:
        gp = int(p.get('stats', {}).get('gamesPlayed', 0) or 0)
        if gp > max_gp:
            max_gp = gp
    return max_gp


def _classify_vacuum(
    out_player: dict,
    team_games: int,
    roster: list,
) -> Dict:
    """
    Classify whether a player's absence creates an active vacuum.

    Returns:
        {
            "status": "active" | "partial" | "absorbed" | "skip",
            "reason": str,         # Human-readable explanation
            "scale": float,        # 0.0 to 1.0 — multiplier on the boost
        }
    """
    stats = out_player.get('stats', {})
    name = out_player['name']
    gp = int(stats.get('gamesPlayed', 0) or 0)
    mpg = float(stats.get('mins', 0) or 0)
    injury = out_player.get('injury', {})
    injury_desc = (injury.get('description') or '').lower()

    # --- Check 1: Trade detection via BDL logs ---
    # Use BDL to detect if player was recently traded and has limited games for new team
    trade_info = detect_trade_and_get_stats(name)
    if trade_info.get("traded"):
        if trade_info.get("no_data"):
            return {
                "status": "skip",
                "reason": f"{name} recently traded — no games data for new team yet",
                "scale": 0.0,
            }
        games_for_new_team = trade_info.get("games_played", 0)
        if games_for_new_team < 5:
            return {
                "status": "skip",
                "reason": f"{name} recently traded — only {games_for_new_team} games for {trade_info.get('recent_team', 'new team')}",
                "scale": 0.0,
            }
        # Player has enough games for new team - use post-trade stats
        # (continue to vacuum calculation but note the trade)

    # --- Check 2: Minimum games played ---
    if gp < MIN_GAMES_FOR_VACUUM:
        return {
            "status": "skip",
            "reason": f"{name} has played only {gp} games — minimal contribution to absorb",
            "scale": 0.0,
        }

    # --- Check 3: Low-minutes player (bench warmer, not meaningful vacuum) ---
    if mpg < MIN_CONTRIBUTION_MPG:
        return {
            "status": "skip",
            "reason": f"{name} averages {mpg:.1f} MPG — not a significant usage source",
            "scale": 0.0,
        }

    # --- Check 4: Games-played ratio vs team total ---
    if team_games > 0:
        gp_ratio = gp / team_games
    else:
        gp_ratio = 1.0  # Can't determine, assume active

    # Long-term injury keyword check (lower the ratio threshold)
    has_long_term_keyword = any(kw in injury_desc for kw in LONG_TERM_KEYWORDS)

    if gp_ratio < ABSORBED_THRESHOLD or (has_long_term_keyword and gp_ratio < FULL_VACUUM_THRESHOLD):
        games_missed = team_games - gp
        return {
            "status": "absorbed",
            "reason": f"{name} has missed ~{games_missed} games — team already adjusted",
            "scale": 0.0,
        }

    if gp_ratio >= FULL_VACUUM_THRESHOLD:
        return {
            "status": "active",
            "reason": f"{name} played {gp}/{team_games} games — recent absence, full vacuum",
            "scale": 1.0,
        }

    # Partial vacuum: scale linearly between thresholds
    scale = (gp_ratio - ABSORBED_THRESHOLD) / (FULL_VACUUM_THRESHOLD - ABSORBED_THRESHOLD)
    scale = round(max(0.0, min(1.0, scale)), 2)
    return {
        "status": "partial",
        "reason": f"{name} played {gp}/{team_games} games — partial vacuum ({int(scale * 100)}% weight)",
        "scale": scale,
    }


def _find_beneficiaries(
    out_player: dict,
    roster: list,
    max_beneficiaries: int = 2,
) -> list:
    """
    Find the best beneficiaries when a player goes out.
    Prefers same-position players, then falls back to highest-minutes.
    """
    out_pos = (out_player.get('position') or '').upper()
    candidates = []

    for p in roster:
        if p['name'] == out_player['name']:
            continue

        # Skip injured/suspended
        injury = p.get('injury', {})
        desig = (injury.get('designation') or '').upper()
        if desig in ['OUT', 'DOUBTFUL', 'SUSPENDED', 'INACTIVE']:
            continue

        stats = p.get('stats', {})
        if not stats:
            continue

        p_mins = float(stats.get('mins', 0) or 0)
        if p_mins < MIN_ROTATION_MPG:
            continue

        p_pos = (p.get('position') or '').upper()
        # Position match score: exact match = 2, partial overlap = 1, none = 0
        pos_score = 0
        if out_pos and p_pos:
            if p_pos == out_pos:
                pos_score = 2
            elif any(c in p_pos for c in out_pos) or any(c in out_pos for c in p_pos):
                # e.g., "SG" overlaps with "SG-SF", or "F" in "SF"
                pos_score = 1

        candidates.append({
            'name': p['name'],
            'position': p_pos,
            'pos_score': pos_score,
            'mins': p_mins,
            'pts': float(stats.get('pts', 0) or 0),
            'ast': float(stats.get('ast', 0) or 0),
            'reb': float(stats.get('reb', 0) or 0),
        })

    if not candidates:
        return []

    # Sort: position match first, then by minutes
    candidates.sort(key=lambda x: (x['pos_score'], x['mins']), reverse=True)
    return candidates[:max_beneficiaries]


def calculate_promotion_boost(
    base_minutes: float,
    base_stat: float,
    vacuum_scale: float = 1.0,
) -> Dict:
    """
    Calculate stat boost using Ludi-Bot's promotion logic.

    vacuum_scale: 0.0-1.0 multiplier from smart vacuum detection.
    Full (1.0) = recently out. Partial (0.5) = been out a while.
    """
    if base_minutes == 0 or vacuum_scale == 0:
        return {'boost_pct': 0, 'boost_amount': 0, 'projected': base_stat}

    # Scale the extra minutes by vacuum factor
    effective_extra_mins = PROMOTION_MINUTES * vacuum_scale
    minutes_adjustment = 1 + (effective_extra_mins / base_minutes)

    boosted_stat = base_stat * minutes_adjustment
    boost_amount = boosted_stat - base_stat
    boost_pct = ((boosted_stat / base_stat) - 1) * 100 if base_stat > 0 else 0

    return {
        'boost_pct': round(boost_pct, 1),
        'boost_amount': round(boost_amount, 1),
        'projected': round(boosted_stat, 1)
    }


def get_usage_vacuum_analysis(
    team_abbr: str,
    injured_players: List[str],
    game_total: Optional[float] = None
) -> Dict:
    """
    Generate smart usage vacuum analysis.

    Now filters out:
    - Long-term injuries (team already adjusted)
    - Recently traded players (haven't played for team yet)
    - Low-minutes/low-games players (minimal vacuum)
    And scales partial vacuums proportionally.
    """
    roster = get_team_roster(team_abbr, include_stats=True)
    if not roster or not injured_players:
        return {}

    team_games = _estimate_team_games(roster)
    analysis = {}

    for player_out_name in injured_players:
        # Find OUT player on roster
        out_player = None
        for p in roster:
            if player_out_name.lower() in p['name'].lower():
                out_player = p
                break

        if not out_player or not out_player.get('stats'):
            continue

        # Smart vacuum classification
        vacuum = _classify_vacuum(out_player, team_games, roster)

        if vacuum['status'] == 'skip' or vacuum['scale'] == 0:
            # Still record it so the prompt knows WHY we skipped
            analysis[player_out_name] = {
                'skipped': True,
                'reason': vacuum['reason'],
                'status': vacuum['status'],
            }
            continue

        # Find position-aware beneficiaries
        beneficiaries = _find_beneficiaries(out_player, roster)
        if not beneficiaries:
            continue

        primary = beneficiaries[0]
        scale = vacuum['scale']

        # Calculate scaled promotion boosts
        pts_boost = calculate_promotion_boost(primary['mins'], primary['pts'], scale)
        ast_boost = calculate_promotion_boost(primary['mins'], primary['ast'], scale)
        reb_boost = calculate_promotion_boost(primary['mins'], primary['reb'], scale)

        # Apply pace context
        pace_factor = 1.0
        pace_note = ""
        if game_total:
            if game_total > 238:
                pace_factor = HIGH_PACE_BOOST
                pace_note = " (high-pace game)"
            elif game_total < 218:
                pace_factor = LOW_PACE_DECLINE
                pace_note = " (low-pace game)"

        analysis[player_out_name] = {
            'skipped': False,
            'status': vacuum['status'],
            'reason': vacuum['reason'],
            'vacuum_scale': scale,
            'primary_beneficiary': primary['name'],
            'beneficiary_position': primary['position'],
            'stats': {
                'pts': {
                    'current': primary['pts'],
                    'boost': round(pts_boost['boost_amount'] * pace_factor, 1),
                    'projected': round(pts_boost['projected'] * pace_factor, 1),
                    'boost_pct': pts_boost['boost_pct']
                },
                'ast': {
                    'current': primary['ast'],
                    'boost': round(ast_boost['boost_amount'] * pace_factor, 1),
                    'projected': round(ast_boost['projected'] * pace_factor, 1),
                    'boost_pct': ast_boost['boost_pct']
                },
                'reb': {
                    'current': primary['reb'],
                    'boost': round(reb_boost['boost_amount'] * pace_factor, 1),
                    'projected': round(reb_boost['projected'] * pace_factor, 1),
                    'boost_pct': reb_boost['boost_pct']
                }
            },
            'context': {
                'minutes_increase': round(PROMOTION_MINUTES * scale, 1),
                'pace_factor': pace_factor,
                'pace_note': pace_note,
                'team_games': team_games,
            }
        }

        # Add secondary beneficiary if exists
        if len(beneficiaries) > 1:
            secondary = beneficiaries[1]
            analysis[player_out_name]['secondary_beneficiary'] = secondary['name']

    return analysis


def format_usage_vacuum_for_prompt(analysis: Dict) -> str:
    """
    Format smart vacuum analysis for Claude prompts.

    Now includes context notes explaining WHY each vacuum was classified.
    Skipped players show explanation instead of fake projections.
    """
    if not analysis:
        return "No significant usage vacuum scenarios."

    active_entries = []
    skipped_entries = []

    for player_out, data in analysis.items():
        if data.get('skipped'):
            skipped_entries.append(f"- {player_out}: {data['reason']}")
            continue

        beneficiary = data['primary_beneficiary']
        pts = data['stats']['pts']
        ast = data['stats']['ast']
        reb = data['stats']['reb']
        pace_note = data['context']['pace_note']
        status = data['status']

        # Header with vacuum strength indicator
        if status == 'partial':
            scale_pct = int(data['vacuum_scale'] * 100)
            header = f"\n**{player_out} OUT** → {beneficiary} benefits (partial vacuum, {scale_pct}% weight):"
        else:
            header = f"\n**{player_out} OUT** → {beneficiary} primary beneficiary:"

        section = header

        if pts['boost'] >= 1.0:
            section += f"\n- PTS: {pts['current']} → {pts['projected']} (+{pts['boost']}, +{pts['boost_pct']}%)"
        if ast['boost'] >= 0.5:
            section += f"\n- AST: {ast['current']} → {ast['projected']} (+{ast['boost']}, +{ast['boost_pct']}%)"
        if reb['boost'] >= 0.5:
            section += f"\n- REB: {reb['current']} → {reb['projected']} (+{reb['boost']}, +{reb['boost_pct']}%)"

        if data.get('secondary_beneficiary'):
            section += f"\n- Secondary: {data['secondary_beneficiary']} also benefits"

        if pace_note:
            section += f"\n  {pace_note}"

        active_entries.append(section)

    output = []
    if active_entries:
        output.extend(active_entries)
    if skipped_entries:
        output.append("\n**Vacuum not applied (already absorbed):**")
        output.extend(skipped_entries)

    return "\n".join(output) if output else "No significant usage vacuum scenarios."
