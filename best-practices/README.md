# Best Practices — Ludi-Lite

**Purpose:** Coding, API, and data patterns for Streamlit NBA prop analysis app

---

## Quick Navigation

| I need to... | Read this |
|-------------|-----------|
| Add an API or fix data source issues | `api/API_QUICK_REFERENCE.md` |
| Understand the data pipeline | `api/API_QUICK_REFERENCE.md#4-tier-data-division` |
| Integrate Claude/Perplexity | `api/LLM_INTEGRATION.md` |
| Write new Python code | `coding/CODING_STANDARDS.md` |
| Design or modify database tables | `data/DATA_MODELING.md` |
| Write or modify prompts | `prompts/PROMPT_PATTERNS.md` |
| Debug a bug or incident | `debugging/DEBUGGING_PLAYBOOK.md` |

---

## Decision Tree

```
I'm writing a new feature that calls an API
  → Is it for Streamlit? → YES → Wrap in @st.cache_data FIRST
  → Is there a fallback? → NO → Add fallback before committing

I'm seeing unexpected behavior in the app
  → Run: st.cache_data.clear() 
  → Check: DEBUGGING_PLAYBOOK.md incident table

I'm changing a function that returns multiple values
  → Check: coding/CODING_STANDARDS.md "Tuple unpacking" section
  → Grep all callers BEFORE committing

I'm adding a new database table
  → Check: data/DATA_MODELING.md "CREATE TABLE IF NOT EXISTS" pattern
  → Add: snapshot_time column for freshness tracking
```

---

## File Structure

```
best-practices/
├── README.md                       # This file
├── api/
│   ├── API_QUICK_REFERENCE.md      # Data sources, endpoints, rate limits
│   └── LLM_INTEGRATION.md          # Claude/Perplexity patterns
├── coding/
│   └── CODING_STANDARDS.md         # Python rules + Streamlit patterns
├── data/
│   └── DATA_MODELING.md            # SQLite schema, DB-first cache
├── prompts/
│   └── PROMPT_PATTERNS.md          # Prompt structure, few-shot rules
└── debugging/
    └── DEBUGGING_PLAYBOOK.md       # Known incidents + fixes
```

---

## What NOT to Duplicate

These exist elsewhere and are linked, not duplicated:

| File | Location |
|------|----------|
| Product vision | `docs/PRD.md` |
| Build workflow | `docs/LUDI_LITE_BUILD_SOP.md` |
| Feature backlog | `docs/FUTURE_ENHANCEMENTS.md` |
| Setup guide | `README.md` |
| Session history | `memory/MEMORY.md` |

---

## Module Dependency Graph

```
app.py
├── prompts.py
│   └── perplexity_client.py
│       └── RSS feeds (rotowire, realgm)
├── season_context.py
│   ├── bdl_client.py
│   ├── tank01_client.py
│   └── espn_client.py
├── injury_verification.py
│   ├── tank01_client.py
│   ├── bdl_client.py
│   └── espn_client.py
├── usage_calculator.py
│   └── bdl_client.py
└── database.py (SQLite)
```

---

**Last Updated:** February 2026
