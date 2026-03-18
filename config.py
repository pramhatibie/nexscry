"""
NexScry Configuration
All settings centralized here. Override via environment variables.
"""
import os

# ─────────────────────────────────────────────
# API Keys (set as GitHub Secrets)
# ─────────────────────────────────────────────
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
GEMINI_FALLBACK_MODEL = "gemini-1.5-flash"  # fallback if primary unavailable

# Email subscribe — set BEEHIIV_PUB_ID as GitHub Secret to enable the form
# Get your pub ID from app.beehiiv.com → Settings → Publication ID
BEEHIIV_PUB_ID = os.environ.get("BEEHIIV_PUB_ID", "")

# ─────────────────────────────────────────────
# Site Configuration
# ─────────────────────────────────────────────
SITE_NAME = "NexScry"
SITE_TAGLINE = "AI-powered intelligence layer for builders"
SITE_URL = os.environ.get("SITE_URL", "https://nexscry.xyz")
SITE_DESCRIPTION = (
    "Every morning, NexScry scrapes 300+ signals from HN, GitHub, ArXiv, "
    "Product Hunt, and DEV.to — then cross-references them with AI to surface "
    "the best build opportunities for indie hackers and founders. Free, daily, open."
)

# ─────────────────────────────────────────────
# Scraper Configs
# ─────────────────────────────────────────────

# Reddit — public JSON endpoint (no auth needed)
REDDIT_SUBS = [
    "SaaS", "startups", "Entrepreneur", "webdev", "reactjs",
    "Python", "MachineLearning", "IndieHackers", "sideproject",
    "programming", "artificial", "LocalLLaMA",
]
REDDIT_SORT = "hot"
REDDIT_LIMIT = 50  # posts per sub
REDDIT_PAIN_KEYWORDS = [
    "I hate", "why is there no", "I wish", "frustrated",
    "anyone else", "can't believe", "need a tool", "looking for",
    "alternative to", "is there a", "broke for me", "doesn't work",
]

# Hacker News — Algolia API (fully open)
HN_FRONT_PAGE_LIMIT = 60
HN_COMMENT_DEPTH = 3  # levels of comments to fetch

# GitHub — public search API (no auth = 10 req/min, enough for daily)
GITHUB_LANGUAGES = ["Python", "TypeScript", "Rust", "Go", "JavaScript"]
GITHUB_TRENDING_DAYS = 7
GITHUB_MIN_STARS = 50

# ArXiv — Atom feed (fully open, no limits)
ARXIV_CATEGORIES = ["cs.AI", "cs.LG", "cs.CL", "cs.SE", "stat.ML"]
ARXIV_MAX_PAPERS = 100

# Product Hunt — no official API needed, we use their public feed
PH_DAILY_LIMIT = 30

# DEV.to — fully open API
DEVTO_LIMIT = 30

# ─────────────────────────────────────────────
# Cross-Source Intelligence (Sonnet didn't have this)
# ─────────────────────────────────────────────
# NexScry doesn't just summarize — it finds CONNECTIONS across sources.
# Example: Reddit user complains about X → GitHub repo solving X trending
#          → ArXiv paper about X published this week
CROSSREF_ENABLED = True
CROSSREF_MIN_SOURCES = 2  # minimum sources mentioning same topic to flag

# ─────────────────────────────────────────────
# Content Generation
# ─────────────────────────────────────────────
MAX_TOKENS_PER_ITEM = 500
DIGEST_ITEMS_PER_SOURCE = 10
TREND_LOOKBACK_DAYS = 7

# ─────────────────────────────────────────────
# Output Paths
# ─────────────────────────────────────────────
DATA_DIR = "data"
BUILD_DIR = "docs"  # GitHub Pages serves from /docs
