"""
Time utilities for Ludi Lite
Time context, analysis modes, and prompt injection.
"""

from datetime import datetime
import pytz

from season_context import get_full_season_context

# Timezone for game times (Eastern)
ET = pytz.timezone('America/New_York')


def get_time_context() -> dict:
    """Get current time context for analysis"""
    try:
        now_et = datetime.now(ET)
    except Exception:
        now_et = datetime.now()

    hour = now_et.hour

    if hour < 12:
        mode = "EARLY_LOOK"
        confidence = "LOW - Verify closer to game time"
        color = "#FCD34D"
    elif hour < 17:
        mode = "AFTERNOON"
        confidence = "MEDIUM - Watch for updates"
        color = "#60A5FA"
    elif hour < 19:
        mode = "PRE_GAME"
        confidence = "HIGH - Most lineups confirmed"
        color = "#34D399"
    else:
        mode = "LOCK_TIME"
        confidence = "HIGHEST - Games starting"
        color = "#F87171"

    return {
        "timestamp": now_et.strftime("%I:%M %p ET"),
        "date": now_et.strftime("%b %d, %Y"),
        "mode": mode,
        "confidence": confidence,
        "color": color,
        "hour": hour
    }


def build_time_aware_prompt(base_prompt: str, time_context: dict, late_news: str = "") -> str:
    """Inject time context and season data into prompt"""
    # Get current season context (rosters, injuries, etc.)
    season_context = get_full_season_context()

    time_header = f"""
=== ANALYSIS TIMESTAMP ===
Current Time: {time_context['timestamp']} on {time_context['date']}
Analysis Mode: {time_context['mode']}
Confidence: {time_context['confidence']}

{season_context}
"""
    if late_news.strip():
        time_header += f"""
=== LATE NEWS (User Provided - Prioritize This) ===
{late_news}
"""
    return time_header + "\n" + base_prompt
