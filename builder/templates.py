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
# BRANDING ASSETS
# ─────────────────────────────────────────────

# Inline SVG favicon — "N" logo, dark rounded square, cyan letter
FAVICON_SVG = """\
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">
  <rect width="32" height="32" rx="7" fill="#0a0a0f"/>
  <rect x="6" y="6" width="4" height="20" rx="1" fill="#22d3ee"/>
  <rect x="22" y="6" width="4" height="20" rx="1" fill="#22d3ee"/>
  <line x1="6" y1="6" x2="26" y2="26" stroke="#22d3ee" stroke-width="4.5" stroke-linecap="round"/>
</svg>"""

# 1200×630 OG image — shown when shared on Twitter/LinkedIn
OG_IMAGE_SVG = """\
<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630">
  <defs>
    <linearGradient id="topbar" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#22d3ee"/>
      <stop offset="50%" stop-color="#4d7cff"/>
      <stop offset="100%" stop-color="#a78bfa"/>
    </linearGradient>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0a0a0f"/>
      <stop offset="100%" stop-color="#111118"/>
    </linearGradient>
  </defs>
  <rect width="1200" height="630" fill="url(#bg)"/>
  <rect y="0" width="1200" height="5" fill="url(#topbar)"/>
  <text x="80" y="210" font-family="monospace" font-size="88" font-weight="700" fill="#22d3ee">NexScry</text>
  <text x="80" y="278" font-family="-apple-system,sans-serif" font-size="36" fill="#8888a0">AI-powered intelligence layer for builders</text>
  <rect x="80" y="315" width="70" height="4" rx="2" fill="#22d3ee"/>
  <rect x="80" y="365" width="190" height="46" rx="23" fill="#16161f" stroke="#2a2a3a" stroke-width="1"/>
  <text x="175" y="394" font-family="monospace" font-size="18" fill="#22d3ee" text-anchor="middle">6 sources</text>
  <rect x="290" y="365" width="250" height="46" rx="23" fill="#16161f" stroke="#2a2a3a" stroke-width="1"/>
  <text x="415" y="394" font-family="monospace" font-size="18" fill="#a78bfa" text-anchor="middle">AI cross-signals</text>
  <rect x="560" y="365" width="210" height="46" rx="23" fill="#16161f" stroke="#2a2a3a" stroke-width="1"/>
  <text x="665" y="394" font-family="monospace" font-size="18" fill="#34d399" text-anchor="middle">updated daily</text>
  <text x="80" y="510" font-family="monospace" font-size="24" fill="#3d3d55">Reddit · HN · GitHub · ArXiv · Product Hunt · DEV.to</text>
  <text x="80" y="580" font-family="monospace" font-size="24" fill="#2a2a3a">nexscry.xyz</text>
</svg>"""


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

/* ─── SEARCH BAR ─── */
.search-wrapper {
  position: relative;
  margin-bottom: 24px;
}

.search-input {
  width: 100%;
  padding: 12px 16px 12px 44px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  color: var(--text-primary);
  font-family: var(--font-display);
  font-size: 0.9rem;
  outline: none;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.search-input::placeholder { color: var(--text-muted); }

.search-input:focus {
  border-color: var(--accent-blue);
  box-shadow: 0 0 0 3px var(--glow-blue);
}

.search-icon {
  position: absolute;
  left: 14px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--text-muted);
  font-size: 1rem;
  pointer-events: none;
}

.search-count {
  font-family: var(--font-mono);
  font-size: 0.7rem;
  color: var(--text-muted);
  margin-bottom: 16px;
  min-height: 1em;
}

.search-count span { color: var(--accent-cyan); }

/* ─── SCROLL TO TOP ─── */
.scroll-top {
  position: fixed;
  bottom: 32px;
  right: 32px;
  width: 44px;
  height: 44px;
  background: var(--bg-card);
  border: 1px solid var(--border-accent);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  opacity: 0;
  transform: translateY(16px);
  transition: opacity 0.3s, transform 0.3s, border-color 0.2s;
  z-index: 100;
  font-size: 1rem;
  color: var(--text-secondary);
}

.scroll-top.visible {
  opacity: 1;
  transform: translateY(0);
}

.scroll-top:hover {
  border-color: var(--accent-cyan);
  color: var(--accent-cyan);
}

/* ─── NO RESULTS ─── */
.no-results {
  text-align: center;
  padding: 60px 20px;
  color: var(--text-muted);
  font-family: var(--font-mono);
  font-size: 0.85rem;
  display: none;
}

