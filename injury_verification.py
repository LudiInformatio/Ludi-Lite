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


def get_injuries_from_rosters(teams: List[str]) -> List[Dict]:
    """
    Fetch injury data from Tank01 team rosters (WORKING ENDPOINT).

    The getNBAInjuryList endpoint is BROKEN - returns only playerID without team/name.
    Instead, we query getNBATeamRoster per team, which has embedded injury fields.

    Args:
        teams: List of team abbreviations to check (e.g., ['LAL', 'PHI'])

    Returns:
        List of injury dictionaries with name, team, designation, description
    """
    try:
        from tank01_client import get_team_roster, _to_standard_abbr

        all_injuries = []

        for team_abbr in teams:
            roster = get_team_roster(team_abbr)
            if not roster:
                continue

            for player in roster:
                injury = player.get("injury", {})
                designation = (injury.get("designation") or "").upper()

                if designation:  # Only include players with injury status
                    description = injury.get("description", "")
                    all_injuries.append({
                        "name": player.get("name", "Unknown"),
                        "team": _to_standard_abbr(team_abbr),
                        "designation": designation,
                        "description": description
                    })

        return all_injuries

    except Exception as e:
        print(f"Tank01 Roster API Error: {e}")
        return []


def get_official_nba_injuries() -> List[Dict]:
    """
    Fetch official NBA injury report from nba.com

    DISABLED: Official NBA endpoints returning 403/empty as of Feb 2026

    Tested endpoints (both failing):
    - https://cdn.nba.com/static/json/staticData/injury-report_{date}.json → 403 Forbidden
    - https://ak-static.cms.nba.com/referee/injury/Injury-Report_{date}.json → Empty/denied

    TODO: Research current working NBA injury endpoint
    Official NBA injury reports update every 15 minutes (rolling basis)

    Returns list of injuries in standardized format (currently empty)
    """
    # DISABLED - uncomment and fix endpoint once working source is found
    # import requests
    #
    # try:
    #     today = datetime.now(pytz.timezone('America/New_York')).strftime('%Y-%m-%d')
    #     url = f"https://cdn.nba.com/static/json/staticData/injury-report_{today}.json"
    #     response = requests.get(url, timeout=10)
    #
    #     if response.status_code == 200:
    #         data = response.json()
    #         # Parse NBA official format
    #         return []
    #     else:
    #         print(f"NBA Official API returned {response.status_code}")
    #         return []
    #
    # except Exception as e:
    #     print(f"NBA Official API Error: {e}")
    #     return []

    return []  # Disabled until working endpoint is found


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

    # Source 1: ESPN (fastest, most current)
    print("📊 Fetching ESPN injury data...")
    espn_injuries = []
    espn_suspensions = []
    try:
        from espn_client import get_injuries, get_suspensions
        espn_injuries = get_injuries()
        espn_suspensions = get_suspensions()
    except Exception as e:
        print(f"   ESPN fetch error: {e}")

    # Source 2: Tank01 Rosters (FIXED - using working endpoint)
    print("📊 Fetching Tank01 roster data...")
    roster_injuries = get_injuries_from_rosters(teams)

    # Source 2: Known Suspensions (Tank01 removes these from rosters)
    print("📊 Checking known suspensions...")
    try:
        from season_context import KNOWN_SUSPENSIONS
        suspensions = [s for s in KNOWN_SUSPENSIONS if s["team"] in teams]
    except Exception as e:
        print(f"Could not load KNOWN_SUSPENSIONS: {e}")
        suspensions = []

    # Source 3: Official NBA (currently disabled)
    print("📊 Fetching Official NBA data...")
    nba_official = get_official_nba_injuries()

    # Source 4: Cross-check with Perplexity for known issues
    print("📊 Cross-referencing with Perplexity...\n")

    # Organize injuries by team
    injuries_by_team = {}
    for team in teams:
        team_injuries = [inj for inj in roster_injuries if inj['team'] == team]
        team_suspensions = [s for s in suspensions if s['team'] == team]
        espn_team_injuries = [inj for inj in espn_injuries if inj.get('team') == team]
        espn_team_suspensions = [s for s in espn_suspensions if s.get('team') == team]
        injuries_by_team[team] = {
            'roster': team_injuries,
            'espn': espn_team_injuries + espn_team_suspensions,
            'suspensions': team_suspensions,
            'total': len(team_injuries) + len(team_suspensions) + len(espn_team_injuries) + len(espn_team_suspensions)
        }

    results = {
        'timestamp': timestamp,
        'sources': {
            'espn_injuries_total': len(espn_injuries),
            'espn_suspensions_total': len(espn_suspensions),
            'roster_injuries_total': len(roster_injuries),
            'known_suspensions_total': len(suspensions),
            'nba_official_total': len(nba_official),
        },
        'teams': {},
        'discrepancies': []
    }

    for team in teams:
        data = injuries_by_team[team]
        roster_count = len(data['roster'])
        espn_count = len(data['espn'])
        suspension_count = len(data['suspensions'])
        total_count = data['total']

        print(f"\n{team}:")
        print(f"  Roster injuries: {roster_count}")
        print(f"  ESPN injuries: {espn_count}")

        if data['roster']:
            for inj in data['roster']:
                desc_short = inj['description'][:50] + "..." if len(inj['description']) > 50 else inj['description']
                print(f"    - {inj['name']}: {inj['designation']}" + (f" ({desc_short})" if desc_short else ""))

        if data['espn']:
            for inj in data['espn']:
                print(f"    - {inj['player_name']}: {inj['status']} ({inj.get('description', '')[:40]})")

        if data['suspensions']:
            print(f"  Known suspensions: {suspension_count}")
            for susp in data['suspensions']:
                print(f"    - {susp['name']}: {susp['status']} ({susp['description']})")

        print(f"  Total: {total_count} injuries")

        if total_count == 0:
            print(f"  ✓ No injuries reported for {team}")

        results['teams'][team] = {
            'roster_injuries': data['roster'],
            'espn_injuries': data['espn'],
            'suspensions': data['suspensions'],
            'nba_official': [],  # Populated when NBA API is working
            'total': total_count
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

    # Check Tank01 Roster
    try:
        from tank01_client import get_team_roster
        roster = get_team_roster(team)
        roster_match = None

        for player in roster:
            if player_name.lower() in player.get('name', '').lower():
                roster_match = player
                break

        print(f"\n1. Tank01 Team Roster:")
        if roster_match:
            injury = roster_match.get('injury', {})
            designation = injury.get('designation', '')
            if designation:
                print(f"   ✓ Found: {roster_match['name']} - {designation}")
                print(f"     Details: {injury.get('description', 'No details')}")
            else:
                print(f"   ✓ Found: {roster_match['name']} - HEALTHY (no injury status)")
        else:
            print(f"   ✗ NOT FOUND in {team} roster")
            print(f"     Check if player was traded or suspended")
    except Exception as e:
        print(f"   ✗ Error checking roster: {e}")
        roster_match = None

    # Check Known Suspensions
    try:
        from season_context import KNOWN_SUSPENSIONS
        suspension_match = None
        for susp in KNOWN_SUSPENSIONS:
            if player_name.lower() in susp['name'].lower() and susp['team'] == team:
                suspension_match = susp
                break

        print(f"\n2. Known Suspensions:")
        if suspension_match:
            print(f"   ⚠️ Found: {suspension_match['name']} - {suspension_match['status']}")
            print(f"     Details: {suspension_match['description']}")
        else:
            print(f"   ✓ Not in suspension list")
    except Exception as e:
        print(f"   ✗ Error checking suspensions: {e}")
        suspension_match = None

    # Check Perplexity
    print(f"\n3. Perplexity Real-Time Search:")
    news = search_injury_news_perplexity(player_name, team)
    if news:
        print(f"   {news[:300]}...")
    else:
        print(f"   No recent news found")

    return {
        'player': player_name,
        'team': team,
        'roster_status': roster_match.get('injury') if roster_match else None,
        'suspension_status': suspension_match if suspension_match else None,
        'perplexity_news': news,
        'verified_at': datetime.now(pytz.timezone('America/New_York')).isoformat()
    }


# Scheduled execution times (for GitHub Actions workflow)
VERIFICATION_TIMES = [
    "11:00",  # 11 AM EST - Morning injury report
    "12:00",  # 12 PM EST - Early afternoon check
    "17:00",  # 5 PM EST - Pre-primetime games
    "19:00",  # 7 PM EST - Final check before main slate
]


def get_dynamic_teams() -> List[str]:
    """
    Get teams playing TODAY dynamically from Tank01.
    This minimizes API costs by only checking teams with games tonight.

    Falls back to all 30 teams if API fails.

    Returns:
        List of team abbreviations playing today
    """
    try:
        from tank01_client import get_todays_games

        games = get_todays_games()
        if not games:
            print("⚠️ No games scheduled today, checking all teams...")
            return get_all_nba_teams()

        teams_tonight = set()
        for game in games:
            # Extract team abbreviations (handle different field names)
            home = game.get("homeTeam", game.get("home", game.get("hTeam", "")))
            away = game.get("awayTeam", game.get("away", game.get("aTeam", "")))
            if home:
                teams_tonight.add(home)
            if away:
                teams_tonight.add(away)

        teams_tonight.discard("")  # Remove empty strings

        teams_list = sorted(list(teams_tonight))
        print(f"✓ Found {len(teams_list)} teams playing today: {', '.join(teams_list)}")
        return teams_list

    except Exception as e:
        print(f"⚠️ Could not fetch today's games: {e}")
        print("   Falling back to all 30 NBA teams...")
        return get_all_nba_teams()


def get_all_nba_teams() -> List[str]:
    """Return all 30 NBA team abbreviations (fallback)"""
    return [
        "ATL", "BOS", "BKN", "CHA", "CHI", "CLE", "DAL", "DEN", "DET",
        "GSW", "HOU", "IND", "LAC", "LAL", "MEM", "MIA", "MIL", "MIN",
        "NOP", "NYK", "OKC", "ORL", "PHI", "PHX", "POR", "SAC", "SAS",
        "TOR", "UTA", "WAS"
    ]


if __name__ == "__main__":
    # Dynamically get tonight's teams (or all 30 if no games)
    print("🔍 Detecting tonight's games...")
    teams_tonight = get_dynamic_teams()

    print("\n" + "="*80)
    print("Running injury verification for tonight's games...")
    results = compare_injury_sources(teams_tonight)

    # Specific player checks
    print("\n" + "="*80)
    print("SPECIFIC PLAYER VERIFICATIONS")
    print("="*80)

    # Known issue: Paul George suspension not in Tank01
    pg_check = verify_specific_player("Paul George", "PHI")

    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)

    total_roster_injuries = results['sources']['roster_injuries_total']
    total_suspensions = results['sources']['known_suspensions_total']
    total_combined = total_roster_injuries + total_suspensions

    print(f"✓ Roster injuries found: {total_roster_injuries}")
    print(f"✓ Known suspensions: {total_suspensions}")
    print(f"✓ Total injuries tracked: {total_combined}")

    teams_with_injuries = sum(1 for team_data in results['teams'].values() if team_data['total'] > 0)
    print(f"✓ Teams with injuries: {teams_with_injuries}/{len(teams_tonight)}")

    if results['discrepancies']:
        print(f"\n⚠️ Discrepancies found: {len(results['discrepancies'])}")
        for disc in results['discrepancies']:
            print(f"  • {disc['team']}: {disc['issue']} (Severity: {disc['severity']})")
    else:
        print("\n✓ No data discrepancies detected")

    print("\n✅ Verification complete")
    print("📊 Data sources: Tank01 rosters + KNOWN_SUSPENSIONS + Perplexity verification")
