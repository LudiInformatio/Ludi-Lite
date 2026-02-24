# Ludi Lite - AI Sports Research Lab

A head-to-head comparison tool: **Claude Freestyle** vs **Claude + Ludi Methodology**

Test whether structured betting methodology improves AI analysis over raw Claude capabilities.

## Features

- **Dual Analysis Mode**: Compare raw AI reasoning vs S.A.V.A.G.E. methodology
- **Game Analysis**: Full matchup breakdowns with playtype matrices
- **Player Spotlight**: Deep dives on specific player props
- **All Stats Supported**: PTS, AST, REB, 3PM, STL, BLK, plus combos (PRA, PA, PR, RA, Stocks)
- **Time-Aware**: Analysis confidence adjusts based on time until tipoff
- **Live Injury + Suspension Intel**: ESPN-sourced suspensions (type_id=17), cached in SQLite
- **WOWY Trade Detection**: Detects mid-season trades via BDL game logs — shows new-team stats only
- **RSS News**: Rotowire + RealGM headlines injected before analysis. Perplexity only if RSS is empty
- **Canonical Player Table**: BDL ↔ Tank01 ↔ SportsDataIO ID crosswalk, synced on startup
- **2025-26 Season Context**: Current rosters, trades, defense/offense schemes baked in

## Quick Start (Local)

```bash
# Clone the repo
git clone https://github.com/LudiInformatio/ludi-lite.git
cd ludi-lite

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up secrets (copy example and add your API keys)
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Edit secrets.toml with your keys (see section below)

# Run the app
streamlit run app.py
```

## Deploy to Streamlit Cloud (24/7)

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "feat: deploy"
   git push
   ```

2. **Connect to Streamlit Cloud**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Click "New app" → select your `ludi-lite` repo
   - Set main file path: `app.py`
   - Click "Deploy"

3. **Add Secrets**
   In Streamlit Cloud → App Settings → Secrets:
   ```toml
   # Required
   ANTHROPIC_API_KEY = "your-anthropic-api-key"

   # Recommended (live data)
   TANK01_KEY = "your-rapidapi-key"        # Rosters, depth charts, box scores
   BALLDONTLIE_KEY = "your-bdl-key"        # Stats, game logs, odds fallback
   ODDS_API_KEY = "your-odds-api-key"      # Game lines, player props (primary)

   # Optional (enhanced Freestyle)
   PERPLEXITY_API_KEY = "pplx-..."         # Real-time web search (RSS used first)
   SPORTSDATA_API_KEY = "your-key"         # Canonical player ID crosswalk
   ```

4. **Done!** Your app will be live at `https://your-app.streamlit.app`

## Usage

### Game Analysis
Type natural language queries like:
- `DEN vs NYK` - Full game breakdown
- `Lakers Celtics` - Matchup analysis
- `tonight's games` - Show today's slate

### Player Props
- `Luka assists 8.5` - Player prop analysis
- `Jokic PRA` - Points + Rebounds + Assists combo
- `Tatum points rebounds` - Multiple stat focus

### Supported Stats
| Single Stats | Combo Props |
|--------------|-------------|
| PTS, AST, REB | PRA (PTS+REB+AST) |
| 3PM, STL, BLK | PA (PTS+AST) |
| TO, MIN, FGM, FTM | PR (PTS+REB) |
| | RA (REB+AST) |
| | Stocks (STL+BLK) |

## The Methodology

**S.A.V.A.G.E. Framework:**
1. **Usage Vacuum Theory** - Redistribution when stars are OUT
2. **Archetype vs Defense Scheme** - Player style vs team defense matchups
3. **Pace Context** - Game total impact on volume
4. **Blowout Tax** - Spread impact on starter minutes
5. **B2B Fatigue** - Schedule density adjustments
6. **Line Movement Intelligence** - Market signal interpretation

## Time Context

Analysis confidence varies by time:
| Badge | Time to Tipoff | Confidence |
|-------|----------------|------------|
| EARLY LOOK | 6+ hours | Low (lineups TBD) |
| AFTERNOON | 2-6 hours | Medium |
| PRE-GAME | 30min-2hr | High |
| LOCK TIME | <30 min | Highest |

## Data Sources & APIs

### AI
- **Claude API (Anthropic)** - claude-sonnet-4-6 for analysis
- **Perplexity API** (Optional) - Real-time web search for Freestyle mode (RSS feeds checked first)

### Data Priority Chain
| Priority | Source | Used For |
|----------|--------|---------|
| 1st | SQLite cache (`ludi_lite.db`) | Recent data with freshness check |
| 2nd | Tank01 | Live rosters, games, depth charts |
| 3rd | BDL / BallDontLie | Stats, game logs, season averages, odds fallback |
| 4th | ESPN (free, no key) | Injuries + suspensions (type_id=17) |
| 5th | Perplexity | Real-time news (last resort — RSS used first) |

