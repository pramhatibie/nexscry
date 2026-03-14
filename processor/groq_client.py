"""
NexScry AI Processor — powered by Google Gemini 2.0 Flash (free tier).

This is NOT just a summarizer. It does:
1. Per-item enrichment (classify, extract insights)
2. Cross-source intelligence (find connections across Reddit + HN + GitHub + ArXiv)
3. Trend detection (what's emerging across all sources)
4. Builder-focused framing (every insight answers "so what should I build?")
"""
import json
import re
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone
from config import GEMINI_API_KEY, GEMINI_MODEL, GEMINI_FALLBACK_MODEL, MAX_TOKENS_PER_ITEM


def _extract_json(text: str) -> str:
    """Strip markdown code fences that Gemini sometimes wraps around JSON."""
    text = text.strip()
    # Handle ```json ... ``` or ``` ... ```
    m = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if m:
        return m.group(1).strip()
    # If response starts with [ or { it's already raw JSON
    if text.startswith(("{", "[")):
        return text
    # Try to find a JSON object/array anywhere in the response
    m2 = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", text)
    if m2:
        return m2.group(1)
    return text

GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"

# Gemini free tier: 15 requests/minute — enforce a gap between calls
_GEMINI_MIN_INTERVAL = 4.5  # seconds between calls to stay under 15 RPM
_last_call_time = 0.0


def call_groq(
    prompt: str,
    system: str = "",
    model: str = GEMINI_MODEL,
    max_tokens: int = MAX_TOKENS_PER_ITEM,
    temperature: float = 0.3,
    retry: bool = True,
) -> str:
    """Call Google Gemini API. Respects free-tier rate limits automatically."""
    global _last_call_time

    if not GEMINI_API_KEY:
        print("  ❌ GEMINI_API_KEY is not set — add it as a GitHub Secret named GEMINI_API_KEY")
        return '{"error": "no_api_key"}'

    # Enforce minimum interval between calls (15 RPM free tier)
    elapsed = time.time() - _last_call_time
    if elapsed < _GEMINI_MIN_INTERVAL:
        time.sleep(_GEMINI_MIN_INTERVAL - elapsed)

    url = f"{GEMINI_API_BASE}/{model}:generateContent?key={GEMINI_API_KEY}"

    body: dict = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "maxOutputTokens": max_tokens,
            "temperature": temperature,
        },
    }
    if system:
        body["systemInstruction"] = {"parts": [{"text": system}]}

    payload = json.dumps(body).encode()
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode())
            _last_call_time = time.time()
            return data["candidates"][0]["content"]["parts"][0]["text"]
    except urllib.error.HTTPError as e:
        _last_call_time = time.time()
        err_body = ""
        try:
            err_body = e.read().decode("utf-8", errors="replace")
        except Exception:
            err_body = str(e)

        if e.code == 400:
            print(f"  ⚠ Gemini 400 BAD REQUEST — model '{model}' may be unavailable. Body: {err_body[:200]}")
            if retry and model != GEMINI_FALLBACK_MODEL:
                print(f"  🔄 Retrying with fallback model {GEMINI_FALLBACK_MODEL}...")
                return call_groq(prompt, system, GEMINI_FALLBACK_MODEL, max_tokens, temperature, retry=False)
            return '{"error": "bad_request"}'
        if e.code == 429:
            if retry:
                print(f"  ⏳ Gemini rate-limited (429) — waiting 30s...")
                time.sleep(30)
                return call_groq(prompt, system, model, max_tokens, temperature, retry=False)
            print(f"  ⚠ Gemini still rate-limited — skipping this item")
            return '{"error": "rate_limited"}'
        if e.code in (401, 403):
            print(f"  ❌ Gemini {e.code} — API key invalid or expired. Check GEMINI_API_KEY secret. Body: {err_body[:200]}")
            return '{"error": "invalid_api_key"}'
        print(f"  ⚠ Gemini HTTP {e.code}: {err_body[:200]}")
        return f'{{"error": "http_{e.code}"}}'
    except Exception as e:
        _last_call_time = time.time()
        print(f"  ⚠ Gemini connection error: {e}")
        return '{"error": "connection_failed"}'


def test_groq_connection() -> bool:
    """Quick check that the API key is valid before running the full pipeline."""
    if not GEMINI_API_KEY:
        print("  ❌ GEMINI_API_KEY not set — AI features will be disabled")
        print("  ℹ  Get a free key at: https://aistudio.google.com/app/apikey")
        return False
    result = call_groq("Reply with the single word: ok", max_tokens=5, retry=False)
    ok = "ok" in result.lower() and "error" not in result
    if ok:
        print(f"  ✅ Gemini API key valid (model: {GEMINI_MODEL})")
    else:
        print(f"  ❌ Gemini API key test failed. Response: {result[:200]}")
    return ok