/* ─── RESPONSIVE ─── */
@media (max-width: 768px) {
  .brief-headline { font-size: 1.3rem; }
  .source-grid { grid-template-columns: 1fr; }
  .stats-bar { gap: 16px; }
  .container { padding: 0 16px; }
  .daily-brief { padding: 20px; }
  .scroll-top { bottom: 20px; right: 20px; }
}

/* ─── ANIMATIONS ─── */
@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

.daily-brief { animation: fadeInUp 0.5s ease-out; }
.signal-card { animation: fadeInUp 0.5s ease-out both; }
.item-card { animation: fadeInUp 0.4s ease-out both; }

/* Staggered animation delays for cards */
.item-card:nth-child(1) { animation-delay: 0.05s; }
.item-card:nth-child(2) { animation-delay: 0.10s; }
.item-card:nth-child(3) { animation-delay: 0.15s; }
.item-card:nth-child(4) { animation-delay: 0.20s; }
.item-card:nth-child(5) { animation-delay: 0.25s; }
.item-card:nth-child(6) { animation-delay: 0.30s; }
.item-card:nth-child(7) { animation-delay: 0.35s; }
.item-card:nth-child(8) { animation-delay: 0.40s; }
.item-card:nth-child(9) { animation-delay: 0.45s; }
.item-card:nth-child(10) { animation-delay: 0.50s; }

.signal-card:nth-child(1) { animation-delay: 0.05s; }
.signal-card:nth-child(2) { animation-delay: 0.10s; }
.signal-card:nth-child(3) { animation-delay: 0.15s; }
.signal-card:nth-child(4) { animation-delay: 0.20s; }
.signal-card:nth-child(5) { animation-delay: 0.25s; }

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

/* ─── READING PROGRESS BAR ─── */
.progress-bar {
  position: fixed;
  top: 0; left: 0;
  height: 2px;
  width: 0%;
  background: linear-gradient(90deg, var(--accent-cyan), var(--accent-blue), var(--accent-purple));
  z-index: 1000;
  transition: width 0.1s linear;
}

/* ─── SHARE BUTTON ─── */
.share-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  background: transparent;
  border: 1px solid var(--border-accent);
  border-radius: 100px;
  color: var(--text-secondary);
  font-family: var(--font-mono);
  font-size: 0.75rem;
  cursor: pointer;
  transition: all 0.2s;
  margin-top: 20px;
  text-decoration: none;
}

.share-btn:hover {
  border-color: var(--accent-cyan);
  color: var(--accent-cyan);
  background: var(--glow-cyan);
}

.brief-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin-top: 20px;
}

/* ─── COPY BUTTON ─── */
.copy-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px; height: 24px;
  background: transparent;
  border: 1px solid var(--border);
  border-radius: 6px;
  color: var(--text-muted);
  font-size: 0.7rem;
  cursor: pointer;
  transition: all 0.15s;
  vertical-align: middle;
  margin-left: 6px;
  flex-shrink: 0;
}

.copy-btn:hover {
  border-color: var(--accent-blue);
  color: var(--accent-blue);
}

.item-ai-insight {
  display: flex;
  align-items: flex-start;
  gap: 6px;
}

.item-ai-insight span { flex: 1; }

/* ─── TRENDING TOPICS ─── */
.trending-section {
  margin: 32px 0;
}

.topics-cloud {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  padding: 20px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
}

.topic-pill {
  font-family: var(--font-mono);
  padding: 6px 14px;
  background: rgba(255,255,255,0.03);
  border: 1px solid var(--border);
  border-radius: 100px;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s;
  text-decoration: none;
  display: inline-block;
  line-height: 1;
}

.topic-pill:hover {
  border-color: var(--accent-cyan);
  color: var(--accent-cyan);
  background: var(--glow-cyan);
}

.topic-pill.hot { border-color: rgba(251, 146, 60, 0.4); color: var(--accent-orange); }
.topic-pill.warm { border-color: rgba(77, 124, 255, 0.35); color: var(--accent-blue); }
.topic-pill.cool { border-color: rgba(167, 139, 250, 0.3); color: var(--accent-purple); }

/* ─── NEWSLETTER CTA ─── */
.newsletter-cta {
  margin: 40px 0;
  padding: 28px 32px;
  background: linear-gradient(135deg, var(--bg-card) 0%, rgba(34, 211, 238, 0.04) 100%);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  display: flex;
  align-items: center;
  gap: 24px;
  flex-wrap: wrap;
  position: relative;
  overflow: hidden;
}

