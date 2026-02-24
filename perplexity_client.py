"""
Perplexity API Client for Ludi Lite
Provides real-time web search to enhance Claude Freestyle analysis.
API Docs: https://docs.perplexity.ai/

Uses search_recency_filter for time-bounded searches:
- "hour": Last 60 minutes (pre-game, late scratches)
- "day": Last 24 hours (game day news)
- "week": Last 7 days (trends, matchup history)

Also includes RSS feed integration for Rotowire and RealGM news.
"""

import requests
import streamlit as st
from typing import Optional
from datetime import datetime
import pytz

try:
    import feedparser
    FEEDPARSER_AVAILABLE = True
except ImportError:
    FEEDPARSER_AVAILABLE = False


def _get_api_key() -> Optional[str]:
    """Get Perplexity API key from Streamlit secrets or environment"""
    try:
        return st.secrets.get("PERPLEXITY_API_KEY")
    except Exception:
        import os
        return os.getenv("PERPLEXITY_API_KEY")


def _get_recency_filter(hours_to_game: int = 24) -> str:
    """
    Determine appropriate recency filter based on time to tipoff.

    Industry best practice (per Parlay Savant, Action Network):
    - Close to game: Need latest injury/lineup news
    - Day of game: Focus on today's updates
    - Far from game: Can include weekly trends

    Args:
        hours_to_game: Hours until game starts

    Returns:
        Perplexity recency filter: "hour", "day", "week"
    """
    if hours_to_game <= 2:
        return "hour"   # Pre-game: late scratches, lineup changes
    elif hours_to_game <= 12:
        return "day"    # Game day: today's injury reports
    else:
        return "week"   # Advance look: trends, matchup history


@st.cache_data(ttl=1800, show_spinner=False)  # 30 min cache
def search_game_context(away_team: str, home_team: str, hours_to_game: int = 12) -> str:
    """
    Search for real-time context about a game matchup.
    Uses Perplexity's search_recency_filter for time-bounded results.

    Args:
        away_team: Away team name or abbreviation
        home_team: Home team name or abbreviation
        hours_to_game: Hours until tipoff (affects recency filter)

    Returns:
        Formatted context string with recent news, injuries, and insights
    """
    api_key = _get_api_key()
    if not api_key:
        return ""  # Silently skip if no API key

    recency = _get_recency_filter(hours_to_game)

    # Focused query - let API handle time filtering
    # Sources: @underdognba on Twitter/X for late-breaking player info
    query = f"""
    NBA 2025-26 SEASON: {away_team} vs {home_team} game.

    TRUSTED SOURCES: @underdognba Twitter, ESPN injury report, official team accounts, betting community

    STATUS KEYWORDS:
    - OUT: "ruled out", "won't play", "suspended", "inactive"
    - GTD: "questionable", "game-time decision", "day-to-day"
    - ACTIVE: "cleared", "will play", "probable"

    Return ONLY:
    1. Players OUT/DOUBTFUL/SUSPENDED (name + status)
    2. Recent team form (last 3 games W/L)
    3. Sharp money indicators - line movement against public, steam moves, reverse line movement
    4. Breaking news from THIS SEASON only

    Max 120 words. Bullets only. No old recaps or percentage projections.
    """

    try:
        response = requests.post(
            "https://api.perplexity.ai/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "sonar",
                "messages": [
                    {"role": "system", "content": "You are a sports research assistant for the 2025-26 NBA season. Return ONLY verifiable facts from web sources. Never invent stats, injury statuses, or game outcomes. If you cannot find information, say 'No data found.' Include source names when possible."},
                    {"role": "user", "content": query}
                ],
                "max_tokens": 500,
                "temperature": 0.2,
                "return_citations": True,
                # API-level time filtering (more reliable than prompt)
                "search_recency_filter": recency
            },
            timeout=15
        )

        if response.status_code == 200:
            data = response.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            if content:
                recency_label = {"hour": "Last Hour", "day": "Last 24h", "week": "Last 7 Days"}
                return f"\n=== REAL-TIME CONTEXT (Perplexity - {recency_label.get(recency, recency)}) ===\n{content}\n"

        return ""

    except Exception as e:
        return ""  # Silently fail - don't break the app