# ─────────────────────────────────────────────
# 1. PER-ITEM ENRICHMENT
# ─────────────────────────────────────────────

ENRICHMENT_SYSTEM = """You are NexScry — the sharpest AI intelligence layer for solo builders, indie hackers, and startup founders.
Your job: extract SPECIFIC, ACTIONABLE signal from raw internet data.
Be precise. Name real problems, real communities, real monetization paths.
Always respond in valid JSON. No markdown, no backticks, just JSON."""


def enrich_reddit_post(post: dict) -> dict:
    """Add AI analysis to a Reddit post."""
    prompt = f"""Analyze this Reddit post as a market signal for builders:

Title: {post['title']}
Subreddit: r/{post['sub']}
Text: {post.get('selftext', '')[:600]}
Score: {post['score']} | Comments: {post['num_comments']}
Pain signals detected: {post.get('pain_signals', [])}

Return JSON (be SPECIFIC — no vague generalities):
{{
  "category": "pain_point|tool_request|market_signal|discussion|showcase",
  "opportunity_score": <integer 1-10>,
  "one_liner": "one punchy sentence: what exact problem this reveals for builders",
  "build_idea": "if opportunity_score >= 7: describe a specific product/tool/feature that would solve this. Be concrete: what it does, how it makes money. Otherwise null.",
  "market_size_hint": "small niche | growing niche | mass market",
  "keywords": ["3-5 specific topic keywords"],
  "audience": "exact type of person who has this problem"
}}"""
    result = call_groq(prompt, ENRICHMENT_SYSTEM)
    try:
        post["ai"] = json.loads(_extract_json(result))
    except json.JSONDecodeError:
        post["ai"] = {"one_liner": "", "category": "unknown", "opportunity_score": 0, "keywords": []}
    return post


def enrich_hn_story(story: dict) -> dict:
    """Add AI analysis to a HN story."""
    prompt = f"""Analyze this Hacker News story as a signal for builders:

Title: {story['title']}
Points: {story.get('points', 0)} | Comments: {story.get('num_comments', 0)}
URL: {story.get('url', 'N/A')}
Type: {story.get('type', 'story')}

Return JSON (translate tech jargon into business reality):
{{
  "category": "launch|tool|essay|research|hiring|discussion|tutorial",
  "relevance": <integer 1-10>,
  "one_liner": "what this means for builders — in plain English, not HN-speak",
  "builder_takeaway": "one specific action: what should a builder DO with this information right now?",
  "signal_type": "opportunity|threat|trend|noise",
  "keywords": ["3-5 specific topic keywords"]
}}"""
    result = call_groq(prompt, ENRICHMENT_SYSTEM)
    try:
        story["ai"] = json.loads(_extract_json(result))
    except json.JSONDecodeError:
        story["ai"] = {"one_liner": "", "category": "unknown", "relevance": 0, "keywords": []}
    return story


def enrich_github_repo(repo: dict) -> dict:
    """Add AI analysis to a GitHub repo."""
    prompt = f"""Analyze this trending GitHub repo as a market signal:

Repo: {repo['name']}
Description: {repo.get('description', '')}
Language: {repo.get('language', 'N/A')}
Stars: {repo['stars']} | Gaining {repo.get('star_velocity', 0)} stars/day
Topics: {repo.get('topics', [])}

Return JSON (explain the business reality, not just the tech):
{{
  "category": "framework|tool|library|ai_model|devops|data|other",
  "hype_vs_substance": <integer 1-10>,
  "one_liner": "what problem this repo actually solves, in one sentence",
  "why_trending": "the real reason this is gaining attention NOW — what changed in the ecosystem?",
  "builder_action": "specific way a builder could use, fork, build on top of, or compete with this",
  "adjacent_opportunity": "a gap this repo does NOT cover that someone could build",
  "keywords": ["3-5 specific topic keywords"]
}}"""
    result = call_groq(prompt, ENRICHMENT_SYSTEM)
    try:
        repo["ai"] = json.loads(_extract_json(result))
    except json.JSONDecodeError:
        repo["ai"] = {"one_liner": "", "category": "unknown", "keywords": []}
    return repo


