# Debugging Playbook — Ludi-Lite

**Status:** Active (Feb 2026)
**Purpose:** Known incidents and troubleshooting sequences for Streamlit NBA prop analysis app

---

## Ludi-Lite Known Incidents

| Date | Incident | Fix | Prevention |
|------|---------|-----|-----------|
| Feb 2026 | **The-Odds-API quota exhausted** — Streamlit re-runs the entire script on every page interaction/refresh. Without `@st.cache_data`, `fetch_todays_games()` called The-Odds-API on every widget click, burning the monthly quota | Added `@st.cache_data(ttl=300)` to all odds/games fetchers | **RULE:** Every external API call in Streamlit MUST be wrapped in `@st.cache_data`. Default Streamlit re-execution = N users × N interactions × full API call |
| Feb 2026 | NBA Official API → 403 | Disabled; using ESPN | Check status codes, don't assume endpoints are permanent |
| Feb 2026 | Tank01 `getNBAInjuryList` returns only playerID | Use roster endpoint instead | Test each endpoint with real response before building logic |
| Feb 2026 | BDL suspensions not returned (only medical) | ESPN type_id=17 for suspensions | Know data source limits before designing dependency |
| Feb 2026 | `@st.cache_data` doesn't persist through Streamlit restart | SQLite `player_injuries` table | Any data that must survive restarts → SQLite |
| Feb 2026 | Trade chain hallucination (AD: Claude thinks LAL→LAL, real: LAL→DAL→WAS) | API-only WOWY detection via BDL game logs | Never use Claude training data for trades |
| Feb 2026 | `bdl_client.py` nearly re-created (already existed) | Read-first → found the file | Always glob/search project before creating new files |
| Feb 2026 | `get_recent_game_logs()` missing `team` field | Add 1 line: `"team": game.get("team", {}).get("abbreviation", "")` | Check actual response dict keys against log_entry before building logic |

---

## Streamlit Debugging Sequence

When app behaves unexpectedly:

1. **Check console for Python exceptions** — not just browser errors
2. **Add `st.write(variable)` temporarily** to inspect state
3. **Clear Streamlit cache:** Settings → Clear Cache or `st.cache_data.clear()`
4. **Check `st.session_state` keys** for stale values
5. **Verify secrets.toml keys** match what the client reads

---

## API Debugging Sequence

1. **Check for HTTP status codes:**
   - 401 → wrong API key
   - 403 → endpoint moved/blocked
   - 429 → rate limit hit
2. **Print raw response** before parsing — never assume structure
3. **Use `inspect.signature()`** to verify function parameters haven't changed after updates

---

## Error Handling Hierarchy

| Code type | Strategy | Example |
|-----------|----------|---------|
| Core pipeline (odds, props) | Fail loudly | Raise exception, stop execution |
| Enhancement (Perplexity, RSS) | Degrade gracefully | Return empty/fallback, log warning |
| Background sync | Log + continue | `print(f"[ERROR] {e}")` then continue |

---

## Key Anti-Patterns

| Anti-Pattern | Why It's Bad | Fix |
|-------------|-------------|-----|
| `except: pass` | Hides every error forever | Always `print(f"[ERROR] {e}")` |
| No `@st.cache_data` on Streamlit API calls | Burns quota on every interaction | Add decorator to all external calls |
| Using Claude training data for NBA facts | Outdated rosters, trades, injuries | Inject from APIs |
| Bare `except Exception: continue` | Silent data loss | Log before continuing |
