"""
Perplexity API Client for Ludi Lite
Provides real-time web search to enhance Claude Freestyle analysis.
API Docs: https://docs.perplexity.ai/

Uses search_recency_filter for time-bounded searches:
- "hour": Last 60 minutes (pre-game, late scratches)
- "day": Last 24 hours (game day news)
- "week": Last 7 days (trends, matchup history)
"""

import requests
import streamlit as st
from typing import Optional
from datetime import datetime
import pytz


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
    Uses Perplexity's search_recency_filter for time-bounded results.

    Args:
        player_name: Player's name
        opponent: Optional opponent team
        hours_to_game: Hours until tipoff (affects recency filter)

    Returns:
        Formatted context string with recent performance and news
    """
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