def enrich_arxiv_paper(paper: dict) -> dict:
    """ELI5 an ArXiv paper for practitioners."""
    prompt = f"""Explain this ArXiv paper to a software developer who wants to know if it changes what they should build:

Title: {paper['title']}
Abstract: {paper['summary'][:700]}
Categories: {paper.get('categories', [])}

Return JSON (developer-first, not academic):
{{
  "eli5": "2 sentences: what this research does and why it matters. Use plain English. No jargon.",
  "practical_use": "the most concrete near-term application of this — what product could use this in 6 months?",
  "who_cares": "which specific type of developer/builder should bookmark this and why",
  "novelty_score": <integer 1-10>,
  "time_to_production": "months until this could realistically ship in a product",
  "keywords": ["3-5 specific topic keywords"]
}}"""
    result = call_groq(prompt, ENRICHMENT_SYSTEM)
    try:
        paper["ai"] = json.loads(_extract_json(result))
    except json.JSONDecodeError:
        paper["ai"] = {"eli5": "", "novelty_score": 0, "keywords": []}
    return paper


def enrich_devto_article(article: dict) -> dict:
    """Add AI analysis to a DEV.to article."""
    prompt = f"""Analyze this DEV.to article as a signal of what developers care about:

Title: {article['title']}
Description: {article.get('description', '')}
Tags: {article.get('tags', [])}
Reactions: {article.get('reactions', 0)} | Comments: {article.get('comments', 0)}

Return JSON:
{{
  "category": "tutorial|opinion|project|news|career|other",
  "relevance": <integer 1-10>,
  "one_liner": "what this tells builders about what the dev community is currently struggling with or excited about",
  "builder_takeaway": "one specific action or insight a builder should extract from this article's popularity",
  "keywords": ["3-5 specific topic keywords"]
}}"""
    result = call_groq(prompt, ENRICHMENT_SYSTEM)
    try:
        article["ai"] = json.loads(_extract_json(result))
    except json.JSONDecodeError:
        article["ai"] = {"one_liner": "", "category": "unknown", "relevance": 0, "keywords": []}
    return article


def enrich_producthunt_launch(launch: dict) -> dict:
    """Analyze PH launch for market intelligence."""
    prompt = f"""Analyze this Product Hunt launch:

Product: {launch['title']}
Description: {launch.get('description', '')}

Return JSON:
{{
  "category": "ai_tool|saas|devtool|design|productivity|other",
  "market_signal": "what this launch tells us about market demand",
  "competitive_gap": "what's missing that a builder could fill",
  "keywords": ["3-5 topic keywords"]
}}"""
    result = call_groq(prompt, ENRICHMENT_SYSTEM)
    try:
        launch["ai"] = json.loads(_extract_json(result))
    except json.JSONDecodeError:
        launch["ai"] = {"market_signal": "", "keywords": []}
    return launch


# ─────────────────────────────────────────────
# 2. CROSS-SOURCE INTELLIGENCE (the killer feature)
# ─────────────────────────────────────────────

