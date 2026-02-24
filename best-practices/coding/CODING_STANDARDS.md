# Coding Standards — Ludi-Lite

**Purpose:** Python rules and Streamlit-specific patterns

---

## Core Rules

### CRITICAL: Every External API Call MUST Be Wrapped in `@st.cache_data`

Streamlit re-executes the entire script on every widget click, refresh, or user interaction. Without caching, each interaction = a new API call. This burned The-Odds-API quota.

```python
# ❌ BAD: Every page refresh = new API call
def fetch_todays_games():
    response = requests.get("https://api.the-odds-api.com/...")
    return response.json()

# ✅ GOOD: Cache for 5 minutes
@st.cache_data(ttl=300)
def fetch_todays_games():
    response = requests.get("https://api.the-odds-api.com/...")
    return response.json()
```

**TTL decision guide:**
- Odds/games: 300 seconds (5 min)
- Injuries (SQLite-backed): 900 seconds (15 min)
- RSS news: 1200 seconds (20 min)
- Season averages: 86400 seconds (24 hours)

---

## Never Bare `except: pass`

This incident: API returning wrong data went undetected for days because errors were swallowed.

```python
# ❌ Silent failure — NEVER do this
for row in rows:
    try:
        process_row(row)
    except Exception:
        continue  # Error is completely invisible

# ✅ Minimum: always log before continuing
for row in rows:
    try:
        process_row(row)
    except Exception as e:
        print(f"[ERROR] Row {row.get('id', '?')} failed: {e}")
        continue
```

---

## Lazy Imports for Optional Dependencies

Tank01, BDL, and Perplexity are not always available. Import them inside functions, not at module level.

```python
# ❌ Module-level import — fails at import time if not configured
import anthropic

def generate_analysis():
    client = anthropic.Anthropic()

# ✅ Lazy import — only fails if the function is actually called
def generate_analysis():
    import anthropic
    client = anthropic.Anthropic()
```

---

## Tuple Unpacking with `_`

When a function returns more values than you need, use `_` to explicitly discard them.

```python
# ❌ Crashes if function returns 3 values but you unpack 2
briefing, image_path = generate_report(props)

# ✅ Explicit discard — signals "I know there's more, I don't need it"
briefing, image_path, _ = generate_report(props)
```

**Before changing any function's return count:**
```bash
grep -rn "your_function_name(" --include="*.py" .
```

---

## Streamlit-Specific Rules

### Session State Naming Conventions
```python
# ✅ Use descriptive names with underscore
st.session_state.selected_player
st.session_state.current_analysis

# ❌ Avoid generic names
st.session_state.data
st.session_state.val
```

### Error Display Hierarchy
- `st.error()` — user-facing errors that need attention
- `logger.error()` or `print()` — silent errors for debugging

### No Module-Level Client Initialization

```python
# ❌ BAD: Re-runs on every Streamlit re-execution
import anthropic
client = anthropic.Anthropic(api_key=TOKEN)

# ✅ GOOD: Use _get_client() singleton pattern or lazy init
@st.cache_data
def _get_client():
    import anthropic
    return anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
```

### The `_self` Pattern for @st.cache_data on Class Methods

```python
class BDLClient:
    @st.cache_data(show_spinner=False)
    def _self(self, _player_id, _season):
        # _ prefix tells st.cache_data to use the actual arguments, not 'self'
        return self._fetch_player_stats(_player_id, _season)
```

---

## Error Handling Hierarchy

| Code type | Strategy | Example |
|-----------|----------|---------|
| Core pipeline (odds, props) | Fail loudly | `raise Exception()` |
| Enhancement (Perplexity, RSS) | Degrade gracefully | Return empty/fallback |
| Background sync | Log + continue | `print("[ERROR] {e}")` then continue |

---

## Module Return Contracts

When you change what a function returns, you change its contract with all callers. Treat this as a breaking change.

**Checklist before changing return signature:**
1. Find all call sites: `grep -rn "function_name(" --include="*.py" .`
2. Update ALL callers in the same commit
3. Use `_` for unused return values

---

## Anti-Patterns

| Anti-Pattern | Why It's Bad | Fix |
|-------------|-------------|-----|
| No `@st.cache_data` on Streamlit | Burns API quota | Add decorator to all external calls |
| `except: pass` | Hides errors forever | Always log: `print(f"[ERROR] {e}")` |
| Module-level client init | Re-runs on every interaction | Lazy import inside function |
| Tuple unpacking without `_` | Crashes when return grows | Use `_` for unused values |
| Not grepping callers | Silent crashes at call sites | Always check before commit |
