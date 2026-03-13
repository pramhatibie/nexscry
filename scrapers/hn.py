"""
Hacker News Scraper — uses HN's Algolia API (fully open, no auth).
Fetches front page stories + top comments for signal extraction.
"""
import json
import urllib.request
from datetime import datetime, timezone
from config import HN_FRONT_PAGE_LIMIT


ALGOLIA_BASE = "https://hn.algolia.com/api/v1"


def fetch_front_page(limit: int = HN_FRONT_PAGE_LIMIT) -> list[dict]:
    """Fetch current front page stories via Algolia."""
    url = f"{ALGOLIA_BASE}/search?tags=front_page&hitsPerPage={limit}"
    req = urllib.request.Request(url)

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
    except Exception as e:
        print(f"  ⚠ HN front page: {e}")
        return []

    stories = []
    for hit in data.get("hits", []):
        stories.append({
            "source": "hackernews",
            "id": hit.get("objectID"),
            "title": hit.get("title", ""),
            "url": hit.get("url", ""),
            "hn_url": f"https://news.ycombinator.com/item?id={hit.get('objectID')}",
            "points": hit.get("points", 0),
            "num_comments": hit.get("num_comments", 0),
            "author": hit.get("author", ""),
            "created_at": hit.get("created_at", ""),
            "scraped_at": datetime.now(timezone.utc).isoformat(),
        })

    return stories


def fetch_story_comments(story_id: str, limit: int = 15) -> list[dict]:
    """Fetch top comments for a story (for sentiment + insight extraction)."""
    url = f"{ALGOLIA_BASE}/items/{story_id}"
    req = urllib.request.Request(url)

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
    except Exception:
        return []

    comments = []

    def extract_children(node, depth=0):
        if depth > 2:
            return
        for child in node.get("children", []):
            text = child.get("text", "")
            if text:
                comments.append({
                    "text": text[:500],
                    "author": child.get("author", ""),
                    "points": child.get("points"),
                    "depth": depth,
                })
            if len(comments) < limit:
                extract_children(child, depth + 1)

    extract_children(data)
    return comments[:limit]


def fetch_ask_hn(limit: int = 20) -> list[dict]:
    """Fetch recent Ask HN posts — gold mine for builder pain points."""
    url = f"{ALGOLIA_BASE}/search?tags=ask_hn&hitsPerPage={limit}"
    req = urllib.request.Request(url)

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
    except Exception as e:
        print(f"  ⚠ Ask HN: {e}")
        return []

    return [
        {
            "source": "hackernews",
            "type": "ask_hn",
            "id": hit.get("objectID"),
            "title": hit.get("title", ""),
            "text": (hit.get("story_text") or "")[:500],
            "hn_url": f"https://news.ycombinator.com/item?id={hit.get('objectID')}",
            "points": hit.get("points", 0),
            "num_comments": hit.get("num_comments", 0),
            "created_at": hit.get("created_at", ""),
            "scraped_at": datetime.now(timezone.utc).isoformat(),
        }
        for hit in data.get("hits", [])
    ]


def scrape_all() -> list[dict]:
    """Fetch HN front page + Ask HN."""
    print("  📡 Scraping HN front page...")
    stories = fetch_front_page()
    print("  📡 Scraping Ask HN...")
    ask_posts = fetch_ask_hn()

    all_items = stories + ask_posts
    all_items.sort(key=lambda x: x.get("points", 0), reverse=True)

    print(f"  ✅ HN: {len(stories)} stories + {len(ask_posts)} Ask HN")
    return all_items


if __name__ == "__main__":
    items = scrape_all()
    for item in items[:10]:
        print(f"  [{item.get('points', 0)}⬆] {item['title'][:80]}")