def extract_cross_signals(all_data: dict) -> list[dict]:
    """
    Find topics/themes appearing across 2+ platforms simultaneously.
    Uses direct AI analysis of raw item titles — works even without per-item enrichment.
    Falls back to keyword frequency if AI call fails.
    """
    # Build a compact per-source item list for Gemini to analyze
    source_summaries: dict = {}
    for source_name, items in all_data.items():
        titles = []
        for item in items[:20]:
            title = item.get("title", item.get("name", "")).strip()
            if not title:
                continue
            # Include AI keywords if available (bonus signal)
            kws = item.get("ai", {}).get("keywords", [])
            entry = title + (f" [{', '.join(kws[:3])}]" if kws else "")
            titles.append(entry)
        if titles:
            source_summaries[source_name] = titles[:12]

    if len(source_summaries) < 2:
        return []

    prompt = f"""Analyze these items scraped today from {len(source_summaries)} different tech platforms:

{json.dumps(source_summaries, indent=2)[:3500]}

Find 3-5 specific topics or themes that appear across 2 or more platforms.
These are genuine convergence signals — things the builder/tech community is buzzing about simultaneously on multiple channels.

Return a JSON array ONLY (no markdown, no explanation outside JSON):
[
  {{
    "signal": "specific topic name (2-4 words)",
    "sources_involved": ["platform1", "platform2"],
    "narrative": "2 sentences: what is happening across these platforms simultaneously and why it matters for builders",
    "builder_opportunity": "one concrete thing a solo developer could build or do based on this convergence right now",
    "confidence": "high|medium|low"
  }}
]

Rules:
- Exclude generic terms (AI, Python, GitHub, API, software, developer)
- Focus on SPECIFIC emerging topics, not always-present noise
- Max 5 signals
- Return valid JSON array ONLY"""

    result = call_groq(prompt, ENRICHMENT_SYSTEM, max_tokens=1500)
    try:
        synthesized = json.loads(_extract_json(result))
        if isinstance(synthesized, list) and synthesized:
            # Validate structure
            valid = [
                s for s in synthesized
                if isinstance(s, dict) and s.get("signal") and s.get("sources_involved")
            ]
            if valid:
                return valid[:5]
    except (json.JSONDecodeError, TypeError):
        pass

    # Fallback: keyword frequency across sources (works without AI)
    stop_words = {
        "that", "with", "from", "this", "have", "been", "will", "what", "your",
        "more", "than", "they", "when", "some", "into", "then", "there", "these",
        "their", "about", "using", "make", "build", "just", "like", "open",
    }
    keyword_map: dict = {}
    for source_name, items in all_data.items():
        for item in items:
            text = " ".join([
                item.get("title", item.get("name", "")),
                item.get("description", ""),
                " ".join(item.get("topics", [])),
            ]).lower()
            words = set(re.findall(r"\b[a-z]{4,}\b", text)) - stop_words
            for w in words:
                if w not in keyword_map:
                    keyword_map[w] = set()
                keyword_map[w].add(source_name)

    fallback = [
        {
            "signal": kw,
            "sources_involved": list(srcs),
            "narrative": f"'{kw}' is mentioned across {', '.join(srcs)} today.",
            "builder_opportunity": "",
            "confidence": "low",
            "num_sources": len(srcs),
        }
        for kw, srcs in keyword_map.items()
        if len(srcs) >= 2
    ]
    fallback.sort(key=lambda x: x["num_sources"], reverse=True)
    return fallback[:5]


# ─────────────────────────────────────────────
# 3. BUILD OPPORTUNITIES — the killer feature
# ─────────────────────────────────────────────

def generate_build_opportunities(all_data: dict, cross_signals: list) -> list:
    """
    THE REASON PEOPLE COME BACK DAILY.

    Synthesizes signals from ALL sources into specific, validated build
    opportunities — each with a problem, evidence, timing, and where to
    find first users. Solo devs should be able to act on these TODAY.
    """
    # Gather richest signals
    pain_posts = [
        {
            "title": p.get("title", ""),
            "sub": p.get("sub", ""),
            "score": p.get("score", 0),
            "comments": p.get("num_comments", 0),
            "pain_signals": p.get("pain_signals", []),
            "ai_build_idea": p.get("ai", {}).get("build_idea", ""),
        }
        for p in all_data.get("reddit", [])
        if p.get("has_pain") and p.get("score", 0) > 5
    ][:12]

    ask_hn = [
        {"title": s.get("title", ""), "points": s.get("points", 0), "comments": s.get("num_comments", 0)}
        for s in all_data.get("hackernews", [])
        if s.get("type") == "ask_hn"
    ][:6]

    hot_repos = [
        {
            "name": r.get("name", ""),
            "desc": r.get("description", ""),
            "velocity": r.get("star_velocity", 0),
            "adjacent_opportunity": r.get("ai", {}).get("adjacent_opportunity", ""),
        }
        for r in sorted(all_data.get("github", []), key=lambda x: x.get("star_velocity", 0), reverse=True)
    ][:6]

    ph_launches = [
        {"title": l.get("title", ""), "desc": l.get("description", "")[:150], "gap": l.get("ai", {}).get("competitive_gap", "")}
        for l in all_data.get("producthunt", [])
    ][:5]

    context = {
        "reddit_pain_signals": pain_posts,
        "ask_hn_questions": ask_hn,
        "hot_github_repos": hot_repos,
        "product_hunt_launches": ph_launches,
        "cross_source_signals": cross_signals[:5],
    }

    prompt = f"""You are NexScry's opportunity engine. Today's real internet data:

{json.dumps(context, indent=2)[:4500]}

Identify the TOP 3-5 SPECIFIC business opportunities for a solo developer right now.

RULES:
- SPECIFIC beats vague. "CLI tool for managing Ollama model context windows" > "AI tool"
- Each opportunity must have at least 2 independent signals from the data above
- Must be buildable by 1 person within weeks, not months
- Focus on EMERGING gaps (not already saturated markets)

Return a JSON array ONLY. No text outside the JSON:
[
  {{
    "title": "5-8 word specific opportunity title",
    "problem": "Exactly what pain exists. Reference specific signals from the data. 2-3 sentences.",
    "evidence": "How many signals, which platforms, what engagement numbers support this",
    "why_now": "What specific recent shift (new model, API change, regulation, trend) makes this the RIGHT moment",
    "opportunity_score": <integer 1-10>,
    "where_to_find_users": "Specific communities: r/xyz, HN thread about X, specific Discord/Slack",
    "build_complexity": "weekend hack|2-week MVP|1-month launch",
    "monetization_hint": "How this makes money: SaaS $X/mo, one-time, API pricing, etc."
  }}
]"""

    result = call_groq(prompt, ENRICHMENT_SYSTEM, max_tokens=2500, temperature=0.35)
    try:
        opps = json.loads(_extract_json(result))
        return opps if isinstance(opps, list) else []
    except json.JSONDecodeError:
        return []


