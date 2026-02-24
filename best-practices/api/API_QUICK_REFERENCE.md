# API Quick Reference — Ludi-Lite

**Purpose:** One-page cheatsheet for data sources, endpoints, and integration patterns

---

## 4-Tier Data Division

| Use Case | Primary | Secondary | Tertiary |
|----------|--------|-----------|----------|
| Games / odds | The-Odds-API | BDL | Tank01 |
| Player props | The-Odds-API | BDL | Tank01 |
| Live rosters | Tank01 | BDL `search_player()` | — |
| Injuries (medical) | Tank01 roster (embedded) | BDL `get_active_injuries()` | — |
| Suspensions | ESPN (new) | `KNOWN_SUSPENSIONS` fallback | — |
| Injuries (fast) | ESPN (new) | Tank01 / BDL | — |
| Recent game logs | BDL (exists) | — | — |
| News / context | Rotowire RSS (new) | RealGM RSS (new) | Perplexity |

---

## The Golden Rules

1. **Never use Claude training data for NBA rosters/trades/injuries** — inject from APIs
2. **Always have a fallback** — ESPN → `KNOWN_SUSPENSIONS`, Tank01 → BDL, etc.
3. **Fail loudly in core pipeline, degrade gracefully in enhancements**
4. **`@st.cache_data` ≠ persistent** — use SQLite for injury data that must survive restarts
5. **Every external API call in Streamlit MUST be wrapped in `@st.cache_data`**

---

## Endpoint Quick Reference

### Tank01
- **Rosters:** `getNBATeams()` → players
- **Games:** `getNBAGamesByDate()`
- **Depth charts:** `getNBADepthCharts()`
- **Box scores:** `getNBABoxScore()`
- Primary for live data (no API key needed)

### BDL (BallDontLie)
- **Advanced stats:** `/nba/v2/stats/advanced`
- **Season averages:** `/v1/season_averages/general`
- **Game logs:** `/v1/stats`
- **Player props:** `/v2/odds/player_props`
- **Requires:** `BALLDON in secrets.toml

TLIE_KEY`### ESPN
- **Injuries:** `https://sports.core.api.espn.com/v2/sports/basketball/leagues/nba/teams/{id}/injuries`
- **Suspensions:** Filter `type_id==17`
- **Team IDs:** ATL=1, BOS=2, NOP=3, CHA=4, CHI=5, CLE=6, DAL=7, DEN=8, DET=9, GS=10, HOU=11, IND=12, LAC=13, LAL=14, MEM=15, MIA=16, MIL=17, MIN=18, BKN=19, NYK=20, ORL=21, PHI=22, PHX=23, POR=24, SAC=25, SA=26, OKC=27, UTA=28, WAS=29, TOR=30
- No API key needed

### Perplexity
- **Use only if RSS returns empty** — expensive
- **Cache minimum:** 20 minutes
- **Model:** sonar for quick, sonar-pro for complex

### The-Odds-API
- **Game odds:** `/odds`
- **Player props:** `/props`
- **Primary odds source** — wrap ALL calls in `@st.cache_data`

---

## Known Broken/Missing Endpoints

| Endpoint | Status | Fix |
|----------|--------|-----|
| NBA Official API | 403 Forbidden | Disabled; use ESPN |
| Tank01 `getNBAInjuryList` | Returns only playerID (unusable) | Use roster endpoint instead |
| BDL suspensions | Not included (disciplinary only) | Use ESPN type_id=17 |

---

## Team Abbreviation Mismatches

Tank01 uses different abbreviations than standard:

| Standard | Tank01 |
|----------|--------|
| PHX | PHO |
| GSW | GS |
| SAS | SA |
| NOP | NO |
| NYK | NY |

Functions in `tank01_client.py`:
- `_to_tank01_abbr()` — standard → Tank01
- `_to_standard_abbr()` — Tank01 → standard

---

## TTL Guidelines

| Data Type | TTL | Reasoning |
|-----------|-----|-----------|
| Odds / games | 5 min | Streamlit re-runs on every interaction |
| Injuries | 15 min (SQLite) | Must survive restart; check snapshot_time |
| Season averages | 24 hours | Changes daily at most |
| RSS news | 20 min | Perplexity fallback only |
| Suspensions | 15 min (SQLite) | ESPN fetch + DB-first pattern |

---

## HTTP Status Code Actions

| Code | Meaning | Action |
|------|---------|--------|
| 200 | Success | Return data |
| 401 | Unauthorized | Check API key, DON'T RETRY |
| 403 | Forbidden | Check permissions, DON'T RETRY |
| 429 | Rate limit | Sleep + retry with backoff |
| 500+ | Server error | Retry later |
