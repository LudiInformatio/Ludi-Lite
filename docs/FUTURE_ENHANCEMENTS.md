# Ludi Lite - Future Enhancements

**Last Updated:** February 9, 2026
**Status:** Documented for future sessions

---

## Planned Features (Not Yet Implemented)

These features were identified during competitive research and user testing.
They are documented here for future implementation when priorities allow.

---

### UI/UX Enhancements

| Feature | Description | Inspiration | Priority |
|---------|-------------|-------------|----------|
| **Accordion Cards** | Only one game expanded at a time, others collapse | LandYourBets | MEDIUM |
| **Auto-Run on Expand** | Trigger analysis automatically when user clicks a game | Sharp Hunter | MEDIUM |
| **Hit Rate Dots** | Visual ●●●○○ indicator for L5 performance | LandYourBets | LOW |
| **Line vs Proj Display** | Show +/- differential with color coding (green/red) | LandYourBets | MEDIUM |
| **BOOST Tags** | Badges like "MATCHUP PTS", "MATCHUP AST" for edges | LandYourBets | MEDIUM |

---

### Data Display Features

| Feature | Description | Data Source | Priority |
|---------|-------------|-------------|----------|
| **L15 Games Table** | Last 15 games with DATE, OPP, MIN, USG, FGA, PTS, REB, AST, +/- | Tank01 Box Scores | MEDIUM |
| **Usage Trends** | Recent Min vs Season Min with Diff | player_game_logs | LOW |
| **Injury Impact Panel** | Expandable cards showing who's OUT and beneficiaries | Tank01 + S.A.V.A.G.E. | MEDIUM |
| **INTEL Section** | Soft news like "Coach wants him to shoot more" | Perplexity/RotoWire | LOW |
| **Team Projections Table** | Full roster with MIN, PTS, REB, AST projections | Module C Oracle | HIGH |

---

### Backend/Model Enhancements

| Feature | Description | Implementation | Priority |
|---------|-------------|----------------|----------|
| **Module D AI Upgrade** | Use Perplexity for injury nuance detection | Enhance season_context.py | HIGH |
| **Post-Sim Sanity Check** | AI reviews projections for obvious errors | Add validation layer | MEDIUM |
| **Confidence Scoring** | Signal strength display (Strong/Medium/Speculative) | Edge calculation | LOW |
| **Historical Tracking** | Log picks and results over time | SQLite expansion | MEDIUM |

---

### Competitor Research Sources

- **LandYourBets/Swishland** - Data-first approach with projections tables
- **Sharp Hunter** - Chat-first AI interface with suggested prompts
- **Showstone.io** - AI sports analysis
- **Foxtail Sports** - AI betting assistant

---

## Implementation Notes

1. **Accordion cards** require Streamlit session state management
2. **L15 games table** needs Tank01 historical box score iteration
3. **BOOST tags** map directly to S.A.V.A.G.E. archetype vs scheme logic
4. **Team projections** would require Module C Oracle integration

---

## Current 2025-26 Season Context

When implementing any features, remember:
- **LAC roster**: Kawhi Leonard, James Harden, Norman Powell, Ivica Zubac (NOT Paul George)
- **Recent trades**: Track NBA trade deadline (Feb 6, 2026) impacts
- Tank01 API is source of truth for current rosters
