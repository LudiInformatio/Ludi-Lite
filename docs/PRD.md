# Ludi Lite - Product Requirements Document

**Version:** 1.0
**Created:** February 5, 2026
**Owner:** LudiInformatio
**Status:** Ready for Build

---

## Executive Summary

**Ludi Lite** is a mobile-friendly Streamlit web application that provides AI-powered sports betting research through a dual-analysis interface. Users can compare "raw" Claude analysis against Claude enhanced with the S.A.V.A.G.E. methodology from the parent Ludi-Bot project.

### Vision Statement
Democratize sports betting research by providing side-by-side AI analysis: one from general Claude intelligence and one from Claude trained on proprietary NBA analytics methodology.

---

## Product Overview

### What is Ludi Lite?

A lightweight research dashboard that allows users to:
1. View today's NBA games with live spreads and totals
2. Ask natural language questions about games, players, or props
3. Compare two analysis modes side-by-side:
   - **Freestyle**: Raw Claude intelligence
   - **Ludi Method**: Claude + S.A.V.A.G.E. framework

### Parent Project Relationship

Ludi Lite is a **consumer-facing interface** for the Ludi-Bot engine:

```
┌─────────────────────────────────────────────────────────────┐
│                      LUDI-BOT                               │
│  Full Analytics Engine                                       │
│  - Monte Carlo Simulations                                   │
│  - Injury Intelligence                                       │
│  - Referee Impact                                            │
│  - Matchup Matrix                                            │
│  - Edge Calculation                                          │
│  - Automated Betting Pipeline                                │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ Methodology + Context
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      LUDI-LITE                              │
│  Consumer Research Dashboard                                 │
│  - Dual Analysis Interface                                   │
│  - Natural Language Input                                    │
│  - Mobile-First Design                                       │
│  - Time-Aware Context                                        │
└─────────────────────────────────────────────────────────────┘
```

---

## User Personas

### Primary: The Casual Bettor
- **Profile**: Sports fan who bets recreationally
- **Needs**: Quick research before placing bets
- **Pain Points**: Information overload, no framework for analysis
- **Use Case**: "Should I bet Luka over 28.5 points tonight?"

### Secondary: The Serious Researcher
- **Profile**: Dedicated bettor seeking an edge
- **Needs**: Multiple perspectives on the same bet
- **Pain Points**: Echo chamber analysis, confirmation bias
- **Use Case**: "Compare raw AI take vs methodology-backed analysis"

### Tertiary: The Mobile User
- **Profile**: Bets on the go, often at games or with friends
- **Needs**: Fast, mobile-friendly interface
- **Pain Points**: Desktop-only tools, slow load times
- **Use Case**: "Quick check on my phone before lock"

---

## Core Features

### 1. Today's Games Dashboard
**Priority:** P0 (Must Have)

Display clickable game cards showing:
- Matchup (Away @ Home)
- Spread and total
- Game time (Eastern)
- Click to analyze

**Data Source:** The-Odds-API (via ODDS_API_KEY)

### 2. Dual Analysis Mode
**Priority:** P0 (Must Have)

Side-by-side comparison:

| Freestyle | Ludi Method |
|-----------|-------------|
| Raw Claude analysis | Claude + S.A.V.A.G.E. |
| General sports knowledge | Usage Vacuum, Matchup Matrix |
| No framework constraints | Archetype vs Defense |
| Blue header/border | Green header/border |

### 3. Natural Language Input
**Priority:** P0 (Must Have)

Parse user queries into structured requests:

**Supported Patterns:**
- Games: "DEN vs NYK", "Lakers @ Suns"
- Players: "Luka", "Jokic rebounds"
- Props: "Trae points 28.5", "Luka PRA over 45"
- Combos: "PRA", "PA", "stocks"

**Stat Aliases:**
- Points: pts, points, scoring
- Assists: ast, assists, dimes
- Rebounds: reb, boards, trb
- 3PM: 3s, threes, triples
- Combos: PRA, PA, PR, RA, stocks

### 4. Time-Aware Context
**Priority:** P1 (Should Have)

Adjust confidence based on tipoff proximity:

| Time | Mode | Confidence | Badge Color |
|------|------|------------|-------------|
| Before noon | EARLY_LOOK | LOW | Yellow |
| Noon - 5 PM | AFTERNOON | MEDIUM | Blue |
| 5 - 7 PM | PRE_GAME | HIGH | Green |
| After 7 PM | LOCK_TIME | HIGHEST | Red |

### 5. Manual Input Fallback
**Priority:** P2 (Nice to Have)

Expandable form for detailed manual entry:
- Game: teams, spread, total, context
- Player: name, team, opponent, stat focus
- Late news injection

### 6. Analysis History
**Priority:** P2 (Nice to Have)

SQLite storage for:
- Past queries
- Freestyle responses
- Methodology responses
- Timestamps

---

## S.A.V.A.G.E. Framework Integration

The Ludi Method prompt incorporates these principles from Ludi-Bot:

### 1. Usage Vacuum Theory
When a star is OUT, usage redistributes to teammates.
- Example: "With Embiid OUT, Maxey usage increases 8%"

### 2. Archetype vs Defense Scheme
Player style impacts performance against specific defenses:

