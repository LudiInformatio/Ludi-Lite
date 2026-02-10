"""
Query Parser - Natural language parsing for NBA queries

Handles parsing of chat queries into structured requests:
- Game matchups: "DEN vs NYK", "Lakers @ Suns"
- Player props with lines: "Luka PTS 28.5", "Trae assists over 9.5"
- Player + stat queries: "Jokic rebounds", "Trae PRA"
- General player queries: "tell me about Luka"

Also provides player-to-game matching using live roster data
from Tank01 API with trade deadline override fallback.
"""

import re
from typing import Tuple
from team_mapping import normalize_team
from tank01_client import get_team_roster
from season_context import TRADE_DEADLINE_OVERRIDES

# Common NBA player nicknames/abbreviations → full names
# Used to resolve shorthand before roster matching
# Why: Tank01 rosters use full names, so "sga" won't match "Shai Gilgeous-Alexander"
PLAYER_NICKNAMES = {
    # Acronym nicknames (won't match via substring)
    "sga": "Shai Gilgeous-Alexander",
    "kd": "Kevin Durant",
    "cp3": "Chris Paul",
    "pg": "Paul George",
    "pg13": "Paul George",
    "rj": "RJ Barrett",
    "cj": "CJ McCollum",
    "tj": "TJ McConnell",
    "kat": "Karl-Anthony Towns",
    "ad": "Anthony Davis",
    "rui": "Rui Hachimura",
    "dlo": "D'Angelo Russell",
    "spida": "Donovan Mitchell",
    "abc": "Anthony Black",

    # Short first-name nicknames that could be ambiguous
    "lebron": "LeBron James",
    "bron": "LeBron James",
    "giannis": "Giannis Antetokounmpo",
    "greek freak": "Giannis Antetokounmpo",
    "luka": "Luka Doncic",
    "jokic": "Nikola Jokic",
    "joker": "Nikola Jokic",
    "steph": "Stephen Curry",
    "curry": "Stephen Curry",
    "dame": "Damian Lillard",
    "embiid": "Joel Embiid",
    "trae": "Trae Young",
    "ice trae": "Trae Young",
    "lamelo": "LaMelo Ball",
    "melo": "LaMelo Ball",
    "ant": "Anthony Edwards",
    "ant man": "Anthony Edwards",
    "book": "Devin Booker",
    "booker": "Devin Booker",
    "ja": "Ja Morant",
    "zion": "Zion Williamson",
    "kawhi": "Kawhi Leonard",
    "jimmy": "Jimmy Butler",
    "jimmy buckets": "Jimmy Butler",
    "harden": "James Harden",
    "kyrie": "Kyrie Irving",
    "bam": "Bam Adebayo",
    "fox": "De'Aaron Fox",
    "cade": "Cade Cunningham",
    "paolo": "Paolo Banchero",
    "wemby": "Victor Wembanyama",
    "wemby": "Victor Wembanyama",
    "chet": "Chet Holmgren",
    "brunson": "Jalen Brunson",
    "maxey": "Tyrese Maxey",
    "hali": "Tyrese Haliburton",
    "siakam": "Pascal Siakam",
    "tatum": "Jayson Tatum",
    "jt": "Jayson Tatum",
    "brown": "Jaylen Brown",
    "jb": "Jaylen Brown",
    "garland": "Darius Garland",
    "mobley": "Evan Mobley",
    "scottie": "Scottie Barnes",
    "franz": "Franz Wagner",
    "suggs": "Jalen Suggs",
    "herb": "Herb Jones",
    "ingram": "Brandon Ingram",
    "bi": "Brandon Ingram",
    "reaves": "Austin Reaves",
    "ar": "Austin Reaves",
    "sengun": "Alperen Sengun",
    "amen": "Amen Thompson",
    "jabari": "Jabari Smith Jr.",
    "murray": "Dejounte Murray",
    "jamal": "Jamal Murray",
    "mpj": "Michael Porter Jr.",
    "dort": "Luguentz Dort",
    "shai": "Shai Gilgeous-Alexander",
    "sabonis": "Domantas Sabonis",
    "dejounte": "Dejounte Murray",
    "demar": "DeMar DeRozan",
    "derozan": "DeMar DeRozan",
    "lavine": "Zach LaVine",
    "tre": "Tre Jones",
    "mikal": "Mikal Bridges",
    "cam": "Cam Thomas",
}


def resolve_player_nickname(name: str) -> str:
    """
    Resolve common nicknames/abbreviations to full player names.
    Returns the full name if a match is found, otherwise returns original input.
    """
    return PLAYER_NICKNAMES.get(name.lower().strip(), name)


