# Ludi-Lite — Claude Code Instructions

## Data Integrity (Critical)

**NEVER use training knowledge for live NBA data.** This covers:
- Player rosters and team assignments
- Trade status (deadline or offseason moves)
- Injuries, suspensions, availability
- Season stats, game logs, box scores
- Game schedules, odds, lines, props

**ALWAYS fetch from the project's live sources in this priority order:**

| Priority | Source | Module | Use For |
|----------|--------|--------|---------|
| 1st | SQLite cache (`ludi_lite.db`) | `database.py` | Recent data with freshness check |
| 2nd | Tank01 | `tank01_client.py` | Live rosters, games, depth charts |
| 3rd | BDL / BallDontLie | `bdl_client.py` | Stats, game logs, season averages |
| 4th | ESPN | `espn_client.py` | Injuries, suspensions (type_id=17) |
| 5th | Perplexity | `perplexity_client.py` | Real-time news (expensive — last resort) |

**For mock/test scenarios:** Use clearly labeled fake data. Do NOT substitute recalled
training facts about real players (e.g., don't recall "LeBron plays for LAL" from memory).

> **Why this matters:** Claude's training data has a knowledge cutoff and will confidently
> hallucinate trades, injuries, and rosters that are months out of date. Ludi-Lite's entire
> value depends on current, API-sourced data.

---

## App Setup

```bash
# Run the app
streamlit run app.py

# Install dependencies (if needed)
pip install -r requirements.txt
```

**API Keys:** All in `.streamlit/secrets.toml` (not tracked by git).
Required: `ANTHROPIC_API_KEY`. Optional: `TANK01_KEY`, `ODDS_API_KEY`, `PERPLEXITY_API_KEY`, `BALLDONTLIE_KEY`.

---

## Architecture Rules

- **Do not create new API client files.** All data sources already have modules.
- **Do not add modules** without updating the import graph in `best-practices/README.md`.
- **All external API calls in Streamlit must be wrapped in `@st.cache_data`** — no exceptions.
- **New database tables** follow the pattern in `best-practices/data/DATA_MODELING.md`.

### Key Module Responsibilities

| Module | Owns |
|--------|------|
| `app.py` | Config, CSS, `main()`, `_get_vacuum_context()` |
| `query_parser.py` | NLP parsing, nickname resolution |
| `prompts.py` | All Claude prompt assembly |
| `usage_calculator.py` | S.A.V.A.G.E. stat bump logic |
| `season_context.py` | Live rosters, `KNOWN_SUSPENSIONS` fallback |
| `injury_verification.py` | Multi-source injury/suspension checking |

---

## Critical Gotchas

- **Team abbreviations differ by API:** PHX→PHO, GSW→GS, SAS→SA, NOP→NO, NYK→NY
  Use `_to_tank01_abbr()` / `_to_standard_abbr()` in `tank01_client.py`
- **BDL stats need `season=2025`** — without it, returns historical data
- **BDL does NOT return suspensions** — ESPN only
- **Tank01 removes suspended players from rosters entirely** — they won't appear

---

## Best Practices Reference

Full patterns live in `best-practices/` — consult before adding new code:

| Topic | File |
|-------|------|
| API data sources & endpoints | `best-practices/api/API_QUICK_REFERENCE.md` |
| Claude/Perplexity prompting | `best-practices/api/LLM_INTEGRATION.md` |
| Python & Streamlit patterns | `best-practices/coding/CODING_STANDARDS.md` |
| SQLite schema rules | `best-practices/data/DATA_MODELING.md` |
| Prompt structure | `best-practices/prompts/PROMPT_PATTERNS.md` |
| Known bugs & fixes | `best-practices/debugging/DEBUGGING_PLAYBOOK.md` |
