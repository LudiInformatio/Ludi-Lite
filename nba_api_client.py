"""
NBA API Client for Ludi Lite
Provides game officials from BoxScoreSummaryV3 endpoint.

Note: BoxScoreSummaryV3 returns officials for free (V2 is broken after April 2025).
"""

import streamlit as st
from typing import List, Dict, Optional


@st.cache_data(ttl=3600)
def get_game_officials(game_id: int) -> str:
    """
    Get game officials from NBA.com BoxScoreSummaryV3.
    
    Args:
        game_id: NBA.com game ID
        
    Returns:
        Formatted string with referee crew names
    """
    try:
        from nba_api.stats.endpoints.boxscoresummaryv3 import BoxScoreSummaryV3
        
        summary = BoxScoreSummaryV3(game_id=game_id)
        data = summary.get_dict()
        
        # V3 response structure: { "boxScoreSummary": { "officials": [...] } }
        officials = data.get("boxScoreSummary", {}).get("officials", [])
        
        if not officials:
            return ""
        
        official_names = []
        for off in officials:
            # V3 field names: name, nameI, firstName, familyName, jerseyNum, assignment
            name = off.get("name", "")
            role = off.get("assignment", "")
            jersey = off.get("jerseyNum", "").strip()
            if name:
                label = f"{name} (#{jersey})" if jersey else name
                if role:
                    label += f" [{role}]"
                official_names.append(label)
        
        if official_names:
            return f"=== GAME OFFICIALS (NBA.com) ===\n" + " | ".join(official_names) + "\n"
        
        return ""
    
    except Exception:
        return ""


def is_nba_api_available() -> bool:
    """Check if nba_api is available"""
    try:
        import nba_api
        return True
    except Exception:
        return False
