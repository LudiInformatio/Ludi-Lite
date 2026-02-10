"""
Ludi Lite - Lo-Fi Premium Icon System
"Sanctuary" Theme SVGs to replace generic emojis.
"""

def get_icon(name: str, color: str = "#383531", size: int = 24) -> str:
    """
    Return an inline SVG string for the given icon name.
    """
    # Define icons with minimal whitespace to avoid Markdown code block detection
    icons = {
        # Brand Logo (Shield/Book Concept)
        "logo_main": f'<svg width="{size}" height="{size}" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M24 4L6 12V22C6 33.05 13.92 43.19 24 46C34.08 43.19 42 33.05 42 22V12L24 4ZM24 24H12C12 17.37 17.37 12 24 12V24ZM24 24H36C36 30.63 30.63 36 24 36V24Z" fill="{color}" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
        
        # Methodology / Analysis (Compass/Scale - "Measured Truth")
        "methodology": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><circle cx="12" cy="12" r="10" stroke="{color}" stroke-width="2"/><path d="M16.24 7.76L14.12 14.12L7.76 16.24L9.88 9.88L16.24 7.76Z" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
        
        # Freestyle / AI Research (Prism/Spark - "Raw Intelligence")
        "freestyle": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M12 2L2 22H22L12 2Z" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M12 6L12 18" stroke="{color}" stroke-width="1.5" stroke-linecap="round"/><path d="M6 16L18 16" stroke="{color}" stroke-width="1.5" stroke-linecap="round"/></svg>',
        
        # Time / Schedule (Minimal Clock)
        "time": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><circle cx="12" cy="12" r="9" stroke="{color}" stroke-width="2"/><path d="M12 7V12L15 15" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
        
        # Matchup / Games (Stylized Versus)
        "versus": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><rect x="3" y="3" width="7" height="7" rx="1" stroke="{color}" stroke-width="2"/><rect x="14" y="14" width="7" height="7" rx="1" stroke="{color}" stroke-width="2"/><path d="M7 14L10 10" stroke="{color}" stroke-width="1.5"/><path d="M14 10L17 7" stroke="{color}" stroke-width="1.5"/></svg>',
        
        # Calendar / Upcoming
        "calendar": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><rect x="3" y="4" width="18" height="18" rx="2" stroke="{color}" stroke-width="2"/><path d="M16 2V6" stroke="{color}" stroke-width="2" stroke-linecap="round"/><path d="M8 2V6" stroke="{color}" stroke-width="2" stroke-linecap="round"/><path d="M3 10H21" stroke="{color}" stroke-width="2"/></svg>',

        # Search / Query
        "search": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><circle cx="11" cy="11" r="8" stroke="{color}" stroke-width="2"/><path d="M21 21L16.65 16.65" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>'
    }
    
    return icons.get(name, "")