| Archetype | vs PAINT_PACK | vs BLITZ | vs SWITCH |
|-----------|---------------|----------|-----------|
| STRETCH_BIG | +15% 3PM | Neutral | -5% |
| SLASHER | +10% FTA | -8% PTS | Neutral |
| ISO_SCORER | Neutral | -8% | +5% |

### 3. Pace Context
Game total impacts volume:
- High total (>235): +volume for pace players
- Low total (<210): -volume, favor efficiency

### 4. Blowout Tax
Large spreads reduce starter minutes:
- 10+ spread: -5% volume
- 15+ spread: -15% volume (garbage time risk)

### 5. B2B Fatigue
Back-to-back games impact performance:
- Road B2B: -4.8% production
- Home B2B: -1.5% production
- Guards hit hardest: additional -2%

### 6. Line Movement Intelligence
Market signals provide context:
- Sharp money movement
- Steam moves
- Reverse line movement

---

## Technical Requirements

### Stack
- **Framework:** Streamlit
- **Language:** Python 3.11+
- **Database:** SQLite (local)
- **APIs:** Claude (Anthropic), The-Odds-API
- **Deployment:** Streamlit Cloud

### Dependencies (requirements.txt)
```
streamlit
anthropic
requests
pytz
```

### API Keys Required
| Key | Purpose | Source |
|-----|---------|--------|
| ANTHROPIC_API_KEY | Claude API calls | Streamlit secrets or env |
| ODDS_API_KEY | Live game data | Streamlit secrets or env |

### File Structure
```
ludi-lite/
├── app.py                 # Main Streamlit app
├── prompts.py             # AI prompts (Freestyle, Method, Player)
├── season_context.py      # Team schemes, current season
├── components.py          # Reusable UI components
├── requirements.txt       # Python dependencies
├── README.md              # Setup instructions
├── .streamlit/
│   ├── config.toml        # Streamlit config
│   └── secrets.toml.example
├── .github/
│   └── workflows/
│       └── daily_health_check.yml
└── docs/
    ├── PRD.md             # This document
    └── LUDI_LITE_BUILD_SOP.md
```

---

## UI/UX Requirements

### Design Principles
1. **Mobile-First**: Optimized for phone screens
2. **Dark Theme**: Matches Ludi-Bot aesthetic
3. **Minimal Chrome**: Hide Streamlit branding
4. **Fast Interaction**: Single-tap game selection

### Color Palette (Current - User May Customize)
| Element | Color | Usage |
|---------|-------|-------|
| Background | #0F172A | Main app background |
| Card BG | #1E293B | Game cards, panels |
| Accent | #FBBF24 | Headers, highlights |
| Freestyle | #60A5FA | Blue panel border |
| Method | #10B981 | Green panel border |
| Text | #F8FAFC | Primary text |
| Muted | #94A3B8 | Secondary text |

**Note:** User requested generic template - colors may be removed/customized later.

### Responsive Breakpoints
- Mobile: < 768px (primary target)
- Tablet: 768px - 1024px
- Desktop: > 1024px

---

## Success Metrics

### Launch Criteria
- [ ] App loads on Streamlit Cloud
- [ ] Game cards display (with API key)
- [ ] Dual analysis completes in < 30s
- [ ] Mobile layout renders correctly
- [ ] No exposed secrets

### Post-Launch KPIs
| Metric | Target | Measurement |
|--------|--------|-------------|
| Page Load | < 3s | Streamlit metrics |
| Analysis Time | < 30s | In-app timing |
| Error Rate | < 5% | Health check workflow |
| Daily Active Queries | Track | SQLite logs |

---

## Integration Points

### Ludi-Bot (Parent Project)
- **Location:** `/home/user/Ludi-Bot/`
- **Shared:** Methodology documentation, defense schemes
- **Independent:** Ludi Lite has its own database, no shared state

### Slack Notifications
- **Workspace:** Vibe Starters
- **App:** Claude Agents
- **Channel:** #ludi-lite-health
- **Trigger:** Daily health check workflow

### GitHub Actions
- **Workflow:** daily_health_check.yml
- **Schedule:** 6 AM EST daily (when enabled)
- **Auth:** CLAUDE_CODE_OAUTH_TOKEN (same as Ludi-Bot)

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Odds API downtime | No game cards | Manual input fallback |
| Claude API rate limits | Slow/failed analysis | Caching, error handling |
| Streamlit Cloud limits | App unavailable | Monitor usage, upgrade if needed |
| Mobile layout breaks | Poor UX | Responsive CSS, testing |

---

## Future Roadmap

### Phase 2 (Post-Launch)
- [ ] Save favorite players/games
- [ ] Historical analysis view
- [ ] Push notifications for late news
- [ ] Dark/light theme toggle

### Phase 3 (Integration)
- [ ] Pull real-time edge data from Ludi-Bot
- [ ] Display Diamond Plays directly
- [ ] Sync with Telegram bot

### Phase 4 (Advanced)
- [ ] User accounts
- [ ] Bet tracking
- [ ] Performance analytics

---

## Approval & Sign-Off

| Role | Name | Date |
|------|------|------|
| Product Owner | LudiInformatio | Feb 5, 2026 |
| Build Lead | PM Agent (Claude) | TBD |
| QA Lead | QA Agent (Claude) | TBD |

---

**End of PRD v1.0**

