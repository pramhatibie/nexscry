"""
NexScry Site Builder — generates production-grade static HTML.

Design philosophy:
- Dark mode, high contrast, data-dense but readable
- Feels like a Bloomberg terminal meets a modern AI product
- Every data point is a SEO page (long-tail keyword goldmine)
- No JavaScript frameworks needed — pure HTML/CSS with minimal vanilla JS
"""
import json
import os
import re
from datetime import datetime, timezone
from config import SITE_NAME, SITE_TAGLINE, SITE_URL, SITE_DESCRIPTION, BUILD_DIR


# ─────────────────────────────────────────────
# CSS — the entire design system
# ─────────────────────────────────────────────

SITE_CSS = """
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Outfit:wght@300;400;600;700;800&display=swap');

:root {
  --bg-primary: #0a0a0f;
  --bg-secondary: #111118;
  --bg-card: #16161f;
  --bg-card-hover: #1c1c28;
  --border: #2a2a3a;
  --border-accent: #3d3d55;
  --text-primary: #e8e8f0;
  --text-secondary: #8888a0;
  --text-muted: #55556a;
  --accent-blue: #4d7cff;
  --accent-cyan: #22d3ee;
  --accent-green: #34d399;
  --accent-orange: #fb923c;
  --accent-pink: #f472b6;
  --accent-purple: #a78bfa;
  --accent-red: #ef4444;
  --glow-blue: rgba(77, 124, 255, 0.15);
  --glow-cyan: rgba(34, 211, 238, 0.1);
  --font-display: 'Outfit', -apple-system, sans-serif;
  --font-mono: 'JetBrains Mono', 'Fira Code', monospace;
  --radius: 12px;
  --radius-sm: 8px;
}

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

body {
  background: var(--bg-primary);
  color: var(--text-primary);
  font-family: var(--font-display);
  line-height: 1.6;
  min-height: 100vh;
  -webkit-font-smoothing: antialiased;
}

/* Noise texture overlay */
body::before {
  content: '';
  position: fixed;
  inset: 0;
  background: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.03'/%3E%3C/svg%3E");
  pointer-events: none;
  z-index: 0;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 24px;
  position: relative;
  z-index: 1;
}

/* ─── HEADER ─── */
.site-header {
  padding: 32px 0 24px;
  border-bottom: 1px solid var(--border);
  position: relative;
}

.header-inner {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.logo {
  font-family: var(--font-mono);
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--accent-cyan);
  text-decoration: none;
  letter-spacing: -0.02em;
}

.logo span {
  color: var(--text-muted);
  font-weight: 400;
}

.header-meta {
  font-family: var(--font-mono);
  font-size: 0.75rem;
  color: var(--text-muted);
  text-align: right;
}

.header-meta .live-dot {
  display: inline-block;
  width: 6px;
  height: 6px;
  background: var(--accent-green);
  border-radius: 50%;
  margin-right: 6px;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

/* ─── HERO / DAILY BRIEF ─── */
.daily-brief {
  margin: 40px 0;
  padding: 32px;
  background: linear-gradient(135deg, var(--bg-card) 0%, rgba(77, 124, 255, 0.05) 100%);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  position: relative;
  overflow: hidden;
}

.daily-brief::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, var(--accent-cyan), var(--accent-blue), var(--accent-purple));
}

.brief-label {
  font-family: var(--font-mono);
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.15em;
  color: var(--accent-cyan);
  margin-bottom: 12px;
}

.brief-headline {
  font-size: 1.75rem;
  font-weight: 800;
  line-height: 1.2;
  margin-bottom: 16px;
  background: linear-gradient(135deg, var(--text-primary), var(--accent-cyan));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.brief-tldr {
  font-size: 1rem;
  color: var(--text-secondary);
  max-width: 700px;
  margin-bottom: 24px;
}

.brief-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 16px;
}

.brief-card {
  padding: 16px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
}

.brief-card-label {
  font-family: var(--font-mono);
  font-size: 0.65rem;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  margin-bottom: 8px;
}

.brief-card-label.opportunity { color: var(--accent-green); }
.brief-card-label.trend { color: var(--accent-purple); }
.brief-card-label.contrarian { color: var(--accent-orange); }

.brief-card-text {
  font-size: 0.9rem;
  color: var(--text-secondary);
  line-height: 1.5;
}

/* ─── CROSS SIGNALS (the killer section) ─── */
.cross-signals {
  margin: 40px 0;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 24px;
}

.section-title {
  font-size: 1.25rem;
  font-weight: 700;
}

.section-badge {
  font-family: var(--font-mono);
  font-size: 0.65rem;
  padding: 4px 10px;
  border-radius: 100px;
  text-transform: uppercase;
  letter-spacing: 0.1em;
}

.badge-ai { background: var(--glow-blue); color: var(--accent-blue); border: 1px solid rgba(77, 124, 255, 0.3); }
.badge-live { background: rgba(34, 211, 238, 0.1); color: var(--accent-cyan); border: 1px solid rgba(34, 211, 238, 0.3); }

.signal-card {
  padding: 24px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  margin-bottom: 16px;
  transition: border-color 0.2s, background 0.2s;
}

.signal-card:hover {
  border-color: var(--border-accent);
  background: var(--bg-card-hover);
}

.signal-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.signal-keyword {
  font-family: var(--font-mono);
  font-weight: 700;
  font-size: 1rem;
  color: var(--accent-cyan);
}

.signal-sources {
  display: flex;
  gap: 6px;
}

.source-pill {
  font-family: var(--font-mono);
  font-size: 0.6rem;
  padding: 2px 8px;
  border-radius: 100px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.src-reddit { background: rgba(255, 69, 0, 0.15); color: #ff6b35; }
.src-hackernews { background: rgba(255, 102, 0, 0.15); color: #ff8c42; }
.src-github { background: rgba(110, 84, 148, 0.2); color: #a78bfa; }
.src-arxiv { background: rgba(180, 30, 30, 0.15); color: #ef6b6b; }
.src-producthunt { background: rgba(218, 85, 47, 0.15); color: #e8824a; }
.src-devto { background: rgba(0, 0, 0, 0.15); color: #aaa; }

.signal-narrative {
  font-size: 0.9rem;
  color: var(--text-secondary);
  margin-bottom: 12px;
  line-height: 1.6;
}

.signal-opportunity {
  font-size: 0.85rem;
  padding: 12px 16px;
  background: rgba(52, 211, 153, 0.06);
  border-left: 3px solid var(--accent-green);
  border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
  color: var(--accent-green);
}

.signal-confidence {
  font-family: var(--font-mono);
  font-size: 0.65rem;
  color: var(--text-muted);
  margin-top: 8px;
  text-transform: uppercase;
  letter-spacing: 0.1em;
}

/* ─── SOURCE SECTIONS ─── */
.source-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 16px;
  margin-bottom: 40px;
}

.item-card {
  padding: 20px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  transition: all 0.2s;
  text-decoration: none;
  color: inherit;
  display: block;
}

.item-card:hover {
  border-color: var(--accent-blue);
  transform: translateY(-2px);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}

.item-source {
  font-family: var(--font-mono);
  font-size: 0.6rem;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: var(--text-muted);
  margin-bottom: 8px;
}

.item-title {
  font-size: 0.95rem;
  font-weight: 600;
  margin-bottom: 8px;
  line-height: 1.4;
}

.item-ai-insight {
  font-size: 0.8rem;
  color: var(--text-secondary);
  margin-bottom: 12px;
  padding: 8px 12px;
  background: var(--glow-blue);
  border-radius: var(--radius-sm);
  border-left: 2px solid var(--accent-blue);
}

.item-meta {
  font-family: var(--font-mono);
  font-size: 0.7rem;
  color: var(--text-muted);
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.item-score {
  color: var(--accent-orange);
}

.item-keywords {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  margin-top: 8px;
}

.keyword-tag {
  font-family: var(--font-mono);
  font-size: 0.6rem;
  padding: 2px 8px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--border);
  border-radius: 100px;
  color: var(--text-muted);
}

/* ─── STATS BAR ─── */
.stats-bar {
  display: flex;
  gap: 24px;
  padding: 16px 0;
  margin-bottom: 24px;
  border-bottom: 1px solid var(--border);
  flex-wrap: wrap;
}

.stat {
  font-family: var(--font-mono);
  font-size: 0.75rem;
}

.stat-value {
  color: var(--accent-cyan);
  font-weight: 700;
  font-size: 1.1rem;
}

.stat-label {
  color: var(--text-muted);
  font-size: 0.65rem;
  text-transform: uppercase;
  letter-spacing: 0.1em;
}

/* ─── NAV TABS ─── */
.source-tabs {
  display: flex;
  gap: 4px;
  margin-bottom: 24px;
  overflow-x: auto;
  padding-bottom: 4px;
}

.tab {
  font-family: var(--font-mono);
  font-size: 0.75rem;
  padding: 8px 16px;
  border-radius: 100px;
  border: 1px solid var(--border);
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.2s;
}

.tab:hover, .tab.active {
  background: var(--glow-blue);
  border-color: var(--accent-blue);
  color: var(--accent-blue);
}

/* ─── FOOTER ─── */
.site-footer {
  padding: 32px 0;
  border-top: 1px solid var(--border);
  margin-top: 60px;
  text-align: center;
}

.footer-text {
  font-family: var(--font-mono);
  font-size: 0.7rem;
  color: var(--text-muted);
}

.footer-text a {
  color: var(--accent-cyan);
  text-decoration: none;
}

/* ─── RESPONSIVE ─── */
@media (max-width: 768px) {
  .brief-headline { font-size: 1.3rem; }
  .source-grid { grid-template-columns: 1fr; }
  .stats-bar { gap: 16px; }
  .container { padding: 0 16px; }
  .daily-brief { padding: 20px; }
}

/* ─── ANIMATIONS ─── */
@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

.daily-brief { animation: fadeInUp 0.6s ease-out; }
.signal-card { animation: fadeInUp 0.6s ease-out; }
.item-card { animation: fadeInUp 0.4s ease-out; }

/* Pain signal highlight */
.pain-flag {
  display: inline-block;
  font-family: var(--font-mono);
  font-size: 0.6rem;
  padding: 2px 8px;
  background: rgba(239, 68, 68, 0.12);
  color: var(--accent-red);
  border-radius: 100px;
  margin-left: 8px;
}
"""