### Tank01 API (RapidAPI)
| Endpoint | Purpose |
|----------|---------|
| `getNBATeamRoster` | Current rosters with stats |
| `getNBATeams` | All 30 teams with rosters |
| `getNBAGamesForDate` | Today's games |
| `getNBADepthCharts` | Starters vs backups |
| `getNBABoxScore` | Historical game stats |

> **Note:** `getNBAInjuryList` returns only playerID — unusable. Use ESPN for injuries/suspensions.

### BDL / BallDontLie API
| Endpoint | Purpose |
|----------|---------|
| `get_recent_game_logs()` | L5/L10 trends, WOWY trade detection |
| `get_season_averages()` | Full-season stats |
| `get_odds()` | Spreads/totals (fallback if The-Odds-API down) |
| `get_player_props()` | Prop lines (fallback) |
| `get_active_injuries()` | Medical injuries (not suspensions) |

### The-Odds-API
| Market | Type |
|--------|------|
| `spreads` | Point spreads |
| `totals` | Over/under |
| `h2h` | Moneyline |
| `player_points` | PTS props |
| `player_rebounds` | REB props |
| `player_assists` | AST props |
| `player_threes` | 3PM props |
| `player_steals` | STL props |
| `player_blocks` | BLK props |
| `player_points_rebounds_assists` | PRA combo |
| `player_points_assists` | PA combo |
| `player_points_rebounds` | PR combo |
| `player_assists_rebounds` | AR combo |
| `player_double_double` | DD Yes/No |
| `player_triple_double` | TD Yes/No |

### ESPN API (free, no key)
- Injuries and suspensions per team
- `type_id=17` = suspension
- Cached in SQLite with TTL based on time-to-tipoff (20min–4hr)
- Fallback: `KNOWN_SUSPENSIONS` dict in `season_context.py`

## Tech Stack

- **Frontend**: Streamlit
- **AI**: Claude API (Anthropic) + Perplexity (optional)
- **Live Data**: Tank01 (rosters, games) + BDL (stats, logs) + ESPN (injuries/suspensions)
- **Odds**: The-Odds-API (primary) → BDL (fallback) → Tank01 (fallback)
- **News**: Rotowire RSS + RealGM RSS → Perplexity (fallback)
- **Player IDs**: Canonical SQLite crosswalk (BDL ↔ Tank01 ↔ SportsDataIO)
- **Hosting**: Streamlit Cloud
- **CI/CD**: GitHub Actions (injury refresh schedule)

## Project Structure

```
ludi-lite/
├── app.py                  # Main Streamlit app + startup hooks
├── api_clients.py          # 3-tier odds/props fetch chain
├── prompts.py              # Dynamic prompt assembly
├── season_context.py       # Rosters, schemes, suspensions, trends
├── query_parser.py         # NLP parsing, nickname resolution
├── usage_calculator.py     # S.A.V.A.G.E. stat bump + WOWY trade detection
├── injury_verification.py  # Multi-source injury/suspension checker
├── canonical.py            # Player ID crosswalk (BDL↔Tank01↔SportsDataIO)
├── tank01_client.py        # Tank01 API client
├── bdl_client.py           # BallDontLie API client
├── espn_client.py          # ESPN injury/suspension client (free, no key)
├── perplexity_client.py    # Perplexity search + RSS feeds
├── database.py             # SQLite init (analyses, injuries, canonical tables)
├── time_utils.py           # Time context + prompt injection (4 modes)
├── team_mapping.py         # Cross-API team name normalization
├── ui_components.py        # render_* functions
├── components.py           # Advanced UI cards (Private Study palette)
├── requirements.txt        # Python dependencies
├── ludi_lite.db            # SQLite cache (not in git)
├── best-practices/         # Dev standards + debugging playbook
│   ├── README.md
│   ├── api/
│   │   ├── API_QUICK_REFERENCE.md
│   │   └── LLM_INTEGRATION.md
│   ├── coding/
│   │   └── CODING_STANDARDS.md
│   ├── data/
│   │   └── DATA_MODELING.md
│   ├── prompts/
│   │   └── PROMPT_PATTERNS.md
│   └── debugging/
│       └── DEBUGGING_PLAYBOOK.md
├── docs/
│   ├── PRD.md
│   └── LUDI_LITE_BUILD_SOP.md
└── .streamlit/
    ├── config.toml         # Theme configuration
    └── secrets.toml        # API keys (not in git)
```

## Documentation

- **[Product Requirements (PRD)](docs/PRD.md)** - Full feature specs, user personas, success metrics
- **[Build SOP](docs/LUDI_LITE_BUILD_SOP.md)** - Multi-agent build protocol for development & maintenance
- **[Best Practices](best-practices/README.md)** - API reference, coding standards, debugging playbook

## The Experiment

Run for 30 days, logging analyses. At the end, compare:
- When did Freestyle and Methodology agree?
- When they disagreed, who was right more often?
- Did the structured methodology add value?

This answers the question: **Does my betting methodology actually improve AI predictions?**

## License

MIT - Use freely, no warranties.

---

*Built for the 2025-26 NBA season by Ludi Informatio*
