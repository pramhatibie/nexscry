"""
DEV.to Scraper — fully open public API (no auth needed).
Captures what the dev community is writing & reading.
"""
import json
import urllib.request
from datetime import datetime, timezone
from config import DEVTO_LIMIT


DEVTO_API = "https://dev.to/api/articles"


def fetch_articles(limit: int = DEVTO_LIMIT) -> list[dict]:
    """Fetch top recent articles from DEV.to."""
    url = f"{DEVTO_API}?per_page={limit}&top=7"  # top of last 7 days
    req = urllib.request.Request(url, headers={
        "User-Agent": "NexScry/1.0",
        "Accept": "application/json",
    })

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
    except Exception as e:
        print(f"  ⚠ DEV.to: {e}")
        return []

    articles = []
    for a in data:
        articles.append({
            "source": "devto",
            "id": a.get("id"),
            "title": a.get("title", ""),
            "description": a.get("description", ""),
            "url": a.get("url", ""),
            "tags": a.get("tag_list", []),
            "reactions": a.get("public_reactions_count", 0),
            "comments": a.get("comments_count", 0),
            "reading_time": a.get("reading_time_minutes", 0),
            "author": a.get("user", {}).get("username", ""),
            "published_at": a.get("published_at", ""),
            "scraped_at": datetime.now(timezone.utc).isoformat(),
        })

    print(f"  ✅ DEV.to: {len(articles)} articles")
    return articles


def scrape_all() -> list[dict]:
    print("  📡 Scraping DEV.to...")
    return fetch_articles()


if __name__ == "__main__":
    articles = scrape_all()
    for a in articles[:10]:
        print(f"  ❤️{a['reactions']} {a['title'][:60]} [{', '.join(a['tags'][:3])}]")