def _escape_html(text: str) -> str:
    """Escape HTML special characters."""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


def _source_pill(source: str) -> str:
    return f'<span class="source-pill src-{source}">{source}</span>'


def build_index_page(processed_data: dict) -> str:
    """Build the main index.html page."""
    all_data = processed_data.get("data", {})
    cross_signals = processed_data.get("cross_signals", [])
    summary = processed_data.get("daily_summary", {})
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # Stats
    total_items = sum(len(items) for items in all_data.values())
    total_sources = len(all_data)
    pain_count = sum(
        1 for items in all_data.values()
        for item in items if item.get("has_pain")
    )

    # Build cross-signal cards
    cross_html = ""
    for sig in cross_signals[:8]:
        sources_pills = ""
        sources_list = sig.get("sources_involved", sig.get("sources", []))
        for s in sources_list:
            sources_pills += _source_pill(s)

        narrative = _escape_html(sig.get("narrative", ""))
        opportunity = _escape_html(sig.get("builder_opportunity", sig.get("keyword", "")))
        confidence = sig.get("confidence", "")
        keyword = _escape_html(sig.get("signal", sig.get("keyword", "")))

        cross_html += f"""
        <div class="signal-card">
          <div class="signal-header">
            <span class="signal-keyword">{keyword}</span>
            <div class="signal-sources">{sources_pills}</div>
          </div>
          <p class="signal-narrative">{narrative}</p>
          {"<div class='signal-opportunity'>" + opportunity + "</div>" if opportunity else ""}
          {"<p class='signal-confidence'>confidence: " + confidence + "</p>" if confidence else ""}
        </div>"""

    # Build source item cards
    source_sections = ""
    source_order = ["reddit", "hackernews", "github", "arxiv", "producthunt", "devto"]
    source_labels = {
        "reddit": "Reddit",
        "hackernews": "Hacker News",
        "github": "GitHub Trending",
        "arxiv": "ArXiv Papers",
        "producthunt": "Product Hunt",
        "devto": "DEV.to",
    }

    for source in source_order:
        items = all_data.get(source, [])
        if not items:
            continue

        label = source_labels.get(source, source)
        cards_html = ""

        # Sort by AI-assigned score
        display_items = sorted(
            items[:15],
            key=lambda x: x.get("ai", {}).get("opportunity_score", 0)
            or x.get("ai", {}).get("relevance", 0)
            or x.get("ai", {}).get("novelty_score", 0)
            or x.get("ai", {}).get("hype_vs_substance", 0)
            or x.get("score", 0)
            or x.get("stars", 0)
            or x.get("points", 0)
            or 0,
            reverse=True,
        )

        for item in display_items[:10]:
            title = _escape_html(item.get("title", item.get("name", "Untitled")))
            url = item.get("url", item.get("hn_url", "#"))
            ai = item.get("ai", {})

            insight = _escape_html(
                ai.get("one_liner", "")
                or ai.get("eli5", "")
                or ai.get("market_signal", "")
            )

            # Meta info varies by source
            meta_parts = []
            if item.get("score"):
                meta_parts.append(f'<span class="item-score">⬆ {item["score"]}</span>')
            if item.get("points"):
                meta_parts.append(f'<span class="item-score">⬆ {item["points"]}</span>')
            if item.get("stars"):
                meta_parts.append(f'<span class="item-score">★ {item["stars"]}</span>')
            if item.get("num_comments"):
                meta_parts.append(f'<span>💬 {item["num_comments"]}</span>')
            if item.get("sub"):
                meta_parts.append(f'<span>r/{item["sub"]}</span>')
            if item.get("language"):
                meta_parts.append(f'<span>{item["language"]}</span>')
            if item.get("star_velocity"):
                meta_parts.append(f'<span>+{item["star_velocity"]}★/day</span>')

            meta_html = " ".join(meta_parts)

            # Keywords
            keywords = ai.get("keywords", [])
            kw_html = "".join(
                f'<span class="keyword-tag">{_escape_html(k)}</span>'
                for k in keywords[:4]
            )

            pain_html = ""
            if item.get("has_pain"):
                pain_html = '<span class="pain-flag">🔥 pain signal</span>'

            build_idea = ai.get("build_idea") or ai.get("builder_takeaway") or ai.get("builder_action", "")
            build_html = ""
            if build_idea and build_idea != "null":
                build_html = f'<div class="signal-opportunity" style="margin-top:8px;font-size:0.75rem;">{_escape_html(build_idea)}</div>'

            cards_html += f"""
            <a href="{_escape_html(url)}" target="_blank" rel="noopener" class="item-card" data-source="{source}">
              <div class="item-source">{source}{pain_html}</div>
              <div class="item-title">{title}</div>
              {"<div class='item-ai-insight'>🧠 " + insight + "</div>" if insight else ""}
              {build_html}
              <div class="item-meta">{meta_html}</div>
              <div class="item-keywords">{kw_html}</div>
            </a>"""

        source_sections += f"""
        <div class="source-section" id="source-{source}">
          <div class="section-header">
            <h2 class="section-title">{label}</h2>
            <span class="section-badge badge-live">{len(items)} items</span>
          </div>
          <div class="source-grid">{cards_html}</div>
        </div>"""

    # Tab buttons
    tabs_html = '<button class="tab active" onclick="showAll()">All Sources</button>'
    for source in source_order:
        if source in all_data and all_data[source]:
            label = source_labels.get(source, source)
            tabs_html += f'<button class="tab" onclick="filterSource(\'{source}\')">{label}</button>'

    # Daily brief
    headline = _escape_html(summary.get("headline", "Daily Intelligence Brief"))
    tldr = _escape_html(summary.get("tldr", "Processing complete."))
    opportunity = _escape_html(summary.get("top_opportunity", ""))
    trend = _escape_html(summary.get("emerging_trend", ""))
    contrarian = _escape_html(summary.get("contrarian_take", ""))

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{SITE_NAME} — {SITE_TAGLINE}</title>
  <meta name="description" content="{_escape_html(SITE_DESCRIPTION)}">
  <meta name="robots" content="index, follow">
  <meta property="og:title" content="{SITE_NAME} — {headline}">
  <meta property="og:description" content="{tldr}">
  <meta property="og:type" content="website">
  <meta property="og:url" content="{SITE_URL}">
  <link rel="canonical" href="{SITE_URL}">
  <style>{SITE_CSS}</style>