# ─────────────────────────────────────────────
# 4. DAILY TREND SUMMARY
# ─────────────────────────────────────────────

def generate_daily_summary(all_data: dict, cross_signals: list) -> dict:
    """Generate the daily NexScry intelligence report."""
    stats = {source: len(items) for source, items in all_data.items()}

    # Collect top items per source
    highlights = {}
    for source, items in all_data.items():
        sorted_items = sorted(
            items,
            key=lambda x: x.get("ai", {}).get("opportunity_score", 0)
            or x.get("ai", {}).get("relevance", 0)
            or x.get("ai", {}).get("novelty_score", 0)
            or x.get("ai", {}).get("hype_vs_substance", 0)
            or 0,
            reverse=True,
        )
        highlights[source] = sorted_items[:5]

    highlights_text = json.dumps(
        {s: [{"title": i.get("title", i.get("name", "")), "ai": i.get("ai", {})} for i in items]
         for s, items in highlights.items()},
        indent=2,
    )[:3000]

    cross_text = json.dumps(cross_signals[:5], indent=2)[:1500]

    prompt = f"""Write today's NexScry Daily Intelligence Brief for builders.

Data processed: {json.dumps(stats)}

Top signals per source:
{highlights_text}

Cross-source intelligence:
{cross_text}

Write a JSON object:
{{
  "headline": "punchy 8-12 word headline for today's brief",
  "tldr": "3 sentence executive summary — what happened today that builders should know",
  "top_opportunity": "the single best opportunity spotted today, with specific next steps",
  "emerging_trend": "a pattern forming across multiple sources that hasn't peaked yet",
  "contrarian_take": "one thing everyone seems excited about but might be overhyped, and why"
}}"""

    result = call_groq(prompt, ENRICHMENT_SYSTEM, max_tokens=800, temperature=0.5)
    try:
        parsed = json.loads(_extract_json(result))
        if isinstance(parsed, dict) and parsed.get("headline"):
            return parsed
        return {"headline": "Daily Intelligence Brief", "tldr": str(parsed)[:300]}
    except (json.JSONDecodeError, TypeError):
        return {"headline": "Daily Intelligence Brief", "tldr": ""}


# ─────────────────────────────────────────────
# BATCH PROCESSING
# ─────────────────────────────────────────────

def process_all(all_data: dict) -> dict:
    """
    Run full AI pipeline on all scraped data.
    Returns enriched data + cross-source signals + daily summary.
    """
    enrichers = {
        "reddit": enrich_reddit_post,
        "hackernews": enrich_hn_story,
        "github": enrich_github_repo,
        "arxiv": enrich_arxiv_paper,
        "producthunt": enrich_producthunt_launch,
        "devto": enrich_devto_article,
    }

    # Enrich items per source (with rate limit protection)
    for source, items in all_data.items():
        enricher = enrichers.get(source)
        if not enricher:
            continue
        print(f"  🧠 Enriching {source} ({len(items)} items)...")
        # Process top items only to stay within free tier
        top_items = items[:15]  # enrich top 15 per source
        for item in top_items:
            enricher(item)  # rate limiting handled inside call_groq

    print("  🔗 Running cross-source intelligence...")
    cross_signals = extract_cross_signals(all_data)

    print("  🏗 Generating build opportunities...")
    build_opportunities = generate_build_opportunities(all_data, cross_signals)

    print("  📊 Generating daily summary...")
    daily_summary = generate_daily_summary(all_data, cross_signals)

    return {
        "data": all_data,
        "cross_signals": cross_signals,
        "build_opportunities": build_opportunities,
        "daily_summary": daily_summary,
        "processed_at": datetime.now(timezone.utc).isoformat(),
    }
