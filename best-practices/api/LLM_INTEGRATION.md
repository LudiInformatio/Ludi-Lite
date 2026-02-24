# LLM Integration — Ludi-Lite

**Purpose:** Claude/Perplexity patterns for Streamlit app

---

## Model Selection

| Model | Use Case |
|-------|----------|
| Haiku | Classification, extraction, sanity checks |
| Sonnet | Full analysis, player spotlights |
| Perplexity Sonar | Real-time news (expensive — use as fallback only) |

---

## Temperature Guide

| Temperature | Use Case |
|-------------|----------|
| 0.1 | Classification, factual checks |
| 0.2 | Player spotlights, game analysis |
| 0.3 | Freestyle narrative only |

---

## System Prompt (Stable) vs User Prompt (Dynamic)

**System prompt** = role, constraints, rules — keep stable for caching
**User prompt** = game-specific data, questions — changes every call

```python
# ✅ Good: stable system, dynamic user
response = client.messages.create(
    system=ROSTER_RULES + "\n\n" + TASK_INSTRUCTIONS,  # stable
    messages=[{"role": "user", "content": game_data + "\n\n" + question}]  # dynamic
)

# ❌ Bad: mixing dynamic into system breaks caching
system = ROSTER_RULES + f" Today's date: {today}"  # changes every call
```

---

## Anti-Patterns

### Never Use Claude for NBA Facts

```python
# ❌ BAD: Claude's training data is outdated
prompt = "Who are the Lakers' starters tonight?"

# ✅ GOOD: Fetch from API, then give Claude the data
players = tank01_client.get_roster("LAL")
prompt = f"Given these Lakers players: {players}\nAnalyze the matchup..."
```

### Never Initialize Claude Client at Module Level

```python
# ❌ BAD: Re-runs on every Streamlit interaction
import anthropic
client = anthropic.Anthropic(api_key=TOKEN)

# ✅ GOOD: Lazy import inside function
def get_analysis(prompt):
    import anthropic
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
```

### Never Block Pipeline on Perplexity Failure

```python
# ❌ BAD: App crashes if Perplexity is down
news = perplexity_client.get_news(player_name)
st.write(news)

# ✅ GOOD: Graceful degradation
news = perplexity_client.get_news(player_name) or ""
if news:
    st.write(news)
else:
    st.info("No recent news available")
```

---

## Token Budget Awareness

Perplexity is expensive. Use this hierarchy:

1. **RSS feeds first** — Rotowire, RealGM (free)
2. **Perplexity only if RSS empty** — Sonar model
3. **Cache minimum:** 20 minutes

**Approximate costs:**
- RSS: $0
- Perplexity Sonar: ~$0.002 per query
- Perplexity Sonar-pro: ~$0.01 per query

---

## Perplexity Patterns

### When to Use vs RSS
- Use RSS for: Rotowire, RealGM headlines (free, near-real-time)
- Use Perplexity only if: RSS returns empty AND real-time context needed

### Cache Minimum
- Never call Perplexity more than once per 20 minutes per player
- Store results in `analyses` table for cross-session persistence

### Model Selection
- `sonar` — quick queries, simple context
- `sonar-pro` — complex analysis, multiple data sources