</head>
<body>
  <div class="container">
    <!-- HEADER -->
    <header class="site-header">
      <div class="header-inner">
        <a href="/" class="logo">NexScry<span>.xyz</span></a>
        <div class="header-meta">
          <span class="live-dot"></span>updated {now}
        </div>
      </div>
    </header>

    <!-- DAILY BRIEF -->
    <section class="daily-brief">
      <div class="brief-label">📡 Daily Intelligence Brief</div>
      <h1 class="brief-headline">{headline}</h1>
      <p class="brief-tldr">{tldr}</p>
      <div class="brief-cards">
        {"<div class='brief-card'><div class='brief-card-label opportunity'>🎯 Top Opportunity</div><p class='brief-card-text'>" + opportunity + "</p></div>" if opportunity else ""}
        {"<div class='brief-card'><div class='brief-card-label trend'>📈 Emerging Trend</div><p class='brief-card-text'>" + trend + "</p></div>" if trend else ""}
        {"<div class='brief-card'><div class='brief-card-label contrarian'>🤔 Contrarian Take</div><p class='brief-card-text'>" + contrarian + "</p></div>" if contrarian else ""}
      </div>
    </section>

    <!-- STATS BAR -->
    <div class="stats-bar">
      <div class="stat"><div class="stat-value">{total_items}</div><div class="stat-label">Items Scraped</div></div>
      <div class="stat"><div class="stat-value">{total_sources}</div><div class="stat-label">Sources</div></div>
      <div class="stat"><div class="stat-value">{len(cross_signals)}</div><div class="stat-label">Cross-Signals</div></div>
      <div class="stat"><div class="stat-value">{pain_count}</div><div class="stat-label">Pain Points</div></div>
    </div>

    <!-- CROSS-SOURCE INTELLIGENCE -->
    {"<section class='cross-signals'><div class='section-header'><h2 class='section-title'>Cross-Source Intelligence</h2><span class='section-badge badge-ai'>AI-Detected</span></div>" + cross_html + "</section>" if cross_html else ""}

    <!-- SOURCE TABS -->
    <div class="source-tabs">{tabs_html}</div>

    <!-- SOURCE SECTIONS -->
    {source_sections}

    <!-- FOOTER -->
    <footer class="site-footer">
      <p class="footer-text">
        {SITE_NAME} — auto-generated daily by Groq AI · 
        Data from Reddit, HN, GitHub, ArXiv, Product Hunt, DEV.to · 
        <a href="https://github.com/nexscry">GitHub</a>
      </p>
    </footer>
  </div>

  <script>
    function showAll() {{
      document.querySelectorAll('.source-section').forEach(s => s.style.display = '');
      document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
      document.querySelector('.tab').classList.add('active');
    }}
    function filterSource(src) {{
      document.querySelectorAll('.source-section').forEach(s => {{
        s.style.display = s.id === 'source-' + src ? '' : 'none';
      }});
      document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
      event.target.classList.add('active');
    }}
  </script>
</body>
</html>"""


def build_site(processed_data: dict):
    """Build entire static site."""
    os.makedirs(BUILD_DIR, exist_ok=True)

    # Main index
    index_html = build_index_page(processed_data)
    with open(os.path.join(BUILD_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(index_html)
    print(f"  ✅ Built {BUILD_DIR}/index.html")

    # CNAME for custom domain
    cname_path = os.path.join(BUILD_DIR, "CNAME")
    if not os.path.exists(cname_path):
        with open(cname_path, "w") as f:
            f.write("nexscry.xyz")

    # Save processed data as JSON (for API-like access)
    data_dir = os.path.join(BUILD_DIR, "api")
    os.makedirs(data_dir, exist_ok=True)

    with open(os.path.join(data_dir, "latest.json"), "w", encoding="utf-8") as f:
        json.dump(processed_data, f, ensure_ascii=False, indent=2)
    print(f"  ✅ Built {BUILD_DIR}/api/latest.json")

    # .nojekyll (tells GitHub Pages to serve as-is)
    with open(os.path.join(BUILD_DIR, ".nojekyll"), "w") as f:
        f.write("")

    print(f"  🎉 Site build complete!")