def parse_chat_query(query: str) -> Tuple[str, dict]:
    """
    Parse natural language query into structured request

    Handles:
    - Games: "DEN vs NYK", "Lakers @ Suns"
    - Players: "Luka", "Doncic", "Luka Doncic"
    - Stats: PTS, AST, REB, 3PM, STL, BLK, TO, MIN, FG, FT, etc.
    - Combos: PRA, PA, PR, RA, PTS+AST, PTS+REB+AST, stocks, etc.
    - Props: "Luka PTS 28.5", "Trae assists over 9.5"

    Returns: (query_type, params)
    """
    query_lower = query.lower().strip()
    query_original = query.strip()

    # Strip temporal markers (not useful for name/stat matching)
    temporal_words = ["tonight", "today", "tomorrow", "this evening", "right now"]
    for word in temporal_words:
        query_lower = query_lower.replace(word, "").strip()
    # Clean up any double spaces from removal
    query_lower = " ".join(query_lower.split())

    # ===================
    # GAME QUERY PATTERNS
    # ===================
    # "DEN vs NYK", "Lakers @ Suns", "Denver versus New York"
    game_patterns = [
        r"(\w+)\s+(?:vs\.?|versus|@|at)\s+(\w+)",
    ]
    for pattern in game_patterns:
        match = re.search(pattern, query_lower)
        if match:
            # Use proper team normalization (handles "Lakers", "LAL", "Los Angeles", etc.)
            away = normalize_team(match.group(1))
            home = normalize_team(match.group(2))
            return "game", {"away": away, "home": home}

    # ===================
    # STAT NORMALIZATION
    # ===================
    stat_aliases = {
        # Points
        "pts": "Points", "points": "Points", "point": "Points", "scoring": "Points",
        # Assists
        "ast": "Assists", "assists": "Assists", "assist": "Assists", "dimes": "Assists",
        # Rebounds
        "reb": "Rebounds", "rebounds": "Rebounds", "rebound": "Rebounds", "boards": "Rebounds",
        "trb": "Rebounds", "total rebounds": "Rebounds",
        # 3-Pointers
        "3pm": "3PM", "3s": "3PM", "threes": "3PM", "three pointers": "3PM",
        "3pt": "3PM", "3 pointers": "3PM", "triples": "3PM",
        # Steals
        "stl": "Steals", "steals": "Steals", "steal": "Steals",
        # Blocks
        "blk": "Blocks", "blocks": "Blocks", "block": "Blocks",
        # Turnovers
        "to": "Turnovers", "turnovers": "Turnovers", "turnover": "Turnovers", "tos": "Turnovers",
        # Minutes
        "min": "Minutes", "mins": "Minutes", "minutes": "Minutes",
        # Field Goals
        "fgm": "FGM", "fg": "FGM", "field goals": "FGM",
        # Free Throws
        "ftm": "FTM", "ft": "FTM", "free throws": "FTM", "fts": "FTM",
        # Fantasy
        "fpts": "Fantasy", "fantasy": "Fantasy", "fantasy points": "Fantasy", "fp": "Fantasy",

        # === COMBO PROPS ===
        # PRA (Points + Rebounds + Assists)
        "pra": "PTS+REB+AST", "pts+reb+ast": "PTS+REB+AST", "pts reb ast": "PTS+REB+AST",
        "points rebounds assists": "PTS+REB+AST", "p+r+a": "PTS+REB+AST",
        # PA (Points + Assists)
        "pa": "PTS+AST", "pts+ast": "PTS+AST", "points assists": "PTS+AST",
        "points and assists": "PTS+AST", "p+a": "PTS+AST", "pts ast": "PTS+AST",
        # PR (Points + Rebounds)
        "pr": "PTS+REB", "pts+reb": "PTS+REB", "points rebounds": "PTS+REB",
        "points and rebounds": "PTS+REB", "p+r": "PTS+REB", "pts reb": "PTS+REB",
        # RA (Rebounds + Assists)
        "ra": "REB+AST", "reb+ast": "REB+AST", "rebounds assists": "REB+AST",
        "rebounds and assists": "REB+AST", "r+a": "REB+AST", "reb ast": "REB+AST",
        # Stocks (Steals + Blocks)
        "stocks": "STL+BLK", "stl+blk": "STL+BLK", "steals blocks": "STL+BLK",
        "steals and blocks": "STL+BLK", "defensive stats": "STL+BLK",
        # Boards + Dimes
        "boards dimes": "REB+AST", "rebounds dimes": "REB+AST",
        # Double-Double
        "dd": "Double-Double", "double double": "Double-Double", "double-double": "Double-Double",
        # Triple-Double
        "td": "Triple-Double", "triple double": "Triple-Double", "triple-double": "Triple-Double",
    }

    # ===================
    # PROP WITH LINE PATTERN
    # ===================
    # "Luka PTS 28.5", "Trae Young assists 9.5", "Jokic PRA over 45.5"
    # Pattern: [name] [stat] [optional: over/under] [number]

    # Build stat pattern from aliases
    stat_keywords = "|".join(sorted(stat_aliases.keys(), key=len, reverse=True))

    # Pattern 1: Name + Stat + Number
    prop_pattern = rf"(.+?)\s+({stat_keywords})\s+(?:over|under|o|u)?\s*(\d+\.?\d*)"
    prop_match = re.search(prop_pattern, query_lower)

    if prop_match:
        name_raw = prop_match.group(1).strip()
        stat_raw = prop_match.group(2).strip()
        line = float(prop_match.group(3))

        # Clean up name (remove common prefixes)
        name = name_raw.replace("give me", "").replace("info on", "").replace("about", "").strip()
        # Resolve nicknames BEFORE title-casing (e.g., "sga" → "Shai Gilgeous-Alexander")
        name = resolve_player_nickname(name)
        if name == name_raw.strip():
            name = name.title()  # Only title-case if not resolved from nickname map

        # Normalize stat
        stat = stat_aliases.get(stat_raw, stat_raw.upper())

        return "player_prop", {"name": name, "stat": stat, "line": line}

    # ===================
    # PLAYER + STAT (no line)
    # ===================
    # "Luka assists", "Jokic rebounds", "Trae PRA"
    stat_pattern = rf"(.+?)\s+({stat_keywords})(?:\s|$)"
    stat_match = re.search(stat_pattern, query_lower)

    if stat_match:
        name_raw = stat_match.group(1).strip()
        stat_raw = stat_match.group(2).strip()

        # Clean name
        name = name_raw.replace("give me", "").replace("info on", "").replace("about", "").strip()
        # Resolve nicknames before title-casing
        name = resolve_player_nickname(name)
        if name == name_raw.strip():
            name = name.title()

        # Normalize stat
        stat = stat_aliases.get(stat_raw, stat_raw.upper())

        return "player", {"name": name, "stat": stat}

    # ===================
    # PLAYER ONLY (general query)
    # ===================
    # "Luka", "tell me about Jokic", "info on Trae Young"

    # Remove common prefixes
    clean_query = query_lower
    prefixes_to_remove = [
        "give me info on", "give me information on", "tell me about",
        "info on", "information on", "about", "what about",
        "how is", "how's", "analyze", "breakdown", "break down"
    ]
    for prefix in prefixes_to_remove:
        if clean_query.startswith(prefix):
            clean_query = clean_query[len(prefix):].strip()
            break

    # If something remains, treat as player name
    if clean_query and len(clean_query) > 1:
        # Resolve nicknames (e.g., "sga" → "Shai Gilgeous-Alexander")
        resolved = resolve_player_nickname(clean_query)
        if resolved == clean_query:
            resolved = clean_query.title()
        return "player", {"name": resolved, "stat": "All Stats"}

    return "unknown", {}


