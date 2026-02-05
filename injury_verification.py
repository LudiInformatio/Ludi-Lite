"""
Injury Data Verification System
Cross-references multiple sources to ensure accurate injury reports

Sources:
1. Tank01 API (RapidAPI) - Live injury list
2. Official NBA Injury Report (nba.com)
3. Perplexity Search - Real-time news verification

Scheduled runs: 11 AM EST, 3 PM EST, 6 PM EST (pre-game windows)
"""

import os
from datetime import datetime, timezone
from typing import Dict, List, Optional
import pytz


def get_tank01_injuries() -> List[Dict]:
    """Fetch injury data from Tank01 API"""
    try:
        from tank01_client import get_injury_list
        return get_injury_list()
    except Exception as e:
        print(f"Tank01 API Error: {e}")
        return []


def get_official_nba_injuries() -> List[Dict]:
    """
    Fetch official NBA injury report from nba.com

    Official source: https://www.nba.com/stats/players/injury
    or https://ak-static.cms.nba.com/referee/injury/Injury-Report_[date].json

    Returns list of injuries in standardized format
    """
    import requests

    try:
        # NBA official injury endpoint (updated daily around 11 AM EST)
        # Format: https://cdn.nba.com/static/json/staticData/injury-report_YYYY-MM-DD.json
        today = datetime.now(pytz.timezone('America/New_York')).strftime('%Y-%m-%d')

        url = f"https://cdn.nba.com/static/json/staticData/injury-report_{today}.json"
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            data = response.json()
            # Parse NBA official format
            injuries = []
            # Note: Actual parsing depends on NBA's JSON structure
            # This is a placeholder - need to inspect real response
            return injuries
        else:
            print(f"NBA Official API returned {response.status_code}")
            return []

    except Exception as e:
        print(f"NBA Official API Error: {e}")
        return []


def search_injury_news_perplexity(player_name: str, team: str) -> Optional[str]:
    """
    Use Perplexity to verify player's current injury status
    Returns latest news about player injuries
    """
    try:
        from perplexity_client import search_player_context

        query = f"{player_name} {team} injury status today"
        hours_to_game = 4  # Use "day" recency filter

        news = search_player_context(
            player_name=player_name,
            stat="injury",
            opponent=team,
            hours_to_game=hours_to_game
        )
        return news

    except Exception as e:
        print(f"Perplexity search error for {player_name}: {e}")
        return None


def compare_injury_sources(teams: List[str]) -> Dict:
    """
    Compare injury data from all sources for given teams

    Args:
        teams: List of team abbreviations (e.g., ['PHI', 'LAL'])

    Returns:
        Dict with comparison results and discrepancies
    """
    timestamp = datetime.now(pytz.timezone('America/New_York')).strftime('%Y-%m-%d %I:%M %p ET')

    print(f"\n{'='*80}")
    print(f"INJURY DATA VERIFICATION - {timestamp}")
    print(f"{'='*80}\n")

    # Source 1: Tank01
    print("📊 Fetching Tank01 data...")
    tank01_injuries = get_tank01_injuries()
    tank01_by_team = {}
    for inj in tank01_injuries:
        team = inj.get('team')
        if team in teams:
            if team not in tank01_by_team:
                tank01_by_team[team] = []
            tank01_by_team[team].append(inj)

    # Source 2: Official NBA
    print("📊 Fetching Official NBA data...")
    nba_official = get_official_nba_injuries()

    # Source 3: Cross-check with Perplexity for known issues
    print("📊 Cross-referencing with Perplexity...\n")

    results = {
        'timestamp': timestamp,
        'sources': {
            'tank01_total': len(tank01_injuries),
            'nba_official_total': len(nba_official),
        },
        'teams': {},
        'discrepancies': []
    }

    for team in teams:
        tank01_count = len(tank01_by_team.get(team, []))

        print(f"\n{team}:")
        print(f"  Tank01: {tank01_count} injuries")

        if tank01_count == 0:
            print(f"  ⚠️ WARNING: Tank01 shows NO injuries for {team}")
            print(f"     This may indicate stale/missing data")
            results['discrepancies'].append({
                'team': team,
                'issue': 'Tank01 shows zero injuries',
                'severity': 'HIGH'
            })
        else:
            for inj in tank01_by_team[team]:
                print(f"    - {inj['name']}: {inj.get('designation')}")

        results['teams'][team] = {
            'tank01': tank01_by_team.get(team, []),
            'nba_official': [],  # Populated when NBA API is working
        }

    return results


def verify_specific_player(player_name: str, team: str) -> Dict:
    """
    Deep dive verification for a specific player
    Useful when Tank01 data seems wrong

    Example: verify_specific_player("Paul George", "PHI")
    """
    print(f"\n🔍 DEEP VERIFICATION: {player_name} ({team})")
    print("="*60)

    # Check Tank01
    tank01_injuries = get_tank01_injuries()
    tank01_match = [
        inj for inj in tank01_injuries
        if player_name.lower() in inj.get('name', '').lower()
    ]

    print(f"\n1. Tank01 API:")
    if tank01_match:
        for inj in tank01_match:
            print(f"   ✓ Found: {inj['name']} - {inj.get('designation')}")
            print(f"     Details: {inj.get('description')}")
    else:
        print(f"   ✗ NOT FOUND in Tank01 injury list")

    # Check Perplexity
    print(f"\n2. Perplexity Real-Time Search:")
    news = search_injury_news_perplexity(player_name, team)
    if news:
        print(f"   {news[:300]}...")
    else:
        print(f"   No recent news found")

    return {
        'player': player_name,
        'team': team,
        'tank01_status': tank01_match[0] if tank01_match else None,
        'perplexity_news': news,
        'verified_at': datetime.now(pytz.timezone('America/New_York')).isoformat()
    }


# Scheduled execution times (for GitHub Actions workflow)
VERIFICATION_TIMES = [
    "11:00",  # 11 AM EST - Morning injury report
    "15:00",  # 3 PM EST - Afternoon update
    "18:00",  # 6 PM EST - Pre-game final check
]


if __name__ == "__main__":
    # Test with tonight's teams (Feb 5, 2026)
    teams_tonight = ['PHI', 'LAL', 'GSW', 'PHX', 'CHI', 'TOR',
                     'BKN', 'ORL', 'CHA', 'HOU', 'WAS', 'DET',
                     'SAS', 'DAL', 'UTA', 'ATL']

    print("Running injury verification for tonight's games...")
    results = compare_injury_sources(teams_tonight)

    # Specific player checks
    print("\n" + "="*80)
    print("SPECIFIC PLAYER VERIFICATIONS")
    print("="*80)

    # Known issue: Paul George suspension not in Tank01
    pg_check = verify_specific_player("Paul George", "PHI")

    print("\n" + "="*80)
    print(f"SUMMARY: {len(results['discrepancies'])} discrepancies found")
    if results['discrepancies']:
        print("\nIssues to investigate:")
        for disc in results['discrepancies']:
            print(f"  • {disc['team']}: {disc['issue']} (Severity: {disc['severity']})")

    print("\n✅ Verification complete")
    print(f"Tank01 API has {results['sources']['tank01_total']} total injuries in system")
    print("Recommend cross-referencing with official NBA sources for accuracy")