@st.cache_data(ttl=1800, show_spinner=False)  # 30 min cache
def search_player_context(player_name: str, opponent: str = "", hours_to_game: int = 12) -> str:
    """
    Search for real-time context about a specific player.
    Uses RSS feeds (Rotowire, RealGM) first. Falls back to Perplexity if no RSS news.
    
    Args:
        player_name: Player's name
        opponent: Optional opponent team
        hours_to_game: Hours until tipoff (affects recency filter)
        
    Returns:
        Formatted context string with recent performance and news
    """
    rss_news = get_rss_news(player_name)
    if rss_news:
        return f"\n{rss_news}\n"
    
    api_key = _get_api_key()
    if not api_key:
        return ""

    recency = _get_recency_filter(hours_to_game)
    opp_text = f"vs {opponent}" if opponent else ""

    # Focused query - let API handle time filtering
    query = f"""
    NBA 2025-26 SEASON: {player_name} {opp_text}.

    TRUSTED SOURCES: @underdognba Twitter, official team injury reports

    CHECK:
    - Status: OUT/SUSPENDED/DOUBTFUL/GTD/PROBABLE/ACTIVE?
    - Minutes restriction?
    - Last 3 games performance (trending up/down?)

    Return ONLY:
    1. Current status (OUT/GTD/ACTIVE)
    2. Last 3 games trend (qualitative: hot/cold/normal)
    3. Any relevant news

    Max 80 words. Bullets only. No specific percentage projections.
    """

    try:
        response = requests.post(
            "https://api.perplexity.ai/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "sonar",
                "messages": [
                    {"role": "system", "content": "You are a sports research assistant for the 2025-26 NBA season. Return ONLY verifiable facts from web sources. Never invent stats, injury statuses, or game outcomes. If you cannot find information, say 'No data found.' Include source names when possible."},
                    {"role": "user", "content": query}
                ],
                "max_tokens": 400,
                "temperature": 0.2,
                "return_citations": True,
                # API-level time filtering
                "search_recency_filter": recency
            },
            timeout=15
        )

        if response.status_code == 200:
            data = response.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            if content:
                recency_label = {"hour": "Last Hour", "day": "Last 24h", "week": "Last 7 Days"}
                return f"\n=== REAL-TIME PLAYER INFO (Perplexity - {recency_label.get(recency, recency)}) ===\n{content}\n"

        return ""

    except Exception:
        return ""


@st.cache_data(ttl=300, show_spinner=False)  # 5 min cache - needs freshness
def search_late_news(team_abbr: str) -> str:
    """
    Search for ONLY the most recent news (last hour) for late-breaking info.
    Use this close to tipoff for lineup changes and late scratches.

    Args:
        team_abbr: Team abbreviation

    Returns:
        Formatted string with late-breaking news only
    """
    api_key = _get_api_key()
    if not api_key:
        return ""

    query = f"""
    NBA {team_abbr} breaking news RIGHT NOW.

    TRUSTED SOURCES: @underdognba Twitter, official team accounts

    ONLY return:
    - Lineup changes
    - Late scratches
    - Game-time decisions resolved

    Max 50 words. If nothing new, say "No late updates."
    """

    try:
        response = requests.post(
            "https://api.perplexity.ai/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "sonar",
                "messages": [
                    {"role": "system", "content": "You are a sports research assistant for the 2025-26 NBA season. Return ONLY verifiable facts from web sources. Never invent stats, injury statuses, or game outcomes. If you cannot find information, say 'No data found.' Include source names when possible."},
                    {"role": "user", "content": query}
                ],
                "max_tokens": 200,
                "temperature": 0.1,
                "return_citations": True,
                "search_recency_filter": "hour"  # ONLY last hour
            },
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            if content and "no late" not in content.lower():
                return f"\n⚡ LATE NEWS: {content}\n"

        return ""

    except Exception:
        return ""


