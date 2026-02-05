# Ludi Lite - AI Sports Research Lab

A head-to-head comparison tool: **Claude Freestyle** vs **Claude + Ludi Methodology**

Test whether structured betting methodology improves AI analysis over raw Claude capabilities.

## Features

- **Dual Analysis Mode**: Compare raw AI reasoning vs S.A.V.A.G.E. methodology
- **Game Analysis**: Full matchup breakdowns with playtype matrices
- **Player Spotlight**: Deep dives on specific player props
- **All Stats Supported**: PTS, AST, REB, 3PM, STL, BLK, plus combos (PRA, PA, PR, RA, Stocks)
- **Time-Aware**: Analysis confidence adjusts based on time until tipoff
- **2025-26 Season Context**: Current rosters, trades, defense schemes baked in

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

# Set up secrets (copy example and add your API key)
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Edit secrets.toml with your ANTHROPIC_API_KEY

# Run the app
streamlit run app.py
```

## Deploy to Streamlit Cloud (24/7)

1. **Push to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit - Ludi Lite"
   git remote add origin https://github.com/LudiInformatio/ludi-lite.git
   git push -u origin main
   ```

2. **Connect to Streamlit Cloud**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Click "New app"
   - Select your `ludi-lite` repository
   - Set main file path: `app.py`
   - Click "Deploy"

3. **Add Secrets**
   - In Streamlit Cloud, go to your app's Settings
   - Click "Secrets"
   - Add your API keys:
     ```toml
     ANTHROPIC_API_KEY = "sk-ant-api03-..."
     ODDS_API_KEY = "your-key-here"  # Optional
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

## Tech Stack

- **Frontend**: Streamlit
- **AI**: Claude API (Anthropic)
- **Live Data**: Tank01 API (rosters, injuries, depth charts)
- **Odds**: The-Odds-API (game lines, props)
- **Hosting**: Streamlit Cloud
- **CI/CD**: GitHub Actions with Claude Code

## Project Structure

```
ludi-lite/
├── app.py              # Main Streamlit application
├── prompts.py          # Freestyle + Methodology prompts
├── season_context.py   # 2025-26 rosters, schemes, trades
├── tank01_client.py    # Tank01 API client for live NBA data
├── components.py       # UI card components
├── requirements.txt    # Python dependencies
├── setup.sh            # Automated setup script
├── ludi_lite.db        # SQLite database (local cache)
├── README.md           # This file
├── docs/               # Project documentation
│   ├── PRD.md          # Product requirements document
│   └── LUDI_LITE_BUILD_SOP.md  # Build standard operating procedures
└── .streamlit/
    ├── config.toml     # Theme configuration
    └── secrets.toml    # API keys (not in git)
```

## Documentation

- **[Product Requirements (PRD)](docs/PRD.md)** - Full feature specs, user personas, success metrics
- **[Build SOP](docs/LUDI_LITE_BUILD_SOP.md)** - Multi-agent build protocol for development & maintenance

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

