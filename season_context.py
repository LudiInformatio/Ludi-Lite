"""
Season Context for 2025-26 NBA Season
This file grounds AI analysis in the CURRENT season, not training data.
Updated: February 2026
"""

CURRENT_SEASON = "2025-26"
SEASON_START_DATE = "2025-10-22"

# Key roster moves for 2025-26 (AI often has stale data)
ROSTER_CONTEXT = """
KEY 2025-26 ROSTER CHANGES (Use this, not your training data):

=== OFFSEASON MOVES (July 2024) ===
- Klay Thompson: NOW ON DALLAS (signed July 2024, NOT Golden State)
- Paul George: NOW ON PHILADELPHIA (signed July 2024, NOT LA Clippers)
- DeMar DeRozan: NOW ON SACRAMENTO (signed July 2024, NOT Chicago)
- Tyus Jones: NOW ON PHOENIX (signed July 2024, starting PG)
- Tobias Harris: NOW ON DETROIT (signed July 2024)
- Dejounte Murray: NOW ON NEW ORLEANS (traded from Atlanta)
- Kentavious Caldwell-Pope: NOW ON ORLANDO (signed July 2024)
- Jonas Valanciunas: NOW ON WASHINGTON
- Malik Beasley: NOW ON DETROIT
- Isaiah Hartenstein: NOW ON OKLAHOMA CITY (signed July 2024, starting C)
- Caleb Martin: NOW ON PHILADELPHIA (signed July 2024)

=== TRADE DEADLINE MOVES (Feb 2026) ===
- Anthony Davis: NOW ON WASHINGTON (traded from Dallas, Feb 4)
- James Harden: NOW ON CLEVELAND (traded from LA Clippers, Feb 4)
- Nikola Vučević: NOW ON BOSTON (traded from Chicago, Feb 4)
- Jared McCain: NOW ON OKLAHOMA CITY (traded from Philadelphia, Feb 4)
- Coby White: NOW ON CHARLOTTE (traded from Chicago, Feb 4)
- Chris Paul: NOW ON TORONTO (three-team trade, Feb 4)
- Lonzo Ball: FREE AGENT (waived by Utah after trade from Cleveland)
- Darius Garland: NOW ON LA CLIPPERS (traded from Cleveland for Harden)

=== DEADLINE IS FEB 5, 2026 AT 3 PM ET - MORE MOVES POSSIBLE ===
"""

# Defense scheme assignments for 2025-26
# These change year-to-year based on personnel and coaching
DEFENSE_SCHEMES_2025_26 = {
    "PAINT_PACK": ["OKC", "BOS", "DET", "MIN", "SAS", "ORL"],
    "BLITZ": ["HOU", "TOR", "MIA", "PHX"],
    "PERIMETER": ["GSW", "DAL", "NYK"],
    "SWITCH_HEAVY": ["CLE", "LAC", "MEM"],
    "FUNNEL": ["WAS", "ATL", "CHI", "UTA", "SAC"],
    "NEUTRAL": ["LAL", "DEN", "MIL", "BKN", "IND", "POR", "CHA", "NOP"]
}

# Offensive classifications for 2025-26
OFFENSE_SCHEMES_2025_26 = {
    "THREE_POINT_CENTRIC": ["BOS", "GSW", "IND", "ATL", "UTA"],
    "MOTION_OFFENSE": ["DEN", "MIA", "SAS"],
    "PACE_PUSH": ["SAC", "IND", "ATL", "CHA"],
    "PAINT_ATTACK": ["MIL", "NOP", "CLE", "ORL"],
    "ISOLATION_HEAVY": ["PHX", "DAL", "LAL", "BKN"],
    "BALANCED": ["OKC", "NYK", "MIN", "LAC", "MEM", "HOU", "TOR", "POR", "DET", "WAS", "CHI"]
}

# Key injuries/situations to track (update as season progresses)
CURRENT_CONTEXT_NOTES = """
CURRENT 2025-26 CONTEXT (as of February 5, 2026):
- This is the CURRENT season, games are happening NOW
- TRADE DEADLINE: February 5, 2026 at 3:00 PM ET (TODAY)
- All-Star break is mid-February 2026
- Playoff race is heating up

MAJOR DEADLINE RUMORS TO WATCH:
- Giannis Antetokounmpo (MIL): May be traded, 4-6 weeks out with calf injury
- Ja Morant (MEM): Sacramento Kings heavily linked, Miami Heat also interested
- More moves expected before 3 PM ET deadline

NOTE: Newly traded players may not be integrated into new teams immediately.
Check if player has played with new team before projecting.
"""

def get_defense_scheme(team_abbr: str) -> str:
    """Get a team's defensive scheme for 2025-26"""
    for scheme, teams in DEFENSE_SCHEMES_2025_26.items():
        if team_abbr.upper() in teams:
            return scheme
    return "NEUTRAL"

def get_offense_scheme(team_abbr: str) -> str:
    """Get a team's offensive classification for 2025-26"""
    for scheme, teams in OFFENSE_SCHEMES_2025_26.items():
        if team_abbr.upper() in teams:
            return scheme
    return "BALANCED"

def get_full_season_context() -> str:
    """Return complete season context for AI prompts"""
    defense_list = "\n".join([
        f"  - {scheme}: {', '.join(teams)}"
        for scheme, teams in DEFENSE_SCHEMES_2025_26.items()
    ])

    return f"""
=== CURRENT SEASON: {CURRENT_SEASON} NBA SEASON ===
Today's Date: Use current date, not training data.
Season Status: Regular season in progress (started {SEASON_START_DATE})

{ROSTER_CONTEXT}

DEFENSE SCHEME ASSIGNMENTS (2025-26):
{defense_list}

{CURRENT_CONTEXT_NOTES}

IMPORTANT: If your training data conflicts with the above, USE THE ABOVE.
These are the CURRENT facts for the 2025-26 season.
"""