@st.cache_data(ttl=1800, show_spinner=False)  # 30 min cache
def search_social_sentiment(away_team: str, home_team: str) -> str:
    """
    Search social media and betting communities for sentiment on this game.
    Uses sonar-pro model for comprehensive social search.

    Args:
        away_team: Away team name or abbreviation
        home_team: Home team name or abbreviation

    Returns:
        Formatted sentiment analysis with signal labels
    """
    api_key = _get_api_key()
    if not api_key:
        return ""  # Silently skip if no API key

    query = f"""
    NBA 2025-26 SEASON: {away_team} @ {home_team} game.

    SEARCH SOURCES:
    - Twitter/X: @underdognba, NBA Twitter community
    - Reddit: r/nba, r/sportsbook, r/sportsbetting, r/NBA_Bets
    - NBA Discord communities

    IDENTIFY AND LABEL:
    - PUBLIC LEAN: General betting public's preference (which side is popular?)
    - SHARP SIGNAL: Sharp money indicators, line movement against public
    - BUZZ: Player buzz, breakout narratives, trending players
    - CONCERN: Injury concerns, lineup uncertainty, negative sentiment
    - LATE NEWS: Breaking news affecting this game

    Return ONLY labeled signals (e.g., "PUBLIC LEAN: 65% on Lakers", "SHARP SIGNAL: Line moved toward Warriors").
    Max 100 words. If no clear signals, say "No strong social signals detected."
    """

    try:
        response = requests.post(
            "https://api.perplexity.ai/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "sonar-pro",
                "messages": [
                    {"role": "system", "content": "You are a sports research assistant for the 2025-26 NBA season. Return ONLY verifiable facts from web sources. Never invent stats, injury statuses, or game outcomes. If you cannot find information, say 'No data found.' Include source names when possible."},
                    {"role": "user", "content": query}
                ],
                "max_tokens": 400,
                "temperature": 0.2,
                "return_citations": True
            },
            timeout=15
        )

        if response.status_code == 200:
            data = response.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            if content and "no strong social" not in content.lower():
                return f"\n=== SOCIAL SENTIMENT (Perplexity - Twitter/Reddit) ===\n{content}\n"

        return ""

    except Exception:
        return ""  # Silently fail - don't break the app


def is_perplexity_available() -> bool:
    """Check if Perplexity API is configured"""
    return _get_api_key() is not None


@st.cache_data(ttl=3600, show_spinner=False)  # 1 hour cache - refs announced ~9 AM ET
def search_referee_context(home_team: str, away_team: str) -> str:
    """
    Search for referee crew assignments and their pace/foul tendencies.
    Uses Perplexity's sonar model for web search.
    
    Args:
        home_team: Home team abbreviation
        away_team: Away team abbreviation
        
    Returns:
        Formatted string with referee crew and tendencies
    """
    api_key = _get_api_key()
    if not api_key:
        return ""
    
    query = f"""
    NBA referee assignments for tonight's {away_team} @ {home_team} game.
    
    TRUSTED SOURCES: official NBA referee assignments page, @RefAnalytics on Twitter, r/sportsbook
    
    Return ONLY:
    1. Crew chief and referees assigned (names)
    2. Crew pace tendency (fast-paced vs slow-paced games)
    3. Foul rate tendency (high FT attempts vs low)
    4. Over/Under tendency for this crew (do games tend to go over or under?)
    
    Max 100 words. If no ref info found, say "Referee assignments not yet available."
    """
    
    try:
        response = requests.post(
            "https://api.perplexity.ai/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "sonar",
                "messages": [
                    {"role": "system", "content": "You are a sports research assistant for NBA officiating. Return ONLY verifiable facts from web sources. Include referee names and their historical tendencies."},
                    {"role": "user", "content": query}
                ],
                "max_tokens": 400,
                "temperature": 0.2,
                "return_citations": True
            },
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            if content and "not yet available" not in content.lower():
                return f"\n=== REFEREE CONTEXT (Perplexity) ===\n{content}\n"
        
        return ""
    
    except Exception:
        return ""


