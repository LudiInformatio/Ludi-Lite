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

    TRUSTED SOURCES: @underdognba Twitter, ESPN injury report, official team accounts

    STATUS KEYWORDS:
    - OUT: "ruled out", "won't play", "suspended", "inactive"
    - GTD: "questionable", "game-time decision", "day-to-day"
    - ACTIVE: "cleared", "will play", "probable"

    Return ONLY:
    1. Players OUT/DOUBTFUL/SUSPENDED (name + status)
    2. Recent team form (last 3 games W/L)
    3. Breaking news from THIS SEASON only

    Max 100 words. Bullets only. No old recaps or percentage projections.
    """

    try:
        response = requests.post(
            "https://api.perplexity.ai/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.1-sonar-small-128k-online",
                "messages": [
                    {"role": "user", "content": query}
                ],
                "max_tokens": 500,
                "temperature": 0.2,
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
                "model": "llama-3.1-sonar-small-128k-online",
                "messages": [
                    {"role": "user", "content": query}
                ],
                "max_tokens": 400,
                "temperature": 0.2,
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
                "model": "llama-3.1-sonar-small-128k-online",
                "messages": [
                    {"role": "user", "content": query}
                ],
                "max_tokens": 200,
                "temperature": 0.1,
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


def is_perplexity_available() -> bool:
    """Check if Perplexity API is configured"""
    return _get_api_key() is not None
