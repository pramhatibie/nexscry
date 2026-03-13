"""
Product Hunt Scraper — uses public RSS/Atom feed (no auth needed).
Tracks daily launches to spot market moves and competitor activity.
"""
import json
import re
import urllib.request
from datetime import datetime, timezone
from config import PH_DAILY_LIMIT


PH_RSS_URL = "https://www.producthunt.com/feed"


def fetch_launches(limit: int = PH_DAILY_LIMIT) -> list[dict]:
    """Fetch latest Product Hunt launches from RSS."""
    req = urllib.request.Request(PH_RSS_URL, headers={"User-Agent": "NexScry/1.0"})

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            xml = resp.read().decode("utf-8")
    except Exception as e:
        print(f"  ⚠ Product Hunt: {e}")
        return []

    # Parse RSS items
    items_raw = re.findall(r"<item>(.*?)</item>", xml, re.DOTALL)
    launches = []

    for raw in items_raw[:limit]:
        def get_tag(tag):
            m = re.search(rf"<{tag}[^>]*>(.*?)</{tag}>", raw, re.DOTALL)
            return m.group(1).strip() if m else ""

        def get_cdata(tag):
            m = re.search(rf"<{tag}[^>]*><!\[CDATA\[(.*?)\]\]></{tag}>", raw, re.DOTALL)
            if m:
                return m.group(1).strip()
            return get_tag(tag)

        title = get_cdata("title") or get_tag("title")
        description = get_cdata("description") or get_tag("description")
        # Strip HTML tags from description
        description = re.sub(r"<[^>]+>", "", description)

        launches.append({
            "source": "producthunt",
            "title": title,
            "description": description[:500],
            "url": get_tag("link"),
            "published": get_tag("pubDate"),
            "scraped_at": datetime.now(timezone.utc).isoformat(),
        })

    print(f"  ✅ Product Hunt: {len(launches)} launches")
    return launches


def scrape_all() -> list[dict]:
    print("  📡 Scraping Product Hunt...")
    return fetch_launches()


if __name__ == "__main__":
    launches = scrape_all()
    for l in launches[:10]:
        print(f"  🚀 {l['title'][:60]} — {l['description'][:80]}")
