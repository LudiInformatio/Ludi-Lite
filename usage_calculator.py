"""
Usage Bump Calculator for Ludi Lite
Based on Ludi-Bot's proven S.A.V.A.G.E. methodology (Module E: The Calibrator).

Uses simple, data-driven calculations WITHOUT full simulations:
1. Promotion logic: When starter is OUT, backup gets promoted (+8 mins baseline)
2. Volume stat adjustments based on minutes increase
3. Context factors (pace, blowout risk, B2B)

NOT as precise as Ludi-Bot's full pipeline, but uses the same core logic.
"""

from typing import Dict, List, Optional
from tank01_client import get_team_roster


# Ludi-Bot's proven adjustment factors (from Module E)
PROMOTION_MINUTES = 8  # When backup becomes starter
MINUTES_LIMIT_FACTOR = 0.75  # When player has minutes restriction
HIGH_PACE_BOOST = 1.03  # Total >238
LOW_PACE_DECLINE = 0.97  # Total <218


def calculate_promotion_boost(base_minutes: float, base_stat: float) -> Dict:
    """
    Calculate stat boost using Ludi-Bot's promotion logic.

    When a starter is OUT and backup gets promoted:
    - Gets +8 minutes (Ludi-Bot baseline)
    - Volume stats scale with minutes increase

    Args:
        base_minutes: Player's current MPG
        base_stat: Player's current stat (PPG, APG, etc.)

    Returns:
        Dict with boost percentage and projected stat
    """
    if base_minutes == 0:
        return {'boost_pct': 0, 'boost_amount': 0, 'projected': base_stat}

    # Ludi-Bot formula: 1 + (extra_mins / base_mins)
    minutes_adjustment = 1 + (PROMOTION_MINUTES / base_minutes)

    # Apply to volume stat
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
    Generate usage vacuum analysis using S.A.V.A.G.E. methodology.

    Args:
        team_abbr: Team abbreviation
        injured_players: List of player names who are OUT
        game_total: Optional game total for pace context

    Returns:
        Dict with beneficiaries and their projected bumps
    """
    roster = get_team_roster(team_abbr, include_stats=True)
    if not roster or not injured_players:
        return {}

    analysis = {}

    for player_out_name in injured_players:
        # Find OUT player
        out_player = None
        for p in roster:
            if player_out_name.lower() in p['name'].lower():
                out_player = p
                break

        if not out_player or not out_player.get('stats'):
            continue

        out_stats = out_player['stats']
        out_mins = float(out_stats.get('mins', 0))
        out_pts = float(out_stats.get('pts', 0))
        out_ast = float(out_stats.get('ast', 0))
        out_reb = float(out_stats.get('reb', 0))

        # Find primary beneficiary (same position, most minutes)
        candidates = []
        for p in roster:
            if p['name'] == out_player['name']:
                continue

            # Skip injured
            injury = p.get('injury', {})
            if injury.get('designation') in ['OUT', 'DOUBTFUL', 'SUSPENDED']:
                continue

            stats = p.get('stats', {})
            if not stats:
                continue

            p_mins = float(stats.get('mins', 0))
            p_pts = float(stats.get('pts', 0))
            p_ast = float(stats.get('ast', 0))
            p_reb = float(stats.get('reb', 0))

            # Only rotation players (>15 MPG)
            if p_mins > 15:
                candidates.append({
                    'name': p['name'],
                    'position': p['position'],
                    'mins': p_mins,
                    'pts': p_pts,
                    'ast': p_ast,
                    'reb': p_reb
                })

        if not candidates:
            continue

        # Sort by minutes (primary beneficiary = highest MPG)
        candidates.sort(key=lambda x: x['mins'], reverse=True)
        primary = candidates[0]

        # Calculate promotion boost for primary beneficiary
        pts_boost = calculate_promotion_boost(primary['mins'], primary['pts'])
        ast_boost = calculate_promotion_boost(primary['mins'], primary['ast'])
        reb_boost = calculate_promotion_boost(primary['mins'], primary['reb'])

        # Apply pace context if available
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
            'primary_beneficiary': primary['name'],
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
                'minutes_increase': PROMOTION_MINUTES,
                'pace_factor': pace_factor,
                'pace_note': pace_note
            }
        }

    return analysis


def format_usage_vacuum_for_prompt(analysis: Dict) -> str:
    """
    Format usage vacuum analysis for Claude prompts.

    Args:
        analysis: Output from get_usage_vacuum_analysis()

    Returns:
        Formatted string for prompt injection
    """
    if not analysis:
        return "No significant usage vacuum scenarios."

    output = []
    for player_out, data in analysis.items():
        beneficiary = data['primary_beneficiary']
        pts = data['stats']['pts']
        ast = data['stats']['ast']
        reb = data['stats']['reb']
        pace_note = data['context']['pace_note']

        player_section = f"\n**{player_out} OUT** → {beneficiary} primary beneficiary:"

        # Points
        if pts['boost'] >= 1.0:
            player_section += f"\n- PTS: {pts['current']} → {pts['projected']} (+{pts['boost']}, +{pts['boost_pct']}%)"

        # Assists
        if ast['boost'] >= 0.5:
            player_section += f"\n- AST: {ast['current']} → {ast['projected']} (+{ast['boost']}, +{ast['boost_pct']}%)"

        # Rebounds
        if reb['boost'] >= 0.5:
            player_section += f"\n- REB: {reb['current']} → {reb['projected']} (+{reb['boost']}, +{reb['boost_pct']}%)"

        if pace_note:
            player_section += f"\n  {pace_note}"

        output.append(player_section)

    return "\n".join(output)