RSS_CACHE: dict = {}
RSS_CACHE_TTL = 20 * 60  # 20 minutes

# Action words used to detect the player-name boundary in RealGM headlines.
# Words that appear BEFORE the first action word are treated as the player name.
_REALGM_ACTION_WORDS = {
    "out", "injured", "questionable", "doubtful", "probable",
    "listed", "miss", "misses", "missing", "return", "returns",
    "returned", "activated", "placed", "undergoes", "underwent",
    "undergo", "suffered", "suffers", "diagnosed", "shut",
    "leaves", "left", "plans", "pushes",
}

# Reject RealGM headline if name candidate contains any of these —
# means the headline is about a team/concept, not a specific player.
_REALGM_TEAM_WORDS = {
    "nba", "trade", "deal", "contract", "draft", "free agency",
    "report", "rumors", "update", "preview", "analysis",
    "lakers", "celtics", "warriors", "nets", "knicks", "heat",
    "bucks", "suns", "nuggets", "clippers", "jazz", "hawks",
    "sixers", "cavaliers", "raptors", "bulls", "pistons",
    "pacers", "magic", "hornets", "grizzlies", "pelicans",
    "spurs", "mavericks", "rockets", "thunder", "blazers",
    "kings", "wolves", "wizards",
}

# Keywords for classifying headline injury severity
_OUT_KEYWORDS = [
    "out ", "out.", "won't play", "will not play", "not expected to play",
    "season-ending", "season ending", "surgery", "shut down",
    "diagnosed with", "suffered", "suffers", "leaves game", "left the game",
    "placed on", "inactive",
]
_DOUBTFUL_KEYWORDS = [
    "doubtful", "unlikely", "iffy",
    "undergo imaging", "undergo an mri", "undergo mri",
]
_GTD_KEYWORDS = [
    "questionable", "game-time", "day-to-day", "limited", "probable",
    "return", "activated",
]

# Lazy-loaded canonical NBA player name set — populated once per process lifetime
_canonical_names: Optional[set] = None


def _parse_rss_date(date_str: str) -> Optional[datetime]:
    """Parse RSS date string to datetime."""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str[:25], "%a, %d %b %Y %H:%M:%S")
    except Exception:
        try:
            return datetime.strptime(date_str[:25], "%Y-%m-%dT%H:%M:%S")
        except Exception:
            return None


def _is_within_24_hours(pub_date: str) -> bool:
    """Check if RSS entry is within last 24 hours."""
    parsed = _parse_rss_date(pub_date)
    if not parsed:
        return True
    age = datetime.now() - parsed
    return age.total_seconds() < 86400


def _fetch_rss_feed(url: str, force: bool = False) -> list:
    """Fetch and parse RSS feed with simple caching."""
    cache_key = url
    
    if not force and cache_key in RSS_CACHE:
        cached_time, cached_data = RSS_CACHE[cache_key]
        age = (datetime.now() - cached_time).total_seconds()
        if age < RSS_CACHE_TTL:
            return cached_data
    
    if not FEEDPARSER_AVAILABLE:
        return []
    
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return []
        
        feed = feedparser.parse(response.content)
        entries = []
        
        for entry in feed.entries:
            if not _is_within_24_hours(getattr(entry, "published", "")):
                continue
            
            title = getattr(entry, "title", "")
            description = getattr(entry, "description", "")
            entries.append({
                "title": title,
                "description": description,
                "published": getattr(entry, "published", ""),
            })
        
        RSS_CACHE[cache_key] = (datetime.now(), entries)
        return entries
    
    except Exception:
        return []


def _load_canonical_names() -> set:
    """Lazy-load normalized NBA player names from canonical DB for RSS validation.
    Returns empty set if canonical.py or DB is unavailable (graceful fallback)."""
    global _canonical_names
    if _canonical_names is not None:
        return _canonical_names
    try:
        from canonical import DB_PATH
        import sqlite3
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT name_normalized FROM canonical_players WHERE is_active = 1")
        _canonical_names = {row[0] for row in c.fetchall()}
        conn.close()
    except Exception:
        _canonical_names = set()
    return _canonical_names


