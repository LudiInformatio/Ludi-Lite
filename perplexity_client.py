"""
Perplexity API Client for Ludi Lite
Provides real-time web search to enhance Claude Freestyle analysis.
API Docs: https://docs.perplexity.ai/
"""

import requests
import streamlit as st
from typing import Optional


def _get_api_key() -> Optional[str]:
    """Get Perplexity API key from Streamlit secrets or environment"""
    try:
        return st.secrets.get("PERPLEXITY_API_KEY")
    except Exception:
        import os
        return os.getenv("PERPLEXITY_API_KEY")


def search_game_context(away_team: str, home_team: str) -> str:
    """
    Search for real-time context about a game matchup.

    Args:
        away_team: Away team name or abbreviation
        home_team: Home team name or abbreviation

    Returns:
        Formatted context string with recent news, injuries, and insights
    """
    api_key = _get_api_key()
    if not api_key:
        return ""  # Silently skip if no API key

    query = f"""
    NBA game {away_team} vs {home_team} today.
    Provide brief bullet points on:
    1. Key injuries for both teams
    2. Recent form (last 5 games)
    3. Any relevant news or storylines
    Keep response under 200 words.
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
                "temperature": 0.2
            },
            timeout=15
        )

        if response.status_code == 200:
            data = response.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            if content:
                return f"\n=== REAL-TIME CONTEXT (Perplexity Search) ===\n{content}\n"

        return ""

    except Exception as e:
        return ""  # Silently fail - don't break the app


def search_player_context(player_name: str, opponent: str = "") -> str:
    """
    Search for real-time context about a specific player.

    Args:
        player_name: Player's name
        opponent: Optional opponent team

    Returns:
        Formatted context string with recent performance and news
    """
    api_key = _get_api_key()
    if not api_key:
        return ""

    opp_text = f"against {opponent}" if opponent else ""
    query = f"""
    NBA player {player_name} {opp_text} latest news and performance.
    Provide brief bullet points on:
    1. Recent stats (last 5 games if available)
    2. Current injury/health status
    3. Any relevant matchup notes
    Keep response under 150 words.
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
                "temperature": 0.2
            },
            timeout=15
        )

        if response.status_code == 200:
            data = response.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            if content:
                return f"\n=== REAL-TIME PLAYER INFO (Perplexity Search) ===\n{content}\n"

        return ""

    except Exception:
        return ""


def is_perplexity_available() -> bool:
    """Check if Perplexity API is configured"""
    return _get_api_key() is not None