.newsletter-cta::before {
  content: '';
  position: absolute;
  bottom: 0; right: 0;
  width: 200px; height: 200px;
  background: radial-gradient(circle, rgba(34, 211, 238, 0.06) 0%, transparent 70%);
  pointer-events: none;
}

.cta-icon { font-size: 2rem; flex-shrink: 0; }

.cta-body { flex: 1; min-width: 200px; }

.cta-title {
  font-size: 1.1rem;
  font-weight: 700;
  margin-bottom: 6px;
}

.cta-desc {
  font-size: 0.85rem;
  color: var(--text-secondary);
  line-height: 1.5;
}

.cta-links {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  flex-shrink: 0;
}

.cta-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  border-radius: 100px;
  font-family: var(--font-mono);
  font-size: 0.75rem;
  text-decoration: none;
  transition: all 0.2s;
  white-space: nowrap;
}

.cta-btn-primary {
  background: var(--accent-cyan);
  color: #0a0a0f;
  border: 1px solid var(--accent-cyan);
  font-weight: 700;
}

.cta-btn-primary:hover { opacity: 0.85; }

.cta-btn-secondary {
  background: transparent;
  color: var(--text-secondary);
  border: 1px solid var(--border-accent);
}

.cta-btn-secondary:hover {
  border-color: var(--accent-orange);
  color: var(--accent-orange);
}