def _extract_player_from_realgm_title(title: str) -> Optional[str]:
    """Extract the player name from a RealGM headline using action word boundary detection.
    Returns words before the first action verb as the player name, or None if not found."""
    words = title.lower().split()
    for i, word in enumerate(words):
        clean_word = word.strip(".,;:")
        if clean_word in _REALGM_ACTION_WORDS:
            name_words = words[:i]
            name_candidate = " ".join(name_words).strip(".,;: ")
            if len(name_words) < 2:
                return None  # single word isn't a full player name
            if any(tw in name_candidate for tw in _REALGM_TEAM_WORDS):
                return None  # team/concept word — not a player headline
            return name_candidate.title()
    return None  # no action word found


def _classify_rss_headline(title: str) -> Optional[str]:
    """Classify an RSS headline into an injury status string.
    Returns 'OUT', 'DOUBTFUL', 'GTD', or None."""
    t = title.lower()
    if any(k in t for k in _OUT_KEYWORDS):
        return "OUT"
    if any(k in t for k in _DOUBTFUL_KEYWORDS):
        return "DOUBTFUL"
    if any(k in t for k in _GTD_KEYWORDS):
        return "GTD"
    return None


def get_rss_news(player_name: str) -> str:
    """
    Fetch Rotowire and RealGM RSS news for a player.
    Filters to last 24 hours only.
    Cache 20 minutes per player.
    """
    if not FEEDPARSER_AVAILABLE:
        return ""
    
    cache_key = f"rss_{player_name.lower()}"
    if cache_key in RSS_CACHE:
        cached_time, cached_result = RSS_CACHE[cache_key]
        age = (datetime.now() - cached_time).total_seconds()
        if age < RSS_CACHE_TTL:
            return cached_result
    
    roto_url = "https://www.rotowire.com/rss/news.php?sport=NBA"
    realgm_url = "https://basketball.realgm.com/rss/wiretap/0/0.xml"
    
    clean_name = player_name.lower().strip()
    news_items = []
    
    roto_entries = _fetch_rss_feed(roto_url)
    for entry in roto_entries:
        title = entry.get("title", "")
        if clean_name in title.lower():
            news_items.append({
                "source": "RotoWire",
                "title": title,
                "description": entry.get("description", ""),
            })
    
    realgm_entries = _fetch_rss_feed(realgm_url)
    canonical_names = _load_canonical_names()
    for entry in realgm_entries:
        title = entry.get("title", "")
        extracted = _extract_player_from_realgm_title(title)
        if extracted is None:
            continue  # headline isn't about a specific player
        # Validate against canonical NBA roster when available
        if canonical_names:
            try:
                from canonical import normalize_name
                if normalize_name(extracted) not in canonical_names:
                    continue  # not a real NBA player
            except Exception:
                pass
        if clean_name not in extracted.lower():
            continue  # not the player we're looking for
        status = _classify_rss_headline(title)
        news_items.append({
            "source": "RealGM",
            "title": title,
            "description": entry.get("description", ""),
            "status": status,
        })

    if not news_items:
        result = ""
    else:
        lines = ["=== RSS NEWS (Last 24h) ==="]
        for item in news_items[:5]:
            status_tag = f"[{item['status']}] " if item.get("status") else ""
            lines.append(f"[{item['source']}] {status_tag}{item['title']}")
            if item.get("description"):
                desc = item["description"]
                if len(desc) > 150:
                    desc = desc[:150] + "..."
                lines.append(f"  {desc}")
        result = "\n".join(lines)
    
    RSS_CACHE[cache_key] = (datetime.now(), result)
    return result


def is_rss_available() -> bool:
    """Check if RSS feeds are available."""
    return FEEDPARSER_AVAILABLE
