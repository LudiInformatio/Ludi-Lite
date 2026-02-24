# Prompt Patterns — Ludi-Lite

**Purpose:** Prompt structure and engineering rules

---

## Our Prompt Structure (Canonical)

```
=== ANALYSIS TIMESTAMP ===     ← from time_utils.build_time_aware_prompt()
=== SEASON CONTEXT ===         ← from season_context.get_full_season_context()
=== RSS NEWS ===               ← from perplexity_client.get_rss_news() (free first)
=== PERPLEXITY CONTEXT ===    ← only if RSS is empty (expensive)
=== BASE PROMPT ===            ← from prompts.get_dynamic_prompt()
```

---

## Key Principles

### Data First
Inject stats before instructions. Top-to-bottom context ordering.

```python
# ✅ Good: data → instructions
user_prompt = f"""
=== PLAYER STATS ===
{player_stats}

=== YOUR TASK ===
Analyze this prop bet.
"""

# ❌ Bad: instructions → data (context appears after constraints)
user_prompt = """
=== YOUR TASK ===
Analyze this prop bet.

=== PLAYER STATS ===
{player_stats}
"""
```

### Label Space First
Define what the output should look like BEFORE showing data.

```python
# ✅ Good: valid output defined first
system_prompt = """You are a prop bet analyzer.
VALID OUTPUT:
{"result": "OVER", "reason": "..."}
{"result": "UNDER", "reason": "..."}
Return JSON only."""

# ❌ Bad: schema buried in instruction
user_prompt = """Analyze this bet. Return JSON with result and reason."""
```

### 3-5 High-Quality Examples > 20 Mediocre

Few-shot principle from BERT research: 3-5 examples outperform 20 mediocre ones.

---

## Never Use Claude Training Data for NBA Facts

Always inject roster, injury, and trade data from APIs:

```python
# ❌ BAD: "Who is playing for the Lakers tonight?"
# ✅ GOOD: Fetch from tank01_client, then pass to Claude
roster = tank01_client.get_roster("LAL")
prompt = f"Lakers roster: {roster}\nAnalyze these props..."
```

---

## Chain-of-Thought Sections

Include explicit reasoning sections in prompts:

```
=== ANALYSIS PROTOCOL ===
1. Check injury status (OUT = fade, GTD = risk)
2. Evaluate matchup (pace, defense rating)
3. Consider rest/Back-to-Back
4. Make final recommendation

=== DATA CITATION RULES ===
- Cite specific game logs when mentioning trends
- Cite injury report source
- No claims without data
```

---

## Self-Verification Step

Prompts should end with Claude checking its own numbers:

```
=== VERIFICATION ===
Before outputting, double-check:
- Did you include the player's recent games?
- Is the over/under line accurate?
- Did you account for injuries?
```

---

## System Prompt Stability

Don't inject dynamic data into system prompt — breaks caching:

```python
# ❌ BAD: changes every call
system = f"You are analyzing games on {today_date}..."

# ✅ GOOD: stable across calls
system = "You are an NBA prop bet analyst. Analyze the provided data."
```

---

## RSS → Perplexity Fallback Pattern

```python
def get_player_context(player_name):
    # Step 1: Try free RSS
    rss_news = get_rss_news(player_name)
    if rss_news:
        return format_rss_block(rss_news)
    
    # Step 2: Only if RSS empty, call Perplexity (expensive)
    perplexity_news = get_perplexity_news(player_name)
    return format_perplexity_block(perplexity_news)
```

---

## Context Block Order

The order matters — Claude reads top-to-bottom:

1. **Timestamp** — when is this analysis from?
2. **Season context** — team stats, pace, injuries
3. **RSS News** — free, near-real-time headlines
4. **Perplexity** — only if RSS empty (expensive)
5. **Base prompt** — the actual task instructions

Each section should be clearly delimited with `=== SECTION NAME ===`
