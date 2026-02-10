"""
Matchup rating utilities for Ludi Lite.
Traffic light indicators based on opponent defensive quality.
"""
from typing import Dict
from tank01_client import get_all_team_stats


def get_defensive_rankings() -> Dict[str, int]:
    """
    Rank all 30 teams by points allowed (oppg).
    1 = best defense (fewest points allowed), 30 = worst.
    """
    stats = get_all_team_stats()
    if not stats:
        return {}
    sorted_teams = sorted(stats.items(), key=lambda x: x[1].get("oppg", 999))
    return {team: rank + 1 for rank, (team, _) in enumerate(sorted_teams)}


def get_matchup_rating(opponent_abbr: str) -> Dict:
    """
    Traffic light rating for facing this opponent's defense.

    Returns: {"emoji": "🟢", "label": "Favorable", "rank": 28}
    - 🟢 Favorable = opponent rank 21-30 (worst defenses)
    - 🟡 Neutral = opponent rank 11-20
    - 🔴 Tough = opponent rank 1-10 (best defenses)
    """
    rankings = get_defensive_rankings()
    rank = rankings.get(opponent_abbr.upper(), 15)

    if rank >= 21:
        return {"emoji": "🟢", "label": "Favorable", "rank": rank}
    elif rank <= 10:
        return {"emoji": "🔴", "label": "Tough", "rank": rank}
    else:
        return {"emoji": "🟡", "label": "Neutral", "rank": rank}