/* ─── CUSTOM SCROLLBAR ─── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: var(--bg-primary); }
::-webkit-scrollbar-thumb { background: var(--border-accent); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--accent-blue); }

@media (max-width: 768px) {
  .newsletter-cta { flex-direction: column; gap: 16px; }
  .cta-links { width: 100%; }
  .cta-btn { justify-content: center; flex: 1; }
}
"""


def _escape_xml(text: str) -> str:
    """Escape XML/RSS special characters."""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def _extract_trending_topics(all_data: dict) -> list:
    """Count keyword frequency across all enriched items, return top 20."""
    counts: dict = {}
    for items in all_data.values():
        for item in items:
            for kw in item.get("ai", {}).get("keywords", []):
                kw = kw.lower().strip()
                if len(kw) >= 3:
                    counts[kw] = counts.get(kw, 0) + 1
    # Filter trivial words
    stop = {"api", "app", "use", "new", "one", "get", "set", "two", "llm", "ai"}
    sorted_topics = sorted(
        [(k, v) for k, v in counts.items() if k not in stop and v >= 1],
        key=lambda x: x[1],
        reverse=True,
    )
    return sorted_topics[:20]


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

    # Trending topics cloud
    trending_topics = _extract_trending_topics(all_data)
    topics_html = ""
    for i, (topic, count) in enumerate(trending_topics):
        size = "hot" if count >= 4 else ("warm" if count >= 2 else "cool")
        font_size = 1.0 if count >= 4 else (0.85 if count >= 2 else 0.75)
        topics_html += f'<a href="javascript:void(0)" class="topic-pill {size}" style="font-size:{font_size}rem" onclick="document.getElementById(\'searchInput\').value=\'{_escape_html(topic)}\';handleSearch(\'{_escape_html(topic)}\');document.getElementById(\'searchInput\').scrollIntoView({{behavior:\'smooth\'}})">{_escape_html(topic)} <span style="opacity:0.5;font-size:0.7em">{count}</span></a>'

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

            copy_btn = ""
            if insight:
                raw_insight = (
                    ai.get("one_liner", "")
                    or ai.get("eli5", "")
                    or ai.get("market_signal", "")
                ).replace('"', '&quot;').replace("'", "&#39;")
                copy_btn = f'<button class="copy-btn" onclick="event.preventDefault();copyText(this,\'{raw_insight}\')" title="Copy insight">⎘</button>'

            cards_html += f"""
            <a href="{_escape_html(url)}" target="_blank" rel="noopener" class="item-card" data-source="{source}">
              <div class="item-source">{source}{pain_html}</div>
              <div class="item-title">{title}</div>
              {"<div class='item-ai-insight'>🧠 <span>" + insight + "</span>" + copy_btn + "</div>" if insight else ""}
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
    tabs_html = '<button class="tab active" onclick="showAll(this)">All Sources</button>'
    for source in source_order:
        if source in all_data and all_data[source]:
            label = source_labels.get(source, source)
            tabs_html += f'<button class="tab" onclick="filterSource(\'{source}\', this)">{label}</button>'

    # Daily brief
    headline = _escape_html(summary.get("headline", "Daily Intelligence Brief"))
    tldr = _escape_html(summary.get("tldr", "Processing complete."))
    opportunity = _escape_html(summary.get("top_opportunity", ""))
    trend = _escape_html(summary.get("emerging_trend", ""))
    contrarian = _escape_html(summary.get("contrarian_take", ""))

    today_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    json_ld = json.dumps({
        "@context": "https://schema.org",
        "@type": "NewsArticle",
        "headline": summary.get("headline", "Daily Intelligence Brief"),
        "description": summary.get("tldr", SITE_DESCRIPTION),
        "url": SITE_URL,
        "datePublished": today_iso,
        "dateModified": today_iso,
        "publisher": {
            "@type": "Organization",
            "name": SITE_NAME,
            "url": SITE_URL,
            "logo": {"@type": "ImageObject", "url": f"{SITE_URL}/favicon.svg"},
        },
        "image": f"{SITE_URL}/og-image.svg",
    }, ensure_ascii=False)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{SITE_NAME} — {headline}</title>
  <meta name="description" content="{_escape_html(summary.get('tldr', SITE_DESCRIPTION)[:160])}">
  <meta name="robots" content="index, follow">
  <meta name="theme-color" content="#0a0a0f">

  <!-- Open Graph -->
  <meta property="og:title" content="{SITE_NAME} — {headline}">
  <meta property="og:description" content="{tldr}">
  <meta property="og:type" content="article">
  <meta property="og:url" content="{SITE_URL}">
  <meta property="og:image" content="{SITE_URL}/og-image.svg">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:site_name" content="{SITE_NAME}">

  <!-- Twitter Card -->
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:creator" content="@nexscry">
  <meta name="twitter:title" content="{SITE_NAME} — {headline}">
  <meta name="twitter:description" content="{tldr}">
  <meta name="twitter:image" content="{SITE_URL}/og-image.svg">

  <!-- Canonical + RSS -->
  <link rel="canonical" href="{SITE_URL}">
  <link rel="alternate" type="application/rss+xml" title="{SITE_NAME} Daily Brief" href="{SITE_URL}/feed.xml">

  <!-- Favicon -->
  <link rel="icon" type="image/svg+xml" href="/favicon.svg">

  <!-- Structured Data -->
  <script type="application/ld+json">{json_ld}</script>

  <style>{SITE_CSS}</style>
</head>
<body>
  <div class="progress-bar" id="progressBar"></div>
  <div class="container">
    <!-- HEADER -->
    <header class="site-header">
      <div class="header-inner">
        <a href="/" class="logo">NexScry<span>.xyz</span></a>
        <div class="header-meta">
          <a href="/archive/" style="color:var(--text-muted);text-decoration:none;font-family:var(--font-mono);font-size:0.75rem;margin-right:16px;">Archive</a>
          <span class="live-dot"></span>updated {now}
        </div>
      </div>
    </header>

    <!-- DAILY BRIEF -->
    <section class="daily-brief">
      <div class="brief-label">📡 Daily Intelligence Brief · {today_iso}</div>
      <h1 class="brief-headline">{headline}</h1>
      <p class="brief-tldr">{tldr}</p>
      <div class="brief-cards">
        {"<div class='brief-card'><div class='brief-card-label opportunity'>🎯 Top Opportunity</div><p class='brief-card-text'>" + opportunity + "</p></div>" if opportunity else ""}
        {"<div class='brief-card'><div class='brief-card-label trend'>📈 Emerging Trend</div><p class='brief-card-text'>" + trend + "</p></div>" if trend else ""}
        {"<div class='brief-card'><div class='brief-card-label contrarian'>🤔 Contrarian Take</div><p class='brief-card-text'>" + contrarian + "</p></div>" if contrarian else ""}
      </div>
      <div class="brief-actions">
        <button class="share-btn" onclick="shareBrief()">↗ Share Today's Brief</button>
        <a href="/feed.xml" class="share-btn" title="Subscribe via RSS">⬡ RSS Feed</a>
        <a href="/archive/" class="share-btn">🗂 Archive</a>
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

    <!-- TRENDING TOPICS CLOUD -->
    {"<section class='trending-section'><div class='section-header'><h2 class='section-title'>Trending Topics</h2><span class='section-badge badge-live'>Today — click to filter</span></div><div class='topics-cloud'>" + topics_html + "</div></section>" if topics_html else ""}

    <!-- SOURCE TABS -->
    <div class="source-tabs">{tabs_html}</div>

    <!-- SEARCH -->
    <div class="search-wrapper">
      <span class="search-icon">🔍</span>
      <input
        class="search-input"
        type="search"
        id="searchInput"
        placeholder="Search topics, keywords, repos, papers..."
        oninput="handleSearch(this.value)"
        autocomplete="off"
      >
    </div>
    <div class="search-count" id="searchCount"></div>
    <div class="no-results" id="noResults">No results found. Try a different keyword.</div>

    <!-- SOURCE SECTIONS -->
    {source_sections}

    <!-- SPREAD THE WORD CTA -->
    <section class="newsletter-cta">
      <div class="cta-icon">📡</div>
      <div class="cta-body">
        <h3 class="cta-title">If this brief saved you time, spread the word</h3>
        <p class="cta-desc">Share it with a builder friend, post it on Reddit, or submit to Hacker News. That's how this grows.</p>
      </div>
      <div class="cta-links">
        <a href="/feed.xml" class="cta-btn cta-btn-primary" target="_blank">⬡ Subscribe via RSS</a>
        <a href="https://reddit.com/submit?url={SITE_URL}&title=NexScry+—+daily+AI+intelligence+for+builders" class="cta-btn cta-btn-secondary" target="_blank" rel="noopener">Share on Reddit</a>
        <a href="https://news.ycombinator.com/submitlink?u={SITE_URL}&t=NexScry+—+AI+intelligence+for+builders" class="cta-btn cta-btn-secondary" target="_blank" rel="noopener">Submit to HN</a>
        <a href="https://github.com/nexscry/nexscry" class="cta-btn cta-btn-secondary" target="_blank" rel="noopener">⭐ Star on GitHub</a>
      </div>
    </section>

    <!-- FOOTER -->
    <footer class="site-footer">
      <p class="footer-text">
        {SITE_NAME} — auto-generated daily · Powered by Groq AI ·
        Data: Reddit, HN, GitHub, ArXiv, Product Hunt, DEV.to ·
        <a href="/archive/">Archive</a> ·
        <a href="/feed.xml">RSS</a> ·
        <a href="https://github.com/nexscry/nexscry">GitHub</a>
      </p>
    </footer>
  </div>

  <!-- SCROLL TO TOP -->
  <button class="scroll-top" id="scrollTop" onclick="window.scrollTo({{top:0,behavior:'smooth'}})" title="Back to top">↑</button>

  <script>
    // ── Reading progress bar ──
    const progressBar = document.getElementById('progressBar');
    window.addEventListener('scroll', () => {{
      const scroll = document.documentElement.scrollTop;
      const height = document.documentElement.scrollHeight - document.documentElement.clientHeight;
      progressBar.style.width = (height > 0 ? (scroll / height) * 100 : 0) + '%';
    }}, {{ passive: true }});

    // ── Tab filtering ──
    function showAll(el) {{
      document.querySelectorAll('.source-section').forEach(s => s.style.removeProperty('display'));
      document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
      el.classList.add('active');
      handleSearch(document.getElementById('searchInput').value);
    }}
    function filterSource(src, el) {{
      document.querySelectorAll('.source-section').forEach(s => {{
        s.style.display = s.id === 'source-' + src ? '' : 'none';
      }});
      document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
      el.classList.add('active');
      handleSearch(document.getElementById('searchInput').value);
    }}

    // ── Search ──
    function handleSearch(query) {{
      const q = query.trim().toLowerCase();
      const cards = document.querySelectorAll('.item-card');
      let visible = 0;
      cards.forEach(card => {{
        const section = card.closest('.source-section');
        if (section && section.style.display === 'none') return;
        if (!q) {{ card.style.display = ''; visible++; return; }}
        if (card.textContent.toLowerCase().includes(q)) {{
          card.style.display = ''; visible++;
        }} else {{
          card.style.display = 'none';
        }}
      }});
      const countEl = document.getElementById('searchCount');
      const noResults = document.getElementById('noResults');
      if (q) {{
        countEl.innerHTML = 'Showing <span>' + visible + '</span> results for "<span>' + escHtml(query) + '</span>"';
        noResults.style.display = visible === 0 ? 'block' : 'none';
      }} else {{
        countEl.innerHTML = '';
        noResults.style.display = 'none';
      }}
    }}

    // ── Copy to clipboard ──
    function copyText(btn, text) {{
      const decoded = text.replace(/&amp;/g,'&').replace(/&lt;/g,'<').replace(/&gt;/g,'>').replace(/&quot;/g,'"').replace(/&#39;/g,"'");
      navigator.clipboard.writeText(decoded).then(() => {{
        const orig = btn.textContent;
        btn.textContent = '✓'; btn.style.color = 'var(--accent-green)';
        setTimeout(() => {{ btn.textContent = orig; btn.style.color = ''; }}, 2000);
      }}).catch(() => {{ btn.textContent = '✗'; }});
    }}

    // ── Share today's brief ──
    function shareBrief() {{
      const headline = document.querySelector('.brief-headline') ? document.querySelector('.brief-headline').textContent.trim() : '{SITE_NAME}';
      const url = window.location.origin || '{SITE_URL}';
      const text = 'Today on {SITE_NAME}: ' + headline;
      if (navigator.share) {{
        // Native share sheet on mobile — works for WhatsApp, Telegram, email, etc.
        navigator.share({{ title: '{SITE_NAME} Daily Brief', text: text, url: url }})
          .catch(() => {{}});
      }} else {{
        // Desktop fallback: copy link to clipboard
        navigator.clipboard.writeText(url + ' — ' + text).then(() => {{
          const btn = document.querySelector('.share-btn');
          if (btn) {{ const o = btn.textContent; btn.textContent = 'Link copied!'; setTimeout(() => btn.textContent = o, 2000); }}
        }}).catch(() => {{ window.open('https://reddit.com/submit?url=' + encodeURIComponent(url), '_blank'); }});
      }}
    }}

    // ── Scroll to top ──
    const scrollBtn = document.getElementById('scrollTop');
    window.addEventListener('scroll', () => {{
      scrollBtn.classList.toggle('visible', window.scrollY > 400);
    }}, {{ passive: true }});

    // ── Keyboard shortcut: / to focus search ──
    document.addEventListener('keydown', e => {{
      if (e.key === '/' && document.activeElement.tagName !== 'INPUT') {{
        e.preventDefault();
        document.getElementById('searchInput').focus();
      }}
    }});

    function escHtml(s) {{
      return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
    }}
  </script>
</body>
</html>"""


def build_archive_page(entries: list[dict]) -> str:
    """Build an archive/history page listing all past daily briefs."""
    rows = ""
    for e in sorted(entries, key=lambda x: x["date"], reverse=True):
        headline = _escape_html(e.get("headline", "Daily Brief"))
        date = _escape_html(e["date"])
        tldr = _escape_html(e.get("tldr", ""))[:120]
        rows += f"""
        <div class="archive-row">
          <a href="/archive/{date}.html" class="archive-link">
            <span class="archive-date">{date}</span>
            <div>
              <div class="archive-headline">{headline}</div>
              {"<div class='archive-tldr'>" + tldr + "…</div>" if tldr else ""}
            </div>
          </a>
        </div>"""

    if not rows:
        rows = '<p style="color:var(--text-muted);font-family:var(--font-mono);font-size:0.8rem;">No archive entries yet. Run the pipeline daily to build history.</p>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{SITE_NAME} — Archive</title>
  <meta name="description" content="Daily intelligence briefs archive — {SITE_NAME}">
  <style>
  {SITE_CSS}
  .archive-row {{ margin-bottom: 12px; }}
  .archive-link {{
    display: flex;
    gap: 20px;
    align-items: flex-start;
    padding: 16px 20px;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    text-decoration: none;
    color: inherit;
    transition: border-color 0.2s, background 0.2s;
  }}
  .archive-link:hover {{
    border-color: var(--accent-blue);
    background: var(--bg-card-hover);
  }}
  .archive-date {{
    font-family: var(--font-mono);
    font-size: 0.75rem;
    color: var(--accent-cyan);
    white-space: nowrap;
    min-width: 90px;
    padding-top: 2px;
  }}
  .archive-headline {{ font-weight: 600; font-size: 0.95rem; margin-bottom: 4px; }}
  .archive-tldr {{ font-size: 0.8rem; color: var(--text-muted); }}
  </style>
</head>
<body>
  <div class="container">
    <header class="site-header">
      <div class="header-inner">
        <a href="/" class="logo">NexScry<span>.xyz</span></a>
        <div class="header-meta"><a href="/" style="color:var(--accent-cyan);text-decoration:none;">← Back to today</a></div>
      </div>
    </header>
    <section style="margin:32px 0;">
      <div class="section-header">
        <h1 class="section-title">Archive</h1>
        <span class="section-badge badge-live">{len(entries)} briefs</span>
      </div>
      {rows}
    </section>
  </div>
</body>
</html>"""


def _update_archive_index(processed_data: dict):
    """Append today's summary to docs/archive/index.json."""
    archive_dir = os.path.join(BUILD_DIR, "archive")
    os.makedirs(archive_dir, exist_ok=True)
    index_path = os.path.join(archive_dir, "index.json")

    entries = []
    if os.path.exists(index_path):
        try:
            with open(index_path, "r", encoding="utf-8") as f:
                entries = json.load(f)
        except (json.JSONDecodeError, IOError):
            entries = []

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    summary = processed_data.get("daily_summary", {})
    new_entry = {
        "date": today,
        "headline": summary.get("headline", "Daily Intelligence Brief"),
        "tldr": summary.get("tldr", ""),
    }

    # Replace today's entry if it already exists (re-run scenario)
    entries = [e for e in entries if e.get("date") != today]
    entries.append(new_entry)

    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)

    return entries


def build_rss_feed(processed_data: dict) -> str:
    """Generate RSS 2.0 feed for the daily brief."""
    now = datetime.now(timezone.utc)
    rfc_date = now.strftime("%a, %d %b %Y %H:%M:%S +0000")
    today = now.strftime("%Y-%m-%d")
    summary = processed_data.get("daily_summary", {})
    cross_signals = processed_data.get("cross_signals", [])
    all_data = processed_data.get("data", {})

    items_xml = ""

    # Daily summary as first item
    headline = _escape_xml(summary.get("headline", "Daily Intelligence Brief"))
    tldr = _escape_xml(summary.get("tldr", ""))
    opportunity = _escape_xml(summary.get("top_opportunity", ""))
    trend = _escape_xml(summary.get("emerging_trend", ""))
    items_xml += f"""
    <item>
      <title>{headline}</title>
      <link>{SITE_URL}/archive/{today}.html</link>
      <guid isPermaLink="true">{SITE_URL}/archive/{today}.html</guid>
      <pubDate>{rfc_date}</pubDate>
      <description><![CDATA[<p>{summary.get("tldr","")}</p>{"<p><strong>Top Opportunity:</strong> " + summary.get("top_opportunity","") + "</p>" if opportunity else ""}{"<p><strong>Emerging Trend:</strong> " + summary.get("emerging_trend","") + "</p>" if trend else ""}]]></description>
      <category>Daily Brief</category>
    </item>"""

    # Cross-signals as items
    for sig in cross_signals[:5]:
        sig_title = _escape_xml(sig.get("signal", sig.get("keyword", "Signal")))
        narrative = sig.get("narrative", "")
        opp = sig.get("builder_opportunity", "")
        items_xml += f"""
    <item>
      <title>Signal: {sig_title}</title>
      <link>{SITE_URL}/#cross-signals</link>
      <guid>{SITE_URL}/signal/{today}-{re.sub(r"[^a-z0-9]", "-", sig_title.lower())[:40]}</guid>
      <pubDate>{rfc_date}</pubDate>
      <description><![CDATA[<p>{narrative}</p>{"<p><strong>Builder Opportunity:</strong> " + opp + "</p>" if opp else ""}]]></description>
      <category>Cross-Source Intelligence</category>
    </item>"""

    # Top items per source
    for source, items in all_data.items():
        for item in sorted(items, key=lambda x: x.get("score", 0) or x.get("points", 0) or x.get("stars", 0) or 0, reverse=True)[:3]:
            title = _escape_xml(item.get("title", item.get("name", "")))
            url = item.get("url", item.get("hn_url", SITE_URL))
            insight = item.get("ai", {}).get("one_liner") or item.get("ai", {}).get("eli5") or ""
            if not title:
                continue
            items_xml += f"""
    <item>
      <title>[{source.upper()}] {title}</title>
      <link>{_escape_xml(url)}</link>
      <guid>{_escape_xml(url)}</guid>
      <pubDate>{rfc_date}</pubDate>
      <description><![CDATA[{"<p>" + insight + "</p>" if insight else ""}]]></description>
      <category>{source}</category>
    </item>"""

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:content="http://purl.org/rss/1.0/modules/content/">
  <channel>
    <title>{_escape_xml(SITE_NAME)} — Daily Intelligence Brief</title>
    <link>{SITE_URL}</link>
    <description>{_escape_xml(SITE_DESCRIPTION)}</description>
    <language>en-us</language>
    <pubDate>{rfc_date}</pubDate>
    <lastBuildDate>{rfc_date}</lastBuildDate>
    <ttl>1440</ttl>
    <atom:link href="{SITE_URL}/feed.xml" rel="self" type="application/rss+xml"/>
    <image>
      <url>{SITE_URL}/og-image.svg</url>
      <title>{_escape_xml(SITE_NAME)}</title>
      <link>{SITE_URL}</link>
    </image>
    {items_xml}
  </channel>
</rss>"""


def build_sitemap(archive_entries: list) -> str:
    """Generate XML sitemap for SEO."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    urls = [
        f"  <url><loc>{SITE_URL}/</loc><lastmod>{today}</lastmod><changefreq>daily</changefreq><priority>1.0</priority></url>",
        f"  <url><loc>{SITE_URL}/archive/</loc><lastmod>{today}</lastmod><changefreq>daily</changefreq><priority>0.8</priority></url>",
        f"  <url><loc>{SITE_URL}/feed.xml</loc><lastmod>{today}</lastmod><changefreq>daily</changefreq><priority>0.5</priority></url>",
    ]
    for entry in archive_entries:
        date = entry.get("date", "")
        if date:
            urls.append(
                f"  <url><loc>{SITE_URL}/archive/{date}.html</loc><lastmod>{date}</lastmod><changefreq>never</changefreq><priority>0.6</priority></url>"
            )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(urls)
        + "\n</urlset>"
    )


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
    api_dir = os.path.join(BUILD_DIR, "api")
    os.makedirs(api_dir, exist_ok=True)
    with open(os.path.join(api_dir, "latest.json"), "w", encoding="utf-8") as f:
        json.dump(processed_data, f, ensure_ascii=False, indent=2)
    print(f"  ✅ Built {BUILD_DIR}/api/latest.json")

    # Favicon SVG
    with open(os.path.join(BUILD_DIR, "favicon.svg"), "w", encoding="utf-8") as f:
        f.write(FAVICON_SVG)

    # OG image SVG
    with open(os.path.join(BUILD_DIR, "og-image.svg"), "w", encoding="utf-8") as f:
        f.write(OG_IMAGE_SVG)
    print(f"  ✅ Built {BUILD_DIR}/favicon.svg + og-image.svg")

    # RSS feed
    rss_content = build_rss_feed(processed_data)
    with open(os.path.join(BUILD_DIR, "feed.xml"), "w", encoding="utf-8") as f:
        f.write(rss_content)
    print(f"  ✅ Built {BUILD_DIR}/feed.xml")

    # Archive: save today's brief as standalone page
    archive_dir = os.path.join(BUILD_DIR, "archive")
    os.makedirs(archive_dir, exist_ok=True)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    with open(os.path.join(archive_dir, f"{today}.html"), "w", encoding="utf-8") as f:
        f.write(index_html)

    # Update archive index + build archive listing page
    entries = _update_archive_index(processed_data)
    archive_page = build_archive_page(entries)
    with open(os.path.join(archive_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(archive_page)
    print(f"  ✅ Built {BUILD_DIR}/archive/ ({len(entries)} entries)")

    # Sitemap
    sitemap_content = build_sitemap(entries)
    with open(os.path.join(BUILD_DIR, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(sitemap_content)
    print(f"  ✅ Built {BUILD_DIR}/sitemap.xml")

    # robots.txt
    with open(os.path.join(BUILD_DIR, "robots.txt"), "w", encoding="utf-8") as f:
        f.write(
            f"User-agent: *\nAllow: /\n\nSitemap: {SITE_URL}/sitemap.xml\n"
        )
    print(f"  ✅ Built {BUILD_DIR}/robots.txt")

    # .nojekyll (tells GitHub Pages to serve as-is)
    with open(os.path.join(BUILD_DIR, ".nojekyll"), "w") as f:
        f.write("")

    print(f"  🎉 Site build complete! Generated: index, feed.xml, sitemap.xml, robots.txt, og-image.svg, favicon.svg, archive/")
