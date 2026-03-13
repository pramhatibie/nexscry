"""
NexScry AI Processor — powered by Groq.

This is NOT just a summarizer. It does:
1. Per-item enrichment (classify, extract insights)
2. Cross-source intelligence (find connections across Reddit + HN + GitHub + ArXiv)
3. Trend detection (what's emerging across all sources)
4. Builder-focused framing (every insight answers "so what should I build?")
"""
import json
import time
import urllib.request
import urllib.error
from config import GROQ_API_KEY, GROQ_MODEL, GROQ_FALLBACK_MODEL, MAX_TOKENS_PER_ITEM


def call_groq(
    prompt: str,
    system: str = "",
    model: str = GROQ_MODEL,
    max_tokens: int = MAX_TOKENS_PER_ITEM,
    temperature: float = 0.3,
    retry: bool = True,
) -> str:
    """Call Groq API. Falls back to smaller model if rate-limited."""
    if not GROQ_API_KEY:
        return '{"error": "No GROQ_API_KEY set"}'

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    payload = json.dumps({
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }).encode()

    req = urllib.request.Request(
        "https://api.groq.com/openai/v1/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
            return data["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as e:
        if e.code == 429 and retry:
            print(f"    ⏳ Rate limited, waiting 10s then using fallback model...")
            time.sleep(10)
            return call_groq(prompt, system, GROQ_FALLBACK_MODEL, max_tokens, temperature, retry=False)
        body = e.read().decode() if hasattr(e, 'read') else str(e)
        print(f"    ⚠ Groq API error {e.code}: {body[:200]}")
        return '{"error": "API call failed"}'
    except Exception as e:
        print(f"    ⚠ Groq error: {e}")
        return '{"error": "Connection failed"}'


# ─────────────────────────────────────────────
# 1. PER-ITEM ENRICHMENT
# ─────────────────────────────────────────────

ENRICHMENT_SYSTEM = """You are NexScry, an AI intelligence layer for builders (developers, founders, indie hackers).
Your job: extract actionable signal from raw internet data.
Always respond in valid JSON. No markdown, no backticks, just JSON."""


def enrich_reddit_post(post: dict) -> dict:
    """Add AI analysis to a Reddit post."""
    prompt = f"""Analyze this Reddit post for builder intelligence:

Title: {post['title']}
Subreddit: r/{post['sub']}
Text: {post.get('selftext', '')[:500]}
Score: {post['score']} | Comments: {post['num_comments']}
Pain signals detected: {post.get('pain_signals', [])}

Return JSON:
{{
  "category": "pain_point|tool_request|market_signal|discussion|showcase",
  "opportunity_score": 1-10,
  "one_liner": "one sentence: what this means for builders",
  "build_idea": "if opportunity_score > 6, suggest what to build. else null",
  "keywords": ["3-5 topic keywords"],
  "audience": "who would care about this"
}}"""
    result = call_groq(prompt, ENRICHMENT_SYSTEM)
    try:
        post["ai"] = json.loads(result)
    except json.JSONDecodeError:
        post["ai"] = {"one_liner": result[:200], "category": "unknown", "opportunity_score": 0}
    return post


def enrich_hn_story(story: dict) -> dict:
    """Add AI analysis to a HN story."""
    prompt = f"""Analyze this Hacker News story for builders:

Title: {story['title']}
Points: {story.get('points', 0)} | Comments: {story.get('num_comments', 0)}
URL: {story.get('url', 'N/A')}

Return JSON:
{{
  "category": "launch|tool|essay|research|hiring|drama|tutorial",
  "relevance": 1-10,
  "one_liner": "what this means — translated from HN jargon to plain business English",
  "builder_takeaway": "one concrete action a builder should take based on this",
  "keywords": ["3-5 topic keywords"]
}}"""
    result = call_groq(prompt, ENRICHMENT_SYSTEM)
    try:
        story["ai"] = json.loads(result)
    except json.JSONDecodeError:
        story["ai"] = {"one_liner": result[:200], "category": "unknown", "relevance": 0}
    return story


def enrich_github_repo(repo: dict) -> dict:
    """Add AI analysis to a GitHub repo."""
    prompt = f"""Analyze this trending GitHub repo for builders:

Repo: {repo['name']}
Description: {repo.get('description', '')}
Language: {repo.get('language', 'N/A')}
Stars: {repo['stars']} | Star velocity: {repo.get('star_velocity', 0)}/day
Topics: {repo.get('topics', [])}
Hiring signal: {repo.get('hiring_signal', False)}

Return JSON:
{{
  "category": "framework|tool|library|ai_model|devops|data|other",
  "hype_vs_substance": 1-10,
  "one_liner": "what this repo does in plain English",
  "why_trending": "why this is gaining stars now",
  "builder_action": "how a builder could use or learn from this",
  "keywords": ["3-5 topic keywords"]
}}"""
    result = call_groq(prompt, ENRICHMENT_SYSTEM)
    try:
        repo["ai"] = json.loads(result)
    except json.JSONDecodeError:
        repo["ai"] = {"one_liner": result[:200], "category": "unknown"}
    return repo


def enrich_arxiv_paper(paper: dict) -> dict:
    """ELI5 an ArXiv paper for practitioners."""
    prompt = f"""Explain this ArXiv paper for a software developer who doesn't read academic papers:

Title: {paper['title']}
Abstract: {paper['summary'][:600]}
Categories: {paper.get('categories', [])}

Return JSON:
{{
  "eli5": "explain like I'm a developer, not a PhD. 2-3 sentences max",
  "practical_use": "one real-world application of this research",
  "who_cares": "which type of builder should pay attention to this",
  "novelty_score": 1-10,
  "keywords": ["3-5 topic keywords"]
}}"""
    result = call_groq(prompt, ENRICHMENT_SYSTEM)
    try:
        paper["ai"] = json.loads(result)
    except json.JSONDecodeError:
        paper["ai"] = {"eli5": result[:200], "novelty_score": 0}
    return paper


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
        launch["ai"] = json.loads(result)
    except json.JSONDecodeError:
        launch["ai"] = {"market_signal": result[:200]}
    return launch


# ─────────────────────────────────────────────
# 2. CROSS-SOURCE INTELLIGENCE (the killer feature)
# ─────────────────────────────────────────────

def extract_cross_signals(all_data: dict) -> list[dict]:
    """
    THE FEATURE SONNET DIDN'T BUILD.
    
    Takes data from ALL sources and finds connections:
    - Reddit user complains about X → GitHub repo solving X trending
    - ArXiv paper about technique Y → HN discussion about Y's implications
    - Product Hunt launch in niche Z → Reddit thread asking for Z
    
    This is what makes NexScry an intelligence platform, not just an aggregator.
    """
    # Collect all keywords from enriched items
    keyword_map = {}  # keyword → list of items
    for source_name, items in all_data.items():
        for item in items:
            ai_data = item.get("ai", {})
            keywords = ai_data.get("keywords", [])
            for kw in keywords:
                kw_lower = kw.lower().strip()
                if len(kw_lower) < 3:
                    continue
                if kw_lower not in keyword_map:
                    keyword_map[kw_lower] = []
                keyword_map[kw_lower].append({
                    "source": source_name,
                    "title": item.get("title", item.get("name", "")),
                    "url": item.get("url", item.get("hn_url", "")),
                    "ai_summary": ai_data.get("one_liner") or ai_data.get("eli5") or ai_data.get("market_signal", ""),
                })

    # Find keywords that appear across multiple sources
    cross_signals = []
    for keyword, items in keyword_map.items():
        sources = set(i["source"] for i in items)
        if len(sources) >= 2:
            cross_signals.append({
                "keyword": keyword,
                "num_sources": len(sources),
                "sources": list(sources),
                "items": items[:6],  # cap for readability
            })

    cross_signals.sort(key=lambda x: x["num_sources"], reverse=True)

    # Use Groq to synthesize the top cross-signals
    if cross_signals[:10]:
        top_signals_text = json.dumps(cross_signals[:10], indent=2)[:3000]
        prompt = f"""You found these cross-source signals — topics appearing across multiple platforms simultaneously:

{top_signals_text}

For each meaningful signal, write a "NexScry Intelligence Brief":
Return a JSON array of objects:
[
  {{
    "signal": "topic name",
    "sources_involved": ["reddit", "github", ...],
    "narrative": "2-3 sentences: what's happening across these platforms and why it matters",
    "builder_opportunity": "specific thing a builder could do right now based on this convergence",
    "confidence": "high|medium|low"
  }}
]

Only include signals that represent genuine convergence (not just common words like 'python' or 'api').
Max 5 signals. Return valid JSON array only."""

        result = call_groq(prompt, ENRICHMENT_SYSTEM, max_tokens=1500)
        try:
            synthesized = json.loads(result)
            return synthesized if isinstance(synthesized, list) else cross_signals[:5]
        except json.JSONDecodeError:
            pass

    return cross_signals[:5]


# ─────────────────────────────────────────────
# 3. DAILY TREND SUMMARY
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
        return json.loads(result)
    except json.JSONDecodeError:
        return {"headline": "Daily Intelligence Brief", "tldr": result[:300]}


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
    }

    # Enrich items per source (with rate limit protection)
    for source, items in all_data.items():
        enricher = enrichers.get(source)
        if not enricher:
            continue
        print(f"  🧠 Enriching {source} ({len(items)} items)...")
        # Process top items only to stay within free tier
        top_items = items[:15]  # enrich top 15 per source
        for i, item in enumerate(top_items):
            enricher(item)
            if i % 5 == 4:
                time.sleep(2)  # respect Groq free tier rate limits

    print("  🔗 Running cross-source intelligence...")
    cross_signals = extract_cross_signals(all_data)

    print("  📊 Generating daily summary...")
    daily_summary = generate_daily_summary(all_data, cross_signals)

    return {
        "data": all_data,
        "cross_signals": cross_signals,
        "daily_summary": daily_summary,
        "processed_at": datetime.now(timezone.utc).isoformat() if 'datetime' in dir() else "",
    }


# Need datetime for timestamp
from datetime import datetime, timezone
