"""
Reddit Scraper — uses public RSS feeds instead of JSON API.
Reddit's RSS endpoints bypass the Cloudflare blocks that affect GitHub Actions IPs.
"""
import re
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone
from config import REDDIT_SUBS, REDDIT_SORT, REDDIT_LIMIT, REDDIT_PAIN_KEYWORDS


USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0"


def _parse_rss(xml: str, sub: str) -> list[dict]:
    """Parse Reddit RSS feed into post dicts."""
    posts = []
    items = re.findall(r"<item>(.*?)</item>", xml, re.DOTALL)

    for raw in items:
        def get_tag(tag, text=raw):
            m = re.search(rf"<{tag}[^>]*>(.*?)</{tag}>", text, re.DOTALL)
            return m.group(1).strip() if m else ""

        def get_cdata(tag, text=raw):
            m = re.search(rf"<{tag}[^>]*><!\[CDATA\[(.*?)\]\]></{tag}>", text, re.DOTALL)
            return m.group(1).strip() if m else get_tag(tag, text)

        title = get_cdata("title") or get_tag("title")
        # Skip "submitted by" meta titles
        if not title or title.startswith("submitted by"):
            continue

        link = get_tag("link") or get_cdata("link")
        # Clean up description/selftext
        desc = get_cdata("description") or ""
        desc = re.sub(r"<[^>]+>", " ", desc)
        desc = re.sub(r"\s+", " ", desc).strip()[:1000]

        text_blob = f"{title} {desc}".lower()
        pain_matches = [kw for kw in REDDIT_PAIN_KEYWORDS if kw.lower() in text_blob]

        posts.append({
            "source": "reddit",
            "sub": sub,
            "id": "",
            "title": title,
            "selftext": desc,
            "url": link,
            "score": 0,  # RSS doesn't expose score
            "num_comments": 0,
            "created_utc": 0,
            "author": "",
            "pain_signals": pain_matches,
            "has_pain": len(pain_matches) > 0,
            "flair": "",
            "scraped_at": datetime.now(timezone.utc).isoformat(),
        })

    return posts


def fetch_subreddit(sub: str, sort: str = REDDIT_SORT, limit: int = REDDIT_LIMIT) -> list[dict]:
    """Fetch posts from a subreddit via RSS (bypasses Cloudflare IP blocks)."""
    # RSS URL — not affected by the JSON API's Cloudflare rules
    url = f"https://www.reddit.com/r/{sub}/{sort}.rss?limit={min(limit, 100)}"
    req = urllib.request.Request(url, headers={
        "User-Agent": USER_AGENT,
        "Accept": "application/rss+xml, application/xml, text/xml, */*",
    })

    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                xml = resp.read().decode("utf-8", errors="replace")
            posts = _parse_rss(xml, sub)
            return posts
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait = 10 * (attempt + 1)
                print(f"  ⏳ r/{sub} RSS rate-limited — waiting {wait}s...")
                time.sleep(wait)
                continue
            print(f"  ⚠ r/{sub} RSS HTTP {e.code}: {e}")
            return []
        except Exception as e:
            print(f"  ⚠ r/{sub} RSS error: {e}")
            return []

    print(f"  ⚠ r/{sub}: all RSS attempts failed")
    return []


def scrape_all() -> list[dict]:
    """Scrape all configured subreddits via RSS. Returns flat list of posts."""
    all_posts = []
    for sub in REDDIT_SUBS:
        print(f"  📡 Scraping r/{sub}...")
        posts = fetch_subreddit(sub)
        all_posts.extend(posts)
        time.sleep(1.5)  # polite rate limiting

    # Sort by pain signals first (most actionable), then by title length as proxy for substance
    all_posts.sort(key=lambda p: (len(p["pain_signals"]), len(p["title"])), reverse=True)

    print(f"  ✅ Reddit: {len(all_posts)} posts from {len(REDDIT_SUBS)} subs")
    return all_posts


if __name__ == "__main__":
    posts = scrape_all()
    pain_posts = [p for p in posts if p["has_pain"]]
    print(f"\n🔥 Pain signal posts: {len(pain_posts)}/{len(posts)}")
    for p in pain_posts[:5]:
        print(f"  [{p['sub']}] {p['title'][:80]}  (signals: {p['pain_signals']})")
