"""
NBA Team Name Mapping for Ludi Lite
Consistent with Ludi-Bot's utils/mappings.py

Handles conversion between different API naming conventions:
- The-Odds-API: Full names ("Los Angeles Lakers")
- Tank01: Abbreviations ("LAL")
- User input: Various formats ("Lakers", "LA", "LAL")
"""

# Authoritative mapping (consistent with Ludi-Bot)
TEAM_MAP = {
    # City names
    "Atlanta": "ATL", "Boston": "BOS", "Brooklyn": "BKN", "Charlotte": "CHA",
    "Chicago": "CHI", "Cleveland": "CLE", "Dallas": "DAL", "Denver": "DEN",
    "Detroit": "DET", "Golden State": "GSW", "Houston": "HOU", "Indiana": "IND",
    "Memphis": "MEM", "Miami": "MIA", "Milwaukee": "MIL", "Minnesota": "MIN",
    "New Orleans": "NOP", "New York": "NYK", "Oklahoma City": "OKC",
    "Orlando": "ORL", "Philadelphia": "PHI", "Phoenix": "PHX",
    "Portland": "POR", "Sacramento": "SAC", "San Antonio": "SAS",
    "Toronto": "TOR", "Utah": "UTA", "Washington": "WAS",

    # LA teams (special handling)
    "L.A. Clippers": "LAC", "LA Clippers": "LAC", "Clippers": "LAC",
    "L.A. Lakers": "LAL", "LA Lakers": "LAL", "Lakers": "LAL",
    "Los Angeles Lakers": "LAL", "Los Angeles Clippers": "LAC",

    # Full team names (The-Odds-API format)
    "Atlanta Hawks": "ATL",
    "Boston Celtics": "BOS",
    "Brooklyn Nets": "BKN",
    "Charlotte Hornets": "CHA",
    "Chicago Bulls": "CHI",
    "Cleveland Cavaliers": "CLE",
    "Dallas Mavericks": "DAL",
    "Denver Nuggets": "DEN",
    "Detroit Pistons": "DET",
    "Golden State Warriors": "GSW",
    "Houston Rockets": "HOU",
    "Indiana Pacers": "IND",
    "Memphis Grizzlies": "MEM",
    "Miami Heat": "MIA",
    "Milwaukee Bucks": "MIL",
    "Minnesota Timberwolves": "MIN",
    "New Orleans Pelicans": "NOP",
    "New York Knicks": "NYK",
    "Oklahoma City Thunder": "OKC",
    "Orlando Magic": "ORL",
    "Philadelphia 76ers": "PHI",
    "Phoenix Suns": "PHX",
    "Portland Trail Blazers": "POR",
    "Sacramento Kings": "SAC",
    "San Antonio Spurs": "SAS",
    "Toronto Raptors": "TOR",
    "Utah Jazz": "UTA",
    "Washington Wizards": "WAS",

    # Nicknames only (for user input)
    "Knicks": "NYK",
    "Nets": "BKN",
    "Celtics": "BOS",
    "76ers": "PHI",
    "Sixers": "PHI",
    "Heat": "MIA",
    "Magic": "ORL",
    "Hawks": "ATL",
    "Hornets": "CHA",
    "Bulls": "CHI",
    "Cavaliers": "CLE",
    "Cavs": "CLE",
    "Pistons": "DET",
    "Pacers": "IND",
    "Bucks": "MIL",
    "Wizards": "WAS",
    "Raptors": "TOR",
    "Nuggets": "DEN",
    "Timberwolves": "MIN",
    "Wolves": "MIN",
    "Thunder": "OKC",
    "Trail Blazers": "POR",
    "Blazers": "POR",
    "Jazz": "UTA",
    "Warriors": "GSW",
    "Suns": "PHX",
    "Kings": "SAC",
    "Mavericks": "DAL",
    "Mavs": "DAL",
    "Rockets": "HOU",
    "Grizzlies": "MEM",
    "Pelicans": "NOP",
    "Spurs": "SAS",
}

# Valid 3-letter abbreviations
VALID_ABBREVS = {
    "ATL", "BOS", "BKN", "CHA", "CHI", "CLE", "DAL", "DEN", "DET", "GSW",
    "HOU", "IND", "LAC", "LAL", "MEM", "MIA", "MIL", "MIN", "NOP", "NYK",
    "OKC", "ORL", "PHI", "PHX", "POR", "SAC", "SAS", "TOR", "UTA", "WAS"
}

# Abbreviation to full name (for display)
ABBREV_TO_FULL = {
    "ATL": "Atlanta Hawks", "BOS": "Boston Celtics", "BKN": "Brooklyn Nets",
    "CHA": "Charlotte Hornets", "CHI": "Chicago Bulls", "CLE": "Cleveland Cavaliers",
    "DAL": "Dallas Mavericks", "DEN": "Denver Nuggets", "DET": "Detroit Pistons",
    "GSW": "Golden State Warriors", "HOU": "Houston Rockets", "IND": "Indiana Pacers",
    "LAC": "Los Angeles Clippers", "LAL": "Los Angeles Lakers", "MEM": "Memphis Grizzlies",
    "MIA": "Miami Heat", "MIL": "Milwaukee Bucks", "MIN": "Minnesota Timberwolves",
    "NOP": "New Orleans Pelicans", "NYK": "New York Knicks", "OKC": "Oklahoma City Thunder",
    "ORL": "Orlando Magic", "PHI": "Philadelphia 76ers", "PHX": "Phoenix Suns",
    "POR": "Portland Trail Blazers", "SAC": "Sacramento Kings", "SAS": "San Antonio Spurs",
    "TOR": "Toronto Raptors", "UTA": "Utah Jazz", "WAS": "Washington Wizards"
}


def normalize_team(raw_name: str) -> str:
    """
    Standardize team names to 3-letter abbreviations.
    Consistent with Ludi-Bot's resolve_team_abbr().

    Args:
        raw_name: Any team name format

    Returns:
        3-letter abbreviation (e.g., "LAL", "NYK", "GSW")
        Returns "???" if not found

    Examples:
        >>> normalize_team("Los Angeles Lakers")
        'LAL'
        >>> normalize_team("Lakers")
        'LAL'
        >>> normalize_team("LAL")
        'LAL'
    """
    if not raw_name:
        return "???"

    # Clean input
    clean_name = raw_name.replace('.', '').strip()

    # Direct lookup
    if clean_name in TEAM_MAP:
        return TEAM_MAP[clean_name]

    # Case-insensitive lookup
    for key, abbr in TEAM_MAP.items():
        if key.lower() == clean_name.lower():
            return abbr

    # Check if already a valid abbreviation
    upper = clean_name.upper()
    if upper in VALID_ABBREVS:
        return upper

    # Partial match (e.g., "Lakers" in "Los Angeles Lakers")
    for key, abbr in TEAM_MAP.items():
        if key.lower() in clean_name.lower() or clean_name.lower() in key.lower():
            return abbr

    return "???"


def get_full_name(abbrev: str) -> str:
    """Get full team name from abbreviation."""
    return ABBREV_TO_FULL.get(abbrev.upper(), abbrev)