def match_player_to_game(player_name: str, games: list) -> dict:
    """
    Auto-match a player to tonight's game by searching team rosters.
    Two-tier lookup:
      1. Tank01 live rosters (cached, returns full player objects)
      2. TRADE_DEADLINE_OVERRIDES fallback (for recently traded players)
    """
    if not player_name or not games:
        return {}

    player_lower = player_name.lower().strip()

    # Tier 1: Search Tank01 rosters for tonight's teams
    for game in games:
        for side in ['home', 'away']:
            team = game[side]
            try:
                roster = get_team_roster(team)
            except Exception:
                continue
            if not roster:
                continue
            for player in roster:
                if player_lower in player.get('name', '').lower():
                    opponent = game['away'] if side == 'home' else game['home']
                    return {
                        "team": team,
                        "opponent": opponent,
                        "is_home": side == 'home',
                        "game": game
                    }

    # Tier 2: Check trade deadline overrides (Tank01 lags 24-48hrs post-trade)
    override_team = TRADE_DEADLINE_OVERRIDES.get(player_lower)
    if override_team:
        for game in games:
            if game['home'] == override_team:
                return {"team": override_team, "opponent": game['away'], "is_home": True, "game": game}
            elif game['away'] == override_team:
                return {"team": override_team, "opponent": game['home'], "is_home": False, "game": game}
        return {"team": override_team}  # Team found but no game tonight

    return {}
