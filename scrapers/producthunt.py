"""
Product Hunt Scraper — uses public RSS/Atom feed (no auth needed).
Tracks daily launches to spot market moves and competitor activity.
"""
import re
import urllib.request
import urllib.error
from datetime import datetime, timezone
from config import PH_DAILY_LIMIT


# Try multiple endpoints in order
PH_FEED_URLS = [
    "https://www.producthunt.com/feed",
    "https://www.producthunt.com/feed?category=tech",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; NexScry/1.0; +https://github.com/pramhatibie/nexscry)",
    "Accept": "application/rss+xml, application/xml, text/xml, */*",
}


def _parse_feed(xml: str, limit: int) -> list[dict]:
    """Parse RSS/Atom feed XML into launch dicts."""
    launches = []

    # Try RSS <item> format first, then Atom <entry>
    items_raw = re.findall(r"<item>(.*?)</item>", xml, re.DOTALL)
    if not items_raw:
        items_raw = re.findall(r"<entry>(.*?)</entry>", xml, re.DOTALL)

    for raw in items_raw[:limit]:
        def get_tag(tag, text=raw):
            m = re.search(rf"<{tag}[^>]*>(.*?)</{tag}>", text, re.DOTALL)
            return m.group(1).strip() if m else ""

        def get_cdata(tag, text=raw):
            m = re.search(rf"<{tag}[^>]*><!\[CDATA\[(.*?)\]\]></{tag}>", text, re.DOTALL)
            if m:
                return m.group(1).strip()
            return get_tag(tag, text)

        title = get_cdata("title") or get_tag("title")
        description = get_cdata("description") or get_cdata("summary") or get_tag("description")
        # Strip HTML tags from description
        description = re.sub(r"<[^>]+>", " ", description)
        description = re.sub(r"\s+", " ", description).strip()

        # Link: RSS <link>, Atom <link href="...">, then <guid>
        link = (
            get_cdata("link")
            or get_tag("link")
            or re.search(r'<link[^>]+href=["\']([^"\']+)["\']', raw, re.IGNORECASE) and
               re.search(r'<link[^>]+href=["\']([^"\']+)["\']', raw, re.IGNORECASE).group(1)
            or get_tag("guid")
            or ""
        )
        pub_date = get_tag("pubDate") or get_tag("published") or get_tag("updated")

        if not title:
            continue

        launches.append({
            "source": "producthunt",
            "title": title,
            "description": description[:500],
            "url": link,
            "published": pub_date,
            "scraped_at": datetime.now(timezone.utc).isoformat(),
        })

    return launches


def fetch_launches(limit: int = PH_DAILY_LIMIT) -> list[dict]:
    """Fetch latest Product Hunt launches from RSS, trying multiple endpoints."""
    for feed_url in PH_FEED_URLS:
        req = urllib.request.Request(feed_url, headers=HEADERS)
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                xml = resp.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            print(f"  ⚠ Product Hunt {feed_url}: HTTP {e.code}")
            continue
        except Exception as e:
            print(f"  ⚠ Product Hunt {feed_url}: {e}")
            continue

        launches = _parse_feed(xml, limit)
        if launches:
            print(f"  ✅ Product Hunt: {len(launches)} launches")
            return launches
        print(f"  ⚠ Product Hunt: feed returned no items from {feed_url}")

    print("  ⚠ Product Hunt: all feed endpoints failed or empty")
    return []


def scrape_all() -> list[dict]:
    print("  📡 Scraping Product Hunt...")
    return fetch_launches()


if __name__ == "__main__":
    launches = scrape_all()
    for l in launches[:10]:
        print(f"  🚀 {l['title'][:60]} — {l['description'][:80]}")
